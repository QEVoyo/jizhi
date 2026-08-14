"""
管理员鉴权中间件 — 三级角色体系
  super_admin: 超级管理员，可管理其他管理员
  admin:       管理员，可管理用户和内容
  user:        普通用户
"""
from fastapi import HTTPException, Depends
from config import settings
from utils.auth_middleware import get_current_user
import httpx


async def get_current_admin(current_user: str = Depends(get_current_user)) -> str:
    """验证当前用户是否为管理员（admin 或 super_admin），是则返回 user_id，否则 403"""
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        res = await client.get(
            f"{settings.SUPABASE_URL}/rest/v1/profiles?id=eq.{current_user}&select=role,is_admin",
            headers=headers
        )
        if res.status_code != 200:
            raise HTTPException(status_code=503, detail="无法验证管理员身份")
        data = res.json()
        if not data:
            raise HTTPException(status_code=403, detail="无权访问管理后台")
        role = data[0].get("role", "")
        is_admin = data[0].get("is_admin", False)
        # 兼容旧 is_admin 字段和新 role 字段
        if role not in ("admin", "super_admin") and not is_admin:
            raise HTTPException(status_code=403, detail="无权访问管理后台")
    return current_user


async def get_current_super_admin(current_user: str = Depends(get_current_user)) -> str:
    """验证当前用户是否为超级管理员，是则返回 user_id，否则 403"""
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        res = await client.get(
            f"{settings.SUPABASE_URL}/rest/v1/profiles?id=eq.{current_user}&select=role,is_admin",
            headers=headers
        )
        if res.status_code != 200:
            raise HTTPException(status_code=503, detail="无法验证超级管理员身份")
        data = res.json()
        if not data or data[0].get("role") != "super_admin":
            raise HTTPException(status_code=403, detail="需要超级管理员权限")
    return current_user


def get_admin_headers():
    """获取使用 service_role key 的请求头（绕过 RLS）"""
    return {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json"
    }


async def write_audit_log(admin_id: str, action: str, target_type: str = "",
                          target_id: str = "", detail: dict = None):
    """写入管理员操作日志（非阻塞，失败不影响主流程）"""
    import json
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            nick = ""
            try:
                r = await client.get(
                    f"{settings.SUPABASE_URL}/rest/v1/profiles?id=eq.{admin_id}&select=nickname",
                    headers=get_admin_headers()
                )
                if r.status_code == 200 and r.json():
                    nick = r.json()[0].get("nickname", "")
            except Exception:
                pass

            await client.post(
                f"{settings.SUPABASE_URL}/rest/v1/admin_audit_logs",
                headers=get_admin_headers(),
                json={
                    "admin_id": admin_id,
                    "admin_nickname": nick,
                    "action": action,
                    "target_type": target_type,
                    "target_id": str(target_id) if target_id else "",
                    "detail": detail or {}
                }
            )
    except Exception:
        pass
