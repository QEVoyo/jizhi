from fastapi import APIRouter, HTTPException, Query, Body, Path, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta, timezone
from config import settings
import httpx, uuid, re, json
import asyncio
from collections import defaultdict
from utils.xunfei_client import XunfeiClient
from agents.qwen_client import call_qwen, call_qwen_stream, call_qwen_vision
from agents.intent_router import route_intent
from utils.auth_middleware import get_current_user, verify_user_match
from services.supabase import get_supabase_headers
from services import xiaoji_memory
from services import xiaoji_persona
from logging_config import logger
from .models import *
import base64
from fastapi.responses import StreamingResponse, JSONResponse
router = APIRouter(prefix="/community", tags=["社区-小基"])
# ============================================================
# 小基（AI好友）相关接口
# ============================================================

async def _save_xiaoji_message(user_id: str, role: str, content: str, kind: str = "chat", extra: dict = None):
    """保存小基消息到数据库"""
    headers = get_supabase_headers()
    msg = {"user_id": user_id, "role": role, "content": content, "kind": kind}
    if extra:
        msg.update(extra)
    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.post(f"{settings.SUPABASE_URL}/rest/v1/xiaoji_messages", headers=headers, json=msg)
        return res.status_code


# ============================================================
# 小基世界·队员真实分流（2026-09-02 全套改造）
# 之前：队友卡只是把预设提问送进小基同一条对话通道（共用小基人设、零真实数据，
#       署名全靠前端内存，刷新即丢）
# 现在：plan/evaluate 各自独立人设 + 服务端注入真实学习数据；
#       generate 走真实题目生成管线（/xiaoji/agent-generate）；
#       assistant 消息落库 agent 字段（fix_xiaoji_agent_column.sql）供历史回显
# ============================================================

# ⚠️ 现状（2026-09-10 自动分流改造后）：本表与下方 _build_agent_grounding 已**暂无调用方**——
# 规划/评估不再走「换人设聊天」，改为出卡片（计划卡调 /learning-plan/generate-tasks、
# 评估卡调 /evaluation/deep-analysis）。这里保留是因为 grounding 那套「拉真实学习数据
# 拼成上下文」正是下一步「按聊天记录生成个性化计划」要复用的输入，届时在此接回。
AGENT_PERSONAS = {
    "plan": {
        "name": "规划 Agent",
        "tagline": "三阶段备考规划师 · 节奏官",
        "persona": """你的职责：基于用户的真实计划与任务数据，诊断计划执行情况、给出节奏与任务量建议。
- 说话简洁、口语化，一次只给 2-3 个要点
- 只引用【真实数据】里有的数字，绝不编造计划或完成率
- 数据为空时明说「还没有计划数据」，并建议去创建计划
- 不要用 Markdown，不要长篇大论""",
    },
    "evaluate": {
        "name": "评估 Agent",
        "tagline": "敢下结论的学习裁判",
        "persona": """你的职责：基于用户的真实做题数据，下诊断结论、指出薄弱点、给出可执行建议。
- 先给结论（一句话），再给依据（真实数字），最后给 1-2 条行动建议
- 只引用【真实数据】里有的数字，绝不编造
- 没有数据时明说「还没有做题数据」，并鼓励用户先做题
- 不要用 Markdown，不要长篇大论""",
    },
}


async def _build_agent_grounding(user_id: str, agent_key: str) -> str:
    """拉取用户真实学习数据注入队员 system prompt（plan=计划任务 / evaluate=做题掌握度）"""
    try:
        from routers.agent_center import _collect
        since = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        data = await _collect(user_id, since)
    except Exception:
        return "（真实数据暂不可用，请如实说明无法获取数据，不要编造）"

    if agent_key == "plan":
        tasks = data.get("tasks", [])
        done = sum(1 for t in tasks if t.get("completed"))
        rate = round(done / len(tasks) * 100) if tasks else 0
        plan_count = len(data.get("plans", []))
        days = {}
        for t in tasks:
            d = (t.get("date") or "")[:10]
            if d:
                days.setdefault(d, [0, 0])
                days[d][1] += 1
                if t.get("completed"):
                    days[d][0] += 1
        recent = sorted(days.items())[-7:]
        day_lines = "、".join(f"{d[5:]}:{v[0]}/{v[1]}" for d, v in recent) or "无"
        # 自定义计划（learning_plans）
        lplans = []
        try:
            headers = get_supabase_headers()
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.get(
                    f"{settings.SUPABASE_URL}/rest/v1/learning_plans?user_id=eq.{user_id}"
                    f"&select=name,progress,status,end_date&order=created_at.desc&limit=5",
                    headers=headers)
                lplans = res.json() if res.status_code == 200 else []
        except Exception:
            pass
        lp_lines = "；".join(
            f"{p.get('name', '未命名')}(进度 {p.get('progress', 0) or 0}%、{p.get('status', 'active')}、截止 {(p.get('end_date') or '')[:10] or '未定'})"
            for p in lplans) or "无"
        return (
            f"学科计划 {plan_count} 个；近 30 天任务完成 {done}/{len(tasks)}（完成率 {rate}%）；"
            f"近 7 天每日完成（日期:完成/总数）：{day_lines}；"
            f"自定义计划：{lp_lines}"
        )

    # evaluate
    records = data.get("records", [])
    total = len(records)
    correct = sum(1 for r in records if r.get("is_correct"))
    rate = round(correct / total * 100) if total else 0
    days = {}
    for r in records:
        d = (r.get("created_at") or "")[:10]
        if d:
            days.setdefault(d, [0, 0])
            days[d][1] += 1
            if r.get("is_correct"):
                days[d][0] += 1
    recent = sorted(days.items())[-7:]
    day_lines = "、".join(f"{d[5:]} {v[0]}/{v[1]}" for d, v in recent) or "无"
    scored = [m for m in data.get("mastery", []) if m.get("mastery_score") is not None]
    weak = sorted(scored, key=lambda m: m.get("mastery_score") or 0)[:5]
    strong = sorted(scored, key=lambda m: m.get("mastery_score") or 0, reverse=True)[:3]

    def kname(m):
        return (m.get("kp_name") or m.get("kp_id") or "未知知识点")

    weak_lines = "、".join(f"{kname(m)}({(m.get('mastery_score') or 0):.0f}%)" for m in weak) or "无"
    strong_lines = "、".join(kname(m) for m in strong) or "无"
    exams = len(data.get("exams", []))
    return (
        f"近 30 天做题 {total} 道、正确 {correct} 道（正确率 {rate}%）；"
        f"最近 7 天（日期 对/总数）：{day_lines}；"
        f"薄弱知识点 TOP5：{weak_lines}；已掌握好的：{strong_lines}；"
        f"真题卷记录 {exams} 份"
    )


async def _build_xiaoji_chat_messages(user_id: str, user_content: str, agent_key: str = "") -> list:
    """构建聊天 messages：昵称 + 小基配置（名称/语气风格）+ 最近 10 条上下文
    三个查询互相独立，asyncio.gather 并发拉取（串行会拖慢流式首字节 ~3s）；
    队友卡（agent_key）时并发拉取真实数据 grounding 并换队员人设"""
    headers = get_supabase_headers()
    profile_url = f"{settings.SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}"
    config_url = f"{settings.SUPABASE_URL}/rest/v1/xiaoji_config?user_id=eq.{user_id}"
    # 最近原文条数（长期记忆见 services/xiaoji_memory.py：事实档案 + 滚动摘要补足更早的信息）
    history_url = (f"{settings.SUPABASE_URL}/rest/v1/xiaoji_messages"
                   f"?user_id=eq.{user_id}&order=created_at.desc&limit={xiaoji_memory.RECENT_MESSAGES}")

    persona = AGENT_PERSONAS.get(agent_key)
    grounding_task = asyncio.create_task(_build_agent_grounding(user_id, agent_key)) if persona else None
    # 长期记忆与其余查询并发拉取；表未建时返回 None，下面自动跳过
    memory_task = asyncio.create_task(xiaoji_memory.load(user_id))

    async with httpx.AsyncClient(timeout=30.0) as client:
        profile_res, config_res, history_res = await asyncio.gather(
            client.get(profile_url, headers=headers),
            client.get(config_url, headers=headers),
            client.get(history_url, headers=headers),
            return_exceptions=True,
        )
        profile = {}
        if isinstance(profile_res, httpx.Response) and profile_res.status_code == 200:
            rows = profile_res.json()
            if isinstance(rows, list) and rows:
                profile = rows[0]
        nickname = profile.get("nickname", "同学")

        cfg = {}
        if isinstance(config_res, httpx.Response) and config_res.status_code == 200 and config_res.json():
            cfg = config_res.json()[0]
        xiaoji_name = (cfg.get("name") or "小基").strip() or "小基"
        personality = cfg.get("personality") or "warm"

    grounding = ""
    if grounding_task:
        grounding = await grounding_task

    # 长期记忆（事实档案 + 滚动摘要）：空/表未建时 context_block 返回空串，无副作用
    try:
        memory = await memory_task
    except Exception:
        memory = None
    mem_block = xiaoji_memory.context_block(memory)

    # 队员人设：专业身份 + 真实数据（与小基陪伴人设互斥）
    if persona:
        system_prompt = f"""你是「{persona['name']}」——{persona['tagline']}，用户「{nickname}」的专属学习队友。

{persona['persona']}

【真实数据】（服务端实时拉取，只以此为准）
{grounding}

记住：你的署名是「{persona['name']}」，不是小基；你是专业队员，回答必须体现专业判断。"""
    else:
        style_text = xiaoji_persona.style_of(personality)

        system_prompt = f"""你是一个{style_text}的AI学习伙伴，名字叫「{xiaoji_name}」。

你的性格特点：
- {style_text}
- 耐心倾听，不会打断用户
- 擅长鼓励和引导，不直接给答案

你的角色定位：
- 你是用户「{nickname}」的学习伙伴
- 你会关心用户的学习状态和情绪
- 你会用轻松自然的方式聊学习

说话风格：
- 自然口语化，不用官方腔
- 不要用 Markdown 格式

记住：你是朋友，不是老师。你的目标是让学习变得有趣。
"""

    # 长期记忆拼在人格设定之后（对两种人设都生效）
    if mem_block:
        system_prompt += "\n" + mem_block + "\n"

    history = []
    if isinstance(history_res, httpx.Response) and history_res.status_code == 200:
        history = history_res.json()
        history.reverse()

    messages = [{"role": "system", "content": system_prompt}]
    for msg in history:
        messages.append({
            "role": msg.get("role", "user"),
            "content": msg.get("content", "")
        })
    messages.append({"role": "user", "content": user_content})
    return messages


@router.get("/xiaoji/messages")
async def get_xiaoji_messages(
        user_id: str = Query(...),
        search: Optional[str] = Query(None),
        limit: int = Query(30, ge=1, le=100),
        offset: int = Query(0, ge=0),
        current_user: str = Depends(get_current_user)
):
    """获取用户与小基的聊天记录（分页：默认最近 30 条；search 时全量升序返回）"""
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()
    url = f"{settings.SUPABASE_URL}/rest/v1/xiaoji_messages?user_id=eq.{user_id}"
    if search:
        # PostgREST 模糊匹配通配符是 *（会转成 SQL 的 %），不能用裸 %
        url += f"&content=ilike.*{search}*&order=created_at.asc"
    else:
        url += f"&order=created_at.desc&limit={limit}&offset={offset}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.get(url, headers={**headers, "Prefer": "count=exact"})
        # count=exact + limit 且结果被截断时 PostgREST 返回 206 Partial Content（正常态）
        if res.status_code not in (200, 206):
            return {"messages": [], "total": 0, "has_more": False}
        messages = res.json()
        # 分页模式取的是 desc 最新一页，反转为升序给前端直接展示/前置拼接
        if not search:
            messages.reverse()
        for msg in messages:
            if msg.get("role") == "user":
                msg["sender_id"] = msg.get("user_id")
            else:
                msg["sender_id"] = "xiaoji"
        if search:
            return {"messages": messages, "total": len(messages), "has_more": False}
        # content-range: 0-29/123 → total=123
        total = 0
        content_range = res.headers.get("content-range", "")
        if "/" in content_range:
            total = int(content_range.rsplit("/", 1)[-1])
        return {"messages": messages, "total": total, "has_more": offset + limit < total}


@router.post("/xiaoji/chat")
async def send_xiaoji_message(
        user_id: str = Query(...),
        data: dict = Body(...),
        current_user: str = Depends(get_current_user)
):
    """与小基聊天（非流式，保留给旧调用方）"""
    verify_user_match(user_id, current_user)

    user_content = data.get("content", "")
    if not user_content:
        raise HTTPException(status_code=400, detail="内容不能为空")

    messages = await _build_xiaoji_chat_messages(user_id, user_content)
    response = call_qwen(messages, temperature=0.8)

    await _save_xiaoji_message(user_id, "user", user_content)
    await _save_xiaoji_message(user_id, "assistant", response)

    return {"reply": response}


@router.post("/xiaoji/route")
async def xiaoji_route(data: dict = Body(...), current_user: str = Depends(get_current_user)):
    """对话意图判别（2026-09-10 自动分流）

    deep=false（默认）：只跑规则层与关键词门——零成本零延迟，供输入框实时预判；
    deep=true：允许在「像派活但规则没抓住」时调一次 qwen-flash 兜底，发送时用。
    """
    text = (data.get("text") or "").strip()
    if not text:
        return {"intent": "chat", "matched": "short", "hit": ""}
    return route_intent(text, allow_llm=bool(data.get("deep")))


@router.post("/xiaoji/chat-stream")
async def send_xiaoji_message_stream(
        user_id: str = Query(...),
        data: dict = Body(...),
        current_user: str = Depends(get_current_user)
):
    """小基对话入口——**自动判别**（2026-09-10，取代前端手动选角色）

    - 判为闲聊 → 原样流式返回文本（前端边收边显示 + 按句子语音播报）
    - 判为派活（generate/plan/evaluate）→ 不在这里回答，直接返回 JSON 路由指令，
      由前端出对应卡片（省一次往返；卡片各自去调专用端点）

    判别成本：规则层零成本；仅「像派活但规则没抓住」时才多一次 qwen-flash（~0.4s）。
    """
    verify_user_match(user_id, current_user)

    user_content = data.get("content", "")
    if not user_content:
        raise HTTPException(status_code=400, detail="内容不能为空")

    # force_chat：陪伴类快捷提问（「背个单词」「求安慰」）跳过判别，固定走队长闲聊
    route = {"intent": "chat", "matched": "forced"} if data.get("force_chat") else route_intent(user_content)
    if route["intent"] != "chat":
        # 用户消息照常落库，保持对话历史完整
        try:
            await _save_xiaoji_message(user_id, "user", user_content)
        except Exception:
            pass
        logger.info(f"[xiaoji] 分流 {route['intent']}（{route['matched']}）← {user_content[:30]!r}")
        return JSONResponse({"route": route["intent"], "matched": route["matched"]})

    # ===== 以下为闲聊链路（原逻辑不变）=====
    # 用户消息落库与上下文构建并发（落库不阻塞流式首字节）
    save_task = asyncio.create_task(_save_xiaoji_message(user_id, "user", user_content))
    messages = await _build_xiaoji_chat_messages(user_id, user_content)

    async def generate():
        full = ""
        try:
            # call_qwen_stream 直接产出文本片段
            for c in call_qwen_stream(messages, temperature=0.8):
                full += c
                yield c
        except Exception as e:
            logger.info(f"小基流式聊天错误: {e}")
            if not full:
                fallback = "抱歉，我刚刚走神了，请再说一次～"
                full = fallback
                yield fallback
        if full:
            await _save_xiaoji_message(user_id, "assistant", full)
            # 长期记忆增量压缩：后台跑，不占用用户等待；表未建/量不够会自动跳过
            asyncio.create_task(xiaoji_memory.maybe_compress(user_id))

    try:
        await save_task
    except Exception:
        pass  # 用户消息落库失败不影响对话

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/xiaoji/agent-generate")
async def xiaoji_agent_generate(
        user_id: str = Query(...),
        data: dict = Body(None),
        current_user: str = Depends(get_current_user)
):
    """生成 Agent 队友：用户指定知识点（自由提问）或自动选题（薄弱优先→错题主题→综合）
    → 真实生成落库 → 题目卡回聊。不再走聊天通道（2026-09-02 真实分流）"""
    verify_user_match(user_id, current_user)
    data = data or {}

    topic = (data.get("topic") or "").strip()
    picked_from = ""
    if topic and len(topic) >= 2:
        from utils.sensitive_words import check_content_safety
        safe, reason = check_content_safety(topic)
        if not safe:
            raise HTTPException(status_code=400, detail=f"知识点包含敏感信息：{reason}")
        picked_from = f"按你指定的知识点「{topic}」"
    else:
        topic, picked_from = await _pick_generate_topic(user_id)

    extra = data.get("extra") or ""
    if extra:
        from utils.sensitive_words import check_content_safety
        safe, reason = check_content_safety(extra)
        if not safe:
            raise HTTPException(status_code=400, detail=f"补充说明包含敏感信息：{reason}")

    # 薄弱点定向 → 简单档建立信心；否则默认中等
    difficulty = data.get("difficulty") or ("简单" if picked_from.startswith("根据你的薄弱知识点") else "中等")
    question_type = data.get("question_type") or "选择题"

    from routers.questions import generate_question_core
    question = await generate_question_core(user_id, "通用", topic, question_type, difficulty, extra)
    return {"question": question, "topic": topic, "picked_from": picked_from}


async def _pick_generate_topic(user_id: str):
    """出题卡自动选题：60 天掌握度薄弱 → 生成题错题主题 → 无数据时综合题（学科自定）"""
    import random
    try:
        from routers.agent_center import _collect
        since = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
        data = await _collect(user_id, since)
    except Exception:
        data = {}

    # 1) 掌握度薄弱（user_kp_mastery，kp_name 优先）
    weak = [m for m in data.get("mastery", []) if (m.get("mastery_score") or 100) < 60]
    if weak:
        weak.sort(key=lambda m: m.get("mastery_score") or 0)
        m = random.choice(weak[:8])
        name = (m.get("kp_name") or m.get("kp_id") or "").strip()
        if name:
            return name, f"根据你的薄弱知识点「{name}」（掌握度 {(m.get('mastery_score') or 0):.0f}%）"

    # 2) 生成题里的错题主题（questions 表 mistake_status）
    try:
        headers = get_supabase_headers()
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.get(
                f"{settings.SUPABASE_URL}/rest/v1/questions?user_id=eq.{user_id}"
                f"&select=topic,normalized_topic,mistake_status&limit=500",
                headers=headers)
            rows = res.json() if res.status_code == 200 else []
        wrong_topics = []
        for q in rows:
            ms = q.get("mistake_status")
            t = (q.get("normalized_topic") or q.get("topic") or "").strip()
            if ms and ms != "none" and t:
                wrong_topics.append(t)
        if wrong_topics:
            t = random.choice(wrong_topics)
            return t, f"根据你的错题知识点「{t}」"
    except Exception:
        pass

    return "", "暂无掌握度/错题数据，先来一道综合题"


@router.post("/xiaoji/vision")
async def xiaoji_vision(
        user_id: str = Query(...),
        data: dict = Body(...),
        current_user: str = Depends(get_current_user)
):
    """小基图片理解"""
    verify_user_match(user_id, current_user)

    image_url = data.get("image_url", "")
    question = data.get("question", "这张图片里有什么？")

    if not image_url:
        raise HTTPException(status_code=400, detail="请提供图片")

    headers = get_supabase_headers()

    user_msg = {
        "user_id": user_id,
        "role": "user",
        "content": question or "[图片]",
        "image_url": image_url,
        "kind": "vision"
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        await client.post(
            f"{settings.SUPABASE_URL}/rest/v1/xiaoji_messages",
            headers=headers,
            json=user_msg
        )

    try:
        response = call_qwen_vision(image_url, question or "这张图片里有什么？", temperature=0.8)
    except Exception as e:
        logger.info(f"图片理解失败: {e}")
        raise HTTPException(status_code=500, detail=f"图片理解失败: {str(e)}")

    assistant_msg = {
        "user_id": user_id,
        "role": "assistant",
        "content": response,
        "kind": "vision"

    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        await client.post(
            f"{settings.SUPABASE_URL}/rest/v1/xiaoji_messages",
            headers=headers,
            json=assistant_msg
        )

    return {"reply": response}


@router.post("/xiaoji/video-analyze")
async def xiaoji_video_analyze(
        user_id: str = Query(...),
        data: dict = Body(...),
        current_user: str = Depends(get_current_user)
):
    """小基视频分析（2026-09-05）：前端本地抽帧(3-5 张 jpeg data URL) →
    逐帧并行识图 → 汇总成一条分析回复（不入库截图，走 xiaoji_messages kind=video）"""
    verify_user_match(user_id, current_user)

    frames = [f for f in (data.get("frames") or []) if isinstance(f, str) and f][:5]
    question = str(data.get("question") or "").strip() or "分析这个视频讲了什么"
    if not frames:
        raise HTTPException(status_code=400, detail="请先上传视频")

    async def describe_one(i: int, f: str) -> str:
        try:
            desc = await asyncio.to_thread(
                call_qwen_vision, f,
                f"这是视频的第 {i + 1} 帧画面。请简短描述画面内容：人物/场景/文字/图表/关键信息（≤80字）。",
                temperature=0.5,
            )
            return f"第{i + 1}帧：{desc}"
        except Exception:
            return f"第{i + 1}帧：识别失败"

    descs = await asyncio.gather(*[describe_one(i, f) for i, f in enumerate(frames)])
    joined = "\n".join(descs)
    prompt = (
        f"下面是用户上传的一个视频的抽帧画面描述（共 {len(descs)} 帧）：\n{joined}\n\n"
        f"用户的问题：{question}\n"
        "请依据抽帧内容回答：这个视频在讲什么、有哪些要点。可以是内容总结、题目讲解或学习建议。"
        "用中文作答，300 字以内，口语一点，不要用 markdown。"
    )
    try:
        response = await asyncio.to_thread(
            call_qwen, [{"role": "user", "content": prompt}], temperature=0.7, model=settings.QWEN_REASON_MODEL
        )
    except Exception as e:
        logger.info(f"视频分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"视频分析失败: {str(e)}")

    headers = get_supabase_headers()
    to_save = [
        {"user_id": user_id, "role": "user", "content": question or "[视频]", "kind": "video"},
        {"user_id": user_id, "role": "assistant", "content": response, "kind": "video"},
    ]
    async with httpx.AsyncClient(timeout=30.0) as client:
        for m in to_save:
            try:
                await client.post(f"{settings.SUPABASE_URL}/rest/v1/xiaoji_messages", headers=headers, json=m)
            except Exception:
                pass

    return {"reply": response}


@router.get("/xiaoji/config")
async def get_xiaoji_config(user_id: str = Query(...), current_user: str = Depends(get_current_user)):
    """获取小基配置"""
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()
    url = f"{settings.SUPABASE_URL}/rest/v1/xiaoji_config?user_id=eq.{user_id}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.get(url, headers=headers)
        if res.status_code == 200 and res.json():
            return res.json()[0]
        return {
            "user_id": user_id,
            "name": "小基",
            "personality": "温暖学伴",
            "voice_enabled": True,
            "proactive_enabled": True
        }


@router.put("/xiaoji/config")
async def update_xiaoji_config(user_id: str = Query(...), data: dict = Body(...), current_user: str = Depends(get_current_user)):
    """更新小基配置"""
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()

    check_url = f"{settings.SUPABASE_URL}/rest/v1/xiaoji_config?user_id=eq.{user_id}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        check_res = await client.get(check_url, headers=headers)

        if check_res.status_code == 200 and check_res.json():
            url = f"{settings.SUPABASE_URL}/rest/v1/xiaoji_config?user_id=eq.{user_id}"
            res = await client.patch(url, headers=headers, json=data)
        else:
            data["user_id"] = user_id
            url = f"{settings.SUPABASE_URL}/rest/v1/xiaoji_config"
            res = await client.post(url, headers=headers, json=data)

        if res.status_code not in [200, 201, 204]:
            raise HTTPException(status_code=400, detail=f"更新失败: {res.text}")
        return {"success": True, "message": "更新成功"}

@router.post("/xiaoji/tts")
async def xiaoji_tts(data: dict = Body(...)):
    """文字转语音（千问 TTS-Plus，与 /xiaoji/tts 同源）"""

    text = data.get("text", "")
    speed = data.get("speed", 5)
    volume = data.get("volume", 5)
    voice_name = data.get("voice_name", "longanqian")

    if not text:
        raise HTTPException(status_code=400, detail="text 不能为空")

    from utils.qwen_tts_client import get_tts_audio
    audio_data = get_tts_audio(text, voice_name, speed, volume, 5)

    if not audio_data:
        raise HTTPException(status_code=500, detail="语音合成失败")

    return {
        "success": True,
        "audio_base64": base64.b64encode(audio_data).decode("utf-8"),
        "format": "mp3"
    }


@router.post("/xiaoji/asr")
async def xiaoji_asr(data: dict = Body(...)):
    """语音转文字 - 使用讯飞 ASR"""

    client = XunfeiClient()
    audio_base64 = data.get("audio_base64", "")
    audio_format = data.get("format", "wav")

    if not audio_base64:
        raise HTTPException(status_code=400, detail="audio_base64 不能为空")

    try:
        audio_bytes = base64.b64decode(audio_base64)
        result = client.speech_to_text(audio_bytes, audio_format)

        if not result:
            raise HTTPException(status_code=500, detail="语音识别失败")

        return {"success": True, "text": result}
    except Exception as e:
        logger.info(f"ASR 错误: {e}")
        raise HTTPException(status_code=500, detail=f"ASR 错误: {str(e)}")

# ============================================================
# 小基 - 题目评价接口
# ============================================================

# 题目四维度评价提示词：非流式与流式两个端点共用，只维护这一份
_EVAL_QUESTION_PROMPT = """你是一位资深学习导师，请从4个维度评价用户发送的题目。

【题目信息】
标题：{question_title}
内容：{question_content}
题型：{question_type}
难度：{difficulty}
正确答案：{correct_answer}
解析：{explanation}

请按以下4个维度输出，每个维度用 ## 标题分隔：

## 📖 理解题目
- 这道题在考什么知识点？
- 题目的核心难点是什么？

## 📊 评估
- 这道题对用户来说难度如何？
- 用户可能在哪一步卡住？

## 💡 解析思路
- 给出解题思路（不要直接给答案）
- 关键步骤和提示

## 📚 学习规划
- 如果用户做对了，接下来应该学什么？
- 如果用户没做对，应该补什么知识点？
- 给出具体的学习建议

请用温暖、鼓励的语气，像朋友一样自然。不要直接给答案，要引导用户思考。
"""


@router.post("/xiaoji/evaluate-question")
async def xiaoji_evaluate_question(
    user_id: str = Query(...),
    data: dict = Body(...),
    current_user: str = Depends(get_current_user)
):
    """小基评价用户发送的题目 - 4维度输出"""
    verify_user_match(user_id, current_user)

    question = data.get("question", {})
    if not question:
        raise HTTPException(status_code=400, detail="请提供题目")

    # ===== 提取题目信息 =====
    question_title = question.get("title", "")
    question_content = question.get("question_content", "") or question.get("title", "")
    question_type = question.get("question_type", "未知")
    difficulty = question.get("difficulty_score", 5)
    correct_answer = question.get("answer", "未提供")
    explanation = question.get("explanation", "")

    # ===== 获取用户昵称 =====
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        profile_url = f"{settings.SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}&select=nickname"
        profile_res = await client.get(profile_url, headers=headers)
        nickname = profile_res.json()[0].get("nickname", "同学") if profile_res.json() else "同学"

    # ===== 4维度 Prompt =====
    eval_prompt = _EVAL_QUESTION_PROMPT.format(
        question_title=question_title,
        question_content=question_content,
        question_type=question_type,
        difficulty=difficulty,
        correct_answer=correct_answer,
        explanation=explanation,
    )

    messages = [
        {"role": "system", "content": f"你是小基，一个温暖幽默的学习伙伴。用户叫「{nickname}」。"},
        {"role": "user", "content": eval_prompt}
    ]

    try:
        response = call_qwen(messages, temperature=0.7, model=settings.QWEN_REASON_MODEL)

        # ===== 保存到数据库 =====
        headers = {
            "apikey": settings.SUPABASE_KEY,
            "Authorization": f"Bearer {settings.SUPABASE_KEY}",
            "Content-Type": "application/json"
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            assistant_msg = {
                "user_id": user_id,
                "role": "assistant",
                "content": response,
                "is_evaluation": True,
                "kind": "evaluate"
            }
            await client.post(
                f"{settings.SUPABASE_URL}/rest/v1/xiaoji_messages",
                headers=headers,
                json=assistant_msg
            )

        return {"reply": response}

    except Exception as e:
        logger.info(f"评价失败: {e}")
        raise HTTPException(status_code=500, detail=f"评价失败: {str(e)}")


@router.post("/xiaoji/evaluate-set")
async def xiaoji_evaluate_set(
    user_id: str = Query(...),
    data: dict = Body(...),
    current_user: str = Depends(get_current_user)
):
    """
    小基评价用户发送的整个题集
    """
    verify_user_match(user_id, current_user)

    set_data = data.get("set", {})
    questions = data.get("questions", [])

    if not set_data or not questions:
        raise HTTPException(status_code=400, detail="请提供题集数据")

    # 获取掌握度
    headers = get_supabase_headers()
    async with httpx.AsyncClient(timeout=30.0) as client:
        mastery_url = f"{settings.SUPABASE_URL}/rest/v1/questions?user_id=eq.{user_id}&select=normalized_topic,mastery_score"
        mastery_res = await client.get(mastery_url, headers=headers)
        qs = mastery_res.json() if mastery_res.status_code == 200 else []
        topic_mastery = {}
        for q in qs:
            topic = q.get("normalized_topic") or q.get("topic") or "未分类"
            if topic not in topic_mastery:
                topic_mastery[topic] = {"sum": 0, "count": 0}
            topic_mastery[topic]["sum"] += q.get("mastery_score", 0)
            topic_mastery[topic]["count"] += 1
        mastery_summary = [f"{t}: {round(d['sum']/d['count'])}%" for t, d in topic_mastery.items()]
        mastery_text = "用户的知识点掌握度：\n" + "\n".join(mastery_summary) if mastery_summary else "暂无掌握度数据"

    # 构建题集评价 Prompt
    set_name = set_data.get("name", "未命名题集")
    question_count = len(questions)

    eval_prompt = f"""用户发送了一个题集「{set_name}」，包含 {question_count} 道题目。

【用户掌握度数据】
{mastery_text}

【题集题目列表】
{json.dumps([{
    "title": q.get("title", ""),
    "type": q.get("question_type", ""),
    "difficulty": q.get("difficulty_score", 5)
} for q in questions], ensure_ascii=False, indent=2)}

请从以下几个维度评价这个题集：
1. 这个题集的整体难度和主题是什么
2. 用户当前的掌握度与这个题集的匹配度如何
3. 哪些题目用户可能会觉得困难
4. 给出整体鼓励和学习建议
5. 如果题集难度适中，夸夸用户选得好
6. 如果题集偏难，告诉用户不用着急

用温暖、鼓励的语气回复。"""

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            profile_url = f"{settings.SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}&select=nickname"
            profile_res = await client.get(profile_url, headers=headers)
            nickname = profile_res.json()[0].get("nickname", "同学") if profile_res.json() else "同学"

        messages = [
            {"role": "system", "content": f"你是小基，一个温暖幽默的学习伙伴。用户叫「{nickname}」。"},
            {"role": "user", "content": eval_prompt}
        ]

        response = call_qwen(messages, temperature=0.7, model=settings.QWEN_REASON_MODEL)

        # 保存
        assistant_msg = {
            "user_id": user_id,
            "role": "assistant",
            "content": response,
            "is_evaluation": True
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            await client.post(
                f"{settings.SUPABASE_URL}/rest/v1/xiaoji_messages",
                headers=headers,
                json=assistant_msg
            )

        return {"reply": response}

    except Exception as e:
        logger.info(f"评价题集失败: {e}")
        raise HTTPException(status_code=500, detail=f"评价失败: {str(e)}")



@router.post("/xiaoji/evaluate-question-stream")
async def xiaoji_evaluate_question_stream(
    user_id: str = Query(...),
    data: dict = Body(...),
    current_user: str = Depends(get_current_user)
):
    """流式评价题目 - 4个智能体依次输出"""
    verify_user_match(user_id, current_user)

    question = data.get("question", {})
    if not question:
        raise HTTPException(status_code=400, detail="请提供题目")

    question_title = question.get("title", "")
    question_content = question.get("question_content", "") or question.get("title", "")
    question_type = question.get("question_type", "未知")
    difficulty = question.get("difficulty_score", 5)
    correct_answer = question.get("answer", "未提供")
    explanation = question.get("explanation", "")

    eval_prompt = _EVAL_QUESTION_PROMPT.format(
        question_title=question_title,
        question_content=question_content,
        question_type=question_type,
        difficulty=difficulty,
        correct_answer=correct_answer,
        explanation=explanation,
    )

    # 获取用户昵称
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        profile_url = f"{settings.SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}&select=nickname"
        profile_res = await client.get(profile_url, headers=headers)
        nickname = profile_res.json()[0].get("nickname", "同学") if profile_res.json() else "同学"

    messages = [
        {"role": "system", "content": f"你是小基，一个温暖幽默的学习伙伴。用户叫「{nickname}」。"},
        {"role": "user", "content": eval_prompt}
    ]

    stream = call_qwen_stream(messages, temperature=0.7, model=settings.QWEN_REASON_MODEL)

    async def generate():
        full_content = ""
        # call_qwen_stream 直接产出文本片段（非 OpenAI 对象）
        for chunk in stream:
            if chunk:
                full_content += chunk
                yield chunk

        # 保存到数据库
        headers = {
            "apikey": settings.SUPABASE_KEY,
            "Authorization": f"Bearer {settings.SUPABASE_KEY}",
            "Content-Type": "application/json"
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            assistant_msg = {
                "user_id": user_id,
                "role": "assistant",
                "content": full_content,
                "is_evaluation": True,
                "kind": "evaluate"
            }
            await client.post(
                f"{settings.SUPABASE_URL}/rest/v1/xiaoji_messages",
                headers=headers,
                json=assistant_msg
            )

    return StreamingResponse(generate(), media_type="text/plain")
