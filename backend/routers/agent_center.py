"""
智能体中心聚合路由 — 只读分析 + 参数/磨合读写
============================================
数据原则（见 agent_center_design.md）：
  调用计数 → user_actions（action_type + metadata.touchpoint）
  效果指标 → 业务表（plan_daily_tasks / question_records / exam_paper_records /
             generation_history / questions / question_sets / learning_logs /
             xiaoji_messages / user_kp_mastery / diagnosis_results / subject_plans）
  参数/磨合 → agent_prefs / agent_tuning_log（本模块写）
跨表联合全部在 Python 侧完成（PostgREST 只做单表过滤拉取）。
"""
import asyncio

import httpx
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel

from config import settings
from utils.auth_middleware import get_current_user, verify_user_match

router = APIRouter()

# 北京时间（UTC+8）：通话时段分桶统一按北京时间
BEIJING = timezone(timedelta(hours=8))

# ============================================================
# 基础工具
# ============================================================

def _headers():
    return {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json",
    }


async def _get(table: str, params: Dict[str, str]) -> list:
    """PostgREST 单表查询，任何失败返回 []（分析接口优雅降级）"""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.get(
                f"{settings.SUPABASE_URL}/rest/v1/{table}",
                headers=_headers(), params=params,
            )
            if res.status_code == 200:
                return res.json() if isinstance(res.json(), list) else []
    except Exception:
        pass
    return []


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _since_iso(days: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


def _day(s: str) -> str:
    return (s or "")[:10]


def _pct(n: float, d: float) -> Optional[float]:
    """百分比，分母为 0 返回 None"""
    if not d:
        return None
    return round(n / d * 100, 1)


# ============================================================
# 触点清单（与 agent_center_design.md 一致）
# ============================================================

TOUCHPOINTS: Dict[str, List[Dict[str, str]]] = {
    "chat": [
        # 对话 Agent = 主对话区（Web 端已由小基取代，2026-09-10 起如实计 0）。
        # 主对话的埋点约定带 metadata.touchpoint='chat_main'；不加过滤会把
        # 小基队友栏写的 use_*_agent 也算进来（那是小基的分流，不是对话 Agent 的）
        {"name": "答疑对话", "scene": "主对话区", "source": "action_meta", "action_type": "chat",
         "touchpoint": "chat_main"},
        {"name": "词义讲解", "scene": "对话·词条卡", "source": "vocab_lookup", "touchpoint": "chat_ask"},
        {"name": "规划分流", "scene": "对话→规划 Agent", "source": "action_meta", "action_type": "use_plan_agent",
         "touchpoint": "chat_main"},
        {"name": "生成分流", "scene": "对话→生成 Agent", "source": "action_meta", "action_type": "use_generate_agent",
         "touchpoint": "chat_main"},
        {"name": "评估分流", "scene": "对话→评估 Agent", "source": "action_meta", "action_type": "use_evaluate_agent",
         "touchpoint": "chat_main"},
        {"name": "日志摘要", "scene": "自动", "source": "learning_logs"},
    ],
    "plan": [
        {"name": "聊天里问规划", "scene": "对话", "source": "action", "action_type": "use_plan_agent"},
        {"name": "诊断生成计划", "scene": "考纲页", "source": "diagnosis_results"},
        {"name": "答卷生成计划", "scene": "真题卷", "source": "plan_source_exam"},
        {"name": "每日学习讲解", "scene": "每日任务", "source": "task_learning_content"},
    ],
    "generate": [
        {"name": "聊天里出题", "scene": "对话", "source": "action", "action_type": "use_generate_agent"},
        {"name": "资源库生成", "scene": "资源库", "source": "action_meta", "action_type": "generate_question", "touchpoint": "reslib_generate"},
        {"name": "掌握度定向生成", "scene": "资源库", "source": "action_meta", "action_type": "generate_question", "touchpoint": "mastery_generate"},
        {"name": "题集创建", "scene": "资源库", "source": "action", "action_type": "create_set"},
    ],
    "evaluate": [
        {"name": "聊天里问评估", "scene": "对话", "source": "action", "action_type": "use_evaluate_agent"},
        {"name": "做题提交批改", "scene": "做题页", "source": "qr_ai_feedback"},
        {"name": "真题交卷分析", "scene": "真题卷", "source": "exam_paper_records"},
        {"name": "画像 AI 总结", "scene": "个人画像", "source": "profile_ai_summary"},
    ],
    "xiaoji": [
        {"name": "小基聊天", "scene": "小基页", "source": "xiaoji_kind", "kind": "chat"},
        {"name": "语音通话", "scene": "通话页", "source": "call_logs"},
        {"name": "工具使用", "scene": "小基工具区", "source": "action", "action_type": "xiaoji_tool"},
        {"name": "词条抓取", "scene": "识图拍题提词", "source": "vocab_lookup", "touchpoint": "xiaoji_vision"},
        {"name": "小基识图", "scene": "小基页", "source": "xiaoji_kind", "kind": "vision"},
        {"name": "评价题目/题集", "scene": "小基页", "source": "xiaoji_kind", "kind": "evaluate"},
        # 队友栏快捷提问分流（2026-09-02 补：08-27 遗留——小基卡片上看得见联动能力）
        {"name": "快捷提问分流", "scene": "小基页·队友栏",
         "source": "action_touch",
         "action_type": "use_plan_agent|use_generate_agent|use_evaluate_agent",
         "touchpoint": "xiaoji_quick_ask|xiaoji_gen_card"},
    ],
}

AGENT_NAMES = {"chat": "对话 Agent", "plan": "规划 Agent", "generate": "生成 Agent", "evaluate": "评估 Agent", "xiaoji": "小基"}


# ============================================================
# 原始数据一次性拉取（Python 侧聚合）
# ============================================================

async def _collect(user_id: str, since: str) -> Dict[str, Any]:
    """一次性拉取所有原始数据：单连接 + asyncio.gather 并发（否则串行 14 个请求要 10s+）"""
    async with httpx.AsyncClient(timeout=15.0) as client:

        async def get(table: str, params: Dict[str, str]) -> list:
            try:
                res = await client.get(
                    f"{settings.SUPABASE_URL}/rest/v1/{table}",
                    headers=_headers(), params=params)
                if res.status_code == 200:
                    return res.json() if isinstance(res.json(), list) else []
            except Exception:
                pass
            return []

        keys = [
            "actions", "xiaoji_msgs", "tasks", "plans", "diagnoses", "records",
            "exams", "gen_history", "gen_questions", "sets", "logs", "mastery",
            "profile_settings", "vocab_lookups", "word_mastery", "call_logs",
        ]
        results = await asyncio.gather(
            get("user_actions", {
                "user_id": f"eq.{user_id}",
                "select": "action_type,metadata,action_at",
                "action_at": f"gte.{since}", "order": "action_at.asc", "limit": "5000",
            }),
            get("xiaoji_messages", {
                "user_id": f"eq.{user_id}", "select": "kind,role,created_at",
                "created_at": f"gte.{since}", "limit": "5000",
            }),
            get("plan_daily_tasks", {
                "user_id": f"eq.{user_id}",
                "select": "date,completed,learning_content,phase,question_ids", "limit": "5000",
            }),
            get("subject_plans", {
                "user_id": f"eq.{user_id}", "select": "id,source,syllabus_id",
            }),
            get("diagnosis_results", {
                "user_id": f"eq.{user_id}", "select": "id,created_at",
                "created_at": f"gte.{since}", "limit": "5000",
            }),
            get("question_records", {
                "user_id": f"eq.{user_id}",
                "select": "question_id,is_correct,ai_feedback,created_at", "limit": "5000",
            }),
            get("exam_paper_records", {
                "user_id": f"eq.{user_id}", "select": "id,question_results,created_at",
                "created_at": f"gte.{since}", "limit": "5000",
            }),
            get("generation_history", {
                "user_id": f"eq.{user_id}", "select": "id,created_at",
                "created_at": f"gte.{since}", "limit": "5000",
            }),
            get("questions", {
                "user_id": f"eq.{user_id}", "source": "eq.generated",
                "select": "id,difficulty_score", "limit": "5000",
            }),
            get("question_sets", {
                "user_id": f"eq.{user_id}", "select": "id,question_ids",
            }),
            get("learning_logs", {
                "user_id": f"eq.{user_id}", "select": "id,created_at",
                "created_at": f"gte.{since}", "limit": "5000",
            }),
            get("user_kp_mastery", {
                "user_id": f"eq.{user_id}",
                "select": "kp_id,mastery_score,last_practiced_at", "limit": "5000",
            }),
            get("profile_card_settings", {
                "user_id": f"eq.{user_id}", "select": "data",
            }),
            get("vocab_lookups", {
                "user_id": f"eq.{user_id}", "select": "word,touchpoint,created_at",
                "created_at": f"gte.{since}", "limit": "5000",
            }),
            get("word_mastery", {
                "user_id": f"eq.{user_id}", "select": "word,mastery_score,last_practiced_at", "limit": "5000",
            }),
            get("xiaoji_call_logs", {
                "user_id": f"eq.{user_id}",
                "select": "id,started_at,duration_seconds,turns",
                "started_at": f"gte.{since}", "limit": "5000",
            }),
        )
    return dict(zip(keys, results))


def _has_ai_summary(row: dict) -> bool:
    d = row.get("data")
    if isinstance(d, dict):
        return bool(d.get("ai_summary") or d.get("summary") or d.get("ai_summary_text"))
    return False


def _action_count(data: dict, action_type: str, touchpoint: Optional[str] = None) -> int:
    n = 0
    for a in data["actions"]:
        if a.get("action_type") != action_type:
            continue
        if touchpoint and (a.get("metadata") or {}).get("touchpoint") != touchpoint:
            continue
        n += 1
    return n


ACTION_SOURCES = ("action", "action_meta", "action_touch")


def _distinct_action_count(data: dict) -> int:
    """去重后的 action 事件数（2026-09-10 修正重复计）。

    同一条 user_actions 记录会被多个 agent 的触点视角同时引用——设计上就是
    「对话 Agent 的『分流』× 目标 Agent 的『触达』，同一动作两视角」（见
    agent_center_design.md）。各 agent 的 calls 相加得到 KPI 总调用数会重复计，
    故总调用数的 action 部分单独按去重事件数统计；业务表类触点各自独立，仍相加。
    """
    hit = set()
    for tps in TOUCHPOINTS.values():
        for tp in tps:
            if tp["source"] not in ACTION_SOURCES:
                continue
            types = set((tp.get("action_type") or "").split("|"))
            tp_touch = tp.get("touchpoint")
            touches = set(tp_touch.split("|")) if tp_touch else None
            for i, a in enumerate(data["actions"]):
                if a.get("action_type") not in types:
                    continue
                if touches is not None and (a.get("metadata") or {}).get("touchpoint") not in touches:
                    continue
                hit.add(i)
    return len(hit)


def _count_touchpoints(data: dict, agent_key: str) -> List[dict]:
    out = []
    for tp in TOUCHPOINTS[agent_key]:
        src = tp["source"]
        if src == "action":
            n = _action_count(data, tp["action_type"])
        elif src == "action_meta":
            n = _action_count(data, tp["action_type"], tp.get("touchpoint"))
        elif src == "action_touch":
            # 多个 action_type × 多个 touchpoint 的组合计数（2026-09-02 队友栏分流）
            types = tp.get("action_type", "").split("|")
            touches = tp.get("touchpoint", "").split("|")
            n = sum(
                1 for a in data["actions"]
                if a.get("action_type") in types
                and (a.get("metadata") or {}).get("touchpoint") in touches
            )
        elif src == "learning_logs":
            n = len(data["logs"])
        elif src == "diagnosis_results":
            n = len(data["diagnoses"])
        elif src == "plan_source_exam":
            n = sum(1 for p in data["plans"] if p.get("source") == "exam_paper")
        elif src == "task_learning_content":
            n = sum(1 for t in data["tasks"] if t.get("learning_content"))
        elif src == "qr_ai_feedback":
            n = sum(1 for r in data["records"] if r.get("ai_feedback"))
        elif src == "exam_paper_records":
            n = len(data["exams"])
        elif src == "profile_ai_summary":
            n = sum(1 for s in data["profile_settings"] if _has_ai_summary(s))
        elif src == "xiaoji_kind":
            n = sum(1 for m in data["xiaoji_msgs"] if m.get("kind") == tp.get("kind"))
        elif src == "call_logs":
            n = len(data["call_logs"])
        elif src == "vocab_lookup":
            n = sum(1 for l in data["vocab_lookups"] if l.get("touchpoint") == tp.get("touchpoint"))
        else:
            n = 0
        out.append({"name": tp["name"], "scene": tp["scene"], "count": n})
    return out


# ============================================================
# 效果指标与趋势（Python 侧聚合）
# ============================================================

def _daily_series(rows: list, date_field: str, since_days: int = 30) -> List[int]:
    """把带时间的行聚合成近 N 天每日计数序列（旧→新）"""
    buckets = defaultdict(int)
    for r in rows:
        d = _day(r.get(date_field) or "")
        if d:
            buckets[d] += 1
    out = []
    for i in range(since_days - 1, -1, -1):
        d = (datetime.now(timezone.utc) - timedelta(days=i)).strftime("%Y-%m-%d")
        out.append(buckets.get(d, 0))
    return out


def _chat_days(data: dict) -> set:
    return {_day(a.get("action_at") or "") for a in data["actions"]
            if a.get("action_type") == "chat"}


def _xiaoji_days(data: dict) -> set:
    return {_day(m.get("created_at") or "") for m in data["xiaoji_msgs"]}


def _records_per_day_on(data: dict, days: set) -> Optional[float]:
    """指定日期的日均做题量"""
    per_day = defaultdict(int)
    for r in data["records"]:
        per_day[_day(r.get("created_at") or "")] += 1
    if not days:
        return None
    total = sum(per_day.get(d, 0) for d in days)
    return round(total / len(days), 1)


def _plan_completion(data: dict) -> Optional[float]:
    if not data["tasks"]:
        return None
    done = sum(1 for t in data["tasks"] if t.get("completed"))
    return _pct(done, len(data["tasks"]))


def _tasks_learning_rates(data: dict):
    """讲解 vs 无讲解任务的完成率"""
    with_lc = [t for t in data["tasks"] if t.get("learning_content")]
    without_lc = [t for t in data["tasks"] if not t.get("learning_content")]
    return (
        _pct(sum(1 for t in with_lc if t.get("completed")), len(with_lc)),
        _pct(sum(1 for t in without_lc if t.get("completed")), len(without_lc)),
    )


def _phase_rates(data: dict) -> List[dict]:
    groups = defaultdict(list)
    for t in data["tasks"]:
        groups[t.get("phase") or "未分阶段"].append(t)
    out = []
    for phase, rows in groups.items():
        out.append({
            "label": phase,
            "value": _pct(sum(1 for t in rows if t.get("completed")), len(rows)) or 0,
            "unit": "%",
        })
    order = {"基础期": 0, "强化期": 1, "冲刺期": 2}
    out.sort(key=lambda x: order.get(x["label"], 99))
    return out


def _task_volume_rates(data: dict) -> List[dict]:
    """任务量与完成率：按每日任务数分组"""
    groups = {">=6": [], "4-5": [], "<=3": []}
    for t in data["tasks"]:
        n = len(t.get("question_ids") or [])
        groups[">=6" if n >= 6 else ("4-5" if n >= 4 else "<=3")].append(t)
    labels = [("<=3", "<=3 个/天"), ("4-5", "4-5 个/天"), (">=6", ">=6 个/天")]
    out = []
    for key, label in labels:
        rows = groups[key]
        out.append({
            "label": label,
            "value": _pct(sum(1 for t in rows if t.get("completed")), len(rows)) or 0,
            "unit": "%",
        })
    return out


def _difficulty_buckets(data: dict) -> List[dict]:
    buckets = {"1-3": [], "4-6": [], "7-8": [], "9-10": []}
    for q in data["gen_questions"]:
        s = q.get("difficulty_score") or 0
        k = "9-10" if s > 8.5 else ("7-8" if s > 6.5 else ("4-6" if s > 3.5 else "1-3"))
        buckets[k].append(q)
    total = len(data["gen_questions"])
    labels = [("1-3", "1-3 级（入门）"), ("4-6", "4-6 级（适中）"), ("7-8", "7-8 级（偏难）"), ("9-10", "9-10 级（挑战）")]
    return [{"label": lab, "value": _pct(len(buckets[k]), total) or 0, "unit": "%"} for k, lab in labels]


def _set_collection_rates(data: dict) -> List[dict]:
    """各难度段的题集收录率"""
    all_set_ids = set()
    for s in data["sets"]:
        all_set_ids.update(s.get("question_ids") or [])
    buckets = {"1-3": [], "4-6": [], "7-8": [], "9-10": []}
    for q in data["gen_questions"]:
        s = q.get("difficulty_score") or 0
        k = "9-10" if s > 8.5 else ("7-8" if s > 6.5 else ("4-6" if s > 3.5 else "1-3"))
        buckets[k].append(q)
    labels = [("1-3", "1-3 级"), ("4-6", "4-6 级"), ("7-8", "7-8 级"), ("9-10", "9-10 级")]
    out = []
    for k, lab in labels:
        rows = buckets[k]
        collected = sum(1 for q in rows if q.get("id") in all_set_ids)
        out.append({"label": lab, "value": _pct(collected, len(rows)) or 0, "unit": "%"})
    return out


def _collection_rate(data: dict) -> Optional[float]:
    all_set_ids = set()
    for s in data["sets"]:
        all_set_ids.update(s.get("question_ids") or [])
    if not data["gen_questions"]:
        return None
    collected = sum(1 for q in data["gen_questions"] if q.get("id") in all_set_ids)
    return _pct(collected, len(data["gen_questions"]))


def _redo_rates(data: dict):
    """首答 vs 末次作答正确率（同题 >=2 次作答）"""
    attempts = defaultdict(list)
    for r in data["records"]:
        attempts[r.get("question_id")].append(r)
    firsts, lasts = [], []
    for qid, rows in attempts.items():
        if len(rows) < 2:
            continue
        rows.sort(key=lambda r: r.get("created_at") or "")
        firsts.append(1 if rows[0].get("is_correct") else 0)
        lasts.append(1 if rows[-1].get("is_correct") else 0)
    if not firsts:
        return None, None
    return (
        round(sum(firsts) / len(firsts) * 100, 1),
        round(sum(lasts) / len(lasts) * 100, 1),
    )


def _exam_coverage(data: dict) -> Optional[float]:
    """真题错因分析覆盖：question_results 里有 ai 分析的错题 / 总错题"""
    analyzed, wrong = 0, 0
    for e in data["exams"]:
        qrs = e.get("question_results")
        if not isinstance(qrs, dict):
            continue
        for qr in qrs.values():
            if not isinstance(qr, dict):
                continue
            if not qr.get("is_correct"):
                wrong += 1
                if qr.get("ai_analysis") or qr.get("ai_feedback"):
                    analyzed += 1
    return _pct(analyzed, wrong) if wrong else None


def _weak_kp_count(data: dict) -> int:
    return sum(1 for m in data["mastery"] if (m.get("mastery_score") or 0) < 60)


def _word_mastery_dist(data: dict) -> List[dict]:
    """词条熟练度分布：高熟练 / 中熟练 / 薄弱"""
    rows = data["word_mastery"]
    if not rows:
        return []
    high = sum(1 for r in rows if (r.get("mastery_score") or 0) >= 80)
    mid = sum(1 for r in rows if 60 <= (r.get("mastery_score") or 0) < 80)
    total = len(rows)
    return [
        {"label": "高熟练（≥80%）", "value": _pct(high, total) or 0, "unit": "%"},
        {"label": "中熟练（60-79%）", "value": _pct(mid, total) or 0, "unit": "%"},
        {"label": "薄弱（<60%）", "value": _pct(total - high - mid, total) or 0, "unit": "%"},
    ]


def _top_lookup_words(data: dict, touchpoint: str = "xiaoji_vision", n: int = 3) -> List[dict]:
    """高频抓取词条 TOP n"""
    counter = {}
    for l in data["vocab_lookups"]:
        if l.get("touchpoint") == touchpoint and l.get("word"):
            w = l["word"]
            counter[w] = counter.get(w, 0) + 1
    top = sorted(counter.items(), key=lambda x: -x[1])[:n]
    return [{"label": w, "value": c, "unit": "次"} for w, c in top]


def _call_time_buckets(data: dict) -> List[dict]:
    """通话时段分布（xiaoji_call_logs.started_at 按小时分桶）"""
    buckets = {"深夜(0-6点)": 0, "上午(6-12点)": 0, "下午(12-18点)": 0, "晚上(18-24点)": 0}
    for c in data["call_logs"]:
        try:
            # 按北京时间分桶（2026-08-26 修复：原按 UTC 小时）
            h = datetime.fromisoformat((c.get("started_at") or "").replace("Z", "+00:00")).astimezone(BEIJING).hour
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
    if not data["call_logs"]:
        return []
    return [{"label": k, "value": v, "unit": "次"} for k, v in buckets.items()]


def _call_stats(data: dict) -> tuple:
    """(通话次数, 总时长秒)"""
    rows = data["call_logs"]
    return len(rows), sum(r.get("duration_seconds") or 0 for r in rows)


# ============================================================
# 单智能体详情
# ============================================================

async def _agent_detail(agent_key: str, data: dict, since_days: int = 30) -> dict:
    touchpoints = _count_touchpoints(data, agent_key)
    calls = sum(t["count"] for t in touchpoints)

    if agent_key == "chat":
        chat_days = _chat_days(data)
        non_chat_days = {_day(r.get("created_at") or "") for r in data["records"]} - chat_days
        trend_label, trend_unit = "每日调用次数", "次/天"
        metric = {
            "label": "对话日做题量",
            "value": _records_per_day_on(data, chat_days),
            "unit": "题/天",
        }
        trend = _daily_series([a for a in data["actions"]], "action_at", since_days)
        stats = [
            {"label": "总调用", "value": calls, "unit": "次"},
            {"label": "对话日做题量", "value": metric["value"], "unit": "题/天"},
            {"label": "日志摘要", "value": len(data["logs"]), "unit": "条"},
        ]
        features = [
            {"title": "意图路由分布", "desc": "你的每个问题被分流去了哪里", "type": "bars",
             "source": "来自主对话区的使用记录",
             "items": [{"label": "答疑", "value": _action_count(data, "chat", "chat_main")},
                       {"label": "规划分流", "value": _action_count(data, "use_plan_agent", "chat_main")},
                       {"label": "生成分流", "value": _action_count(data, "use_generate_agent", "chat_main")},
                       {"label": "评估分流", "value": _action_count(data, "use_evaluate_agent", "chat_main")}]},
            {"title": "词条熟练度分布", "desc": "讲解过的词条熟练度构成", "type": "bars",
             "source": "统计自你的词条学习记录", "items": _word_mastery_dist(data)},
        ]
    elif agent_key == "plan":
        trend_label, trend_unit = "计划完成率", "%"
        metric = {"label": "计划完成率", "value": _plan_completion(data), "unit": "%"}
        trend = []
        for i in range(since_days - 1, -1, -1):
            d = (datetime.now(timezone.utc) - timedelta(days=i)).strftime("%Y-%m-%d")
            day_tasks = [t for t in data["tasks"] if _day(t.get("date") or "") == d]
            trend.append(_pct(sum(1 for t in day_tasks if t.get("completed")), len(day_tasks)) or 0)
        stats = [
            {"label": "总调用", "value": calls, "unit": "次"},
            {"label": "计划完成率", "value": metric["value"], "unit": "%"},
            {"label": "生成计划", "value": len(data["plans"]), "unit": "个"},
            {"label": "日均任务量",
             "value": round(sum(len(t.get("question_ids") or []) for t in data["tasks"]) / len(data["tasks"]), 1) if data["tasks"] else None,
             "unit": "个"},
        ]
        features = [
            {"title": "三阶段完成率", "desc": "基础 → 强化 → 冲刺", "type": "bars",
             "source": "按计划阶段统计", "items": _phase_rates(data)},
            {"title": "任务量与完成率", "desc": "每天任务越少，完成率越高", "type": "bars",
             "source": "按每日任务量分组", "items": _task_volume_rates(data)},
        ]
    elif agent_key == "generate":
        trend_label, trend_unit = "每日生成题量", "题/天"
        metric = {"label": "题集收录率", "value": _collection_rate(data), "unit": "%"}
        trend = _daily_series(data["gen_history"], "created_at", since_days)
        stats = [
            {"label": "总调用", "value": calls, "unit": "次"},
            {"label": "生成题量", "value": len(data["gen_history"]), "unit": "题"},
            {"label": "题集数", "value": len(data["sets"]), "unit": "个"},
            {"label": "题集收录率", "value": metric["value"], "unit": "%"},
        ]
        features = [
            {"title": "生成题难度分布", "desc": "近 30 天生成题目的难度构成", "type": "bars",
             "source": "按生成题难度统计", "items": _difficulty_buckets(data)},
            {"title": "收录率 vs 难度", "desc": "难度越高，越少被收进题集", "type": "bars",
             "source": "生成题被收进题集的比例", "items": _set_collection_rates(data)},
        ]
    elif agent_key == "evaluate":
        graded = sum(1 for r in data["records"] if r.get("ai_feedback"))
        trend_label, trend_unit = "每日批改题量", "题/天"
        metric = {"label": "批改题量", "value": graded, "unit": "题"}
        trend = _daily_series([r for r in data["records"] if r.get("ai_feedback")], "created_at", since_days)
        first_rate, last_rate = _redo_rates(data)
        stats = [
            {"label": "总调用", "value": calls, "unit": "次"},
            {"label": "批改题量", "value": graded, "unit": "题"},
            {"label": "真题交卷分析", "value": len(data["exams"]), "unit": "次"},
            {"label": "错因分析覆盖", "value": _exam_coverage(data), "unit": "%"},
        ]
        features = [
            {"title": "批改来源构成", "desc": "裁判工作都发生在哪里", "type": "bars",
             "source": "批改、真题分析、画像总结",
             "items": [{"label": "做题提交批改", "value": graded},
                       {"label": "真题交卷分析", "value": len(data["exams"])},
                       {"label": "画像 AI 总结", "value": sum(1 for s in data["profile_settings"] if _has_ai_summary(s))}]},
            {"title": "重做前后正确率", "desc": "批改过的题，重做正确率明显提升", "type": "compare",
             "source": "同一道题多次作答的对比",
             "items": [{"label": "首答正确率", "value": first_rate, "unit": "%"},
                       {"label": "批改后重做正确率", "value": last_rate, "unit": "%"}]},
        ]
    else:  # xiaoji
        xj_days = _xiaoji_days(data)
        non_xj_days = {_day(r.get("created_at") or "") for r in data["records"]} - xj_days
        trend_label, trend_unit = "每日做题量", "题/天"
        metric = {"label": "互动日做题量", "value": _records_per_day_on(data, xj_days), "unit": "题/天"}
        trend = _daily_series(data["records"], "created_at", since_days)
        call_count, call_seconds = _call_stats(data)
        stats = [
            {"label": "总调用", "value": calls, "unit": "次"},
            {"label": "通话次数", "value": call_count, "unit": "次"},
            {"label": "通话时长", "value": round(call_seconds / 60, 1) if call_seconds else 0, "unit": "分钟"},
            {"label": "互动天数", "value": len(xj_days), "unit": "天"},
        ]
        features = [
            {"title": "互动 vs 非互动日做题量", "desc": "有小基陪伴的日子，你多做了多少题", "type": "compare",
             "source": "陪伴日 vs 无陪伴日",
             "items": [{"label": "互动日平均", "value": metric["value"], "unit": "题/天"},
                       {"label": "非互动日平均", "value": _records_per_day_on(data, non_xj_days), "unit": "题/天"}]},
            {"title": "通话时段分布", "desc": "你习惯在什么时间找小基打电话", "type": "bars",
             "source": "统计自语音通话记录", "items": _call_time_buckets(data)},
            {"title": "高频抓取词条", "desc": "识图拍题提取最多的生词", "type": "bars",
             "source": "统计自你的识图提词记录", "items": _top_lookup_words(data)},
        ]

    return {
        "key": agent_key,
        "name": AGENT_NAMES[agent_key],
        "calls": calls,
        "metric": metric,
        "trend": trend,
        "trend_label": trend_label,
        "trend_unit": trend_unit,
        "stats": stats,
        "touchpoints": touchpoints,
        "features": features,
    }


# ============================================================
# 总览（协作分析）
# ============================================================

@router.get("/overview")
async def overview(user_id: str = Query(...), days: int = Query(30, ge=7, le=365),
                   current_user: str = Depends(get_current_user)):
    verify_user_match(user_id, current_user)
    since = _since_iso(days)
    data = await _collect(user_id, since)
    agents = {}
    for key in TOUCHPOINTS:
        agents[key] = await _agent_detail(key, data, days)

    # 总调用次数：action 类触点会被「分流 × 触达」两个视角引用同一条记录，各 agent 相加会重复计
    # → action 部分按去重事件数统计；业务表类触点（计划数/批改数/小基消息…）各自独立，正常相加
    biz_calls = 0
    for key in TOUCHPOINTS:
        for tp, counted in zip(TOUCHPOINTS[key], _count_touchpoints(data, key)):
            if tp["source"] not in ACTION_SOURCES:
                biz_calls += counted["count"]
    total_calls = _distinct_action_count(data) + biz_calls
    active = sum(1 for a in agents.values() if a["calls"] > 0)

    # 小基陪伴线（并行入口）
    xj_days = _xiaoji_days(data)
    non_xj_days = {_day(r.get("created_at") or "") for r in data["records"]} - xj_days
    xj_on = _records_per_day_on(data, xj_days)
    xj_off = _records_per_day_on(data, non_xj_days)
    xiaoji_line = {
        "text": (f"小基陪伴线（并行入口）：互动日做题 "
                 f"{xj_on if xj_on is not None else '—'} vs 非互动日 {xj_off if xj_off is not None else '—'} 题/天"),
        "source": "对比有小基陪伴和没有陪伴的日子",
    }

    # ===== 协作闭环 =====
    chat_in = agents["chat"]["calls"]
    plan_tasks = sum(1 for t in data["tasks"] if t.get("learning_content"))
    graded = sum(1 for r in data["records"] if r.get("ai_feedback"))
    mastery_gen = _action_count(data, "generate_question", "mastery_generate")
    weak = _weak_kp_count(data)
    loop = [
        {"step": "问题入口", "agent_key": "chat",
         "text": f"{chat_in} 次对话", "sub": "对话与智能体分流的总次数"},
        {"step": "计划与任务", "agent_key": "plan",
         "text": f"{len(data['plans'])} 个计划 · {plan_tasks} 次讲解",
         "sub": "已生成的计划与学习讲解次数"},
        {"step": "练习与批改", "agent_key": "evaluate",
         "text": f"{graded} 题批改", "sub": "AI 批改过的题目数"},
        {"step": "错题定向", "agent_key": "generate",
         "text": f"{mastery_gen} 次定向生成", "sub": "针对薄弱点的定向出题次数"},
        {"step": "掌握度", "agent_key": None,
         "text": f"{weak} 个薄弱知识点",
         "sub": "掌握度低于 60% 的知识点数"},
    ]

    # ===== 协同增益 =====
    def _completion_on(days_set: set) -> Optional[float]:
        if not days_set:
            return None
        rows = [t for t in data["tasks"] if _day(t.get("date") or "") in days_set]
        return _pct(sum(1 for t in rows if t.get("completed")), len(rows)) if rows else None

    with_lc, without_lc = _tasks_learning_rates(data)
    first_rate, last_rate = _redo_rates(data)
    chat_days = _chat_days(data)
    non_chat_days = {_day(r.get("created_at") or "") for r in data["records"]} - chat_days

    def _syn(agent_a, agent_b, metric, base, boost, note, source, unit):
        delta = None
        if base is not None and boost is not None:
            delta = round(boost - base, 1)
        return {"pair": [agent_a, agent_b], "metric": metric,
                "base": base, "boost": boost, "delta": delta, "unit": unit,
                "note": note, "source": source}

    synergy = [
        _syn("xiaoji", "plan", "计划完成率",
             _completion_on(non_xj_days), _completion_on(xj_days),
             "互动日 vs 非互动日", "陪伴日 vs 无陪伴日的计划完成情况", "%"),
        _syn("plan", "practice", "任务完成率",
             without_lc, with_lc,
             "有讲解 vs 无讲解", "有 AI 讲解 vs 无讲解的任务完成情况", "%"),
        _syn("evaluate", "practice", "重做正确率",
             first_rate, last_rate,
             "首答 vs 批改后重做", "同一道题多次作答的对比", "%"),
        _syn("generate", "mastery", "薄弱知识点数",
             None, weak,
             "当前薄弱点数（前后对比 v2）", "薄弱知识点统计", "个"),
        _syn("chat", "practice", "做题量",
             _records_per_day_on(data, non_chat_days), _records_per_day_on(data, chat_days),
             "对话日 vs 非对话日", "有对话 vs 无对话的日子", "题/天"),
    ]

    # ===== 路由转化 =====
    def _route(agent_key, output_desc, output_val, rate, rate_unit, warn, note):
        return {"agent_key": agent_key,
                "uses": _action_count(data, f"use_{agent_key}_agent"),
                "output": f"{output_val} {output_desc}" if output_val is not None else None,
                "rate": rate, "rate_unit": rate_unit, "warn": warn, "note": note}

    plan_uses = _action_count(data, "use_plan_agent")
    gen_uses = _action_count(data, "use_generate_agent")
    eva_uses = _action_count(data, "use_evaluate_agent")
    plan_rate = _pct(len(data["plans"]), plan_uses)
    gen_rate = round(len(data["gen_history"]) / gen_uses, 1) if gen_uses else None
    routing = [
        _route("plan", "个计划", len(data["plans"]),
               plan_rate, "%", plan_rate is not None and plan_rate < 30,
               "聊天里问规划 → 实际生成的计划"),
        _route("generate", "道生成题", len(data["gen_history"]),
               gen_rate, "题/次", False,
               "聊天里出题 → 生成的题目数（含其他入口，近似）"),
        _route("evaluate", None, None, None, None, False,
               "聊天里的评估产出暂未单独统计"),
    ]

    # ===== 动态结论 =====
    pos_syn = sum(1 for s in synergy if s["delta"] is not None and s["delta"] > 0)
    synergy_summary = (
        f"结论：{len(synergy)} 对协同中 {pos_syn} 对为正增益——陪伴、讲解、批改、定向生成都在真实拉动学习效果。"
        if pos_syn else "结论：协同数据积累中，暂时没有足够的对照样本。"
    )
    warn_routes = [r for r in routing if r["warn"]]
    routing_summary = (
        f"结论：{warn_routes[0]['agent_key']} 分流转化偏低，是当前最明显的瓶颈链路。"
        if warn_routes else "结论：各分流链路转化正常，暂无瓶颈。"
    )

    return {
        "range_days": days,
        "kpi": {
            "total_calls": total_calls,
            "active_agents": f"{active} / 5",
            "plan_completion": _plan_completion(data),
            "generated_questions": len(data["gen_history"]),
            "graded_questions": graded,
            "vocab_lookups": len(data["vocab_lookups"]),
        },
        "loop": loop,
        "xiaoji_line": xiaoji_line,
        "synergy": synergy,
        "synergy_summary": synergy_summary,
        "routing": routing,
        "routing_summary": routing_summary,
        "agents": [
            {"key": a["key"], "name": a["name"], "calls": a["calls"],
             "metric": a["metric"], "trend": a["trend"]}
            for a in agents.values()
        ],
    }


@router.get("/agents/{agent_key}")
async def agent_detail(agent_key: str, user_id: str = Query(...), days: int = Query(30, ge=7, le=365),
                       current_user: str = Depends(get_current_user)):
    verify_user_match(user_id, current_user)
    if agent_key not in TOUCHPOINTS:
        raise HTTPException(status_code=404, detail="未知智能体")
    since = _since_iso(days)
    data = await _collect(user_id, since)
    return await _agent_detail(agent_key, data, days)


# ============================================================
# 参数（agent_prefs）
# ============================================================

class PrefItem(BaseModel):
    param_key: str
    value: Any = None
    auto_managed: bool = False


@router.get("/agents/{agent_key}/prefs")
async def get_prefs(agent_key: str, user_id: str = Query(...),
                    current_user: str = Depends(get_current_user)):
    verify_user_match(user_id, current_user)
    rows = await _get("agent_prefs", {
        "user_id": f"eq.{user_id}", "agent_key": f"eq.{agent_key}",
        "select": "id,param_key,param_value,auto_managed", "limit": "500",
    })
    return [{"param_key": r["param_key"], "value": r.get("param_value"),
             "auto_managed": r.get("auto_managed", False)} for r in rows]


@router.put("/agents/{agent_key}/prefs")
async def put_prefs(agent_key: str, user_id: str = Query(...),
                    prefs: List[PrefItem] = Body(...),
                    current_user: str = Depends(get_current_user)):
    verify_user_match(user_id, current_user)
    existing = await _get("agent_prefs", {
        "user_id": f"eq.{user_id}", "agent_key": f"eq.{agent_key}",
        "select": "id,param_key", "limit": "500",
    })
    by_key = {r["param_key"]: r for r in existing}
    now = _now_iso()
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            for p in prefs:
                payload = {"param_value": p.value, "auto_managed": p.auto_managed, "updated_at": now}
                if p.param_key in by_key:
                    res = await client.patch(
                        f"{settings.SUPABASE_URL}/rest/v1/agent_prefs?id=eq.{by_key[p.param_key]['id']}",
                        headers=_headers(), json=payload)
                else:
                    payload.update({"user_id": user_id, "agent_key": agent_key, "param_key": p.param_key})
                    res = await client.post(
                        f"{settings.SUPABASE_URL}/rest/v1/agent_prefs",
                        headers=_headers(), json=payload)
                if res.status_code not in (200, 201, 204):
                    raise HTTPException(status_code=500, detail=f"保存参数失败({p.param_key}): {res.status_code} {res.text[:200]}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存参数失败: {str(e)}")
    return {"success": True}


# ============================================================
# 磨合记录（agent_tuning_log）
# ============================================================

class TuningItem(BaseModel):
    param_key: str
    old_value: Any = None
    new_value: Any = None
    reason: str = ""
    source: str = "manual"  # manual / auto


@router.get("/agents/{agent_key}/tuning")
async def get_tuning(agent_key: str, user_id: str = Query(...),
                     current_user: str = Depends(get_current_user)):
    verify_user_match(user_id, current_user)
    return await _get("agent_tuning_log", {
        "user_id": f"eq.{user_id}", "agent_key": f"eq.{agent_key}",
        "select": "param_key,old_value,new_value,reason,source,created_at",
        "order": "created_at.desc", "limit": "100",
    })


@router.post("/agents/{agent_key}/tuning")
async def post_tuning(agent_key: str, user_id: str = Query(...),
                      item: TuningItem = Body(...),
                      current_user: str = Depends(get_current_user)):
    verify_user_match(user_id, current_user)
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.post(
                f"{settings.SUPABASE_URL}/rest/v1/agent_tuning_log",
                headers=_headers(),
                json={"user_id": user_id, "agent_key": agent_key,
                      "param_key": item.param_key, "old_value": item.old_value,
                      "new_value": item.new_value, "reason": item.reason,
                      "source": item.source, "created_at": _now_iso()})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"写入磨合记录失败: {str(e)}")
    if res.status_code not in (200, 201):
        raise HTTPException(status_code=500, detail=f"写入磨合记录失败: {res.status_code}")
    return {"success": True}


# ============================================================
# 磨合规则引擎（立即评估；后台每日评估见 agents/tuning.py）
# ============================================================

@router.post("/tuning/run")
async def run_tuning(user_id: str = Query(...),
                     current_user: str = Depends(get_current_user)):
    """立即执行一次磨合规则评估（详情页「立即评估」按钮）"""
    verify_user_match(user_id, current_user)
    from agents.tuning import run_tuning_for_user
    applied = await run_tuning_for_user(user_id)
    return {"success": True, "applied": applied}
