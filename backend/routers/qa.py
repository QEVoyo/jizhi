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
    """发送Q&A邮件（带图片附件）"""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from email.mime.image import MIMEImage

    msg = MIMEMultipart()
    msg["Subject"] = f"【Q&A提问】来自 {nickname}"
    msg["From"] = settings.EMAIL_USER
    msg["To"] = settings.EMAIL_RECEIVER

    body = f"""
收到新的Q&A提问：

提问人：{nickname}
邮箱：{email}
用户ID：{''}
时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

问题内容：
{question}

{'📎 附带了图片（见附件）' if image_base64 else ''}

---
请回复此邮件解答用户问题。
"""
    msg.attach(MIMEText(body, "plain", "utf-8"))

    # 如果有图片，解码并作为附件添加
    if image_base64:
        try:
            # 去掉 data:image/png;base64, 前缀
            if "," in image_base64:
                image_base64 = image_base64.split(",")[1]

            image_data = base64.b64decode(image_base64)
            image = MIMEImage(image_data)
            image.add_header('Content-Disposition', 'attachment', filename='提问图片.png')
            msg.attach(image)
        except Exception as e:
            logger.info(f"图片附件添加失败: {e}")

    try:
        with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
            server.starttls()
            server.login(settings.EMAIL_USER, settings.EMAIL_PASSWORD)
            server.sendmail(settings.EMAIL_USER, settings.EMAIL_RECEIVER, msg.as_string())
        return True
    except Exception as e:
        logger.info(f"发送邮件失败: {e}")
        return False


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

    return {"success": True, "message": "问题已发送，我们会尽快回复"}