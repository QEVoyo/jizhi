import os
import httpx
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def sign_up(email, password, nickname=None):
    url = f"{SUPABASE_URL}/auth/v1/signup"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    data = {"email": email, "password": password}

    res = httpx.post(url, headers=headers, json=data)
    if res.status_code == 200:
        return {"email": email, "id": email}, None  # 直接用邮箱当 id
    return None, res.text

def sign_in(email, password):
    url = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    data = {"email": email, "password": password}
    res = httpx.post(url, headers=headers, json=data)

    if res.status_code == 200:
        # 直接返回邮箱当用户标识，不用管 Supabase 的 id
        return {"id": email, "email": email}, None
    return None, res.text

def get_user_nickname(user_id):
    return None  # 暂时不用