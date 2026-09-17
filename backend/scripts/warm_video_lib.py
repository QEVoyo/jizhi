"""学科计划题库暖库脚本（2026-09-04 视频库冷启动）

枚举 backend/data/{考纲题库}.json 的知识点（按题目数热度倒序）
→ POST 到运行中的后端 /video/lib/warm 批量排产。

用法（后端先启动，且已执行 sql/create_video_library.sql）：
    cd backend
    python scripts/warm_video_lib.py --syllabus cet4 --max 50 --goal 1
    python scripts/warm_video_lib.py --dry --max 20      # 只看排产清单不提交
全量:去掉 --syllabus 即所有考纲；--max 限制知识点条数（高频在前）。
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import httpx

BACKEND = Path(__file__).resolve().parent.parent
DATA = BACKEND / "data"


def make_knowledge_key(subject: str, kp_id: str) -> str:
    """与 services/video_gen.py 同款键约定：学科 + kp_id 短哈希"""
    h = hashlib.sha1(str(kp_id).strip().encode("utf-8")).hexdigest()[:12]
    return f"{subject}:{h}"


def collect_knowledge_points(syllabus_ids):
    """枚举考纲题库，聚合知识点：kp_id → {name, count, syllabus_id}"""
    syllabi = json.load(open(DATA / "syllabi.json", encoding="utf-8"))
    selected = [s for s in syllabi if not syllabus_ids or s["id"] in set(syllabus_ids)]
    if syllabus_ids:
        found = {s["id"] for s in selected}
        missing = set(syllabus_ids) - found
        if missing:
            print(f"⚠️ 未知考纲: {missing}，可用: {sorted(x['id'] for x in syllabi)}")
            sys.exit(1)

    kps = {}
    for s in selected:
        bank_file = s.get("question_bank")
        if not bank_file or not (DATA / bank_file).exists():
            print(f"跳过 {s['id']}：无题库文件 {bank_file}")
            continue
        bank = json.load(open(DATA / bank_file, encoding="utf-8"))
        for q in bank:
            kp_id = q.get("kp_id") or q.get("sub_category")
            if not kp_id:
                continue
            entry = kps.setdefault(kp_id, {
                "name": q.get("kp_name") or kp_id,
                "count": 0,
                "syllabus_id": s["id"],
            })
            entry["count"] += 1

    # 热度倒序：题多的知识点优先排产 → [(kp_id, entry)]
    items = sorted(kps.items(), key=lambda kv: -kv[1]["count"])
    return items


async def main():
    ap = argparse.ArgumentParser(description="学科计划题库 → 视频库批量暖库")
    ap.add_argument("--syllabus", action="append", default=[], help="考纲 id，可多次；缺省=全部")
    ap.add_argument("--goal", type=int, default=1, help="每个知识点目标视频条数（角度数）")
    ap.add_argument("--max", type=int, default=0, help="最多排产 N 个知识点（0=不限）")
    ap.add_argument("--per", type=int, default=0, help="每考纲各取前 N 个（试点：--per 1 = 每科 1 个知识点 1 条视频）")
    ap.add_argument("--host", default="http://localhost:8000", help="后端地址")
    ap.add_argument("--chunk", type=int, default=50, help="每次 POST 的条数")
    ap.add_argument("--dry", action="store_true", help="只打印排产清单")
    args = ap.parse_args()

    items = collect_knowledge_points(args.syllabus)
    if args.per > 0:
        # 每考纲各取热度前 N（按问卷顺序出，保证每科都有代表知识点）
        by_syllabus = {}
        for kp_id, it in items:
            by_syllabus.setdefault(it["syllabus_id"], []).append((kp_id, it))
        items = []
        for kp_list in by_syllabus.values():
            items.extend(kp_list[:args.per])
    if args.max > 0:
        items = items[:args.max]

    print(f"排产清单（共 {len(items)} 个知识点，前 15 个预览）：")
    for kp_id, it in items[:15]:
        key = make_knowledge_key(it["syllabus_id"], kp_id)
        print(f"  {it['syllabus_id']:<10} {it['name']:<24} 题数 {it['count']:<5} → {key}")
    if len(items) > 15:
        print(f"  … 其余 {len(items) - 15} 个")

    if args.dry:
        print("dry-run 结束，未提交。")
        return

    async with httpx.AsyncClient(timeout=300) as client:
        total_enqueued = total_skipped = 0
        for i in range(0, len(items), args.chunk):
            chunk = items[i:i + args.chunk]
            payload = [
                {
                    "subject": it["syllabus_id"],
                    "knowledge_name": it["name"],
                    "knowledge_key": make_knowledge_key(it["syllabus_id"], kp_id),
                    "stage": "",
                    "goal": args.goal,
                    "author_name": "官方基智",
                    "author_avatar": "/logo.png",
                }
                for kp_id, it in chunk
            ]
            resp = await client.post(f"{args.host}/video/lib/warm", json={"items": payload, "goal": args.goal})
            info = resp.json() if resp.status_code < 300 else {"detail": resp.text[:200]}
            enq, skip = info.get("enqueued", 0), info.get("skipped", 0)
            total_enqueued += enq
            total_skipped += skip
            print(f"  批次 {i // args.chunk + 1}: 新增入队 {enq} / 已有跳过 {skip}")
        stats = await client.get(f"{args.host}/video/lib/queue/stats")
        print(f"完成: 总入队 {total_enqueued} / 总跳过 {total_skipped} → 队列 {stats.json()}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())