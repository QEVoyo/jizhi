from fastapi import APIRouter, HTTPException, Query, Body, Depends
from pydantic import BaseModel
from typing import Optional
from config import settings
import httpx
import base64
from utils.xunfei_client import XunfeiClient
from utils.auth_middleware import get_current_user, verify_user_match
from logging_config import logger

logger.info("[xiaoji] router loaded")

router = APIRouter(prefix="/xiaoji", tags=["小基"])


# ===== 模型 =====

class XiaojiConfigUpdate(BaseModel):
    name: Optional[str] = None
    personality: Optional[str] = None
    voice_enabled: Optional[bool] = None
    voice_speed: Optional[int] = None
    voice_volume: Optional[int] = None
    voice_name: Optional[str] = None
    proactive_enabled: Optional[bool] = None


class TTSRequest(BaseModel):
    text: str
    speed: Optional[int] = 5
    volume: Optional[int] = 5
    pitch: Optional[int] = 5
    voice_name: Optional[str] = "xiaoyan"


class ASRRequest(BaseModel):
    audio_base64: str
    format: str = "wav"


# ===== 辅助函数 =====

from services.supabase import get_supabase_headers, get_supabase_service_headers


# ============================================================
# 1. 小基配置
# ============================================================

@router.get("/config/{user_id}")
async def get_xiaoji_config(user_id: str, current_user: str = Depends(get_current_user)):
    """获取小基配置"""
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()

    async with httpx.AsyncClient(timeout=30.0) as client:
        url = f"{settings.SUPABASE_URL}/rest/v1/xiaoji_config?user_id=eq.{user_id}"
        res = await client.get(url, headers=headers)

        if res.status_code == 200 and res.json():
            return res.json()[0]

        return {
            "user_id": user_id,
            "name": "小基",
            "personality": "warm",
            "voice_enabled": True,
            "voice_speed": 5,
            "voice_volume": 5,
            "voice_name": "xiaoyan",
            "proactive_enabled": True
        }


@router.put("/config/{user_id}")
async def update_xiaoji_config(user_id: str, data: XiaojiConfigUpdate, current_user: str = Depends(get_current_user)):
    """更新小基配置"""
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()
    update_data = {k: v for k, v in data.dict().items() if v is not None}

    async with httpx.AsyncClient(timeout=30.0) as client:
        check_url = f"{settings.SUPABASE_URL}/rest/v1/xiaoji_config?user_id=eq.{user_id}"
        check_res = await client.get(check_url, headers=headers)

        if check_res.status_code == 200 and check_res.json():
            url = f"{settings.SUPABASE_URL}/rest/v1/xiaoji_config?user_id=eq.{user_id}"
            res = await client.patch(url, headers=headers, json=update_data)
        else:
            update_data["user_id"] = user_id
            url = f"{settings.SUPABASE_URL}/rest/v1/xiaoji_config"
            res = await client.post(url, headers=headers, json=update_data)

        if res.status_code not in [200, 201, 204]:
            raise HTTPException(status_code=400, detail=f"更新失败: {res.text}")

        return {"success": True}


# ============================================================
# 2. 音色列表
# ============================================================

@router.get("/voice/list")
async def get_voice_list():
    """获取可用音色列表"""
    client = XunfeiClient()
    return {"voices": client.get_available_voices()}


# ============================================================
# 3. 语音合成（TTS）
# ============================================================

@router.post("/tts")
async def text_to_speech(data: TTSRequest):
    """文字转语音（TTS）"""
    logger.info(f"🔊 TTS 请求: {data.text[:50]}...")

    client = XunfeiClient()

    try:
        audio_data = client.get_tts_audio(
            text=data.text,
            speed=data.speed,
            volume=data.volume,
            pitch=data.pitch,
            voice_name=data.voice_name
        )

        if not audio_data:
            raise HTTPException(status_code=500, detail="语音合成失败")

        audio_base64 = base64.b64encode(audio_data).decode("utf-8")

        return {
            "success": True,
            "audio_base64": audio_base64,
            "format": "mp3"
        }

    except Exception as e:
        logger.info(f"TTS 错误: {e}")
        raise HTTPException(status_code=500, detail=f"TTS 错误: {str(e)}")


# ============================================================
# 4. 语音识别（ASR）
# ============================================================

@router.post("/asr")
async def speech_to_text(data: ASRRequest):
    """语音转文字（ASR）"""
    logger.info(f"🎤 ASR 请求: 音频长度 {len(data.audio_base64)} 字符")

    try:
        audio_bytes = base64.b64decode(data.audio_base64)
        client = XunfeiClient()
        result = client.speech_to_text(audio_bytes, data.format)

        if not result:
            raise HTTPException(status_code=500, detail="语音识别失败")

        return {"success": True, "text": result}

    except Exception as e:
        logger.info(f"ASR 错误: {e}")
        raise HTTPException(status_code=500, detail=f"ASR 错误: {str(e)}")


# ============================================================
# 5. 小基聊天记录（含搜索）
# ============================================================

@router.get("/messages/{user_id}")
async def get_xiaoji_messages(
    user_id: str,
    search: Optional[str] = Query(None),
    current_user: str = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """获取小基聊天记录（支持搜索）"""
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()

    url = f"{settings.SUPABASE_URL}/rest/v1/xiaoji_messages?user_id=eq.{user_id}&order=created_at.desc&limit={limit}&offset={offset}"

    if search:
        url += f"&content=ilike.%{search}%"

    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.get(url, headers=headers)

        if res.status_code == 200:
            return {"messages": res.json(), "total": len(res.json())}
        return {"messages": [], "total": 0}


@router.delete("/message/{message_id}")
async def delete_xiaoji_message(message_id: str, user_id: str = Query(...), current_user: str = Depends(get_current_user)):
    """删除小基消息"""
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()

    async with httpx.AsyncClient(timeout=30.0) as client:
        url = f"{settings.SUPABASE_URL}/rest/v1/xiaoji_messages?id=eq.{message_id}&user_id=eq.{user_id}"
        res = await client.delete(url, headers=headers)

        if res.status_code in [200, 204]:
            return {"success": True}
        raise HTTPException(status_code=400, detail="删除失败")


@router.delete("/messages/{user_id}")
async def clear_xiaoji_messages(user_id: str, current_user: str = Depends(get_current_user)):
    """清空小基聊天记录"""
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()

    async with httpx.AsyncClient(timeout=30.0) as client:
        url = f"{settings.SUPABASE_URL}/rest/v1/xiaoji_messages?user_id=eq.{user_id}"
        res = await client.delete(url, headers=headers)

        if res.status_code in [200, 204]:
            return {"success": True}
        raise HTTPException(status_code=400, detail="清空失败")