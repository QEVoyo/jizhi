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

load_dotenv()

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


st.set_page_config(page_title="基智 · 多智能体学习系统", page_icon="🎓", layout="wide", initial_sidebar_state="auto")


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

    from utils.name_generator import generate_random_name
    nickname = st.text_input("昵称", value=generate_random_name())

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
            email = st.text_input("邮箱", placeholder="example@domain.com", value=st.session_state.auto_email)
            password = st.text_input("密码", type="password")
            submitted = st.form_submit_button("登录", use_container_width=True)

            if submitted:
                if not email or not password:
                    st.warning("请输入邮箱和密码")
                else:
                    from utils.auth import sign_in
                    user, err = sign_in(email, password)
                    if user:
                        # 关键：直接用邮箱当用户 ID，不依赖 Supabase 的 id
                        user_id = email
                        st.session_state.logged_in = True
                        st.session_state.user_email = email
                        st.session_state.user_id = user_id
                        st.session_state.username = nickname or email.split("@")[0]

                        from session_manager import SessionManager
                        from memory import UserMemory
                        from checkin import CheckInManager
                        from mistakes import MistakeManager
                        from learning_log import LearningLogManager
                        from countdown import CountdownManager
                        from timer import TimerManager

                        st.session_state.session_mgr = SessionManager(user_id=user_id)
                        st.session_state.user_memory = UserMemory(user_id=user_id)
                        st.session_state.checkin_manager = CheckInManager(user_id=user_id)
                        st.session_state.mistake_manager = MistakeManager(user_id=user_id)
                        st.session_state.learning_log_manager = LearningLogManager(user_id=user_id)
                        st.session_state.countdown_manager = CountdownManager(user_id=user_id)
                        st.session_state.timer_manager = TimerManager(user_id=user_id)

                        st.session_state.messages = []
                        st.rerun()
                    else:
                        st.error("登录失败，请检查邮箱或密码")

    # ========= 注册 Tab =========
    with tab2:
        with st.form("register_form"):
            email = st.text_input("邮箱", placeholder="example@domain.com", key="reg_email")
            password = st.text_input("密码", type="password", key="reg_pwd")
            confirm = st.text_input("确认密码", type="password", key="reg_confirm")
            submitted = st.form_submit_button("注册", use_container_width=True)

            if submitted:
                if not email or not password:
                    st.warning("请填写邮箱和密码")
                elif len(password) < 6:
                    st.warning("密码长度至少为 6 位")
                elif password != confirm:
                    st.warning("两次密码不一致")
                else:
                    from utils.auth import sign_up
                    final_nickname = nickname if nickname else generate_random_name()
                    user, err = sign_up(email, password, final_nickname)

                    if user:
                        st.success("注册成功！请去登录")
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
# ========== 未登录则显示登录页 ==========
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

    # 语言切换
    col_lang1, col_lang2 = st.columns(2)
    with col_lang1:
        if st.button("中文", use_container_width=True, disabled=lang == "中文"):
            st.session_state.language = "中文"
            st.rerun()
    with col_lang2:
        if st.button("English", use_container_width=True, disabled=lang == "English"):
            st.session_state.language = "English"
            st.rerun()
    st.markdown("---")

    # ========== 用户信息 + 退出登录 / 个人中心 ==========
    if st.session_state.logged_in:
        st.markdown(f'<i class="fas fa-user-circle"></i> 当前用户：{st.session_state.username}', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚪 退出登录", use_container_width=True):
                for key in ["logged_in", "user_email", "user_id", "username", "session_mgr",
                            "user_memory", "checkin_manager", "mistake_manager",
                            "learning_log_manager", "countdown_manager", "timer_manager"]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
        with col2:
            if st.button("👤 个人中心", use_container_width=True):
                st.session_state.show_profile = True
                st.rerun()
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
                new_id = st.session_state.session_mgr.create_session(title="新对话" if lang == "中文" else "New Chat")
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

        # 历史对话列表
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
                        all_sessions = st.session_state.session_mgr.get_all_sessions()
                        st.session_state.session_mgr.data["sessions"] = [x for x in all_sessions if x["id"] != s["id"]]
                        if current_id == s["id"]:
                            remaining = st.session_state.session_mgr.data["sessions"]
                            if remaining:
                                st.session_state.session_mgr.switch_session(remaining[0]["id"])
                                if remaining[0].get("messages") and isinstance(remaining[0]["messages"], list):
                                    st.session_state.messages = remaining[0]["messages"].copy()
                                else:
                                    st.session_state.messages = []
                            else:
                                new_id = st.session_state.session_mgr.create_session(
                                    title="新对话" if lang == "中文" else "New Chat")
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

        # 7个Tab（使用纯 emoji 确保100%显示）
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "📅 打卡", "⏰ 倒计时", "⏱️ 计时器",
            "📝 学习日志", "📖 错题本", "📊 成绩分析", "📈 学情报告"
        ])

        # Tab1: 打卡
        with tab1:
            checkin_mgr = st.session_state.checkin_manager
            projects = checkin_mgr.get_projects()
            for p in projects:
                col_a, col_b, col_c = st.columns([3, 1, 1])
                with col_a:
                    st.write(f"**{p['name']}**")
                    st.progress(p['completed_days'] / p['target_days'] if p['target_days'] > 0 else 0)
                    st.caption(f"进度：{p['completed_days']}/{p['target_days']} 天")
                with col_b:
                    if st.button("✅", key=f"checkin_{p['name']}"):
                        success, msg = checkin_mgr.checkin(p['name'])
                        if success:
                            st.success(msg)
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.warning(msg)
                with col_c:
                    if st.button("🗑️", key=f"del_checkin_{p['name']}"):
                        checkin_mgr.delete_project(p['name'])
                        st.rerun()
                st.markdown("---")

            with st.expander("➕ 添加新打卡项目"):
                col_a, col_b = st.columns(2)
                with col_a:
                    new_name = st.text_input("项目名称", key="new_checkin_name")
                with col_b:
                    new_target = st.number_input("目标天数", min_value=1, max_value=365, value=30, key="new_checkin_target")
                if st.button("添加", key="add_checkin_submit"):
                    if new_name:
                        success, msg = checkin_mgr.add_project(new_name, new_target)
                        if success:
                            st.success(msg)
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error(msg)

        # Tab2: 倒计时
        with tab2:
            countdown_mgr = st.session_state.countdown_manager
            events = countdown_mgr.get_events()
            for e in events:
                col_a, col_b = st.columns([4, 1])
                with col_a:
                    st.write(f"**{e['name']}**")
                    days = countdown_mgr.get_days_remaining(e['target_date'])
                    if days >= 0:
                        st.write(f"📅 距离 {e['name']} 还有 **{days}** 天")
                        st.caption(f"目标日期：{e['target_date']}")
                    else:
                        st.write(f"📅 {e['name']} 已结束（{abs(days)}天前）")
                        st.caption(f"目标日期：{e['target_date']}")
                with col_b:
                    if st.button("🗑️", key=f"del_countdown_{e['id']}"):
                        countdown_mgr.delete_event(e['id'])
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
                        countdown_mgr.add_event(new_name, new_date.strftime("%Y-%m-%d"))
                        st.rerun()
                    else:
                        st.warning("请输入事件名称")
            if not events:
                st.info("暂无倒计时事件")

        # Tab3: 计时器
        with tab3:
            timer_mgr = st.session_state.timer_manager
            timers = timer_mgr.get_timers()
            for timer_item in timers:
                col_a, col_b, col_c = st.columns([3, 1, 1])
                with col_a:
                    type_icon = "⏳" if timer_item["type"] == "countdown" else "⏱️"
                    type_text = "倒计时" if timer_item["type"] == "countdown" else "正向计时"
                    duration_text = f" - {timer_item['duration_minutes']}分钟" if timer_item["type"] == "countdown" else ""
                    st.write(f"{type_icon} **{timer_item['name']}** ({type_text}{duration_text})")
                with col_b:
                    if st.button("▶️ 开始", key=f"start_{timer_item['id']}"):
                        st.session_state.active_timer = {
                            "id": timer_item['id'],
                            "name": timer_item['name'],
                            "type": timer_item["type"],
                            "duration_minutes": timer_item['duration_minutes'] if timer_item["type"] == "countdown" else 0,
                            "remaining_seconds": timer_item['duration_minutes'] * 60 if timer_item["type"] == "countdown" else 0,
                            "elapsed_seconds": 0 if timer_item["type"] == "stopwatch" else 0,
                            "start_time": time.time(),
                            "running": True,
                            "paused": False
                        }
                        st.rerun()
                with col_c:
                    if st.button("🗑️", key=f"del_timer_{timer_item['id']}"):
                        timer_mgr.delete_timer(timer_item['id'])
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
                    new_duration = st.number_input("时长（分钟）", min_value=1, max_value=180, value=25, step=5, key="new_timer_duration")
                if st.button("添加", key="add_timer_submit"):
                    if new_name:
                        timer_type = "countdown" if new_type == "倒计时" else "stopwatch"
                        timer_mgr.add_timer(new_name, timer_type, new_duration if new_type == "倒计时" else 0)
                        st.rerun()
                    else:
                        st.warning("请输入任务名称")

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
                        st.session_state.learning_log_manager.add_log(keyword=keyword, date=datetime.now().strftime("%Y-%m-%d"))
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
                                active["start_time"] = time.time() - (active["duration_minutes"] * 60 - active["remaining_seconds"])
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
                            st.session_state.learning_log_manager.add_log(keyword=keyword, date=datetime.now().strftime("%Y-%m-%d"))
                            st.success(f"🎉 {keyword}！已记录到学习日志")
                            del st.session_state.active_timer
                            st.rerun()
                time.sleep(1)
                st.rerun()

            if not timers and "active_timer" not in st.session_state:
                st.info("暂无计时器模板")

        # Tab4: 学习日志
        with tab4:
            log_mgr = st.session_state.learning_log_manager
            grouped = log_mgr.get_logs_grouped_by_date()
            if not grouped:
                st.info("暂无学习日志")
            else:
                for date, logs in list(grouped.items())[:30]:
                    st.markdown(f"### 📅 {date}")
                    for log in logs[:10]:
                        st.markdown(f"- {log['keyword']}")
                    if len(logs) > 10:
                        st.caption(f"...还有 {len(logs)-10} 条")
                    st.markdown("---")
            if st.button("🗑️ 清空所有日志", key="clear_logs_btn"):
                log_mgr.clear_all()
                st.rerun()

        # Tab5: 错题本
        with tab5:
            mistake_mgr = st.session_state.mistake_manager
            learning_cnt, conquered_cnt = mistake_mgr.count_by_status()
            st.caption(f"📚 学习中：{learning_cnt}  |  ✅ 已攻克：{conquered_cnt}")

            sub1, sub2 = st.tabs(["📖 学习中", "✅ 已攻克"])
            with sub1:
                for m in mistake_mgr.get_learning_mistakes()[:20]:
                    title = m.get('title', m['question'][:60])
                    with st.expander(f"❓ {title}"):
                        if m.get("conversation_snapshot"):
                            st.markdown("**用户问题：**")
                            st.info(m["conversation_snapshot"]["user"][:300])
                            st.markdown("**AI回复：**")
                            st.success(m["conversation_snapshot"]["assistant"][:300])
                        st.caption(f"📅 {m['created_at']}")
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button("✅ 标记已攻克", key=f"conquer_{m['id']}"):
                                mistake_mgr.mark_conquered(m['id'])
                                st.rerun()
                        with col_b:
                            if st.button("🗑️", key=f"del_learning_{m['id']}"):
                                mistake_mgr.delete_mistake(m['id'])
                                st.rerun()
                    st.markdown("---")
                if not mistake_mgr.get_learning_mistakes():
                    st.info("暂无学习中错题")

            with sub2:
                for m in mistake_mgr.get_conquered_mistakes()[:20]:
                    title = m.get('title', m['question'][:60])
                    with st.expander(f"✅ {title}"):
                        if m.get("conversation_snapshot"):
                            st.markdown("**用户问题：**")
                            st.info(m["conversation_snapshot"]["user"][:300])
                            st.markdown("**AI回复：**")
                            st.success(m["conversation_snapshot"]["assistant"][:300])
                        st.caption(f"📅 {m['created_at']}")
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button("📖 复习", key=f"review_{m['id']}"):
                                st.session_state.review_question = m['question']
                                st.rerun()
                        with col_b:
                            if st.button("🗑️", key=f"del_conquered_{m['id']}"):
                                mistake_mgr.delete_mistake(m['id'])
                                st.rerun()
                    st.markdown("---")
                if not mistake_mgr.get_conquered_mistakes():
                    st.info("暂无已攻克错题")

        # Tab6: 成绩分析
        with tab6:
            st.info("上传成绩单图片（选择「个人成绩单」类型），系统会自动分析")

        # Tab7: 学情报告
        with tab7:
            st.markdown("## 📊 学情报告")
            st.caption("汇总你的学习数据，生成正向激励报告")
            if st.button("📈 生成学情报告", use_container_width=True, key="generate_report_btn"):
                with st.spinner("正在分析你的学习数据..."):
                    logs = st.session_state.learning_log_manager.get_recent_logs(limit=50)
                    log_keywords = list(set([log["keyword"] for log in logs]))[:20]
                    learning_cnt, conquered_cnt = st.session_state.mistake_manager.count_by_status()
                    projects = st.session_state.checkin_manager.get_projects()
                    total_checkin_days = sum(p["completed_days"] for p in projects)
                    events = st.session_state.countdown_manager.get_events()
                    upcoming_events = []
                    for e in events:
                        days = st.session_state.countdown_manager.get_days_remaining(e["target_date"])
                        if days >= 0 and days <= 30:
                            upcoming_events.append(f"「{e['name']}」还有 {days} 天")

                    keywords_str = "、".join(log_keywords) if log_keywords else "暂无"
                    prompt = f"""请根据以下学习数据，给用户生成一份正向激励的学习报告。

学习数据：
- 近期学习内容：{keywords_str}
- 已攻克错题：{conquered_cnt} 个
- 学习中错题：{learning_cnt} 个
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
                st.info("点击「生成学情报告」按钮，系统会根据你的学习数据生成正向激励报告")

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
            st.caption(f"...等{len(uploaded_files)-3}张")
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
        selected_diff_display = st.selectbox("难度", list(diff_reverse.keys()), index=list(diff_reverse.keys()).index(diff_display.get(current_diff, "中等")))
    with col2:
        selected_style_display = st.selectbox("风格", list(style_reverse.keys()), index=list(style_reverse.keys()).index(style_display.get(current_style, "均衡")))

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

    # 功能介绍
    with st.popover("✨ 功能介绍", use_container_width=True):
        st.markdown(t["feature_content"])

    # 团队详情
    with st.popover("🏆 团队详情", use_container_width=True):
        st.markdown(t["team_content"])

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
                from utils.llm_client import call_llm_stream

                messages = [
                    {"role": "system", "content": "你是基智，个性化学习助手。" + memory_context},
                    *history,
                    {"role": "user", "content": full_input}
                ]
                # 流式输出
                stream = call_llm_stream(messages, temperature=0.7)
                result = st.write_stream(stream)

                # 学习日志
                keyword = generate_mistake_title(result, user_input)
                from datetime import datetime

                st.session_state.learning_log_manager.add_log(keyword=keyword, date=datetime.now().strftime("%Y-%m-%d"))

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
                from utils.llm_client import call_llm_stream

                messages = [
                    {"role": "system", "content": "你是基智，友好的学习助手。" + memory_context},
                    *history,
                    {"role": "user", "content": full_input}
                ]
                stream = call_llm_stream(messages, temperature=0.7)
                result = st.write_stream(stream)

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