"""
管理后台 API
所有接口（除公告公开查询外）均需管理员身份验证
"""
from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from pathlib import Path
import uuid
import httpx
import time
import logging
from urllib.parse import quote

from config import settings
from utils.admin_middleware import get_current_admin, get_current_super_admin, get_admin_headers, write_audit_log
from utils.sanctions import invalidate as invalidate_sanction_cache
from utils.notification import create_notification
import local_question_bank

logger = logging.getLogger("jizhi.admin")

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
    if res.status_code not in (200, 206):
        return [], 0
    data = res.json() if res.text else []
    content_range = res.headers.get("content-range", "")
    total = int(content_range.split("/")[-1]) if "/" in content_range else len(data)
    return data, total


# ⚠️ PostgREST 在「返回的是部分数据」时用 **206 Partial Content**。
#    只要总数超过一页（带 Prefer: count=exact + limit 的查询几乎总是如此），
#    响应就是 206 而不是 200 —— 只认 200 的检查会把**正常响应**当成故障。
#    实例：GET /admin/users 有 22 个用户、每页 20 → 第一页恒为 206
#          → 被判定为"上游失败"，接口 502；仪表盘 7 个计数同理全变 0。
#    下面这个判断凡是用在**读**请求上，都要用它而不是 `== 200`。
def _ok_read(res: httpx.Response) -> bool:
    """读请求是否成功（200 完整 / 206 部分，都算成功）"""
    return res.status_code in (200, 206)


def _fail_upstream(label: str, res: httpx.Response) -> None:
    """上游查询失败 → 明确报 502，**不要伪装成「没有数据」**。

    ⚠️ 这是本项目反复吃亏的一个模式：读端点把任何非 200 都降级成空列表 / 空分页，
       于是 401、403、42501（权限不足）、表不存在、网络故障在后台**一律表现为
       「暂无数据」**。故障和「业务上本来就是空」长得一模一样，所以永远查不出来。

    实例：2026-09-30 反馈 / Q&A / 举报 三个页面全空 —— 根因是 admin_tables.sql
    建表时漏了 GRANT 触发 42501，而这一层降级把它盖成了「没有数据」。
    """
    body = (res.text or "")[:300]
    logger.error(f"[admin] {label}查询失败 status={res.status_code} body={body}")
    raise HTTPException(status_code=502, detail=f"{label}查询失败（上游返回 {res.status_code}）")


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


async def _require_exists(table: str, row_id: str, label: str) -> None:
    """确认这一行存在，否则 404。

    ⚠️ 为什么必须先查：PostgREST 对 PATCH / DELETE 的响应**不区分
       「改了 1 行」和「匹配 0 行」**——两种都是 204。所以光看状态码，
       改/删一个不存在的 id 会一路走到"操作成功"。
       2026-09-30 用幽灵 UUID 逐个端点探测时实测到：
         PUT /admin/feedback/{不存在}     → 200「已处理」
         PUT /admin/qa/{不存在}           → 200「已处理」
         DELETE /admin/announcements/{不存在} → 200「公告已删除」
    """
    res = await _supabase_get(f"{table}?id=eq.{row_id}&select=id")
    if not _ok_read(res):
        _fail_upstream(f"{label}存在性检查", res)
    if not res.json():
        raise HTTPException(status_code=404, detail=f"{label}不存在")


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
    # 取不到的指标在这里留痕（key=指标名, value=原因）。
    # 之前这些统计全部 except: pass + 失败即 0，面板一片 0 和"业务上真的没有"
    # 长得一模一样 —— 有了这个字段，前端才能把"取不到"和"真的是 0"分开显示。
    errors: Dict[str, str] = {}


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
    status: str = "resolved"          # resolved | dismissed（兼容旧前端）
    # 处置动作：dismiss / warn / delete_content / mute / ban
    # 留空则按 status 推断（dismissed → dismiss，resolved → warn 之外的"仅标记"）
    action: str = ""
    admin_note: Optional[str] = None
    mute_days: int = 0                # action=mute：天数，0 或负数 = 永久
    mute_scope: str = "all"           # action=mute：all / post / comment


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
    # ⚠️「今日」必须按北京时间算。原先用 timezone.utc，
    #    导致「今日新增 / 今日答题」在北京时间早上 8 点重置，而不是零点。
    today_str = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d")

    errors: Dict[str, str] = {}

    async with httpx.AsyncClient(timeout=20.0) as client:
        headers = get_admin_headers()
        headers["Prefer"] = "count=exact"

        async def count(label: str, path: str, **params) -> int:
            """取一个 count=exact 计数。

            ⚠️ 原先是 7 个 try/except: pass —— 失败即 0，面板显示成一片 0，
               和「业务上真的没有」完全无法区分。现在失败会记日志 + 落进 errors，
               前端可以据此把「取不到」和「真的是 0」分开显示。
            """
            try:
                r = await client.get(
                    _supabase_url(path, select="*", limit="1", **params),
                    headers=headers,
                )
            except Exception as e:
                logger.error(f"[admin] 仪表盘·{label} 请求异常: {e}")
                errors[label] = f"请求异常: {e}"
                return 0
            if r.status_code not in (200, 206):
                logger.error(f"[admin] 仪表盘·{label} 查询失败 status={r.status_code} body={r.text[:200]}")
                errors[label] = f"上游 {r.status_code}"
                return 0
            return _safe_int_from_header(r)

        total_users          = await count("用户总数",     "profiles")
        today_new_users      = await count("今日新增用户", "profiles",         created_at=f"gte.{today_str}")
        total_questions_done = await count("总答题数",     "question_records")
        today_questions_done = await count("今日答题数",   "question_records", created_at=f"gte.{today_str}")
        pending_reports      = await count("待处理举报",   "content_reports",  status="eq.pending")
        pending_feedback     = await count("待处理反馈",   "user_feedback",    status="eq.pending")
        total_plans          = await count("总学习计划数", "subject_plans")

    return DashboardResponse(
        total_users=total_users,
        today_new_users=today_new_users,
        total_questions_done=total_questions_done,
        today_questions_done=today_questions_done,
        pending_reports=pending_reports,
        pending_feedback=pending_feedback,
        total_plans=total_plans,
        errors=errors,
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
        if res.status_code not in (200, 206):
            _fail_upstream("用户列表", res)

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
        if res.status_code not in (200, 206) or not res.json():
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

        # 4. 帖子数
        # ⚠️ posts 表的主人是 user_id，不是 author_id —— 原先写成 author_id，
        #    PostgREST 回 42703（列不存在），被下面的状态码判断吞掉，post_count 恒为 0。
        #    排查时别被"posts 表可能不存在"误导：表一直都在。
        post_count = 0
        try:
            r = await client.get(
                _supabase_url("posts", select="*", limit="1",
                              user_id=f"eq.{user_id}"),
                headers=headers,
            )
            if r.status_code in (200, 206):
                post_count = _safe_int_from_header(r)
            else:
                logger.warning(f"[admin] 查帖子数失败 status={r.status_code} body={r.text[:200]}")
        except Exception as e:
            logger.warning(f"[admin] 查帖子数异常: {e}")

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
        # ⚠️ role 之前漏传 → 详情接口永远回默认值 "user"，
        #    从列表进详情会看到角色"变了"（列表是传了的）。
        role=user.get("role") or "user",
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
    current_admin: str = Depends(get_current_super_admin),   # ← 原先误用 get_current_admin
):
    """设置/取消管理员（仅超级管理员可操作）

    ⚠️ 这里原先依赖的是 get_current_admin，而 docstring 写着「仅超级管理员」——
       结果是任何普通管理员都能给自己 is_admin=true 提权，也能把超管降级。
       get_current_super_admin 在本文件里此前只有 import、从未被调用，闸门形同虚设。
    """
    if user_id == current_admin and not body.is_admin:
        raise HTTPException(status_code=400, detail="不能取消自己的管理员权限")

    new_role = "admin" if body.is_admin else "user"
    res = await _supabase_patch(
        f"profiles?id=eq.{user_id}",
        {"role": new_role, "is_admin": body.is_admin},
    )
    if res.status_code not in (200, 204):
        raise HTTPException(status_code=500, detail=f"操作失败: {res.text[:200]}")

    # 回读校验：PostgREST 的 PATCH 对「0 行匹配」同样返回 204，
    # 不回读的话，改一个不存在的 user_id 也会报"已设为管理员"。
    chk = await _supabase_get(f"profiles?id=eq.{user_id}&select=role,is_admin")
    if chk.status_code not in (200, 206):
        raise HTTPException(status_code=502, detail=f"回读失败: {chk.text[:200]}")
    rows = chk.json()
    if not rows:
        raise HTTPException(status_code=404, detail="用户不存在")
    if (rows[0].get("role") or "") != new_role or bool(rows[0].get("is_admin")) != bool(body.is_admin):
        raise HTTPException(status_code=502, detail="角色更新未生效，请重试")

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
        if res.status_code not in (200, 206):
            _fail_upstream("举报列表", res)
        data = res.json() if res.text else []
        total = _safe_int_from_header(res)

    return PaginatedResponse(items=data, total=total, page=page, page_size=page_size)


# 永久禁言用一个"等于永久"的时间戳。
# 之所以不用 NULL：profiles.muted_until 的语义是「NULL 或已过期 = 未禁言」，
# NULL 表达不了"永久禁言"。（要更干净可以另加一个 muted_permanent 布尔列。）
_PERMA_UNTIL = "9999-12-31T23:59:59+00:00"


async def _resolve_target_author(target_type: str, target_id: str) -> Optional[str]:
    """反查被举报内容的作者。

    举报记录里没存 target_author_id 时（历史数据、或写入方升级前的行）走这里。
    """
    table = "posts" if target_type == "post" else "comments"
    try:
        r = await _supabase_get(f"{table}?id=eq.{target_id}&select=user_id")
        if r.status_code in (200, 206) and r.json():
            return r.json()[0].get("user_id")
    except Exception as e:
        logger.warning(f"[admin] 反查被举报内容作者失败: {e}")
    return None


async def _soft_delete_content(target_type: str, target_id: str) -> None:
    """软删被举报内容（posts / comments 都有 is_deleted 列）。"""
    table = "posts" if target_type == "post" else "comments"
    res = await _supabase_patch(f"{table}?id=eq.{target_id}", {"is_deleted": True})
    if res.status_code not in (200, 204):
        _fail_upstream("删除被举报内容", res)


async def _set_profile_state(user_id: str, data: dict, label: str) -> None:
    """改 profiles 上的处置快路径状态（muted_until / mute_scope / is_active）。

    ⚠️ 两个必须做的检查，缺一不可：
      ① PostgREST 的 PATCH 对「匹配 0 行」同样返回 204 —— 不回读的话，
         处罚一个不存在的用户也会报成功；
      ② profiles 表曾经只有 SELECT 权限（UPDATE 返回 42501），
         这条链一断，禁言/封禁全都静默失败。所以状态码要显式看。
    """
    res = await _supabase_patch(f"profiles?id=eq.{user_id}", data)
    if res.status_code not in (200, 204):
        _fail_upstream(label, res)

    cols = ",".join(data.keys())
    chk = await _supabase_get(f"profiles?id=eq.{user_id}&select={cols}")
    if chk.status_code not in (200, 206):
        _fail_upstream(f"{label}·回读", chk)
    rows = chk.json()
    if not rows:
        raise HTTPException(status_code=404, detail=f"用户不存在，{label}未生效")
    row = rows[0]
    for k, v in data.items():
        if str(row.get(k)) != str(v):
            raise HTTPException(status_code=502,
                                detail=f"{label}未生效（{k} 库中仍为 {row.get(k)}）")


async def _write_sanction(user_id: str, kind: str, *, scope: Optional[str] = None,
                          reason: str = "", report_id: Optional[str] = None,
                          admin_id: Optional[str] = None,
                          expires_at: Optional[str] = None) -> None:
    """写一条处置历史（user_sanctions）。

    注意：这里**只写历史**。真正生效的状态落在 profiles 上（见 utils/sanctions.py）。
    """
    body = {
        "user_id": user_id,
        "kind": kind,
        "scope": scope,
        "reason": reason or None,
        "report_id": report_id,
        "admin_id": admin_id,
        "expires_at": expires_at,
    }
    res = await _supabase_post("user_sanctions", body)
    # ⚠️ PostgREST 在插入被 RLS/GRANT 拦下时返回 **201 + 空数组**，
    #    只看状态码会以为成功。这里连 body 一起看（同 announcements 的教训）。
    if res.status_code not in (200, 201):
        logout = (res.text or "")[:200]
        logger.error(f"[admin] 写处置记录失败 status={res.status_code} body={logout}")
        raise HTTPException(status_code=502, detail=f"写处置记录失败: {logout}")
    try:
        created = res.json()
    except Exception:
        created = []
    if isinstance(created, list) and not created:
        raise HTTPException(status_code=502, detail="处置记录未写入（上游返回空）")


@router.put("/reports/{report_id}/resolve")
async def resolve_report(
    report_id: str,
    body: ResolveReport,
    current_admin: str = Depends(get_current_admin),
):
    """处理举报 —— 一步完成「判定 + 处置 + 留痕」。

    action 可选：
      dismiss         驳回，不处置
      warn            警告（记处置历史 + 站内信，不限制行为）
      delete_content  删除被举报内容（posts/comments 软删 is_deleted=true）
      mute            禁言 N 天（mute_days<=0 表示永久），范围 mute_scope
      ban             封禁账号（认证中间件会直接拒绝该用户的一切请求）

    ⚠️ 此前这个端点**只改举报记录自己的状态**，对被举报人零动作 ——
       管理员审核完想处罚，得自己记下 user_id、切到用户管理页、搜人、再点封禁，
       而那个封禁还是个没人校验的布尔。整条处置闭环在接口层是断的。
    """
    # 兼容旧前端：不传 action 时按 status 推断
    action = (body.action or "").strip() or ("dismiss" if body.status == "dismissed" else "mark")
    if action not in ("dismiss", "warn", "delete_content", "mute", "ban", "mark"):
        raise HTTPException(status_code=400,
                            detail="action 应为 dismiss/warn/delete_content/mute/ban")

    rep = await _supabase_get(f"content_reports?id=eq.{report_id}&select=*")
    if rep.status_code not in (200, 206):
        _fail_upstream("举报记录", rep)
    rows = rep.json()
    if not rows:
        raise HTTPException(status_code=404, detail="举报不存在")
    report = rows[0]

    target_type = report.get("target_type") or "post"
    target_id = report.get("target_id")
    author_id = report.get("target_author_id") or await _resolve_target_author(target_type, target_id)

    needs_author = action in ("warn", "mute", "ban")
    if needs_author and not author_id:
        raise HTTPException(status_code=422,
                            detail="这条举报查不到被举报人（历史数据缺 target_author_id，且内容已不可达），"
                                   "无法执行处罚；可改用 dismiss 或 delete_content")

    now = datetime.now(timezone.utc)
    expires_at = None
    sanction_kind = None

    # ── 执行处置 ──
    if action == "dismiss":
        new_status = "dismissed"

    elif action == "mark":                       # 仅标记已处理，不处罚（旧行为）
        new_status = "resolved"

    elif action == "warn":
        sanction_kind = "warn"
        new_status = "resolved"
        await _write_sanction(author_id, "warn", reason=body.admin_note or "举报成立",
                              report_id=report_id, admin_id=current_admin)
        try:
            await create_notification(
                user_id=author_id, notif_type="system",
                title="你收到一条社区警告",
                content=body.admin_note or "你发布的内容被举报并经管理员核实，请注意社区规范。",
                source_id=report_id,
            )
        except Exception as e:
            logger.warning(f"[admin] 警告通知发送失败（不影响处置）: {e}")

    elif action == "delete_content":
        sanction_kind = "warn"                   # 删内容也留一条历史
        new_status = "resolved"
        await _soft_delete_content(target_type, target_id)
        if author_id:
            await _write_sanction(author_id, "warn",
                                  reason=body.admin_note or "内容违规被删除",
                                  report_id=report_id, admin_id=current_admin)

    elif action == "mute":
        scope = body.mute_scope if body.mute_scope in ("all", "post", "comment") else "all"
        expires_at = _PERMA_UNTIL if body.mute_days <= 0 else \
            (now + timedelta(days=body.mute_days)).isoformat()
        sanction_kind = "mute"
        new_status = "resolved"
        # ⚠️ 顺序：**先落状态，再写历史**。
        #    反过来的话，状态写失败时会在 user_sanctions 里留下一条
        #    "声称已禁言、其实没生效"的孤儿记录（实测踩到过）。
        await _set_profile_state(author_id, {"muted_until": expires_at, "mute_scope": scope},
                                 "禁言状态写入")
        invalidate_sanction_cache(author_id)
        await _write_sanction(author_id, "mute", scope=scope,
                              reason=body.admin_note or "举报成立",
                              report_id=report_id, admin_id=current_admin,
                              expires_at=expires_at)

    elif action == "ban":
        sanction_kind = "ban"
        new_status = "resolved"
        await _set_profile_state(author_id, {"is_active": False}, "封禁状态写入")
        invalidate_sanction_cache(author_id)
        await _write_sanction(author_id, "ban", scope="all",
                              reason=body.admin_note or "举报成立",
                              report_id=report_id, admin_id=current_admin)

    else:                                        # 理论上不可达
        raise HTTPException(status_code=400, detail=f"未知动作 {action}")

    # ── 回写举报记录 ──
    update_data: dict = {
        "status": new_status,
        "admin_id": current_admin,
        "resolved_at": now.isoformat(),
        "action_taken": action,
    }
    if body.admin_note:
        update_data["admin_note"] = body.admin_note

    res = await _supabase_patch(f"content_reports?id=eq.{report_id}", update_data)
    if res.status_code not in (200, 204):
        _fail_upstream("举报记录回写", res)

    # ── 回读校验：PostgREST 的 PATCH 对「匹配 0 行」也返回 204 ──
    chk = await _supabase_get(f"content_reports?id=eq.{report_id}&select=status,action_taken")
    if chk.status_code in (200, 206) and chk.json():
        got = chk.json()[0]
        if got.get("status") != new_status:
            raise HTTPException(status_code=502,
                                detail=f"举报状态未生效（库中仍为 {got.get('status')}）")

    await write_audit_log(
        admin_id=current_admin,
        action=f"resolve_report_{new_status}",
        target_type="report",
        target_id=report_id,
        detail={"action": action, "status": new_status,
                "target_type": target_type, "target_id": str(target_id or ""),
                "author_id": str(author_id or ""),
                "mute_scope": body.mute_scope if action == "mute" else None,
                "mute_until": expires_at,
                "sanction": sanction_kind,
                "admin_note": body.admin_note or ""},
    )

    return {"success": True, "action": action, "status": new_status,
            "message": {
                "dismiss": "已驳回", "mark": "已标记处理", "warn": "已警告并通知对方",
                "delete_content": "已删除被举报内容", "mute": "已禁言", "ban": "已封禁",
            }.get(action, "已处理")}


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
        if res.status_code not in (200, 206):
            _fail_upstream("反馈列表", res)
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
    await _require_exists("user_feedback", feedback_id, "反馈")
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
        if res.status_code not in (200, 206):
            _fail_upstream("Q&A 列表", res)
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
    await _require_exists("user_qa", qa_id, "Q&A")
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

    # ⚠️ 必须校验，否则空 body 会**在题库里留下一道全 null 的题**。
    #    原先用 model_dump(exclude_unset=False)，把 content/answer/analysis/kp_name
    #    四个默认 None 的字段原样写进 JSON —— 2026-09-30 用空 body 探测时
    #    当场造出一道 {"content":null,"answer":null,...} 的脏题（已清理）。
    #    而且它是 /admin/questions?search= 崩溃的源头（_get_stem 撞上 content=null）。
    content = body.content if isinstance(body.content, dict) else {}
    stem = (content.get("stem") or "").strip()
    if not stem:
        raise HTTPException(status_code=400, detail="题干（content.stem）不能为空")
    if body.answer is None or (isinstance(body.answer, str) and not body.answer.strip()):
        raise HTTPException(status_code=400, detail="答案（answer）不能为空")

    # exclude_unset=True：只写调用方**真的传了**的字段，
    # 没传的不要以 null 落库 —— 那正是上面那道脏题的成因。
    new_q = body.model_dump(exclude_unset=True)
    new_q["content"] = content
    if not new_q.get("id"):
        new_q["id"] = str(uuid.uuid4())
    if not new_q.get("difficulty"):
        new_q["difficulty"] = 3

    local_question_bank.add_questions(syllabus_id, [new_q])

    # 回读：add_questions 在 syllabi.json 缺失 / 没匹配到考纲时会**静默跳过落盘**
    # （只改内存），那样接口报"已创建"、重启即丢。
    if not local_question_bank.find_question_global(new_q["id"]):
        raise HTTPException(status_code=502, detail="题目未写入题库，请检查题库文件权限与考纲配置")

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
        if res.status_code not in (200, 206):
            _fail_upstream("公告列表", res)
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
        if res.status_code not in (200, 206):
            _fail_upstream("公开公告列表", res)
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
    await _require_exists("system_announcements", announcement_id, "公告")
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
        if res.status_code not in (200, 206):
            _fail_upstream("审计日志", res)
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
        # 原先硬编码 0，永远返回 0（实际有 17 个考纲）。改成真实统计。
        syllabus_count=len(local_question_bank.all_banks()),
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
