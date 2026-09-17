from fastapi import APIRouter, HTTPException, Query, Body, Depends, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional
from config import settings
import httpx
import base64
import asyncio
import json
import jwt
import time
import uuid
from datetime import datetime, timedelta, timezone
from utils.xunfei_client import XunfeiClient
from utils.qwen_tts_client import get_tts_audio, get_available_voices, QWEN_DEFAULT_VOICE, _strip_emoji
from utils.auth_middleware import get_current_user, verify_user_match
from services import xiaoji_persona
from logging_config import logger


async def _ws_connect(*args, **kwargs):
    """连接下游 WebSocket（讯飞 ASR / 千问 realtime）。

    websockets 是可选依赖，只被语音识别与语音通话用到。延迟导入，
    缺这个包时那两个功能不可用，但不该拖垮整个服务启动。
    """
    try:
        from websockets.asyncio.client import connect
    except ImportError as e:
        raise RuntimeError(
            "未安装 websockets（pip install 'websockets>=13'），语音识别与语音通话不可用"
        ) from e
    return await connect(*args, **kwargs)

logger.info("[xiaoji] router loaded")

router = APIRouter(prefix="/xiaoji", tags=["小基"])

# 北京时间（UTC+8）：使用日志的时间展示/分桶统一按北京时间，与用户所在地一致
BEIJING = timezone(timedelta(hours=8))


def _to_beijing_iso(iso: str) -> str:
    """Supabase timestamptz 字符串 → 北京时间 ISO（带 +08:00），解析失败原样返回"""
    try:
        dt = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
        return dt.astimezone(BEIJING).isoformat()
    except (ValueError, AttributeError):
        return iso


def _beijing_date(iso: str) -> str:
    """时间戳 → 北京日期 YYYY-MM-DD（用于按天统计），解析失败退回前 10 位"""
    try:
        dt = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
        return dt.astimezone(BEIJING).strftime("%Y-%m-%d")
    except (ValueError, AttributeError):
        return str(iso)[:10]


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
    voice_name: Optional[str] = "longanqian"


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
            "voice_name": "longanqian",
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
    """获取可用音色列表（千问音色，TTS 与语音通话共用）"""
    return {"voices": get_available_voices()}


# ============================================================
# 2.5 小基页侧栏数据：每日推荐 + 学习关心统计
# ============================================================

@router.get("/daily/{user_id}")
async def get_xiaoji_daily(user_id: str, current_user: str = Depends(get_current_user)):
    """小基页左右侧栏数据：
    - recommendation：最新一条每日推荐通知（daily_rec，定时任务生成，存 notifications 表）
    - stats：近 7 天学习天数 / 本周做题数 / 词条本（总数/已掌握/薄弱）
    三查询并发（gather），任何一项失败不拖垮整体"""
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()
    since = (datetime.now(BEIJING) - timedelta(days=7)).strftime("%Y-%m-%d")

    rec_url = (
        f"{settings.SUPABASE_URL}/rest/v1/notifications"
        f"?user_id=eq.{user_id}&type=eq.daily_rec&order=created_at.desc&limit=1"
    )
    records_url = (
        f"{settings.SUPABASE_URL}/rest/v1/question_records"
        f"?user_id=eq.{user_id}&select=created_at&created_at=gte.{since}&limit=2000"
    )
    vocab_url = (
        f"{settings.SUPABASE_URL}/rest/v1/word_mastery"
        f"?user_id=eq.{user_id}&select=mastery_score&limit=2000"
    )
    calls_url = (
        f"{settings.SUPABASE_URL}/rest/v1/xiaoji_call_logs"
        f"?user_id=eq.{user_id}&order=started_at.desc&limit=100"
    )
    chat_url = (
        f"{settings.SUPABASE_URL}/rest/v1/xiaoji_messages"
        f"?user_id=eq.{user_id}&kind=eq.chat&select=id&limit=2000"
    )
    tools_url = (
        f"{settings.SUPABASE_URL}/rest/v1/user_actions"
        f"?user_id=eq.{user_id}&action_type=eq.xiaoji_tool&select=metadata,action_at"
        f"&action_at=gte.{since}&limit=2000"
    )

    async with httpx.AsyncClient(timeout=20.0) as client:
        rec_res, records_res, vocab_res, calls_res, chat_res, tools_res = await asyncio.gather(
            client.get(rec_url, headers=headers),
            client.get(records_url, headers=headers),
            client.get(vocab_url, headers=headers),
            client.get(calls_url, headers=headers),
            client.get(chat_url, headers=headers),
            client.get(tools_url, headers=headers),
            return_exceptions=True,
        )

        recommendation = None
        if isinstance(rec_res, httpx.Response) and rec_res.status_code == 200:
            rows = rec_res.json()
            if rows:
                r = rows[0]
                recommendation = {
                    "title": r.get("title"),
                    "content": r.get("content"),
                    "action_label": r.get("action_label"),
                    "action_link": r.get("action_link"),
                }

        records = []
        if isinstance(records_res, httpx.Response) and records_res.status_code == 200:
            records = records_res.json()
        # 按北京时间切日期（UTC 直接切前 10 位会把凌晨 0-8 点的记录算到前一天）
        days = {_beijing_date(r.get("created_at", "")) for r in records}

        vocab = []
        if isinstance(vocab_res, httpx.Response) and vocab_res.status_code == 200:
            vocab = vocab_res.json()
        mastered = sum(1 for v in vocab if (v.get("mastery_score") or 0) >= 80)
        weak = sum(1 for v in vocab if (v.get("mastery_score") or 0) < 60)

        # ===== 使用日志：通话次数/时长/最近通话/时段分布/聊天条数 =====
        calls = []
        if isinstance(calls_res, httpx.Response) and calls_res.status_code == 200:
            calls = calls_res.json()
        chat_count = 0
        if isinstance(chat_res, httpx.Response) and chat_res.status_code == 200:
            chat_count = len(chat_res.json())

        buckets = {"深夜(0-6点)": 0, "上午(6-12点)": 0, "下午(12-18点)": 0, "晚上(18-24点)": 0}
        for c in calls:
            try:
                # 时段按北京时间分桶（2026-08-26 修复：原按 UTC 小时，北京 19 点会被分进「上午」）
                h = datetime.fromisoformat(
                    c.get("started_at", "").replace("Z", "+00:00")
                ).astimezone(BEIJING).hour
            except (ValueError, AttributeError):
                continue
            if h < 6:
                buckets["深夜(0-6点)"] += 1
            elif h < 12:
                buckets["上午(6-12点)"] += 1
            elif h < 18:
                buckets["下午(12-18点)"] += 1
            else:
                buckets["晚上(18-24点)"] += 1
        bucket_items = []
        for label, n in buckets.items():
            bucket_items.append({
                "label": label,
                "value": n,
                "pct": round(n / len(calls) * 100) if calls else 0,
            })

        # 全量下发（查询层已 limit=100）：前端记录区自由伸缩 + 内部滚动，
        # 不再固定 5 条（2026-09-02 用户反馈「应该自适应」）
        recent_calls = [{
            "id": c.get("id"),
            # 下发北京时间（+08:00）：前端显示不再依赖浏览器时区
            "started_at": _to_beijing_iso(c.get("started_at") or ""),
            "duration_seconds": c.get("duration_seconds") or 0,
            "turns": c.get("turns") or 0,
        } for c in calls]

        # ===== 工具使用（打卡/倒计时/计时器，2026-08-25 使用数据交给小基） =====
        tool_actions = []
        if isinstance(tools_res, httpx.Response) and tools_res.status_code == 200:
            tool_actions = tools_res.json()
        tool_counts = {"checkin": 0, "countdown": 0, "timer": 0, "stopwatch": 0}
        for a in tool_actions:
            meta = a.get("metadata") or {}
            if isinstance(meta, str):
                try:
                    meta = json.loads(meta)
                except (ValueError, TypeError):
                    meta = {}
            t = meta.get("tool")
            if t in tool_counts:
                tool_counts[t] += 1

        return {
            "recommendation": recommendation,
            "stats": {
                "study_days_7d": len(days),
                "week_questions": len(records),
                "vocab_total": len(vocab),
                "vocab_mastered": mastered,
                "vocab_weak": weak,
            },
            "logs": {
                "call_count": len(calls),
                "call_total_seconds": sum(c.get("duration_seconds") or 0 for c in calls),
                "recent_calls": recent_calls,
                "time_buckets": bucket_items,
                "chat_count": chat_count,
                "tool_usage_7d": len(tool_actions),
                "tool_counts": tool_counts,
            }
        }


# ============================================================
# 3. 语音合成（TTS，千问 qwen-audio-3.0-tts-plus）
# ============================================================

@router.post("/tts")
async def text_to_speech(data: TTSRequest):
    """文字转语音（TTS）"""
    logger.info(f"🔊 TTS 请求: {data.text[:50]}...")

    try:
        audio_data = get_tts_audio(
            text=data.text,
            voice=data.voice_name,
            speed=data.speed,
            volume=data.volume,
            pitch=data.pitch,
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
        # PostgREST 模糊匹配通配符是 *（会转成 SQL 的 %），不能用裸 %
        url += f"&content=ilike.*{search}*"

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


# ============================================================
# 6. 实时语音听写（浏览器 WS ↔ 讯飞 iat WS 中转）
# ============================================================

@router.websocket("/asr-ws")
async def xiaoji_asr_websocket(websocket: WebSocket):
    """
    实时语音听写：浏览器持续发送 16k PCM 帧（{"status": 0|2, "audio": base64}），
    后端中转给讯飞 iat 流式识别，实时回传 {"text": 累计文本, "done": 是否最终}。
    """
    await websocket.accept()

    client = XunfeiClient()
    business = {
        "domain": "iat",
        "language": "zh_cn",
        "accent": "mandarin",
        "dwa": "wpgs",
        "ptt": 0,
        "aue": "raw",
        "vad_eos": 10000,   # 服务端断句阈值调大：自动结束由前端静音检测主导，避免文本重置
    }

    xf_ws = None
    try:
        xf_ws = await _ws_connect(client._ws_url(client.IAT_HOST, "/v2/iat"))
        await xf_ws.send(json.dumps({
            "common": {"app_id": client.appid},
            "business": business,
            "data": {"status": 0, "format": "audio/L16;rate=16000", "encoding": "raw", "audio": ""},
        }))

        browser_gone = False

        async def forward():
            """浏览器 → 讯飞"""
            nonlocal browser_gone
            while True:
                try:
                    msg = await websocket.receive_json()
                except Exception:
                    browser_gone = True
                    return
                await xf_ws.send(json.dumps({
                    "data": {
                        "status": int(msg.get("status", 0)),
                        "format": "audio/L16;rate=16000",
                        "encoding": "raw",
                        "audio": msg.get("audio", ""),
                    }
                }))
                if msg.get("status") == 2:
                    return

        async def relay():
            """讯飞 → 浏览器：apd/rpl 帧实时回传累计文本；data.status=2（客户端收尾后）回传最终文本 + done"""
            last_text = ""
            while True:
                try:
                    raw = await xf_ws.recv()
                except Exception:
                    return
                if isinstance(raw, bytes):
                    continue
                try:
                    ctrl = json.loads(raw)
                except (ValueError, TypeError):
                    continue
                if ctrl.get("code") not in (0, None):
                    try:
                        await websocket.send_json({"error": ctrl.get("message") or "识别失败"})
                    except Exception:
                        pass
                    return
                data = ctrl.get("data") or {}
                result = data.get("result") or {}
                pgs = result.get("pgs", "")
                text = "".join(
                    c.get("w", "")
                    for item in (result.get("ws") or [])
                    for c in (item.get("cw") or [])
                )
                if text:
                    last_text = text
                    try:
                        await websocket.send_json({"text": text, "done": False})
                    except Exception:
                        return
                if data.get("status") == 2:
                    try:
                        await websocket.send_json({"text": last_text, "done": True})
                    except Exception:
                        pass
                    return

        forward_task = asyncio.create_task(forward())
        relay_task = asyncio.create_task(relay())
        # 浏览器发完 status=2 后，必须继续等 relay 回传讯飞最终结果再关闭；
        # 浏览器中途断开则立即停 relay
        await forward_task
        if browser_gone:
            relay_task.cancel()
        else:
            try:
                await asyncio.wait_for(relay_task, timeout=8)
            except (asyncio.TimeoutError, Exception):
                relay_task.cancel()

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.info(f"[xiaoji] ASR-WS 异常: {e}")
        try:
            await websocket.send_json({"error": "语音服务异常，请重试"})
        except Exception:
            pass
    finally:
        if xf_ws is not None:
            try:
                await xf_ws.close()
            except Exception:
                pass
        try:
            await websocket.close()
        except Exception:
            pass


# ============================================================
# 7. 语音通话（千问 Qwen-Audio-3.0-Realtime 实时语音对话，2026-08-25 新增）
#    与聊天页分离的独立通话界面：浏览器 ↔ 本端点（鉴权/人设/落库）↔ 千问 realtime WS
#    音频进 16k PCM16 → 千问 server_vad 断句/自动打断 → 音频出 24k PCM16 回传播放
# ============================================================

QWEN_REALTIME_URL = "wss://dashscope.aliyuncs.com/api-ws/v1/realtime?model=qwen-audio-3.0-realtime-plus"
QWEN_CALL_MAX_SECONDS = 1800   # 单次通话最长 30 分钟，防僵尸连接


def _build_call_instructions(xiaoji_name: str, personality: str, nickname: str) -> str:
    """语音通话人设（与聊天页 system prompt 同源，加语音场景要求）"""
    style = xiaoji_persona.style_of(personality)
    return (
        f"你是「{xiaoji_name}」，一个{style}的AI学习伙伴，用户「{nickname}」正在与你进行实时语音通话。\n"
        "性格：耐心倾听，不打断用户；擅长鼓励和引导，不直接给答案。\n"
        "语音通话要求：\n"
        "- 回答必须简短口语化：一般不超过 3 句，每句不超过 25 个字\n"
        "- 不要使用 Markdown、列表、表情符号，不念英文缩写\n"
        "- 像朋友打电话一样自然，开头不要每次都说「喂」\n"
        "记住：你是朋友，不是老师，你的目标是让学习变得有趣。"
    )


async def _verify_ws_token(token: str) -> Optional[str]:
    """浏览器 WS 不能带 Header，token 走 query：先试自签 JWT，再走 Supabase 验证"""
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        uid = payload.get("sub") or payload.get("user_id")
        if uid:
            return uid
    except Exception:
        pass
    try:
        headers = {"apikey": settings.SUPABASE_KEY, "Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(f"{settings.SUPABASE_URL}/auth/v1/user", headers=headers)
        if res.status_code == 200:
            return (res.json() or {}).get("id")
    except Exception:
        pass
    return None


async def _fetch_xiaoji_recent_history(user_id: str, limit: int = 6) -> list:
    """取最近 N 条小基聊天记录（升序），作为通话开场上下文"""
    headers = get_supabase_headers()
    url = (
        f"{settings.SUPABASE_URL}/rest/v1/xiaoji_messages"
        f"?user_id=eq.{user_id}&order=created_at.desc&limit={limit}"
    )
    async with httpx.AsyncClient(timeout=15.0) as client:
        res = await client.get(url, headers=headers)
    if res.status_code != 200:
        return []
    rows = res.json()
    rows.reverse()
    return rows


# ============================================================
# 通话日志（xiaoji_call_logs 表：次数/时长/时段 → 侧栏日志 + 智能体中心）
# ============================================================

async def _save_call_log_start(user_id: str) -> str:
    """通话开始落一条日志（表未建时静默跳过），返回 call_id"""
    call_id = str(uuid.uuid4())
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            await client.post(
                f"{settings.SUPABASE_URL}/rest/v1/xiaoji_call_logs",
                headers=get_supabase_headers(),
                json={"id": call_id, "user_id": user_id},
            )
    except Exception as e:
        logger.info(f"[xiaoji] 通话日志未记录（表未就绪？）: {e}")
    return call_id


async def _save_call_log_end(call_id: str, duration_seconds: int, turns: int):
    """通话结束补写时长/轮数（表未建或网络抖动时静默跳过）"""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            await client.patch(
                f"{settings.SUPABASE_URL}/rest/v1/xiaoji_call_logs?id=eq.{call_id}",
                headers=get_supabase_headers(),
                json={
                    "ended_at": datetime.now(timezone.utc).isoformat(),
                    "duration_seconds": duration_seconds,
                    "turns": turns,
                },
            )
    except Exception as e:
        logger.info(f"[xiaoji] 通话日志收尾失败: {e}")


@router.websocket("/call-ws")
async def xiaoji_call_websocket(websocket: WebSocket):
    """
    小基语音通话：
      浏览器持续发送 16k PCM 帧（{"status":0,"audio":base64}），后端中转给千问
      realtime 模型，音频/字幕事件实时回传。控制消息：
        {"type":"interrupt"} 打断（response.cancel） / {"type":"bye"} 挂断
    服务端事件：
        ready / user_text / ai_text / ai_audio / done / interrupted / speech_started / error
    """
    await websocket.accept()

    # ── 鉴权（浏览器 WS 不能带 Header，token 走 query）──
    user_id = websocket.query_params.get("user_id", "")
    token_uid = await _verify_ws_token(websocket.query_params.get("token", ""))
    if not user_id or token_uid != user_id:
        try:
            await websocket.send_json({"type": "error", "message": "通话鉴权失败，请重新登录"})
        except Exception:
            pass
        await websocket.close(code=4401)
        return

    # ── 读小基配置：名称/语气风格（人设）+ 音色 + 主动问候开关 ──
    xiaoji_name = "小基"
    personality = "warm"
    qwen_voice = QWEN_DEFAULT_VOICE
    proactive_enabled = True
    try:
        headers = get_supabase_headers()
        url = f"{settings.SUPABASE_URL}/rest/v1/xiaoji_config?user_id=eq.{user_id}"
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.get(url, headers=headers)
        if res.status_code == 200 and res.json():
            cfg = res.json()[0]
            xiaoji_name = (cfg.get("name") or "小基").strip() or "小基"
            personality = cfg.get("personality") or "warm"
            # 音色与 TTS 共用同一千问音色列表（老讯飞音色自动回退默认）
            valid_voices = {v["value"] for v in get_available_voices()}
            if cfg.get("voice_name") in valid_voices:
                qwen_voice = cfg["voice_name"]
            proactive_enabled = cfg.get("proactive_enabled", True) is not False
    except Exception as e:
        logger.info(f"[xiaoji] 通话配置读取失败，用默认值: {e}")

    # ── 昵称（人设用）──
    nickname = "同学"
    try:
        headers = get_supabase_headers()
        url = f"{settings.SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}&select=nickname"
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.get(url, headers=headers)
        rows = res.json() if res.status_code == 200 else []
        if isinstance(rows, list) and rows:
            nickname = rows[0].get("nickname") or "同学"
    except Exception:
        pass

    if not settings.DASHSCOPE_API_KEY:
        try:
            await websocket.send_json({"type": "error", "message": "未配置 DashScope API Key，无法通话"})
        except Exception:
            pass
        await websocket.close()
        return

    # ── 通话日志：开始 ──
    call_id = await _save_call_log_start(user_id)
    call_turns = {"n": 0}
    call_started = time.monotonic()

    # ── 连千问 realtime ──
    try:
        qwen_ws = await _ws_connect(
            QWEN_REALTIME_URL,
            additional_headers={"Authorization": f"Bearer {settings.DASHSCOPE_API_KEY}"},
            open_timeout=10,
        )
    except Exception as e:
        logger.info(f"[xiaoji] 千问 realtime 连接失败: {e}")
        await _save_call_log_end(call_id, 0, 0)
        try:
            await websocket.send_json({"type": "error", "message": "语音服务连接失败，请稍后重试"})
        except Exception:
            pass
        await websocket.close()
        return

    try:
        # 等服务端 session.created 再更新会话配置
        session_ready = False
        for _ in range(10):
            try:
                raw = await asyncio.wait_for(qwen_ws.recv(), timeout=3)
            except Exception:
                break
            if isinstance(raw, bytes):
                continue
            try:
                evt = json.loads(raw)
            except (ValueError, TypeError):
                continue
            if evt.get("type") in ("session.created", "session.updated"):
                session_ready = True
                break
        if not session_ready:
            raise RuntimeError("千问 session 未就绪")

        await qwen_ws.send(json.dumps({
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "voice": qwen_voice,
                "instructions": _build_call_instructions(xiaoji_name, personality, nickname),
                "input_audio_format": "pcm",
                "output_audio_format": "pcm",
                "turn_detection": {"type": "server_vad", "threshold": 0.5, "silence_duration_ms": 800},
                "max_history_turns": 20,
            }
        }))

        # ── 预载最近聊天记录作为上下文（剥掉 emoji，避免通话里被读出来）──
        for msg in await _fetch_xiaoji_recent_history(user_id):
            role = msg.get("role")
            content = _strip_emoji(msg.get("content") or "")
            if role not in ("user", "assistant") or not content:
                continue
            await qwen_ws.send(json.dumps({
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": role,
                    "content": [{
                        "type": "input_text" if role == "user" else "text",
                        "text": content,
                    }],
                }
            }))

        # ── 主动问候（按设置开关）：注入打招呼触发器并请求一轮回复 ──
        if proactive_enabled:
            await qwen_ws.send(json.dumps({
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": "（电话刚接通）"}],
                }
            }))
            await qwen_ws.send(json.dumps({"type": "response.create"}))

        await websocket.send_json({
            "type": "ready",
            "config": {"name": xiaoji_name, "proactive_enabled": proactive_enabled},
        })

        # ── 双向中转 ──
        stop = asyncio.Event()
        assistant_parts = []     # 当前一轮 assistant 文本累积
        holder = {"response_active": False}   # 是否有进行中的回复（cancel 只在有回复时发）
        start_time = time.monotonic()

        async def browser_to_qwen():
            while not stop.is_set():
                try:
                    msg = await websocket.receive_json()
                except Exception:
                    stop.set()
                    return
                mtype = msg.get("type")
                if mtype == "interrupt":
                    # 用户抢话：取消千问当前回复（空闲时 cancel 会触发无效请求错误，跳过）
                    if holder["response_active"]:
                        try:
                            await qwen_ws.send(json.dumps({"type": "response.cancel"}))
                        except Exception:
                            stop.set()
                            return
                elif mtype == "bye":
                    stop.set()
                    return
                elif mtype == "ping":
                    continue
                else:
                    audio = msg.get("audio", "")
                    if audio:
                        try:
                            await qwen_ws.send(json.dumps({
                                "type": "input_audio_buffer.append",
                                "audio": audio,
                            }))
                        except Exception:
                            stop.set()
                            return
                    if msg.get("status") == 2:
                        try:
                            await qwen_ws.send(json.dumps({"type": "input_audio_buffer.commit"}))
                        except Exception:
                            stop.set()
                            return

        async def qwen_to_browser():
            nonlocal assistant_parts
            while not stop.is_set():
                try:
                    raw = await asyncio.wait_for(qwen_ws.recv(), timeout=30)
                except asyncio.TimeoutError:
                    # 长时间静默：WS 层 ping 保活
                    try:
                        await qwen_ws.ping()
                    except Exception:
                        stop.set()
                    continue
                except Exception:
                    stop.set()
                    return
                if isinstance(raw, bytes):
                    continue
                try:
                    evt = json.loads(raw)
                except (ValueError, TypeError):
                    continue
                etype = evt.get("type", "")

                if etype == "error":
                    err = evt.get("error") or {}
                    err_type = err.get("type", "")
                    # 客户端错误（如空闲时 cancel 的「无进行中回复」）是良性的，不打扰通话
                    if err_type == "server_error":
                        try:
                            await websocket.send_json({
                                "type": "error",
                                "message": str(err.get("message") or err)[:200],
                            })
                        except Exception:
                            pass
                        stop.set()
                    else:
                        logger.info(f"[xiaoji] 千问客户端错误（忽略）: {err.get('message')}")
                    continue

                if etype == "response.created":
                    holder["response_active"] = True
                    continue

                if etype == "conversation.item.input_audio_transcription.delta":
                    # 实时识别渐进文本（stash 字段）→ 前端「我」的实时字幕
                    stash = (evt.get("stash") or "").strip()
                    if stash:
                        try:
                            await websocket.send_json({"type": "partial_text", "text": stash})
                        except Exception:
                            stop.set()
                            return
                    continue

                if etype == "conversation.item.input_audio_transcription.completed":
                    text = (evt.get("transcript") or "").strip()
                    if text:
                        try:
                            await websocket.send_json({"type": "user_text", "text": text})
                        except Exception:
                            stop.set()
                            return
                        from routers.community.xiaoji import _save_xiaoji_message
                        try:
                            await _save_xiaoji_message(user_id, "user", text, kind="voice_call")
                        except Exception as se:
                            # 落库失败不打断通话（Supabase 抖动）
                            logger.info(f"[xiaoji] 通话消息落库失败: {se}")
                        call_turns["n"] += 1
                    continue

                if etype in ("response.audio_transcript.delta", "response.output_audio_transcript.delta"):
                    d = evt.get("delta", "")
                    if d:
                        assistant_parts.append(d)
                        try:
                            await websocket.send_json({"type": "ai_text", "delta": d})
                        except Exception:
                            stop.set()
                            return
                    continue

                if etype == "response.audio.delta":
                    d = evt.get("delta", "")
                    if d:
                        try:
                            await websocket.send_json({"type": "ai_audio", "delta": d})
                        except Exception:
                            stop.set()
                            return
                    continue

                if etype == "response.done":
                    holder["response_active"] = False
                    status = (evt.get("response") or {}).get("status", "")
                    text = "".join(assistant_parts).strip()
                    assistant_parts = []
                    if status == "completed" and text:
                        from routers.community.xiaoji import _save_xiaoji_message
                        try:
                            await _save_xiaoji_message(user_id, "assistant", text, kind="voice_call")
                        except Exception as se:
                            # 落库失败不打断通话（Supabase 抖动）
                            logger.info(f"[xiaoji] 通话消息落库失败: {se}")
                    try:
                        await websocket.send_json({
                            "type": "interrupted" if status == "cancelled" else "done",
                            "status": status,
                        })
                    except Exception:
                        stop.set()
                    continue

                if etype == "input_audio_buffer.speech_started":
                    # 用户开始说话（服务端 VAD）：通知前端切换状态/停止播报
                    try:
                        await websocket.send_json({"type": "speech_started"})
                    except Exception:
                        stop.set()
                    continue

                # 其余事件（session.* / response.created / conversation.item.* 等）忽略

        browser_task = asyncio.create_task(browser_to_qwen())
        qwen_task = asyncio.create_task(qwen_to_browser())

        # 最长通话时长守护
        while not stop.is_set():
            await asyncio.sleep(10)
            if time.monotonic() - start_time > QWEN_CALL_MAX_SECONDS:
                logger.info("[xiaoji] 通话超过 30 分钟，服务端主动挂断")
                stop.set()

        browser_task.cancel()
        qwen_task.cancel()

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.info(f"[xiaoji] 通话异常: {e}")
        try:
            await websocket.send_json({"type": "error", "message": f"通话异常: {str(e)[:120]}"})
        except Exception:
            pass
    finally:
        # 通话日志：结束（时长/轮数）
        await _save_call_log_end(
            call_id,
            int(time.monotonic() - call_started),
            call_turns["n"],
        )
        try:
            await qwen_ws.close()
        except Exception:
            pass
        try:
            await websocket.close()
        except Exception:
            pass