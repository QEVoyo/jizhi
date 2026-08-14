from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Header, Depends, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from config import settings
import httpx
import time
import uuid
import random
from PIL import Image
import io
from utils.email import send_verification_code_email
from utils.auth_middleware import get_current_user, verify_user_match
from utils.rate_limit import check_rate_limit
from logging_config import logger

router = APIRouter(prefix="/auth", tags=["认证"])


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
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",  # ← 改这里
        "Content-Type": "application/json"
    }

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


# ============================================================
# 微信公众平台测试号 · 网页扫码登录（个人可用，免费）
# ============================================================
# 流程：网页生成二维码 → 用户微信扫码 → 公众号授权页 → 授权后
#       微信浏览器回调后端 → 后端记录结果 → 网页轮询拿到 token
# ============================================================
import hashlib
import secrets
import jwt as pyjwt
import qrcode as qrcode_lib
import io as _io
import base64 as _b64
from datetime import datetime, timedelta
from urllib.parse import quote

# 内存临时存储（生产环境应换 Redis）
_poll_results: dict[str, dict] = {}              # poll_token → {jwt, user_info, created_at}
_state_map: dict[str, dict] = {}                  # state → {poll_token, created_at}
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


def _cleanup_expired():
    """清理过期的 poll / state"""
    now = time.time()
    for store in [_poll_results, _state_map]:
        expired = [k for k, v in store.items()
                   if now - v.get("created_at", now) > 600]
        for k in expired:
            del store[k]


@router.get("/wechat/qrcode")
async def wechat_qrcode(redirect: str = "/home"):
    """
    返回微信扫码登录的二维码（base64 PNG）和轮询 token。
    仅限已绑定微信的账号——未绑定则返回 bound: false。
    """
    if not settings.WECHAT_WEB_APPID or not settings.WECHAT_WEB_SECRET:
        raise HTTPException(status_code=503,
                            detail="微信登录未配置。请前往 mp.weixin.qq.com/debug 获取测试号 appid/secret")

    _cleanup_expired()

    poll_token = secrets.token_urlsafe(24)
    state = secrets.token_urlsafe(32)
    _state_map[state] = {"poll_token": poll_token, "mode": "login", "created_at": time.time()}
    _poll_results[poll_token] = {"created_at": time.time()}

    callback_url = f"{settings.BACKEND_EXTERNAL_URL}/auth/wechat/callback"
    oauth_url = (
        f"https://open.weixin.qq.com/connect/oauth2/authorize"
        f"?appid={settings.WECHAT_WEB_APPID}"
        f"&redirect_uri={quote(callback_url, safe='')}"
        f"&response_type=code"
        f"&scope=snsapi_userinfo"
        f"&state={state}"
        f"#wechat_redirect"
    )

    img = qrcode_lib.make(oauth_url)
    buf = _io.BytesIO()
    img.save(buf, format='PNG')
    qr_base64 = _b64.b64encode(buf.getvalue()).decode()

    return {
        "qrcode": f"data:image/png;base64,{qr_base64}",
        "poll_token": poll_token,
        "expires_in": 300,
    }


@router.get("/wechat/bind-qrcode")
async def wechat_bind_qrcode(current_user: str = Depends(get_current_user)):
    """
    已登录用户绑定微信——返回二维码，扫码后 openid 写入该用户的 profiles。
    """
    if not settings.WECHAT_WEB_APPID or not settings.WECHAT_WEB_SECRET:
        raise HTTPException(status_code=503,
                            detail="微信登录未配置。请前往 mp.weixin.qq.com/debug 获取测试号 appid/secret")

    _cleanup_expired()

    poll_token = secrets.token_urlsafe(24)
    state = secrets.token_urlsafe(32)
    _state_map[state] = {
        "poll_token": poll_token,
        "mode": "bind",
        "user_id": current_user,
        "created_at": time.time()
    }
    _poll_results[poll_token] = {"created_at": time.time()}

    callback_url = f"{settings.BACKEND_EXTERNAL_URL}/auth/wechat/callback"
    oauth_url = (
        f"https://open.weixin.qq.com/connect/oauth2/authorize"
        f"?appid={settings.WECHAT_WEB_APPID}"
        f"&redirect_uri={quote(callback_url, safe='')}"
        f"&response_type=code"
        f"&scope=snsapi_userinfo"
        f"&state={state}"
        f"#wechat_redirect"
    )

    img = qrcode_lib.make(oauth_url)
    buf = _io.BytesIO()
    img.save(buf, format='PNG')
    qr_base64 = _b64.b64encode(buf.getvalue()).decode()

    return {
        "qrcode": f"data:image/png;base64,{qr_base64}",
        "poll_token": poll_token,
        "expires_in": 300,
    }


@router.get("/wechat/callback")
async def wechat_oauth_callback(code: str, state: str):
    """
    微信公众号 OAuth 回调——微信浏览器扫码授权后调这里。

    这个端点被手机微信浏览器访问，因此需要 BACKEND_EXTERNAL_URL 能从手机访问到。
    """
    entry = _state_map.pop(state, None)
    if not entry:
        return HTMLResponse("<h2>已过期，请返回网页重新操作</h2>", status_code=400)
    poll_token = entry.get("poll_token")
    mode = entry.get("mode", "login")
    bind_user_id = entry.get("user_id")  # 仅 bind 模式有

    # 用 code 换 access_token
    async with httpx.AsyncClient(timeout=15.0) as client:
        token_url = (
            f"https://api.weixin.qq.com/sns/oauth2/access_token"
            f"?appid={settings.WECHAT_WEB_APPID}"
            f"&secret={settings.WECHAT_WEB_SECRET}"
            f"&code={code}"
            f"&grant_type=authorization_code"
        )
        token_res = await client.get(token_url)
        if token_res.status_code != 200:
            return HTMLResponse("<h2>微信服务器无响应，请重试</h2>", status_code=502)

        token_data = token_res.json()
        if "errcode" in token_data:
            errmsg = token_data.get("errmsg", "")
            return HTMLResponse(f"<h2>微信授权失败：{errmsg}</h2>", status_code=400)

        access_token = token_data.get("access_token")
        openid = token_data.get("openid")
        unionid = token_data.get("unionid", "")

        if not openid:
            return HTMLResponse("<h2>未获取到用户标识</h2>", status_code=502)

        # 获取用户信息
        nickname = ""
        avatar_url = ""
        userinfo_res = await client.get(
            f"https://api.weixin.qq.com/sns/userinfo?access_token={access_token}&openid={openid}"
        )
        if userinfo_res.status_code == 200:
            ui = userinfo_res.json()
            if "errcode" not in ui:
                nickname = ui.get("nickname", "")
                avatar_url = ui.get("headimgurl", "")

    if mode == "bind":
        # ── 绑定模式：将 openid 写入已登录用户 ──
        ok = await _bind_wechat_to_user(bind_user_id, openid, unionid, nickname, avatar_url)
        if ok:
            _poll_results[poll_token] = {
                "created_at": time.time(),
                "bound": True,
                "nickname": nickname,
            }
            return HTMLResponse(f"""
            <html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
            <style>body{{display:flex;align-items:center;justify-content:center;height:100vh;margin:0;
            font-family:-apple-system,sans-serif;background:#f5f5f5}}</style></head>
            <body><div style="text-align:center;padding:24px;border-radius:16px;background:#fff;box-shadow:0 2px 16px rgba(0,0,0,.08)">
            <div style="font-size:48px;margin-bottom:12px">🔗</div>
            <h2 style="margin:0 0 4px;color:#07c160">绑定成功</h2>
            <p style="color:#999;margin:0">微信已绑定到账号</p>
            <p style="color:#bbb;font-size:13px;margin-top:16px">{nickname or ''}</p>
            </div></body></html>
            """)
        else:
            _poll_results[poll_token] = {"created_at": time.time(), "bound": False, "error": "绑定失败，请重试"}
            return HTMLResponse("<h2>绑定失败，请重试</h2>", status_code=400)

    else:
        # ── 登录模式：查 openid 是否已绑定 ──
        user = await _find_wechat_user(openid, unionid)
        if user:
            jwt_token = _gen_jwt(user["id"])
            _poll_results[poll_token] = {
                "created_at": time.time(),
                "access_token": jwt_token,
                "user": user,
            }
            return HTMLResponse(f"""
            <html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
            <style>body{{display:flex;align-items:center;justify-content:center;height:100vh;margin:0;
            font-family:-apple-system,sans-serif;background:#f5f5f5}}</style></head>
            <body><div style="text-align:center;padding:24px;border-radius:16px;background:#fff;box-shadow:0 2px 16px rgba(0,0,0,.08)">
            <div style="font-size:48px;margin-bottom:12px">✅</div>
            <h2 style="margin:0 0 4px;color:#07c160">登录成功</h2>
            <p style="color:#999;margin:0">请返回网页继续</p>
            <p style="color:#bbb;font-size:13px;margin-top:16px">{user.get('nickname', '')}</p>
            </div></body></html>
            """)
        else:
            # 未绑定
            _poll_results[poll_token] = {
                "created_at": time.time(),
                "bound": False,
                "wechat_nickname": nickname,
                "wechat_avatar": avatar_url,
            }
            return HTMLResponse(f"""
            <html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
            <style>body{{display:flex;align-items:center;justify-content:center;height:100vh;margin:0;
            font-family:-apple-system,sans-serif;background:#f5f5f5}}</style></head>
            <body><div style="text-align:center;padding:24px;border-radius:16px;background:#fff;box-shadow:0 2px 16px rgba(0,0,0,.08)">
            <div style="font-size:48px;margin-bottom:12px">⚠️</div>
            <h2 style="margin:0 0 4px;color:#f59e0b">未绑定账号</h2>
            <p style="color:#999;margin:4px 0">请用账号密码登录后</p>
            <p style="color:#999;margin:0">在个人中心绑定微信</p>
            <p style="color:#bbb;font-size:13px;margin-top:16px">{nickname or ''}</p>
            </div></body></html>
            """)


@router.get("/wechat/poll/{poll_token}")
async def wechat_poll(poll_token: str):
    """
    网页端轮询此接口。

    返回：
    - {ready: false}                     → 还没扫码
    - {ready: true, access_token, user}  → 登录成功
    - {ready: true, bound: false}        → 未绑定账号
    - {ready: true, bound: true}         → 绑定成功
    """
    _cleanup_expired()

    result = _poll_results.get(poll_token)
    if not result:
        return {"ready": False, "error": "二维码已过期，请重新获取"}

    if "access_token" in result:
        token = result.pop("access_token")
        user = result.pop("user")
        return {"ready": True, "access_token": token, "user": user}
    elif "bound" in result:
        # 绑定结果或未绑定
        out = {"ready": True, "bound": result.get("bound", False)}
        if "error" in result:
            out["error"] = result["error"]
        if "nickname" in result:
            out["nickname"] = result["nickname"]
        del _poll_results[poll_token]
        return out

    return {"ready": False}


# ── 查找微信用户（仅查询，不创建）──
async def _find_wechat_user(openid: str, unionid: str) -> dict | None:
    """从 Supabase profiles 查 openid/unionid 对应的用户，未找到返回 None"""
    try:
        headers = {
            "apikey": settings.SUPABASE_KEY,
            "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            for field, val in [("wechat_unionid", unionid), ("wechat_openid", openid)]:
                if not val:
                    continue
                r = await client.get(
                    f"{settings.SUPABASE_URL}/rest/v1/profiles?{field}=eq.{val}&limit=1",
                    headers=headers)
                if r.status_code == 200 and r.json():
                    p = r.json()[0]
                    return {
                        "id": p["id"], "email": p.get("email"), "nickname": p.get("nickname"),
                        "user_account": p.get("user_account"), "avatar_url": p.get("avatar_url"),
                        "role": p.get("role", "user"), "is_admin": p.get("is_admin", False),
                        "wechat_openid": openid, "wechat_unionid": unionid,
                    }
    except Exception as e:
        logger.warning(f"查询微信用户失败: {e}")
    return None


# ── 绑定微信到账户 ──
async def _bind_wechat_to_user(user_id: str, openid: str, unionid: str, nickname: str, avatar_url: str) -> bool:
    """将 openid/unionid 写入指定用户的 profiles"""
    try:
        headers = {
            "apikey": settings.SUPABASE_KEY,
            "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        }
        data = {"wechat_openid": openid, "wechat_unionid": unionid or ""}
        if nickname:
            data["nickname"] = nickname
        if avatar_url:
            data["avatar_url"] = avatar_url

        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.patch(
                f"{settings.SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}",
                headers=headers, json=data)
            if r.status_code in [200, 204]:
                return True
            logger.warning(f"绑定微信失败({r.status_code}): {r.text}")
    except Exception as e:
        logger.warning(f"绑定微信异常: {e}")
    return False


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

    # ── 查找已绑定用户（不再自动创建新账号）──
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
                # ✅ 已绑定 — 直接登录
                user_id = exist_user.get("id")
                nickname = exist_user.get("nickname") or f"微信用户{openid[-6:]}"
                user_account = exist_user.get("user_account")
            else:
                # ❌ 未绑定 — 返回 need_bind，让用户输入网页账号密码来绑定
                return {
                    "success": True,
                    "need_bind": True,
                    "openid": openid,
                    "unionid": unionid or "",
                    "message": "请绑定已有网页账号，或创建新账号后绑定",
                }
    except Exception as e:
        logger.warning(f"小程序登录 Supabase 查询失败: {e}，降级返回 need_bind")
        return {
            "success": True,
            "need_bind": True,
            "openid": openid,
            "unionid": unionid or "",
            "message": "服务暂不可用，请稍后重试",
        }

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
    check_rate_limit(f"wxbind:{client_ip}", max_requests=5, window_seconds=60,
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
    async with httpx.AsyncClient(timeout=10.0) as client:
        patch_url = f"{settings.SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}"
        patch_data = {
            "wechat_openid": req.openid,
        }
        if req.unionid:
            patch_data["wechat_unionid"] = req.unionid
        patch_res = await client.patch(patch_url, headers=headers, json=patch_data)

    # 4. 查询完整用户信息
    async with httpx.AsyncClient(timeout=10.0) as client:
        profile_url = f"{settings.SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}"
        profile_res = await client.get(profile_url, headers=headers)
        profile = profile_res.json()[0] if profile_res.status_code == 200 and profile_res.json() else {}

    token = _gen_jwt(user_id)
    return {
        "success": True,
        "access_token": token,
        "user": {
            "id": user_id,
            "nickname": profile.get("nickname", ""),
            "user_account": profile.get("user_account", ""),
            "email": email,
            "wechat_openid": req.openid,
            "wechat_unionid": req.unionid or profile.get("wechat_unionid", ""),
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