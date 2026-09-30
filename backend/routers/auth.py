from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Header, Depends, Request
from pydantic import BaseModel
from typing import Optional
from config import settings
import httpx
import time
import uuid
import random
from PIL import Image
import io
from utils.email import send_verification_code_email
from utils.auth_middleware import get_current_user, verify_user_match
from services.supabase import get_supabase_headers, get_supabase_service_headers
from utils.rate_limit import check_rate_limit
from logging_config import logger

router = APIRouter(prefix="/auth", tags=["认证"])

# 微信不提供邮箱，而建号必须有个唯一登录标识 —— 用这个保留域做占位。
# .local 是 RFC 6762 保留 TLD，永远不可投递；用户之后可在设置页补真实邮箱+密码。
WECHAT_PLACEHOLDER_DOMAIN = "miniapp.local"


class LoginRequest(BaseModel):
    login_input: str
    password: str


@router.post("/login")
async def login(req: LoginRequest, request: Request):
    # ✅ 速率限制：同一账号 60秒内最多5次尝试
    client_ip = request.client.host if request.client else "unknown"
    check_rate_limit(f"login:{client_ip}:{req.login_input}", max_requests=5, window_seconds=60,
                     error_message="登录尝试过于频繁，请60秒后重试")
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

    if "@" in req.login_input:
        email = req.login_input
        url = f"{settings.SUPABASE_URL}/auth/v1/token?grant_type=password"
        data = {"email": email, "password": req.password}
    else:
        search_url = f"{settings.SUPABASE_URL}/rest/v1/profiles?user_account=eq.{req.login_input}"
        async with httpx.AsyncClient() as client:
            search_res = await client.get(search_url, headers=headers)
            if search_res.status_code != 200 or not search_res.json():
                raise HTTPException(status_code=401, detail="账号不存在")
            email = search_res.json()[0].get("email")
            if not email:
                raise HTTPException(status_code=401, detail="账号未绑定邮箱")
        url = f"{settings.SUPABASE_URL}/auth/v1/token?grant_type=password"
        data = {"email": email, "password": req.password}

    async with httpx.AsyncClient() as client:
        res = await client.post(url, headers=headers, json=data)

        if res.status_code != 200:
            error_msg = res.text
            if "Invalid login credentials" in error_msg:
                raise HTTPException(status_code=401, detail="账号或密码错误")
            if "Email not confirmed" in error_msg:
                raise HTTPException(status_code=401, detail="邮箱尚未验证")
            raise HTTPException(status_code=401, detail="登录失败")

        user_data = res.json()
        user = user_data.get("user", {})
        user_id = user.get("id")
        access_token = user_data.get("access_token")

        profile_url = f"{settings.SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}"
        profile_res = await client.get(profile_url, headers=headers)

        user_account = None
        nickname = None
        avatar_url = None
        bio = None
        learning_stage = None
        grade = None
        major = None
        learning_goal = None
        difficulty_preference = None
        learning_style = None
        daily_study_time = None

        if profile_res.status_code == 200 and profile_res.json():
            profile = profile_res.json()[0]
            user_account = profile.get("user_account")
            nickname = profile.get("nickname")
            avatar_url = profile.get("avatar_url")
            bio = profile.get("bio")
            learning_stage = profile.get("learning_stage")
            grade = profile.get("grade")
            major = profile.get("major")
            learning_goal = profile.get("learning_goal")
            difficulty_preference = profile.get("difficulty_preference")
            learning_style = profile.get("learning_style")
            daily_study_time = profile.get("daily_study_time")
            is_admin = profile.get("is_admin", False)
            role = profile.get("role", "user")

        return {
            "id": user_id,
            "email": email,
            "access_token": access_token,
            "user_account": user_account,
            "nickname": nickname,
            "avatar_url": avatar_url,
            "bio": bio,
            "learning_stage": learning_stage,
            "grade": grade,
            "major": major,
            "learning_goal": learning_goal,
            "difficulty_preference": difficulty_preference,
            "learning_style": learning_style,
            "daily_study_time": daily_study_time,
            "is_admin": is_admin,
            "role": role
        }


# ============================================================
# ✅ 新增：发送验证码接口
# ============================================================
@router.post("/send-code")
async def send_verification_code(email: str, request: Request):
    """发送邮箱验证码"""
    # ✅ 速率限制：同一 IP + 邮箱 60秒内最多1次
    client_ip = request.client.host if request.client else "unknown"
    check_rate_limit(f"send_code:{client_ip}:{email}", max_requests=1, window_seconds=60,
                     error_message="验证码已发送，请60秒后重试")
    # 生成6位数字验证码
    code = ''.join(random.choices('0123456789', k=6))

    # ✅ 用 Service Role Key（更高权限）
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        # 删除该邮箱之前的旧验证码
        delete_url = f"{settings.SUPABASE_URL}/rest/v1/email_verification_codes?email=eq.{email}"
        delete_res = await client.delete(delete_url, headers=headers)
        logger.info(f"删除旧验证码: {delete_res.status_code}")

        # 插入新验证码
        insert_data = {
            "email": email,
            "code": code,
            "expires_at": int(time.time()) + 600
        }
        insert_url = f"{settings.SUPABASE_URL}/rest/v1/email_verification_codes"
        insert_res = await client.post(insert_url, headers=headers, json=insert_data)
        logger.info(f"插入验证码状态: {insert_res.status_code}")
        logger.info(f"插入验证码响应: {insert_res.text}")

        if insert_res.status_code not in [200, 201]:
            raise HTTPException(status_code=500, detail=f"保存验证码失败: {insert_res.text}")

    # 发送邮件
    success = send_verification_code_email(email, code)
    if not success:
        raise HTTPException(status_code=500, detail="邮件发送失败，请检查邮箱地址")

    return {"success": True, "message": "验证码已发送"}


# ============================================================
# ✅ 修改：注册接口（新增 code 字段验证）
# ============================================================
class RegisterRequest(BaseModel):
    email: str
    password: str
    code: str  # ✅ 新增验证码字段
    nickname: str = None


@router.post("/register")
async def register(req: RegisterRequest, request: Request):
    # ✅ 速率限制：同一 IP 60秒内最多3次注册
    client_ip = request.client.host if request.client else "unknown"
    check_rate_limit(f"register:{client_ip}", max_requests=3, window_seconds=60,
                     error_message="注册请求过于频繁，请60秒后重试")
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

    # ===== 1. 验证验证码 =====
    async with httpx.AsyncClient() as client:
        query_url = f"{settings.SUPABASE_URL}/rest/v1/email_verification_codes?email=eq.{req.email}&order=created_at.desc&limit=1"
        res = await client.get(query_url, headers=headers)

        if res.status_code != 200 or not res.json():
            raise HTTPException(status_code=400, detail="请先获取验证码")

        record = res.json()[0]

        # 检查验证码是否正确
        if record.get("code") != req.code:
            raise HTTPException(status_code=400, detail="验证码错误")

        # 检查是否过期
        expires_at = record.get("expires_at")
        if expires_at and time.time() > expires_at:
            raise HTTPException(status_code=400, detail="验证码已过期，请重新获取")

        # 检查是否已使用
        if record.get("used", False):
            raise HTTPException(status_code=400, detail="验证码已使用，请重新获取")

    # ===== 2. 创建 Supabase 用户 =====
    signup_url = f"{settings.SUPABASE_URL}/auth/v1/signup"
    data = {"email": req.email, "password": req.password}

    async with httpx.AsyncClient() as client:
        res = await client.post(signup_url, headers=headers, json=data, timeout=30)

        if res.status_code != 200:
            error_msg = res.text
            if "already registered" in error_msg.lower() or "user already" in error_msg.lower():
                raise HTTPException(status_code=400, detail="该邮箱已注册")
            raise HTTPException(status_code=400, detail=f"注册失败: {error_msg}")

        user_data = res.json()
        user_id = user_data.get("id")
        if not user_id:
            user_id = user_data.get("user", {}).get("id")

        # ===== 2.5 自动确认邮箱 =====
        # 站点有自己的邮箱验证码流程，Supabase 默认的 Confirm email 是多余的；
        # 不确认的话新注册用户登录时 grant_type=password 会报 "Email not confirmed" → 401
        if settings.SUPABASE_SERVICE_ROLE_KEY:
            try:
                admin_headers = {
                    "apikey": settings.SUPABASE_KEY,
                    "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
                    "Content-Type": "application/json"
                }
                confirm_res = await client.put(
                    f"{settings.SUPABASE_URL}/auth/v1/admin/users/{user_id}",
                    headers=admin_headers,
                    json={"email_confirm": True},
                    timeout=15
                )
                logger.info(f"自动确认邮箱状态: {confirm_res.status_code}")
                if confirm_res.status_code != 200:
                    logger.warning(f"自动确认邮箱失败: {confirm_res.text}")
            except Exception as e:
                logger.warning(f"自动确认邮箱异常: {e}")

        # ===== 3. 创建 profile =====
        user_account = str(random.randint(10000000, 99999999))

        profile_url = f"{settings.SUPABASE_URL}/rest/v1/profiles"
        profile_data = {
            "id": user_id,
            "email": req.email,
            "nickname": req.nickname or req.email.split("@")[0],
            "user_account": user_account
        }
        profile_res = await client.post(profile_url, headers=headers, json=profile_data, timeout=30)

        if profile_res.status_code not in [200, 201]:
            raise HTTPException(status_code=400, detail="创建用户资料失败")

        # ===== 4. 标记验证码已使用 =====
        update_url = f"{settings.SUPABASE_URL}/rest/v1/email_verification_codes?id=eq.{record['id']}"
        await client.patch(update_url, headers=headers, json={"used": True})

        return {
            "success": True,
            "id": user_id,
            "email": req.email,
            "user_account": user_account,
            "message": "注册成功"
        }


@router.get("/profile/{user_id}")
async def get_profile(user_id: str):
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

    profile_url = f"{settings.SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}"

    async with httpx.AsyncClient() as client:
        res = await client.get(profile_url, headers=headers)

        if res.status_code != 200 or not res.json():
            raise HTTPException(status_code=404, detail="用户不存在")

        profile = res.json()[0]
        return {
            "id": profile.get("id"),
            "email": profile.get("email"),
            "nickname": profile.get("nickname"),
            "user_account": profile.get("user_account"),
            "avatar_url": profile.get("avatar_url"),
            "bio": profile.get("bio"),
            "learning_stage": profile.get("learning_stage"),
            "grade": profile.get("grade"),
            "major": profile.get("major")
        }


class UpdateNicknameRequest(BaseModel):
    user_id: str
    nickname: str


@router.put("/update-nickname")
async def update_nickname(req: UpdateNicknameRequest, current_user: str = Depends(get_current_user)):
    verify_user_match(req.user_id, current_user)
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

    url = f"{settings.SUPABASE_URL}/rest/v1/profiles?id=eq.{req.user_id}"
    data = {"nickname": req.nickname}

    async with httpx.AsyncClient() as client:
        res = await client.patch(url, headers=headers, json=data, timeout=30)

        if res.status_code not in [200, 204]:
            raise HTTPException(status_code=400, detail="更新昵称失败")

        return {"success": True, "nickname": req.nickname}


class UpdateBioRequest(BaseModel):
    user_id: str
    bio: str


@router.put("/update-bio")
async def update_bio(req: UpdateBioRequest, current_user: str = Depends(get_current_user)):
    verify_user_match(req.user_id, current_user)
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

    url = f"{settings.SUPABASE_URL}/rest/v1/profiles?id=eq.{req.user_id}"
    data = {"bio": req.bio}

    async with httpx.AsyncClient() as client:
        res = await client.patch(url, headers=headers, json=data, timeout=30)

        if res.status_code not in [200, 204]:
            raise HTTPException(status_code=400, detail="更新简介失败")

        return {"success": True, "bio": req.bio}


class UpdateLearningInfoRequest(BaseModel):
    user_id: str
    learning_stage: str = ""
    grade: str = ""
    major: str = ""
    learning_goal: str = ""
    difficulty_preference: str = ""
    learning_style: str = ""
    daily_study_time: str = ""


@router.put("/update-learning-info")
async def update_learning_info(req: UpdateLearningInfoRequest, current_user: str = Depends(get_current_user)):
    verify_user_match(req.user_id, current_user)
    """更新学习信息（学习阶段、年级、专业/方向 + 学习偏好）"""
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

    url = f"{settings.SUPABASE_URL}/rest/v1/profiles?id=eq.{req.user_id}"
    data = {k: v for k, v in req.dict().items() if k != "user_id" and v != ""}

    async with httpx.AsyncClient() as client:
        res = await client.patch(url, headers=headers, json=data, timeout=30)

        if res.status_code not in [200, 204]:
            raise HTTPException(status_code=400, detail="更新学习信息失败")

        return {
            "success": True,
            "learning_stage": req.learning_stage,
            "grade": req.grade,
            "major": req.major
        }


@router.post("/upload-avatar/{user_id}")
async def upload_avatar(user_id: str, file: UploadFile = File(...), current_user: str = Depends(get_current_user)):
    verify_user_match(user_id, current_user)
    contents = await file.read()
    img = Image.open(io.BytesIO(contents))
    img = img.resize((200, 200))

    img_bytes_io = io.BytesIO()
    img.save(img_bytes_io, format='PNG')
    compressed_bytes = img_bytes_io.getvalue()

    timestamp = str(int(time.time()))
    file_path = f"{user_id}/{timestamp}.png"

    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "image/png"
    }

    storage_url = f"{settings.SUPABASE_URL}/storage/v1/object/avatars/{file_path}"

    async with httpx.AsyncClient() as client:
        res = await client.post(storage_url, headers=headers, content=compressed_bytes)

        if res.status_code not in [200, 201]:
            raise HTTPException(status_code=400, detail="上传失败")

        public_url = f"{settings.SUPABASE_URL}/storage/v1/object/public/avatars/{file_path}"

        profile_url = f"{settings.SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}"
        profile_headers = {
            "apikey": settings.SUPABASE_KEY,
            "Authorization": f"Bearer {settings.SUPABASE_KEY}",
            "Content-Type": "application/json"
        }
        profile_res = await client.patch(
            profile_url,
            headers=profile_headers,
            json={"avatar_url": public_url}
        )

        if profile_res.status_code not in [200, 204]:
            raise HTTPException(status_code=400, detail="保存头像URL失败")

        return {"success": True, "avatar_url": public_url}


@router.put("/status")
async def update_status(user_id: str = Query(...), status: str = Query(...), current_user: str = Depends(get_current_user)):
    verify_user_match(user_id, current_user)
    # 标准 anon headers：profiles 表未授予 service_role UPDATE 权限，用 service_role 会被 403
    headers = get_supabase_headers()

    valid_status = ["online", "offline", "invisible"]
    if status not in valid_status:
        raise HTTPException(status_code=400, detail="无效的状态")

    url = f"{settings.SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}"
    async with httpx.AsyncClient() as client:
        res = await client.patch(url, headers=headers, json={"status": status})
        if res.status_code not in [200, 204]:
            raise HTTPException(status_code=400, detail="更新状态失败")
        return {"success": True, "status": status}


@router.post("/logout")
async def logout():
    return {"success": True}


class UpdatePasswordRequest(BaseModel):
    old_password: str
    new_password: str


@router.put("/update-password")
async def update_password(
    req: UpdatePasswordRequest,
    user_id: str = Query(...),
    authorization: str = Header(...),  # ✅ 接收用户的 token
    current_user: str = Depends(get_current_user)
):
    """修改密码"""
    verify_user_match(user_id, current_user)
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

    profile_url = f"{settings.SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}"
    async with httpx.AsyncClient() as client:
        profile_res = await client.get(profile_url, headers=headers)
        if profile_res.status_code != 200 or not profile_res.json():
            raise HTTPException(status_code=404, detail="用户不存在")
        email = profile_res.json()[0].get("email")

        # 验证旧密码
        verify_url = f"{settings.SUPABASE_URL}/auth/v1/token?grant_type=password"
        verify_data = {"email": email, "password": req.old_password}
        verify_res = await client.post(verify_url, headers=headers, json=verify_data)
        if verify_res.status_code != 200:
            raise HTTPException(status_code=401, detail="当前密码错误")

        # ✅ 修改密码：用用户自己的 token
        update_headers = {
            "apikey": settings.SUPABASE_KEY,
            "Authorization": authorization,  # ← 用前端传过来的用户 token
            "Content-Type": "application/json"
        }
        update_data = {"password": req.new_password}
        update_res = await client.put(
            f"{settings.SUPABASE_URL}/auth/v1/user",
            headers=update_headers,
            json=update_data
        )

        if update_res.status_code != 200:
            raise HTTPException(status_code=400, detail="修改密码失败")

        return {"success": True, "message": "密码修改成功"}


class SetCredentialsRequest(BaseModel):
    email: str
    code: str
    password: str


@router.post("/set-credentials")
async def set_credentials(
    req: SetCredentialsRequest,
    user_id: str = Query(...),
    current_user: str = Depends(get_current_user)
):
    """给「微信一键登录」建的账号补上真实邮箱和密码。

    微信建的号只有一个占位邮箱（wx_*@miniapp.local）和一个没人知道的随机密码，
    用户在网页端/桌面端/手机端够不着它。补上邮箱+密码后，同一个账号到处都能登。

    这是**替代「账号合并」**的做法：不迁移任何数据，只是给账号补一把能用的钥匙。
    所以不存在「两个账号合一个」那种要改 user_id 的工程。

    只对占位邮箱的账号开放；已有真实邮箱的账号要改邮箱是另一件事（未做）。
    """
    verify_user_match(user_id, current_user)

    if not settings.SUPABASE_SERVICE_ROLE_KEY:
        logger.error("❌ 未配置 SUPABASE_SERVICE_ROLE_KEY，无法设置邮箱密码")
        raise HTTPException(status_code=500,
                            detail="服务端未配置 SUPABASE_SERVICE_ROLE_KEY，该功能不可用")

    email = (req.email or "").strip().lower()
    if "@" not in email or email.startswith("@") or email.endswith("@"):
        raise HTTPException(status_code=400, detail="邮箱格式不正确")
    if len(req.password or "") < 6:
        raise HTTPException(status_code=400, detail="密码至少 6 位")

    svc_headers = get_supabase_service_headers()

    async with httpx.AsyncClient(timeout=30.0) as client:
        # ── 1. 确认这是微信建的号 ──
        profile_res = await client.get(
            f"{settings.SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}&select=id,email",
            headers=svc_headers)
        rows = profile_res.json() if profile_res.status_code == 200 else []
        if not rows:
            raise HTTPException(status_code=404, detail="用户不存在")
        current_email = (rows[0].get("email") or "").lower()
        if not current_email.endswith("@" + WECHAT_PLACEHOLDER_DOMAIN):
            raise HTTPException(status_code=400,
                                detail="该账号已有邮箱和密码，如需修改密码请用「修改密码」")

        # ── 2. 新邮箱不能已被别人占用 ──
        taken_res = await client.get(
            f"{settings.SUPABASE_URL}/rest/v1/profiles?email=eq.{email}&select=id&limit=1",
            headers=svc_headers)
        if taken_res.status_code == 200 and taken_res.json():
            raise HTTPException(status_code=400, detail="该邮箱已被其他账号使用")

        # ── 3. 校验邮箱验证码（与 /register 同一张表、同一套规则）──
        code_res = await client.get(
            f"{settings.SUPABASE_URL}/rest/v1/email_verification_codes"
            f"?email=eq.{email}&order=created_at.desc&limit=1",
            headers=svc_headers)
        if code_res.status_code != 200 or not code_res.json():
            raise HTTPException(status_code=400, detail="请先获取验证码")
        record = code_res.json()[0]
        if record.get("code") != req.code:
            raise HTTPException(status_code=400, detail="验证码错误")
        expires_at = record.get("expires_at")
        if expires_at and time.time() > expires_at:
            raise HTTPException(status_code=400, detail="验证码已过期，请重新获取")
        if record.get("used", False):
            raise HTTPException(status_code=400, detail="验证码已使用，请重新获取")

        # ── 4. 写 auth 用户（这一步才是真正让「邮箱登录」生效的）──
        upd_res = await client.put(
            f"{settings.SUPABASE_URL}/auth/v1/admin/users/{user_id}",
            headers=svc_headers,
            json={"email": email, "password": req.password, "email_confirm": True})
        if upd_res.status_code not in [200, 201]:
            logger.error(f"❌ 设置邮箱密码失败({upd_res.status_code}): {upd_res.text}")
            if "already" in (upd_res.text or "").lower():
                raise HTTPException(status_code=400, detail="该邮箱已被其他账号使用")
            raise HTTPException(status_code=502, detail="设置失败，请稍后重试")

        # ── 5. 同步 profiles.email ──
        # 注意顺序：auth 先写、profiles 后写。若这步失败，profiles.email 仍是占位值，
        # 第 1 步的闸门就还开着、验证码也还没标记已用 —— 用户原地重试即可，不会卡死。
        patch_res = await client.patch(
            f"{settings.SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}",
            headers=svc_headers, json={"email": email})
        if patch_res.status_code not in [200, 204]:
            logger.error(f"❌ 同步 profiles.email 失败({patch_res.status_code}): {patch_res.text}")
            raise HTTPException(status_code=502, detail="设置失败，请稍后重试")

        # 回读：RLS 拦住的 UPDATE 是「静默 0 行 + 204」，只有回读能发现（09-27 的教训）
        check_res = await client.get(
            f"{settings.SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}&select=email",
            headers=svc_headers)
        crows = check_res.json() if check_res.status_code == 200 else []
        stored = (crows[0].get("email") or "").lower() if crows else None
        if stored != email:
            logger.error(f"❌ 邮箱回读校验失败: 期望 {email}，库里 {stored}")
            raise HTTPException(status_code=502, detail="设置失败，请稍后重试")

        # ── 6. 验证码标记已用 ──
        await client.patch(
            f"{settings.SUPABASE_URL}/rest/v1/email_verification_codes?id=eq.{record['id']}",
            headers=svc_headers, json={"used": True})

    logger.info(f"✅ 用户 {user_id} 补设邮箱密码: {email}")
    return {"success": True, "email": email,
            "message": "设置成功，现在可以用这个邮箱在网页端/桌面端/手机端登录了"}


@router.get("/account-status")
async def account_status(
    user_id: str = Query(...),
    current_user: str = Depends(get_current_user)
):
    """账号登录凭据状态 —— 让客户端知道该显示「修改密码」还是「设置邮箱和密码」。

    微信一键登录建的号：占位邮箱 + 一个没人知道的随机密码。这种账号在「修改密码」
    表单里必然卡死（第一步就要输当前密码，而用户根本不知道）。所以要先问清楚。
    """
    verify_user_match(user_id, current_user)

    async with httpx.AsyncClient(timeout=10.0) as client:
        res = await client.get(
            f"{settings.SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}&select=email",
            headers=get_supabase_service_headers())
        rows = res.json() if res.status_code == 200 else []
        if not rows:
            raise HTTPException(status_code=404, detail="用户不存在")
        email = (rows[0].get("email") or "").strip().lower()

    # 邮箱为空或还是占位域 —— 都算「没有可用凭据」
    has_credentials = bool(email) and not email.endswith("@" + WECHAT_PLACEHOLDER_DOMAIN)
    return {
        "email_set": has_credentials,
        "email": email if has_credentials else None,
        "can_change_password": has_credentials,
    }


# ============================================================
# JWT 签发
# ============================================================
import secrets
import jwt as pyjwt
from datetime import datetime, timedelta

# 内存临时存储（生产环境应换 Redis）
_temp_user_store: dict[str, dict] = {}            # user_id → user info（Supabase 不可用时）


def _gen_jwt(user_id: str, extra: dict = None) -> str:
    """生成自签 JWT（不依赖 Supabase）"""
    now = datetime.utcnow()
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + timedelta(hours=settings.JWT_EXPIRE_HOURS),
    }
    if extra:
        payload.update(extra)
    return pyjwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


# ── 微信首次登录：直接建号 ──
async def _delete_auth_user(client: httpx.AsyncClient, svc_headers: dict, user_id: str) -> None:
    """回滚：删掉刚建的 auth 用户。尽力而为，失败只留痕——留着孤儿账号也比抛错强。"""
    try:
        r = await client.delete(
            f"{settings.SUPABASE_URL}/auth/v1/admin/users/{user_id}", headers=svc_headers)
        if r.status_code not in [200, 204]:
            logger.warning(f"回滚删除 auth 用户失败({r.status_code}): {r.text}")
    except Exception as e:
        logger.warning(f"回滚删除 auth 用户异常: {e}")


async def _pick_user_account(client: httpx.AsyncClient, svc_headers: dict) -> str:
    """生成一个没被占用的 8 位数字账号。

    profiles.user_account 目前没有 UNIQUE 约束（/auth/register 也不查重），
    而 /auth/login 按用户名登录时取的是 `[0]`——真撞了会登进别人的号。
    这里先做一层应用侧查重兜住常见情况。
    """
    for _ in range(5):
        candidate = str(random.randint(10000000, 99999999))
        r = await client.get(
            f"{settings.SUPABASE_URL}/rest/v1/profiles?user_account=eq.{candidate}&select=id&limit=1",
            headers=svc_headers)
        if r.status_code == 200 and not r.json():
            return candidate
        if r.status_code != 200:
            logger.warning(f"账号查重失败({r.status_code})，改用更大取值范围")
            break
    return str(random.randint(100000000, 999999999))


async def _create_wechat_account(openid: str, unionid: str) -> tuple[str, str, str]:
    """给首次登录的微信用户建一个基智账号，返回 (user_id, nickname, user_account)。

    微信不提供邮箱，而建号又必须有个唯一登录标识，所以用一个占位邮箱。
    占位域用 .local（RFC 6762 保留 TLD，永远不可投递）——用户之后可以在设置页
    补真实邮箱+密码（见 /auth/set-credentials），补完就能在网页/桌面/手机端登录同一个号。
    """
    if not settings.SUPABASE_SERVICE_ROLE_KEY:
        # 没 service_role 就建不了号。这时必须报错：
        # 静默降级会让用户以为登录成功，实际什么都没建。
        logger.error("❌ 未配置 SUPABASE_SERVICE_ROLE_KEY，无法为微信新用户建号")
        raise HTTPException(status_code=500,
                            detail="服务端未配置 SUPABASE_SERVICE_ROLE_KEY，微信登录不可用")

    svc_headers = get_supabase_service_headers()
    nickname = f"微信用户{openid[-6:]}"
    placeholder_email = f"wx_{openid}@{WECHAT_PLACEHOLDER_DOMAIN}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        # ── 1. 建 auth 用户 ──
        create_res = await client.post(
            f"{settings.SUPABASE_URL}/auth/v1/admin/users",
            headers=svc_headers,
            json={
                "email": placeholder_email,
                "password": secrets.token_urlsafe(32),  # 随机密码：没人知道，也登不了
                "email_confirm": True,                  # 占位邮箱收不到确认信，必须直接确认
            })
        if create_res.status_code not in [200, 201]:
            logger.error(f"❌ 微信建号失败({create_res.status_code}): {create_res.text}")
            raise HTTPException(status_code=502, detail="创建账号失败，请稍后重试")

        user_id = (create_res.json() or {}).get("id")
        if not user_id:
            logger.error(f"❌ 微信建号未返回 id: {create_res.text}")
            raise HTTPException(status_code=502, detail="创建账号失败，请稍后重试")

        # ── 2. 建 profile ──
        user_account = await _pick_user_account(client, svc_headers)
        profile_res = await client.post(
            f"{settings.SUPABASE_URL}/rest/v1/profiles",
            headers=svc_headers,
            json={
                "id": user_id,
                "email": placeholder_email,
                "nickname": nickname,
                "user_account": user_account,
                "wechat_openid": openid,
                "wechat_unionid": unionid or "",
            })
        if profile_res.status_code not in [200, 201]:
            # profile 写不进去 = openid 没落库 = 下次登录会再建一个新号。
            # 必须回滚掉刚建的 auth 用户，否则每次重试都漏一个孤儿账号。
            logger.error(f"❌ 微信建号 profile 写入失败({profile_res.status_code}): {profile_res.text}")
            await _delete_auth_user(client, svc_headers, user_id)
            raise HTTPException(status_code=502, detail="创建账号失败，请稍后重试")

        # ── 3. 回读校验：openid 必须真的落库 ──
        # 它是这个账号唯一的找回凭据；写丢了用户下次登录就会变成一个全新账号，
        # 而且学习记录全留在旧号上。INSERT 失败会报错，但值被改写不会——只有回读能发现。
        check_res = await client.get(
            f"{settings.SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}&select=id,wechat_openid",
            headers=svc_headers)
        rows = check_res.json() if check_res.status_code == 200 else []
        stored_openid = rows[0].get("wechat_openid") if rows else None
        if stored_openid != openid:
            logger.error(f"❌ 微信建号回读校验失败: 期望 {openid}，库里 {stored_openid}")
            await _delete_auth_user(client, svc_headers, user_id)
            raise HTTPException(status_code=502, detail="创建账号失败，请稍后重试")

    logger.info(f"✅ 微信首次登录建号 user_id={user_id} account={user_account}")
    return user_id, nickname, user_account


# ============================================================
# 微信小程序登录（复用同一套 JWT）
# ============================================================
class WxLoginRequest(BaseModel):
    code: str


class WxBindRequest(BaseModel):
    openid: str
    unionid: str = ""
    login_input: str  # 邮箱或用户名
    password: str


@router.post("/wx-login")
async def wx_miniapp_login(req: WxLoginRequest):
    """
    微信小程序登录：
    uni.login() 获取 code → 后端换 openid → 查/建用户 → 返回 JWT

    与网页版共用同一套用户体系和 JWT 签发逻辑。
    """
    if not settings.WECHAT_MP_APPID or not settings.WECHAT_MP_SECRET:
        raise HTTPException(status_code=503, detail="小程序登录未配置（缺少 WECHAT_MP_APPID / WECHAT_MP_SECRET）")

    # 用小程序 code 换 openid
    async with httpx.AsyncClient(timeout=15.0) as client:
        jscode_url = (
            f"https://api.weixin.qq.com/sns/jscode2session"
            f"?appid={settings.WECHAT_MP_APPID}"
            f"&secret={settings.WECHAT_MP_SECRET}"
            f"&js_code={req.code}"
            f"&grant_type=authorization_code"
        )
        jscode_res = await client.get(jscode_url)
        if jscode_res.status_code != 200:
            raise HTTPException(status_code=502, detail="微信服务器无响应")

        jscode_data = jscode_res.json()
        if "errcode" in jscode_data and jscode_data["errcode"] != 0:
            errcode = jscode_data.get("errcode")
            errmsg = jscode_data.get("errmsg", "")
            raise HTTPException(status_code=400, detail=f"微信错误({errcode}): {errmsg}")

        openid = jscode_data.get("openid")
        unionid = jscode_data.get("unionid", "")

    if not openid:
        raise HTTPException(status_code=502, detail="未获取到微信 openid")

    # ── 先按 openid / unionid 找已有账号 ──
    user_id = None
    exist_user = None

    supabase_headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 先按 unionid 查
            if unionid:
                query_res = await client.get(
                    f"{settings.SUPABASE_URL}/rest/v1/profiles?wechat_unionid=eq.{unionid}&limit=1",
                    headers=supabase_headers
                )
                if query_res.status_code == 200 and query_res.json():
                    exist_user = query_res.json()[0]

            # 再按 openid 查
            if not exist_user:
                query_res = await client.get(
                    f"{settings.SUPABASE_URL}/rest/v1/profiles?wechat_openid=eq.{openid}&limit=1",
                    headers=supabase_headers
                )
                if query_res.status_code == 200 and query_res.json():
                    exist_user = query_res.json()[0]

            if exist_user:
                # ✅ 已有账号 — 直接登录
                user_id = exist_user.get("id")
                nickname = exist_user.get("nickname") or f"微信用户{openid[-6:]}"
                user_account = exist_user.get("user_account")
    except Exception as e:
        # 这里原来「降级返回 need_bind」。need_bind 那条路已经没了，
        # 再降级等于把用户送进一个不存在的流程 —— 如实报错。
        logger.error(f"❌ 小程序登录查询失败: {e}")
        raise HTTPException(status_code=503, detail="服务暂不可用，请稍后重试")

    # 首次登录 —— 直接建号，不再要求先绑定网页账号
    if not user_id:
        user_id, nickname, user_account = await _create_wechat_account(openid, unionid)

    token = _gen_jwt(user_id)
    return {
        "success": True,
        "need_bind": False,
        "access_token": token,
        "user": {
            "id": user_id,
            "nickname": nickname,
            "user_account": user_account,
            "wechat_openid": openid,
            "wechat_unionid": unionid,
        }
    }


# ============================================================
# 小程序绑定已有网页账号
# ============================================================
@router.post("/wx-bind")
async def wx_bind(req: WxBindRequest, request: Request):
    """
    小程序用户绑定已有网页账号：
    openid（微信获取） + 邮箱/用户名 + 密码 → 验证 → 绑定 openid 到 profiles → 返回 JWT
    """
    if not req.openid:
        raise HTTPException(status_code=400, detail="缺少 openid")

    client_ip = request.client.host if request.client else "unknown"
    # 两级限流（2026-09-27 修）：
    # 原来只按纯 IP 限 5 次/60 秒 —— NAT / 校园网下整栋楼共用一个桶，
    # 别人试几次就把你挤掉，用户侧表现就是「能走到绑定、但绑定失败」。
    # 改成和本文件 /login（第 30 行）同一套写法：按「IP + 登录账号」限，各账号各占一个桶。
    check_rate_limit(f"wxbind:{client_ip}:{req.login_input.strip().lower()}",
                     max_requests=5, window_seconds=60,
                     error_message="该账号绑定尝试过于频繁，请60秒后重试")
    # 再补一条按 IP 的总量闸，防止换个账号名继续扫。
    check_rate_limit(f"wxbind:ip:{client_ip}", max_requests=20, window_seconds=60,
                     error_message="绑定尝试过于频繁，请60秒后重试")

    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

    # 1. 根据登录输入查找或验证用户
    login_input = req.login_input.strip()
    if "@" in login_input:
        email = login_input
    else:
        # 按 user_account 查找邮箱
        async with httpx.AsyncClient(timeout=10.0) as client:
            search_url = f"{settings.SUPABASE_URL}/rest/v1/profiles?user_account=eq.{login_input}"
            search_res = await client.get(search_url, headers=headers)
            if search_res.status_code != 200 or not search_res.json():
                raise HTTPException(status_code=401, detail="账号不存在")
            email = search_res.json()[0].get("email")
            if not email:
                raise HTTPException(status_code=401, detail="账号未绑定邮箱")

    # 2. Supabase 验证密码
    async with httpx.AsyncClient(timeout=10.0) as client:
        auth_url = f"{settings.SUPABASE_URL}/auth/v1/token?grant_type=password"
        auth_data = {"email": email, "password": req.password}
        auth_res = await client.post(auth_url, headers=headers, json=auth_data)

        if auth_res.status_code != 200:
            error_msg = auth_res.text
            if "Invalid login credentials" in error_msg:
                raise HTTPException(status_code=401, detail="账号或密码错误")
            raise HTTPException(status_code=401, detail="验证失败，请检查账号密码")

        user_data = auth_res.json()
        user = user_data.get("user", {})
        user_id = user.get("id")

    # 3. 把 openid 写入 profiles 表
    #    ⚠️ 必须用 service_role：这是服务端代表用户写 profiles，anon key 会被 RLS 拦掉。
    #    而 UPDATE 被 RLS 拦是「静默 0 行、照样返回 204」—— 老代码既不检查返回值也不回读，
    #    于是照样发 token，客户端以为绑好了，下次登录又要求绑定（用户报的「绑定失败」）。
    #    services/supabase.py:154 已经记过同一个坑（存音频同理）。2026-09-27 修。
    if not settings.SUPABASE_SERVICE_ROLE_KEY:
        # ⚠️ 没有 service_role key 时 service_headers 会拼出 "Bearer None"，
        # 请求直接 401 —— 这比老代码（静默假成功）更难排查。显式报出来。
        # 部署前务必确认服务器 .env 配了 SUPABASE_SERVICE_ROLE_KEY。
        logger.error("❌ 未配置 SUPABASE_SERVICE_ROLE_KEY，wx-bind 无法绕过 RLS 写 profiles")
        raise HTTPException(status_code=500, detail="服务端未配置 SUPABASE_SERVICE_ROLE_KEY，绑定功能不可用")

    svc_headers = get_supabase_service_headers()
    async with httpx.AsyncClient(timeout=10.0) as client:
        patch_url = f"{settings.SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}"
        patch_data = {
            "wechat_openid": req.openid,
        }
        if req.unionid:
            patch_data["wechat_unionid"] = req.unionid
        patch_res = await client.patch(patch_url, headers=svc_headers, json=patch_data)
        if patch_res.status_code not in (200, 204):
            logger.error(f"❌ 绑定写入 profiles 失败 user={user_id} {patch_res.status_code}: {patch_res.text[:300]}")
            raise HTTPException(status_code=502, detail=f"绑定失败：写入用户资料出错（{patch_res.status_code}）")

    # 4. 回读确认真的落库了 —— RLS 静默 0 行这种情况，只有回读能发现
    async with httpx.AsyncClient(timeout=10.0) as client:
        profile_url = f"{settings.SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}"
        profile_res = await client.get(profile_url, headers=svc_headers)
        profile = profile_res.json()[0] if profile_res.status_code == 200 and profile_res.json() else {}

    if profile.get("wechat_openid") != req.openid:
        logger.error(
            f"❌ 绑定回读不一致 user={user_id}: 期望 {req.openid}，库里 {profile.get('wechat_openid')!r}"
        )
        raise HTTPException(status_code=502, detail="绑定未生效，请重试；若反复出现请联系管理员")

    token = _gen_jwt(user_id)
    return {
        "success": True,
        "access_token": token,
        "user": {
            "id": user_id,
            "nickname": profile.get("nickname", ""),
            "user_account": profile.get("user_account", ""),
            "email": email,
            # 回显库里的值，不再回显请求参数 —— 老代码回显 req.openid，
            # 写入失败时客户端照样看到自己的 openid，更坐实了「绑定成功」的假象。
            "wechat_openid": profile.get("wechat_openid", ""),
            "wechat_unionid": profile.get("wechat_unionid", "") or req.unionid or "",
            "grade": profile.get("grade", ""),
            "major": profile.get("major", ""),
            "learning_stage": profile.get("learning_stage", ""),
            "avatar_url": profile.get("avatar_url", ""),
        }
    }


# ============================================================
# 微信用户信息查询（供前端 localStorage 恢复后完整获取用户资料）
# ============================================================
@router.get("/wechat/user/{user_id}")
async def get_wechat_user(user_id: str):
    """根据 user_id 获取用户资料（微信登录用户无 Supabase 时的本地存储查询）"""
    local = _temp_user_store.get(f"user:{user_id}")
    if local:
        return {"success": True, "user": local}

    # 回退 Supabase
    try:
        headers = {
            "apikey": settings.SUPABASE_KEY,
            "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(
                f"{settings.SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}&limit=1",
                headers=headers
            )
            if res.status_code == 200 and res.json():
                return {"success": True, "user": res.json()[0]}
    except Exception:
        pass

    raise HTTPException(status_code=404, detail="用户不存在")

# ============================================================
# 账号主题定制四轴：背景色 + 组件色 + 品牌色 + 字体方案，跨设备同步
#   2026-09-02 品牌/字体 → 2026-09-03 补背景色/组件色、PUT 改全量保存
# 存储：user_theme_settings 表（backend/sql/fix_user_theme.sql，幂等）
# ============================================================

class ShortcutsRequest(BaseModel):
    user_id: str
    # {动作 id: 组合键}。空串 = 用户主动解绑。
    # 用 dict 而不是固定字段：动作会随时增删，做成列就得跟着改表。
    bindings: dict = {}


class ThemeRequest(BaseModel):
    user_id: str
    brand_color: Optional[str] = None
    text_scheme: Optional[str] = None
    text_overrides: Optional[dict] = None
    bg_color: Optional[str] = None       # 自定义背景色 hex；None = 跟随浅/深模式
    surface_color: Optional[str] = None  # 自定义组件色（毛玻璃）hex；None = 白描层默认


def _valid_hex(color: str) -> bool:
    return bool(color) and len(color) in (4, 7) and color.startswith("#")


@router.get("/theme/{user_id}")
async def get_theme(user_id: str, current_user: str = Depends(get_current_user)):
    """读取账号主题定制（无记录返回默认值）"""
    verify_user_match(user_id, current_user)
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
    }
    url = f"{settings.SUPABASE_URL}/rest/v1/user_theme_settings?user_id=eq.{user_id}"
    async with httpx.AsyncClient(timeout=15.0) as client:
        res = await client.get(url, headers=headers)
        if res.status_code == 200 and res.json():
            row = res.json()[0]
            return {
                "brand_color": row.get("brand_color") or "#409EFF",
                "text_scheme": row.get("text_scheme") or "default",
                "text_overrides": row.get("text_overrides") or None,
                "bg_color": row.get("bg_color") or None,
                "surface_color": row.get("surface_color") or None,
            }
        return {"brand_color": "#409EFF", "text_scheme": "default", "text_overrides": None,
                "bg_color": None, "surface_color": None}


@router.put("/theme")
async def update_theme(req: ThemeRequest, current_user: str = Depends(get_current_user)):
    """保存账号主题定制（全量保存 + upsert：前端始终发完整状态，null 即清空该轴）"""
    verify_user_match(req.user_id, current_user)

    brand = req.brand_color or "#409EFF"
    if not _valid_hex(brand):
        raise HTTPException(status_code=400, detail="品牌色格式错误（应为 #RRGGBB）")
    bg = req.bg_color or None
    if bg is not None and not _valid_hex(bg):
        raise HTTPException(status_code=400, detail="背景色格式错误（应为 #RRGGBB）")
    surface = req.surface_color or None
    if surface is not None and not _valid_hex(surface):
        raise HTTPException(status_code=400, detail="组件色格式错误（应为 #RRGGBB）")

    payload = {
        "brand_color": brand,
        "text_scheme": req.text_scheme or "default",
        "text_overrides": req.text_overrides,
        "bg_color": bg,
        "surface_color": surface,
    }

    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        check = await client.get(
            f"{settings.SUPABASE_URL}/rest/v1/user_theme_settings?user_id=eq.{req.user_id}",
            headers=headers)
        exists = check.status_code == 200 and check.json()

        if exists:
            url = f"{settings.SUPABASE_URL}/rest/v1/user_theme_settings?user_id=eq.{req.user_id}"
            res = await client.patch(url, headers=headers, json=payload)
        else:
            payload["user_id"] = req.user_id
            url = f"{settings.SUPABASE_URL}/rest/v1/user_theme_settings"
            res = await client.post(url, headers=headers, json=payload)

        if res.status_code not in (200, 201, 204):
            raise HTTPException(status_code=400, detail=f"保存主题失败: {res.text}")
        return {"success": True}

# ============================================================
# 自定义快捷键（跟随账号）
# ============================================================
@router.get("/shortcuts/{user_id}")
async def get_shortcuts(user_id: str, current_user: str = Depends(get_current_user)):
    """读取账号的快捷键绑定。没有记录就返回空映射 —— 由前端的注册表补默认值。

    这里**不返回默认值**：默认键定义在前端 `shortcuts/registry.js` 里，
    后端不该重复维护一份（两边不一致时，「默认」到底是哪个就说不清了）。
    """
    verify_user_match(user_id, current_user)
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
    }
    url = f"{settings.SUPABASE_URL}/rest/v1/user_shortcuts?user_id=eq.{user_id}&select=bindings"
    async with httpx.AsyncClient(timeout=15.0) as client:
        res = await client.get(url, headers=headers)
        if res.status_code == 200 and res.json():
            return {"bindings": res.json()[0].get("bindings") or {}}
        if res.status_code != 200:
            # 表还没建会走到这里（42P01）。明确报出来，
            # 别让前端以为「这个人没配过快捷键」而把默认值当作用户选择写回去。
            logger.warning(f"读取快捷键失败({res.status_code}): {res.text[:200]}")
            raise HTTPException(status_code=502, detail="读取快捷键设置失败，请稍后重试")
        return {"bindings": {}}


@router.put("/shortcuts")
async def update_shortcuts(req: ShortcutsRequest, current_user: str = Depends(get_current_user)):
    """全量保存快捷键绑定（前端始终发完整状态，与主题那套一致）。

    只做最基本的形状校验：id 非空、值是字符串。**不校验 id 是否是已知动作** ——
    旧版本客户端可能带着已下线的动作 id，硬拒会让用户整个保存不了；
    前端会忽略不认识的 id。
    """
    verify_user_match(req.user_id, current_user)

    clean = {}
    for k, v in (req.bindings or {}).items():
        if not isinstance(k, str) or not k.strip():
            continue
        if not isinstance(v, str):
            raise HTTPException(status_code=400, detail=f"快捷键「{k}」的值必须是字符串")
        # 长度兜底，防脏数据把 JSONB 撑爆；正常组合键不会超过这个数
        if len(v) > 64:
            raise HTTPException(status_code=400, detail=f"快捷键「{k}」过长")
        clean[k.strip()] = v

    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    base = f"{settings.SUPABASE_URL}/rest/v1/user_shortcuts"
    async with httpx.AsyncClient(timeout=15.0) as client:
        check = await client.get(f"{base}?user_id=eq.{req.user_id}&select=user_id", headers=headers)
        exists = check.status_code == 200 and check.json()

        if exists:
            res = await client.patch(
                f"{base}?user_id=eq.{req.user_id}",
                headers=headers,
                json={"bindings": clean, "updated_at": datetime.utcnow().isoformat() + "Z"})
        else:
            res = await client.post(
                base, headers=headers,
                json={"user_id": req.user_id, "bindings": clean})

        if res.status_code not in (200, 201, 204):
            logger.error(f"保存快捷键失败({res.status_code}): {res.text[:200]}")
            raise HTTPException(status_code=502, detail="保存快捷键失败，请稍后重试")

    return {"success": True, "count": len(clean)}
