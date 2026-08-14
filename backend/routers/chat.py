import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import json
import httpx
from datetime import datetime
from utils.sensitive_words import check_content_safety
from utils.auth_middleware import get_current_user, verify_user_match
from agents.planner import plan_with_history_stream
from agents.generator import generate_with_history_stream
from agents.evaluator import evaluate_with_history_stream
from agents.llm_client import call_llm_stream, call_llm
from config import settings
from logging_config import logger

router = APIRouter(prefix="/chat", tags=["对话"])


class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]
    user_id: str
    temperature: float = 0.7
    intent: Optional[str] = "chat"


class LogRequest(BaseModel):
    user_id: str
    keyword: str


class SummaryRequest(BaseModel):
    content: str
    user_id: str


class IntentRequest(BaseModel):
    text: str


class TitleRequest(BaseModel):
    user_id: str
    content: str
    response: str


class VisionRequest(BaseModel):
    user_id: str
    image_url: str
    question: str = "请描述这张图片的内容"


@router.post("/detect-intent")
async def detect_intent(req: IntentRequest):
    if not req.text or len(req.text) < 2:
        return {"intent": "chat"}

    prompt = f"""判断用户输入的意图，只输出一个词：
- plan：用户想规划学习路径、制定学习计划、问怎么学
- generate：用户想生成题目、练习题、试卷、出题
- evaluate：用户想被评估、批改、了解自己的学习水平
- chat：普通聊天、提问、咨询、闲聊

用户输入：{req.text[:300]}

只输出一个词：plan / generate / evaluate / chat"""

    try:
        result = call_llm([{"role": "user", "content": prompt}], temperature=0.1)
        intent = result.strip().lower()
        if intent not in ['plan', 'generate', 'evaluate', 'chat']:
            intent = 'chat'
        return {"intent": intent}
    except Exception as e:
        logger.info(f"意图分类失败: {e}")
        return {"intent": "chat"}


async def get_user_profile(user_id: str) -> dict:
    """查询用户真实画像，用于 Agent prompt 个性化"""
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
    }
    profile = {}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 1. 查基础信息
            profile_url = f"{settings.SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}&select=learning_stage,grade,major,learning_goal,difficulty_preference,learning_style,daily_study_time"
            profile_res = await client.get(profile_url, headers=headers)
            if profile_res.status_code == 200 and profile_res.json():
                profile = profile_res.json()[0] or {}

            # 2. 查掌握度数据
            mastery_url = f"{settings.SUPABASE_URL}/rest/v1/questions?user_id=eq.{user_id}&select=topic,mastery_score&limit=50"
            mastery_res = await client.get(mastery_url, headers=headers)
            topic_scores = {}
            if mastery_res.status_code == 200:
                for q in (mastery_res.json() or []):
                    topic = q.get("topic") or "未分类"
                    score = q.get("mastery_score", 0)
                    if topic not in topic_scores:
                        topic_scores[topic] = []
                    topic_scores[topic].append(score)
            weak = [t for t, scores in topic_scores.items() if sum(scores)/len(scores) < 50][:3]
            strong = [t for t, scores in topic_scores.items() if sum(scores)/len(scores) >= 80][:3]
    except Exception as e:
        logger.info(f"获取用户画像失败，使用默认: {e}")

    return {
        "learning_stage": profile.get("learning_stage") or "未知",
        "grade": profile.get("grade") or "未知",
        "major": profile.get("major") or "未知",
        "learning_goal": profile.get("learning_goal") or "未设置",
        "difficulty_preference": profile.get("difficulty_preference") or "适中",
        "learning_style": profile.get("learning_style") or "详细讲解",
        "daily_study_time": profile.get("daily_study_time") or "未设置",
        "weak_topics": weak,
        "strong_topics": strong,
    }


def build_system_prompt(profile: dict) -> str:
    """根据用户画像构建个性化 system prompt"""
    parts = ["你是基智，一个热情、博学的AI学习助手。"]

    # 用户背景
    if profile["learning_stage"] != "未知":
        bg = f"用户是 {profile['learning_stage']} · {profile['grade']}"
        if profile["major"] != "未知":
            bg += f" · {profile['major']}"
        parts.append(f"用户背景：{bg}。")

    # 学习偏好
    prefs = []
    if profile["learning_goal"] != "未设置":
        prefs.append(f"学习目标：{profile['learning_goal']}")
    if profile["difficulty_preference"] != "适中":
        prefs.append(f"偏好难度：{profile['difficulty_preference']}")
    if profile["learning_style"] != "详细讲解":
        prefs.append(f"讲解偏好：{profile['learning_style']}")
    if prefs:
        parts.append("学习偏好：" + "，".join(prefs) + "。")

    # 强弱项
    if profile["weak_topics"]:
        parts.append(f"薄弱知识点：{'、'.join(profile['weak_topics'])}。")
    if profile["strong_topics"]:
        parts.append(f"擅长知识点：{'、'.join(profile['strong_topics'])}。")

    # 通用规则
    parts.append("""
## 行为准则：
1. 根据用户背景和偏好调整回答的深度和风格
2. 如果用户背景未知，保持通用回答
3. 优先关联用户薄弱知识点进行引导

## ⚠️ 防幻觉原则：
1. 不确定的直接说"我不确定"
2. 不编造事实、数据或代码
3. 部分了解时明确说明范围""")

    return "\n\n".join(parts)


@router.post("/send")
async def chat(req: ChatRequest, current_user: str = Depends(get_current_user)):
    # ✅ 验证用户身份
    verify_user_match(req.user_id, current_user)
    # ✅ 内容安全过滤
    user_message = req.messages[-1].get("content", "") if req.messages else ""

    if user_message:
        safe, reason = check_content_safety(user_message)
        if not safe:
            raise HTTPException(status_code=400, detail=f"内容包含敏感信息：{reason}")

    # ✅ 从数据库查询真实用户画像
    user_profile = await get_user_profile(req.user_id)

    history = req.messages[:-1] if req.messages else []

    if req.intent == "plan":
        stream = plan_with_history_stream(user_profile, user_message, history)
        return StreamingResponse(stream_generator(stream), media_type="text/event-stream")

    elif req.intent == "generate":
        stream = generate_with_history_stream(user_message, user_profile, history)
        return StreamingResponse(stream_generator(stream), media_type="text/event-stream")

    elif req.intent == "evaluate":
        stream = evaluate_with_history_stream(user_message, user_profile, user_message, history)
        return StreamingResponse(stream_generator(stream), media_type="text/event-stream")

    else:
        system_content = build_system_prompt(user_profile)
        messages_with_system = req.messages + [{"role": "system", "content": system_content}]
        stream = call_llm_stream(messages_with_system, temperature=req.temperature)
        return StreamingResponse(stream_generator(stream), media_type="text/event-stream")


def stream_generator(stream):
    for chunk in stream:
        yield chunk

def doubao_stream_generator(stream):
    """专门解析豆包（VolcEngine）流式响应的生成器（逐字追加版）"""
    for line in stream:
        if line:
            if line.startswith("data:") and line != "data: [DONE]":
                try:
                    data = json.loads(line[5:])
                    if "choices" in data and len(data["choices"]) > 0:
                        delta = data["choices"][0].get("delta", {})
                        if "content" in delta:
                            # 豆包一个 token 是单个字或词，直接原样推送
                            yield delta["content"]
                except Exception:
                    continue


@router.post("/log")
async def save_log(req: LogRequest, current_user: str = Depends(get_current_user)):
    verify_user_match(req.user_id, current_user)
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        get_url = f"{settings.SUPABASE_URL}/rest/v1/learning_logs?user_id=eq.{req.user_id}&select=data"
        res = await client.get(get_url, headers=headers)

        if res.status_code == 200 and res.json():
            logs = res.json()[0].get("data", [])
        else:
            logs = []

        logs.insert(0, {
            "id": f"log_{int(datetime.now().timestamp())}",
            "keyword": req.keyword[:50],
            "date": datetime.now().strftime("%Y-%m-%d"),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        if res.status_code == 200 and res.json():
            update_url = f"{settings.SUPABASE_URL}/rest/v1/learning_logs?user_id=eq.{req.user_id}"
            await client.patch(update_url, headers=headers, json={"data": logs})
        else:
            insert_url = f"{settings.SUPABASE_URL}/rest/v1/learning_logs"
            await client.post(insert_url, headers=headers, json={
                "user_id": req.user_id,
                "data": logs
            })

    return {"success": True}


@router.post("/summary")
async def extract_summary(req: SummaryRequest, current_user: str = Depends(get_current_user)):
    verify_user_match(req.user_id, current_user)
    prompt = f"""请将以下内容的核心要点提炼为**极简标签**（不超过10个字），用于记录用户的学习日志。只输出标签，不要其他内容。

内容：
{req.content[:1500]}

只输出极简标签（不超过10个字）："""

    try:
        summary = call_llm([{"role": "user", "content": prompt}], temperature=0.3)
        summary = summary.strip().strip('"').strip('"')
        if len(summary) > 15:
            summary = summary[:15]
        return {"summary": summary}
    except Exception as e:
        logger.info(f"提取摘要失败: {e}")
        fallback = req.content.replace('\n', ' ').strip()[:15]
        return {"summary": fallback}


@router.post("/title")
async def generate_title(req: TitleRequest, current_user: str = Depends(get_current_user)):
    verify_user_match(req.user_id, current_user)
    prompt = f"""请根据以下对话内容，生成一个简短的标题（不超过15个字）：

用户问题：{req.content[:200]}
AI回答：{req.response[:200]}

只输出标题，不要有其他内容。"""

    try:
        title = call_llm([{"role": "user", "content": prompt}], temperature=0.5)
        title = title.strip().strip('"').strip('"')
        if len(title) > 20:
            title = title[:20]
        return {"title": title}
    except Exception:
        title = req.content[:20] + ('...' if len(req.content) > 20 else '')
        return {"title": title}


@router.post("/vision")
async def handle_vision(req: VisionRequest, current_user: str = Depends(get_current_user)):
    verify_user_match(req.user_id, current_user)
    """豆包多模态图片理解 - 真流式输出"""
    from utils.volc_client import VolcClient

    client = VolcClient()
    stream = client.vision_stream(req.image_url, req.question)

    return StreamingResponse(
        doubao_stream_generator(stream),  # 👈 换用豆包专用解析生成器
        media_type="text/event-stream"
    )


class AdviceRequest(BaseModel):
    prompt: str
    user_id: str


@router.post("/advice")
async def generate_advice(req: AdviceRequest, current_user: str = Depends(get_current_user)):
    verify_user_match(req.user_id, current_user)
    from agents.llm_client import call_llm
    try:
        result = call_llm([{"role": "user", "content": req.prompt}], temperature=0.5)
        return {"advice": result}
    except Exception as e:
        logger.info(f"生成建议失败: {e}")
        return {"advice": "生成建议失败，请稍后重试。"}