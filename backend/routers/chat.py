import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import json
import httpx
from datetime import datetime

from agents.planner import plan_with_history_stream
from agents.generator import generate_with_history_stream
from agents.evaluator import evaluate_with_history_stream
from agents.llm_client import call_llm_stream, call_llm
from config import settings

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
        print(f"意图分类失败: {e}")
        return {"intent": "chat"}


@router.post("/send")
async def chat(req: ChatRequest):
    user_profile = {"level": "中等", "style": "喜欢例子"}

    user_message = req.messages[-1].get("content", "") if req.messages else ""
    history = req.messages[:-1] if req.messages else []

    if req.intent == "plan":
        stream = plan_with_history_stream(user_profile, user_message, history)
        return StreamingResponse(stream_generator(stream), media_type="text/plain")

    elif req.intent == "generate":
        stream = generate_with_history_stream(user_message, user_profile, history)
        return StreamingResponse(stream_generator(stream), media_type="text/plain")

    elif req.intent == "evaluate":
        stream = evaluate_with_history_stream(user_message, user_profile, user_message, history)
        return StreamingResponse(stream_generator(stream), media_type="text/plain")

    else:
        messages_with_system = req.messages + [{"role": "system", "content": "你是基智，一个热情、博学的AI学习助手。"}]
        stream = call_llm_stream(messages_with_system, temperature=req.temperature)
        return StreamingResponse(stream_generator(stream), media_type="text/plain")


def stream_generator(stream):
    for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

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
                except:
                    continue


@router.post("/log")
async def save_log(req: LogRequest):
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
async def extract_summary(req: SummaryRequest):
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
        print(f"提取摘要失败: {e}")
        fallback = req.content.replace('\n', ' ').strip()[:15]
        return {"summary": fallback}


@router.post("/title")
async def generate_title(req: TitleRequest):
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
    except:
        title = req.content[:20] + ('...' if len(req.content) > 20 else '')
        return {"title": title}


@router.post("/vision")
async def handle_vision(req: VisionRequest):
    """豆包多模态图片理解 - 真流式输出"""
    from utils.volc_client import VolcClient

    client = VolcClient()
    stream = client.vision_stream(req.image_url, req.question)

    return StreamingResponse(
        doubao_stream_generator(stream),  # 👈 换用豆包专用解析生成器
        media_type="text/plain"
    )


class AdviceRequest(BaseModel):
    prompt: str
    user_id: str


@router.post("/advice")
async def generate_advice(req: AdviceRequest):
    from agents.llm_client import call_llm
    try:
        result = call_llm([{"role": "user", "content": req.prompt}], temperature=0.5)
        return {"advice": result}
    except Exception as e:
        print(f"生成建议失败: {e}")
        return {"advice": "生成建议失败，请稍后重试。"}