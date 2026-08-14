"""
管理后台 API
所有接口（除公告公开查询外）均需管理员身份验证
"""
from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from pathlib import Path
import uuid
import httpx
import time
from urllib.parse import quote

from config import settings
from utils.admin_middleware import get_current_admin, get_current_super_admin, get_admin_headers, write_audit_log
import local_question_bank

router = APIRouter(prefix="/admin", tags=["管理后台"])


# ============================
# 辅助函数
# ============================

def _supabase_url(path: str, **params) -> str:
    """构建 Supabase REST API URL，params 中的 None/空值会被跳过"""
    base = f"{settings.SUPABASE_URL}/rest/v1/{path}"
    parts = []
    for k, v in params.items():
        if v is not None and v != "" and not (isinstance(v, str) and v.strip() == ""):
            parts.append(f"{k}={v}")
    if parts:
        return base + "?" + "&".join(parts)
    return base


async def _supabase_get(path: str, **params) -> httpx.Response:
    """带管理员头的 GET 请求"""
    url = _supabase_url(path, **params)
    async with httpx.AsyncClient(timeout=15.0) as client:
        return await client.get(url, headers=get_admin_headers())


async def _supabase_get_with_count(path: str, **params) -> tuple[list[dict], int]:
    """带 Prefer: count=exact 的 GET，返回 (数据列表, 总数)"""
    url = _supabase_url(path, **params)
    headers = get_admin_headers()
    headers["Prefer"] = "count=exact"
    async with httpx.AsyncClient(timeout=15.0) as client:
        res = await client.get(url, headers=headers)
    if res.status_code != 200:
        return [], 0
    data = res.json() if res.text else []
    content_range = res.headers.get("content-range", "")
    total = int(content_range.split("/")[-1]) if "/" in content_range else len(data)
    return data, total


async def _supabase_post(path: str, body: dict) -> httpx.Response:
    """带管理员头的 POST 请求"""
    headers = get_admin_headers()
    headers["Prefer"] = "return=representation"
    async with httpx.AsyncClient(timeout=15.0) as client:
        return await client.post(
            f"{settings.SUPABASE_URL}/rest/v1/{path}",
            headers=headers,
            json=body,
        )


async def _supabase_patch(path: str, body: dict) -> httpx.Response:
    """带管理员头的 PATCH 请求"""
    async with httpx.AsyncClient(timeout=15.0) as client:
        return await client.patch(
            f"{settings.SUPABASE_URL}/rest/v1/{path}",
            headers=get_admin_headers(),
            json=body,
        )


async def _supabase_delete(path: str) -> httpx.Response:
    """带管理员头的 DELETE 请求"""
    async with httpx.AsyncClient(timeout=15.0) as client:
        return await client.delete(
            f"{settings.SUPABASE_URL}/rest/v1/{path}",
            headers=get_admin_headers(),
        )


def _safe_int_from_header(res: httpx.Response) -> int:
    """从 content-range 头中提取总数"""
    try:
        cr = res.headers.get("content-range", "")
        if "/" in cr:
            return int(cr.split("/")[-1])
    except Exception:
        pass
    return 0


# ============================
# 请求/响应模型
# ============================

class DashboardResponse(BaseModel):
    total_users: int = 0
    today_new_users: int = 0
    total_questions_done: int = 0
    today_questions_done: int = 0
    pending_reports: int = 0
    pending_feedback: int = 0
    total_plans: int = 0


class UserListItem(BaseModel):
    id: str
    email: Optional[str] = None
    nickname: Optional[str] = None
    user_account: Optional[str] = None
    avatar_url: Optional[str] = None
    learning_stage: Optional[str] = None
    is_admin: bool = False
    is_active: bool = True
    role: str = "user"
    created_at: Optional[str] = None


class UserDetailResponse(BaseModel):
    id: str
    email: Optional[str] = None
    nickname: Optional[str] = None
    user_account: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    learning_stage: Optional[str] = None
    grade: Optional[str] = None
    major: Optional[str] = None
    learning_goal: Optional[str] = None
    difficulty_preference: Optional[str] = None
    learning_style: Optional[str] = None
    daily_study_time: Optional[str] = None
    is_admin: bool = False
    is_active: bool = True
    role: str = "user"
    created_at: Optional[str] = None
    plan_count: int = 0
    question_count: int = 0
    post_count: int = 0


class StatusUpdate(BaseModel):
    is_active: bool


class AdminToggle(BaseModel):
    is_admin: bool


class ResolveReport(BaseModel):
    status: str  # "resolved" | "dismissed"
    admin_note: Optional[str] = None


class ResolveFeedback(BaseModel):
    status: str = "resolved"
    admin_note: Optional[str] = None


class ResolveQA(BaseModel):
    status: str = "resolved"
    admin_note: Optional[str] = None


class QuestionCreate(BaseModel):
    category: str = ""
    sub_category: str = ""
    question_type: str = ""
    difficulty: int = 1
    content: Optional[Dict[str, Any]] = None
    answer: Optional[Any] = None
    analysis: Optional[str] = None
    kp_name: Optional[str] = None
    id: Optional[str] = None
    # 允许额外字段
    class Config:
        extra = "allow"


class QuestionImport(BaseModel):
    questions: List[Dict[str, Any]]


class AnnouncementCreate(BaseModel):
    title: str
    content: str = ""
    image_url: str = ""
    is_active: bool = True


class AnnouncementUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None


class PaginatedResponse(BaseModel):
    items: List[Any] = []
    total: int = 0
    page: int = 1
    page_size: int = 20


class SystemSettings(BaseModel):
    question_bank_count: int = 0
    syllabus_count: int = 0
    api_providers: Dict[str, bool] = {}


# ============================
# 仪表盘
# ============================

@router.get("/dashboard", response_model=DashboardResponse)
async def dashboard(current_admin: str = Depends(get_current_admin)):
    """管理后台仪表盘 - 总览数据"""
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    total_users = 0
    today_new_users = 0
    total_questions_done = 0
    today_questions_done = 0
    pending_reports = 0
    pending_feedback = 0
    total_plans = 0

    async with httpx.AsyncClient(timeout=20.0) as client:
        headers = get_admin_headers()

        # 用户总数
        try:
            headers["Prefer"] = "count=exact"
            r = await client.get(
                _supabase_url("profiles", select="*", limit="1"),
                headers=headers,
            )
            total_users = _safe_int_from_header(r)
        except Exception:
            pass

        # 今日新增用户
        try:
            r = await client.get(
                _supabase_url("profiles", select="*", limit="1",
                              created_at=f"gte.{today_str}"),
                headers=headers,
            )
            today_new_users = _safe_int_from_header(r)
        except Exception:
            pass

        # 总答题数
        try:
            r = await client.get(
                _supabase_url("question_records", select="*", limit="1"),
                headers=headers,
            )
            total_questions_done = _safe_int_from_header(r)
        except Exception:
            pass

        # 今日答题数
        try:
            r = await client.get(
                _supabase_url("question_records", select="*", limit="1",
                              created_at=f"gte.{today_str}"),
                headers=headers,
            )
            today_questions_done = _safe_int_from_header(r)
        except Exception:
            pass

        # 待处理举报
        try:
            r = await client.get(
                _supabase_url("content_reports", select="*", limit="1",
                              status="eq.pending"),
                headers=headers,
            )
            pending_reports = _safe_int_from_header(r)
        except Exception:
            pass

        # 待处理反馈
        try:
            r = await client.get(
                _supabase_url("user_feedback", select="*", limit="1",
                              status="eq.pending"),
                headers=headers,
            )
            pending_feedback = _safe_int_from_header(r)
        except Exception:
            pass

        # 总学习计划数
        try:
            r = await client.get(
                _supabase_url("subject_plans", select="*", limit="1"),
                headers=headers,
            )
            total_plans = _safe_int_from_header(r)
        except Exception:
            pass

    return DashboardResponse(
        total_users=total_users,
        today_new_users=today_new_users,
        total_questions_done=total_questions_done,
        today_questions_done=today_questions_done,
        pending_reports=pending_reports,
        pending_feedback=pending_feedback,
        total_plans=total_plans,
    )


# ============================
# 用户管理
# ============================

@router.get("/users")
async def list_users(
    search: str = Query(default="", description="搜索邮箱或昵称"),
    status: str = Query(default="", description="active / banned"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_admin: str = Depends(get_current_admin),
):
    """用户列表 - 分页 + 搜索 + 状态筛选"""
    params = {
        "select": "id,email,nickname,user_account,avatar_url,learning_stage,is_admin,is_active,role,created_at",
        "order": "created_at.desc",
        "limit": str(page_size),
        "offset": str((page - 1) * page_size),
    }

    # 搜索：邮箱或昵称模糊匹配
    search_clauses = []
    if search.strip():
        encoded = quote(search.strip())
        search_clauses.append(f"or=(email.ilike.*{encoded}*,nickname.ilike.*{encoded}*)")
    if status == "active":
        search_clauses.append("is_active=eq.true")
    elif status == "banned":
        search_clauses.append("is_active=eq.false")

    # 手动拼接 URL（避免 httpx 编码 PostgREST 特殊字符）
    base = f"{settings.SUPABASE_URL}/rest/v1/profiles"
    query_parts = [f"{k}={v}" for k, v in params.items()]
    query_parts.extend(search_clauses)
    url = base + "?" + "&".join(query_parts)

    headers = get_admin_headers()
    headers["Prefer"] = "count=exact"

    async with httpx.AsyncClient(timeout=15.0) as client:
        res = await client.get(url, headers=headers)
        if res.status_code != 200:
            return PaginatedResponse(items=[], total=0, page=page, page_size=page_size)

        data = res.json() if res.text else []
        total = _safe_int_from_header(res)

    items = []
    for u in data:
        items.append(UserListItem(
            id=u.get("id", ""),
            email=u.get("email"),
            nickname=u.get("nickname"),
            user_account=u.get("user_account"),
            avatar_url=u.get("avatar_url"),
            learning_stage=u.get("learning_stage"),
            is_admin=u.get("is_admin", False),
            is_active=u.get("is_active", True),
            role=u.get("role", "user"),
            created_at=u.get("created_at"),
        ))

    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/users/{user_id}", response_model=UserDetailResponse)
async def get_user_detail(
    user_id: str,
    current_admin: str = Depends(get_current_admin),
):
    """查看用户详情 + 统计数据"""
    async with httpx.AsyncClient(timeout=20.0) as client:
        headers = get_admin_headers()

        # 1. 基础信息
        res = await client.get(
            _supabase_url("profiles", select="*", id=f"eq.{user_id}"),
            headers=headers,
        )
        if res.status_code != 200 or not res.json():
            raise HTTPException(status_code=404, detail="用户不存在")

        user = res.json()[0]

        # 2. 学习计划数
        plan_count = 0
        try:
            headers["Prefer"] = "count=exact"
            r = await client.get(
                _supabase_url("subject_plans", select="*", limit="1",
                              user_id=f"eq.{user_id}"),
                headers=headers,
            )
            plan_count = _safe_int_from_header(r)
        except Exception:
            pass

        # 3. 答题数
        question_count = 0
        try:
            r = await client.get(
                _supabase_url("question_records", select="*", limit="1",
                              user_id=f"eq.{user_id}"),
                headers=headers,
            )
            question_count = _safe_int_from_header(r)
        except Exception:
            pass

        # 4. 帖子数（posts 表可能不存在，做容错）
        post_count = 0
        try:
            r = await client.get(
                _supabase_url("posts", select="*", limit="1",
                              author_id=f"eq.{user_id}"),
                headers=headers,
            )
            if r.status_code == 200:
                post_count = _safe_int_from_header(r)
        except Exception:
            pass

    return UserDetailResponse(
        id=user.get("id", ""),
        email=user.get("email"),
        nickname=user.get("nickname"),
        user_account=user.get("user_account"),
        avatar_url=user.get("avatar_url"),
        bio=user.get("bio"),
        learning_stage=user.get("learning_stage"),
        grade=user.get("grade"),
        major=user.get("major"),
        learning_goal=user.get("learning_goal"),
        difficulty_preference=user.get("difficulty_preference"),
        learning_style=user.get("learning_style"),
        daily_study_time=user.get("daily_study_time"),
        is_admin=user.get("is_admin", False),
        is_active=user.get("is_active", True),
        created_at=user.get("created_at"),
        plan_count=plan_count,
        question_count=question_count,
        post_count=post_count,
    )


@router.put("/users/{user_id}/status")
async def toggle_user_status(
    user_id: str,
    body: StatusUpdate,
    current_admin: str = Depends(get_current_admin),
):
    """封禁/解封用户"""
    res = await _supabase_patch(
        f"profiles?id=eq.{user_id}",
        {"is_active": body.is_active},
    )
    if res.status_code not in (200, 204):
        raise HTTPException(status_code=500, detail="操作失败")

    action = "ban_user" if not body.is_active else "unban_user"
    await write_audit_log(
        admin_id=current_admin,
        action=action,
        target_type="user",
        target_id=user_id,
        detail={"is_active": body.is_active},
    )

    return {"success": True, "message": "封禁成功" if not body.is_active else "解封成功"}


@router.put("/users/{user_id}/admin")
async def toggle_admin(
    user_id: str,
    body: AdminToggle,
    current_admin: str = Depends(get_current_admin),
):
    """设置/取消管理员（仅超级管理员可操作）"""
    if user_id == current_admin and not body.is_admin:
        raise HTTPException(status_code=400, detail="不能取消自己的超级管理员权限")

    new_role = "admin" if body.is_admin else "user"
    res = await _supabase_patch(
        f"profiles?id=eq.{user_id}",
        {"role": new_role, "is_admin": body.is_admin},
    )
    if res.status_code not in (200, 204):
        raise HTTPException(status_code=500, detail="操作失败")

    action = "set_admin" if body.is_admin else "remove_admin"
    await write_audit_log(
        admin_id=current_admin,
        action=action,
        target_type="user",
        target_id=user_id,
        detail={"role": new_role, "is_admin": body.is_admin},
    )

    return {"success": True, "message": "已设为管理员" if body.is_admin else "已取消管理员"}


# ============================
# 内容审核
# ============================

@router.get("/reports")
async def list_reports(
    status: str = Query(default=""),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_admin: str = Depends(get_current_admin),
):
    """举报列表"""
    params = {
        "select": "*",
        "order": "created_at.desc",
        "limit": str(page_size),
        "offset": str((page - 1) * page_size),
    }
    if status:
        params["status"] = f"eq.{status}"

    url = _supabase_url("content_reports", **params)
    headers = get_admin_headers()
    headers["Prefer"] = "count=exact"

    async with httpx.AsyncClient(timeout=15.0) as client:
        res = await client.get(url, headers=headers)
        if res.status_code != 200:
            return PaginatedResponse(items=[], total=0, page=page, page_size=page_size)
        data = res.json() if res.text else []
        total = _safe_int_from_header(res)

    return PaginatedResponse(items=data, total=total, page=page, page_size=page_size)


@router.put("/reports/{report_id}/resolve")
async def resolve_report(
    report_id: str,
    body: ResolveReport,
    current_admin: str = Depends(get_current_admin),
):
    """处理举报"""
    if body.status not in ("resolved", "dismissed"):
        raise HTTPException(status_code=400, detail="状态只能是 resolved 或 dismissed")

    update_data: dict = {
        "status": body.status,
        "admin_id": current_admin,
        "resolved_at": datetime.now(timezone.utc).isoformat(),
    }
    if body.admin_note:
        update_data["admin_note"] = body.admin_note

    res = await _supabase_patch(f"content_reports?id=eq.{report_id}", update_data)
    if res.status_code not in (200, 204):
        raise HTTPException(status_code=500, detail="操作失败")

    await write_audit_log(
        admin_id=current_admin,
        action=f"resolve_report_{body.status}",
        target_type="report",
        target_id=report_id,
        detail={"status": body.status, "admin_note": body.admin_note or ""},
    )

    return {"success": True, "message": "已处理"}


# ============================
# 反馈管理
# ============================

@router.get("/feedback")
async def list_feedback(
    status: str = Query(default=""),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_admin: str = Depends(get_current_admin),
):
    """反馈列表"""
    params = {
        "select": "*",
        "order": "created_at.desc",
        "limit": str(page_size),
        "offset": str((page - 1) * page_size),
    }
    if status:
        params["status"] = f"eq.{status}"

    url = _supabase_url("user_feedback", **params)
    headers = get_admin_headers()
    headers["Prefer"] = "count=exact"

    async with httpx.AsyncClient(timeout=15.0) as client:
        res = await client.get(url, headers=headers)
        if res.status_code != 200:
            return PaginatedResponse(items=[], total=0, page=page, page_size=page_size)
        data = res.json() if res.text else []
        total = _safe_int_from_header(res)

    return PaginatedResponse(items=data, total=total, page=page, page_size=page_size)


@router.put("/feedback/{feedback_id}")
async def resolve_feedback(
    feedback_id: str,
    body: ResolveFeedback,
    current_admin: str = Depends(get_current_admin),
):
    """处理反馈"""
    update_data: dict = {
        "status": "resolved",
        "resolved_at": datetime.now(timezone.utc).isoformat(),
    }
    if body.admin_note:
        update_data["admin_note"] = body.admin_note

    res = await _supabase_patch(f"user_feedback?id=eq.{feedback_id}", update_data)
    if res.status_code not in (200, 204):
        raise HTTPException(status_code=500, detail="操作失败")

    await write_audit_log(
        admin_id=current_admin,
        action="resolve_feedback",
        target_type="feedback",
        target_id=feedback_id,
        detail={"admin_note": body.admin_note or ""},
    )

    return {"success": True, "message": "已处理"}


# ============================
# Q&A 管理
# ============================

@router.get("/qa")
async def list_qa(
    status: str = Query(default=""),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_admin: str = Depends(get_current_admin),
):
    """Q&A 列表"""
    params = {
        "select": "*",
        "order": "created_at.desc",
        "limit": str(page_size),
        "offset": str((page - 1) * page_size),
    }
    if status:
        params["status"] = f"eq.{status}"

    url = _supabase_url("user_qa", **params)
    headers = get_admin_headers()
    headers["Prefer"] = "count=exact"

    async with httpx.AsyncClient(timeout=15.0) as client:
        res = await client.get(url, headers=headers)
        if res.status_code != 200:
            return PaginatedResponse(items=[], total=0, page=page, page_size=page_size)
        data = res.json() if res.text else []
        total = _safe_int_from_header(res)

    return PaginatedResponse(items=data, total=total, page=page, page_size=page_size)


@router.put("/qa/{qa_id}")
async def resolve_qa(
    qa_id: str,
    body: ResolveQA,
    current_admin: str = Depends(get_current_admin),
):
    """处理 Q&A"""
    update_data: dict = {
        "status": "resolved",
        "resolved_at": datetime.now(timezone.utc).isoformat(),
    }
    if body.admin_note:
        update_data["admin_note"] = body.admin_note

    res = await _supabase_patch(f"user_qa?id=eq.{qa_id}", update_data)
    if res.status_code not in (200, 204):
        raise HTTPException(status_code=500, detail="操作失败")

    await write_audit_log(
        admin_id=current_admin,
        action="resolve_qa",
        target_type="qa",
        target_id=qa_id,
        detail={"admin_note": body.admin_note or ""},
    )

    return {"success": True, "message": "已处理"}


# ============================
# 题目库管理
# ============================

@router.get("/questions")
async def list_questions(
    category: str = Query(default=""),
    sub_category: str = Query(default=""),
    question_type: str = Query(default=""),
    search: str = Query(default=""),
    syllabus_id: str = Query(default=""),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_admin: str = Depends(get_current_admin),
):
    """题目列表 + 统计（支持按考纲筛选）"""
    results, total = local_question_bank.query_global(
        category=category or None,
        sub_category=sub_category or None,
        question_type=question_type or None,
        search=search or None,
        syllabus_id=syllabus_id or None,
        limit=page_size,
        offset=(page - 1) * page_size,
    )

    stats = local_question_bank.all_category_stats()

    return {
        "items": results,
        "total": total,
        "page": page,
        "page_size": page_size,
        "stats": stats,
    }


@router.get("/questions/{question_id}")
async def get_question(
    question_id: str,
    current_admin: str = Depends(get_current_admin),
):
    """获取单道题目（跨考纲查找）"""
    sid, q = local_question_bank.find_question_global(question_id)
    if not q:
        raise HTTPException(status_code=404, detail="题目不存在")
    return {**q, "syllabus_id": sid}


@router.post("/questions")
async def create_question(
    body: QuestionCreate,
    syllabus_id: str = Query(default="cet4"),
    current_admin: str = Depends(get_current_admin),
):
    """新增题目（需指定考纲）"""
    if not local_question_bank.has_bank(syllabus_id):
        raise HTTPException(status_code=400, detail=f"考纲 {syllabus_id} 无题库配置")

    new_q = body.model_dump(exclude_unset=False)
    if not new_q.get("id"):
        new_q["id"] = str(uuid.uuid4())
    if new_q.get("difficulty") is None:
        new_q["difficulty"] = 3

    local_question_bank.add_questions(syllabus_id, [new_q])

    await write_audit_log(
        admin_id=current_admin,
        action="create_question",
        target_type="question",
        target_id=new_q["id"],
        detail={"syllabus_id": syllabus_id, "category": new_q.get("category", ""),
                "question_type": new_q.get("question_type", "")},
    )

    return {"success": True, "id": new_q["id"], "message": "题目已创建"}


@router.put("/questions/{question_id}")
async def update_question(
    question_id: str,
    body: QuestionCreate,
    current_admin: str = Depends(get_current_admin),
):
    """更新题目"""
    sid, q = local_question_bank.find_question_global(question_id)
    if not q:
        raise HTTPException(status_code=404, detail="题目不存在")

    update_data = body.model_dump(exclude_unset=True)
    update_data.pop("id", None)
    q.update(update_data)
    local_question_bank.save_bank_to_file(sid)

    await write_audit_log(
        admin_id=current_admin,
        action="update_question",
        target_type="question",
        target_id=question_id,
        detail={"syllabus_id": sid, "updated_fields": list(update_data.keys())},
    )

    return {"success": True, "message": "题目已更新"}


@router.delete("/questions/{question_id}")
async def delete_question(
    question_id: str,
    current_admin: str = Depends(get_current_admin),
):
    """删除题目"""
    ok, sid = local_question_bank.delete_question_global(question_id)
    if not ok:
        raise HTTPException(status_code=404, detail="题目不存在")

    await write_audit_log(
        admin_id=current_admin,
        action="delete_question",
        target_type="question",
        target_id=question_id,
        detail={"syllabus_id": sid},
    )

    return {"success": True, "message": "题目已删除"}


@router.post("/questions/import")
async def import_questions(
    body: QuestionImport,
    syllabus_id: str = Query(default="cet4"),
    current_admin: str = Depends(get_current_admin),
):
    """批量导入题目（需指定考纲）"""
    if not local_question_bank.has_bank(syllabus_id):
        raise HTTPException(status_code=400, detail=f"考纲 {syllabus_id} 无题库配置")

    imported_count = 0
    for q in body.questions:
        if not q.get("id"):
            q["id"] = str(uuid.uuid4())
        imported_count += 1

    local_question_bank.add_questions(syllabus_id, body.questions)

    await write_audit_log(
        admin_id=current_admin,
        action="import_questions",
        target_type="question",
        detail={"count": imported_count},
    )

    return {"success": True, "imported": imported_count, "message": f"已导入 {imported_count} 道题目"}


# ============================
# 公告管理
# ============================

@router.get("/announcements")
async def list_announcements(
    current_admin: str = Depends(get_current_admin),
):
    """公告列表（管理员视图，含未激活的）"""
    params = {
        "select": "*",
        "order": "created_at.desc",
    }
    url = _supabase_url("system_announcements", **params)
    async with httpx.AsyncClient(timeout=15.0) as client:
        res = await client.get(url, headers=get_admin_headers())
        if res.status_code != 200:
            return []
        return res.json()


@router.get("/announcements/active")
async def list_active_announcements():
    """公开公告列表（无需管理员身份）"""
    params = {
        "select": "*",
        "order": "created_at.desc",
        "is_active": "eq.true",
    }
    url = _supabase_url("system_announcements", **params)
    async with httpx.AsyncClient(timeout=15.0) as client:
        res = await client.get(url, headers=get_admin_headers())
        if res.status_code != 200:
            return []
        return res.json()


@router.post("/announcements")
async def create_announcement(
    body: AnnouncementCreate,
    current_admin: str = Depends(get_current_admin),
):
    """发布公告"""
    insert_data = {
        "title": body.title,
        "content": body.content,
        "is_active": body.is_active,
        "created_by": current_admin,
    }
    if body.image_url:
        insert_data["image_url"] = body.image_url
    import logging
    logger = logging.getLogger(__name__)
    res = await _supabase_post("system_announcements", insert_data)
    logger.warning(f"[announcement] POST status={res.status_code} body={res.text[:500]}")
    if res.status_code not in (200, 201):
        detail = "发布失败"
        try:
            err_body = res.json()
            detail = err_body.get("message", str(err_body))
        except:
            detail = res.text[:200] or "未知错误"
        raise HTTPException(status_code=500, detail=detail)

    created = res.json() if res.text else {}
    ann_id = created[0].get("id", "") if isinstance(created, list) and created else ""

    await write_audit_log(
        admin_id=current_admin,
        action="create_announcement",
        target_type="announcement",
        target_id=ann_id,
        detail={"title": body.title},
    )

    return {"success": True, "id": ann_id, "message": "公告已发布"}


@router.put("/announcements/{announcement_id}")
async def update_announcement(
    announcement_id: str,
    body: AnnouncementUpdate,
    current_admin: str = Depends(get_current_admin),
):
    """编辑公告"""
    update_data = body.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="没有要更新的内容")
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    res = await _supabase_patch(
        f"system_announcements?id=eq.{announcement_id}",
        update_data,
    )
    if res.status_code not in (200, 204):
        raise HTTPException(status_code=500, detail="更新失败")

    await write_audit_log(
        admin_id=current_admin,
        action="update_announcement",
        target_type="announcement",
        target_id=announcement_id,
        detail={"updated_fields": list(update_data.keys())},
    )

    return {"success": True, "message": "公告已更新"}


@router.delete("/announcements/{announcement_id}")
async def delete_announcement(
    announcement_id: str,
    current_admin: str = Depends(get_current_admin),
):
    """删除公告"""
    res = await _supabase_delete(f"system_announcements?id=eq.{announcement_id}")
    if res.status_code not in (200, 204):
        raise HTTPException(status_code=500, detail="删除失败")

    await write_audit_log(
        admin_id=current_admin,
        action="delete_announcement",
        target_type="announcement",
        target_id=announcement_id,
    )

    return {"success": True, "message": "公告已删除"}


# ============================
# 审计日志
# ============================

@router.get("/logs")
async def list_audit_logs(
    action: str = Query(default=""),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=30, ge=1, le=100),
    current_admin: str = Depends(get_current_admin),
):
    """审计日志列表"""
    params = {
        "select": "*",
        "order": "created_at.desc",
        "limit": str(page_size),
        "offset": str((page - 1) * page_size),
    }
    if action:
        params["action"] = f"eq.{action}"

    url = _supabase_url("admin_audit_logs", **params)
    headers = get_admin_headers()
    headers["Prefer"] = "count=exact"

    async with httpx.AsyncClient(timeout=15.0) as client:
        res = await client.get(url, headers=headers)
        if res.status_code != 200:
            return PaginatedResponse(items=[], total=0, page=page, page_size=page_size)
        data = res.json() if res.text else []
        total = _safe_int_from_header(res)

    return PaginatedResponse(items=data, total=total, page=page, page_size=page_size)


# ============================
# 系统信息
# ============================

@router.get("/settings")
async def get_system_settings(current_admin: str = Depends(get_current_admin)):
    """系统配置信息"""
    return SystemSettings(
        question_bank_count=local_question_bank.count(),  # 跨所有考纲总题目数
        syllabus_count=0,
        api_providers={
            "deepseek": bool(settings.DEEPSEEK_API_KEY),
            "volc": bool(settings.VOLC_ACCESS_KEY or settings.VOLC_API_KEY),
            "xunfei": bool(settings.XUNFEI_APPID),
        },
    )


# ============================
# 图片上传
# ============================

@router.post("/upload-image")
async def upload_admin_image(
    file: UploadFile = File(...),
    current_admin: str = Depends(get_current_admin),
):
    """管理员上传图片到 Supabase Storage（用于公告等）"""
    # 校验类型
    allowed = {"image/png", "image/jpeg", "image/gif", "image/webp"}
    if file.content_type not in allowed:
        raise HTTPException(status_code=400, detail="仅支持 PNG / JPEG / GIF / WebP")

    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="图片大小不能超过 5MB")

    # 生成文件名
    ext = file.filename.split(".")[-1] if "." in (file.filename or "") else "png"
    filename = f"{uuid.uuid4().hex}.{ext}"
    storage_path = f"admin/{filename}"

    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": file.content_type,
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        res = await client.post(
            f"{settings.SUPABASE_URL}/storage/v1/object/admin-images/{storage_path}",
            headers=headers,
            content=contents,
        )
        if res.status_code not in (200, 201):
            raise HTTPException(status_code=500, detail=f"上传失败: {res.text[:200]}")

    public_url = f"{settings.SUPABASE_URL}/storage/v1/object/public/admin-images/{storage_path}"

    await write_audit_log(
        admin_id=current_admin,
        action="upload_image",
        target_type="image",
        target_id=filename,
        detail={"url": public_url},
    )

    return {"success": True, "url": public_url}
