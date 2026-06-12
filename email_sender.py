import smtplib
from email.mime.text import MIMEText
from email.header import Header
import streamlit as st
import os


def get_email_config():
    try:
        return {
            "host": st.secrets["EMAIL_HOST"],
            "port": int(st.secrets["EMAIL_PORT"]),
            "user": st.secrets["EMAIL_USER"],
            "password": st.secrets["EMAIL_PASSWORD"],
            "receiver": st.secrets["EMAIL_RECEIVER"]
        }
    except:
        from dotenv import load_dotenv
        load_dotenv()
        return {
            "host": os.getenv("EMAIL_HOST"),
            "port": int(os.getenv("EMAIL_PORT", 587)),
            "user": os.getenv("EMAIL_USER"),
            "password": os.getenv("EMAIL_PASSWORD"),
            "receiver": os.getenv("EMAIL_RECEIVER")
        }


def send_feedback_email(username: str, rating: int, comment: str):
    try:
        config = get_email_config()

        subject = f"【基智反馈】{username} 评分 {rating}分"
        body = f"""
用户：{username}
评分：{rating}/10
建议：{comment if comment else '无'}
时间：{__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """

        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = Header(subject, "utf-8")
        msg["From"] = config["user"]
        msg["To"] = config["receiver"]

        server = smtplib.SMTP(config["host"], config["port"])
        server.starttls()
        server.login(config["user"], config["password"])
        server.sendmail(config["user"], [config["receiver"]], msg.as_string())
        server.quit()

        return True
    except Exception as e:
        print(f"邮件发送失败: {e}")
        return False