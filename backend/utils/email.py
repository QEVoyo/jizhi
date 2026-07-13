import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from config import settings


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
        print(f"发送邮件失败: {e}")
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