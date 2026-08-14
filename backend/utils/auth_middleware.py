"""
认证中间件 - FastAPI 依赖注入
从 Authorization header 中提取 JWT token 并验证用户身份

支持两种 Token：
1. Supabase JWT — 邮箱/密码登录，由 Supabase Auth 签发
2. 自签 JWT   — 微信扫码登录，由本后端签发（JWT_SECRET）
"""
from fastapi import Header, HTTPException
from config import settings
import httpx
import jwt


async def get_current_user(authorization: str = Header(None)) -> str:
    """
    验证 JWT token 并返回 user_id。
    优先走 Supabase 验证，失败后再尝试自签 JWT（微信登录）。
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="未登录，请先登录")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="认证格式错误")

    token = authorization.replace("Bearer ", "").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Token 为空")

    # ── 策略 1：尝试自签 JWT（微信登录 token，本地验证零延迟）──
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload.get("sub") or payload.get("user_id")
        if user_id:
            return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token 已过期，请重新登录")
    except jwt.InvalidTokenError:
        pass  # 不是自签 JWT，继续走 Supabase 验证

    # ── 策略 2：Supabase 验证（邮箱登录 token）──
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {token}",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            res = await client.get(
                f"{settings.SUPABASE_URL}/auth/v1/user",
                headers=headers
            )
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"认证服务不可用: {str(e)}")

        if res.status_code != 200:
            raise HTTPException(status_code=401, detail="Token 无效或已过期，请重新登录")

        try:
            user_data = res.json()
            user_id = user_data.get("id")
            if not user_id:
                raise HTTPException(status_code=401, detail="无法获取用户信息")
            return user_id
        except Exception:
            raise HTTPException(status_code=401, detail="Token 解析失败")


def verify_user_match(param_user_id: str, token_user_id: str) -> None:
    """
    验证请求参数中的 user_id 是否与 token 中的 user_id 一致。
    如果不一致，抛出 403 异常。
    """
    if param_user_id != token_user_id:
        raise HTTPException(
            status_code=403,
            detail="无权操作其他用户的数据"
        )
