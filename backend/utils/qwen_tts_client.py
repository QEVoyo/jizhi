# -*- coding: utf-8 -*-
"""千问语音合成客户端（qwen-audio-3.0-tts-plus，2026-08-25 实测协议）

替换讯飞 TTS：小基语音播报统一走阿里云 DashScope（与语音通话同一个 key）。
协议（实测确认）：
  - 端点：wss://dashscope.aliyuncs.com/api-ws/v1/inference，Authorization Bearer 头鉴权
  - 请求：{"header": {"action": "run-task", "task_id": ..., "streaming": "outcome"},
            "payload": {"model": "qwen-audio-3.0-tts-plus", "task_group": "audio",
                        "task": "tts", "function": "SpeechSynthesizer",
                        "parameters": {"format": "mp3", "voice": ..., "rate": ..., "volume": ...},
                        "input": {"text": ...}}}
  - 响应：JSON 事件 task-started →（二进制 MP3 帧，ID3 头）→ task-finished
  - 实测可用音色：longanqian / longanlingxin / longanlingxi / longanlufeng
    （longanxiaoxin 在 TTS 模型上报 cosyvoice Engine error 411，不可用）
"""
import json
import re
import time
import uuid
import base64
from typing import Optional

import websocket

from config import settings
from logging_config import logger


# emoji 不朗读：合成前剥掉（含肤色修饰/ZWJ 组合/变体选择符/按键符）
_EMOJI_RE = re.compile(
    "["
    "\U0001F000-\U0001FAFF"    # emoji 主区 + 扩展
    "☀-➿"            # 杂项符号 / 装饰符号
    "⬀-⯿"            # 杂项符号与箭头补充
    "←-⇿"            # 箭头
    "⌀-⏿"            # 技术符号
    "️"                   # 变体选择符
    "‍"                   # 零宽连字（组合 emoji）
    "⃣"                   # 按键帽
    "©®"             # © ®
    "]+"
)


def _strip_emoji(text: str) -> str:
    """剥掉 emoji（保留空格，避免词粘连）"""
    return _EMOJI_RE.sub(" ", text).strip()


QWEN_TTS_MODEL = "qwen-audio-3.0-tts-plus"
QWEN_TTS_URL = "wss://dashscope.aliyuncs.com/api-ws/v1/inference"

# 与语音通话（qwen-audio-3.0-realtime-plus）共用的音色列表
QWEN_TTS_VOICES = [
    {"value": "longanqian", "label": "龙安倩 · 温柔女声"},
    {"value": "longanlingxin", "label": "龙安灵心 · 知心女声"},
    {"value": "longanlingxi", "label": "龙安灵犀 · 清新女声"},
    {"value": "longanlufeng", "label": "龙安鲁风 · 开朗男声"},
]
QWEN_DEFAULT_VOICE = "longanqian"


def get_available_voices() -> list:
    """可用音色列表（设置页 /voice/list 数据源）"""
    return QWEN_TTS_VOICES


def get_tts_audio(
    text: str,
    voice: str = QWEN_DEFAULT_VOICE,
    speed: int = 5,
    volume: int = 5,
    pitch: int = 5,
    format: str = "mp3",
) -> Optional[bytes]:
    """
    文字转语音（千问 TTS-Plus）→ 返回 mp3 字节，失败返回 None
    :param speed: 语速 1-9（内部映射 rate 0.5-2.0）
    :param volume: 音量 1-9（内部映射 0-100）
    :param pitch: 音高 1-9（内部映射 pitch 0.5-2.0）
    """
    if not text:
        return None
    text = _strip_emoji(text)[:2000]
    if not text:
        return None

    if voice not in {v["value"] for v in QWEN_TTS_VOICES}:
        voice = QWEN_DEFAULT_VOICE

    def scale_to(v: int, lo: float, hi: float) -> float:
        """1-9 → [lo, hi] 线性映射"""
        try:
            v = int(v)
        except (TypeError, ValueError):
            v = 5
        v = max(1, min(9, v))
        return round(lo + (v - 1) / 8 * (hi - lo), 2)

    task = {
        "header": {
            "action": "run-task",
            "task_id": f"jizhi-{uuid.uuid4().hex[:12]}",
            "streaming": "outcome",
        },
        "payload": {
            "model": QWEN_TTS_MODEL,
            "task_group": "audio",
            "task": "tts",
            "function": "SpeechSynthesizer",
            "parameters": {
                "format": format,
                "voice": voice,
                "rate": scale_to(speed, 0.5, 2.0),
                "volume": round(scale_to(volume, 0, 100)),
                "pitch": scale_to(pitch, 0.5, 2.0),
            },
            "input": {"text": text},
        },
    }

    ws = None
    audio_parts = []
    try:
        # 握手偶发超时（网络抖动），重试一次
        try:
            ws = websocket.create_connection(
                QWEN_TTS_URL,
                header=[f"Authorization: Bearer {settings.DASHSCOPE_API_KEY}"],
                timeout=10,
            )
        except Exception:
            ws = websocket.create_connection(
                QWEN_TTS_URL,
                header=[f"Authorization: Bearer {settings.DASHSCOPE_API_KEY}"],
                timeout=10,
            )

        ws.send(json.dumps(task, ensure_ascii=False))
        ws.settimeout(15)

        while True:
            try:
                raw = ws.recv()
            except Exception:
                break  # 静默超时视为结束
            if isinstance(raw, bytes):
                # 二进制 MP3 帧（新协议直接推裸音频）
                audio_parts.append(raw)
                continue
            try:
                ctrl = json.loads(raw)
            except (ValueError, TypeError):
                continue
            ev = ctrl.get("header", {}).get("event", "")
            if ev == "result-generated":
                # 兼容旧协议：base64 音频帧
                data = ctrl.get("payload", {}).get("output", {}).get("audio", {})
                if data.get("data"):
                    audio_parts.append(base64.b64decode(data["data"]))
            elif ev == "task-failed":
                logger.info(
                    f"[千问TTS] 合成失败: {ctrl.get('header', {}).get('error_message', '')}"
                )
                return None
            elif ev == "task-finished":
                break

        audio = b"".join(audio_parts)
        if not audio:
            logger.info("[千问TTS] 未收到音频数据")
            return None
        return audio
    except Exception as e:
        logger.info(f"[千问TTS] 异常: {e}")
        return None
    finally:
        if ws is not None:
            try:
                ws.close()
            except Exception:
                pass
