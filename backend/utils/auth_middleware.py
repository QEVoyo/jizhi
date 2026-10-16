"""
认证中间件 - FastAPI 依赖注入
从 Authorization header 中提取 JWT token 并验证用户身份

支持两种 Token：
1. Supabase JWT — 邮箱/密码登录，由 Supabase Auth 签发
2. 自签 JWT   — 微信扫码登录，由本后端签发（JWT_SECRET）
"""
from fastapi import Header, HTTPException
from config import settings
from utils.sanctions import assert_not_banned
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
            # 封禁校验必须在**每一个**认证出口上，否则被封的人只要持旧 token
            # 就照样能用（自签 JWT 是本地验证的，不查库根本发现不了）。
            await assert_not_banned(user_id)
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
            await assert_not_banned(user_id)
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


async def verify_user_match_logged(
    param_user_id: str,
    token_user_id: str,
    request=None,
    what: str = "",
) -> None:
    """
    同 verify_user_match，但把**冒充尝试**记进安全事件（security_events）。

    为什么不直接改 verify_user_match：
        它已经被约 130 处调用，改它等于全站一次性换行为，风险与收益不匹配。
        新写的、或本轮加固的接口用这个；老接口维持原样。

    为什么值得单独记一条事件：
        「请求里自报的 user_id」和「token 里的 user_id」不一致，
        在正常使用中**几乎不可能发生** —— 前端两个值本来就同源。
        所以每一条都对应一次真实的越权尝试，是本项目最干净的一个攻击信号。
        项目原有的 write 接口大量靠 body 自报身份（video_social 那一批），
        这正是攻击者最可能来碰的地方。
    """
    if param_user_id == token_user_id:
        return

    # 延迟导入：auth_middleware 被几乎所有 router 引用，
    # 顶层引入 security_log 会把它的依赖链（httpx/config/services）也拖进每次冷启动。
    from utils.security_log import (
        EVENT_IMPERSONATION, SEVERITY_HIGH, record_event,
    )
    try:
        await record_event(
            EVENT_IMPERSONATION,
            severity=SEVERITY_HIGH,
            request=request,
            user_id=token_user_id,
            status_code=403,
            detail={
                "claimed_user_id": str(param_user_id)[:64],
                "token_user_id": str(token_user_id)[:64],
                "action": what or "unknown",
            },
        )
    except Exception:
        # 记事件失败不能改变鉴权结果 —— 403 照发
        pass

    # 扣信誉分。
    # ⚠️ 分值在库里（reputation_rules 的 access.impersonation），要调改表即可；
    #    不想要这条联动的话，把那条规则 enabled 置 false 就行，不用动代码。
    #    之所以敢自动扣：已登录接口里"自报 user_id 与凭证不符"几乎没有正常场景 ——
    #    前端两个值同源。
    try:
        from utils.reputation import apply_delta
        await apply_delta(
            token_user_id, "access.impersonation",
            source_type="security",
            reason_text=f"请求自报身份与凭证不符（{what or '未标注动作'}）",
            detail={"claimed_user_id": str(param_user_id)[:64], "action": what or ""},
        )
    except Exception:
        # 同上：扣分失败不能改变鉴权结果
        pass

    raise HTTPException(status_code=403, detail="无权操作其他用户的数据")
