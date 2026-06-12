import os
import httpx
import random
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


def generate_user_account():
    """生成唯一的8位数字账号"""
    import random
    while True:
        account = str(random.randint(10000000, 99999999))  # 8位
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
    return "00000000"  # 保底账号


def sign_up(email, password, nickname=None):
    print(f"开始注册: {email}")

    # 1. 注册用户
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

    # 2. 生成账号
    user_account = generate_user_account()
    print(f"生成账号: {user_account}")

    # 3. 写入 profiles 表
    profile_url = f"{SUPABASE_URL}/rest/v1/profiles"
    profile_data = {
        "id": user_id,
        "email": email,
        "nickname": nickname if nickname else email.split("@")[0],
        "user_account": user_account
    }

    profile_res = httpx.post(profile_url, headers=headers, json=profile_data, timeout=30)
    print(f"写入 profiles: {profile_res.status_code}")
    print(f"响应内容: {profile_res.text}")

    if profile_res.status_code not in [200, 201]:
        return None, f"写入用户资料失败: {profile_res.text}"

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
        # 账号登录：查邮箱
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
        return None, res.text

    data = res.json()
    user = data.get("user", {})
    user_id = user.get("id")
    access_token = data.get("access_token")

    # 获取 user_account
    profile_url = f"{SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}"
    profile_res = httpx.get(profile_url, headers=headers)
    user_account = None
    if profile_res.status_code == 200 and profile_res.json():
        user_account = profile_res.json()[0].get("user_account")

    return {"id": user_id, "email": email, "access_token": access_token, "user_account": user_account}, None


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
    res = httpx.patch(url, headers=headers, json=data)
    return res.status_code == 200


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