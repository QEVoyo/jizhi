"""视频库 · 管理后台（2026-09-04 用户定调「后台也要完善」）

视频管理（全量） / 发布审核 / 举报处理 / 批量暖库生成。
"""
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Any

from fastapi import APIRouter, Query, HTTPException, Depends
from pydantic import BaseModel
import httpx

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


def _write_ok(resp, label: str) -> None:
    """写操作的状态码检查。

    ⚠️ PostgREST 对 PATCH / DELETE **不区分「改了 1 行」和「匹配 0 行」**——
       两种都返回 204。所以只看状态码不足以防「改了个不存在的 id 也报成功」，
       必须配合下面的 _require_row 先确认行存在。
       原先本文件这几处把返回值直接丢弃，审核/删除不存在的视频一律报成功。
    """
    if getattr(resp, "status_code", 500) not in (200, 201, 204):
        body = (getattr(resp, "text", "") or "")[:200]
        raise HTTPException(status_code=502, detail=f"{label}失败: {body}")


async def _require_row(table: str, row_id: str, label: str) -> dict:
    """确认这一行确实存在，否则 404。"""
    rows = _rows(await db.select(table, eq={"id": row_id}, use_service_role=True))
    if not rows:
        raise HTTPException(status_code=404, detail=f"{label}不存在")
    return rows[0]


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
    # 先确认视频存在 —— 否则 PATCH 匹配 0 行也是 204，会报"审核成功"
    await _require_row("video_library", video_id, "视频")
    _write_ok(await db.update("video_library", eq={"id": video_id},
                              data={"publish_status": target}, use_service_role=True),
              "视频审核")
    await write_audit_log(current_admin, "video_review", target_type="video",
                          target_id=video_id, detail={"action": action, "publish_status": target})
    return {"success": True, "publish_status": target}


@router.post("/{video_id}/retry")
async def admin_video_retry(video_id: str, current_admin: str = Depends(get_current_admin)):
    """后台重试失败视频（不受本人限制）"""
    v = await _require_row("video_library", video_id, "视频")
    _write_ok(await db.update("video_library", eq={"id": video_id},
                              data={"status": "generating", "error": None}, use_service_role=True),
              "视频重试")
    video_gen.requeue_spec(v.get("subject") or "", v.get("knowledge_key"), v.get("angle"))
    await write_audit_log(current_admin, "video_retry", target_type="video",
                          target_id=video_id)
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
    # 先确认存在 —— 否则 DELETE 匹配 0 行也是 204，删一个不存在的 id 会报成功
    await _require_row("video_library", video_id, "视频")
    _write_ok(await db.delete("video_library", eq={"id": video_id}, use_service_role=True),
              "视频删除")
    await write_audit_log(current_admin, "video_delete", target_type="video",
                          target_id=video_id)
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
    total = await _exact_count("video_reports", {"status": status})

    # ⚠️ 原先这里为给当页 ≤100 条举报补视频信息，**无 eq、无 limit 地全表拉 video_library**
    #    再在 Python 里筛。两个毛病：
    #      ① 全表扫描，视频一多就白拉；
    #      ② 只取前 50 个唯一 video_id（`[...][:50]`），而 page_size 最大 100 ——
    #         第 51 个之后的举报 video 恒为 None，丢哪 50 个还是随机的（set 无序）。
    #    改成按当页实际用到的 id 精确查。
    videos = {}
    if reports:
        ids = sorted({r["video_id"] for r in reports if r.get("video_id")})
        if ids:
            vresp = await db.select("video_library",
                                    select="id,title,knowledge_name,author_name,"
                                           "publish_status,status",
                                    in_={"id": ids}, use_service_role=True)
            for v in _rows(vresp):
                videos[v["id"]] = v
    items = [dict(r, video=videos.get(r.get("video_id"))) for r in reports]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("/reports/{report_id}/handle")
async def admin_video_report_handle(report_id: str, body: dict,
                                    current_admin: str = Depends(get_current_admin)):
    """处理举报：dismiss 驳回（视频保留）/ remove 下架视频"""
    action = str(body.get("action") or "")
    if action not in ("dismiss", "remove"):
        raise HTTPException(status_code=400, detail="action 应为 dismiss/remove")
    report = await _require_row("video_reports", report_id, "举报")

    # ⚠️ 顺序要紧：必须**先回写举报状态、再删视频**。
    #    video_reports.video_id 是 ON DELETE CASCADE（见 sql/fix_video_social.sql），
    #    删视频会连带把这条举报行自己也删掉 —— 原先先删后改，那一改必然命中 0 行，
    #    而返回值被丢弃 → 管理员看到"已处理"，实际举报记录已经没了，
    #    用 ?status=removed 也永远查不到东西。
    #    （根治要靠把外键改成 ON DELETE SET NULL 或给视频做软删，见待办；
    #      在那之前至少保证：状态先落库、且每次处置都有审计留痕 —— 下面就是。）
    _write_ok(await db.update("video_reports", eq={"id": report_id},
                              data={"status": "removed" if action == "remove" else "dismissed",
                                    "handled_by": current_admin,
                                    "handled_at": datetime.now(timezone.utc).isoformat()},
                              use_service_role=True),
              "举报状态回写")

    if action == "remove":
        from config import settings
        try:
            await db._request("DELETE",
                              f"{settings.SUPABASE_URL}/storage/v1/object/video-lib/{report['video_id']}/audio.mp3",
                              dict(db.service_headers), timeout=10.0)
        except Exception:
            pass
        _write_ok(await db.delete("video_library", eq={"id": report["video_id"]},
                                  use_service_role=True),
                  "视频下架删除")
    await write_audit_log(current_admin, "video_report_handle", target_type="video_report",
                          target_id=report_id,
                          detail={"action": action, "video_id": report.get("video_id")})
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
    await write_audit_log(current_admin, "video_warm", target_type="video_library",
                          detail={"enqueued": res["enqueued"], "skipped": res.get("skipped"),
                                  "planned": len(items)})
    return {"success": True, "planned": len(items), **res, "queue": video_gen.queue_stats()}


async def _exact_count(table: str, eq: Optional[dict] = None) -> int:
    """精确行数 —— 从 Content-Range 响应头读，不是从 body 数。

    ⚠️ 此前 stats / reports 是**全表拉取后在 Python 里聚合**。
       PostgREST 单次返回有行数上限（Supabase 默认 max-rows，本项目未确认具体值），
       超上限后**静默截断、无任何报错** —— 看板上的数字看着对、其实少了。
       计数改用 count=exact，不受这个上限影响。
    """
    from config import settings
    params = {"select": "id", "limit": "1"}
    for k, v in (eq or {}).items():
        params[k] = f"eq.{v}"
    headers = dict(db.service_headers)
    headers["Prefer"] = "count=exact"
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(f"{settings.SUPABASE_URL}/rest/v1/{table}",
                             params=params, headers=headers)
    if r.status_code not in (200, 206):
        raise HTTPException(status_code=502, detail=f"{table} 计数失败: {r.status_code}")
    cr = r.headers.get("content-range", "")
    return int(cr.split("/")[-1]) if "/" in cr else 0


@router.get("/stats")
async def admin_video_stats(current_admin: str = Depends(get_current_admin)):
    """视频库数据概览（后台看板用）"""
    total          = await _exact_count("video_library")
    public_ready   = await _exact_count("video_library", {"publish_status": "public", "status": "ready"})
    pending_review = await _exact_count("video_library", {"publish_status": "pending", "status": "ready"})
    generating     = await _exact_count("video_library", {"status": "generating"})
    failed         = await _exact_count("video_library", {"status": "failed"})
    pending_reports = await _exact_count("video_reports", {"status": "pending"})

    # total_views 只能拉出来自己加 —— PostgREST 在本项目里禁用了聚合函数
    # （PGRST123: Use of aggregate functions is not allowed），没有 sum() 可用。
    # 所以这里必须**如实报告有没有被截断**，不能像以前那样悄悄少算。
    from config import settings
    VIEWS_BATCH = 5000
    headers = dict(db.service_headers)
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.get(f"{settings.SUPABASE_URL}/rest/v1/video_library",
                             params={"select": "views_count", "limit": str(VIEWS_BATCH)},
                             headers=headers)
    views_rows = r.json() if r.status_code == 200 and r.text else []
    total_views = sum(int(v.get("views_count") or 0) for v in views_rows)
    views_truncated = len(views_rows) >= VIEWS_BATCH

    return {
        "total": total,
        "public_ready": public_ready,
        "pending_review": pending_review,
        "generating": generating,
        "failed": failed,
        "total_views": total_views,
        # 被截断时前端应当显示"≥"，而不是把它当成精确值
        "total_views_truncated": views_truncated,
        "pending_reports": pending_reports,
        "queue": video_gen.queue_stats(),
    }