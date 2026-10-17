from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from config import settings
import httpx
import base64
import io
from email.mime.image import MIMEImage
from datetime import datetime
from utils.auth_middleware import get_current_user, verify_user_match
from utils.admin_middleware import get_admin_headers
from logging_config import logger

router = APIRouter(prefix="/qa", tags=["Q&A"])


class QASubmitRequest(BaseModel):
    user_id: str
    user_email: str
    user_nickname: str
    question: str
    has_image: bool = False
    image_data: Optional[str] = None


def send_qa_email_with_image(nickname: str, email: str, question: str, image_base64: str = None):
    """发送 Q&A 邮件（HTML + 图片内嵌，发到管理员邮箱；Reply-To 指回提问人）"""
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from email.mime.image import MIMEImage
    from utils.email import smtp_send_to_admins, render_admin_email, admin_plain

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows = [
        ("提问人", nickname or "用户"),
        ("邮箱", email or "（未填写）"),
        ("提交时间", now),
    ]
    image_cid = "question_image" if image_base64 else None
    notice = "用户正在等待答复，请尽快登录管理后台处理。"
    action_url = "https://www.jizhi-learn.com/admin/qa"
    html_body = render_admin_email(
        "新的 Q&A 提问", "用户通过帮助中心提交", rows, question, "问题内容",
        image_cid=image_cid,
        accent="#7c5cff", icon="💬", badge="待回复", notice=notice,
        action_url=action_url, action_label="前往回复用户",
    )
    text_body = admin_plain("新的 Q&A 提问", rows, question, "问题内容",
                            notice=notice, action_url=action_url, action_label="前往回复用户")

    msg = MIMEMultipart("related")
    msg["Subject"] = f"【基智·待处理】新的 Q&A 提问 · 来自 {nickname or '用户'}"
    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText(text_body, "plain", "utf-8"))
    alt.attach(MIMEText(html_body, "html", "utf-8"))
    msg.attach(alt)

    # 图片内嵌（HTML 里用 cid:question_image 引用），同时也保留附件形态
    if image_base64:
        try:
            if "," in image_base64:
                image_base64 = image_base64.split(",")[1]

            image_data = base64.b64decode(image_base64)
            image = MIMEImage(image_data)
            image.add_header('Content-ID', '<question_image>')
            image.add_header('Content-Disposition', 'inline', filename='提问图片.png')
            msg.attach(image)
        except Exception as e:
            logger.info(f"图片附件添加失败: {e}")

    reply_to = email if email and "@" in email else None
    return smtp_send_to_admins(msg, reply_to=reply_to)


@router.post("/submit")
async def submit_qa_question(data: QASubmitRequest, current_user: str = Depends(get_current_user)):
    """提交Q&A问题（发邮件 + 存DB）"""
    verify_user_match(data.user_id, current_user)
    if not data.question or len(data.question) < 3:
        raise HTTPException(status_code=400, detail="问题至少3个字")

    # 存入数据库（异步，失败不影响主流程）
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Q&A 可能带图片，存图片URL到DB（图片本身已通过邮件发送）
            await client.post(
                f"{settings.SUPABASE_URL}/rest/v1/user_qa",
                headers=get_admin_headers(),
                json={
                    "user_id": data.user_id,
                    "nickname": data.user_nickname or "用户",
                    "email": data.user_email or "",
                    "question": data.question,
                    "image_url": None  # 图片通过邮件附件发送，DB只标记has_image
                }
            )
    except Exception as e:
        logger.info(f"Q&A存DB失败（不影响邮件发送）: {e}")

    success = send_qa_email_with_image(
        nickname=data.user_nickname,
        email=data.user_email,
        question=data.question,
        image_base64=data.image_data if data.has_image else None
    )

    if not success:
        raise HTTPException(status_code=500, detail="邮件发送失败，请稍后重试")

    # 告诉管理员有新提问（2026-10-07 接的消息点：原来靠人肉刷后台）
    try:
        from utils.notification import notify_admins, NotifyError
        await notify_admins("admin.new_qa", title="有新的用户提问待处理",
                            content=data.question[:40], link="/admin/qa")
    except NotifyError as e:
        logger.error(f"⚠️ 管理员待办通知失败: {e}")
    except KeyError as e:
        logger.error(f"⚠️ 管理员待办类型未注册: {e}")

    return {"success": True, "message": "问题已发送，我们会尽快回复"}