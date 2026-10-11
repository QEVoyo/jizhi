# -*- coding: utf-8 -*-
"""消息写入的唯一入口（2026-10-07 重写）

改造前的三个病，这个文件就是来治它们的：

  1. **静默失败**：`_upsert_notification()` 的 PATCH 写 `updated_at`，而 notifications
     表根本没有这一列 → 每次 400，返回 False，而调用方（messages.py:180）不检查返回值。
     实测后果：接收者的私信通知冻结在 2026-08-24、msg_count 永远是 1，
     而同一发送者后来还发过 3 条 —— 两个月没人发现。
     → 现在：**失败必须抛 NotifyError**，不许吞。

  2. **类型没人管**：线上出现过 `task_done` / `task_failed` 这种「后端在写、前端没定义」
     的类型，在列表里显示成英文原文。
     → 现在：**未注册的类型直接 KeyError**，先在 notification_registry 注册再发。

  3. **谁都能绕过**：capsule（tools.py）和每日推荐（daily_generator.py）自己拼 dict 插表。
     → 现在：**全部收编到这里**，聚合/去重/开关/时间戳只有一套实现。

⚠️ 唯一的例外是 `notify_broadcast()`（2026-10-08 加）：给全体用户发同一条消息
   （目前只有公告）。逐人走 `notify()` 是 2N 次往返，会把管理员的发布按钮卡死；
   它改用数组插入，代价是**开关要自己判**（改成查退订名单）。见该函数的说明。
   **除它之外，任何写入都必须走 `notify()`。**

写入用 service_role：这张表的数据是私信正文与处置记录，
而 anon key 打包在前端产物里（谁都能扒）。
⚠️ 依赖 `sql/message_center_rework.sql` 第 6 步的 GRANT —— **先跑 SQL，再部署后端**。
"""
import httpx
from datetime import datetime, timezone

from config import settings
from logging_config import logger
from notification_registry import spec, resolve_link, switch_of
from services.supabase import get_supabase_service_headers


class NotifyError(RuntimeError):
    """消息写入失败。调用方要么拦下请求，要么记 ERROR —— 但不许静默吞掉。"""


# 设置表读不到时的默认值：宁可多发（用户能关），不可因为读不到就静默不发。
#
# ⚠️ 两个时间键（2026-10-08 补）此前**只存在于设置页的返回里**（`message_center.py`
#    硬编码了一份），没有进这里。后果是**设置页显示 08:00、而调度器读到 None** ——
#    同一个默认值两份实现，UI 和真实行为对不上。现在只有这一份，
#    设置页也从这里取（那里不再硬编码）。
#
#    默认值对齐建列语句（`sql/fix_settings_tables.sql`：08:00 / 07:00）。
DEFAULT_SETTINGS = {
    "chat_enabled": True, "social_enabled": True, "learning_enabled": True,
    "plan_reminder_enabled": True, "evaluation_enabled": True, "career_enabled": True,
    "todo_enabled": True, "system_enabled": True, "admin_enabled": True,
    "daily_rec_enabled": True, "daily_summary_enabled": True,
    "daily_rec_time": "08:00",          # 用户没设过 → 早上 8 点推推荐
    "daily_summary_time": "07:00",      # 总结在推荐之前（总结说的是昨天）
    "daily_rec_source": "mix",          # 推荐依据：结合 / 按资料 / 按记录，见 §六
}


def _now() -> str:
    """UTC 带时区。

    ⚠️ 不要用 `datetime.now().isoformat()` —— 那是本地时间（东八区）却不带时区，
    PostgREST 会按 UTC 存进 timestamptz，**整整差 8 小时**。改造前的代码就是这么写的。
    """
    return datetime.now(timezone.utc).isoformat()


async def get_settings(user_id: str) -> dict:
    """读用户的消息设置（开关 + 免打扰）。读不到返回默认值，不抛。"""
    url = f"{settings.SUPABASE_URL}/rest/v1/notification_settings?user_id=eq.{user_id}&limit=1"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.get(url, headers=get_supabase_service_headers())
        if res.status_code == 200 and res.json():
            merged = dict(DEFAULT_SETTINGS)
            merged.update({k: v for k, v in res.json()[0].items() if v is not None})
            return merged
    except Exception as e:                                    # noqa: BLE001
        logger.warning(f"[notify] 读设置失败，按默认值处理 user={user_id}: {e}")
    return dict(DEFAULT_SETTINGS)


async def notify(
    to_user: str,
    notif_type: str,
    *,
    actor_id: str = None,
    actor_name: str = None,
    source_id: str = None,
    title: str = None,
    content: str = "",
    link: str = None,
    image_url: str = "",
    payload: dict = None,
) -> str | None:
    """发一条消息。返回行 id；被开关挡下返回 None；失败抛 NotifyError。

    Args:
        notif_type: 必须是 notification_registry.TYPES 里注册过的键。
        actor_name: 触发者昵称。聚合型会累积进 payload.actors（最多 5 个）——
                    「3 人赞了你的帖子」点开详情要能看见是谁。
        source_id:  聚合键。同一 (user, type, source_id) 的未读消息会并成一行。
        payload:    结构化内容（每日学习推荐的三合一、聚合的 actors）。
    """
    s = spec(notif_type)                       # 未注册 → KeyError，就是要炸
    if not title:
        title = s["label"]

    # ---- 开关：这是「设置」真正生效的地方（改造前没有任何代码读这些开关）----
    cfg = await get_settings(to_user)
    if not cfg.get(switch_of(notif_type), True):
        return None

    headers = {**get_supabase_service_headers(), "Content-Type": "application/json"}
    base = f"{settings.SUPABASE_URL}/rest/v1/notifications"
    row = {
        "user_id": to_user, "type": notif_type, "group_key": s["group"],
        "actor_id": actor_id, "source_id": source_id,
        "title": title, "content": content or "",
        "link": link or resolve_link(notif_type, source_id, actor_id),
        "image_url": image_url or "",
        "is_read": False, "is_todo": bool(s.get("todo")), "msg_count": 1,
        "created_at": _now(), "last_at": _now(),
    }
    # 聚合型：把触发者昵称攒进 payload —— 详情页要显示「谁赞的」
    if s["aggregate"] and actor_name:
        row["payload"] = {**(payload or {}), "actors": [actor_name]}
    elif payload:
        row["payload"] = payload
    row = {k: v for k, v in row.items() if v is not None}

    async with httpx.AsyncClient(timeout=20.0) as client:
        # ---- 只发一次的类型：曾经发过就不再发（成就、段位、胶囊到期…）----
        if s.get("once") and source_id:
            q = f"{base}?user_id=eq.{to_user}&type=eq.{notif_type}&source_id=eq.{source_id}&select=id&limit=1"
            try:
                if (await client.get(q, headers=headers)).json():
                    return None
            except Exception:                                  # noqa: BLE001
                pass   # 查不到就当没发过 —— 宁可重复提醒，不可因为查询失败而漏发

        res = await client.post(f"{base}?select=id", headers=headers, json=row)

        # ---- 聚合：撞上部分唯一索引（409）说明已有未读行 → 改走更新 ----
        if res.status_code == 409 and s["aggregate"] and source_id:
            return await _bump(client, base, headers, to_user, notif_type, source_id,
                               title, content, payload, actor_name)

        if res.status_code not in (200, 201):
            raise NotifyError(
                f"写入通知失败 [{res.status_code}] type={notif_type} "
                f"to={to_user}: {res.text[:300]}"
            )
        body = res.json()
        return body[0]["id"] if isinstance(body, list) and body else None


async def _bump(client, base, headers, to_user, notif_type, source_id,
                title, content, payload, actor_name=None) -> str | None:
    """聚合更新：msg_count+1、内容换成最新一条、刷新 last_at、累积触发者。

    ⚠️ 只写真实存在的列。改造前这里多写了一个 `updated_at`（表里没这列），
    导致每一次聚合更新都 400 —— 而返回值没人看，于是静默了两个月。
    """
    q = (f"{base}?user_id=eq.{to_user}&type=eq.{notif_type}&source_id=eq.{source_id}"
         f"&is_read=eq.false&select=id,msg_count,payload&limit=1")
    got = await client.get(q, headers=headers)
    if got.status_code != 200 or not got.json():
        # 极端情况：唯一索引撞了但按「未读」查不到（并发已读）→ 重发一条新的
        raise NotifyError(f"聚合更新找不到目标行 type={notif_type} source={source_id}")

    row = got.json()[0]
    patch = {
        "msg_count": (row.get("msg_count") or 0) + 1,
        "title": title, "content": content or "", "last_at": _now(),
    }
    # 触发者名单：详情要显示「谁赞的」。只留最近 5 个，去重保序。
    old = (row.get("payload") or {}) if isinstance(row.get("payload"), dict) else {}
    actors = list(old.get("actors") or [])
    if actor_name and actor_name not in actors:
        actors.append(actor_name)
    merged = {**old, **(payload or {})}
    if actors:
        merged["actors"] = actors[-5:]
    if merged:
        patch["payload"] = merged
    pr = await client.patch(f"{base}?id=eq.{row['id']}", headers=headers, json=patch)
    if pr.status_code not in (200, 204):
        raise NotifyError(
            f"聚合更新失败 [{pr.status_code}] id={row['id']}: {pr.text[:300]}"
        )
    return row["id"]


async def notify_admins(notif_type: str, **kw) -> int:
    """发给全部管理员（admin 组的消息点用）。

    返回成功条数。单个管理员写入失败不影响其它人 ——
    但会记 ERROR（不静默），并且整批失败会抛 NotifyError。
    """
    url = (f"{settings.SUPABASE_URL}/rest/v1/profiles"
           f"?role=eq.admin&select=id&limit=100")
    async with httpx.AsyncClient(timeout=20.0) as client:
        res = await client.get(url, headers=get_supabase_service_headers())
    if res.status_code != 200:
        raise NotifyError(f"取管理员列表失败 [{res.status_code}]: {res.text[:200]}")

    admins = [r["id"] for r in (res.json() or [])]
    ok, errs = 0, []
    for uid in admins:
        try:
            if await notify(uid, notif_type, **kw):
                ok += 1
        except NotifyError as e:
            errs.append(f"{uid}: {e}")
            logger.error(f"[notify] 发给管理员失败 {uid}: {e}")
    if admins and not ok and errs:
        raise NotifyError(f"管理员通知全部失败（{len(admins)} 人）：{errs[0]}")
    return ok


# ============================================================================
# 广播 —— 本文件第二个（也是最后一个）写入口
# ============================================================================

async def _all_user_ids(client, headers: dict, page: int = 1000) -> list:
    """分页取全部用户 id。

    PostgREST 单次默认只回一页，**不能只发一个不带 Range 的请求就当成全量** ——
    那会把「广播给了前 1000 人」伪装成「广播成功」。
    """
    ids, offset = [], 0
    while True:
        res = await client.get(
            f"{settings.SUPABASE_URL}/rest/v1/profiles?select=id&order=id",
            headers={**headers, "Range-Unit": "items",
                     "Range": f"{offset}-{offset + page - 1}"})
        # 206 = 还有下一页；200 = 到底了
        if res.status_code not in (200, 206):
            raise NotifyError(
                f"取用户列表失败 [{res.status_code}]: {res.text[:200]}")
        chunk = [r["id"] for r in (res.json() or []) if r.get("id")]
        ids.extend(chunk)
        if len(chunk) < page:
            return ids
        offset += page


async def notify_broadcast(
    notif_type: str,
    *,
    title: str = None,
    content: str = "",
    link: str = None,
    image_url: str = "",
    payload: dict = None,
    batch_size: int = 200,
) -> int:
    """给**全体用户**发同一条消息，返回写入行数。

    ⚠️ 这是 `notify()` 之外**唯一**的写入口，所以 `notify()` 替调用方做的那几件事
    得由它自己承担：
      · 类型必须注册（`spec()` 照抛 KeyError）
      · 用户级开关 —— `notify()` 是「一人一查设置」，那是 N 次往返；
        这里反过来查**「显式关掉了这条的人」**，一次请求拿到黑名单再排除。
        没建过设置行的用户取默认值（`DEFAULT_SETTINGS`），所以不算黑名单。

    为什么值得开这个口子：发布公告是管理员点一下的**同步请求**，
    逐个用户走 `notify()` 是 2N 次 HTTP 往返（每人还要查一次设置），
    几百人就能把「发布」按钮卡到超时。PostgREST 支持数组插入，一次写一批。

    ⚠️ **刻意不收 `source_id`。** 未读聚合的部分唯一索引建在
    (user_id, type, source_id) 上，而数组插入撞上唯一索引会**整批 409 失败**；
    部分索引的谓词又没法用 ON CONFLICT 表达（见 message_center_rework.sql 第 3 节），
    没有干净的兜底。广播型消息点本来就该「每次广播都是一条新消息」，
    所以这里把 source_id 留空（NULL 不参与那个索引）。
    将来真有广播点需要它，先想清楚「重复广播怎么办」再加。
    """
    s = spec(notif_type)                       # 未注册 → KeyError，就是要炸
    if not title:
        title = s["label"]
    if s["aggregate"]:
        # 聚合是「同一个人收到多条并成一行」，广播给每人只写一行，聚合无从谈起。
        raise ValueError(f"广播型消息点不能是 aggregate：{notif_type}")

    hdrs = {**get_supabase_service_headers(), "Content-Type": "application/json"}
    base = f"{settings.SUPABASE_URL}/rest/v1/notifications"
    switch = switch_of(notif_type)

    async with httpx.AsyncClient(timeout=60.0) as client:
        user_ids = await _all_user_ids(client, get_supabase_service_headers())
        off_res = await client.get(
            f"{settings.SUPABASE_URL}/rest/v1/notification_settings"
            f"?{switch}=eq.false&select=user_id",
            headers=get_supabase_service_headers())
        # 查黑名单失败就**当成没人退订**：宁可多发（用户能关），不可静默漏发
        muted = ({r["user_id"] for r in (off_res.json() or [])}
                 if off_res.status_code == 200 else set())
        targets = [u for u in user_ids if u not in muted]
        if not targets:
            logger.warning(f"[notify] 广播 {notif_type} 没有收件人（共 {len(user_ids)} 用户）")
            return 0

        now = _now()
        fixed = {"type": notif_type, "group_key": s["group"],
                 "title": title, "content": content or "",
                 "link": link or resolve_link(notif_type),
                 "image_url": image_url or "",
                 "is_read": False, "is_todo": bool(s.get("todo")),
                 "msg_count": 1, "created_at": now, "last_at": now}
        if payload:
            fixed["payload"] = payload

        written, errs = 0, []
        for i in range(0, len(targets), batch_size):
            chunk = targets[i:i + batch_size]
            body = [{**fixed, "user_id": u} for u in chunk]
            res = await client.post(base, headers=hdrs, json=body)
            if res.status_code in (200, 201):
                written += len(chunk)
            else:
                errs.append(f"[{res.status_code}] {res.text[:200]}")
                logger.error(f"[notify] 广播 {notif_type} 第 {i // batch_size + 1} 批失败: "
                             f"[{res.status_code}] {res.text[:200]}")

        logger.info(f"[notify] 广播 {notif_type}：{written}/{len(targets)} 人"
                    f"（全体 {len(user_ids)}，退订 {len(muted)}）")
        if errs and not written:
            raise NotifyError(f"广播 {notif_type} 全部失败：{errs[0]}")
        return written
