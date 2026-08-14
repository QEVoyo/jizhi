import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from config import settings
from logging_config import logger


def send_email(subject: str, body: str, to_email: str = None):
    """通用发邮件函数"""
    if to_email is None:
        to_email = settings.EMAIL_RECEIVER

    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = settings.EMAIL_USER
    msg["To"] = to_email
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
            server.starttls()
            server.login(settings.EMAIL_USER, settings.EMAIL_PASSWORD)
            server.sendmail(settings.EMAIL_USER, to_email, msg.as_string())
        return True
    except Exception as e:
        logger.info(f"发送邮件失败: {e}")
        return False


def send_feedback_email(user_nickname: str, user_email: str, feedback_type: str, content: str):
    """发送意见反馈邮件"""
    type_map = {
        "suggestion": "💡 功能建议",
        "bug": "🐛 问题反馈",
        "feature": "✨ 功能请求",
        "other": "📝 其他"
    }
    type_label = type_map.get(feedback_type, feedback_type)

    body = f"""
收到新的意见反馈：

反馈类型：{type_label}
用户昵称：{user_nickname}
用户邮箱：{user_email}
时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

反馈内容：
{content}
    """
    return send_email("【意见反馈】" + type_label, body)


def send_report_email(reporter_nickname: str, target_type: str, target_id: str, reason: str, target_content: str = "", target_author: str = ""):
    """发送举报邮件"""
    type_map = {
        "post": "动态",
        "comment": "评论"
    }
    type_label = type_map.get(target_type, target_type)

    body = f"""
收到新的举报：

举报人：{reporter_nickname}
举报类型：{type_label}
被举报内容：{target_content}
发布者：{target_author}
目标ID：{target_id}
时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

举报理由：
{reason}
    """
    return send_email("【举报通知】" + type_label + " 被举报", body)


def send_verification_code_email(to_email: str, code: str):
    """发送邮箱验证码（精美HTML版）"""
    subject = "【基智】邮箱验证码"

    # HTML 正文
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>验证码邮件</title>
    </head>
    <body style="margin:0; padding:0; background-color:#f5f7fa; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 520px; margin: 0 auto; background-color: #ffffff; border-radius: 20px; box-shadow: 0 8px 40px rgba(0,0,0,0.06);">
            <tr>
                <td style="padding: 40px 36px 30px 36px; text-align: center; border-bottom: 2px solid #f0f2f5;">
                    <!-- Logo + 品牌名 -->
                    <table align="center" border="0" cellpadding="0" cellspacing="0">
                        <tr>
                            <td style="padding-right: 12px;">
                                <img src="https://jizhi-learn.com/logo.png" alt="基智" width="40" height="40" style="display: block; border-radius: 10px;">
                            </td>
                            <td style="font-size: 24px; font-weight: 700; color: #1a1a2e; letter-spacing: 1px;">
                                基智
                            </td>
                        </tr>
                    </table>
                    <p style="margin: 6px 0 0 0; font-size: 14px; color: #8c8fa7; letter-spacing: 2px;">多智能体学习助手</p >
                </td>
            </tr>
            <tr>
                <td style="padding: 36px 36px 28px 36px;">
                    <h2 style="margin: 0 0 8px 0; font-size: 20px; font-weight: 600; color: #1a1a2e; text-align: center;">
                        邮箱验证码
                    </h2>
                    <p style="margin: 0 0 24px 0; font-size: 14px; color: #6b6f8a; text-align: center; line-height: 1.6;">
                        您正在注册基智学习助手账号，请使用以下验证码完成验证。
                    </p >

                    <!-- 验证码区域 -->
                    <table align="center" border="0" cellpadding="0" cellspacing="0" style="background: #f7f8fc; border-radius: 16px; width: 100%;">
                        <tr>
                            <td style="padding: 20px 0; text-align: center;">
                                <span style="font-size: 36px; font-weight: 700; color: #4a6cf7; letter-spacing: 12px; font-family: 'Courier New', monospace;">
                                    {code}
                                </span>
                            </td>
                        </tr>
                    </table>

                    <p style="margin: 20px 0 0 0; font-size: 13px; color: #8c8fa7; text-align: center; line-height: 1.6;">
                        ⏱ 验证码有效期为 <strong style="color: #4a6cf7;">10 分钟</strong>
                        <br>
                        请勿将验证码透露给他人，如非本人操作请忽略此邮件。
                    </p >
                </td>
            </tr>
            <tr>
                <td style="padding: 20px 36px 32px 36px; text-align: center; border-top: 1px solid #f0f2f5;">
                    <p style="margin: 0 0 4px 0; font-size: 12px; color: #b0b4c8;">
                        基智学习助手 · 让学习更有趣
                    </p >
                    <p style="margin: 0; font-size: 11px; color: #cdd0e0;">
                        © 2026 基智 · 本邮件由系统自动发送，请勿回复
                    </p >
                </td>
            </tr>
        </table>
        <!-- 底部提醒 -->
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 520px; margin: 10px auto 0;">
            <tr>
                <td style="padding: 0 36px; text-align: center;">
                    <p style="margin: 0; font-size: 11px; color: #c5c8d8;">
                        如果收件箱未找到邮件，请检查垃圾邮件文件夹
                    </p >
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    # 改用 HTML 格式发送
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.EMAIL_USER
    msg["To"] = to_email

    # 纯文本备用
    text_part = f"【基智】您的验证码是：{code}，有效期10分钟，请勿泄露。"
    msg.attach(MIMEText(text_part, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
            server.starttls()
            server.login(settings.EMAIL_USER, settings.EMAIL_PASSWORD)
            server.sendmail(settings.EMAIL_USER, to_email, msg.as_string())
        return True
    except Exception as e:
        logger.info(f"发送邮件失败: {e}")
        return False