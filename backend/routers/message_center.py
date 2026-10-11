# -*- coding: utf-8 -*-
"""消息中心 · 读接口（2026-10-07 新写）

替代改造前那四套互相打架的读法：
    /community/messages/unread/summary   —— 只查未读，点一下就消失
    /community/messages/unread/count     —— 另一套计数
    /community/sidebar-badges            —— 第三套计数（chat 按 sender 去重）
    /admin/announcements/active          —— 公告走另一张表、前端直接 fetch

现在只有一套：
    GET /messages            列表（分页 + 筛选 + 已读未读都在）
    GET /messages/badges     唯一角标来源
    GET /messages/registry   消息点注册表（前端 Tab/图标/配色/跳转全靠它）

三条变成已读的路径（见 message_center_design.md §五）：
    A. 点消息 → 跳转 → PUT /messages/{id}/read
    B. 走到目标页 → PUT /messages/read-by-route   ⚠️ system / todo 两组不参与
    C. 直接标记   → PUT /messages/read

⚠️ 所有查询走 service_role：这张表存私信正文与处置记录，
   而 anon key 打包在前端产物里。依赖 message_center_rework.sql 第 6 步的 GRANT。
"""
from datetime import datetime, timezone, timedelta
from typing import Optional

import httpx
from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel

from config import settings
from logging_config import logger
from notification_registry import GROUPS, public_registry, spec, TYPES
from services.supabase import get_supabase_service_headers
from utils.auth_middleware import get_current_user, verify_user_match

router = APIRouter(prefix="/messages", tags=["消息中心"])

# 不参与「走到页面即已读」的两个组 —— 理由见设计文档 §5.2
NO_ROUTE_READ = ("system", "todo")

# 不可删除的组：处置与安全通知要留底
NO_DELETE = ("system",)

MAX_PAGE_SIZE = 50


def _h() -> dict:
    return {**get_supabase_service_headers(), "Content-Type": "application/json"}


def _base() -> str:
    return f"{settings.SUPABASE_URL}/rest/v1/notifications"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ok(status: int) -> bool:
    """⚠️ PostgREST 在超过一页（带 count=exact）时返回的是 **206**，不是 200。

    09-30 记过一次：把 7 处「非 200 降级成空」改成抛 502 时漏了 206，
    结果 /admin/users 和整个仪表盘挂掉。这里从一开始就认 206。
    """
    return status in (200, 204, 206)


def _rows(res: httpx.Response) -> list:
    try:
        data = res.json()
    except Exception:                                          # noqa: BLE001
        return []
    return data if isinstance(data, list) else []


# ============================================================
# 列表
# ============================================================
@router.get("")
async def list_messages(
    user_id: str = Query(...),
    group: Optional[str] = Query(None, description="大类：chat/social/learning/…"),
    type: Optional[str] = Query(None, description="具体消息点，如 learning.video_ready"),
    unread_only: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=MAX_PAGE_SIZE),
    current_user: str = Depends(get_current_user),
):
    """消息列表。**已读的也在里面** —— 这是与改造前最大的区别。

    排序：未读在前，同组内按 last_at 倒序。
    """
    verify_user_match(user_id, current_user)

    q = (f"{_base()}?user_id=eq.{user_id}&deleted_at=is.null"
         f"&select=id,type,group_key,actor_id,source_id,title,content,link,image_url,"
         f"is_read,is_todo,msg_count,created_at,last_at,payload"
         f"&order=is_read.asc,last_at.desc"
         f"&limit={page_size}&offset={(page - 1) * page_size}")
    if group:
        q += f"&group_key=eq.{group}"
    if type:
        q += f"&type=eq.{type}"
    if unread_only:
        q += "&is_read=eq.false"

    headers = {**_h(), "Prefer": "count=exact", "Range-Unit": "items"}
    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.get(q, headers=headers)
    if not _ok(res.status_code):
        # 不降级成空列表 —— 那正是「静默失败」的老配方
        raise HTTPException(status_code=502, detail=f"读取消息失败：{res.text[:200]}")

    total = None
    cr = res.headers.get("content-range") or ""      # 形如 "0-19/57"
    if "/" in cr:
        try:
            total = int(cr.split("/")[-1])
        except ValueError:
            total = None

    return {"items": _rows(res), "page": page, "page_size": page_size, "total": total}


# ============================================================
# 角标 —— 全站唯一来源
# ============================================================
@router.get("/badges")
async def get_badges(user_id: str = Query(...),
                     current_user: str = Depends(get_current_user)):
    """未读角标。侧边栏、消息中心 Tab、桌宠、浏览器标题**全部**用这一个。

    返回：
        total          总未读（按行计，聚合行算 1 —— 与用户看到的条数一致）
        groups         按大类
        types          按具体消息点
        todos          待办数（待办型角标单独显示，不用未读数）
        latest         **最新一条未读**的摘要（2026-10-08 加，桌面通知用）

    ⚠️ `latest` 是给「桌面通知弹窗」用的：前端 30 秒轮询这个接口，
    比对 `latest.id` 有没有变就知道**有没有新消息**，不必再开一个接口、
    也不必每轮都拉整个列表（那是全行查询，比这个大得多）。
    `id` 变了才去拉一次列表，拿具体是哪几条。
    """
    verify_user_match(user_id, current_user)

    # 排序只为挑出最新的那条；后面的计数与顺序无关。
    # 聚合行的时间看 `last_at`（被 bump 过），非聚合看 `created_at` —— 取两者较晚的。
    q = (f"{_base()}?user_id=eq.{user_id}&is_read=eq.false&deleted_at=is.null"
         f"&select=id,type,group_key,is_todo,title,content,link,created_at,last_at"
         f"&order=last_at.desc.nullslast,created_at.desc")
    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.get(q, headers=_h())
    if not _ok(res.status_code):
        raise HTTPException(status_code=502, detail=f"读取角标失败：{res.text[:200]}")

    rows = _rows(res)
    groups: dict = {g: 0 for g in GROUPS}
    types: dict = {}
    todos = 0
    for r in rows:
        g = r.get("group_key") or "system"
        groups[g] = groups.get(g, 0) + 1
        types[r["type"]] = types.get(r["type"], 0) + 1
        if r.get("is_todo"):
            todos += 1

    latest = None
    if rows:
        top = rows[0]
        latest = {
            "id": top.get("id"),
            "type": top.get("type"),
            "group_key": top.get("group_key") or "system",
            "title": top.get("title") or "",
            "content": top.get("content") or "",
            "link": top.get("link") or "",
            "is_todo": bool(top.get("is_todo")),
            "at": top.get("last_at") or top.get("created_at"),
        }

    return {"total": len(rows), "groups": groups, "types": types,
            "todos": todos, "latest": latest}


# ============================================================
# 注册表（前端拿它生成 Tab / 图标 / 配色 / 跳转）
# ============================================================
@router.get("/registry")
async def get_registry():
    """消息点注册表。不需要登录（里面没有用户数据）—— 前端启动时拿一次即可。"""
    return public_registry()


# ============================================================
# 已读：三种路径
# ============================================================
class ReadBody(BaseModel):
    ids: Optional[list[str]] = None
    group: Optional[str] = None
    type: Optional[str] = None
    all: bool = False


@router.put("/{message_id}/read")
async def read_one(message_id: str,
                   user_id: str = Query(...),
                   current_user: str = Depends(get_current_user)):
    """路径 A：点了这一条。"""
    verify_user_match(user_id, current_user)
    return await _mark_read(f"{_base()}?id=eq.{message_id}&user_id=eq.{user_id}")


@router.put("/read")
async def read_many(body: ReadBody = Body(...),
                    user_id: str = Query(...),
                    current_user: str = Depends(get_current_user)):
    """路径 C：在消息中心里直接标记（单条 / 某类 / 全部）。"""
    verify_user_match(user_id, current_user)
    if not (body.ids or body.group or body.type or body.all):
        raise HTTPException(status_code=400, detail="要标记哪些？给 ids / group / type / all 之一")

    q = f"{_base()}?user_id=eq.{user_id}&is_read=eq.false&deleted_at=is.null"
    if body.ids:
        q += "&id=in.(" + ",".join(body.ids) + ")"
    if body.group:
        q += f"&group_key=eq.{body.group}"
    if body.type:
        q += f"&type=eq.{body.type}"
    return await _mark_read(q)


class RouteBody(BaseModel):
    url: str


@router.put("/read-by-route")
async def read_by_route(body: RouteBody = Body(...),
                        user_id: str = Query(...),
                        current_user: str = Depends(get_current_user)):
    """路径 B：用户自己走到了目标页面 → 指向该页的未读自动已读。

    ⚠️ system / todo 两组不参与：
      · system —— 去 /settings 改个主题不该把「你被禁言了」顺手清掉
      • todo   —— 待办必须由处理动作驱动，看见不算
    """
    verify_user_match(user_id, current_user)

    q = (f"{_base()}?user_id=eq.{user_id}&is_read=eq.false&deleted_at=is.null"
         f"&group_key=not.in.({','.join(NO_ROUTE_READ)})"
         f"&select=id,link&limit=200")
    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.get(q, headers=_h())
    if not _ok(res.status_code):
        raise HTTPException(status_code=502, detail=f"读取待匹配消息失败：{res.text[:200]}")

    hit = [r["id"] for r in _rows(res) if _route_matches(r.get("link") or "", body.url)]
    if not hit:
        return {"marked": 0}
    out = await _mark_read(f"{_base()}?user_id=eq.{user_id}&id=in.({','.join(hit)})")
    return {"marked": out.get("updated", 0)}


def _route_matches(link: str, url: str) -> bool:
    """消息的落点与当前地址是不是同一个页面。

    规则（设计文档 §5.2）：
      · 路径**逐段相等**才命中 —— 进 /career 不会清掉 /career/achievements 的消息，
        必须真的走到那一页
      · link 带 query 时（如 /community?post=abc），query 也要被当前 url 覆盖
    """
    def split(s: str):
        s = (s or "").split("#")[0]
        if "?" in s:
            p, qs = s.split("?", 1)
            return p.rstrip("/") or "/", dict(
                kv.split("=", 1) for kv in qs.split("&") if "=" in kv)
        return s.rstrip("/") or "/", {}

    lp, lq = split(link)
    up, uq = split(url)
    if lp != up:
        return False
    return all(uq.get(k) == v for k, v in lq.items())


async def _mark_read(url: str) -> dict:
    headers = {**_h(), "Prefer": "return=representation"}
    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.patch(url, headers=headers,
                                 json={"is_read": True, "read_at": _now()})
    if not _ok(res.status_code):
        raise HTTPException(status_code=502, detail=f"标记已读失败：{res.text[:200]}")
    # ⚠️ PATCH 对「匹配 0 行」也返回 204（09-30 踩过），所以回读一次拿真实条数
    return {"updated": len(_rows(res)), "success": True}


# ============================================================
# 待办：处理动作驱动已读
# ============================================================
@router.put("/{message_id}/handled")
async def mark_handled(message_id: str,
                       user_id: str = Query(...),
                       current_user: str = Depends(get_current_user)):
    """待办型专用：处理完了（接受/拒绝/回复）→ 才算已读。

    改造前没有这个区分，用户点开看一眼角标就没了、事还在。
    """
    verify_user_match(user_id, current_user)
    headers = {**_h(), "Prefer": "return=representation"}
    q = (f"{_base()}?id=eq.{message_id}&user_id=eq.{user_id}"
         f"&is_read=eq.false")
    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.patch(q, headers=headers,
                                 json={"is_read": True, "read_at": _now(),
                                       "handled_at": _now()})
    if not _ok(res.status_code):
        raise HTTPException(status_code=502, detail=f"标记待办失败：{res.text[:200]}")
    rows = _rows(res)
    if not rows:
        raise HTTPException(status_code=404, detail="消息不存在或已处理")
    return {"success": True, "id": rows[0]["id"]}


# ============================================================
# 删除（软删）
# ============================================================
@router.delete("/{message_id}")
async def delete_one(message_id: str,
                     user_id: str = Query(...),
                     current_user: str = Depends(get_current_user)):
    verify_user_match(user_id, current_user)
    headers = {**_h(), "Prefer": "return=representation"}
    q = f"{_base()}?id=eq.{message_id}&user_id=eq.{user_id}&deleted_at=is.null"
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 先看这条属于哪个组 —— system 组只能已读、不能删（要留底）
        chk = await client.get(
            f"{_base()}?id=eq.{message_id}&user_id=eq.{user_id}&select=group_key&limit=1",
            headers=_h())
        rows = _rows(chk)
        if not rows:
            raise HTTPException(status_code=404, detail="消息不存在")
        if rows[0].get("group_key") in NO_DELETE:
            raise HTTPException(
                status_code=400,
                detail="系统与安全类通知不可删除（需留底），可以标记为已读")
        res = await client.patch(q, headers=headers,
                                 json={"deleted_at": _now(), "is_read": True,
                                       "read_at": _now()})
    if not _ok(res.status_code):
        raise HTTPException(status_code=502, detail=f"删除失败：{res.text[:200]}")
    return {"success": True}


@router.delete("")
async def clear_messages(user_id: str = Query(...),
                         group: Optional[str] = Query(None),
                         type: Optional[str] = Query(None),
                         current_user: str = Depends(get_current_user)):
    """清空（软删）。system 组永远保留 —— 处置与安全记录要留底。"""
    verify_user_match(user_id, current_user)
    if not (group or type):
        raise HTTPException(status_code=400, detail="要清空哪一类？给 group 或 type")

    q = (f"{_base()}?user_id=eq.{user_id}&deleted_at=is.null"
         f"&group_key=not.in.({','.join(NO_DELETE)})")
    if group:
        q += f"&group_key=eq.{group}"
    if type:
        q += f"&type=eq.{type}"

    headers = _h()
    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.patch(q, headers=headers,
                                 json={"deleted_at": _now(), "is_read": True,
                                       "read_at": _now()})
    if not _ok(res.status_code):
        raise HTTPException(status_code=502, detail=f"清空失败：{res.text[:200]}")
    return {"success": True}


# ============================================================
# 设置（唯一入口在设置页，消息中心不再自带一份）
# ============================================================
class SettingsBody(BaseModel):
    chat_enabled: Optional[bool] = None
    social_enabled: Optional[bool] = None
    learning_enabled: Optional[bool] = None
    plan_reminder_enabled: Optional[bool] = None
    evaluation_enabled: Optional[bool] = None
    career_enabled: Optional[bool] = None
    todo_enabled: Optional[bool] = None
    system_enabled: Optional[bool] = None
    admin_enabled: Optional[bool] = None
    daily_rec_enabled: Optional[bool] = None
    daily_summary_enabled: Optional[bool] = None
    daily_rec_time: Optional[str] = None
    daily_summary_time: Optional[str] = None
    # 每日推荐的依据：profile（按个人信息）/ history（按做题记录）/ mix（结合，默认）
    daily_rec_source: Optional[str] = None
    dnd_start: Optional[str] = None
    dnd_end: Optional[str] = None
    retention_days: Optional[int] = None


@router.get("/settings")
async def get_settings(user_id: str = Query(...),
                       current_user: str = Depends(get_current_user)):
    verify_user_match(user_id, current_user)
    from utils.notification import DEFAULT_SETTINGS
    url = f"{settings.SUPABASE_URL}/rest/v1/notification_settings?user_id=eq.{user_id}&limit=1"
    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.get(url, headers=_h())
    if not _ok(res.status_code):
        raise HTTPException(status_code=502, detail=f"读取设置失败：{res.text[:200]}")
    rows = _rows(res)
    out = dict(DEFAULT_SETTINGS)
    # ⚠️ 时间与推荐依据的默认值**已经收进 DEFAULT_SETTINGS**（2026-10-08）——
    #    这里不再重复一份。以前这里硬编码，而调度器读的 DEFAULT_SETTINGS 里没有，
    #    于是「设置页显示 08:00、后台按随时发」两边对不上。
    out.update({"dnd_start": "", "dnd_end": "", "retention_days": 30,
                "user_id": user_id})
    if rows:
        out.update({k: v for k, v in rows[0].items() if v is not None})
    return out


@router.put("/settings")
async def update_settings(body: SettingsBody = Body(...),
                          user_id: str = Query(...),
                          current_user: str = Depends(get_current_user)):
    """保存设置。

    ⚠️ 改造前这里前后端都是 `catch {}` —— 保存失败用户以为存上了。
    现在写失败直接抛，并且**写后回读校验**（PATCH 匹配 0 行也返回 204）。
    """
    verify_user_match(user_id, current_user)
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    if not data:
        raise HTTPException(status_code=400, detail="没有要更新的字段")

    base = f"{settings.SUPABASE_URL}/rest/v1/notification_settings"
    headers = {**_h(), "Prefer": "return=representation"}
    async with httpx.AsyncClient(timeout=30.0) as client:
        chk = await client.get(f"{base}?user_id=eq.{user_id}&select=user_id&limit=1",
                               headers=_h())
        exists = bool(_rows(chk))
        if exists:
            res = await client.patch(f"{base}?user_id=eq.{user_id}", headers=headers,
                                     json=data)
        else:
            res = await client.post(f"{base}?select=user_id", headers=headers,
                                    json={"user_id": user_id, **data})
        if not _ok(res.status_code):
            raise HTTPException(status_code=502, detail=f"保存设置失败：{res.text[:200]}")
        got = _rows(res)
        if not got:
            raise HTTPException(status_code=502, detail="设置未生效（上游返回空）")
    return {"success": True, "settings": got[0]}


# ============================================================
# 详情 ⚠️ 必须放在 /badges /registry /settings **之后** ——
#    FastAPI 按声明顺序匹配，否则 "/badges" 会被 "/{message_id}" 吃掉。
# ============================================================
@router.get("/{message_id}")
async def get_message(message_id: str,
                      user_id: str = Query(...),
                      current_user: str = Depends(get_current_user)):
    """单条消息详情。

    列表里的聚合行只有一句「3 人赞了你的帖子」，**详情才是能看到全部内容的地方**：
    完整正文、聚合明细（payload.actors，最多留最近 5 个）、图片、跳转目标。
    """
    verify_user_match(user_id, current_user)
    q = (f"{_base()}?id=eq.{message_id}&user_id=eq.{user_id}"
         f"&select=id,type,group_key,actor_id,source_id,title,content,link,image_url,"
         f"is_read,is_todo,handled_at,msg_count,created_at,last_at,read_at,payload&limit=1")
    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.get(q, headers=_h())
    if not _ok(res.status_code):
        raise HTTPException(status_code=502, detail=f"读取详情失败：{res.text[:200]}")
    rows = _rows(res)
    if not rows:
        raise HTTPException(status_code=404, detail="消息不存在")
    return rows[0]
