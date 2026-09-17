"""视频库音轨重合成小工具（2026-09-05）

只重跑 TTS，不动脚本/分镜（脚本与音轨解耦）。用途：
    - 用户定调语速偏快 → 换更低语速档重合成
    - 换音色

用法（cd backend）：
    python scripts/video_reaudio.py <knowledge_key>          # 用 config 的 VIDEO_TTS_SPEED 档
    python scripts/video_reaudio.py <knowledge_key> --speed 4 --voice lingxi
"""
import argparse
import asyncio
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import settings
from services.supabase import db
from utils.qwen_tts_client import get_tts_audio


def rate_of(speed: int) -> float:
    """语速档 1-9 → 千问 rate 0.5-2.0（与 qwen_tts_client.scale_to 同公式）"""
    speed = max(1, min(9, int(speed)))
    return 0.5 + (speed - 1) / 8 * 1.5


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("knowledge_key")
    ap.add_argument("--speed", type=int, default=None, help="语速档 1-9（默认取 config.VIDEO_TTS_SPEED）")
    ap.add_argument("--voice", default="", help="换音色（默认沿用行里的 voice_key）")
    args = ap.parse_args()

    speed = args.speed or settings.VIDEO_TTS_SPEED
    resp = await db.select("video_library", select="*",
                           eq={"knowledge_key": args.knowledge_key}, use_service_role=True)
    rows = resp.json() if resp.status_code < 300 else []
    if not rows:
        print("找不到该知识点:", resp.status_code, (resp.text or "")[:200])
        return

    for row in rows:
        vid = row["id"]
        narration = str(row.get("script_text")
                         or (row.get("script") or {}).get("narration") or "").strip()
        if not narration:
            print(f"行 {vid} 无口播文本，跳过")
            continue
        voice = args.voice or row.get("voice_key") or "longanqian"
        old_rate = rate_of(settings.VIDEO_TTS_SPEED) if not args.speed else rate_of(speed)
        print(f"→ {vid} | {row.get('title')!r} | {len(narration)} 字 | 音色 {voice} | 语速档 {speed}")

        audio = await asyncio.to_thread(get_tts_audio, narration, voice=voice, speed=speed)
        if not audio:
            print("  ✗ 千问 TTS 返回空音频（可能是限流/网络），稍后重试")
            continue
        up = await db.storage_upload("video-lib", f"{vid}/audio.mp3", audio, content_type="audio/mpeg",
                                upsert=True, use_service_role=True)
        if up.status_code >= 300:
            print(f"  ✗ storage 上传失败 {up.status_code}: {up.text[:200]}")
            continue
        # 时长：沿用 video_gen 的字数估算口径（第 6 档 ≈ 6.2 字/秒），按语速档比率换算——
        # 语速档越低 rate 越小 → 每秒字数越少 → 时长越长
        # 播放器实际用 <audio> 元数据实时校准，此处仅供列表展示
        cps = 6.2 * (rate_of(speed) / rate_of(6))
        new_dur = round(len(narration) / cps, 1)
        await db.update("video_library", eq={"id": vid}, data={
            "audio_duration": new_dur,
            "voice_key": voice,
            "tts_engine": "qwen",
            "audio_url": f"{settings.SUPABASE_URL}/storage/v1/object/public/video-lib/{vid}/audio.mp3",
            "updated_at": datetime.utcnow().isoformat(),
        }, use_service_role=True)
        print(f"  ✓ 完成 {len(audio)//1024}KB · 展示时长 {new_dur}s（真实时长播放器内自动校准）")


if __name__ == "__main__":
    asyncio.run(main())