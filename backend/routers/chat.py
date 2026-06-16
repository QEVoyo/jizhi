from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
from utils.llm_client import call_llm_stream
from config import settings
import json
import httpx

router = APIRouter(prefix="/chat", tags=["对话"])


class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]
    user_id: str
    temperature: float = 0.7


class LogRequest(BaseModel):
    user_id: str
    keyword: str


@router.post("/send")
async def chat(req: ChatRequest):
    """发送消息，流式返回"""

    def generate():
        stream = call_llm_stream(req.messages, temperature=req.temperature)
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

    # 获取现有日志
    get_url = f"{settings.SUPABASE_URL}/rest/v1/learning_logs?user_id=eq.{req.user_id}&select=data"

    async with httpx.AsyncClient() as client:
        res = await client.get(get_url, headers=headers)

        if res.status_code == 200 and res.json():
            logs = res.json()[0].get("data", [])
        else:
            logs = []

        # 添加新日志
        logs.insert(0, {
            "id": f"log_{int(datetime.now().timestamp())}",
            "keyword": req.keyword[:50],
            "date": datetime.now().strftime("%Y-%m-%d"),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        # 更新
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