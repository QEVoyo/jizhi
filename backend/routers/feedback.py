from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from config import settings
from utils.email import send_feedback_email
from utils.auth_middleware import get_current_user, verify_user_match
from utils.admin_middleware import get_admin_headers
import httpx
from logging_config import logger

router = APIRouter(prefix="/feedback", tags=["反馈"])


class FeedbackSubmit(BaseModel):
    user_id: str
    user_email: str
    user_nickname: str
    type: str
    content: str


@router.post("/submit")
async def submit_feedback(data: FeedbackSubmit, current_user: str = Depends(get_current_user)):
    """提交意见反馈（发邮件 + 存DB）"""
    verify_user_match(data.user_id, current_user)
    if not data.content or len(data.content) < 10:
        raise HTTPException(status_code=400, detail="内容至少10个字")

    # 存入数据库（异步，失败不影响主流程）
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(
                f"{settings.SUPABASE_URL}/rest/v1/user_feedback",
                headers=get_admin_headers(),
                json={
                    "user_id": data.user_id,
                    "nickname": data.user_nickname or "用户",
                    "email": data.user_email or "",
                    "feedback_type": data.type,
                    "content": data.content
                }
            )
    except Exception as e:
        logger.info(f"反馈存DB失败（不影响邮件发送）: {e}")

    # 发邮件
    success = send_feedback_email(
        user_nickname=data.user_nickname or "用户",
        user_email=data.user_email or "未提供邮箱",
        feedback_type=data.type,
        content=data.content
    )

    if not success:
        raise HTTPException(status_code=500, detail="邮件发送失败，请稍后重试")

    return {"success": True, "message": "感谢反馈！我们会认真对待每一条建议 💪"}