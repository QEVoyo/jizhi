"""内容待审队列 · 管理后台（2026-10-15）

信誉值「内容先审后发」的后台那一半：
低信誉用户发的帖子/评论以 status='pending' 落库（仅自己可见），在这里被通过或驳回。

数据层见 sql/content_review_queue.sql。

⚠️ 通过时**必须补发通知**。
   评论在写入时因为没公开而刻意没通知作者（见 posts.py 的说明），
   如果审核通过也不再通知，那条评论就永远没人知道它出现过 ——
   作者以为发了、被评论的人从来不知道。整个流程等于把内容吞掉了。
"""

from datetime import datetime, timezone
from typing import Any, List, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from config import settings
from logging_config import logger
from utils.admin_middleware import get_current_admin, write_audit_log

router = APIRouter(prefix="/admin/content-review", tags=["管理后台·内容审核"])

_TABLES = {"post": "posts", "comment": "comments"}


def _svc_headers() -> dict:
    return {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
    }


def _rows(res: httpx.Response) -> List[dict]:
    if res.status_code not in (200, 206):
        return []
    try:
        data = res.json()
    except Exception:
        return []
    return data if isinstance(data, list) else []


async def _get(table: str, params: dict) -> httpx.Response:
    qs = "&".join(f"{k}={v}" for k, v in params.items())
    async with httpx.AsyncClient(timeout=15.0) as client:
        return await client.get(
            f"{settings.SUPABASE_URL}/rest/v1/{table}?{qs}", headers=_svc_headers()
        )


async def _patch(table: str, row_id: str, body: dict) -> httpx.Response:
    async with httpx.AsyncClient(timeout=15.0) as client:
        return await client.patch(
            f"{settings.SUPABASE_URL}/rest/v1/{table}?id=eq.{row_id}",
            headers={**_svc_headers(), "Prefer": "return=representation"},
            json=body,
        )


class ReviewAction(BaseModel):
    action: str                      # approve / reject
    note: Optional[str] = ""


@router.get("/pending")
async def list_pending(
    kind: str = Query("all", pattern="^(all|post|comment)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_admin: str = Depends(get_current_admin),
):
    """
    待审列表。post 和 comment 是两张表，这里合成一个按时间倒序的流
    —— 管理员关心的是"有什么等着我处理"，不是它存在哪张表里。

    ⚠️ 两表分别取 page_size 条再合并截断，所以某一类特别多时，
       另一类会被挤掉。当前量级（低信誉用户是少数）无所谓；
       真到了"待审积压"的程度，说明阈值该调了，而不是该改这个接口。
    """
    out: List[dict] = []
    kinds = ["post", "comment"] if kind == "all" else [kind]

    for k in kinds:
        table = _TABLES[k]
        res = await _get(table, {
            "status": "eq.pending", "is_deleted": "eq.false",
            "select": "*,profiles!user_id(nickname,user_account,avatar_url)",
            "order": "created_at.desc", "limit": str(page_size),
        })
        if res.status_code not in (200, 206):
            # 表没有 status 列（SQL 没跑）时会 400 —— 明确报出来，
            # 不要让它表现成「没有待审内容」。那会让人以为队列是空的。
            logger.error(f"[content-review] 读取 {table} 失败 status={res.status_code} {res.text[:200]}")
            raise HTTPException(
                status_code=502,
                detail=f"读取待审 {table} 失败（{res.status_code}）。"
                       f"若提示列不存在，请先执行 sql/content_review_queue.sql。",
            )
        for r in _rows(res):
            r["_kind"] = k
            out.append(r)

    out.sort(key=lambda r: r.get("created_at") or "", reverse=True)
    start = (page - 1) * page_size
    return {"items": out[start:start + page_size], "total": len(out), "page": page,
            "page_size": page_size}


@router.get("/stats")
async def review_stats(current_admin: str = Depends(get_current_admin)):
    """待审计数（后台侧边栏角标 / 看板用）"""
    counts = {}
    for k, table in _TABLES.items():
        res = await _get(table, {"status": "eq.pending", "is_deleted": "eq.false", "select": "id"})
        counts[k] = len(_rows(res))
    return {"post": counts.get("post", 0), "comment": counts.get("comment", 0),
            "total": sum(counts.values())}


@router.post("/{kind}/{row_id}")
async def review_one(
    kind: str,
    row_id: str,
    body: ReviewAction,
    current_admin: str = Depends(get_current_admin),
):
    """通过或驳回一条待审内容。"""
    if kind not in _TABLES:
        raise HTTPException(status_code=400, detail="kind 应为 post / comment")
    if body.action not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="action 应为 approve / reject")

    table = _TABLES[kind]
    new_status = "published" if body.action == "approve" else "rejected"

    # 先确认它确实在待审 —— 否则管理员可能对一条已经公开的内容再点一次"通过"，
    # 而那次操作会把 reviewed_by 覆盖掉，审计上就看不出真正是谁审的了。
    cur = _rows(await _get(table, {"id": f"eq.{row_id}", "select": "id,status,user_id,post_id"}))
    if not cur:
        raise HTTPException(status_code=404, detail="内容不存在")
    row = cur[0]
    if row.get("status") != "pending":
        raise HTTPException(status_code=409,
                            detail=f"这条内容当前是 {row.get('status')}，不在待审队列里")

    res = await _patch(table, row_id, {
        "status": new_status,
        "reviewed_by": current_admin,
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "review_note": (body.note or "")[:500] or None,
    })
    if res.status_code not in (200, 204):
        logger.error(f"[content-review] 写回失败 {table}#{row_id} status={res.status_code} {res.text[:200]}")
        raise HTTPException(status_code=502, detail="审核结果写入失败")

    # 回读校验：PostgREST 对「匹配 0 行」也返回 204
    chk = _rows(await _get(table, {"id": f"eq.{row_id}", "select": "status"}))
    if chk and chk[0].get("status") != new_status:
        raise HTTPException(status_code=502,
                            detail=f"审核结果未生效（库中仍为 {chk[0].get('status')}）")

    # ── 通过时补发被压住的通知 ──
    # 见文件头：评论在写入时因为没公开而没通知，通过时必须补上，
    # 否则那条评论永远没人知道它出现过。
    if new_status == "published" and kind == "comment":
        await _notify_after_approve(row, current_admin)

    # ── 驳回时告诉作者，并说清原因 ──
    if new_status == "rejected" and row.get("user_id"):
        await _notify_author_rejected(kind, row_id, row["user_id"], body.note or "")

    await write_audit_log(
        admin_id=current_admin,
        action=f"content_review_{body.action}",
        target_type=kind,
        target_id=row_id,
        detail={"author_id": row.get("user_id"), "note": body.note or ""},
    )
    return {"success": True, "status": new_status}


async def _notify_after_approve(row: dict, admin_id: str) -> None:
    try:
        from utils.notification import notify, NotifyError
        post_id = row.get("post_id")
        author = row.get("user_id")
        if not post_id or not author:
            return
        # 帖子作者 —— 通知内容与 posts.py 的 _notify_comment 保持一致口径
        pr = _rows(await _get("posts", {"id": f"eq.{post_id}", "select": "user_id,title"}))
        if not pr:
            return
        owner = pr[0].get("user_id")
        if not owner or owner == author:
            return
        await notify(owner, "social.post_comment", actor_id=author,
                     source_id=post_id,
                     title="有人评论了你的动态",
                     content="（该评论刚才通过了审核）")
    except Exception as e:
        # 通知是派生产物，失败不改审核结果，但必须留痕
        logger.error(f"[content-review] 通过后补发通知失败: {e}")


async def _notify_author_rejected(kind: str, row_id: str, author: str, note: str) -> None:
    """驳回必须告诉作者，且必须带原因 —— 不然他只会反复重发同一条。"""
    try:
        from utils.notification import notify
        kind_label = "动态" if kind == "post" else "评论"
        await notify(author, "system.content_rejected",
                     title=f"你的{kind_label}未通过审核",
                     content=note or "内容未通过审核，如有疑问可联系管理员。",
                     link="/community")
    except KeyError:
        # 注册表里还没登记 system.content_rejected —— 这是**已知会走到**的分支，
        # 因为加消息点要走 notification_registry。留 ERROR 而不是静默。
        logger.error("[content-review] 待办类型 system.content_rejected 未注册，"
                     "驳回通知未发送（请在 notification_registry 里补登记）")
    except Exception as e:
        logger.error(f"[content-review] 驳回通知失败: {e}")
