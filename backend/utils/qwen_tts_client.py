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

from config import settings
from logging_config import logger
from utils import gen_audit

# 生成审计用的标识。TTS 是**按量计费**的，而且不只是语音播报在用 ——
# services/video_gen.py 的视频配音也走这里，那条链路此前完全没有计数。
_PROVIDER = "qwen"


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
    fail_reason: Optional[list] = None,
    purpose: str = "unknown",
) -> Optional[bytes]:
    """
    文字转语音（千问 TTS-Plus）→ 返回 mp3 字节，失败返回 None

    :param speed: 语速 1-9（内部映射 rate 0.5-2.0）
    :param volume: 音量 1-9（内部映射 0-100）
    :param pitch: 音高 1-9（内部映射 pitch 0.5-2.0）
    :param fail_reason: 传一个 list 进来，失败时会把**原因**塞进去（不改返回值，老调用方不受影响）。

    ⚠️ 为什么要这个出口（2026-10-01）：这个函数有 6 条失败路径 —— 文本为空、
        去 emoji 后为空、**websocket-client 没装**、API 报 task-failed、
        没收到音频帧、抛异常 —— 但**全都只是 `return None`**。
        调用方看到「空」就只能写一句「TTS 返回空音频」，于是日志/数据库里
        永远查不出到底哪一种，**很可能往 TTS 服务上找，而问题根本不在那儿**
        （比如依赖没装、或者旁白本来就是空的）。
    """
    # 是否**真的发起了**对 TTS 服务的调用。前面几条 return（文本为空、依赖没装、
    # 音色非法）根本没碰到服务，不算 AI 调用 —— 记进去会把「调用次数」灌水。
    # ⚠️ 这两个变量必须在 def _fail 之前赋值：_fail 会在它们赋值之前就被调用。
    called = False
    started = 0.0

    def _fail(reason: str):
        if fail_reason is not None:
            fail_reason.append(reason)
        # warning 而不是 info：失败原因必须能在日志里看见
        logger.warning(f"[千问TTS] {reason}")
        if called:
            # 真连了服务却没拿到音频。status 用 empty_output 而不是 provider_error：
            # 这里大多数情况是"服务正常但没吐音频帧"，不是调用失败。
            gen_audit.note_status(
                provider=_PROVIDER, model=QWEN_TTS_MODEL, purpose=purpose,
                started=started, status=gen_audit.STATUS_EMPTY_OUTPUT,
                input_chars=len(text) or None,
                detail={"reason": reason[:200], "voice": voice, "format": format})
        return None

    if not text:
        return _fail("旁白文本为空，无可合成内容")
    text = _strip_emoji(text)[:2000]
    if not text:
        return _fail("旁白去掉表情符号后为空，无可合成内容")

    # websocket-client 是可选依赖（只有语音合成用它）。
    # 延迟导入：缺这个包时语音播报不可用，但不该拖垮整个服务启动。
    try:
        import websocket
    except ImportError:
        return _fail("未安装 websocket-client（pip install websocket-client）—— 和 TTS 服务本身无关")

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
        # ── 埋点从这一行开始：下面才是真的连 TTS 服务 ──
        called = True
        started = time.perf_counter()
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
                err = ctrl.get("header", {}).get("error_message", "") or "（服务端没给原因）"
                return _fail(f"服务端返回 task-failed：{err}")
            elif ev == "task-finished":
                break

        audio = b"".join(audio_parts)
        if not audio:
            return _fail(f"连接正常但没收到任何音频帧（旁白 {len(text)} 字，音色 {voice}）")
        # input_chars 记的是**送去合成的字数**（TTS 的输入就是文本）；
        # 产出是音频，字节数放 detail —— 和别处的 output_chars（字符数）不是一个量纲，
        # 混进同一列会让「输出长度」这个指标失去意义。
        gen_audit.note_status(
            provider=_PROVIDER, model=QWEN_TTS_MODEL, purpose=purpose,
            started=started, status=gen_audit.STATUS_OK,
            input_chars=len(text) or None,
            detail={"audio_bytes": len(audio), "voice": voice, "format": format})
        return audio
    except Exception as e:
        return _fail(f"调用异常：{type(e).__name__}: {e}")
    finally:
        if ws is not None:
            try:
                ws.close()
            except Exception:
                pass
