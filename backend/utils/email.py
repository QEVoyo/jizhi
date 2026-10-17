import smtplib
import html as html_lib
import httpx
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from datetime import datetime
from config import settings
from logging_config import logger


def _smtp_client():
    """阿里云 DirectMail：465 走 SSL；其它端口（如 587）走 STARTTLS。"""
    port = int(settings.EMAIL_PORT)
    if settings.EMAIL_USE_SSL or port == 465:
        return smtplib.SMTP_SSL(settings.EMAIL_HOST, port, timeout=30)
    server = smtplib.SMTP(settings.EMAIL_HOST, port, timeout=30)
    server.starttls()
    return server


def _apply_mail_headers(msg, to_email: str, reply_to: str = None):
    msg["From"] = formataddr((settings.EMAIL_FROM_NAME, settings.EMAIL_USER))
    msg["To"] = to_email
    actual_reply = reply_to or settings.EMAIL_REPLY_TO
    if actual_reply:
        msg["Reply-To"] = actual_reply


def smtp_send_message(msg, to_email: str = None, reply_to: str = None):
    """统一发信入口：验证码 / 反馈 / 举报 / Q&A / 公告都走这里。"""
    to_email = to_email or settings.EMAIL_RECEIVER
    _apply_mail_headers(msg, to_email, reply_to)
    try:
        with _smtp_client() as server:
            server.login(settings.EMAIL_USER, settings.EMAIL_PASSWORD)
            server.sendmail(settings.EMAIL_USER, to_email, msg.as_string())
        return True
    except Exception as e:
        logger.info(f"发送邮件失败: {e}")
        return False


def get_admin_emails() -> list:
    """取全部管理员的邮箱（profiles.role 或 is_admin），失败时回落 EMAIL_RECEIVER。

    逐个发送，不把多个地址塞进 To，避免管理员之间互相看到邮箱。
    """
    fallback = (settings.EMAIL_RECEIVER or "").strip()
    emails = []
    try:
        headers = {
            "apikey": settings.SUPABASE_KEY,
            "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
        }
        url = (f"{settings.SUPABASE_URL}/rest/v1/profiles"
               "?select=email,is_active"
               "&or=(role.in.(admin,super_admin),is_admin.eq.true)"
               "&limit=100")
        with httpx.Client(timeout=8.0) as client:
            res = client.get(url, headers=headers)
        if res.status_code == 200:
            for row in res.json() or []:
                email = (row.get("email") or "").strip()
                # is_active 为 null 的历史账号仍按有效处理
                if email and "@" in email and row.get("is_active") is not False:
                    emails.append(email)
        else:
            logger.info(f"取管理员邮箱失败 [{res.status_code}]，回落到 EMAIL_RECEIVER")
    except Exception as e:
        logger.info(f"取管理员邮箱异常: {e}，回落到 EMAIL_RECEIVER")

    if fallback:
        emails.append(fallback)

    seen, unique = set(), []
    for email in emails:
        key = email.lower()
        if key not in seen:
            seen.add(key)
            unique.append(email)
    return unique


def smtp_send_to_admins(msg, reply_to: str = None):
    """把同一封 MIME 消息逐个发给所有管理员。"""
    recipients = get_admin_emails()
    if not recipients:
        logger.info("管理员邮件未发送：没有可用收件人")
        return False
    ok = 0
    for email in recipients:
        if smtp_send_message(msg, email, reply_to=reply_to):
            ok += 1
        else:
            logger.info(f"管理员邮件发送失败: {email}")
    logger.info(f"管理员邮件发送成功 {ok}/{len(recipients)}")
    return ok > 0


# ===== 管理员通知邮件模板（反馈 / 举报 / Q&A）=====
BRAND = "#409EFF"
INK = "#1a1a2e"
INK2 = "#6b6f8a"
LINE = "#eef0f6"
TINT = "#f7f9ff"


def _esc(value) -> str:
    return html_lib.escape(str(value if value is not None else ""))


SITE_URL = "https://www.jizhi-learn.com"


def _tint(hex_color, alpha=0.08):
    """把主题色按比例混到白色里，返回不透明的浅色。

    邮件客户端（尤其 Outlook）对内联 rgba() 支持很差，用实色更稳。
    """
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    mix = lambda c: round(c * alpha + 255 * (1 - alpha))
    return f"#{mix(r):02x}{mix(g):02x}{mix(b):02x}"


def render_admin_email(title, subtitle, rows, content, content_label="内容", image_cid=None,
                       accent=BRAND, icon="🔔", badge="待处理", notice=None,
                       action_url=None, action_label="前往处理"):
    """统一的管理员通知 HTML：按邮件类型换主题色 + 处理提醒 + 后台入口。"""
    row_html = "".join(
        "<tr>"
        f'<td style="padding:7px 0;font-size:12.5px;color:{INK2};white-space:nowrap;'
        f'vertical-align:top;width:92px;">{_esc(k)}</td>'
        f'<td style="padding:7px 0;font-size:13px;color:{INK};line-height:1.7;'
        f'word-break:break-word;white-space:pre-wrap;">{_esc(v)}</td>'
        "</tr>"
        for k, v in rows
    )
    content_html = html_lib.escape(str(content or "")).replace("\n", "<br>") or "（无）"
    notice_text = notice or "请尽快登录管理后台查看并处理。"
    badge_bg = _tint(accent, 0.10)
    soft_bg = _tint(accent, 0.055)
    border = _tint(accent, 0.20)

    image_html = ""
    if image_cid:
        image_html = (
            '<div style="margin-top:16px;font-size:12px;color:#8c8fa7;font-weight:700;'
            'letter-spacing:1px;">附带的图片</div>'
            f'<img src="cid:{image_cid}" alt="附带图片" style="display:block;max-width:100%;'
            'margin-top:8px;border-radius:10px;border:1px solid #eef0f6;">'
        )

    action_html = ""
    if action_url:
        action_html = f"""
        <tr><td style="padding:4px 30px 24px 30px;text-align:center;">
          <table align="center" cellpadding="0" cellspacing="0" border="0"><tr>
            <td style="border-radius:10px;background-color:{accent};">
              <a href="{_esc(action_url)}" style="display:inline-block;padding:11px 32px;
                 font-size:13.5px;font-weight:600;color:#ffffff;text-decoration:none;">
                {_esc(action_label)} →
              </a>
            </td>
          </tr></table>
        </td></tr>"""

    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background-color:#f1f4f9;
             font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'PingFang SC','Microsoft YaHei',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#f1f4f9;">
    <tr><td align="center" style="padding:28px 12px;">
      <table width="600" cellpadding="0" cellspacing="0" border="0"
             style="max-width:600px;width:100%;background-color:#ffffff;border-radius:18px;
                    box-shadow:0 10px 40px rgba(24,42,80,.10);overflow:hidden;">
        <tr><td style="height:5px;line-height:5px;font-size:0;background-color:{accent};">&nbsp;</td></tr>
        <tr><td style="padding:26px 30px 4px 30px;">
          <table width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
            <td width="46" valign="top">
              <div style="width:46px;height:46px;border-radius:13px;background-color:{accent};
                          color:#ffffff;font-size:22px;text-align:center;line-height:46px;">{icon}</div>
            </td>
            <td style="padding-left:13px;">
              <div style="font-size:11.5px;color:#8c8fa7;letter-spacing:2px;">基智 · 管理通知</div>
              <div style="font-size:21px;font-weight:700;color:{INK};margin-top:5px;line-height:1.35;">{_esc(title)}</div>
              <div style="font-size:13px;color:{INK2};margin-top:5px;">{_esc(subtitle)}</div>
              <span style="display:inline-block;margin-top:8px;padding:3px 10px;border-radius:999px;
                           background-color:{badge_bg};color:{accent};font-size:11.5px;font-weight:700;">{_esc(badge)}</span>
            </td>
          </tr></table>
        </td></tr>
        <tr><td style="padding:14px 30px 0 30px;">
          <table width="100%" cellpadding="0" cellspacing="0" border="0"
                 style="background-color:{soft_bg};border:1px solid {border};border-radius:12px;">
            <tr><td style="padding:11px 14px;font-size:13px;line-height:1.65;color:{accent};">
              <b>⏰ 处理提醒</b> · {_esc(notice_text)}
            </td></tr>
          </table>
        </td></tr>
        <tr><td style="padding:14px 30px 2px 30px;">
          <table width="100%" cellpadding="0" cellspacing="0" border="0"
                 style="background-color:{soft_bg};border-radius:12px;">
            <tr><td style="padding:14px 16px;">
              <table width="100%" cellpadding="0" cellspacing="0" border="0">{row_html}</table>
            </td></tr>
          </table>
        </td></tr>
        <tr><td style="padding:12px 30px 8px 30px;">
          <div style="font-size:12px;color:#8c8fa7;font-weight:700;letter-spacing:1px;margin-bottom:7px;">{_esc(content_label)}</div>
          <div style="background-color:#fafbfe;border:1px solid {LINE};border-left:3px solid {accent};
                      border-radius:0 10px 10px 0;padding:14px 16px;font-size:13.5px;
                      line-height:1.85;color:{INK};">{content_html}</div>
          {image_html}
        </td></tr>
        {action_html}
        <tr><td style="padding:14px 30px 22px 30px;border-top:1px solid {LINE};
                       text-align:center;font-size:11px;color:#b0b4c8;">
          基智多智能体学习平台 · 本邮件由系统自动发送
        </td></tr>
      </table>
    </td></tr>
  </table>
</body></html>"""


def admin_plain(title, rows, content, content_label="内容", notice=None,
                action_url=None, action_label="前往处理"):
    lines = [title, ""]
    if notice:
        lines += [f"处理提醒：{notice}", ""]
    for k, v in rows:
        lines.append(f"{k}：{v}")
    lines += ["", f"{content_label}：", str(content or "（无）"), ""]
    if action_url:
        lines += [f"{action_label}：{action_url}", ""]
    lines += ["—— 基智多智能体学习平台"]
    return "\n".join(lines)


def send_email(subject: str, body: str, to_email: str = None, html: str = None, reply_to: str = None):
    """通用发邮件函数；传 html 时自动带 HTML + 纯文本备用。"""
    to_email = to_email or settings.EMAIL_RECEIVER
    if html:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))
        msg.attach(MIMEText(html, "html", "utf-8"))
    else:
        msg = MIMEMultipart()
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))
    return smtp_send_message(msg, to_email, reply_to=reply_to)


def send_email_to_admins(subject: str, body: str, html: str = None, reply_to: str = None):
    """给每个管理员分别发一封（反馈 / 举报等管理员通知用）。"""
    recipients = get_admin_emails()
    if not recipients:
        logger.info("管理员邮件未发送：没有可用收件人")
        return False
    ok = 0
    for email in recipients:
        if send_email(subject, body, to_email=email, html=html, reply_to=reply_to):
            ok += 1
        else:
            logger.info(f"管理员邮件发送失败: {email}")
    logger.info(f"管理员邮件发送成功 {ok}/{len(recipients)}")
    return ok > 0


def send_feedback_email(user_nickname: str, user_email: str, feedback_type: str, content: str):
    """发送意见反馈邮件（HTML，发到管理员邮箱；Reply-To 指回用户）"""
    type_map = {
        "suggestion": "💡 功能建议",
        "bug": "🐛 问题反馈",
        "feature": "✨ 功能请求",
        "other": "📝 其他"
    }
    type_label = type_map.get(feedback_type, feedback_type)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows = [
        ("反馈类型", type_label),
        ("用户昵称", user_nickname),
        ("用户邮箱", user_email),
        ("提交时间", now),
    ]
    notice = "请尽快登录管理后台查看；需要联系用户时，直接回复本邮件即可。"
    action_url = f"{SITE_URL}/admin/feedback"
    html_body = render_admin_email(
        "新的意见反馈", f"类型：{type_label}", rows, content, "反馈内容",
        accent="#0f9f8f", icon="💡", badge="待处理", notice=notice,
        action_url=action_url, action_label="前往处理反馈",
    )
    text_body = admin_plain("新的意见反馈", rows, content, "反馈内容",
                            notice=notice, action_url=action_url, action_label="前往处理反馈")
    reply_to = user_email if user_email and "@" in user_email else None
    return send_email_to_admins("【基智·待处理】新的意见反馈 · " + type_label, text_body,
                                html=html_body, reply_to=reply_to)


def send_report_email(reporter_nickname: str, target_type: str, target_id: str, reason: str, target_content: str = "", target_author: str = ""):
    """发送举报邮件（HTML，发到管理员邮箱；高优先级红色主题）"""
    type_map = {
        "post": "动态",
        "comment": "评论"
    }
    type_label = type_map.get(target_type, target_type)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows = [
        ("举报人", reporter_nickname),
        ("举报类型", type_label),
        ("目标 ID", target_id),
        ("发布者", target_author),
        ("被举报内容", target_content or "（无）"),
        ("提交时间", now),
    ]
    notice = "违规内容可能仍在传播，请在 24 小时内完成处置。"
    action_url = f"{SITE_URL}/admin/reports"
    html_body = render_admin_email(
        "新的举报", f"类型：{type_label}", rows, reason, "举报理由",
        accent="#e5484d", icon="🚨", badge="高优先级", notice=notice,
        action_url=action_url, action_label="前往处理举报",
    )
    text_body = admin_plain("新的举报", rows, reason, "举报理由",
                            notice=notice, action_url=action_url, action_label="前往处理举报")
    return send_email_to_admins("【基智·高优先级】新的举报 · " + type_label, text_body,
                                html=html_body)


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

    # 纯文本备用
    text_part = f"【基智】您的验证码是：{code}，有效期10分钟，请勿泄露。"
    msg.attach(MIMEText(text_part, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    return smtp_send_message(msg, to_email)