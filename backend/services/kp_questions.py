# -*- coding: utf-8 -*-
"""按知识点从题库检索题目（2026-10-08 从 `routers/video.py` 抽出）

分层打分是 2026-10-01 做在 `GET /video/lib/{video_id}/questions` 里的，当时和
「视频卡片的做题按钮」绑死在一起。**每日学习推荐要用同一套检索** ——
再 inline 一份必然会改一处漏一处（这个项目在「同一个算法写两遍」上吃过好几次亏），
所以抽成独立模块，两处共用。

打分档位（**不要改这里的数字而不改 `routers/video.py` 的文档**）：

    120  sha1(kp_id) 精确命中（最准）
    100  知识点名全等
     80  知识点名互相包含
     60  题干 / 标题里出现了该知识点
    +15  同考纲加成（subject 对得上）

⚠️ 加成取 15 而不是更大的值，是为了让「跨库精确」(100) 仍然压得住
「本库模糊」(80+15=95) —— 精确永远优先，同库只在同档里取胜。
"""
import json
from typing import List, Optional

import local_question_bank
from services import video_gen


def q_stem_text(q: dict) -> str:
    """把题干的三种存法（`stem` / `content.stem` / `content` 是纯字符串）拉平成一段文字。

    题库题的题干在 `content.stem`（`SubjectPractice` 就是从那儿读的），
    但扁平化过的题也可能直接挂在 `stem` 上。模糊匹配两者都要能命中。
    """
    raw = q.get("stem")
    if not raw:
        c = q.get("content")
        raw = c.get("stem") if isinstance(c, dict) else (c if isinstance(c, str) else None)
    if isinstance(raw, (list, dict)):
        raw = json.dumps(raw, ensure_ascii=False)
    return str(raw or q.get("title") or "")


def score_by_kp(kp_name: str, kp_id: str = "", subject: str = "",
                limit: int = 12, exclude_ids: Optional[set] = None,
                kp_hash: str = "") -> List[dict]:
    """按相关度检索某个知识点的题，返回**降序**列表。

    返回的每条在原始题目之上多了三个键：
        syllabus_id    题目所属考纲 —— **做题端必须靠它定位题目**
        syllabus_name  考纲显示名
        match_score    相关度分（120/100/80/60 再 +15）

    ⚠️ `syllabus_id` 不是装饰：题库 18,711 题里 **497 个 id 横跨多个库**
    （见 `local_question_bank.find_question_unique` 的说明）。判分端
    `subject_plan.submit_answer` 靠 `syllabus_id` 找题，不带它就会跨库猜 ——
    **拿 A 科目的题判 B 科目的分**。所以调用方把结果存进 payload 时也必须带上它。

    `kp_id` 可空：没有它就走不了 120 那档（算不出哈希），但名字匹配仍然有效。
    每日学习推荐通常只有 topic 名、没有 kp_id，就属于这种情况。
    调用方**已经有哈希**时（比如视频行上的 `knowledge_key`）直接传 `kp_hash`，
    传了它就不用 `kp_id`。

    `exclude_ids`：已经做过的题目 id，直接跳过（无计划路径上 `_get_done_ids`
    依赖 plan_id 用不了，调用方自己查 `question_records` 传进来）。

    同步函数（题库全在内存里）。⚠️ 每次调用会遍历全部题库并对每道题算一次
    sha1 —— 与抽取前的行为一致，约几十毫秒。真要提速就按考纲预计算哈希，
    但那是另一件事。
    """
    target = (kp_name or "").strip()
    t_low = target.lower()
    skip = exclude_ids or set()

    # 目标知识点的哈希。视频/题库两边的 kp 键都是 f"{subject}:{sha1(kp_id)[:12]}"，
    # 这里只取哈希那半 —— subject 前缀历史上有三套命名，完整键对不上不代表不是同一个。
    if not kp_hash and kp_id:
        kp_hash = video_gen.make_knowledge_key("x", kp_id).split(":", 1)[-1]

    names = local_question_bank.syllabus_names()
    scored = []
    try:
        for sid, bank in local_question_bank.all_banks().items():
            for q in (bank or {}).get("questions") or []:
                if q.get("id") in skip:
                    continue
                s = 0
                q_kp_id = str(q.get("kp_id") or q.get("sub_category") or "")
                if kp_hash and q_kp_id and \
                        video_gen.make_knowledge_key("x", q_kp_id).split(":", 1)[-1] == kp_hash:
                    s = 120
                elif t_low:
                    name = (q.get("kp_name") or "").strip().lower()
                    if name:
                        if name == t_low:
                            s = 100
                        elif t_low in name or name in t_low:
                            s = 80
                    if not s and t_low in q_stem_text(q).lower():
                        s = 60
                if not s:
                    continue
                if subject and sid == subject:
                    s += 15
                scored.append((s, sid, q))
        # 分数降序；同分保持题库原顺序（stable sort）
        scored.sort(key=lambda x: -x[0])
    except Exception:                                           # noqa: BLE001
        # 检索失败不该把调用方整条链路带崩（与抽取前一致：失败返回空）
        from logging_config import logger
        logger.exception("[kp_questions] 题库检索失败")
        return []

    return [
        {**q, "syllabus_id": sid, "syllabus_name": names.get(sid, sid),
         "match_score": s}
        for s, sid, q in scored[:limit]
    ]
