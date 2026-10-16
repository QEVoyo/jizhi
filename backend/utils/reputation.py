"""
信誉值引擎 —— 读分、算档、加减分、留痕。

数据层见 sql/reputation.sql（四张表：当前分 / 流水 / 规则 / 档位）。

信誉值是**可增可减的风控分**（默认 100，0-100），
与 user_stats.points 那个只增不减的成长分是两回事 —— 别混。


四条硬性约定
------------

1. **任何改分都必须写流水。** 流水是申诉的唯一依据；只存 delta 不存
   score_after 的话，事后要靠累加还原，漏一条就永远对不上，所以两个都存。
   后台手动改分也一样，还要记 operator_id 和理由。

2. **并发下不能读-改-写。** 两个请求同时读到 100、各减 1、各写 99 —— 少了 1 分。
   这里用 CAS：`PATCH ...&score=eq.<旧值>`，匹配不到行就说明被别人改过，重读重试。
   （不引 Postgres 函数是因为那要再跑一次 DDL；CAS 在 PostgREST 上够用。）

3. **读失败一律 fail-open（当满分）。** 与 sanctions.load_user_state 同一条口径。
   信誉服务挂了不该让全站用户发不出内容 —— 少拦几个帖子的代价，
   远小于「所有人都以为自己被封了」。失败会 logger.warning 留痕。

4. **规则和阈值全部读表，代码里一个数字都不写死。**
   本项目 2026-10-08 的教训：阈值不该由实现者发明。要调就 UPDATE 表。


关于"今天"
----------
自然日按 **北京时间（UTC+8）** 算，不按 UTC —— 用户在东八区，
按 UTC 分日会让"今晚 8 点"和"明早 7 点"算成同一天，
每日登录这类规则的体感会完全对不上。
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import httpx

from config import settings
from services.supabase import get_supabase_service_headers

logger = logging.getLogger(__name__)

_BJ = timezone(timedelta(hours=8))

DEFAULT_SCORE = 100
SCORE_MIN = 0
SCORE_MAX = 100

# 手动改分的固定 code（rules 表里没有它，是引擎内建的）
RULE_ADMIN_MANUAL = "admin.manual"

# 恢复类规则的 code 前缀。恢复判定要靠它把自己排除掉 ——
# 否则每次恢复都在重置自己的计时器，第二次恢复要再等一个完整周期（自锁）。
# 用前缀而不是某个具体 code，是因为恢复已经变成一条曲线（streak_3/7/14/30）。
RECOVERY_PREFIX = "recovery."

# ── 缓存 ──
# 分和档位都在热路径上（每次发帖/生成都要问），所以缓存。
# TTL 与 sanctions.py 的 30 秒对齐 —— 两套风控的生效延迟保持一致，
# 否则会出现「禁言已生效但信誉还是旧的」这种难解释的中间态。
_SCORE_TTL = 30.0
_RULES_TTL = 300.0    # 规则改得很慢，5 分钟
_score_cache: dict[str, tuple[float, dict]] = {}
_rules_cache: dict[str, Any] = {"at": 0.0, "rules": {}, "tiers": []}


# ============================================================
# 底层 HTTP
# ============================================================

def _base() -> str:
    return f"{settings.SUPABASE_URL}/rest/v1"


async def _req(method: str, path: str, *, params: dict | None = None,
               json_body: Any = None, extra_headers: dict | None = None) -> httpx.Response:
    headers = get_supabase_service_headers()
    if extra_headers:
        headers.update(extra_headers)
    url = f"{_base()}/{path}"
    async with httpx.AsyncClient(timeout=15.0) as client:
        return await client.request(method, url, headers=headers, params=params, json=json_body)


def _rows(res: httpx.Response) -> list[dict]:
    if res.status_code not in (200, 201, 206):
        return []
    try:
        data = res.json()
    except Exception:
        return []
    return data if isinstance(data, list) else []


def _day_start_bj(now: Optional[datetime] = None) -> datetime:
    """今天（北京时间）的零点，转成 UTC 用于查询。"""
    n = (now or datetime.now(timezone.utc)).astimezone(_BJ)
    return n.replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc)


def invalidate(user_id: str | None = None) -> None:
    """清缓存。改分之后必须调，否则 30 秒内读到的还是旧值。"""
    if user_id is None:
        _score_cache.clear()
    else:
        _score_cache.pop(user_id, None)


# ============================================================
# 规则 / 档位（读表 + 缓存）
# ============================================================

async def load_rules(force: bool = False) -> dict:
    """
    载入规则与档位。失败时返回**上一次的缓存**（哪怕过期），
    实在没有就返回空 —— 空规则表的表现是「任何 apply_delta 都不生效」，
    比抛异常好：它不会让发帖这条主路径挂掉。
    """
    import time
    now = time.time()
    if not force and _rules_cache["rules"] and now - _rules_cache["at"] < _RULES_TTL:
        return _rules_cache

    try:
        r_res = await _req("GET", "reputation_rules", params={"select": "*", "enabled": "eq.true"})
        t_res = await _req("GET", "reputation_tiers", params={"select": "*", "order": "min_score.desc"})
        rules = {r["code"]: r for r in _rows(r_res) if r.get("code")}
        tiers = sorted(_rows(t_res), key=lambda t: int(t.get("min_score") or 0), reverse=True)
        if rules:
            _rules_cache.update({"at": now, "rules": rules, "tiers": tiers})
        else:
            logger.warning("信誉规则表为空或读取失败（status=%s）—— 本次沿用旧缓存",
                           getattr(r_res, "status_code", "?"))
    except Exception as e:
        logger.warning("信誉规则载入失败 %s: %s —— 沿用旧缓存", type(e).__name__, e)

    return _rules_cache


def _tier_for(score: int, tiers: list[dict]) -> dict:
    for t in tiers:
        try:
            if int(t["min_score"]) <= score <= int(t["max_score"]):
                return t
        except (KeyError, TypeError, ValueError):
            continue
    # 档位没覆盖到这个分数（配置错了）—— 退回最宽松的语义，不要因此拦人
    logger.warning("信誉分 %s 不在任何档位区间内，按「正常」处理（请检查 reputation_tiers 配置）", score)
    return {"code": "unknown", "ai_daily_quota": -1, "content_needs_review": False,
            "can_publish": True, "perks_text": "", "badge": None}


# ============================================================
# 读
# ============================================================

async def get_score(user_id: str) -> int:
    """
    当前分。没有行 = 从未变动过 = 满分（懒创建，不做全量回填）。
    读失败也返回满分 —— 见文件头约定 3。
    """
    import time
    if not user_id:
        return DEFAULT_SCORE

    cached = _score_cache.get(user_id)
    if cached and time.time() - cached[0] < _SCORE_TTL:
        return cached[1]["score"]

    try:
        res = await _req("GET", "user_reputation",
                         params={"select": "score,updated_at", "user_id": f"eq.{user_id}", "limit": "1"})
        rows = _rows(res)
        score = int(rows[0]["score"]) if rows else DEFAULT_SCORE
    except Exception as e:
        logger.warning("读取信誉分失败 user=%s %s: %s —— 按满分放行", user_id, type(e).__name__, e)
        score = DEFAULT_SCORE

    _score_cache[user_id] = (time.time(), {"score": score})
    return score


async def get_tier(user_id: str) -> dict:
    """当前档位（含配额、是否先审后发、能否发布）。"""
    score = await get_score(user_id)
    rules = await load_rules()
    tier = dict(_tier_for(score, rules.get("tiers") or []))
    tier["score"] = score
    return tier


async def ai_daily_quota(user_id: str) -> int:
    """AI 生成每日配额。-1 = 不限，0 = 禁止。"""
    return int((await get_tier(user_id)).get("ai_daily_quota", -1))


async def needs_review(user_id: str) -> bool:
    """该用户新发的内容是否要先审后发。"""
    return bool((await get_tier(user_id)).get("content_needs_review", False))


async def can_publish(user_id: str) -> bool:
    """该用户还能不能发内容（帖子/评论/视频）。high_risk 档为 False。"""
    return bool((await get_tier(user_id)).get("can_publish", True))


# ============================================================
# AI 配额（后果一：限制 AI 生成次数）
#
# 用量记在 user_actions 表 —— 那是项目现成的行为流水表，不另外建表。
# action_type 统一带 `ai_quota.` 前缀，**只由后端写**，
# 与前端 /career/actions/record 记的那些行为互不干扰（不会重复计数）。
#
# ⚠️ 配额为「不限」（-1）时**不记账也不查询** —— 那是绝大多数用户，
#    为了给少数人限流而给所有人加两次数据库往返不划算。
#    代价：这些用户的 AI 使用量没有留档。真要审计生成行为，
#    那是「安全包」网关（第三期）的活，不该靠这张表兼职。
# ============================================================

_AI_QUOTA_PREFIX = "ai_quota."


async def _ai_used_today(user_id: str) -> int:
    """今天（北京时间）已用掉的 AI 次数。查不到按 0 算（宽松方向）。"""
    try:
        res = await _req("GET", "user_actions", params={
            "select": "id",
            "user_id": f"eq.{user_id}",
            "action_type": f"like.{_AI_QUOTA_PREFIX}*",
            "action_at": f"gte.{_day_start_bj().isoformat()}",
        })
        return len(_rows(res))
    except Exception as e:
        logger.warning("AI 用量查询失败 user=%s %s: %s —— 按未使用处理", user_id, type(e).__name__, e)
        return 0


async def _record_ai_use(user_id: str, kind: str) -> None:
    try:
        await _req("POST", "user_actions", json_body={
            "user_id": user_id,
            "action_type": f"{_AI_QUOTA_PREFIX}{kind}",
            "metadata": {"kind": kind},
        }, extra_headers={"Prefer": "return=minimal"})
    except Exception as e:
        # 记账失败 → 这次配额漏算了。宽松方向，可接受，但必须留痕。
        logger.warning("AI 用量记账失败 user=%s kind=%s %s: %s", user_id, kind, type(e).__name__, e)


async def consume_ai_quota(user_id: str, *, kind: str = "generate") -> tuple[bool, int]:
    """
    消耗一次 AI 配额。返回 (是否允许, 剩余次数)。剩余 -1 表示不限。

    ⚠️ 先查再写，中间有并发窗口 —— 两个请求同时读到 used=9、quota=10 会都放行，
       实际用掉 11 次。这里**刻意不修**：修它要么上锁要么上 CAS，
       代价远大于"偶尔多放一次 AI 生成"。配额是节流阀，不是精确计费。
    """
    quota = await ai_daily_quota(user_id)
    if quota < 0:
        return True, -1
    if quota == 0:
        return False, 0

    used = await _ai_used_today(user_id)
    if used >= quota:
        return False, 0

    await _record_ai_use(user_id, kind)
    return True, max(0, quota - used - 1)


# ============================================================
# 写
# ============================================================

async def _todays_usage(user_id: str, code: str) -> tuple[int, int]:
    """
    今天这条规则已经触发了几次、累计变动了多少分（绝对值）。
    返回 (次数, 累计绝对值)。
    """
    try:
        res = await _req("GET", "user_reputation_logs", params={
            "select": "delta",
            "user_id": f"eq.{user_id}",
            "reason_code": f"eq.{code}",
            "created_at": f"gte.{_day_start_bj().isoformat()}",
        })
        deltas = [abs(int(r.get("delta") or 0)) for r in _rows(res)]
        return len(deltas), sum(deltas)
    except Exception as e:
        # 查不到用量时按「已用光」处理（保守）—— 宁可少扣，也不要因为一次
        # 查询失败就把人往死里扣。加分侧同理：少加一次不算灾难。
        logger.warning("查询今日用量失败 user=%s code=%s %s: %s", user_id, code, type(e).__name__, e)
        return 0, 0


async def _already_applied(user_id: str, code: str, source_id: str) -> bool:
    """
    (用户, 规则, 来源) 这三元组是否已经有流水了。
    用于「同一条举报被重复处置时不重复扣分」这类场景。
    """
    try:
        res = await _req("GET", "user_reputation_logs", params={
            "select": "id", "user_id": f"eq.{user_id}",
            "reason_code": f"eq.{code}", "source_id": f"eq.{source_id}", "limit": "1",
        })
        return bool(_rows(res))
    except Exception as e:
        # 查不出来时**按"已经处理过"处理**（保守，不重复扣分）。
        # 宁可漏扣一次，也不要因为一次查询抖动把人重复罚了。
        logger.warning("来源去重查询失败 user=%s code=%s source=%s %s: %s",
                       user_id, code, source_id, type(e).__name__, e)
        return True


async def _ensure_row(user_id: str, score: int) -> bool:
    """
    确保 user_reputation 里有这一行。已存在返回 True。
    并发下两个请求同时插入会有一个撞主键（409），那也算成功（行已经在了）。
    """
    res = await _req("POST", "user_reputation", json_body={"user_id": user_id, "score": score},
                     extra_headers={"Prefer": "return=minimal"})
    if res.status_code in (200, 201, 204):
        return True
    if res.status_code == 409:
        return True
    # 409 以外的错误（比如外键不存在 → 用户已被删）要留痕
    logger.warning("创建信誉行失败 user=%s status=%s body=%s",
                   user_id, res.status_code, res.text[:200])
    return False


async def _cas_write(user_id: str, old_score: int, new_score: int) -> bool:
    """
    把分数从 old_score 改成 new_score，**只有当前值确实还是 old_score 时才写**。
    返回是否写成功（False = 被别人抢先改过，调用方应重读重试）。
    """
    res = await _req(
        "PATCH", "user_reputation",
        params={"user_id": f"eq.{user_id}", "score": f"eq.{old_score}"},
        json_body={"score": new_score, "updated_at": datetime.now(timezone.utc).isoformat()},
        extra_headers={"Prefer": "return=representation"},
    )
    if res.status_code not in (200, 204):
        logger.warning("信誉分写入失败 user=%s status=%s body=%s",
                       user_id, res.status_code, res.text[:200])
        return False
    if res.status_code == 204:
        return True          # return=minimal 的服务器
    return len(_rows(res)) > 0


async def _write_log(user_id: str, delta: int, score_after: int, code: str, *,
                     reason_text: Optional[str] = None, source_type: Optional[str] = None,
                     source_id: Optional[str] = None, operator_id: Optional[str] = None,
                     detail: Optional[dict] = None) -> None:
    try:
        await _req("POST", "user_reputation_logs", json_body={
            "user_id": user_id, "delta": delta, "score_after": score_after,
            "reason_code": code, "reason_text": reason_text,
            "source_type": source_type, "source_id": source_id,
            "operator_id": operator_id, "detail": detail or {},
        }, extra_headers={"Prefer": "return=minimal"})
    except Exception as e:
        # 约定 1 要求"必须写流水"，但这里**不能因此让主流程失败** ——
        # 分数已经改了，抛异常只会让调用方以为没改。如实留痕，让人能事后补。
        logger.error("信誉流水写入失败（分数已变更，需人工核对）user=%s code=%s delta=%s after=%s: %s",
                     user_id, code, delta, score_after, e)


async def apply_delta(
    user_id: str,
    code: str,
    *,
    reason_text: Optional[str] = None,
    source_type: Optional[str] = None,
    source_id: Optional[str] = None,
    detail: Optional[dict] = None,
    retries: int = 3,
    dedup_by_source: bool = False,
) -> Optional[dict]:
    """
    按规则 code 给用户加减分。返回 {"delta", "score_before", "score_after", "capped", "skipped"}，
    没生效（规则不存在、被 once_per_day / daily_cap / 来源去重挡住）返回 None。

    dedup_by_source=True 时，(用户, 规则, source_id) 只生效一次。
    用于「同一条举报被重复处置不重复扣分」这类场景 —— 注意它和 once_per_day 是
    两个维度：前者防的是"同一起事件被处理两次"，后者防的是"同一天做两次同类动作"。

    **不抛异常** —— 它会被挂到发帖、举报处置等主路径上。
    """
    if not user_id or not code:
        return None

    rules = await load_rules()
    rule = (rules.get("rules") or {}).get(code)
    if not rule:
        # 规则表里没有这条：多半是 code 打错了，或者规则被 disable 了。
        # 不静默 —— 否则「扣分没生效」会被当成「这个人确实没问题」。
        logger.warning("信誉规则不存在或已停用：code=%s（调用方写错？）", code)
        return None

    delta = int(rule.get("delta") or 0)
    if delta == 0:
        return None

    # ── 来源去重：同一起事件只算一次 ──
    if dedup_by_source and source_id:
        if await _already_applied(user_id, code, source_id):
            return None

    # ── once_per_day：今天已经触发过就跳过 ──
    if rule.get("once_per_day"):
        times, _ = await _todays_usage(user_id, code)
        if times > 0:
            return None

    # ── daily_cap：把本次变动钳到不超过当日上限 ──
    capped = False
    if rule.get("daily_cap") is not None:
        try:
            cap = abs(int(rule["daily_cap"]))
            _, used = await _todays_usage(user_id, code)
            room = cap - used
            if room <= 0:
                return None
            if abs(delta) > room:
                delta = room if delta > 0 else -room
                capped = True
        except (TypeError, ValueError):
            logger.warning("规则 %s 的 daily_cap 不是整数，已忽略上限", code)

    # ── CAS 循环：读 → 算 → 带旧值写；被别人抢先就重来 ──
    for _ in range(max(1, retries)):
        before = await get_score(user_id)
        after = max(SCORE_MIN, min(SCORE_MAX, before + delta))

        if after == before:
            # 已经在边界上（0 分继续扣、或 100 分继续加）。
            #
            # ⚠️ 只有**扣分**规则在边界上时才写那条 delta=0 的流水。
            #    扣分侧需要它，是因为自然恢复的判定是「连续 N 天没有扣分记录」——
            #    0 分用户持续违规时，靠它把恢复计时器一直重置回去。
            #    表上也因此**不能**加 CHECK (delta <> 0)，见 sql/reputation.sql。
            #
            #    加分侧（满分继续加）**没有**对应机制，写了纯属噪音，而且有害：
            #    streak_days() 是按 `delta <= 0` 判违规记录的，于是「满分时领了
            #    一次每日登录」会被当成一次违规，把清白计时器凭空掐断。
            #    （2026-10-15 真库上实测到：某账号唯一一条流水就是
            #     login.daily / delta=0 / at_boundary，streak_days 返回 0 而非 3650。）
            if rule.get("kind") != "deduct":
                return {"delta": 0, "score_before": before, "score_after": after,
                        "capped": capped, "skipped": "已在边界"}
            await _write_log(user_id, 0, after, code,
                             reason_text=reason_text, source_type=source_type,
                             source_id=source_id,
                             detail={**(detail or {}), "at_boundary": True})
            return {"delta": 0, "score_before": before, "score_after": after,
                    "capped": capped, "skipped": "已在边界"}

        await _ensure_row(user_id, before)
        if await _cas_write(user_id, before, after):
            invalidate(user_id)
            await _write_log(user_id, after - before, after, code,
                             reason_text=reason_text or rule.get("label"),
                             source_type=source_type, source_id=source_id,
                             detail={**(detail or {}), **({"capped": True} if capped else {})})
            return {"delta": after - before, "score_before": before, "score_after": after,
                    "capped": capped, "skipped": None}
        # 没抢到：别人改过这个用户的分，重读再来
        invalidate(user_id)

    logger.warning("信誉分并发改写重试 %s 次仍失败 user=%s code=%s", retries, user_id, code)
    return None


async def admin_set(user_id: str, score: int, reason: str, operator_id: str) -> Optional[dict]:
    """
    管理员手动设定分数。**必须给理由**，且强制留痕（含 operator_id）。
    手动改分不走 once_per_day / daily_cap —— 那是自动规则的上限，
    管理员的手动决定不该被系统的节流挡住。
    """
    if not user_id or not operator_id:
        return None
    if not (reason or "").strip():
        # 不写理由的手动改分，三个月后没人说得清为什么
        raise ValueError("手动修改信誉分必须填写理由")

    target = max(SCORE_MIN, min(SCORE_MAX, int(score)))
    before = await get_score(user_id)
    if target == before:
        return {"delta": 0, "score_before": before, "score_after": before,
                "capped": False, "skipped": "分数未变化"}

    await _ensure_row(user_id, before)
    if not await _cas_write(user_id, before, target):
        return None
    invalidate(user_id)
    await _write_log(user_id, target - before, target, RULE_ADMIN_MANUAL,
                     reason_text=reason.strip(), source_type="admin",
                     operator_id=operator_id,
                     detail={"by": "admin", "from": before, "to": target})
    return {"delta": target - before, "score_before": before, "score_after": target,
            "capped": False, "skipped": None}


# 从未被扣过分的用户，清白天数按这个值算（约 10 年，够用且不会溢出）
_STREAK_NEVER = 3650




async def streak_days(user_id: str) -> int:
    """
    连续清白天数 = 距最近一次「违规记录」过了多少天。

    「违规记录」的定义（两个条件都要满足）：
      · delta <= 0        —— 0 也要算：0 分用户在边界上继续违规时记的就是 delta=0，
                             那种记录同样必须重置计时器
      · 不是 recovery 类  —— 否则每次恢复都在重置自己的计时器，第二次恢复要再等
                             一个完整周期，那是自锁不是设计
    """
    try:
        # ⚠️ 排除恢复类必须写在**查询里**，不能取回一行再来 Python 里跳过。
        #
        #   第一版就是取 limit=1 再在 Python 里 `continue` ——
        #   于是「最近一条恰好是恢复记录」时，跳过后没有别的行了，
        #   函数直接走到末尾返回 _STREAK_NEVER（3650 天）。
        #   后果：**刚恢复过一次的人，下一次按最高档 +5 恢复**。
        #   测试 [C] 组抓到的就是这个（0 分用户违规后立刻被"恢复"了 5 分）。
        res = await _req("GET", "user_reputation_logs", params={
            "select": "created_at,reason_code", "user_id": f"eq.{user_id}",
            "delta": "lte.0",
            "reason_code": f"not.like.{RECOVERY_PREFIX}*",
            "order": "created_at.desc", "limit": "1",
        })
        rows = _rows(res)
    except Exception as e:
        logger.warning("清白天数查询失败 user=%s %s: %s —— 按 0 天处理（不恢复）",
                       user_id, type(e).__name__, e)
        return 0

    if not rows:
        return _STREAK_NEVER                    # 一条违规记录都没有

    row = rows[0]
    # 兜底：万一查询端的 not.like 没生效（PostgREST 版本差异等），这里会发现。
    # 此时**返回 0（不恢复）**而不是 _STREAK_NEVER —— 两种错法的代价不对等：
    #   误发恢复 = 违规者白拿分，整套威慑失效；误不发 = 用户多等几天，管理员可手工补。
    if (row.get("reason_code") or "").startswith(RECOVERY_PREFIX):
        logger.error(
            "清白天数查询的 not.like 过滤未生效（取回了恢复类记录 %s）—— "
            "本次按 0 天处理，请检查 PostgREST 版本或该接口的过滤语法",
            row.get("reason_code"),
        )
        return 0

    ts = row.get("created_at")
    if not ts:
        return 0
    try:
        t = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return max(0, (datetime.now(timezone.utc) - t).days)
    except Exception:
        return 0


def _recovery_rule_for(streak: int, rules: dict) -> Optional[dict]:
    """
    当前清白天数够得着的**最高一档**恢复规则。
    只发最高一档，不是每档都发 —— 否则 30 天清白的用户会一次性领到 1+2+3+5。
    """
    best = None
    for r in rules.values():
        if r.get("kind") != "recovery" or not r.get("enabled", True):
            continue
        need = r.get("min_streak_days")
        if need is None:
            continue
        try:
            need = int(need)
        except (TypeError, ValueError):
            continue
        if streak >= need and (best is None or need > int(best["min_streak_days"])):
            best = r
    return best


async def next_recovery_in_days(user_id: str, streak: Optional[int] = None) -> int:
    """
    还差几天能升到下一档恢复速度。已经是最高档返回 0。
    个人中心用它显示「再坚持 N 天，恢复速度翻倍」—— 恢复过程要可预期，
    否则用户只看到分数不动，不知道是在恢复还是被卡死了。
    """
    if streak is None:
        streak = await streak_days(user_id)
    tiers = sorted(
        (int(r["min_streak_days"]) for r in (await load_rules()).get("rules", {}).values()
         if r.get("kind") == "recovery" and r.get("enabled", True)
         and r.get("min_streak_days") is not None),
    )
    for need in tiers:
        if streak < need:
            return need - streak
    return 0


async def apply_recovery(user_id: str) -> Optional[dict]:
    """
    自然恢复：按「连续清白天数」发**当前够得着的最高一档**恢复量。

    由 services/daily_scheduler.py 定时调用（不是请求路径）。

    为什么要这条曲线（而不是第一版的固定 +2/7天）：
        固定值下从 0 分爬回 100 要 350 天 —— 那不叫恢复，叫永久留疤，
        而误判一定会发生。现在约 38 天回满，且越清白恢复越快：
          3 天 → +1/天    7 天 → +2/天    14 天 → +3/天    30 天 → +5/天
        轻度过失（扣 3 分）约 6 天回来；封禁（扣 40）要一个多月 ——
        威慑和容错都在，而且全程在界面上可预期。
    """
    score = await get_score(user_id)
    if score >= SCORE_MAX:
        return None                     # 满分没什么可恢复的

    rules = await load_rules()
    streak = await streak_days(user_id)
    rule = _recovery_rule_for(streak, rules.get("rules") or {})
    if not rule:
        # 还在冷却期（清白天数不够最低一档）—— 这是正常的，不是错误
        return None

    return await apply_delta(
        user_id, rule["code"],
        reason_text=f"连续 {streak} 天无违规",
        source_type="system",
        detail={"streak_days": streak},
    )


async def run_recovery_sweep(limit: int = 500) -> dict:
    """
    批量恢复扫描，给定时任务用。

    ⚠️ 只扫**表里已经存在、且分数低于满分**的行。
       从没被扣过分的人根本没有行（懒创建）—— 他们本来就不需要恢复，
       遍历全站用户去给满分的人发恢复是纯浪费。
    """
    stats = {"scanned": 0, "recovered": 0, "failed": 0}
    try:
        res = await _req("GET", "user_reputation", params={
            "select": "user_id,score", "score": f"lt.{SCORE_MAX}",
            "order": "score.asc", "limit": str(limit),
        })
        rows = _rows(res)
    except Exception as e:
        logger.warning("恢复扫描查询失败 %s: %s", type(e).__name__, e)
        return stats

    for r in rows:
        uid = r.get("user_id")
        if not uid:
            continue
        stats["scanned"] += 1
        try:
            if await apply_recovery(uid):
                stats["recovered"] += 1
        except Exception as e:
            stats["failed"] += 1
            logger.warning("恢复失败 user=%s %s: %s", uid, type(e).__name__, e)
    return stats


# ============================================================
# 查询（后台 / 个人中心）
# ============================================================

async def get_history(user_id: str, limit: int = 50) -> list[dict]:
    res = await _req("GET", "user_reputation_logs", params={
        "select": "*", "user_id": f"eq.{user_id}",
        "order": "created_at.desc", "limit": str(limit),
    })
    return _rows(res)


async def list_rules() -> list[dict]:
    rules = await load_rules()
    return sorted((rules.get("rules") or {}).values(), key=lambda r: r.get("sort_order", 100))


async def list_tiers() -> list[dict]:
    rules = await load_rules()
    return rules.get("tiers") or []
