import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import json
import httpx
from datetime import datetime

# 导入流式版本
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


@router.post("/detect-intent")
async def detect_intent(req: IntentRequest):
    """用 AI 判断用户意图（plan / generate / evaluate / chat）"""
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
    """发送消息，流式返回，支持多 Agent"""
    user_profile = {"level": "中等", "style": "喜欢例子"}

    # 获取用户最后一条消息
    user_message = req.messages[-1].get("content", "") if req.messages else ""
    history = req.messages[:-1] if req.messages else []

    # 根据 intent 选择 Agent，统一返回流式
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
        # chat 模式
        messages_with_system = req.messages + [{"role": "system", "content": "你是基智，一个热情、博学的AI学习助手。"}]
        stream = call_llm_stream(messages_with_system, temperature=req.temperature)
        return StreamingResponse(stream_generator(stream), media_type="text/plain")


def stream_generator(stream):
    """将 OpenAI 流式响应转换为纯文本流"""
    for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


@router.post("/log")
async def save_log(req: LogRequest):
    """保存学习日志"""
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
    """提取生成内容的极简标签（不超过10个字）"""
    prompt = f"""请将以下内容的核心要点提炼为**极简标签**（不超过10个字），用于记录用户的学习日志。只输出标签，不要其他内容。

内容：
{req.content[:1500]}

示例：
- 用户问了一道高数题 → "高数题"
- 用户让生成英语题 → "英语题"  
- 用户学了微积分 → "微积分"
- 用户做了编程题 → "编程题"
- 用户问旋转体体积 → "旋转体体积"

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
    """根据对话内容生成标题"""
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

class AdviceRequest(BaseModel):
    prompt: str
    user_id: str


@router.post("/advice")
async def generate_advice(req: AdviceRequest):
    """生成学习建议"""
    from agents.llm_client import call_llm
    try:
        result = call_llm([{"role": "user", "content": req.prompt}], temperature=0.5)
        return {"advice": result}
    except Exception as e:
        print(f"生成建议失败: {e}")
        return {"advice": "生成建议失败，请稍后重试。"}