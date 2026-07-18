from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Header
from pydantic import BaseModel
from config import settings
import httpx
import time
import uuid
import random
from PIL import Image
import io
from utils.email import send_verification_code_email

router = APIRouter(prefix="/auth", tags=["认证"])


class LoginRequest(BaseModel):
    login_input: str
    password: str


@router.post("/login")
async def login(req: LoginRequest):
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

        if profile_res.status_code == 200 and profile_res.json():
            profile = profile_res.json()[0]
            user_account = profile.get("user_account")
            nickname = profile.get("nickname")
            avatar_url = profile.get("avatar_url")
            bio = profile.get("bio")
            learning_stage = profile.get("learning_stage")
            grade = profile.get("grade")
            major = profile.get("major")

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
            "major": major
        }


# ============================================================
# ✅ 新增：发送验证码接口
# ============================================================
@router.post("/send-code")
async def send_verification_code(email: str):
    """发送邮箱验证码"""
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
        print(f"删除旧验证码: {delete_res.status_code}")

        # 插入新验证码
        insert_data = {
            "email": email,
            "code": code,
            "expires_at": int(time.time()) + 600
        }
        insert_url = f"{settings.SUPABASE_URL}/rest/v1/email_verification_codes"
        insert_res = await client.post(insert_url, headers=headers, json=insert_data)
        print(f"插入验证码状态: {insert_res.status_code}")
        print(f"插入验证码响应: {insert_res.text}")

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
async def register(req: RegisterRequest):
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
async def update_nickname(req: UpdateNicknameRequest):
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
async def update_bio(req: UpdateBioRequest):
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
    learning_stage: str
    grade: str
    major: str


@router.put("/update-learning-info")
async def update_learning_info(req: UpdateLearningInfoRequest):
    """更新学习信息（学习阶段、年级、专业/方向）"""
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

    url = f"{settings.SUPABASE_URL}/rest/v1/profiles?id=eq.{req.user_id}"
    data = {
        "learning_stage": req.learning_stage,
        "grade": req.grade,
        "major": req.major
    }

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
async def upload_avatar(user_id: str, file: UploadFile = File(...)):
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
async def update_status(user_id: str = Query(...), status: str = Query(...)):
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
    authorization: str = Header(...)  # ✅ 接收用户的 token
):
    """修改密码"""
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