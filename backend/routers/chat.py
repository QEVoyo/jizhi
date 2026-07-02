import sys
from pathlib import Path

# 添加项目根目录到 sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
from ..agents.llm_client import call_llm_stream, call_llm
from config import settings
import json
import httpx

router = APIRouter(prefix="/chat", tags=["对话"])


class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]
    user_id: str
    temperature: float = 0.7
    intent: Optional[str] = "chat"  # chat | plan | generate | evaluate


class LogRequest(BaseModel):
    user_id: str
    keyword: str


@router.post("/send")
async def chat(req: ChatRequest):
    """发送消息，流式返回，支持多 Agent"""

    # 获取用户偏好（暂时用默认值）
    user_profile = {"level": "中等", "style": "喜欢例子"}

    # 根据 intent 选择 Agent
    if req.intent == "plan":
        from ..agents.planner import plan_with_history
        result = plan_with_history(
            user_profile,
            req.messages[-1].get("content", ""),
            req.messages[:-1]
        )
        return StreamingResponse(iter([result]), media_type="text/plain")

    elif req.intent == "generate":
        from ..agents.generator import generate_with_history
        result = generate_with_history(
            req.messages[-1].get("content", ""),
            user_profile,
            "",
            req.messages[:-1]
        )
        return StreamingResponse(iter([result]), media_type="text/plain")

    elif req.intent == "evaluate":
        from ..agents.evaluator import evaluate_with_history
        result = evaluate_with_history(
            req.messages[-1].get("content", ""),
            user_profile,
            req.messages[-1].get("content", ""),
            req.messages[:-1]
        )
        return StreamingResponse(iter([result]), media_type="text/plain")




    else:

        def generate():

            # 把 system 消息放在最后，确保不被覆盖

            messages_with_system = req.messages + [{"role": "system", "content": "你是基智，一个热情、博学的AI学习助手。"}]

            stream = call_llm_stream(messages_with_system, temperature=req.temperature)

            for chunk in stream:

                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        return StreamingResponse(generate(), media_type="text/plain")


@router.post("/log")
async def save_log(req: LogRequest):
    """保存学习日志"""
    from datetime import datetime

    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

    get_url = f"{settings.SUPABASE_URL}/rest/v1/learning_logs?user_id=eq.{req.user_id}&select=data"

    async with httpx.AsyncClient() as client:
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


class TitleRequest(BaseModel):
    user_id: str
    content: str
    response: str


@router.post("/title")
async def generate_title(req: TitleRequest):
    """根据对话内容生成标题"""
    from ..agents.llm_client import call_llm

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