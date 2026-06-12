import os
import httpx
import random
from dotenv import load_dotenv
from PIL import Image
import io

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


def generate_user_account():
    """生成唯一的8位数字账号"""
    while True:
        account = str(random.randint(10000000, 99999999))
        url = f"{SUPABASE_URL}/rest/v1/profiles?user_account=eq.{account}"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}"
        }
        try:
            res = httpx.get(url, headers=headers, timeout=10)
            if res.status_code == 200 and len(res.json()) == 0:
                return account
        except Exception as e:
            print(f"检查账号失败: {e}")
    return "00000000"


def ensure_profile_exists(user_id: str, email: str, nickname: str = None):
    """确保 profiles 表有该用户的记录"""
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

    # 检查是否存在
    check_url = f"{SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}"
    check_res = httpx.get(check_url, headers=headers)

    if check_res.status_code == 200 and check_res.json():
        print(f"用户 {user_id} 的 profiles 已存在")
        return True

    # 不存在则创建
    user_account = generate_user_account()
    profile_url = f"{SUPABASE_URL}/rest/v1/profiles"
    profile_data = {
        "id": user_id,
        "email": email,
        "nickname": nickname if nickname else email.split("@")[0],
        "user_account": user_account
    }
    profile_res = httpx.post(profile_url, headers=headers, json=profile_data, timeout=30)
    print(f"创建 profiles: {profile_res.status_code}")

    return profile_res.status_code in [200, 201]


def sign_up(email, password, nickname=None):
    print(f"开始注册: {email}")

    signup_url = f"{SUPABASE_URL}/auth/v1/signup"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    data = {"email": email, "password": password}

    res = httpx.post(signup_url, headers=headers, json=data, timeout=30)
    print(f"注册响应: {res.status_code}")

    if res.status_code != 200:
        return None, res.text

    user_data = res.json()
    user_id = user_data.get("id")
    if not user_id:
        user_id = user_data.get("user", {}).get("id")

    if not user_id:
        return None, "无法获取用户ID"

    print(f"用户ID: {user_id}")

    # 确保 profiles 存在
    success = ensure_profile_exists(user_id, email, nickname)
    if not success:
        return None, "创建用户资料失败"

    user_account = generate_user_account()  # 重新获取（ensure_profile_exists 中已生成但未返回）
    # 获取刚才生成的账号
    check_url = f"{SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}"
    check_res = httpx.get(check_url, headers=headers)
    if check_res.status_code == 200 and check_res.json():
        user_account = check_res.json()[0].get("user_account")

    return {"id": user_id, "email": email, "user_account": user_account}, None


def sign_in(login_input, password):
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

    if "@" in login_input:
        email = login_input
        url = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"
        data = {"email": email, "password": password}
    else:
        search_url = f"{SUPABASE_URL}/rest/v1/profiles?user_account=eq.{login_input}"
        search_res = httpx.get(search_url, headers=headers)
        if search_res.status_code != 200 or not search_res.json():
            return None, "账号不存在"
        email = search_res.json()[0].get("email")
        if not email:
            return None, "账号未绑定邮箱"
        url = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"
        data = {"email": email, "password": password}

    res = httpx.post(url, headers=headers, json=data)
    if res.status_code != 200:
        error_msg = res.text
        if "Invalid login credentials" in error_msg:
            return None, "账号或密码错误"
        if "Email not confirmed" in error_msg:
            return None, "邮箱尚未验证，请先去邮箱点击验证链接"
        return None, error_msg

    data = res.json()
    user = data.get("user", {})
    user_id = user.get("id")
    access_token = data.get("access_token")

    # 确保 profiles 存在（登录时也检查）
    ensure_profile_exists(user_id, email)

    profile_url = f"{SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}"
    profile_res = httpx.get(profile_url, headers=headers)
    user_account = None
    nickname = None
    avatar_url = None
    bio = None
    if profile_res.status_code == 200 and profile_res.json():
        profile_data = profile_res.json()[0]
        user_account = profile_data.get("user_account")
        nickname = profile_data.get("nickname")
        avatar_url = profile_data.get("avatar_url")
        bio = profile_data.get("bio")

    return {
        "id": user_id,
        "email": email,
        "access_token": access_token,
        "user_account": user_account,
        "nickname": nickname,
        "avatar_url": avatar_url,
        "bio": bio
    }, None


def get_user_nickname(user_id):
    url = f"{SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}"
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    res = httpx.get(url, headers=headers)
    if res.status_code == 200 and res.json():
        return res.json()[0].get("nickname")
    return None


def update_nickname(user_id: str, new_nickname: str):
    url = f"{SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    data = {"nickname": new_nickname}
    try:
        res = httpx.patch(url, headers=headers, json=data, timeout=30)
        print(f"更新昵称响应码: {res.status_code}")
        print(f"更新昵称响应内容: {res.text}")
        # Supabase PATCH 成功返回 200，也可能返回 204（无内容）
        return res.status_code in [200, 204]
    except Exception as e:
        print(f"更新昵称异常: {e}")
        return False


def update_password(access_token: str, new_password: str):
    url = f"{SUPABASE_URL}/auth/v1/user"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    data = {"password": new_password}
    res = httpx.put(url, headers=headers, json=data)
    return res.status_code == 200


def upload_avatar(user_id: str, image_bytes):
    from datetime import datetime
    import httpx
    from PIL import Image
    import io

    # 压缩图片
    img = Image.open(io.BytesIO(image_bytes))
    img = img.resize((200, 200))
    img_bytes_io = io.BytesIO()
    img.save(img_bytes_io, format='PNG')
    compressed_bytes = img_bytes_io.getvalue()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = f"{user_id}/{timestamp}.png"

    # 尝试上传到 avatars bucket
    url = f"{SUPABASE_URL}/storage/v1/object/avatars/{file_path}"

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "image/png"
    }

    try:
        res = httpx.post(url, headers=headers, content=compressed_bytes, timeout=30)
        print(f"上传响应码: {res.status_code}")
        print(f"上传响应内容: {res.text}")

        # 200 或 201 都表示成功
        if res.status_code in [200, 201]:
            public_url = f"{SUPABASE_URL}/storage/v1/object/public/avatars/{file_path}"
            print(f"上传成功: {public_url}")
            return public_url
        else:
            # 打印错误详情
            print(f"上传失败: {res.text}")
            return None
    except Exception as e:
        print(f"上传异常: {e}")
        return None


def get_avatar_url(user_id: str):
    """获取用户头像 URL"""
    url = f"{SUPABASE_URL}/rest/v1/profiles?select=avatar_url&id=eq.{user_id}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    res = httpx.get(url, headers=headers)
    if res.status_code == 200 and res.json():
        return res.json()[0].get("avatar_url")
    return None


def update_avatar_url(user_id: str, avatar_url: str):
    """更新 profiles 表中的 avatar_url"""
    url = f"{SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    data = {"avatar_url": avatar_url}
    try:
        res = httpx.patch(url, headers=headers, json=data, timeout=30)
        print(f"更新头像URL响应码: {res.status_code}")
        print(f"更新头像URL响应内容: {res.text}")
        # 200 或 204 都表示成功
        return res.status_code in [200, 204]
    except Exception as e:
        print(f"更新头像URL异常: {e}")
        return False


def get_user_bio(user_id: str):
    """获取用户简介"""
    url = f"{SUPABASE_URL}/rest/v1/profiles?select=bio&id=eq.{user_id}"
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    res = httpx.get(url, headers=headers)
    if res.status_code == 200 and res.json():
        return res.json()[0].get("bio", "")
    return ""


def update_user_bio(user_id: str, bio: str):
    """更新用户简介"""
    url = f"{SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    data = {"bio": bio}
    res = httpx.patch(url, headers=headers, json=data)
    return res.status_code == 200


# 在 auth.py 末尾添加
def ensure_profile_exists(user_id: str, email: str, nickname: str = None):
    """确保 profiles 表有该用户的记录"""
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

    check_url = f"{SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}"
    check_res = httpx.get(check_url, headers=headers)

    if check_res.status_code == 200 and check_res.json():
        return True

    user_account = generate_user_account()
    profile_url = f"{SUPABASE_URL}/rest/v1/profiles"
    profile_data = {
        "id": user_id,
        "email": email,
        "nickname": nickname if nickname else email.split("@")[0],
        "user_account": user_account
    }
    profile_res = httpx.post(profile_url, headers=headers, json=profile_data, timeout=30)
    return profile_res.status_code in [200, 201]


def get_user_status(user_id: str):
    """获取用户在线状态"""
    url = f"{SUPABASE_URL}/rest/v1/user_status?user_id=eq.{user_id}&select=status"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    try:
        res = httpx.get(url, headers=headers, timeout=10)
        print(f"获取状态响应: {res.status_code} - {res.text}")  # 调试用
        if res.status_code == 200 and res.json():
            return res.json()[0].get("status", "offline")
        else:
            # 没有记录，创建一条
            create_user_status(user_id, "online")
            return "online"
    except Exception as e:
        print(f"获取状态失败: {e}")
        return "offline"


def create_user_status(user_id: str, status: str = "online"):
    """创建用户状态记录"""
    url = f"{SUPABASE_URL}/rest/v1/user_status"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "user_id": user_id,
        "status": status,
        "last_seen": "now()"
    }
    try:
        res = httpx.post(url, headers=headers, json=data, timeout=10)
        print(f"创建状态响应: {res.status_code} - {res.text}")  # 调试用
        return res.status_code in [200, 201]
    except Exception as e:
        print(f"创建状态失败: {e}")
        return False


def update_user_status(user_id: str, status: str):
    """更新用户在线状态"""
    # 先确保记录存在
    create_user_status(user_id, status)

    url = f"{SUPABASE_URL}/rest/v1/user_status?user_id=eq.{user_id}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    data = {"status": status, "updated_at": "now()"}
    try:
        res = httpx.patch(url, headers=headers, json=data, timeout=10)
        print(f"更新状态响应: {res.status_code} - {res.text}")  # 调试用
        return res.status_code in [200, 204]
    except Exception as e:
        print(f"更新状态失败: {e}")
        return False


def update_last_seen(user_id: str):
    """更新最后在线时间"""
    url = f"{SUPABASE_URL}/rest/v1/user_status?user_id=eq.{user_id}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    data = {"last_seen": "now()"}
    try:
        res = httpx.patch(url, headers=headers, json=data, timeout=10)
        return res.status_code in [200, 204]
    except Exception as e:
        print(f"更新时间失败: {e}")
        return False