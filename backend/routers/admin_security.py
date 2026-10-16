"""安全中心 · 管理后台（2026-10-15）

三块东西共用一个前缀，各自对应一张（组）表、一份建表脚本、一个前端 Tab：

  1. 安全事件（security_events）      ← sql/security_center.sql
     问的是「谁在攻击」。只记失败和拦截。
     写入方 utils/security_log.py：中间件自动写（限流命中、鉴权失败、越权）
     和业务主动写（冒充他人 user_id、违禁词命中、信誉扣分）。

  2. 用户信誉（user_reputation 等四张）← sql/reputation.sql
     问的是「这个人整体可不可信」。可以手动改分，但每步都留痕。
     引擎在 utils/reputation.py。

  3. 生成审计（ai_generation_audit）   ← sql/ai_generation_audit.sql
     问的是「我们的 AI 生成跑成什么样」。成功失败都记。
     写入方 utils/gen_audit.py，由 utils/safety_gateway.py 每次生成调用。

⚠️ 报错时要指向**对应的那一份** SQL —— 见 _fail 的 sql_file 参数。

拆分理由同 admin_video.py：admin.py 已经 1400+ 行，安全中心是独立的一块。
"""

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, List, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from config import settings
from logging_config import logger
from services.supabase import ilike_term_params
from utils.admin_middleware import get_current_admin, write_audit_log
from utils.security_log import known_event_types

router = APIRouter(prefix="/admin/security", tags=["管理后台·安全中心"])

# ⚠️ 总览聚合的取数上限。
#
# 为什么在 Python 里聚合而不是走 SQL GROUP BY：
#   PostgREST 不暴露 GROUP BY；走 RPC 要往库里加函数，而 security_center.sql
#   已经执行过了，加函数就得让人再跑一次 DDL。权衡下来先用「取回来自己数」。
#
# ⚠️ 但**必须有上限**，且**触顶时要如实报出来**（见 truncated 字段）。
#   本项目反复吃过「静默降级」的亏：数字看起来正常、其实只统计了一部分，
#   比报错还难查。触顶时宁可告诉使用者"这个数不全"，也不假装它是准的。
#
# 什么时候该换成 RPC：单次窗口内的行数稳定超过这个上限，
# 也就是**真的在被持续攻击**的时候 —— 那时正是最需要数字准的时候。
_AGG_FETCH_LIMIT = 5000

_SEVERITY_ORDER = {"critical": 0, "high": 1, "warn": 2, "info": 3}


class PaginatedResponse(BaseModel):
    items: List[Any] = []
    total: int = 0
    page: int = 1
    page_size: int = 20


class ReputationSet(BaseModel):
    score: int
    reason: str


def _rows(resp) -> List[dict]:
    if getattr(resp, "status_code", 300) >= 300:
        return []
    try:
        data = resp.json()
    except Exception:
        return []
    return data if isinstance(data, list) else []


def _fail(label: str, res: httpx.Response, sql_file: str = "security_center.sql") -> None:
    """
    上游失败 → 明确报 502，**不要伪装成「暂无数据」**。

    同 admin.py 的 _fail_upstream：读端点把非 200 降级成空列表，会让
    「表没建 / GRANT 没给 / 网络挂了」全部表现成「暂无安全事件」——
    而安全中心显示"没有攻击"，恰恰是最危险的一种假象。

    sql_file：本模块跨了三份建表脚本，报错要指向**对应的那一份**。
              写死成 security_center.sql 的话，生成审计表缺失时会把人引到
              一份根本不含该表的脚本上去。
    """
    logger.error(f"安全中心·{label} 查询失败 status={res.status_code} body={res.text[:300]}")
    raise HTTPException(
        status_code=502,
        detail=f"{label}查询失败（上游 {res.status_code}）。"
               f"若提示表不存在或权限不足，请确认 {sql_file} 已执行。",
    )


def _safe_total(res: httpx.Response) -> int:
    try:
        cr = res.headers.get("content-range", "")
        if "/" in cr:
            return int(cr.split("/")[-1])
    except Exception:
        pass
    return 0


async def _fetch(table: str, params: dict | None = None,
                 extra_headers: dict | None = None) -> httpx.Response:
    """
    ⚠️ 查询条件走 `params=` 交给 httpx 编码，**不要自己拼查询串**。

    2026-10-15 就是手工拼的，踩了个很安静的坑：
    `since.isoformat()` 产出的是 `2026-10-08T12:15:57.613420+00:00`，
    而 `+` 在 query string 里**等于空格** —— 服务端收到的是 `...613420 00:00`，
    PostgREST 回 400 `invalid input syntax for type timestamp with time zone`。

    后果分两档：`/overview` 的时间窗是**无条件**加的 → 整个总览页 502（页面空白）；
    `/events` 只在带日期筛选时才加 → 默认页看着好好的，**一筛选时间就挂**。
    两处单测都是绿的 —— 假后端不做真实的 URL 解析，这类问题只有真库才暴露。
    """
    url = f"{settings.SUPABASE_URL}/rest/v1/{table}"
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
    }
    if extra_headers:
        headers.update(extra_headers)
    async with httpx.AsyncClient(timeout=20.0) as client:
        return await client.get(url, headers=headers, params=params)


# ============================
# 筛选器选项
# ============================

@router.get("/filters")
async def security_filters(current_admin: str = Depends(get_current_admin)):
    """
    给前端筛选器用的可选项。

    事件类型从 utils/security_log.py 的登记表来，**不是**从库里 select distinct ——
    后者在冷启动（还没有任何事件）时返回空，筛选器就是死的；
    而且它只能反映"发生过的"，反映不了"支持哪些"。
    """
    return {
        "event_types": sorted(known_event_types()),
        "severities": ["critical", "high", "warn", "info"],
    }


# ============================
# 事件列表
# ============================

@router.get("/events", response_model=PaginatedResponse)
async def list_security_events(
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    event_type: str = Query(""),
    severity: str = Query(""),
    ip: str = Query(""),
    user_id: str = Query(""),
    endpoint: str = Query(""),
    days: int = Query(0, ge=0, le=90),   # 0 = 不限时间
    current_admin: str = Depends(get_current_admin),
):
    """安全事件列表。默认按时间倒序。"""
    params: dict = {
        "select": "*",
        "order": "occurred_at.desc",
        "limit": page_size,
        "offset": (page - 1) * page_size,
    }
    if event_type:
        params["event_type"] = f"eq.{event_type}"
    if severity:
        params["severity"] = f"eq.{severity}"
    if ip:
        params["ip"] = f"eq.{ip}"
    if user_id:
        params["user_id"] = f"eq.{user_id}"
    if endpoint:
        params["endpoint"] = f"like.*{endpoint}*"
    if days:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        params["occurred_at"] = f"gte.{since.isoformat()}"

    res = await _fetch("security_events", params, {"Prefer": "count=exact"})
    if res.status_code not in (200, 206):
        _fail("安全事件", res)

    return PaginatedResponse(
        items=_rows(res), total=_safe_total(res), page=page, page_size=page_size
    )


# ============================
# 总览
# ============================

@router.get("/overview")
async def security_overview(
    days: int = Query(7, ge=1, le=30),
    top_n: int = Query(10, ge=1, le=50),
    current_admin: str = Depends(get_current_admin),
):
    """
    总览聚合。一次取回窗口内的行，在 Python 里数 —— 见文件头 _AGG_FETCH_LIMIT 的说明。
    """
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=days)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Supabase/PostgREST 默认单次最多返回 1000 行，所以要显式声明 Prefer。
    # 拿不到更多时宁可知情地截断（truncated=True），也不要装作数全了。
    res = await _fetch(
        "security_events",
        {
            "select": "event_type,severity,ip,user_id,endpoint,status_code,occurred_at",
            "occurred_at": f"gte.{since.isoformat()}",
            "order": "occurred_at.desc",
            "limit": _AGG_FETCH_LIMIT,
        },
        {"Prefer": "count=exact"},
    )
    if res.status_code not in (200, 206):
        _fail("安全事件总览", res)

    rows = _rows(res)
    total_in_window = _safe_total(res) or len(rows)
    truncated = total_in_window > len(rows)

    by_type: Counter = Counter()
    by_severity: Counter = Counter()
    by_ip: Counter = Counter()
    by_user: Counter = Counter()
    by_day: dict[str, int] = defaultdict(int)
    by_endpoint: Counter = Counter()

    today_count = 0
    low_severity_high = 0

    for r in rows:
        et = r.get("event_type") or "(未知)"
        sev = r.get("severity") or "info"
        by_type[et] += 1
        by_severity[sev] += 1
        if r.get("ip"):
            by_ip[r["ip"]] += 1
        if r.get("user_id"):
            by_user[r["user_id"]] += 1
        if r.get("endpoint"):
            by_endpoint[r["endpoint"]] += 1
        if sev in ("high", "critical"):
            low_severity_high += 1

        ts = r.get("occurred_at") or ""
        if ts:
            by_day[ts[:10]] += 1
            try:
                if datetime.fromisoformat(ts.replace("Z", "+00:00")) >= today_start:
                    today_count += 1
            except Exception:
                pass

    # 趋势补齐空白天 —— 否则图上会把"那天没有事件"画成断点
    trend = []
    for i in range(days - 1, -1, -1):
        d = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        trend.append({"date": d, "count": by_day.get(d, 0)})

    return {
        "window_days": days,
        "since": since.isoformat(),
        "total_in_window": total_in_window,
        "today_count": today_count,
        # ⚠️ 为 True 说明上面所有数字**只统计了前 _AGG_FETCH_LIMIT 条**，
        #    前端要显式提示，不能当准数看。见 _AGG_FETCH_LIMIT 注释。
        "truncated": truncated,
        "scanned": len(rows),
        "high_or_critical": low_severity_high,
        # 去重后的真实个数 —— 不要去拿 top_ips 的长度充数，
        # 那个榜被 top_n 截断过，显示出来会是个偏小的假数字。
        "distinct_ips": len(by_ip),
        "distinct_users": len(by_user),
        "by_severity": [
            {"key": k, "count": v}
            for k, v in sorted(by_severity.items(), key=lambda x: _SEVERITY_ORDER.get(x[0], 9))
        ],
        "by_type": [{"key": k, "count": v} for k, v in by_type.most_common(top_n)],
        "by_endpoint": [{"key": k, "count": v} for k, v in by_endpoint.most_common(top_n)],
        "top_ips": [{"key": k, "count": v} for k, v in by_ip.most_common(top_n)],
        "top_users": [{"key": k, "count": v} for k, v in by_user.most_common(top_n)],
        "trend": trend,
    }


# ============================
# 用户信誉（第二期）
#
# 与安全事件的区别：事件是**客观流水**（谁在什么时候触发了什么），
# 信誉分是**主观结论**（这个人整体上可不可信）。管理员在这里改的是后者，
# 所以每一次改动都强制写理由 + 记 operator_id，且要能被用户查到。
# ============================

@router.get("/users/{user_id}/reputation")
async def get_user_reputation(
    user_id: str,
    history_limit: int = Query(50, ge=1, le=200),
    current_admin: str = Depends(get_current_admin),
):
    """某个用户的信誉分 + 档位 + 完整变更历史。"""
    from utils.reputation import get_history, streak_days, next_recovery_in_days, get_tier

    tier = await get_tier(user_id)
    streak = await streak_days(user_id)
    return {
        "user_id": user_id,
        "score": tier.get("score"),
        "tier": tier.get("code"),
        "tier_label": _TIER_LABEL.get(tier.get("code"), tier.get("code")),
        "ai_daily_quota": tier.get("ai_daily_quota"),
        "content_needs_review": bool(tier.get("content_needs_review")),
        "can_publish": bool(tier.get("can_publish")),
        "streak_days": streak,
        "days_to_next_tier": await next_recovery_in_days(user_id, streak),
        "history": await get_history(user_id, history_limit),
    }


@router.put("/users/{user_id}/reputation")
async def set_user_reputation(
    user_id: str,
    body: ReputationSet,
    current_admin: str = Depends(get_current_admin),
):
    """
    手动设分。**理由必填** —— 不写理由的手动改分，三个月后没人说得清为什么。

    ⚠️ 手动改分**绕过 once_per_day / daily_cap**：
       那是自动规则的节流阀，管理员的人工决定不该被系统挡。
       但留痕一点不少（admin.manual 流水 + operator_id + 审计日志）。
    """
    from utils.reputation import admin_set

    if not (body.reason or "").strip():
        raise HTTPException(status_code=422, detail="必须填写修改理由")

    try:
        result = await admin_set(user_id, body.score, body.reason, current_admin)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    if result is None:
        # admin_set 返回 None = 并发冲突重试失败，不是"成功"
        raise HTTPException(status_code=409, detail="信誉分被并发修改，请刷新后重试")

    await write_audit_log(
        admin_id=current_admin,
        action="set_reputation",
        target_type="user",
        target_id=user_id,
        detail={"from": result["score_before"], "to": result["score_after"],
                "reason": body.reason.strip()[:200]},
    )
    return {"success": True, **result}


# ⚠️ 全站用户列表的取数上限。
#
# 为什么这一页也要「取回窗口自己算」，而不是全下推给 PostgREST：
#   这一页的语义是 profiles LEFT JOIN user_reputation（**没行 = 从未变动 = 满分**），
#   而 PostgREST 的过滤器表达不了「嵌入资源为空**或**满足条件」——
#   2026-10-16 实测：`or=(user_reputation.score.is.null,...)` 直接 PGRST100 语法错；
#   加 `!inner` 又会把没行的用户整个排除掉，那**正是这次要修的病**。
#   所以取回来自己合并、筛选、排序。同 security_overview 的 _AGG_FETCH_LIMIT。
#
#   触顶时如实标 truncated，不假装是全量 —— 本项目反复强调的那条。
_REP_FETCH_LIMIT = 5000


class ReputationListResponse(PaginatedResponse):
    """信誉列表。比通用分页多两个「别让数字骗人」的字段。"""
    truncated: bool = False      # 取数触顶：这个 total 不是全量
    with_record: int = 0         # 其中真正有 user_reputation 行的人数


@router.get("/reputation/list", response_model=ReputationListResponse)
async def list_reputation(
    tier: str = Query("", description="按档位筛选，留空=全部"),
    search: str = Query("", description="按昵称/邮箱/账号模糊搜，留空=全部"),
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    current_admin: str = Depends(get_current_admin),
):
    """
    信誉分列表（**全站用户**，低分在前）。

    ⚠️ 2026-10-16 改：这里**不再只列 user_reputation 里有行的用户**。
    那张表是**懒创建**的 —— 见 utils/reputation.py 的 apply_delta：满分继续加分时
    `after == before` 直接 return，根本走不到 _ensure_row。所以「有行」只说明
    **分数被动过**，不说明这个人有问题。改之前列表里只有 1 个人、而且还是个满分的：
    管理员看到的是「全站 23 个用户里只有 1 个有信誉分」—— 正是本项目反复强调的
    「数字不全比没有数字更危险」。

    现在以 profiles 为准左连接：**没行 = 从未变动 = 满分**，
    与 utils/reputation.py 的 get_score() 完全同口径（那才是全站判定用的那个）。

    想查某个具体用户还是走上面的单个接口；这个列表是「扫一遍谁有问题」用的。
    """
    # DEFAULT_SCORE / _tier_for 都从引擎那边取，**不在这里重写一遍**：
    # 档位边界和默认分只有一处实现，抄第二遍的话改阈值时两边会悄悄分叉。
    # （下划线是私有的，但这个 router 本来就是 reputation.py 的展示层。）
    from utils.reputation import DEFAULT_SCORE, _tier_for, load_rules

    rules = await load_rules()
    tiers = rules.get("tiers") or []
    if tier and not any(t.get("code") == tier for t in tiers):
        raise HTTPException(status_code=422, detail=f"未知档位 {tier}")

    params: dict = {
        "select": "id,nickname,user_account,email,is_active,created_at,"
                  "user_reputation(score,updated_at)",
        "order": "created_at.desc",
        "limit": _REP_FETCH_LIMIT,
    }
    term = search.strip()
    if term:
        # 通配符用 * 不用 %。搜索词过的是 **ilike_term_params** 而不是 ilike_term ——
        # 这里走 httpx 的 params=，用会 quote() 的那个版本会被再编一次码，
        # 中文直接搜不到（而且还是 200）。两个函数的区别见 services/supabase.py。
        t = ilike_term_params(term)
        params["or"] = (f"(nickname.ilike.*{t}*,email.ilike.*{t}*,"
                        f"user_account.ilike.*{t}*)")

    res = await _fetch("profiles", params)
    if res.status_code not in (200, 206):
        _fail("信誉列表", res, "reputation.sql")

    rows = _rows(res)
    truncated = len(rows) >= _REP_FETCH_LIMIT

    items: List[dict] = []
    for r in rows:
        # ⚠️ 用 get 不用 pop —— 不就地改 _rows() 交出来的那些行。
        # 生产上每次响应都是新解析的对象，改了也看不出来；但一旦有"同一份行
        # 被处理两次"的情形（测试夹具就是），pop 会让第二次全部退化成"没有行",
        # 于是所有人都变成满分 —— 静默错，最难查的那种。测试里就是这么抓到的。
        rep = r.get("user_reputation")
        if isinstance(rep, list):        # 一对一时 PostgREST 给对象，兜一下数组形态
            rep = rep[0] if rep else None
        has_record = isinstance(rep, dict) and rep.get("score") is not None
        score = int(rep["score"]) if has_record else DEFAULT_SCORE
        code = _tier_for(score, tiers).get("code")
        if tier and code != tier:
            continue
        items.append({
            "user_id": r.get("id"),
            "nickname": r.get("nickname"),
            "user_account": r.get("user_account"),
            "email": r.get("email"),
            "is_active": r.get("is_active"),
            "score": score,
            "tier": code,
            "tier_label": _TIER_LABEL.get(code, code),
            # False = 从没变动过，这个分数是「没行即满分」算出来的，不是库里的值。
            # 前端要据此说明来源，否则「23 个人都是 100」会被当成 23 条真实记录。
            "has_record": has_record,
            "updated_at": (rep or {}).get("updated_at") if isinstance(rep, dict) else None,
            "_created": r.get("created_at") or "",
        })

    # 低分在前；同分的按注册时间早的在前 —— 排序必须是**全序**，
    # 否则同分用户在不同请求间会换位，翻页时漏人/重人。
    items.sort(key=lambda x: (x["score"], x["_created"]))

    total = len(items)
    with_record = sum(1 for it in items if it["has_record"])
    start = (page - 1) * page_size
    page_items = items[start:start + page_size]
    for it in page_items:
        it.pop("_created", None)

    return ReputationListResponse(items=page_items, total=total, page=page,
                                  page_size=page_size, truncated=truncated,
                                  with_record=with_record)


@router.get("/reputation/rules")
async def get_reputation_rules(current_admin: str = Depends(get_current_admin)):
    """规则 + 档位配置（后台展示与调参用）。改值直接 UPDATE 表，这里只读。"""
    from utils.reputation import list_rules, list_tiers
    return {"rules": await list_rules(), "tiers": await list_tiers()}


# ============================
# 生成审计（第三期）
#
# 数据来自 ai_generation_audit 表，由 utils/safety_gateway.py 每次生成写一行。
#
# 与「安全事件」的区别：那边问的是「谁在攻击」（只记失败和拦截），
# 这边问的是「我们的 AI 生成跑成什么样」（成功失败都记）。
# 两张表分开的理由见 sql/ai_generation_audit.sql 的文件头。
#
# ⚠️ 覆盖率取决于「有多少调用点已经迁到网关」。现在只迁了 2/40，
#    所以这一页的数字**只代表走网关的那部分**，不是全站。前端必须显式说明，
#    否则会被当成全量 —— 那正是这个项目反复强调的「数字不全比没有数字更危险」。
# ============================

# 网关调用点的登记表。迁一个加一个 —— 前端用它把「还有多少没迁」显示出来。
_GATEWAY_COVERAGE = {"migrated": 2, "total": 40}
_GATEWAY_MIGRATED_PURPOSES = ["question_gen", "question_evaluate"]


@router.get("/gen-audit/overview")
async def gen_audit_overview(
    days: int = Query(7, ge=1, le=30),
    top_n: int = Query(10, ge=1, le=50),
    current_admin: str = Depends(get_current_admin),
):
    """
    生成审计总览：成功率 / 按用途 / 按模型 / 耗时 / 趋势。

    同 security_overview：PostgREST 不暴露 GROUP BY，取回窗口内的行在 Python 里数。
    超上限时如实标 truncated。
    """
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=days)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    res = await _fetch(
        "ai_generation_audit",
        {
            "select": "purpose,status,provider,model,user_id,latency_ms,"
                      "input_chars,output_chars,created_at",
            "created_at": f"gte.{since.isoformat()}",
            "order": "created_at.desc",
            "limit": _AGG_FETCH_LIMIT,
        },
        {"Prefer": "count=exact"},
    )
    if res.status_code not in (200, 206):
        _fail("生成审计总览", res, "ai_generation_audit.sql")

    rows = _rows(res)
    total_in_window = _safe_total(res) or len(rows)
    truncated = total_in_window > len(rows)

    by_status: Counter = Counter()
    by_purpose: Counter = Counter()
    by_model: Counter = Counter()
    by_user: Counter = Counter()
    by_day: dict[str, int] = defaultdict(int)
    latencies: list[int] = []
    today_count = 0
    failed = 0
    chars_in = 0
    chars_out = 0

    for r in rows:
        st = r.get("status") or "(未知)"
        by_status[st] += 1
        by_purpose[r.get("purpose") or "(未知)"] += 1
        by_model[r.get("model") or "(未记)"] += 1
        if r.get("user_id"):
            by_user[r["user_id"]] += 1
        if st != "ok":
            failed += 1
        chars_in += int(r.get("input_chars") or 0)
        chars_out += int(r.get("output_chars") or 0)

        lat = r.get("latency_ms")
        if isinstance(lat, int) and lat >= 0:
            latencies.append(lat)

        ts = r.get("created_at") or ""
        if ts:
            by_day[ts[:10]] += 1
            try:
                if datetime.fromisoformat(ts.replace("Z", "+00:00")) >= today_start:
                    today_count += 1
            except Exception:
                pass

    latencies.sort()

    def _pct(p: float) -> Optional[int]:
        if not latencies:
            return None
        idx = min(len(latencies) - 1, max(0, int(round(p * (len(latencies) - 1)))))
        return latencies[idx]

    trend = []
    for i in range(days - 1, -1, -1):
        d = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        trend.append({"date": d, "count": by_day.get(d, 0)})

    scanned = len(rows)
    return {
        "window_days": days,
        "since": since.isoformat(),
        "total_in_window": total_in_window,
        "today_count": today_count,
        "truncated": truncated,
        "scanned": scanned,
        "failed": failed,
        # 失败率按**实际扫到的行**算 —— 分母用 total_in_window 的话，
        # 触顶时会把没扫到的那部分当成"全成功"，把失败率稀释掉。
        "fail_rate": round(failed / scanned, 4) if scanned else None,
        "distinct_users": len(by_user),
        "chars_in": chars_in,
        "chars_out": chars_out,
        "latency": {
            "avg": int(sum(latencies) / len(latencies)) if latencies else None,
            "p50": _pct(0.50),
            "p95": _pct(0.95),
            "max": latencies[-1] if latencies else None,
            "samples": len(latencies),
        },
        "by_status": [{"key": k, "count": v} for k, v in by_status.most_common()],
        "by_purpose": [{"key": k, "count": v} for k, v in by_purpose.most_common(top_n)],
        "by_model": [{"key": k, "count": v} for k, v in by_model.most_common(top_n)],
        "top_users": [{"key": k, "count": v} for k, v in by_user.most_common(top_n)],
        "trend": trend,
        # 覆盖率：这一页只代表走网关的那部分调用点，必须显式告诉看的人
        "coverage": {**_GATEWAY_COVERAGE, "purposes": _GATEWAY_MIGRATED_PURPOSES},
    }


@router.get("/gen-audit")
async def list_gen_audit(
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    purpose: str = Query(""),
    status: str = Query(""),
    model: str = Query(""),
    user_id: str = Query(""),
    days: int = Query(0, ge=0, le=90),   # 0 = 不限时间
    only_failed: bool = Query(False),
    current_admin: str = Depends(get_current_admin),
):
    """生成审计明细。默认按时间倒序。"""
    params: dict = {
        "select": "*",
        "order": "created_at.desc",
        "limit": page_size,
        "offset": (page - 1) * page_size,
    }
    if purpose:
        params["purpose"] = f"eq.{purpose}"
    if model:
        params["model"] = f"eq.{model}"
    if user_id:
        params["user_id"] = f"eq.{user_id}"

    if only_failed:
        # 失败是「除 ok 之外」，用 neq 一条搞定（比 in.(...) 短，也不怕状态变多）
        params["status"] = "neq.ok"
    elif status:
        params["status"] = f"eq.{status}"

    if days:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        params["created_at"] = f"gte.{since.isoformat()}"

    res = await _fetch("ai_generation_audit", params, {"Prefer": "count=exact"})
    if res.status_code not in (200, 206):
        _fail("生成审计", res, "ai_generation_audit.sql")

    return PaginatedResponse(items=_rows(res), total=_safe_total(res),
                             page=page, page_size=page_size)


_TIER_LABEL = {"excellent": "优良", "normal": "正常", "restricted": "受限", "high_risk": "高危"}
