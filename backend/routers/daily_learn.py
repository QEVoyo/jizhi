# -*- coding: utf-8 -*-
"""每日学习推荐 · 独立学习页的数据层（2026-10-08）

一条 `learning.daily_rec` 消息 = 一套**可直接执行的任务**（学习内容 + 题目 + 视频），
见 `message_center_design.md` §六。首页「小基推荐」卡片和消息中心那条
**点进的是同一个页面**（`/daily-learn`），所以取数与进度都收在这一处 ——
两边各写一套的话，进度判定迟早会分叉。

payload 形状（存在 `notifications.payload`，**列早就有了，无需 SQL 迁移**）：

    {
      "content":   {title, kp_id, minutes, basis, sections?},
      "questions": [{qid, stem, type, difficulty, syllabus_id}],
      "video":     {video_id, title, duration, duration_sec, state} | null,
      "progress":  {content: bool, questions: bool, video: bool}
    }

`content.sections`（正文）**不在发送时生成** —— 那要多烧一次 LLM，而大多数用户
当天未必会点开。首次打开时按需生成并**写回这里**，之后直出。

⚠️ `questions[].syllabus_id` 是**必须的**：题库 18,711 题里 **497 个 id 横跨多库**
（见 `local_question_bank.find_question_unique`），做题端靠它定位题目 ——
不带就会跨库猜，**拿 A 科目的题判 B 科目的分**。

⚠️ 与 §六 的差异：§六 原设计是「详情弹层即执行面板，不是跳出去做」。
用户 2026-10-08 明确改成**独立全屏页**，两个入口都跳这里。弹层那边只留预览。
"""
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import APIRouter, Body, Depends, HTTPException, Query

import local_question_bank
from config import settings
from logging_config import logger
from services.supabase import get_supabase_service_headers
from utils.auth_middleware import get_current_user, verify_user_match

router = APIRouter(prefix="/daily-learn", tags=["每日学习推荐"])

REC_TYPE = "learning.daily_rec"
BLOCKS = ("content", "questions", "video")


# ============================================================
# 小工具（与 message_center.py 同一套写法）
# ============================================================
def _h() -> dict:
    return get_supabase_service_headers()


def _base() -> str:
    return f"{settings.SUPABASE_URL}/rest/v1/notifications"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ok(status: int) -> bool:
    """⚠️ PostgREST 超过一页时返回 **206** 而不是 200 —— 只认 200 会把
    「有数据」读成「失败」。09-30 在 /admin/users 上踩过一次，这里从一开始就认。"""
    return status in (200, 204, 206)


def _rows(res: httpx.Response) -> list:
    try:
        data = res.json()
    except Exception:                                          # noqa: BLE001
        return []
    return data if isinstance(data, list) else []


async def _fetch(message_id: str, user_id: str) -> dict:
    """取一条 daily_rec 并校验归属；取不到抛 404。"""
    q = (f"{_base()}?id=eq.{message_id}&user_id=eq.{user_id}&type=eq.{REC_TYPE}"
         f"&select=id,payload,title,content,link,is_read,created_at,handled_at&limit=1")
    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.get(q, headers=_h())
    if not _ok(res.status_code):
        raise HTTPException(status_code=502, detail=f"读取推荐失败：{res.text[:200]}")
    rows = _rows(res)
    if not rows:
        raise HTTPException(status_code=404, detail="没有找到这条学习推荐")
    return rows[0]


# ============================================================
# 1. 取推荐
# ============================================================
async def _latest_row(user_id: str) -> Optional[dict]:
    q = (f"{_base()}?user_id=eq.{user_id}&type=eq.{REC_TYPE}"
         f"&order=created_at.desc&limit=1")
    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.get(q, headers=_h())
    if not _ok(res.status_code):
        raise HTTPException(status_code=502, detail=f"读取推荐失败：{res.text[:200]}")
    rows = _rows(res)
    return rows[0] if rows else None


@router.get("/latest")
async def latest(user_id: str = Query(...),
                 current_user: str = Depends(get_current_user)):
    """我最新的一条每日推荐。

    首页卡片跳的是**不带 id** 的 `/daily-learn` —— 因为 `notify()` 是
    「先 INSERT 再返回 row id」，link 在插入那一刻就要定，拿不到自己的 id。
    没有推荐时返回 `None`（**不是 404**）：卡片要把「今天还没有」显示成空态，
    而不是弹一个错误。
    """
    verify_user_match(user_id, current_user)
    return await _latest_row(user_id)


@router.post("/generate")
async def generate_today(user_id: str = Query(...),
                         current_user: str = Depends(get_current_user)):
    """手动生成今天的推荐 —— 首页卡片空态里那个「生成今日推荐」按钮。

    `force=True` 只忽略**发送时间**（想现在看就现在生成），
    **去重照旧生效**：今天已经有了就直接把它返回，不会多出一条。
    所以这个按钮点几次都安全 —— 用户要的是「看到今天的推荐」，
    不是「每点一次多一条」。
    """
    verify_user_match(user_id, current_user)
    from services.daily_generator import run_daily_recommendation

    res = await run_daily_recommendation(user_id, force=True)
    return {
        "success": True,
        "generated": res.get("generated", 0),
        # detail 里是状态码计数：sent / skipped_done / skipped_off / no_content
        "detail": res.get("detail") or {},
        "recommendation": await _latest_row(user_id),
    }


@router.get("/{message_id}")
async def detail(message_id: str, user_id: str = Query(...),
                 current_user: str = Depends(get_current_user)):
    """指定某一条（从消息中心点旧消息进来时用）。"""
    verify_user_match(user_id, current_user)
    return await _fetch(message_id, user_id)


# ============================================================
# 2. 题目：取完整题面
# ============================================================
async def _from_generated(qid: str) -> Optional[dict]:
    """从 Supabase `questions` 表取 AI 生成题，并适配成题库形状。

    ⚠️ 复用 `subject_plan._adapt_generated_question` 而不是在这里再写一遍
    —— 形状适配（`title → content.stem` 等）是这个项目栽过跟头的地方，
    写两份必然改一处漏一处。
    """
    if not qid:
        return None
    from routers.subject_plan import _adapt_generated_question
    url = f"{settings.SUPABASE_URL}/rest/v1/questions?id=eq.{qid}&limit=1"
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            res = await client.get(url, headers=_h())
    except Exception as e:                                      # noqa: BLE001
        logger.warning(f"[daily-learn] 取生成题异常 {qid}: {e}")
        return None
    rows = _rows(res) if _ok(res.status_code) else []
    return _adapt_generated_question(rows[0]) if rows else None


@router.get("/{message_id}/questions")
async def questions(message_id: str, user_id: str = Query(...),
                    current_user: str = Depends(get_current_user)):
    """取完整题面 —— payload 里只存了 120 字 `stem` 摘要（列表要显示）。

    ⚠️ **按每道题自己的 `syllabus_id` 取**，不能用 `subject_plan` 的
    `by-ids`：那个只收**一个** syllabus_id，而 `score_by_kp` 是跨库扫的，
    命中的题可能来自不同考纲。

    取不到的题**不丢**，标记 `missing: true` 返回 —— 一道题挂了不该让
    整条推荐变成白屏。
    """
    verify_user_match(user_id, current_user)
    msg = await _fetch(message_id, user_id)
    items = (msg.get("payload") or {}).get("questions") or []

    out = []
    for it in items:
        qid = it.get("qid")
        sid = it.get("syllabus_id") or ""
        q = None
        if sid:
            got = local_question_bank.get_by_ids(sid, [qid])
            q = got[0] if got else None
        if not q:
            q = await _from_generated(qid)
        if not q:
            logger.warning(f"[daily-learn] 题面取不到 qid={qid} sid={sid}")
            out.append({**it, "missing": True})
            continue
        out.append({**q, "qid": qid, "syllabus_id": sid})
    return {"message_id": message_id, "questions": out}


# ============================================================
# 3. 学习内容：按需生成 + 幂等缓存
# ============================================================
def _extract_json(raw: str) -> Optional[dict]:
    """括号计数法提 JSON。

    正文很长，模型很可能在前后带说明文字、甚至被截断 —— 简单的
    `re.search(r'\\{.*\\}')` 遇到嵌套或截断就废（`learning_plan.py` 同款处理）。
    """
    if not raw:
        return None
    start = raw.find("{")
    if start < 0:
        return None
    depth, in_str, esc, end = 0, False, False, -1
    for i in range(start, len(raw)):
        ch = raw[i]
        if esc:
            esc = False
            continue
        if ch == "\\":
            esc = True
            continue
        if ch == '"':
            in_str = not in_str
            continue
        if in_str:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    if end <= 0:
        return None
    try:
        import json
        return json.loads(raw[start:end])
    except Exception as e:                                      # noqa: BLE001
        logger.warning(f"[daily-learn] 正文 JSON 解析失败: {e}")
        return None


@router.post("/{message_id}/content")
async def content(message_id: str, user_id: str = Query(...),
                  current_user: str = Depends(get_current_user)):
    """生成（或直接返回）这一天的学习正文。

    **幂等**：`payload.content.sections` 已存在就直接返回，不再烧一次 LLM。
    这很重要 —— 每日推荐**没有任务行**可以当缓存载体（学科计划缓存在
    `plan_daily_tasks.learning_content`、自定义计划在 `learning_tasks.lesson_content`，
    推荐两者都没有），只能回写进 payload 自己。

    ⚠️ 并发打开会各生成一次（读-改-写没有加锁）。代价是偶尔多烧一次 LLM，
    换来的是不需要为它引入锁 —— 可以接受，但知道有这回事。
    """
    verify_user_match(user_id, current_user)
    msg = await _fetch(message_id, user_id)
    payload = msg.get("payload") or {}
    meta = payload.get("content") or {}

    if meta.get("sections"):
        return {"message_id": message_id, "topic": meta.get("title"),
                "lesson": meta, "cached": True}

    topic = (meta.get("title") or "").strip()
    if not topic:
        raise HTTPException(status_code=400, detail="这条推荐没有知识点，无法生成正文")

    basis = meta.get("basis") or ""
    prompt = f"""你是一位擅长把复杂东西讲明白的老师。请为下面这个学习主题写一份**详细的教学正文**。

主题：{topic}
这份内容为什么推荐给他：{basis or '（未说明）'}

【最重要的一条】这是给学生**自学用的教学正文**，不是知识点提纲。
要求：
- 分 3~6 个小节，**每节都要有完整的讲解段落**，把「是什么、为什么、怎么用」讲透
- **必须举具体例子**，例子要展开算/展开讲，不能只写「例如……」
- 不要用「本文将介绍」「综上所述」这类套话，直接讲内容
- 不要写成 bullet 要点列表 —— 那正是「概述知识点」，是我们要避免的

返回严格 JSON：
{{
  "summary": "一句话说明这份正文讲什么（40字内）",
  "sections": [
    {{"heading": "小节标题", "body": "这一节的完整讲解正文（可以很长，段落清晰）", "example": "这一节的例子（展开写的，没有就留空字符串）"}}
  ],
  "key_points": ["学完必须记住的要点", "..."],
  "common_mistakes": ["常见错误及为什么错", "..."]
}}

只返回 JSON，不要额外文字。"""

    raw = ""
    try:
        from agents.qwen_client import call_qwen
        raw = call_qwen(
            [{"role": "system", "content": "你是教学正文写作者，只返回 JSON。"},
             {"role": "user", "content": prompt}],
            model=getattr(settings, "QWEN_CHAT_MODEL", "qwen-flash"),
            temperature=0.6)
    except Exception as e:                                      # noqa: BLE001
        logger.info(f"[daily-learn] 正文 qwen 失败，回退 DeepSeek: {e}")
        try:
            from agents.llm_client import call_llm
            raw = call_llm(
                [{"role": "system", "content": "你是教学正文写作者，只返回 JSON。"},
                 {"role": "user", "content": prompt}],
                temperature=0.6)
        except Exception as e2:                                 # noqa: BLE001
            logger.warning(f"[daily-learn] 正文 DeepSeek 也失败: {e2}")

    lesson = _extract_json(raw)
    if not lesson:
        raise HTTPException(status_code=502, detail="学习正文生成失败，请稍后重试")

    # 回写 payload（读-改-写：把 sections 并进原来的 content 块）
    meta.update(lesson)
    payload["content"] = meta
    async with httpx.AsyncClient(timeout=20.0) as client:
        up = await client.patch(f"{_base()}?id=eq.{message_id}&user_id=eq.{user_id}",
                                headers={**_h(), "Content-Type": "application/json"},
                                json={"payload": payload})
    if up.status_code >= 300:
        # 缓存写不进去不影响这次阅读，但要说出来 —— 否则下次又白烧一次钱
        logger.warning(f"[daily-learn] 正文缓存失败 [{up.status_code}]: {up.text[:200]}")

    return {"message_id": message_id, "topic": topic, "lesson": meta, "cached": False}


# ============================================================
# 4. 进度：哪一块做完了
# ============================================================
@router.put("/{message_id}/progress")
async def progress(message_id: str,
                   block: str = Body(..., embed=True),
                   user_id: str = Query(...),
                   current_user: str = Depends(get_current_user)):
    """标记某一块做完（① 内容读完 / ② 题做完 / ③ 视频看完）。

    三块都完成 → 整条置 `handled_at`（列已存在）。

    **第一次动任何一块就整条已读** —— 与 §六 的「开始做任意一块 → 整条已读；
    但没做完不算完成」一致。已读和完成是两件事，别混。
    """
    if block not in BLOCKS:
        raise HTTPException(status_code=400,
                            detail=f"block 应为 {'/'.join(BLOCKS)} 之一")
    verify_user_match(user_id, current_user)
    msg = await _fetch(message_id, user_id)

    payload = msg.get("payload") or {}
    prog = {b: False for b in BLOCKS}
    prog.update(payload.get("progress") or {})
    prog[block] = True
    payload["progress"] = prog

    patch = {"payload": payload}
    if not msg.get("is_read"):
        patch["is_read"] = True
        patch["read_at"] = _now()
    if all(prog.values()) and not msg.get("handled_at"):
        patch["handled_at"] = _now()

    async with httpx.AsyncClient(timeout=20.0) as client:
        res = await client.patch(f"{_base()}?id=eq.{message_id}&user_id=eq.{user_id}",
                                 headers={**_h(), "Content-Type": "application/json"},
                                 json=patch)
    if not _ok(res.status_code):
        raise HTTPException(status_code=502, detail=f"更新进度失败：{res.text[:200]}")

    return {"success": True, "progress": prog, "all_done": all(prog.values())}
