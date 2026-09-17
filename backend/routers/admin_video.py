"""视频库 · 管理后台（2026-09-04 用户定调「后台也要完善」）

视频管理（全量） / 发布审核 / 举报处理 / 批量暖库生成。
"""
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Any

from fastapi import APIRouter, Query, HTTPException, Depends
from pydantic import BaseModel

from services.supabase import db
from services import video_gen
from utils.admin_middleware import get_current_admin, write_audit_log
from logging_config import logger

router = APIRouter(prefix="/admin/video", tags=["管理后台·视频库"])


def _rows(resp) -> List[dict]:
    if getattr(resp, "status_code", 300) >= 300:
        return []
    try:
        data = resp.json()
    except Exception:
        return []
    return data if isinstance(data, list) else []


@router.get("/list")
async def admin_video_list(
    subject: str = Query(""),
    publish_status: str = Query(""),
    status: str = Query(""),
    q: str = Query(""),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_admin: str = Depends(get_current_admin),
):
    """视频管理列表（全状态，含未发布的用户生成内容）"""
    eq = {}
    if subject:
        eq["subject"] = subject
    if publish_status:
        eq["publish_status"] = publish_status
    if status:
        eq["status"] = status
    or_ = f"(title.ilike.%{q}%,knowledge_name.ilike.%{q}%)" if q else None
    resp = await db.select("video_library", eq=eq, or_=or_,
                           order="created_at.desc",
                           limit=page_size, offset=(page - 1) * page_size,
                           use_service_role=True)
    return {"items": _rows(resp), "page": page, "page_size": page_size}


@router.post("/{video_id}/review")
async def admin_video_review(video_id: str, body: dict,
                             current_admin: str = Depends(get_current_admin)):
    """审核用户发布申请：approve → public / reject → rejected"""
    action = str(body.get("action") or "")
    if action not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="action 应为 approve/reject")
    target = "public" if action == "approve" else "rejected"
    await db.update("video_library", eq={"id": video_id},
                    data={"publish_status": target}, use_service_role=True)
    write_audit_log(current_admin, f"视频审核 {action}: {video_id}")
    return {"success": True, "publish_status": target}


@router.post("/{video_id}/retry")
async def admin_video_retry(video_id: str, current_admin: str = Depends(get_current_admin)):
    """后台重试失败视频（不受本人限制）"""
    rows = _rows(await db.select("video_library", eq={"id": video_id}, use_service_role=True))
    if not rows:
        raise HTTPException(status_code=404, detail="视频不存在")
    v = rows[0]
    await db.update("video_library", eq={"id": video_id},
                    data={"status": "generating", "error": None}, use_service_role=True)
    video_gen.requeue_spec(v.get("subject") or "", v.get("knowledge_key"), v.get("angle"))
    write_audit_log(current_admin, f"视频库重试生成: {video_id}")
    return {"success": True}


@router.delete("/{video_id}")
async def admin_video_remove(video_id: str, current_admin: str = Depends(get_current_admin)):
    """下架/删除视频（含存储尽力清理）"""
    from config import settings
    try:
        await db._request("DELETE",
                          f"{settings.SUPABASE_URL}/storage/v1/object/video-lib/{video_id}/audio.mp3",
                          dict(db.service_headers), timeout=10.0)
    except Exception:
        pass
    await db.delete("video_library", eq={"id": video_id}, use_service_role=True)
    write_audit_log(current_admin, f"视频下架删除: {video_id}")
    return {"success": True}


@router.get("/reports")
async def admin_video_reports(
    status: str = Query("pending"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_admin: str = Depends(get_current_admin),
):
    """举报列表（带视频信息）"""
    resp = await db.select("video_reports", eq={"status": status},
                           order="created_at.desc",
                           limit=page_size, offset=(page - 1) * page_size,
                           use_service_role=True)
    reports = _rows(resp)
    videos = {}
    if reports:
        ids = list({r["video_id"] for r in reports})[:50]
        vresp = await db.select("video_library", select="id,title,knowledge_name,author_name,"
                                                      "publish_status,status",
                                use_service_role=True)
        for v in _rows(vresp):
            if v["id"] in ids:
                videos[v["id"]] = v
    items = [dict(r, video=videos.get(r.get("video_id"))) for r in reports]
    return {"items": items}


@router.post("/reports/{report_id}/handle")
async def admin_video_report_handle(report_id: str, body: dict,
                                    current_admin: str = Depends(get_current_admin)):
    """处理举报：dismiss 驳回（视频保留）/ remove 下架视频"""
    action = str(body.get("action") or "")
    if action not in ("dismiss", "remove"):
        raise HTTPException(status_code=400, detail="action 应为 dismiss/remove")
    rows = _rows(await db.select("video_reports", eq={"id": report_id}, use_service_role=True))
    if not rows:
        raise HTTPException(status_code=404, detail="举报不存在")
    report = rows[0]
    if action == "remove":
        from config import settings
        try:
            await db._request("DELETE",
                              f"{settings.SUPABASE_URL}/storage/v1/object/video-lib/{report['video_id']}/audio.mp3",
                              dict(db.service_headers), timeout=10.0)
        except Exception:
            pass
        await db.delete("video_library", eq={"id": report["video_id"]}, use_service_role=True)
    await db.update("video_reports", eq={"id": report_id},
                    data={"status": "removed" if action == "remove" else "dismissed",
                          "handled_by": current_admin,
                          "handled_at": datetime.now(timezone.utc).isoformat()},
                    use_service_role=True)
    write_audit_log(current_admin, f"视频举报处理 {action}: report={report_id}")
    return {"success": True}


class AdminWarmReq(BaseModel):
    syllabus_ids: Optional[List[str]] = None   # 空 = 全部考纲
    per: int = 1                               # 每考纲取前 N 个知识点
    goal: int = 1
    max_n: int = 0


@router.post("/warm")
async def admin_video_warm(req: AdminWarmReq, current_admin: str = Depends(get_current_admin)):
    """后台批量暖库：按考纲枚举高频知识点 → 官方基智批量生成（先 dry 可传 max_n=0 只看清单）"""
    items = video_gen.collect_syllabus_knowledge(req.syllabus_ids, per=req.per, max_n=req.max_n)
    res = await video_gen.warm_batch(items, goal=req.goal)
    write_audit_log(current_admin, f"视频库批量暖库: enqueued={res['enqueued']} items={len(items)}")
    return {"success": True, "planned": len(items), **res, "queue": video_gen.queue_stats()}


@router.get("/stats")
async def admin_video_stats(current_admin: str = Depends(get_current_admin)):
    """视频库数据概览（后台看板用）"""
    total = _rows(await db.select("video_library", select="id,publish_status,status,views_count",
                                  use_service_role=True))
    by_status = {}
    for v in total:
        key = f"{v.get('publish_status')}|{v.get('status')}"
        by_status[key] = by_status.get(key, 0) + 1
    reports = _rows(await db.select("video_reports", select="id,status", use_service_role=True))
    pending_reports = sum(1 for r in reports if r.get("status") == "pending")
    return {
        "total": len(total),
        "public_ready": by_status.get("public|ready", 0),
        "pending_review": by_status.get("pending|ready", 0),
        "generating": sum(v for k, v in by_status.items() if k.endswith("|generating")),
        "failed": sum(v for k, v in by_status.items() if k.endswith("|failed")),
        "total_views": sum(int(v.get("views_count") or 0) for v in total),
        "pending_reports": pending_reports,
        "queue": video_gen.queue_stats(),
    }