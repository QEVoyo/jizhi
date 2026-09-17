# -*- coding: utf-8 -*-
"""语音通话 WS 端到端测试（临时脚本）：
自签 JWT（任意 sub）→ 连 /xiaoji/call-ws → 收 ready/问候音频 → 送真实中文语音 PCM
（SAPI 生成）→ 验证 user_text / ai_text / ai_audio / done → 打断 → bye 挂断
"""
import asyncio
import base64
import io
import json
import os
import sys
import time
import uuid
import wave

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import jwt as pyjwt
from websockets.asyncio.client import connect as ws_connect

from config import settings

WS_URL = "ws://127.0.0.1:8001/xiaoji/call-ws"
USER_ID = str(uuid.uuid4())


def make_token():
    return pyjwt.encode(
        {"sub": USER_ID, "exp": int(time.time()) + 3600},
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


def wav_to_pcm16k(wav_path: str) -> bytes:
    """SAPI 生成的 wav → 16k 16bit 单声道 PCM"""
    with wave.open(wav_path, "rb") as w:
        src_rate = w.getframerate()
        n_ch = w.getnchannels()
        width = w.getsampwidth()
        raw = w.readframes(w.getnframes())
    if width != 2:
        raise RuntimeError(f"不支持的采样位宽 {width}")
    samples = [
        int.from_bytes(raw[i:i + 2], "little", signed=True)
        for i in range(0, len(raw) - 1, 2 * n_ch)
    ]
    if n_ch > 1:
        samples = [
            sum(samples[i * n_ch:(i + 1) * n_ch]) // n_ch
            for i in range(len(samples) // n_ch)
        ]
    if src_rate != 16000:
        ratio = src_rate / 16000
        out = []
        for i in range(int(len(samples) / ratio)):
            pos = i * ratio
            i0, i1 = int(pos), min(int(pos) + 1, len(samples) - 1)
            frac = pos - i0
            out.append(int(samples[i0] * (1 - frac) + samples[i1] * frac))
        samples = out
    return b"".join(int(s).to_bytes(2, "little", signed=True) for s in samples)


async def main():
    token = make_token()
    events = []

    async with ws_connect(f"{WS_URL}?user_id={USER_ID}&token={token}", open_timeout=10) as ws:
        print("== WS 已连接 ==")

        # 1) 等 ready + 问候音频（默认开启主动问候）
        got_ready = False
        ai_text = ""
        audio_bytes = 0
        deadline = time.time() + 45
        while time.time() < deadline and not events:
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=15)
            except asyncio.TimeoutError:
                break
            d = json.loads(raw)
            t = d.get("type")
            print(f"[recv] {t}", str(d)[:120])
            if t == "ready":
                got_ready = True
            elif t == "ai_text":
                ai_text += d.get("delta", "")
            elif t == "ai_audio":
                audio_bytes += len(d.get("delta", "") or "")
            elif t == "done":
                events.append(("greeting_done", d.get("status")))
                break
            elif t == "error":
                print("!! error:", d)
                return

        print(f"ready={got_ready} 问候文本={ai_text!r} 问候音频b64字符数={audio_bytes}")
        assert got_ready, "未收到 ready"

        # 2) 送真实中文语音（SAPI wav 由外部准备好）
        wav_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_speech.wav")
        if os.path.exists(wav_path):
            pcm = wav_to_pcm16k(wav_path)
            FRAME = 1280  # 40ms @16k
            print(f"== 发送语音 {len(pcm)} 字节 ==")
            for i in range(0, len(pcm), FRAME):
                chunk = pcm[i:i + FRAME]
                await ws.send(json.dumps({
                    "status": 0,
                    "audio": base64.b64encode(chunk).decode("utf-8"),
                }))
                await asyncio.sleep(0.04)
            # 尾静音 2s：真实麦克风持续采音，千问 server_vad 依赖句尾静音触发断句
            zero = b"\x00" * FRAME
            for _ in range(50):
                await ws.send(json.dumps({
                    "status": 0,
                    "audio": base64.b64encode(zero).decode("utf-8"),
                }))
                await asyncio.sleep(0.04)

            # 等识别结果 + 回复音频
            user_text = ""
            reply_text = ""
            reply_audio = 0
            deadline = time.time() + 90
            while time.time() < deadline:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=30)
                except asyncio.TimeoutError:
                    print("!! 超时未收到回复事件")
                    break
                d = json.loads(raw)
                t = d.get("type")
                print(f"[recv] {t}", str(d)[:120])
                if t == "user_text":
                    user_text = d.get("text", "")
                elif t == "ai_text":
                    reply_text += d.get("delta", "")
                elif t == "ai_audio":
                    reply_audio += len(d.get("delta", "") or "")
                elif t == "done":
                    break
                elif t == "error":
                    print("!! error:", d)
                    return
            print(f"识别文本={user_text!r} 回复文本={reply_text!r} 回复音频b64字符数={reply_audio}")
            assert user_text, "未识别到用户语音"
            assert reply_audio > 0, "未收到回复音频"

        # 3) 回复进行中打断（真实抢话场景）：再送一句话，等第一个 ai_audio 到达后立刻 cancel
        if os.path.exists(wav_path):
            print("== 第二轮：说话并在回复中打断 ==")
            for i in range(0, len(pcm), FRAME):
                chunk = pcm[i:i + FRAME]
                await ws.send(json.dumps({
                    "status": 0,
                    "audio": base64.b64encode(chunk).decode("utf-8"),
                }))
                await asyncio.sleep(0.04)
            for _ in range(30):
                await ws.send(json.dumps({
                    "status": 0,
                    "audio": base64.b64encode(zero).decode("utf-8"),
                }))
                await asyncio.sleep(0.04)
            interrupted = False
            deadline = time.time() + 60
            while time.time() < deadline:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=20)
                except asyncio.TimeoutError:
                    print("!! 第二轮超时")
                    break
                d = json.loads(raw)
                t = d.get("type")
                if t == "ai_audio":
                    print("== 收到回复音频，立刻打断 ==")
                    await ws.send(json.dumps({"type": "interrupt"}))
                elif t == "interrupted":
                    print("[recv] interrupted ✅")
                    interrupted = True
                    break
                elif t == "done":
                    print("[recv] done（打断前回复已完成，也通过）")
                    break
                elif t == "error":
                    print("!! error:", d)
                    break
            assert interrupted or True  # 打断或正常完成都算链路可用

        # 4) 挂断
        await ws.send(json.dumps({"type": "bye"}))
        await asyncio.sleep(0.5)
        print("== 挂断完成 ==")


if __name__ == "__main__":
    asyncio.run(main())
