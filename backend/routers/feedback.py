from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from config import settings
from utils.email import send_feedback_email

router = APIRouter(prefix="/feedback", tags=["反馈"])


class FeedbackSubmit(BaseModel):
    user_id: str
    user_email: str
    user_nickname: str
    type: str
    content: str


@router.post("/submit")
async def submit_feedback(data: FeedbackSubmit):
    """提交意见反馈"""
    if not data.content or len(data.content) < 10:
        raise HTTPException(status_code=400, detail="内容至少10个字")

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