"""视频库运维小工具（2026-09-04 晚）

用法（cd backend，用 venv python）：
    python scripts/video_admin.py list
    python scripts/video_admin.py regen <knowledge_key> --name 双指针 --subject algorithm-ds
regen = 删掉该知识点全部行 + 清 storage 音轨 → POST 运行中后端 /video/lib/ensure 重新排产
（生成 worker 在后端进程里，本脚本只做删库与触发）
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path
from urllib.parse import quote

# 保证从 scripts/ 目录运行时 backend 包可导入
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx

from config import settings
from services.supabase import db

BACKEND = "http://localhost:8000"


async def cmd_list():
    resp = await db.select("video_library", select="*", use_service_role=True)
    rows = resp.json() if resp.status_code < 300 else []
    print(f"video_library 共 {len(rows)} 行：")
    for r in sorted(rows, key=lambda x: x.get("updated_at") or ""):
        print(f"- {r.get('subject')!r} | {r.get('knowledge_key')} | {r.get('knowledge_name')} | "
              f"{r.get('angle')} | {r.get('status')} | {r.get('audio_duration', 0)}s | "
              f"voice={r.get('voice_key')} | {r.get('title') or ''}")
    if resp.status_code >= 300:
        print("查询失败:", resp.status_code, resp.text[:200])


async def cmd_purge():
    """清空视频库：全行删除 + storage 桶对象全清（2026-09-05 用户拍板重洗全库）。
    注意 storage 删除用 service role（anon 会被 RLS 拒）。"""
    resp = await db.select("video_library", select="id", use_service_role=True)
    rows = resp.json() if resp.status_code < 300 else []
    print(f"video_library 现有 {len(rows)} 行，全部删除…")
    for r in rows:
        d = await db.delete("video_library", eq={"id": r["id"]}, use_service_role=True)
        print(f"  删行 {r['id']}: {d.status_code}")

    hdr = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
    }

    async def list_all(c, prefix=""):
        """递归列出桶内**真实对象**的完整路径。

        直接照 list 返回的 name 去删会 404：Supabase 的 list 对嵌套路径返回的是
        「文件夹」伪条目（id 与 metadata 均为 null），真正的对象在 `{uuid}/audio.mp3` 里。
        删 `{uuid}` 自然删不到东西——这就是「列表有、删除 404」的来源。
        判据：id/metadata 为空即视作文件夹，带上前缀再往里列一层。
        """
        out = []
        lr = await c.post(f"{settings.SUPABASE_URL}/storage/v1/object/list/video-lib",
                          headers=hdr, json={"prefix": prefix, "limit": 1000, "offset": 0})
        if lr.status_code >= 300:
            print(f"  列目录 {prefix!r} 失败: {lr.status_code} {lr.text[:120]}")
            return out
        for it in lr.json():
            name = it.get("name")
            if not name:
                continue
            full = f"{prefix}{name}"
            if it.get("id") is None and not it.get("metadata"):
                out += await list_all(c, full + "/")     # 文件夹 → 往里走
            else:
                out.append(full)
        return out

    async with httpx.AsyncClient(timeout=30) as c:
        objs = await list_all(c)
        print(f"storage 桶实际对象: 共 {len(objs)} 个")
        for n in objs:
            qn = quote(n, safe="")   # 名字含 / 必须整体转义
            dr = await c.delete(f"{settings.SUPABASE_URL}/storage/v1/object/video-lib/{qn}", headers=hdr)
            flag = "" if dr.status_code < 300 else "  ← 失败"
            print(f"  删对象 {n}: {dr.status_code}{flag}")


async def cmd_regen(knowledge_key: str, name: str, subject: str):
    resp = await db.select("video_library", select="id,subject,knowledge_name",
                           eq={"knowledge_key": knowledge_key}, use_service_role=True)
    rows = resp.json() if resp.status_code < 300 else []
    if resp.status_code >= 300:
        print("查询失败:", resp.status_code, resp.text[:200])
        return
    if rows and (not name or not subject):
        name = name or rows[0].get("knowledge_name") or ""
        subject = subject or rows[0].get("subject") or ""
    print(f"知识点 {knowledge_key} 现有 {len(rows)} 行，全部删除重生成（name={name!r}, subject={subject!r}）")
    for r in rows:
        vid = r["id"]
        d = await db.delete("video_library", eq={"id": vid}, use_service_role=True)
        print(f"  行 {vid} 删除: {d.status_code}")
        # storage 音轨删除（失败不致命，新音频会覆盖同名路径）
        try:
            async with httpx.AsyncClient(timeout=20) as c:
                sd = await c.delete(
                    f"{settings.SUPABASE_URL}/storage/v1/object/video-lib/{vid}/audio.mp3",
                    headers=db.storage_headers)
                print(f"  音轨对象删除: {sd.status_code}")
        except Exception as e:
            print(f"  音轨对象删除异常: {e}")

    # 触发后端 worker 重新排产
    payload = {
        "knowledge_key": knowledge_key,
        "knowledge_name": name,
        "subject": subject,
        "stage": "",
        "goal": 1,
        "author_name": "官方基智",
        "author_avatar": "/logo.png",
    }
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(f"{BACKEND}/video/lib/ensure", json=payload)
        print(f"ensure: {r.status_code} {r.text[:300]}")

    # 轮询到 ready（~40-90s：LLM 脚本 + TTS + 上传）
    print("等待生成…")
    for _ in range(24):
        await asyncio.sleep(10)
        resp = await db.select("video_library", select="id,status,audio_duration,title,audio_url",
                               eq={"knowledge_key": knowledge_key}, use_service_role=True)
        cur = resp.json() if resp.status_code < 300 else []
        if not cur:
            continue
        row = cur[0]
        print(f"  … {row.get('status')} {row.get('audio_duration', 0)}s")
        if row.get("status") in ("ready", "failed"):
            print("完成:", json.dumps(row, ensure_ascii=False))
            return
    print("超时未完成，去 http://localhost:8000/video/lib/queue/stats 或后端日志看")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    sub.add_parser("purge")
    p = sub.add_parser("regen")
    p.add_argument("knowledge_key")
    p.add_argument("--name", default="")
    p.add_argument("--subject", default="")
    args = ap.parse_args()

    if args.cmd == "list":
        asyncio.run(cmd_list())
    elif args.cmd == "purge":
        asyncio.run(cmd_purge())
    else:
        asyncio.run(cmd_regen(args.knowledge_key, args.name, args.subject))


if __name__ == "__main__":
    main()