import os
from dotenv import load_dotenv
import httpx

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

print("URL:", SUPABASE_URL)
print("KEY:", SUPABASE_KEY[:20] if SUPABASE_KEY else "None")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ 环境变量未加载")
else:
    url = f"{SUPABASE_URL}/auth/v1/signup"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    data = {"email": "test@test.com", "password": "123456"}
    res = httpx.post(url, headers=headers, json=data)
    print("状态码:", res.status_code)
    print("返回:", res.text)