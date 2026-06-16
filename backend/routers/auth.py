from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from config import settings
import httpx
import time

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

    # 判断是邮箱还是账号
    if "@" in req.login_input:
        email = req.login_input
        url = f"{settings.SUPABASE_URL}/auth/v1/token?grant_type=password"
        data = {"email": email, "password": req.password}
    else:
        # 先通过账号查邮箱
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

    # 调用 Supabase 登录
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

        # 获取用户资料
        profile_url = f"{settings.SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}"
        profile_res = await client.get(profile_url, headers=headers)

        user_account = None
        nickname = None
        avatar_url = None
        bio = None

        if profile_res.status_code == 200 and profile_res.json():
            profile = profile_res.json()[0]
            user_account = profile.get("user_account")
            nickname = profile.get("nickname")
            avatar_url = profile.get("avatar_url")
            bio = profile.get("bio")

        return {
            "id": user_id,
            "email": email,
            "access_token": access_token,
            "user_account": user_account,
            "nickname": nickname,
            "avatar_url": avatar_url,
            "bio": bio
        }


class RegisterRequest(BaseModel):
    email: str
    password: str
    nickname: str = None


@router.post("/register")
async def register(req: RegisterRequest):
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

    signup_url = f"{settings.SUPABASE_URL}/auth/v1/signup"
    data = {"email": req.email, "password": req.password}

    async with httpx.AsyncClient() as client:
        # 调用 Supabase 注册
        res = await client.post(signup_url, headers=headers, json=data, timeout=30)

        if res.status_code != 200:
            error_msg = res.text
            # Supabase 邮箱已存在的错误码是 422 或 400，信息包含 "already registered" 或 "User already registered"
            if "already registered" in error_msg.lower() or "user already" in error_msg.lower():
                raise HTTPException(status_code=400, detail="该邮箱已注册")
            raise HTTPException(status_code=400, detail=f"注册失败: {error_msg}")

        user_data = res.json()
        user_id = user_data.get("id")
        if not user_id:
            user_id = user_data.get("user", {}).get("id")

        # 生成账号（简化版，后续完善）
        import random
        user_account = str(random.randint(10000000, 99999999))

        # 创建 profiles
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

        return {
            "id": user_id,
            "email": req.email,
            "user_account": user_account,
            "message": "注册成功，请查收验证邮件"
        }


@router.get("/profile/{user_id}")
async def get_profile(user_id: str):
    """获取用户资料"""
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
            "bio": profile.get("bio")
        }


class UpdateNicknameRequest(BaseModel):
    user_id: str
    nickname: str


@router.put("/update-nickname")
async def update_nickname(req: UpdateNicknameRequest):
    """更新用户昵称"""
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
    """更新用户简介"""
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


from fastapi import UploadFile, File
import uuid
import httpx
from PIL import Image
import io


@router.post("/upload-avatar/{user_id}")
async def upload_avatar(user_id: str, file: UploadFile = File(...)):
    """上传头像"""

    # 1. 读取并压缩图片
    contents = await file.read()
    img = Image.open(io.BytesIO(contents))
    img = img.resize((200, 200))

    img_bytes_io = io.BytesIO()
    img.save(img_bytes_io, format='PNG')
    compressed_bytes = img_bytes_io.getvalue()

    # 2. 生成文件路径
    timestamp = str(int(time.time()))
    file_path = f"{user_id}/{timestamp}.png"

    # 3. 上传到 Supabase Storage
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

        # 4. 更新 profiles 表中的 avatar_url
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