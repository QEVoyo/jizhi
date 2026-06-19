import streamlit as st
import os
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import re
import time
import tempfile
import random
from agents.planner import plan
from agents.generator import generate
from agents.evaluator import evaluate
from memory import UserMemory
from session_manager import SessionManager
from checkin import CheckInManager
from mistakes import MistakeManager
from learning_log import LearningLogManager
from countdown import CountdownManager
from timer import TimerManager
from intent import detect_intent
from utils.llm_client import call_llm
from utils.email_sender import send_feedback_email
from utils.title_generator import generate_mistake_title
from dotenv import load_dotenv
from utils.name_generator import generate_random_name
# 阿里云百炼多模态
import dashscope
import requests
import time
# 后端 API 地址
BACKEND_URL = "https://hearty-playfulness-production-78c1.up.railway.app"
from datetime import datetime
@st.cache_data(ttl=60, show_spinner=False)
def get_learning_logs_via_backend(user_id, access_token):
    """获取学习日志"""
    try:
        response = requests.get(
            f"{BACKEND_URL}/tools/learning-logs/{user_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        if response.status_code == 200:
            return response.json().get("logs", []), None
        return [], response.json().get("detail", "获取失败")
    except Exception as e:
        return [], str(e)

def clear_learning_logs_via_backend(user_id, access_token):
    """清空学习日志"""
    try:
        response = requests.delete(
            f"{BACKEND_URL}/tools/learning-logs/{user_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        return response.status_code == 200
    except:
        return False

def login_via_backend(login_input, password):
    """通过后端 API 登录"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/auth/login",
            json={"login_input": login_input, "password": password},
            timeout=10
        )
        if response.status_code == 200:
            return response.json(), None
        else:
            error = response.json().get("detail", "登录失败")
            return None, error
    except requests.exceptions.ConnectionError:
        return None, "无法连接到服务器，请确保后端已启动"
    except Exception as e:
        return None, str(e)
load_dotenv()

def register_via_backend(email, password, nickname):
    """通过后端 API 注册"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/auth/register",
            json={"email": email, "password": password, "nickname": nickname},
            timeout=10
        )
        if response.status_code == 200:
            return response.json(), None
        else:
            error = response.json().get("detail", "注册失败")
            return None, error
    except requests.exceptions.ConnectionError:
        return None, "无法连接到服务器，请确保后端已启动"
    except Exception as e:
        return None, str(e)


def get_profile_via_backend(user_id, access_token):
    """通过后端 API 获取用户资料"""
    try:
        response = requests.get(
            f"{BACKEND_URL}/auth/profile/{user_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        if response.status_code == 200:
            return response.json(), None
        else:
            error = response.json().get("detail", "获取资料失败")
            return None, error
    except requests.exceptions.ConnectionError:
        return None, "无法连接到服务器"
    except Exception as e:
        return None, str(e)

def update_nickname_via_backend(user_id, nickname, access_token):
    """通过后端 API 更新昵称"""
    try:
        response = requests.put(
            f"{BACKEND_URL}/auth/update-nickname",
            json={"user_id": user_id, "nickname": nickname},
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        if response.status_code == 200:
            return response.json(), None
        else:
            error = response.json().get("detail", "更新失败")
            return None, error
    except requests.exceptions.ConnectionError:
        return None, "无法连接到服务器"
    except Exception as e:
        return None, str(e)

def chat_via_backend(messages, user_id, temperature=0.7):
    """通过后端 API 发送消息（流式）"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/chat/send",
            json={"messages": messages, "user_id": user_id, "temperature": temperature},
            stream=True,
            timeout=60
        )
        return response
    except Exception as e:
        return None

def save_log_via_backend(user_id, keyword):
    """保存学习日志"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/tools/learning-logs/{user_id}",
            json={"keyword": keyword, "date": datetime.now().strftime("%Y-%m-%d")},
            timeout=10
        )
        return response.status_code == 200
    except Exception as e:
        print(f"保存日志失败: {e}")
        return False

@st.cache_data(ttl=60, show_spinner=False)
def get_checkin_via_backend(user_id, access_token):
    """获取打卡数据"""
    try:
        response = requests.get(
            f"{BACKEND_URL}/tools/checkin/{user_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        if response.status_code == 200:
            return response.json().get("projects", []), None
        return [], response.json().get("detail", "获取失败")
    except Exception as e:
        return [], str(e)

def save_checkin_via_backend(user_id, projects, access_token):
    """保存打卡数据"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/tools/checkin/{user_id}",
            json={"projects": projects},
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        return response.status_code == 200
    except:
        return False

# 倒计时
@st.cache_data(ttl=60, show_spinner=False)
def get_countdown_via_backend(user_id, access_token):
    try:
        response = requests.get(
            f"{BACKEND_URL}/tools/countdown/{user_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        if response.status_code == 200:
            return response.json().get("events", []), None
        return [], response.json().get("detail", "获取失败")
    except Exception as e:
        return [], str(e)

def save_countdown_via_backend(user_id, events, access_token):
    try:
        response = requests.post(
            f"{BACKEND_URL}/tools/countdown/{user_id}",
            json={"events": events},
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        return response.status_code == 200
    except:
        return False

# 计时器
@st.cache_data(ttl=60, show_spinner=False)
def get_timer_via_backend(user_id, access_token):
    try:
        response = requests.get(
            f"{BACKEND_URL}/tools/timer/{user_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        if response.status_code == 200:
            return response.json().get("timers", []), None
        return [], response.json().get("detail", "获取失败")
    except Exception as e:
        return [], str(e)

def save_timer_via_backend(user_id, timers, access_token):
    try:
        response = requests.post(
            f"{BACKEND_URL}/tools/timer/{user_id}",
            json={"timers": timers},
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        return response.status_code == 200
    except:
        return False

def get_report_via_backend(user_id, access_token):
    try:
        response = requests.get(
            f"{BACKEND_URL}/tools/report/{user_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        if response.status_code == 200:
            return response.json(), None
        return None, response.json().get("detail", "获取失败")
    except Exception as e:
        return None, str(e)

dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")


def analyze_image(image_bytes, prompt="请描述这张图片的内容"):
    try:
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
            tmp_file.write(image_bytes)
            tmp_path = tmp_file.name
        from dashscope import MultiModalConversation
        messages = [{"role": "user", "content": [{"image": f"file://{tmp_path}"}, {"text": prompt}]}]
        response = MultiModalConversation.call(model="qwen-vl-plus", messages=messages)
        os.unlink(tmp_path)
        if response.status_code == 200:
            return response.output.choices[0].message.content[0]["text"]
        else:
            return f"图片分析失败: {response.message}"
    except Exception as e:
        return f"调用失败: {str(e)}"


st.set_page_config(page_title="主界面", page_icon="🏠", layout="wide", initial_sidebar_state="auto")


def show_login_page():
    st.markdown("""
    <style>
        .stApp header { display: none; }
        .main .block-container {
            padding-top: 30px;
            max-width: 500px;
            margin: 0 auto;
        }
        /* 输入框样式（跟随主题） */
        .stTextInput label, .stSelectbox label {
            font-weight: 500;
        }
        /* 按钮圆角 */
        .stButton button {
            border-radius: 12px;
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<h1><i class="fas fa-graduation-cap"></i> 基智 · 多智能体学习助手</h1>', unsafe_allow_html=True)
    st.markdown("### 学习从账号开始")

    # 控制跳转的变量
    if "switch_to_login" not in st.session_state:
        st.session_state.switch_to_login = False
    if "auto_email" not in st.session_state:
        st.session_state.auto_email = ""

    # 强制刷新到登录 Tab
    if st.session_state.switch_to_login:
        st.session_state.switch_to_login = False
        st.query_params["tab"] = "login"
        st.rerun()

    query_tab = st.query_params.get("tab", ["login"])[0]
    tab_index = 0 if query_tab == "login" else 1

    tab1, tab2 = st.tabs(["🔐 登录", "📝 注册"])

    if tab_index == 1:
        st.markdown("""
        <script>
        setTimeout(() => {
            const btns = parent.document.querySelectorAll('button[data-baseweb="tab"]');
            if (btns.length > 1) btns[1].click();
        }, 100);
        </script>
        """, unsafe_allow_html=True)

    # ========= 登录 Tab =========
    with tab1:
        with st.form("login_form"):
            login_input = st.text_input("账号 / 邮箱", placeholder="请输入账号或邮箱")
            password = st.text_input("密码", type="password")
            submitted = st.form_submit_button("登录", use_container_width=True)

            if submitted:
                if not login_input or not password:
                    st.warning("请输入账号/邮箱和密码")
                else:
                    user, err = login_via_backend(login_input, password)
                    if user:
                        # 登录成功
                        user_email = user.get("email")
                        user_id = user.get("id")
                        user_account = user.get("user_account")
                        # ... 现有代码 ...
                        # 设置在线状态
                        from utils.auth import update_user_status
                        update_user_status(user_id, "online")

                        st.session_state.logged_in = True
                        st.session_state.user_email = user_email
                        st.session_state.user_id = user_id
                        st.session_state.user_account = user_account
                        st.session_state.access_token = user.get("access_token")
                        # 从数据库读取昵称，若没有则用邮箱前缀
                        st.session_state.username = user.get("nickname") or user_email.split("@")[0]

                        # 初始化 Manager
                        from session_manager import SessionManager
                        from memory import UserMemory
                        from checkin import CheckInManager
                        from mistakes import MistakeManager
                        from learning_log import LearningLogManager
                        from countdown import CountdownManager
                        from timer import TimerManager

                        st.session_state.session_mgr = SessionManager(user_id=user_id)
                        st.session_state.user_memory = UserMemory(user_id=user_id)
                        #st.session_state.checkin_manager = CheckInManager(user_id=user_id)
                        st.session_state.mistake_manager = MistakeManager(user_id=user_id)
                        st.session_state.learning_log_manager = LearningLogManager(user_id=user_id)
                        #st.session_state.countdown_manager = CountdownManager(user_id=user_id)
                        #st.session_state.timer_manager = TimerManager(user_id=user_id)
                        projects, err = get_checkin_via_backend(user_id, st.session_state.access_token)
                        st.session_state.checkin_projects = projects if projects else []

                        events, err = get_countdown_via_backend(user_id, st.session_state.access_token)
                        st.session_state.countdown_events = events if events else []

                        timers, err = get_timer_via_backend(user_id, st.session_state.access_token)
                        st.session_state.timer_items = timers if timers else []

                        logs, err = get_learning_logs_via_backend(user_id, st.session_state.access_token)
                        st.session_state.learning_logs = logs if logs else []

                        # 创建新对话
                        new_id = st.session_state.session_mgr.create_session(title="新对话")
                        st.session_state.session_mgr.switch_session(new_id)
                        st.session_state.messages = []

                        st.rerun()
                    else:
                        # 友好错误提示
                        error_msg = str(err) if err else "登录失败"
                        # 解析常见错误
                        if "Invalid login credentials" in error_msg:
                            st.error("账号/邮箱或密码错误")
                        elif "Email not confirmed" in error_msg:
                            st.warning("邮箱尚未验证，请先去邮箱点击验证链接")
                        elif "账号不存在" in error_msg:
                            st.error("账号不存在")
                        else:
                            st.error("登录失败，请稍后重试")

    # ========= 注册 Tab =========
    with tab2:
        with st.form("register_form"):
            email = st.text_input("邮箱", placeholder="example@domain.com", key="reg_email")
            password = st.text_input("密码", type="password", key="reg_pwd")
            confirm = st.text_input("确认密码", type="password", key="reg_confirm")
            submitted = st.form_submit_button("注册", use_container_width=True)

            if submitted:
                # 邮箱格式校验
                import re
                def is_valid_email(email):
                    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
                    return re.match(pattern, email) is not None

                if not email or not password:
                    st.warning("请填写邮箱和密码")
                elif not is_valid_email(email):
                    st.warning("邮箱格式不正确，请输入如：name@example.com")
                elif len(password) < 6:
                    st.warning("密码长度至少为 6 位")
                elif password != confirm:
                    st.warning("两次密码不一致")
                else:
                    from utils.name_generator import generate_random_name
                    final_nickname = generate_random_name()
                    user, err = register_via_backend(email, password, final_nickname)  # 改这里

                    if user:
                        st.success("验证邮件已发送，请查收邮箱并点击验证链接。\n\n登录后可在「个人中心」查看你的专属账号。")
                    elif err and "already registered" in err.lower():
                        st.warning("该邮箱已注册，请直接登录")
                    else:
                        st.error(f"注册失败：{err}")

def parse_scores_from_text(text):
    scores = {}
    patterns = [r'([\u4e00-\u9fa5]{2,6})(?:成绩|：|:|\s)*(\d{1,3})', r'(\d{1,3})\s*分?\s*([\u4e00-\u9fa5]{2,6})']
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if len(match) == 2:
                if match[0].isdigit():
                    scores[match[1]] = int(match[0])
                else:
                    scores[match[0]] = int(match[1])
    return scores


def generate_chart(scores, chart_type="bar"):
    if not scores:
        return None
    subjects = list(scores.keys())
    values = list(scores.values())
    fig, ax = plt.subplots(figsize=(8, 5))
    if chart_type == "bar":
        bars = ax.bar(subjects, values, color=['#4ecdc4', '#6c63ff', '#ff6b6b', '#ffd93d', '#a8e6cf'])
        ax.set_ylim(0, 105)
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 2, str(val), ha='center', va='bottom',
                    fontsize=12)
    else:
        ax.plot(subjects, values, marker='o', linewidth=2, markersize=8, color='#6c63ff')
        ax.set_ylim(0, 105)
        for i, val in enumerate(values):
            ax.text(i, val + 2, str(val), ha='center', fontsize=12)
    ax.set_ylabel('分数', fontsize=12)
    ax.set_title('成绩分析图', fontsize=14, fontweight='bold')
    ax.set_ylim(0, 105)
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=100, bbox_inches='tight', facecolor='#1e1e2e', edgecolor='none')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode()
    plt.close(fig)
    return f"data:image/png;base64,{img_base64}"
st.markdown("""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
""", unsafe_allow_html=True)
st.markdown("""
<style>
    /* 移动端适配 */
    @media (max-width: 768px) {
        .main .block-container {
            padding-left: 0.5rem;
            padding-right: 0.5rem;
            padding-top: 0.5rem;
        }
        .stChatMessage {
            font-size: 14px !important;
        }
        .stChatInput textarea {
            font-size: 14px !important;
            padding: 8px 12px !important;
        }
        button {
            font-size: 12px !important;
            padding: 4px 8px !important;
        }
        [data-testid="stSidebar"] {
            width: 250px !important;
        }
        h1 {
            font-size: 1.5rem !important;
        }
        h2 {
            font-size: 1.2rem !important;
        }
        h3 {
            font-size: 1rem !important;
        }
        .stPopover {
            width: 90% !important;
            left: 5% !important;
        }
        .stTabs [data-baseweb="tab-list"] button {
            font-size: 12px !important;
            padding: 4px 8px !important;
        }
        .stImage img {
            max-width: 60px !important;
        }
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<script>
function scrollToBottom() {
    const msgs = parent.document.querySelectorAll('.stChatMessage');
    if(msgs.length) msgs[msgs.length-1].scrollIntoView({ behavior: 'smooth', block: 'end' });
}
window.addEventListener('load', scrollToBottom);
setTimeout(scrollToBottom, 200);
</script>
""", unsafe_allow_html=True)

# ========== 初始化 ==========
# 登录状态
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_id" not in st.session_state:
    st.session_state.user_id = ""
if "user_email" not in st.session_state:
    st.session_state.user_email = ""

# 原有 Manager（登录后赋值）
if "session_mgr" not in st.session_state:
    st.session_state.session_mgr = None
if "user_memory" not in st.session_state:
    st.session_state.user_memory = None
if "checkin_manager" not in st.session_state:
    st.session_state.checkin_manager = None
if "mistake_manager" not in st.session_state:
    st.session_state.mistake_manager = None
if "learning_log_manager" not in st.session_state:
    st.session_state.learning_log_manager = None
if "countdown_manager" not in st.session_state:
    st.session_state.countdown_manager = None
if "timer_manager" not in st.session_state:
    st.session_state.timer_manager = None

# UI 状态
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_images" not in st.session_state:
    st.session_state.current_images = []
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0
if "language" not in st.session_state:
    st.session_state.language = "中文"
if "username" not in st.session_state:
    st.session_state.username = ""
if "image_type" not in st.session_state:
    st.session_state.image_type = "📝 题目/笔记"
if "review_question" not in st.session_state:
    st.session_state.review_question = None
if "current_title_edit" not in st.session_state:
    st.session_state.current_title_edit = None
if "pending_timer_log" not in st.session_state:
    st.session_state.pending_timer_log = None

# ===== 保底：确保当前对话存在 + 自动生成标题（保留你原有的）=====
if st.session_state.session_mgr is not None and st.session_state.session_mgr.get_current_session() is None and st.session_state.messages:
    first_user_msg = ""
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            first_user_msg = msg["content"][:80]
            break

    if first_user_msg:
        title_prompt = f"请为以下学习问题生成一个简短的标题（不超过15字）：{first_user_msg}"
        try:
            new_title = call_llm([{"role": "user", "content": title_prompt}], temperature=0.5)
        except:
            new_title = "新对话"
    else:
        new_title = "新对话"

    new_id = st.session_state.session_mgr.create_session(title=new_title)
    st.session_state.session_mgr.switch_session(new_id)

    for msg in st.session_state.messages:
        st.session_state.session_mgr.add_message(msg["role"], msg["content"])
    st.session_state.session_mgr._save()
    st.rerun()
# ========== 登录检查（必须放在最前面）==========
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    show_login_page()
    st.stop()
# ========== 双语文本定义 ==========
texts = {
    "中文": {
        "switch_user": "🔄 切换用户",
        "feature_title": "✨ 功能介绍",
        "feature_content": """
        **🎓 基智 · 多智能体学习系统**

        由**三个智能体协作**的个性化学习助手：

        - **📋 规划Agent** — 拆解知识点，规划学习路径
        - **📖 生成Agent** — 生成个性化讲解、例子、练习题
        - **🔍 评估Agent** — 评估质量，自动调整难度

        **🎯 核心能力：**
        - ✅ 多智能体协作
        - ✅ 个性化学习 + 自适应难度
        - ✅ 图片理解
        - ✅ 对话记忆
        - ✅ 成绩可视化

        **📅 学习打卡** — 自定义项目，追踪进度
        **📝 学习日志** — 自动记录学过的知识点
        **📖 错题本** — 自动/手动收录，成长报告

        💡 试试说："帮我规划Python学习路径"、"解释一下列表推导式"
        """,
        "team_title": "🏆 团队详情",
        "team_content": """
        **广州软件学院 · KFC 团队**

        参赛题目：A3-基于大模型的个性化资源生成与学习多智能体系统开发

        **团队成员**
        - 欧阳嘉誉（队长）
        - 许钰婷（队员）
        """,
        "upload_images": "📷 上传图片",
        "upload_hint": "支持 PNG、JPG、JPEG，可多张",
        "pref_title": "🎛️ 偏好设置",
        "difficulty": "难度",
        "style": "风格",
        "difficulty_levels": {"初级": "beginner", "中等": "intermediate", "高级": "advanced"},
        "style_levels": {"多举例": "example_heavy", "多理论": "theory_heavy", "均衡": "balanced"},
        "profile_title": "📝 学习档案",
        "main_title": "🎓 基智 · 多智能体学习助手",
        "main_caption": "多智能体协作 | 个性化学习 | 图片理解 | 成绩可视化 | 自适应难度",
        "chat_placeholder": "例如：解释列表推导式、帮我规划Python学习路径...",
        "intent_plan": "📋 规划Agent 工作中...",
        "intent_generate": "📖 生成Agent 工作中...",
        "intent_evaluate": "🔍 评估Agent 工作中...",
        "intent_chat": "💬 对话模式 工作中...",
        "intent_complete": "✅ 完成",
        "error_no_content": "没有可评估的内容",
        "error_process": "处理出错",
        "feedback_title": "📝 使用体验反馈",
        "feedback_name": "你的称呼（可选）",
        "feedback_name_placeholder": "例如：张三",
        "feedback_slider": "整体满意度（1-10分）",
        "feedback_placeholder": "欢迎提出改进意见...",
        "feedback_submit": "提交反馈",
        "feedback_success": "感谢反馈！",
        "clear_chat": "🗑️ 清空当前对话"
    },
    "English": {
        "switch_user": "🔄 Switch User",
        "feature_title": "✨ Features",
        "feature_content": """
        **🎓 JiZhi · Multi-Agent Learning System**

        Personalized learning assistant powered by **three collaborative agents**:

        - **📋 Planning Agent** — Decompose knowledge points, plan learning paths
        - **📖 Generation Agent** — Generate personalized explanations, examples, exercises
        - **🔍 Evaluation Agent** — Evaluate quality, auto-adjust difficulty

        **🎯 Core Capabilities:**
        - ✅ Multi-Agent Collaboration
        - ✅ Personalized Learning + Adaptive Difficulty
        - ✅ Image Understanding
        - ✅ Conversation Memory
        - ✅ Score Visualization

        **📅 Check-in** — Custom projects, track progress
        **📝 Learning Log** — Auto-record learned knowledge
        **📖 Mistake Book** — Auto/manual collection, growth report

        💡 Try saying: "Help me plan my Python learning path", "Explain list comprehension"
        """,
        "team_title": "🏆 Team Info",
        "team_content": """
        **Guangzhou Software Institute · KFC Team**

        Project: A3 - Personalized Resource Generation & Multi-Agent Learning System based on LLM

        **Team Members**
        - Ouyang Jiayu (Leader)
        - Xu Yuting (Member)
        """,
        "upload_images": "📷 Upload Images",
        "upload_hint": "PNG, JPG, JPEG, multiple allowed",
        "pref_title": "🎛️ Preferences",
        "difficulty": "Difficulty",
        "style": "Style",
        "difficulty_levels": {"Beginner": "beginner", "Intermediate": "intermediate", "Advanced": "advanced"},
        "style_levels": {"Example-heavy": "example_heavy", "Theory-heavy": "theory_heavy", "Balanced": "balanced"},
        "profile_title": "📝 Learning Profile",
        "main_title": "🎓 JiZhi · Multi-Agent Learning Assistant",
        "main_caption": "Multi-Agent Collaboration | Personalized Learning | Image Understanding | Score Visualization | Adaptive Difficulty",
        "chat_placeholder": "e.g., Explain list comprehension, plan my Python learning path...",
        "intent_plan": "📋 Planning Agent working...",
        "intent_generate": "📖 Generation Agent working...",
        "intent_evaluate": "🔍 Evaluation Agent working...",
        "intent_chat": "💬 Chat mode working...",
        "intent_complete": "✅ Complete",
        "error_no_content": "No content to evaluate",
        "error_process": "Processing error",
        "feedback_title": "📝 Experience Feedback",
        "feedback_name": "Your name (optional)",
        "feedback_name_placeholder": "e.g., Zhang San",
        "feedback_slider": "Overall Satisfaction (1-10)",
        "feedback_placeholder": "Share your suggestions...",
        "feedback_submit": "Submit",
        "feedback_success": "Thank you for your feedback!",
        "clear_chat": "🗑️ Clear Current Chat"
    }
}

lang = st.session_state.language
t = texts[lang]
# ========== 侧边栏 ==========
# ========== 侧边栏 ==========
with st.sidebar:
    st.markdown('<h2><i class="fas fa-graduation-cap"></i> 基智</h2>', unsafe_allow_html=True)
    st.page_link("app.py", label="🏠 主界面")
    st.page_link("pages/profile.py", label="👤 个人中心")
    st.page_link("pages/resource_lib.py", label="📚 资源库")  # 👈 添加这一行

    st.markdown("---")

    if st.session_state.logged_in:
        from utils.auth import get_user_status, update_user_status

        # 从数据库获取最新的头像 URL
        from utils.auth import get_avatar_url

        avatar_url = get_avatar_url(st.session_state.user_id)
        if avatar_url:
            st.session_state.avatar_url = avatar_url
        else:
            avatar_url = st.session_state.get("avatar_url", "")
        user_account = st.session_state.get("user_account", "")
        user_id = st.session_state.user_id
        # 获取当前用户的在线状态
        user_status = get_user_status(user_id)
        status_display = {
            "online": {"color": "#22c55e", "text": "在线"},
            "offline": {"color": "#a855f7", "text": "离线"},
            "invisible": {"color": "#6b7280", "text": "隐身"}
        }
        status = status_display.get(user_status, status_display["offline"])

        # 三列布局：头像 | 在线状态 | 昵称+账号
        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            if avatar_url:
                st.image(avatar_url, width=50)
            else:
                st.markdown(
                    '<div style="width:50px;height:50px;border-radius:50%;background:#2a2a3a;display:flex;align-items:center;justify-content:center;font-size:24px;">👤</div>',
                    unsafe_allow_html=True)

        with col2:
            st.markdown(
                f'<div style="display:flex;align-items:center;height:50px;"><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:{status["color"]};margin-right:6px;"></span><span style="font-size:13px;">{status["text"]}</span></div>',
                unsafe_allow_html=True)

        with col3:
            st.markdown(f'<div style="font-weight:bold;font-size:15px;">{st.session_state.username}</div>',
                        unsafe_allow_html=True)
            if user_account:
                st.caption(f"账号：{user_account}")


    else:
        st.info("请先登录")
    st.markdown("---")

    # ========== 对话管理 ==========
    with st.popover("💬 对话管理", use_container_width=True):
        st.markdown("## 💬 对话管理")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("➕ 新对话", use_container_width=True):
                for m in st.session_state.mistake_manager.get_learning_mistakes():
                    st.session_state.mistake_manager.mark_conquered(m["id"])
                new_id = st.session_state.session_mgr.create_session(title="新对话")
                st.session_state.session_mgr.switch_session(new_id)
                st.session_state.messages = []
                st.rerun()
        with col2:
            if st.button("🗑️ 清空当前对话", use_container_width=True):
                current = st.session_state.session_mgr.get_current_session()
                if current:
                    current["messages"] = []
                    st.session_state.session_mgr._save()
                    st.session_state.messages = []
                    st.rerun()

        st.markdown("---")

        with st.popover("📜 查看历史对话", use_container_width=True):
            st.markdown("### 📜 历史对话列表")
            sessions = st.session_state.session_mgr.get_all_sessions()
            current_id = st.session_state.session_mgr.data.get("current_session_id")

            for s in sessions[:20]:
                col1, col2 = st.columns([4, 1])
                with col1:
                    title_display = s["title"]
                    if s["id"] == current_id:
                        title_display = f"📌 {title_display}"
                    if st.button(title_display, key=f"session_{s['id']}", use_container_width=True):
                        st.session_state.session_mgr.switch_session(s["id"])
                        if s.get("messages") and isinstance(s["messages"], list):
                            st.session_state.messages = s["messages"].copy()
                        else:
                            st.session_state.messages = []
                        st.rerun()
                with col2:
                    if st.button("🗑️", key=f"del_{s['id']}"):
                        st.session_state.session_mgr.data["sessions"] = [
                            sess for sess in st.session_state.session_mgr.data["sessions"]
                            if sess["id"] != s["id"]
                        ]
                        if current_id == s["id"]:
                            remaining = st.session_state.session_mgr.data["sessions"]
                            if remaining:
                                st.session_state.session_mgr.switch_session(remaining[0]["id"])
                                st.session_state.messages = remaining[0].get("messages", []).copy()
                            else:
                                new_id = st.session_state.session_mgr.create_session(title="新对话")
                                st.session_state.session_mgr.switch_session(new_id)
                                st.session_state.messages = []
                        st.session_state.session_mgr._save()
                        st.rerun()
                st.markdown("---")

            if not sessions:
                st.info("暂无历史对话")

    st.markdown("---")

    # ========== 工作台 ==========
    with st.popover("🧰 工作台", use_container_width=True):
        st.markdown("## 🧰 工作台")

        user_id = st.session_state.user_id
        access_token = st.session_state.access_token

        # 加载数据
        projects = st.session_state.get("checkin_projects", [])
        events = st.session_state.get("countdown_events", [])
        timers = st.session_state.get("timer_items", [])
        logs = st.session_state.get("learning_logs", [])
        st.session_state.learning_logs = logs if logs else []
        # 横排 tabs（只保留5个：打卡、倒计时、计时器、学习日志、学情报告）
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📅 打卡", "⏰ 倒计时", "⏱️ 计时器", "📝 学习日志", "📈 学情报告"
        ])

        # ========== Tab1: 打卡 ==========
        with tab1:
            if not projects:
                st.info("暂无打卡项目，点击下方添加")
            else:
                for p in projects:
                    col_a, col_b, col_c = st.columns([3, 1, 1])
                    with col_a:
                        st.write(f"**{p['name']}**")
                        st.progress(p['completed_days'] / p['target_days'] if p['target_days'] > 0 else 0)
                        st.caption(f"进度：{p['completed_days']}/{p['target_days']} 天")
                    with col_b:
                        if st.button("✅", key=f"checkin_{p['name']}"):
                            today = datetime.now().strftime("%Y-%m-%d")
                            if p.get('last_checkin') == today:
                                st.warning("今天已经打卡过了")
                            else:
                                p['completed_days'] += 1
                                p['last_checkin'] = today
                                if save_checkin_via_backend(user_id, projects, access_token):
                                    st.success(f"打卡成功！已完成 {p['completed_days']}/{p['target_days']} 天")
                                    st.rerun()
                                else:
                                    st.error("保存失败")
                    with col_c:
                        if st.button("🗑️", key=f"del_checkin_{p['name']}"):
                            projects = [proj for proj in projects if proj['name'] != p['name']]
                            if save_checkin_via_backend(user_id, projects, access_token):
                                st.session_state.checkin_projects = projects  # 加上这行
                                st.rerun()
                    st.markdown("---")

            with st.expander("➕ 添加新打卡项目"):
                col_a, col_b = st.columns(2)
                with col_a:
                    new_name = st.text_input("项目名称", key="new_checkin_name")
                with col_b:
                    new_target = st.number_input("目标天数", min_value=1, max_value=365, value=30,
                                                 key="new_checkin_target")
                if st.button("添加", key="add_checkin_submit"):
                    if new_name:
                        if any(p['name'] == new_name for p in projects):
                            st.error("项目名称已存在")
                        else:
                            projects.append({
                                "name": new_name,
                                "target_days": new_target,
                                "completed_days": 0,
                                "last_checkin": None
                            })
                            if save_checkin_via_backend(user_id, projects, access_token):
                                st.success("添加成功")
                                st.rerun()
                            else:
                                st.error("保存失败")
                    else:
                        st.warning("请输入项目名称")

        # ========== Tab2: 倒计时 ==========
        with tab2:
            if not events:
                st.info("暂无倒计时事件")
            else:
                for e in events:
                    col_a, col_b = st.columns([4, 1])
                    with col_a:
                        st.write(f"**{e['name']}**")
                        days = (datetime.strptime(e['target_date'], "%Y-%m-%d") - datetime.now()).days
                        if days >= 0:
                            st.write(f"📅 距离 {e['name']} 还有 **{days}** 天")
                            st.caption(f"目标日期：{e['target_date']}")
                        else:
                            st.write(f"📅 {e['name']} 已结束（{abs(days)}天前）")
                            st.caption(f"目标日期：{e['target_date']}")
                    with col_b:
                        if st.button("🗑️", key=f"del_countdown_{e['id']}"):
                            events = [ev for ev in events if ev['id'] != e['id']]
                            if save_countdown_via_backend(user_id, events, access_token):
                                st.session_state.countdown_events = events  # 加上这行
                                st.rerun()
                    st.markdown("---")

            with st.expander("➕ 添加倒计时"):
                col_a, col_b = st.columns(2)
                with col_a:
                    new_name = st.text_input("事件名称", placeholder="例：比赛截止", key="countdown_name")
                with col_b:
                    new_date = st.date_input("目标日期", key="countdown_date")
                if st.button("添加", key="add_countdown_submit"):
                    if new_name:
                        import uuid

                        events.append({
                            "id": str(uuid.uuid4()),
                            "name": new_name,
                            "target_date": new_date.strftime("%Y-%m-%d"),
                            "created_at": datetime.now().strftime("%Y-%m-%d")
                        })
                        if save_countdown_via_backend(user_id, events, access_token):
                            st.success("添加成功")
                            st.rerun()
                        else:
                            st.error("保存失败")
                    else:
                        st.warning("请输入事件名称")

        # ========== Tab3: 计时器 ==========
        with tab3:
            if not timers:
                st.info("暂无计时器模板")
            else:
                for timer_item in timers:
                    col_a, col_b, col_c = st.columns([3, 1, 1])
                    with col_a:
                        type_icon = "⏳" if timer_item["type"] == "countdown" else "⏱️"
                        type_text = "倒计时" if timer_item["type"] == "countdown" else "正向计时"
                        duration_text = f" - {timer_item['duration_minutes']}分钟" if timer_item[
                                                                                          "type"] == "countdown" else ""
                        st.write(f"{type_icon} **{timer_item['name']}** ({type_text}{duration_text})")
                    with col_b:
                        if st.button("▶️ 开始", key=f"start_{timer_item['id']}"):
                            st.session_state.active_timer = {
                                "id": timer_item['id'],
                                "name": timer_item['name'],
                                "type": timer_item["type"],
                                "duration_minutes": timer_item['duration_minutes'] if timer_item[
                                                                                          "type"] == "countdown" else 0,
                                "remaining_seconds": timer_item['duration_minutes'] * 60 if timer_item[
                                                                                                "type"] == "countdown" else 0,
                                "elapsed_seconds": 0,
                                "start_time": time.time(),
                                "running": True,
                                "paused": False
                            }
                            st.rerun()
                    with col_c:
                        if st.button("🗑️", key=f"del_timer_{timer_item['id']}"):
                            timers = [t for t in timers if t['id'] != timer_item['id']]
                            if save_timer_via_backend(user_id, timers, access_token):
                                st.session_state.timer_items = timers  # 加上这行
                                st.rerun()
                    st.markdown("---")

            with st.expander("➕ 添加计时器模板"):
                col_a, col_b = st.columns(2)
                with col_a:
                    new_name = st.text_input("任务名称", key="new_timer_name")
                with col_b:
                    new_type = st.selectbox("计时类型", ["倒计时", "正向计时"], key="new_timer_type")
                new_duration = 25
                if new_type == "倒计时":
                    new_duration = st.number_input("时长（分钟）", min_value=1, max_value=180, value=25, step=5,
                                                   key="new_timer_duration")
                if st.button("添加", key="add_timer_submit"):
                    if new_name:
                        import uuid

                        timer_type = "countdown" if new_type == "倒计时" else "stopwatch"
                        timers.append({
                            "id": str(uuid.uuid4()),
                            "name": new_name,
                            "type": timer_type,
                            "duration_minutes": new_duration if new_type == "倒计时" else 0
                        })
                        if save_timer_via_backend(user_id, timers, access_token):
                            st.success("添加成功")
                            st.rerun()
                        else:
                            st.error("保存失败")
                    else:
                        st.warning("请输入任务名称")

            # 正在运行的计时器
            if "active_timer" in st.session_state and st.session_state.active_timer.get("running", False):
                st.markdown("---")
                active = st.session_state.active_timer
                if active["type"] == "countdown":
                    if not active.get("paused", False):
                        elapsed = int(time.time() - active["start_time"])
                        remaining = max(0, active["duration_minutes"] * 60 - elapsed)
                        active["remaining_seconds"] = remaining
                    remaining = active["remaining_seconds"]
                    minutes = remaining // 60
                    seconds = remaining % 60
                    st.markdown(f"### ⏳ 倒计时：{active['name']}")
                    st.markdown(f"## {minutes:02d}:{seconds:02d}")
                    if remaining <= 0:
                        keyword = f"学习了「{active['name']}」{active['duration_minutes']}分钟"
                        save_log_via_backend(st.session_state.user_id, keyword)
                        st.success(f"🎉 {keyword}！已记录到学习日志")
                        del st.session_state.active_timer
                        st.rerun()
                else:
                    if not active.get("paused", False):
                        elapsed = int(time.time() - active["start_time"])
                        active["elapsed_seconds"] = elapsed
                    elapsed = active["elapsed_seconds"]
                    minutes = elapsed // 60
                    seconds = elapsed % 60
                    st.markdown(f"### ⏱️ 正向计时：{active['name']}")
                    st.markdown(f"## {minutes:02d}:{seconds:02d}")

                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    if active.get("paused", False):
                        if st.button("▶️ 继续", key="resume_timer"):
                            active["paused"] = False
                            if active["type"] == "countdown":
                                active["start_time"] = time.time() - (
                                            active["duration_minutes"] * 60 - active["remaining_seconds"])
                            else:
                                active["start_time"] = time.time() - active["elapsed_seconds"]
                            st.rerun()
                    else:
                        if st.button("⏸️ 暂停", key="pause_timer"):
                            active["paused"] = True
                            st.rerun()
                with col_b:
                    if st.button("❌ 取消", key="cancel_timer"):
                        del st.session_state.active_timer
                        st.rerun()
                with col_c:
                    if active["type"] == "stopwatch":
                        if st.button("✅ 完成", key="complete_stopwatch"):
                            actual_min = max(1, active["elapsed_seconds"] // 60)
                            keyword = f"学习了「{active['name']}」{actual_min}分钟"
                            save_log_via_backend(st.session_state.user_id, keyword)
                            st.success(f"🎉 {keyword}！已记录到学习日志")
                            del st.session_state.active_timer
                            st.rerun()
                time.sleep(1)
                st.rerun()

        # ========== Tab4: 学习日志 ==========
        # ========== Tab4: 学习日志 ==========
        with tab4:
            logs = st.session_state.get("learning_logs", [])

            if not logs or len(logs) == 0:
                st.info("暂无学习日志")
            else:
                grouped = {}
                for log in logs:
                    date = log.get("date", "未知日期")
                    if date not in grouped:
                        grouped[date] = []
                    grouped[date].append(log)

                for date, logs_list in list(grouped.items())[:30]:
                    st.markdown(f"### 📅 {date}")
                    for log in logs_list[:10]:
                        st.markdown(f"- {log['keyword']}")
                    if len(logs_list) > 10:
                        st.caption(f"...还有 {len(logs_list) - 10} 条")
                    st.markdown("---")

            if st.button("🗑️ 清空所有日志", key="clear_logs_btn"):
                if clear_learning_logs_via_backend(user_id, access_token):
                    st.session_state.learning_logs = []
                    st.success("日志已清空")
                    st.rerun()
                else:
                    st.error("清空失败")

        # ========== Tab5: 学情报告 ==========
        with tab5:
            st.caption("汇总你的学习数据，生成正向激励报告")
            if st.button("📈 生成学情报告", use_container_width=True, key="generate_report_btn"):
                with st.spinner("正在分析你的学习数据..."):
                    report_data, _ = get_report_via_backend(user_id, access_token)
                    if report_data:
                        logs = report_data.get("logs", [])
                        keywords = list(set([log.get("keyword", "") for log in logs[-50:]]))[:20]
                        total_checkin_days = report_data.get("total_checkin_days", 0)
                        events = report_data.get("events", [])
                        upcoming_events = []
                        for e in events:
                            days = (datetime.strptime(e['target_date'], "%Y-%m-%d") - datetime.now()).days
                            if days >= 0 and days <= 30:
                                upcoming_events.append(f"「{e['name']}」还有 {days} 天")

                        keywords_str = "、".join(keywords) if keywords else "暂无"
                        prompt = f"""请根据以下学习数据，给用户生成一份正向激励的学习报告。

    学习数据：
    - 近期学习内容：{keywords_str}
    - 累计打卡天数：{total_checkin_days} 天
    - 近期倒计时事件：{'、'.join(upcoming_events) if upcoming_events else '无'}

    要求：
    1. 语气温暖、积极、正向激励
    2. 肯定用户的进步和努力
    3. 给出1-2条具体的学习建议
    4. 字数控制在150-200字
    5. 使用中文，适当使用emoji

    请生成报告："""
                        from utils.llm_client import call_llm

                        report = call_llm([{"role": "user", "content": prompt}], temperature=0.7)
                        st.markdown("---")
                        st.markdown(report)
                        st.markdown("---")
                        st.caption("📝 报告由AI生成，仅供参考")
                    else:
                        st.error("获取学习数据失败")

    st.markdown("---")

    # 图片上传
    st.markdown("### 📷 上传图片")
    uploaded_files = st.file_uploader(
        "支持 PNG、JPG、JPEG，可多张",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
        key=f"img_uploader_{st.session_state.uploader_key}"
    )
    if uploaded_files:
        st.session_state.current_images = uploaded_files
        st.caption(f"{len(uploaded_files)} 张图片")
        st.radio("图片类型", ["📝 题目/笔记", "📊 个人成绩单"], horizontal=True, key="image_type")
        for idx, img in enumerate(uploaded_files[:3]):
            st.image(img, width=80)
        if len(uploaded_files) > 3:
            st.caption(f"...等{len(uploaded_files) - 3}张")
    st.markdown("---")

    # 偏好设置
    st.markdown("### 🎛️ 偏好设置")
    current_diff = st.session_state.user_memory.data['preferences'].get('difficulty', 'intermediate')
    current_style = st.session_state.user_memory.data['preferences'].get('style', 'balanced')

    diff_display = {"beginner": "初级", "intermediate": "中等", "advanced": "高级"}
    style_display = {"example_heavy": "多举例", "theory_heavy": "多理论", "balanced": "均衡"}
    diff_reverse = {"初级": "beginner", "中等": "intermediate", "高级": "advanced"}
    style_reverse = {"多举例": "example_heavy", "多理论": "theory_heavy", "均衡": "balanced"}

    col1, col2 = st.columns(2)
    with col1:
        selected_diff_display = st.selectbox("难度", list(diff_reverse.keys()), index=list(diff_reverse.keys()).index(
            diff_display.get(current_diff, "中等")))
    with col2:
        selected_style_display = st.selectbox("风格", list(style_reverse.keys()),
                                              index=list(style_reverse.keys()).index(
                                                  style_display.get(current_style, "均衡")))

    if diff_reverse[selected_diff_display] != current_diff:
        st.session_state.user_memory.update_preference("difficulty", diff_reverse[selected_diff_display])
    if style_reverse[selected_style_display] != current_style:
        st.session_state.user_memory.update_preference("style", style_reverse[selected_style_display])

    st.markdown("---")

    # 学习档案
    st.markdown("### 📝 学习档案")
    st.text(st.session_state.user_memory.get_preference_prompt())
    stats = st.session_state.user_memory.data['preferences'].get('feedback_stats', {})
    if stats.get('total', 0) > 0:
        st.caption(f"📊 反馈次数：{stats.get('total', 0)} | 平均分：{stats.get('avg_score', 0):.1f}")

    st.markdown("---")

    # 反馈表单
    st.markdown("### 📝 使用体验反馈")
    with st.form(key="feedback_form", clear_on_submit=True):
        feedback_name = st.text_input("你的称呼（可选）", placeholder="例如：张三")
        rating = st.slider("整体满意度（1-10分）", 1, 10, 8)
        feedback_text = st.text_area("", placeholder="欢迎提出改进意见...", height=80)
        if st.form_submit_button("提交反馈", use_container_width=True):
            username = feedback_name.strip() if feedback_name else "匿名用户"
            success = send_feedback_email(username, rating, feedback_text)
            if success:
                st.success("感谢反馈！")
                time.sleep(1.5)
                st.rerun()
            else:
                st.error("反馈提交失败")
# ========== 主界面 ==========
st.title(t["main_title"])
st.caption(t["main_caption"])

# 显示历史消息
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 复习功能
if st.session_state.review_question:
    user_input = st.session_state.review_question
    st.session_state.review_question = None
else:
    user_input = st.chat_input(t["chat_placeholder"])
if user_input:
    # 手动收录错题（打字触发）
    manual_keywords = ["加入错题本", "添加到错题本", "记下来", "收藏错题", "记一下"]
    if any(kw in user_input for kw in manual_keywords):
        current = st.session_state.session_mgr.get_current_session()
        last_q = ""
        last_a = ""
        if current and len(current.get("messages", [])) >= 2:
            for i in range(len(current["messages"]) - 1, -1, -1):
                if current["messages"][i]["role"] == "assistant":
                    last_a = current["messages"][i]["content"]
                    if i > 0 and current["messages"][i - 1]["role"] == "user":
                        last_q = current["messages"][i - 1]["content"]
                        break
        if last_q:
            title = generate_mistake_title(last_a, last_q)
            st.session_state.mistake_manager.add_mistake(last_q, "", last_a, {"user": last_q, "assistant": last_a}, title)
            st.success("✅ 已加入错题本")
            time.sleep(0.5)
            st.rerun()
        else:
            st.warning("没有找到可添加的对话")
            st.rerun()

    # ========== 1. 图片 / 输入预处理 ==========
    has_image = len(st.session_state.current_images) > 0
    vision_text = ""
    image_type = None

    if has_image:
        vision_results = []
        for img in st.session_state.current_images:
            img_bytes = img.getvalue()
            current_image_type = st.session_state.get("image_type", "📝 题目/笔记")
            if current_image_type == "📝 题目/笔记":
                prompt = "请提取这张图片中的所有文字内容。"
            else:
                prompt = """请分析这张图片，提取所有学习评估信息，包括：
- 知识模块及等级
- 能力指标
- 综合评价文字
- 百分比对比数据

用清晰的文字描述，按类别分组输出。"""
            result = analyze_image(img_bytes, prompt)
            vision_results.append(result)

        vision_text = "\n---\n".join(vision_results)
        image_type = st.session_state.get("image_type", "📝 题目/笔记")

        if image_type == "📝 题目/笔记":
            combined_input = f"【图片识别内容】\n{vision_text}\n\n【用户问题】\n{user_input}"
        else:
            combined_input = f"【成绩单识别内容】\n{vision_text}\n\n【用户需求】\n{user_input}"
    else:
        combined_input = user_input

    # 保存用户消息
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.session_mgr.add_message("user", combined_input)

    # 新对话自动生成标题
    current_session = st.session_state.session_mgr.get_current_session()
    if current_session and len(current_session.get("messages", [])) == 1:
        title_prompt = f"请为以下学习问题生成一个简短的标题（不超过15字）：{user_input[:80]}"
        new_title = call_llm([{"role": "user", "content": title_prompt}], temperature=0.5)
        st.session_state.session_mgr.update_title(current_session["id"], new_title.strip())

    with st.chat_message("user"):
        st.markdown(user_input)
        if has_image:
            st.caption(f"📷 已上传 {len(st.session_state.current_images)} 张图片")

    # ========== 2. 强制历史上下文 ==========
    def build_context(max_messages=20):
        messages = st.session_state.messages
        if not messages:
            return ""

        recent = messages[-max_messages:]
        lines = ["【对话历史】"]
        for m in recent:
            role = "用户" if m["role"] == "user" else "助手"
            lines.append(f"{role}：{m['content']}")
        return "\n".join(lines)

    context = build_context(20)
    full_input = f"""{context}

【用户当前问题】
{combined_input}

请严格基于以上对话历史回答。如果用户问“我们聊了什么”或“刚才的问题”，请基于历史回答。"""

    intent = detect_intent(combined_input)

    intent_display = {
        "plan": "📋 规划Agent",
        "generate": "📖 生成Agent",
        "evaluate": "🔍 评估Agent",
        "chat": "💬 对话模式"
    }
    difficulty = st.session_state.user_memory.data['preferences'].get('difficulty', 'intermediate')

    # 获取当前对话历史
    current_session = st.session_state.session_mgr.get_current_session()
    history = current_session.get("messages", [])[-20:] if current_session else []
    with st.status(intent_display.get(intent, "思考中..."), expanded=True) as status:
        user_profile = {"level": difficulty, "style": "喜欢例子"}
        memory_context = st.session_state.user_memory.get_preference_prompt()

        try:
            if intent == "plan":
                result = plan(user_profile, full_input)

            elif intent == "generate":
                # 构建历史消息列表
                messages = [
                    {"role": "system", "content": """你是基智，一个热情、博学的AI学习助手。

                ## 你的行为准则：
                1. **先完整回答用户的问题**：无论用户问什么（知识、概念、方法、生活问题等），都要先给出清晰、完整、有用的回答。
                2. **再引导学习**：回答完后，自然地引导到学习方向，比如推荐相关知识点、建议下一步学什么、或者出一道相关的思考题。
                3. **语气温暖亲切**：像朋友一样交流，鼓励用户继续探索。

                ## 示例：
                用户问"广东有什么特点？"
                你应该先回答广东的地理、文化、经济特点，然后说："如果你对地理感兴趣，我们可以一起学习中国的地理分区，或者你想了解广东的历史吗？"

                用户问"如何做番茄炒蛋？"
                你应该先给出菜谱步骤，然后说："烹饪也是生活中的一种学习，如果你对营养学感兴趣，我们可以聊聊食物搭配的知识哦！"

                记住：永远先回答问题，再引导学习。"""},
                    *history,
                    {"role": "user", "content": full_input}
                ]
                response = chat_via_backend(messages, st.session_state.user_id, temperature=0.7)
                if response:
                    result = st.write_stream(response.iter_content(chunk_size=100, decode_unicode=True))

                # 学习日志
                keyword = generate_mistake_title(result, user_input)
                from datetime import datetime

                save_log_via_backend(st.session_state.user_id, keyword)
                logs, _ = get_learning_logs_via_backend(st.session_state.user_id, st.session_state.access_token)
                st.session_state.learning_logs = logs if logs else []
            elif intent == "evaluate":
                current = st.session_state.session_mgr.get_current_session()
                last_a = None
                if current:
                    for msg in reversed(current.get("messages", [])):
                        if msg["role"] == "assistant":
                            last_a = msg["content"]
                            break
                if not last_a:
                    result = generate(full_input, user_profile, memory_context)
                else:
                    if image_type == "个人生成内容" and vision_text:
                        analysis_prompt = f"""请根据以下识别内容生成学习评估报告。
    {vision_text}
    用户问题: {user_input}"""
                        result = evaluate(analysis_prompt, {"level": difficulty}, full_input)
                    else:
                        result = evaluate(last_a, {"level": "medium"}, full_input)

            else:  # chat
                messages = [
                    {"role": "system", "content": "你是基智，友好的学习助手。" + memory_context},
                    *history,
                    {"role": "user", "content": full_input}
                ]
                response = chat_via_backend(messages, st.session_state.user_id, temperature=0.7)
                if response:
                    result = st.write_stream(response.iter_content(chunk_size=100, decode_unicode=True))

            status.update(label="完成", state="complete")

        except Exception as e:
            result = f"处理出错: {str(e)}"
            status.update(label="失败", state="error")

    with st.chat_message("assistant"):
        st.markdown(result)

    # 自动收录错题
    auto_keywords = ["不会", "错了", "做错", "不懂", "没懂", "不太会", "没搞懂", "有点难", "不理解"]
    if any(kw in user_input for kw in auto_keywords):
        title = generate_mistake_title(result, user_input)
        st.session_state.mistake_manager.add_mistake(user_input, "", result, {"user": user_input, "assistant": result}, title)

    # 保存助手消息
    st.session_state.messages.append({"role": "assistant", "content": result})
    st.session_state.session_mgr.add_message("assistant", result)

    # 清空图片
    st.session_state.current_images = []
    st.session_state.uploader_key += 1

    st.rerun()