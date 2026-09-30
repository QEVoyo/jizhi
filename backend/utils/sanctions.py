"""
处置状态（封禁 / 禁言）的查询与校验。

背景 —— 这两个概念此前形同虚设：
  · 封禁：`PUT /admin/users/{id}/status` 只写 `profiles.is_active`，
    而**全后端没有任何地方读它**（排除 admin.py 自己后，is_active 的命中只剩
    建列语句、前端显示、和 admin 列表的筛选）。所以"封禁"只是个标签 ——
    被禁的人照样登录、发帖、评论。
  · 禁言：全仓库零实现（搜 禁言|mute|silence|restrict 只命中 CSS 变量名）。

设计取舍：
  · 状态落 **profiles**（is_active / muted_until / mute_scope），不落 user_sanctions。
    因为认证中间件每次请求本来就要查一次 profiles（判管理员角色），
    放同一张表可以合并查询，不给热路径增加往返。
  · user_sanctions 只存**历史**（谁、因为什么、多久、谁操作、是否解除），
    供审计和"这个人被处置过几次"这类查询，不参与热路径。
  · 加一层 30 秒的进程内缓存：封禁不是秒级敏感的操作，
    为此让每个 API 调用多一次数据库往返不划算。（多进程部署时各进程独立，
    最坏情况是解封后 30 秒内某个进程仍拒绝 —— 可以接受。）
"""
import time
from datetime import datetime, timezone, timedelta
from typing import Optional

import httpx
from fastapi import HTTPException

from config import settings
from logging_config import logger

# user_id -> (expire_ts, state)
_CACHE: dict[str, tuple[float, dict]] = {}
_TTL = 30.0


def _parse_ts(v) -> Optional[datetime]:
    """解析 Supabase 返回的时间戳（形如 2026-09-30T12:00:00+00:00 或带微秒）"""
    if not v:
        return None
    if isinstance(v, datetime):
        return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
    try:
        s = str(v).replace("Z", "+00:00")
        d = datetime.fromisoformat(s)
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except Exception:
        return None


async def load_user_state(user_id: str, use_cache: bool = True) -> dict:
    """读用户的处置状态：{is_active, muted_until, mute_scope}

    读不到（用户不存在 / 上游故障）时返回**放行**的默认值，
    避免因为一次查询抖动把所有人挡在门外 —— 真正的封禁判定不差这一次。
    """
    now = time.time()
    if use_cache:
        hit = _CACHE.get(user_id)
        if hit and hit[0] > now:
            return hit[1]

    state = {"is_active": True, "muted_until": None, "mute_scope": None}
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            res = await client.get(
                f"{settings.SUPABASE_URL}/rest/v1/profiles",
                params={"id": f"eq.{user_id}",
                        "select": "is_active,muted_until,mute_scope"},
                headers={
                    "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
                    "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
                },
            )
        if res.status_code == 200 and res.json():
            row = res.json()[0]
            state = {
                # 注意：只有**显式 False** 才算封禁。
                # is_active 为 NULL（历史脏数据）不应当把人锁在门外。
                "is_active": row.get("is_active") is not False,
                "muted_until": row.get("muted_until"),
                "mute_scope": row.get("mute_scope"),
            }
        elif res.status_code == 200:
            pass                      # 查不到这个 id：不拦
        else:
            logger.warning(f"[sanctions] 读处置状态失败 status={res.status_code} body={res.text[:200]}")
    except Exception as e:
        logger.warning(f"[sanctions] 读处置状态异常: {e}")

    _CACHE[user_id] = (now + _TTL, state)
    return state


def invalidate(user_id: str) -> None:
    """处置变更后立刻失效缓存，免得管理员点了封禁、对方还能再蹦 30 秒。"""
    _CACHE.pop(user_id, None)


async def assert_not_banned(user_id: str) -> None:
    """封禁校验 —— 在认证环节调用，封禁用户连登录态都过不去。"""
    st = await load_user_state(user_id)
    if not st["is_active"]:
        raise HTTPException(status_code=403, detail="账号已被封禁，如有疑问请联系管理员")


# 动作 → 需要检查的禁言范围
#   scope='all' 命中一切；'post' 只挡发帖；'comment' 只挡评论
def _scope_hits(scope: Optional[str], action: str) -> bool:
    if not scope:
        return False
    if scope == "all":
        return True
    return scope == action


async def assert_can_act(user_id: str, action: str) -> None:
    """禁言校验 —— 在具体动作入口调用（发帖 / 评论）。

    action ∈ {'post', 'comment'}
    """
    st = await load_user_state(user_id)
    if not st["is_active"]:
        raise HTTPException(status_code=403, detail="账号已被封禁，如有疑问请联系管理员")

    until = _parse_ts(st["muted_until"])
    if until and until > datetime.now(timezone.utc) and _scope_hits(st["mute_scope"], action):
        # 解禁时间按北京时间展示，用户才看得懂
        pretty = until.astimezone(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M")
        what = {"post": "发帖", "comment": "评论"}.get(action, "该操作")
        raise HTTPException(status_code=403, detail=f"你已被禁言，暂时无法{what}（解禁时间 {pretty}）")
