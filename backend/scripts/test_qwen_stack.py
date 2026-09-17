# -*- coding: utf-8 -*-
"""千问收编后端冒烟测试（临时脚本）：
 1) /xiaoji/tts（千问 TTS + emoji 剥离）
 2) /xiaoji/voice/list（4 音色）
 3) /community/xiaoji/chat-stream（qwen-plus 流式，验证确实分块）
 4) /community/xiaoji/vision（qwen3-vl-flash 识图）
"""
import asyncio
import base64
import json
import sys
import time
import uuid
import zlib
import struct

import httpx
import jwt as pyjwt

sys.path.insert(0, ".")
from config import settings

BASE = "http://127.0.0.1:8001"
UID = str(uuid.uuid4())
TOKEN = pyjwt.encode(
    {"sub": UID, "exp": int(time.time()) + 3600},
    settings.JWT_SECRET,
    algorithm=settings.JWT_ALGORITHM,
)
HDRS = {"Authorization": f"Bearer {TOKEN}"}


def make_png(w, h, rgb):
    def chunk(t, d):
        c = t + d
        return struct.pack(">I", len(d)) + c + struct.pack(">I", zlib.crc32(c))
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    raw = b"".join(b"\x00" + bytes(rgb) * w for _ in range(h))
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


async def main():
    async with httpx.AsyncClient(timeout=90.0) as c:
        # 1) TTS：正常文本 + emoji 文本
        r = await c.post(f"{BASE}/xiaoji/tts", json={"text": "你好，我是小基😊，很高兴😄认识你！", "voice_name": "longanqian"})
        d = r.json()
        mp3 = base64.b64decode(d.get("audio_base64", ""))
        print(f"1) TTS status={r.status_code} format={d.get('format')} bytes={len(mp3)} mp3head={mp3[:3].hex()}")

        # 2) 音色列表
        r = await c.get(f"{BASE}/xiaoji/voice/list")
        voices = r.json().get("voices", [])
        print(f"2) voice/list: {[v['value'] for v in voices]}")

        # 3) 流式聊天：分块计数 + 首字节延迟
        t0 = time.time()
        chunks = []
        async with c.stream("POST", f"{BASE}/community/xiaoji/chat-stream", params={"user_id": UID},
                            json={"content": "你好，请用三句话介绍一下你自己"}, headers=HDRS) as r:
            first_at = None
            async for line in r.aiter_raw():
                chunks.append(line)
                if first_at is None:
                    first_at = time.time() - t0
        full = b"".join(chunks).decode("utf-8", "ignore")
        print(f"3) chat-stream status={r.status_code} chunks={len(chunks)} 首字节={first_at:.2f}s 总长={len(full)}")
        print(f"   回复: {full[:80]}")

        # 4) 识图（qwen3-vl-flash）
        png = make_png(32, 32, (0, 0, 255))
        img = "data:image/png;base64," + base64.b64encode(png).decode()
        r = await c.post(f"{BASE}/community/xiaoji/vision", params={"user_id": UID},
                         json={"image_url": img, "question": "这张图是什么颜色？一句话回答"}, headers=HDRS)
        d = r.json()
        print(f"4) vision status={r.status_code} reply={d.get('reply')}")


asyncio.run(main())
