"""视频库全库质检（2026-09-05 批量生成工作流第 3 步）

README: 按当前提示词质量铁律（结构性 / 学科纪律 / 口播方向一致性 /
算术零误差 / 镜数·mood / phrase 收束），对全部 ready 视频跑一遍体检，
输出 PASS/FAIL 汇总。批量暖库后必跑；FAIL 项用 video_admin regen 重生成。

用法（cd backend）：
    python scripts/audit_videos.py             # 全部 ready 行
    python scripts/audit_videos.py --bad-only  # 只列 FAIL 行
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.supabase import db
from services.video_gen import (
    ARRAY_ALLOWED_SUBJECTS,
    _array_notes_arithmetic_ok,
    _moves_narration_consistent,
)


async def main():
    bad_only = "--bad-only" in sys.argv
    resp = await db.select("video_library",
                           select="id,subject,knowledge_name,title,status,script,script_text,audio_duration",
                           order="subject.asc", use_service_role=True)
    rows = resp.json() if resp.status_code < 300 else []
    if resp.status_code >= 300:
        print("查询失败:", resp.status_code, resp.text[:200])
        return

    total = failed = 0
    for x in rows:
        if x.get("status") != "ready":
            continue
        total += 1
        s = x.get("script") or {}
        errs = []

        narr = str(s.get("narration") or x.get("script_text") or "")
        if not narr:
            errs.append("无口播")
        elif len(narr) < 240:
            errs.append(f"口播{len(narr)}字<240")

        scenes = s.get("scenes")
        if not isinstance(scenes, list) or not scenes:
            if not isinstance(s.get("sections"), list):
                errs.append("无scenes")
        else:
            n = len(scenes)
            if not (6 <= n <= 9):
                errs.append(f"镜数{n}超出6-9")
            moods = {sc.get("mood") for sc in scenes if isinstance(sc, dict)}
            if len(moods) < 2:
                errs.append("mood<2种")
            widgets = [sc.get("widget") for sc in scenes if isinstance(sc, dict)]
            if "phrase" not in widgets:
                errs.append("缺phrase收束")

        if (x.get("subject") or "") not in ARRAY_ALLOWED_SUBJECTS:
            if any(isinstance(sc, dict) and sc.get("widget") == "array" for sc in (scenes or [])):
                errs.append("非数理科出现array")

        if not _moves_narration_consistent(s):
            errs.append("口播方向与moves不一致")
        if not _array_notes_arithmetic_ok(s):
            errs.append("note算术错误")

        if errs:
            failed += 1
            print(f"FAIL {x.get('subject')} · {x.get('knowledge_name')} ({x.get('audio_duration')}s) | {'; '.join(errs)}")
        elif not bad_only:
            print(f"PASS {x.get('subject')} · {x.get('knowledge_name')} ({x.get('audio_duration')}s)")

    print(f"\n合计: ready {total} 条, FAIL {failed} 条 ({round(failed / max(1, total) * 100)}%)")


if __name__ == "__main__":
    asyncio.run(main())