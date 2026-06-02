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


st.set_page_config(page_title="基智 · 多智能体学习系统", page_icon="🧠", layout="wide", initial_sidebar_state="auto")


def show_login_page():
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    }
    .stApp header {
        display: none;
    }
    footer {
        display: none;
    }
    .main .block-container {
        padding-top: 20px;
        padding-bottom: 20px;
        max-width: 100%;
    }
    .custom-header {
        background: rgba(0,0,0,0.5);
        backdrop-filter: blur(10px);
        padding: 12px 20px;
        text-align: center;
        font-size: 14px;
        color: #aaa;
        border-bottom: 1px solid rgba(255,255,255,0.1);
        margin-bottom: 20px;
    }
    .name-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 28px;
        padding: 60px 30px;
        text-align: center;
        width: 90%;
        max-width: 500px;
        margin: 0 auto 30px auto;
    }
    .name-card h1 {
        color: white;
        font-size: 2rem;
    }
    .name-card .name {
        color: white;
        font-size: 1.2rem;
        background: rgba(255,255,255,0.2);
        padding: 10px 20px;
        border-radius: 40px;
        display: inline-block;
        margin-top: 15px;
    }
    .stButton button {
        border-radius: 40px !important;
    }
    </style>

    <div class="custom-header">
        🧠 基智 · 多智能体学习助手
    </div>
    """, unsafe_allow_html=True)

    # 卡片
    st.markdown(f"""
    <div style="display: flex; justify-content: center;">
        <div class="name-card">
            <h1>🧠 基智</h1>
            <p>你的学习身份</p >
            <div class="name">✨ {st.session_state.current_name}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 按钮
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔄 换一个", use_container_width=True):
            from utils.name_generator import generate_random_name
            st.session_state.current_name = generate_random_name()
            st.rerun()
    with col2:
        if st.button("✅ 开始", use_container_width=True, type="primary"):
            st.session_state.logged_in = True
            st.session_state.username = st.session_state.current_name
            from session_manager import SessionManager
            from checkin import CheckInManager
            from mistakes import MistakeManager
            from learning_log import LearningLogManager
            from countdown import CountdownManager
            from timer import TimerManager
            from memory import UserMemory
            st.session_state.session_mgr = SessionManager(user_id=st.session_state.username)
            st.session_state.user_memory = UserMemory(user_id=st.session_state.username)
            st.session_state.checkin_manager = CheckInManager(user_id=st.session_state.username)
            st.session_state.mistake_manager = MistakeManager(user_id=st.session_state.username)
            st.session_state.learning_log_manager = LearningLogManager(user_id=st.session_state.username)
            st.session_state.countdown_manager = CountdownManager(user_id=st.session_state.username)
            st.session_state.timer_manager = TimerManager(user_id=st.session_state.username)
            st.session_state.messages = []
            st.rerun()
    with col3:
        if st.button("📝 手动", use_container_width=True):
            st.session_state.manual_input_mode = True
            st.rerun()

# 检查登录状态
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_name" not in st.session_state:
    from utils.name_generator import generate_random_name

    st.session_state.current_name = generate_random_name()
if "manual_input_mode" not in st.session_state:
    st.session_state.manual_input_mode = False

# 未登录或手动输入模式，显示登录页
if not st.session_state.logged_in or st.session_state.manual_input_mode:
    if st.session_state.manual_input_mode:
        st.markdown("### 输入你的学习身份")
        name_input = st.text_input("名字", placeholder="例如：张三")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("确认", use_container_width=True):
                if name_input:
                    st.session_state.current_name = name_input
                    st.session_state.logged_in = True
                    st.session_state.manual_input_mode = False
                    # 初始化 Manager
                    from session_manager import SessionManager
                    from checkin import CheckInManager
                    from mistakes import MistakeManager
                    from learning_log import LearningLogManager
                    from countdown import CountdownManager
                    from timer import TimerManager
                    from memory import UserMemory

                    st.session_state.session_mgr = SessionManager(user_id=st.session_state.current_name)
                    st.session_state.user_memory = UserMemory(user_id=st.session_state.current_name)
                    st.session_state.checkin_manager = CheckInManager(user_id=st.session_state.current_name)
                    st.session_state.mistake_manager = MistakeManager(user_id=st.session_state.current_name)
                    st.session_state.learning_log_manager = LearningLogManager(user_id=st.session_state.current_name)
                    st.session_state.countdown_manager = CountdownManager(user_id=st.session_state.current_name)
                    st.session_state.timer_manager = TimerManager(user_id=st.session_state.current_name)
                    st.session_state.messages = []
                    st.rerun()
                else:
                    st.warning("请输入名字")
        with col2:
            if st.button("返回随机", use_container_width=True):
                st.session_state.manual_input_mode = False
                st.rerun()
    else:
        show_login_page()
    st.stop()

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
if "session_mgr" not in st.session_state:
    st.session_state.session_mgr = None  # 先设为 None，登录后赋值
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

# 登录状态
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_name" not in st.session_state:
    from utils.name_generator import generate_random_name
    st.session_state.current_name = generate_random_name()
if "manual_input_mode" not in st.session_state:
    st.session_state.manual_input_mode = False
# 如果当前会话为空，但 st.session_state.messages 不为空 → 主动创建并绑定
if st.session_state.session_mgr.get_current_session() is None and st.session_state.messages:
    import time
    new_id = st.session_state.session_mgr.create_session(title="当前对话")
    st.session_state.session_mgr.switch_session(new_id)
    # 把已有消息同步到 session_mgr
    for msg in st.session_state.messages:
        st.session_state.session_mgr.add_message(msg["role"], msg["content"])
    st.session_state.session_mgr._save()
    st.rerun()
# ========== 保底：确保当前对话存在 + 自动生成标题 ==========
if st.session_state.session_mgr.get_current_session() is None and st.session_state.messages:
    # 1. 从第一条用户消息提取标题
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

    # 2. 创建会话（使用生成的标题）
    new_id = st.session_state.session_mgr.create_session(title=new_title)
    st.session_state.session_mgr.switch_session(new_id)

    # 3. 把已有消息同步到 session_mgr
    for msg in st.session_state.messages:
        st.session_state.session_mgr.add_message(msg["role"], msg["content"])
    st.session_state.session_mgr._save()
    st.rerun()
# ========== 强制修正标题（解决“当前对话 / 新对话”）==========
current_session = st.session_state.session_mgr.get_current_session()
if current_session and current_session["title"] in ["", "当前对话", "新对话"]:
    first_user_msg = ""
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            first_user_msg = msg["content"][:80]
            break
    if first_user_msg:
        try:
            from utils.llm_client import call_llm
            title_prompt = f"请为以下学习问题生成一个简短的标题（不超过15字）：{first_user_msg}"
            new_title = call_llm([{"role": "user", "content": title_prompt}], temperature=0.5)
            st.session_state.session_mgr.update_title(current_session["id"], new_title)
            st.session_state.session_mgr._save()
        except:
            pass
# ========== 双语文本定义 ==========
texts = {
    "中文": {
        "switch_user": "🔄 切换用户",
        "feature_title": "✨ 功能介绍",
        "feature_content": """
        **🧠 基智 · 多智能体学习系统**

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
        "main_title": "🧠 基智 · 多智能体学习助手",
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
        **🧠 JiZhi · Multi-Agent Learning System**

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
        "main_title": "🧠 JiZhi · Multi-Agent Learning Assistant",
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
with st.sidebar:
    st.title("📚 基智")

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

    # 用户名
    if not st.session_state.username:
        username_label = "👤 你的称呼" if lang == "中文" else "👤 Your Name"
        username_placeholder = "例如：张三、学习爱好者..." if lang == "中文" else "e.g., Zhang San, Learner..."
        st.session_state.username = st.text_input(username_label, placeholder=username_placeholder)
        if st.session_state.username:
            st.session_state.session_mgr = SessionManager(user_id=st.session_state.username)
            st.session_state.checkin_manager = CheckInManager(user_id=st.session_state.username)
            st.session_state.mistake_manager = MistakeManager(user_id=st.session_state.username)
            st.session_state.learning_log_manager = LearningLogManager(user_id=st.session_state.username)
            st.session_state.countdown_manager = CountdownManager(user_id=st.session_state.username)
            st.session_state.timer_manager = TimerManager(user_id=st.session_state.username)
            st.rerun()
    else:
        current_user_text = "👤 当前用户：" if lang == "中文" else "👤 Current User: "
        st.caption(f"{current_user_text}{st.session_state.username}")
        switch_user_text = "🔄 切换用户" if lang == "中文" else "🔄 Switch User"
        if st.button(switch_user_text, use_container_width=True):
            st.session_state.username = ""
            st.rerun()
    st.markdown("---")

    # ========== 对话管理 ==========
    chat_mgr_title = "💬 对话管理" if lang == "中文" else "💬 Chat Manager"
    with st.popover(chat_mgr_title, use_container_width=True):
        st.markdown(f"## {chat_mgr_title}")

        new_chat_text = "➕ 新对话" if lang == "中文" else "➕ New Chat"
        clear_text = "🗑️ 清空当前对话" if lang == "中文" else "🗑️ Clear Current Chat"

        col1, col2 = st.columns(2)
        with col1:
            if st.button(new_chat_text, use_container_width=True):
                for m in st.session_state.mistake_manager.get_learning_mistakes():
                    st.session_state.mistake_manager.mark_conquered(m["id"])
                new_id = st.session_state.session_mgr.create_session(title="新对话" if lang == "中文" else "New Chat")
                st.session_state.session_mgr.switch_session(new_id)
                st.session_state.messages = []
                st.rerun()
        with col2:
            if st.button(clear_text, use_container_width=True):
                current = st.session_state.session_mgr.get_current_session()
                if current:
                    current["messages"] = []
                    st.session_state.session_mgr._save()
                    st.session_state.messages = []
                    st.rerun()

        st.markdown("---")

        # 历史对话列表
        history_title = "📜 查看历史对话" if lang == "中文" else "📜 View History"
        with st.popover(history_title, use_container_width=True):
            history_list_title = "📜 历史对话列表" if lang == "中文" else "📜 Chat History List"
            st.markdown(f"### {history_list_title}")
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

            no_history_text = "暂无历史对话" if lang == "中文" else "No chat history"
            if not sessions:
                st.info(no_history_text)

    st.markdown("---")

    # ========== 工作台 ==========
    workbench_title = "🧰 工作台" if lang == "中文" else "🧰 Workbench"
    with st.popover(workbench_title, use_container_width=True):
        st.markdown(f"## {workbench_title}")

        # 7个Tab
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "📅 打卡" if lang == "中文" else "📅 Check-in",
            "⏰ 倒计时" if lang == "中文" else "⏰ Countdown",
            "⏱️ 计时器" if lang == "中文" else "⏱️ Timer",
            "📝 学习日志" if lang == "中文" else "📝 Learning Log",
            "📖 错题本" if lang == "中文" else "📖 Mistake Book",
            "📊 成绩分析" if lang == "中文" else "📊 Score Analysis",
            "📈 学情报告" if lang == "中文" else "📈 Learning Report"
        ])

        # ===== Tab1: 打卡 =====
        with tab1:
            checkin_mgr = st.session_state.checkin_manager
            projects = checkin_mgr.get_projects()
            for p in projects:
                col_a, col_b, col_c = st.columns([3, 1, 1])
                with col_a:
                    st.write(f"**{p['name']}**")
                    st.progress(p['completed_days'] / p['target_days'] if p['target_days'] > 0 else 0)
                    progress_text = f"进度：{p['completed_days']}/{p['target_days']} 天" if lang == "中文" else f"Progress: {p['completed_days']}/{p['target_days']} days"
                    st.caption(progress_text)
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

            add_text = "➕ 添加新打卡项目" if lang == "中文" else "➕ Add New Check-in Project"
            with st.expander(add_text):
                col_a, col_b = st.columns(2)
                with col_a:
                    name_label = "项目名称" if lang == "中文" else "Project Name"
                    new_name = st.text_input(name_label, key="new_checkin_name")
                with col_b:
                    target_label = "目标天数" if lang == "中文" else "Target Days"
                    new_target = st.number_input(target_label, min_value=1, max_value=365, value=30,
                                                 key="new_checkin_target")
                add_btn = "添加" if lang == "中文" else "Add"
                if st.button(add_btn, key="add_checkin_submit"):
                    if new_name:
                        success, msg = checkin_mgr.add_project(new_name, new_target)
                        if success:
                            st.success(msg)
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error(msg)

        # ===== Tab2: 倒计时 =====
        with tab2:
            countdown_mgr = st.session_state.countdown_manager
            events = countdown_mgr.get_events()
            for e in events:
                col_a, col_b = st.columns([4, 1])
                with col_a:
                    st.write(f"**{e['name']}**")
                    days = countdown_mgr.get_days_remaining(e['target_date'])
                    if days >= 0:
                        remaining_text = f"📅 距离 {e['name']} 还有 **{days}** 天" if lang == "中文" else f"📅 {days} days until {e['name']}"
                        st.write(remaining_text)
                        st.caption(f"目标日期：{e['target_date']}" if lang == "中文" else f"Target: {e['target_date']}")
                    else:
                        ended_text = f"📅 {e['name']} 已结束（{abs(days)}天前）" if lang == "中文" else f"📅 {e['name']} ended ({abs(days)} days ago)"
                        st.write(ended_text)
                        st.caption(f"目标日期：{e['target_date']}" if lang == "中文" else f"Target: {e['target_date']}")
                with col_b:
                    if st.button("🗑️", key=f"del_countdown_{e['id']}"):
                        countdown_mgr.delete_event(e['id'])
                        st.rerun()
                st.markdown("---")

            add_text = "➕ 添加倒计时" if lang == "中文" else "➕ Add Countdown"
            with st.expander(add_text):
                col_a, col_b = st.columns(2)
                with col_a:
                    name_label = "事件名称" if lang == "中文" else "Event Name"
                    new_name = st.text_input(name_label,
                                             placeholder="例：比赛截止" if lang == "中文" else "e.g., Competition Deadline",
                                             key="countdown_name")
                with col_b:
                    date_label = "目标日期" if lang == "中文" else "Target Date"
                    new_date = st.date_input(date_label, key="countdown_date")
                add_btn = "添加" if lang == "中文" else "Add"
                if st.button(add_btn, key="add_countdown_submit"):
                    if new_name:
                        countdown_mgr.add_event(new_name, new_date.strftime("%Y-%m-%d"))
                        st.rerun()
                    else:
                        st.warning("请输入事件名称" if lang == "中文" else "Please enter event name")
            if not events:
                no_text = "暂无倒计时事件，点击「➕ 添加倒计时」开始" if lang == "中文" else "No countdown events. Click '➕ Add Countdown' to start"
                st.info(no_text)

        # ===== Tab3: 计时器 =====
        with tab3:
            timer_mgr = st.session_state.timer_manager
            timers = timer_mgr.get_timers()

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

            add_text = "➕ 添加计时器模板" if lang == "中文" else "➕ Add Timer Template"
            with st.expander(add_text):
                col_a, col_b = st.columns(2)
                with col_a:
                    new_name = st.text_input("任务名称" if lang == "中文" else "Task Name", key="new_timer_name")
                with col_b:
                    new_type = st.selectbox("计时类型" if lang == "中文" else "Timer Type", ["倒计时", "正向计时"],
                                            key="new_timer_type")

                new_duration = 25
                if new_type == "倒计时":
                    new_duration = st.number_input("时长（分钟）" if lang == "中文" else "Duration (minutes)",
                                                   min_value=1, max_value=180, value=25, step=5,
                                                   key="new_timer_duration")

                if st.button("添加" if lang == "中文" else "Add", key="add_timer_submit"):
                    if new_name:
                        timer_type = "countdown" if new_type == "倒计时" else "stopwatch"
                        timer_mgr.add_timer(new_name, timer_type, new_duration if new_type == "倒计时" else 0)
                        st.rerun()
                    else:
                        st.warning("请输入任务名称" if lang == "中文" else "Please enter task name")

            # 显示当前正在运行的计时器
            if "active_timer" in st.session_state and st.session_state.active_timer.get("running", False):
                st.markdown("---")
                active = st.session_state.active_timer

                if active["type"] == "countdown":
                    if not active.get("paused", False):
                        elapsed = int(time.time() - active["start_time"])
                        remaining = max(0, active["duration_minutes"] * 60 - elapsed)
                        active["remaining_seconds"] = remaining
                        st.session_state.active_timer["remaining_seconds"] = remaining
                    remaining = active["remaining_seconds"]
                    minutes = remaining // 60
                    seconds = remaining % 60
                    time_str = f"{minutes:02d}:{seconds:02d}"
                    st.markdown(f"### ⏳ 倒计时：{active['name']}")
                    st.markdown(f"## {time_str}")
                    if remaining <= 0:
                        from datetime import datetime

                        keyword = f"学习了「{active['name']}」{active['duration_minutes']}分钟"
                        st.session_state.learning_log_manager.add_log(keyword=keyword,
                                                                      date=datetime.now().strftime("%Y-%m-%d"))
                        st.success(f"🎉 {keyword}！已记录到学习日志")
                        del st.session_state.active_timer
                        st.rerun()
                else:
                    if not active.get("paused", False):
                        elapsed = int(time.time() - active["start_time"])
                        active["elapsed_seconds"] = elapsed
                        st.session_state.active_timer["elapsed_seconds"] = elapsed
                    elapsed = active["elapsed_seconds"]
                    minutes = elapsed // 60
                    seconds = elapsed % 60
                    time_str = f"{minutes:02d}:{seconds:02d}"
                    st.markdown(f"### ⏱️ 正向计时：{active['name']}")
                    st.markdown(f"## {time_str}")

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
                            from datetime import datetime

                            actual_min = max(1, active["elapsed_seconds"] // 60)
                            keyword = f"学习了「{active['name']}」{actual_min}分钟"
                            st.session_state.learning_log_manager.add_log(keyword=keyword,
                                                                          date=datetime.now().strftime("%Y-%m-%d"))
                            st.success(f"🎉 {keyword}！已记录到学习日志")
                            del st.session_state.active_timer
                            st.rerun()

                time.sleep(1)
                st.rerun()

            if not timers and "active_timer" not in st.session_state:
                no_text = "暂无计时器模板，点击「➕ 添加计时器模板」开始" if lang == "中文" else "No timer templates. Click '➕ Add Timer Template' to start"
                st.info(no_text)

        # ===== Tab4: 学习日志 =====
        with tab4:
            log_mgr = st.session_state.learning_log_manager
            grouped = log_mgr.get_logs_grouped_by_date()
            if not grouped:
                no_text = "暂无学习日志" if lang == "中文" else "No learning logs yet"
                st.info(no_text)
            else:
                for date, logs in list(grouped.items())[:30]:
                    st.markdown(f"### 📅 {date}")
                    for log in logs[:10]:
                        st.markdown(f"- {log['keyword']}")
                    if len(logs) > 10:
                        more_text = f"...还有 {len(logs) - 10} 条" if lang == "中文" else f"...{len(logs) - 10} more"
                        st.caption(more_text)
                    st.markdown("---")
            clear_text = "🗑️ 清空所有日志" if lang == "中文" else "🗑️ Clear All Logs"
            if st.button(clear_text, key="clear_logs_btn"):
                log_mgr.clear_all()
                st.rerun()

        # ===== Tab5: 错题本 =====
        with tab5:
            mistake_mgr = st.session_state.mistake_manager
            learning_cnt, conquered_cnt = mistake_mgr.count_by_status()
            learning_label = "学习中" if lang == "中文" else "Learning"
            conquered_label = "已攻克" if lang == "中文" else "Conquered"
            st.caption(f"📚 {learning_label}：{learning_cnt}  |  ✅ {conquered_label}：{conquered_cnt}")

            sub1, sub2 = st.tabs(
                ["📖 学习中" if lang == "中文" else "📖 Learning", "✅ 已攻克" if lang == "中文" else "✅ Conquered"])

            with sub1:
                for m in mistake_mgr.get_learning_mistakes()[:20]:
                    title = m.get('title', m['question'][:60])
                    with st.expander(f"❓ {title}"):
                        if m.get("conversation_snapshot"):
                            q_label = "用户问题：" if lang == "中文" else "User Question:"
                            a_label = "AI回复：" if lang == "中文" else "AI Response:"
                            st.markdown(f"**{q_label}**")
                            st.info(m["conversation_snapshot"]["user"][:300])
                            st.markdown(f"**{a_label}**")
                            st.success(m["conversation_snapshot"]["assistant"][:300])
                        st.caption(f"📅 {m['created_at']}")
                        col_a, col_b = st.columns(2)
                        with col_a:
                            conquer_btn = "✅ 标记已攻克" if lang == "中文" else "✅ Mark Conquered"
                            if st.button(conquer_btn, key=f"conquer_{m['id']}"):
                                mistake_mgr.mark_conquered(m['id'])
                                st.rerun()
                        with col_b:
                            if st.button("🗑️", key=f"del_learning_{m['id']}"):
                                mistake_mgr.delete_mistake(m['id'])
                                st.rerun()
                    st.markdown("---")
                if not mistake_mgr.get_learning_mistakes():
                    no_text = "暂无学习中错题" if lang == "中文" else "No learning mistakes"
                    st.info(no_text)

            with sub2:
                for m in mistake_mgr.get_conquered_mistakes()[:20]:
                    title = m.get('title', m['question'][:60])
                    with st.expander(f"✅ {title}"):
                        if m.get("conversation_snapshot"):
                            q_label = "用户问题：" if lang == "中文" else "User Question:"
                            a_label = "AI回复：" if lang == "中文" else "AI Response:"
                            st.markdown(f"**{q_label}**")
                            st.info(m["conversation_snapshot"]["user"][:300])
                            st.markdown(f"**{a_label}**")
                            st.success(m["conversation_snapshot"]["assistant"][:300])
                        st.caption(f"📅 {m['created_at']}")
                        col_a, col_b = st.columns(2)
                        with col_a:
                            review_btn = "📖 复习" if lang == "中文" else "📖 Review"
                            if st.button(review_btn, key=f"review_{m['id']}"):
                                st.session_state.review_question = m['question']
                                st.rerun()
                        with col_b:
                            if st.button("🗑️", key=f"del_conquered_{m['id']}"):
                                mistake_mgr.delete_mistake(m['id'])
                                st.rerun()
                    st.markdown("---")
                if not mistake_mgr.get_conquered_mistakes():
                    no_text = "暂无已攻克错题" if lang == "中文" else "No conquered mistakes"
                    st.info(no_text)

        # ===== Tab6: 成绩分析 =====
        with tab6:
            upload_hint = "上传成绩单图片（选择「个人成绩单」类型），系统会自动分析" if lang == "中文" else "Upload score sheet image (select 'Score Sheet' type), system will analyze automatically"
            st.info(upload_hint)

        # ===== Tab7: 学情报告 =====
        with tab7:
            st.markdown("## 📊 学情报告")
            st.caption("汇总你的学习数据，生成正向激励报告")

            if st.button("📈 生成学情报告", use_container_width=True, key="generate_report_btn"):
                with st.spinner("正在分析你的学习数据..."):
                    # 获取数据
                    from datetime import datetime

                    # 学习日志
                    logs = st.session_state.learning_log_manager.get_recent_logs(limit=50)
                    log_keywords = list(set([log["keyword"] for log in logs]))[:20]

                    # 错题本
                    learning_cnt, conquered_cnt = st.session_state.mistake_manager.count_by_status()

                    # 打卡
                    checkin_mgr = st.session_state.checkin_manager
                    projects = checkin_mgr.get_projects()
                    total_checkin_days = sum(p["completed_days"] for p in projects)

                    # 倒计时
                    countdown_mgr = st.session_state.countdown_manager
                    events = countdown_mgr.get_events()
                    upcoming_events = []
                    for e in events:
                        days = countdown_mgr.get_days_remaining(e["target_date"])
                        if days >= 0 and days <= 30:
                            upcoming_events.append(f"「{e['name']}」还有 {days} 天")

                    # 构建 Prompt
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

                    # 调用大模型生成
                    from utils.llm_client import call_llm

                    report = call_llm([{"role": "user", "content": prompt}], temperature=0.7)

                    # 显示报告
                    st.markdown("---")
                    st.markdown(report)
                    st.markdown("---")
                    st.caption("📝 报告由AI生成，仅供参考")

            else:
                st.info("点击「生成学情报告」按钮，系统会根据你的学习数据生成正向激励报告")

    st.markdown("---")

    # 图片上传
    upload_label = "📷 上传图片" if lang == "中文" else "📷 Upload Images"
    st.subheader(upload_label)
    upload_hint = "支持 PNG、JPG、JPEG，可多张" if lang == "中文" else "PNG, JPG, JPEG, multiple allowed"
    uploaded_files = st.file_uploader(
        upload_hint,
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
        key=f"img_uploader_{st.session_state.uploader_key}"
    )
    if uploaded_files:
        st.session_state.current_images = uploaded_files
        img_count_text = f"{len(uploaded_files)} 张图片" if lang == "中文" else f"{len(uploaded_files)} images"
        st.caption(img_count_text)
        image_type_label = "图片类型" if lang == "中文" else "Image Type"
        st.radio(image_type_label, ["📝 题目/笔记", "📊 个人成绩单"], horizontal=True, key="image_type")
        for idx, img in enumerate(uploaded_files[:3]):
            st.image(img, width=80)
        if len(uploaded_files) > 3:
            more_text = f"...等{len(uploaded_files) - 3}张" if lang == "中文" else f"...and {len(uploaded_files) - 3} more"
            st.caption(more_text)
    st.markdown("---")

    # 偏好设置
    pref_title = "🎛️ 偏好设置" if lang == "中文" else "🎛️ Preferences"
    st.subheader(pref_title)
    current_diff = st.session_state.user_memory.data['preferences'].get('difficulty', 'intermediate')
    current_style = st.session_state.user_memory.data['preferences'].get('style', 'balanced')

    diff_display = {"beginner": "初级", "intermediate": "中等", "advanced": "高级"}
    style_display = {"example_heavy": "多举例", "theory_heavy": "多理论", "balanced": "均衡"}
    diff_reverse = {"初级": "beginner", "中等": "intermediate", "高级": "advanced"}
    style_reverse = {"多举例": "example_heavy", "多理论": "theory_heavy", "均衡": "balanced"}

    col1, col2 = st.columns(2)
    with col1:
        diff_label = "难度" if lang == "中文" else "Difficulty"
        selected_diff_display = st.selectbox(diff_label, list(diff_reverse.keys()),
                                             index=list(diff_reverse.keys()).index(
                                                 diff_display.get(current_diff, "中等")))
    with col2:
        style_label = "风格" if lang == "中文" else "Style"
        selected_style_display = st.selectbox(style_label, list(style_reverse.keys()),
                                              index=list(style_reverse.keys()).index(
                                                  style_display.get(current_style, "均衡")))

    if diff_reverse[selected_diff_display] != current_diff:
        st.session_state.user_memory.update_preference("difficulty", diff_reverse[selected_diff_display])
    if style_reverse[selected_style_display] != current_style:
        st.session_state.user_memory.update_preference("style", style_reverse[selected_style_display])

    st.markdown("---")

    # 学习档案
    profile_title = "📝 学习档案" if lang == "中文" else "📝 Learning Profile"
    st.subheader(profile_title)
    st.text(st.session_state.user_memory.get_preference_prompt())

    stats = st.session_state.user_memory.data['preferences'].get('feedback_stats', {})
    if stats.get('total', 0) > 0:
        feedback_text = f"📊 反馈次数：{stats.get('total', 0)} | 平均分：{stats.get('avg_score', 0):.1f}" if lang == "中文" else f"📊 Feedback: {stats.get('total', 0)} | Avg: {stats.get('avg_score', 0):.1f}"
        st.caption(feedback_text)

    st.markdown("---")

    # 功能介绍
    with st.popover(t["feature_title"], use_container_width=True):
        st.markdown(t["feature_content"])

    # 团队详情
    with st.popover(t["team_title"], use_container_width=True):
        st.markdown(t["team_content"])

    st.markdown("---")

    # 反馈表单
    feedback_title = "📝 使用体验反馈" if lang == "中文" else "📝 Experience Feedback"
    st.subheader(feedback_title)
    with st.form(key="feedback_form", clear_on_submit=True):
        name_label = "你的称呼（可选）" if lang == "中文" else "Your name (optional)"
        name_placeholder = "例如：张三" if lang == "中文" else "e.g., Zhang San"
        feedback_name = st.text_input(name_label, placeholder=name_placeholder)
        rating_label = "整体满意度（1-10分）" if lang == "中文" else "Overall Satisfaction (1-10)"
        rating = st.slider(rating_label, 1, 10, 8)
        comment_placeholder = "欢迎提出改进意见..." if lang == "中文" else "Share your suggestions..."
        feedback_text = st.text_area("", placeholder=comment_placeholder, height=80)
        submit_btn = "提交反馈" if lang == "中文" else "Submit Feedback"
        submitted = st.form_submit_button(submit_btn)
        if submitted:
            username = feedback_name.strip() if feedback_name else "匿名用户" if lang == "中文" else "Anonymous"
            success = send_feedback_email(username, rating, feedback_text)
            if success:
                success_text = "感谢反馈！" if lang == "中文" else "Thank you for your feedback!"
                st.success(success_text)
                time.sleep(1.5)
                st.rerun()
            else:
                error_text = "反馈提交失败" if lang == "中文" else "Failed to submit feedback"
                st.error(error_text)
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

    with st.status(intent_display.get(intent, "🤔 思考中..."), expanded=True) as status:
        difficulty = st.session_state.user_memory.data['preferences'].get('difficulty', 'intermediate')
        user_profile = {"level": difficulty, "style": "喜欢例子"}
        memory_context = st.session_state.user_memory.get_preference_prompt()

        try:
            if intent == "plan":
                result = plan(user_profile, full_input)
            elif intent == "generate":
                result = generate(full_input, user_profile, memory_context)
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
                    if image_type == "📊 个人成绩单" and vision_text:
                        analysis_prompt = f"""请根据以下识别内容生成学习评估报告：
识别内容：{vision_text}
用户问题：{user_input}"""
                        result = evaluate(analysis_prompt, {"level": difficulty}, full_input)
                    else:
                        result = evaluate(last_a, {"level": "medium"}, full_input)
            else:  # chat
                messages = [
                    {"role": "system", "content": "你是基智，友好的学习助手。" + memory_context},
                    {"role": "user", "content": full_input}
                ]
                result = call_llm(messages, temperature=0.7)

            status.update(label="✅ 完成", state="complete")
        except Exception as e:
            result = f"处理出错：{str(e)}"
            status.update(label="❌ 失败", state="error")

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