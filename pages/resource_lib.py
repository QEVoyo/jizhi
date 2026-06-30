import streamlit as st
import requests
import time
import json
from datetime import datetime
import base64
import os
from functools import lru_cache

BACKEND_URL = "https://ingenious-rejoicing-production-90b7.up.railway.app"

st.set_page_config(
    page_title="资源库",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="auto"
)


# ====== 背景图 ======
def get_base64_image(img_path):
    if not os.path.exists(img_path):
        return ""
    with open(img_path, "rb") as f:
        return base64.b64encode(f.read()).decode()


img_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "resource_lib_bg.png")
img_base64 = get_base64_image(img_path)

if img_base64:
    st.markdown(f"""
    <style>
        .stApp {{
            background: var(--background-color);
            background-image: 
                linear-gradient(rgba(255,255,255,0.6), rgba(255,255,255,0.6)),
                url("data:image/jpg;base64,{img_base64}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        .main .block-container {{ background: transparent; }}
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        .stApp { background: #f5f5f5; }
        .main .block-container { background: transparent; }
    </style>
    """, unsafe_allow_html=True)

# ====== 全局样式 ======
st.markdown("""
<style>
    h1, h2, h3, h4, h5, h6, p, span, div, label, .stMarkdown, .stCaption,
    .stButton button, .stAlert, .stInfo, .stWarning, .stSuccess,
    .stTextInput label, .stSelectbox label, .stNumberInput label,
    .stTextInput input, .stSelectbox select, .stNumberInput input,
    .stTextArea label, .stTextArea textarea,
    .stTabs [data-baseweb="tab"] {
        text-shadow: 0 1px 4px rgba(0,0,0,0.06), 0 2px 8px rgba(0,0,0,0.03);
    }

    .stButton button {
        background: rgba(128,128,128,0.06) !important;
        border: none !important;
        border-radius: 12px !important;
        color: var(--text-color) !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04), inset 0 1px 0 rgba(255,255,255,0.06) !important;
        transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
        font-weight: 500 !important;
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
    }
    .stButton button:hover {
        background: rgba(128,128,128,0.10) !important;
        box-shadow: 0 6px 24px rgba(0,0,0,0.10), inset 0 1px 0 rgba(255,255,255,0.08) !important;
        transform: translateY(-3px) !important;
    }
    .stButton button:active {
        transform: translateY(0px) !important;
    }
    .stButton button:disabled {
        opacity: 0.35 !important;
        cursor: not-allowed !important;
        transform: none !important;
    }

    .stTextInput input, .stSelectbox select, .stNumberInput input,
    .stTextArea textarea {
        background: rgba(128,128,128,0.05) !important;
        border: none !important;
        border-radius: 12px !important;
        color: var(--text-color) !important;
        box-shadow: inset 0 2px 8px rgba(0,0,0,0.06), 0 1px 0 rgba(255,255,255,0.04) !important;
        transition: all 0.3s ease !important;
        backdrop-filter: blur(4px);
        -webkit-backdrop-filter: blur(4px);
    }
    .stTextInput input:focus, .stSelectbox select:focus,
    .stNumberInput input:focus, .stTextArea textarea:focus {
        background: rgba(128,128,128,0.08) !important;
        box-shadow: inset 0 2px 12px rgba(0,0,0,0.10), 0 0 30px rgba(128,128,128,0.04) !important;
    }

    .stPopover {
        background: var(--background-color) !important;
        border: none !important;
        border-radius: 16px !important;
        box-shadow: 0 8px 40px rgba(0,0,0,0.12), 0 2px 8px rgba(0,0,0,0.04) !important;
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 6px !important;
        background: transparent !important;
    }
    .stTabs [data-baseweb="tab"] {
        background: rgba(128,128,128,0.04) !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 8px 18px !important;
        color: var(--text-color) !important;
        text-shadow: 0 1px 4px rgba(0,0,0,0.06), 0 2px 8px rgba(0,0,0,0.03) !important;
        transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
        box-shadow: 0 1px 4px rgba(0,0,0,0.02) !important;
        cursor: pointer !important;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(128,128,128,0.08) !important;
        box-shadow: 0 4px 16px rgba(0,0,0,0.06) !important;
        transform: translateY(-2px) !important;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: rgba(128,128,128,0.10) !important;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08) !important;
    }

    .stExpander {
        background: transparent !important;
        border: none !important;
    }
    .streamlit-expanderHeader {
        background: rgba(128,128,128,0.04) !important;
        border: none !important;
        border-radius: 12px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.03) !important;
        text-shadow: 0 1px 4px rgba(0,0,0,0.06), 0 2px 8px rgba(0,0,0,0.03) !important;
        backdrop-filter: blur(4px);
        -webkit-backdrop-filter: blur(4px);
        transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
    }
    .streamlit-expanderHeader:hover {
        background: rgba(128,128,128,0.08) !important;
        box-shadow: 0 6px 20px rgba(0,0,0,0.08) !important;
        transform: translateY(-2px) !important;
    }
    .streamlit-expanderContent {
        background: transparent !important;
        border: none !important;
        padding-top: 8px !important;
    }

    hr { border: none !important; height: 1px !important; background: rgba(128,128,128,0.10) !important; margin: 12px 0 !important; }

    .stAlert {
        background: rgba(128,128,128,0.05) !important;
        border: none !important;
        border-radius: 12px !important;
        box-shadow: 0 2px 12px rgba(0,0,0,0.04) !important;
        text-shadow: 0 1px 4px rgba(0,0,0,0.06), 0 2px 8px rgba(0,0,0,0.03) !important;
        backdrop-filter: blur(4px);
        -webkit-backdrop-filter: blur(4px);
    }

    .mastery-card {
        border-radius: 12px;
        padding: 14px 10px;
        text-align: center;
        min-height: 70px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
        cursor: pointer;
    }
    .mastery-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 32px rgba(0,0,0,0.15);
    }

    .stFileUploader {
        border: none !important;
        border-radius: 12px !important;
        padding: 4px !important;
        background: rgba(128,128,128,0.03) !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.03) !important;
    }
    .stFileUploader > div {
        border: none !important;
        box-shadow: none !important;
    }
    .stFileUploader label {
        border: none !important;
        box-shadow: none !important;
    }
    .stFileUploader .stFileUploaderDropzone {
        border: 1px dashed rgba(128,128,128,0.15) !important;
        border-radius: 12px !important;
        background: rgba(128,128,128,0.03) !important;
        padding: 24px !important;
        box-shadow: inset 0 2px 8px rgba(0,0,0,0.04) !important;
        transition: all 0.3s ease !important;
    }
    .stFileUploader .stFileUploaderDropzone:hover {
        background: rgba(128,128,128,0.06) !important;
        box-shadow: inset 0 2px 12px rgba(0,0,0,0.08) !important;
    }
</style>
""", unsafe_allow_html=True)

# ====== 登录检查 ======
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("请先登录")
    st.stop()

user_id = st.session_state.user_id
access_token = st.session_state.access_token


# ====== 记录行为 ======
def record_action(action_type, metadata=None):
    """记录用户行为到后端"""
    if "user_id" not in st.session_state or not st.session_state.user_id:
        return
    try:
        requests.post(
            f"{BACKEND_URL}/career/actions/record",
            json={
                "user_id": st.session_state.user_id,
                "action_type": action_type,
                "metadata": metadata or {}
            },
            timeout=3
        )
    except:
        pass


# ====== 带缓存的 API 调用 ======
@st.cache_data(ttl=300)
def load_mastery_data_cached(user_id, access_token):
    """加载掌握度数据（缓存5分钟）"""
    try:
        response = requests.get(
            f"{BACKEND_URL}/questions/mastery/{user_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return []
    except requests.exceptions.Timeout:
        return []
    except Exception as e:
        return []


@st.cache_data(ttl=300)
def load_mistakes_cached(user_id, access_token):
    """加载错题本（缓存5分钟）"""
    try:
        response = requests.get(
            f"{BACKEND_URL}/questions/mistakes/{user_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return []
    except requests.exceptions.Timeout:
        return []
    except Exception as e:
        return []


@st.cache_data(ttl=300)
def get_question_detail_cached(question_id, access_token):
    """获取题目详情（缓存5分钟）"""
    try:
        response = requests.get(
            f"{BACKEND_URL}/questions/{question_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None


@st.cache_data(ttl=300)
def load_question_sets_cached(user_id, access_token):
    """加载题集列表（缓存5分钟）"""
    try:
        response = requests.get(
            f"{BACKEND_URL}/questions/set/list/{user_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        if response.status_code == 200:
            sets = response.json()
            for s in sets:
                question_ids = s.get('question_ids', [])
                if question_ids:
                    sample_ids = question_ids[:5]
                    total = 0
                    count = 0
                    for q_id in sample_ids:
                        q = get_question_detail_cached(q_id, access_token)
                        if q:
                            total += q.get('mastery_score', 0)
                            count += 1
                    s['avg_mastery'] = round(total / count) if count > 0 else 0
                else:
                    s['avg_mastery'] = 0
            return sets
        return []
    except requests.exceptions.Timeout:
        return []
    except Exception as e:
        return []


@st.cache_data(ttl=300)
def load_history_cached(user_id, access_token):
    """加载生成历史（缓存5分钟）"""
    try:
        response = requests.get(
            f"{BACKEND_URL}/questions/history/{user_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return []
    except requests.exceptions.Timeout:
        return []
    except Exception as e:
        return []


def get_question_detail(question_id):
    """获取题目详情（非缓存版本，用于单个操作）"""
    return get_question_detail_cached(question_id, access_token)


def get_color_by_mastery(score):
    if score < 5:
        return "#FF0000"
    elif score < 10:
        return "#FF1A00"
    elif score < 15:
        return "#FF3300"
    elif score < 20:
        return "#FF4D00"
    elif score < 25:
        return "#FF6600"
    elif score < 30:
        return "#FF8000"
    elif score < 35:
        return "#FF9900"
    elif score < 40:
        return "#FFB300"
    elif score < 45:
        return "#FFCC00"
    elif score < 50:
        return "#FFE600"
    elif score < 55:
        return "#D4E000"
    elif score < 60:
        return "#A8D500"
    elif score < 65:
        return "#7DCC00"
    elif score < 70:
        return "#52C200"
    elif score < 75:
        return "#26B800"
    elif score < 80:
        return "#00AD00"
    elif score < 85:
        return "#00A300"
    elif score < 90:
        return "#009900"
    elif score < 95:
        return "#008000"
    else:
        return "#006600"


def progress_bar_html(pct, bar_color):
    pct = min(max(pct, 0), 100)
    return '<div style="display:flex; align-items:center; gap:8px;"><div style="flex:1; background:rgba(128,128,128,0.18); border-radius:4px; height:8px; overflow:hidden;"><div style="width:' + str(
        pct) + '%; height:100%; background:' + bar_color + '; border-radius:4px; transition:width 0.6s ease;"></div></div><span style="font-size:11px; color:#888; min-width:36px; text-align:right;">' + str(
        pct) + '%</span></div>'


# ========== 顶部布局 ==========
col_left, col_right = st.columns([1, 2])

with col_left:
    st.title("📚 资源库")
    st.caption("生成题目 · 管理题集 · 错题本 · 薄弱点巩固")
    if st.button("← 返回主界面", use_container_width=True):
        st.switch_page("app.py")

with col_right:
    with st.spinner("加载掌握度数据..."):
        all_points = load_mastery_data_cached(user_id, access_token)

    if all_points:
        weak_count = len([p for p in all_points if p['mastery_score'] < 60])
        consolidate_count = len([p for p in all_points if 60 <= p['mastery_score'] < 80])
        strong_count = len([p for p in all_points if p['mastery_score'] >= 80])

        st.markdown(f"""
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <span style="font-size:15px; font-weight:bold; text-shadow:0 1px 4px rgba(0,0,0,0.04);">📊 掌握度看板</span>
            <span style="font-size:13px; text-shadow:0 1px 4px rgba(0,0,0,0.04);">
                🔴 薄弱 {weak_count}  &nbsp;|&nbsp; 🟡 待巩固 {consolidate_count}  &nbsp;|&nbsp; 🟢 优势 {strong_count}
            </span>
        </div>
        """, unsafe_allow_html=True)

        weak_points = [p for p in all_points if p['mastery_score'] < 60]
        weak_points.sort(key=lambda x: x['mastery_score'])

        if weak_points:
            st.markdown("""
            <div style="display:flex; align-items:center; gap:6px; margin-bottom:10px;">
                <span style="font-size:11px; color:#888;">0%</span>
                <div style="flex:1; height:6px; border-radius:4px; background:linear-gradient(to right, 
                    #FF0000, #FF1A00, #FF4400, #FF6E00, #FF9900, #FFC400, #D4E000, #A8D500, #66CC33, #00CC66);">
                </div>
                <span style="font-size:11px; color:#888;">100%</span>
                <span style="font-size:11px; margin-left:6px; color:#888;">薄弱 &lt;60%</span>
            </div>
            """, unsafe_allow_html=True)

            display_count = min(len(weak_points), 4)
            card_cols = st.columns(display_count)
            for i in range(display_count):
                with card_cols[i]:
                    wp = weak_points[i]
                    color = get_color_by_mastery(wp['mastery_score'])
                    st.markdown(f"""
                    <div class="mastery-card" style="background:{color}; color:white;">
                        <div style="font-size:13px; font-weight:bold; margin-bottom:2px; text-shadow:0 1px 4px rgba(0,0,0,0.15);">{wp['topic']}</div>
                        <div style="font-size:22px; font-weight:bold; text-shadow:0 1px 4px rgba(0,0,0,0.15);">{wp['mastery_score']}%</div>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button("🎯 攻克", key=f"conquer_{wp['topic']}_{i}", use_container_width=True):
                        st.session_state.practice_mode = "mastery_board"
                        st.session_state.practice_topic = wp['topic']
                        st.switch_page("pages/generate_from_mastery.py")

            if st.button("📋 查看全部知识点", use_container_width=True):
                st.switch_page("pages/mastery_board.py")
        else:
            st.info("🎉 暂无薄弱点，继续保持！")
            if st.button("📋 查看全部知识点", use_container_width=True):
                st.switch_page("pages/mastery_board.py")
    else:
        st.info("📊 暂无掌握度数据，完成一些练习吧！")

st.markdown("---")

# ========== Tab 切换 ==========
tab1, tab2, tab3, tab4 = st.tabs([
    "🤖 生成题目",
    "📁 我的题集",
    "📖 错题本",
    "📜 生成历史"
])

# ========== Tab1: 生成题目 ==========
with tab1:
    st.subheader("🤖 生成新题目")

    practice_mode = st.session_state.get("practice_mode")
    practice_topic = st.session_state.get("practice_topic", "")

    with st.form("generate_question_form"):
        col1, col2 = st.columns(2)
        with col1:
            if practice_mode == "mastery_board" and practice_topic:
                st.markdown(f"**📌 大类方向：** {practice_topic} 🔒")
                category = st.text_input("学科/领域", placeholder="例：Python、数学、语文、英语、物理...")
                topic_hint = st.text_input(
                    "细化知识点（可选）",
                    placeholder=f"例：在「{practice_topic}」下细分，如列表推导式、三角函数..."
                )
                final_topic = practice_topic + (f" - {topic_hint}" if topic_hint else "")
                st.session_state._final_topic = final_topic
            else:
                category = st.text_input("学科/领域", placeholder="例：Python、数学、语文、英语、物理...")
                topic = st.text_input("具体知识点", placeholder="例：列表推导式、三角函数、古诗词鉴赏、牛顿定律...")
                st.session_state._final_topic = topic

        with col2:
            question_type = st.selectbox("题型", [
                "选择题", "填空题", "判断题", "简答题", "计算题", "论述题", "编程题"
            ])
            difficulty = st.selectbox("难度", ["简单", "中等", "困难"])

        extra = st.text_area("补充说明（可选）", placeholder="例：需要包含实际代码示例 / 结合生活场景...", height=60)
        submitted = st.form_submit_button("✨ 一键生成", use_container_width=True)

        if submitted:
            if practice_mode == "mastery_board" and practice_topic:
                final_topic = st.session_state.get("_final_topic", practice_topic)
                if not final_topic or final_topic == practice_topic:
                    st.warning("请至少填写细化知识点或确认大类方向")
                    st.stop()
            else:
                final_topic = topic
                if not final_topic:
                    st.warning("请填写具体知识点")
                    st.stop()

            with st.spinner("AI 正在生成题目..."):
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/questions/generate",
                        json={
                            "user_id": user_id,
                            "category": category if category else "通用",
                            "topic": final_topic,
                            "question_type": question_type,
                            "difficulty": difficulty,
                            "extra": extra
                        },
                        headers={"Authorization": f"Bearer {access_token}"},
                        timeout=60
                    )

                    if response.status_code == 200:
                        question_data = response.json()
                        record_action("generate_question")

                        try:
                            requests.post(
                                f"{BACKEND_URL}/questions/history/save",
                                json={
                                    "user_id": user_id,
                                    "question_id": question_data.get("id"),
                                    "title": question_data.get("title"),
                                    "question_type": question_data.get("type"),
                                    "category": question_data.get("category"),
                                    "topic": question_data.get("topic")
                                },
                                headers={"Authorization": f"Bearer {access_token}"},
                                timeout=10
                            )
                        except:
                            pass

                        if practice_mode == "mastery_board":
                            st.session_state.practice_mode = None
                            st.session_state.practice_topic = None
                            st.session_state._final_topic = None

                        st.session_state.current_question = question_data
                        st.success("✅ 题目生成成功！")
                        time.sleep(0.5)
                        st.switch_page("pages/do_question.py")
                    else:
                        error = response.json().get("detail", "生成失败")
                        st.error(f"❌ 生成失败：{error}")
                except requests.exceptions.Timeout:
                    st.error("⏰ 请求超时，请重试")
                except Exception as e:
                    st.error(f"❌ 错误：{str(e)}")

# ========== Tab2: 我的题集 ==========
with tab2:
    st.subheader("📁 我的题集")


    def create_question_set(name, desc):
        try:
            response = requests.post(
                f"{BACKEND_URL}/questions/set/create?user_id={user_id}",
                json={"name": name, "description": desc, "set_type": "custom"},
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10
            )
            return response.status_code in [200, 201, 204], response.text
        except Exception as e:
            return False, str(e)


    def delete_question_set(set_id):
        try:
            response = requests.delete(
                f"{BACKEND_URL}/questions/set/{set_id}",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10
            )
            return response.status_code in [200, 204]
        except:
            return False


    with st.expander("➕ 创建新题集", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            new_set_name = st.text_input("题集名称", placeholder="例：Python基础", key="new_set_name")
        with col2:
            new_set_desc = st.text_input("描述（可选）", placeholder="例：Python核心知识点", key="new_set_desc")

        if st.button("✨ 创建题集", key="create_set_btn", use_container_width=True):
            if new_set_name:
                success, msg = create_question_set(new_set_name, new_set_desc)
                if success:
                    record_action("create_set")
                    st.success(f"✅ 题集「{new_set_name}」创建成功")
                    time.sleep(0.5)
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error(f"创建失败：{msg}")
            else:
                st.warning("请输入题集名称")

    st.markdown("---")

    with st.spinner("加载题集..."):
        question_sets = load_question_sets_cached(user_id, access_token)

    search_set = st.text_input("🔍 搜索题集", placeholder="输入题集名称搜索...", key="search_set")

    filtered_sets = question_sets
    if search_set:
        filtered_sets = [s for s in filtered_sets if search_set.lower() in s.get("name", "").lower()]

    if not filtered_sets:
        if search_set:
            st.info("📭 没有匹配的题集")
        else:
            st.info("📭 暂无题集，点击上方创建")
    else:
        for s in filtered_sets:
            set_id = s.get('id')
            set_name = s.get('name', '未命名')
            set_desc = s.get('description', '')
            question_ids = s.get('question_ids', [])

            created_at = s.get('created_at', '')
            if created_at:
                try:
                    from datetime import timedelta

                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    dt_local = dt + timedelta(hours=8)
                    create_time = dt_local.strftime("%Y-%m-%d %H:%M")
                except:
                    create_time = created_at[:16]
            else:
                create_time = "未知时间"

            col1, col2, col3, col4 = st.columns([3, 1.5, 1, 1])
            with col1:
                st.markdown(f"**{set_name}**")
                st.caption(f"{set_desc if set_desc else '无描述'}  ·  📅 {create_time}  ·  📝 {len(question_ids)} 道题")

                avg_mastery = s.get('avg_mastery', 0)
                bar_color = get_color_by_mastery(avg_mastery)
                st.markdown(progress_bar_html(avg_mastery, bar_color), unsafe_allow_html=True)
            with col2:
                if st.button("📖 查看", key=f"view_{set_id}"):
                    st.session_state.view_set_id = set_id
                    st.switch_page("pages/set_detail.py")
            with col3:
                if st.button("🗑️ 删除", key=f"del_{set_id}"):
                    if delete_question_set(set_id):
                        st.success(f"✅ 题集「{set_name}」已删除")
                        st.cache_data.clear()
                        time.sleep(0.3)
                        st.rerun()
                    else:
                        st.error("删除失败")
            with col4:
                if question_ids:
                    if st.button("🎯 练习", key=f"practice_{set_id}"):
                        st.session_state.practice_set_id = set_id
                        st.session_state.practice_questions = question_ids
                        st.session_state.practice_index = 0
                        st.switch_page("pages/do_question.py")
            st.markdown("---")

# ========== Tab3: 错题本 ==========
with tab3:
    st.subheader("📖 错题本")

    filter_options = ["全部", "选择题", "填空题", "判断题", "简答题", "计算题", "论述题", "编程题"]
    type_map = {
        "选择题": "choice",
        "填空题": "fill",
        "判断题": "judge",
        "简答题": "essay",
        "计算题": "calculation",
        "论述题": "essay",
        "编程题": "coding"
    }
    type_display_map = {
        "choice": "选择题",
        "fill": "填空题",
        "judge": "判断题",
        "essay": "简答题/论述题",
        "calculation": "计算题",
        "coding": "编程题"
    }

    with st.spinner("加载错题本..."):
        mistakes = load_mistakes_cached(user_id, access_token)

    learning = [m for m in mistakes if m.get('mistake_status') == 'learning']
    conquered = [m for m in mistakes if m.get('mistake_status') == 'conquered']

    st.caption(f"📚 学习中：{len(learning)}  |  ✅ 已攻克：{len(conquered)}")
    st.markdown("---")

    if not mistakes:
        st.info("🎉 暂无错题，继续保持！")
    else:
        tab_learning, tab_conquered = st.tabs(["📖 学习中", "✅ 已攻克"])

        with tab_learning:
            if not learning:
                st.info("🎉 没有学习中的错题，继续加油！")
            else:
                col_search, col_filter = st.columns([3, 1])
                with col_search:
                    search_learning = st.text_input("🔍 搜索题目", placeholder="输入关键词...", key="search_learning")
                with col_filter:
                    filter_learning = st.selectbox("筛选题型", filter_options, key="filter_learning")

                filtered = learning
                if search_learning:
                    filtered = [m for m in filtered if search_learning.lower() in m.get("title", "").lower()]
                if filter_learning != "全部":
                    filter_en = type_map.get(filter_learning)
                    filtered = [m for m in filtered if m.get("question_type") == filter_en]

                if not filtered:
                    st.info("📭 没有匹配的错题")
                else:
                    for m in filtered:
                        title = m.get('title', '无题目')[:60]
                        mastery = m.get('mastery_score', 0)
                        q_type = type_display_map.get(m.get('question_type', ''), '未知')
                        added_at = m.get('mistake_added_at', '')
                        if added_at:
                            try:
                                dt = datetime.fromisoformat(added_at.replace('Z', '+00:00'))
                                added_time = dt.strftime("%Y-%m-%d %H:%M")
                            except:
                                added_time = added_at[:16]
                        else:
                            added_time = "未知时间"

                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.markdown(f"**{title}**")
                            bar_color = get_color_by_mastery(mastery)
                            st.markdown(progress_bar_html(mastery, bar_color), unsafe_allow_html=True)
                            st.caption(f"题型：{q_type}  |  加入时间：{added_time}")
                        with col2:
                            if st.button("📝 复习", key=f"review_{m.get('id')}"):
                                record_action("conquer_mistake")
                                st.session_state.current_question = m
                                st.session_state.from_mistake_book = True
                                st.switch_page("pages/do_question.py")
                        st.markdown("---")

        with tab_conquered:
            if not conquered:
                st.info("📭 暂无已攻克的错题")
            else:
                col_search, col_filter = st.columns([3, 1])
                with col_search:
                    search_conquered = st.text_input("🔍 搜索题目", placeholder="输入关键词...", key="search_conquered")
                with col_filter:
                    filter_conquered = st.selectbox("筛选题型", filter_options, key="filter_conquered")

                filtered = conquered
                if search_conquered:
                    filtered = [m for m in filtered if search_conquered.lower() in m.get("title", "").lower()]
                if filter_conquered != "全部":
                    filter_en = type_map.get(filter_conquered)
                    filtered = [m for m in filtered if m.get("question_type") == filter_en]

                if not filtered:
                    st.info("📭 没有匹配的错题")
                else:
                    for m in filtered:
                        title = m.get('title', '无题目')[:60]
                        mastery = m.get('mastery_score', 0)
                        q_type = type_display_map.get(m.get('question_type', ''), '未知')

                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.markdown(f"**{title}**")
                            bar_color = get_color_by_mastery(mastery)
                            st.markdown(progress_bar_html(mastery, bar_color), unsafe_allow_html=True)
                            st.caption(f"题型：{q_type}")
                        with col2:
                            if st.button("📝 复习", key=f"review_{m.get('id')}"):
                                record_action("conquer_mistake")
                                st.session_state.current_question = m
                                st.session_state.from_mistake_book = True
                                st.switch_page("pages/do_question.py")
                        st.markdown("---")

# ========== Tab4: 生成历史 ==========
with tab4:
    st.subheader("📜 生成历史")

    with st.spinner("加载生成历史..."):
        history = load_history_cached(user_id, access_token)

    if not history:
        st.info("📭 暂无生成记录，去生成一道题目吧！")
    else:
        search = st.text_input("🔍 搜索题目", placeholder="输入关键词搜索...")
        filter_options = ["全部", "选择题", "填空题", "判断题", "简答题", "计算题", "编程题"]
        filter_type = st.selectbox("筛选题型", filter_options, key="history_filter")

        type_map_hist = {
            "选择题": "choice",
            "填空题": "fill",
            "判断题": "judge",
            "简答题": "essay",
            "计算题": "calculation",
            "编程题": "coding"
        }

        filtered = history
        if search:
            filtered = [h for h in filtered if search.lower() in h.get("title", "").lower()]
        if filter_type != "全部":
            filter_type_en = type_map_hist.get(filter_type)
            filtered = [h for h in filtered if h.get("question_type") == filter_type_en]

        if not filtered:
            st.info("📭 没有匹配的记录")
        else:
            for h in filtered:
                status_map = {
                    "pending": "🔄 待练习",
                    "practiced": "📖 已练习",
                    "mastered": "✅ 已掌握"
                }
                status_display = status_map.get(h.get("status", "pending"), "🔄 待练习")

                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.markdown(f"**{h.get('title', '')[:50]}**")
                    type_display_map_hist = {
                        "choice": "选择题",
                        "fill": "填空题",
                        "judge": "判断题",
                        "essay": "简答题",
                        "calculation": "计算题",
                        "coding": "编程题"
                    }
                    q_type_display = type_display_map_hist.get(h.get('question_type', ''),
                                                               h.get('question_type', '未知'))
                    st.caption(f"{q_type_display}  |  {h.get('category', '未分类')}  |  {h.get('topic', '')}")
                with col2:
                    created_at = h.get('created_at', '')
                    if created_at:
                        try:
                            from datetime import timedelta

                            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                            dt_local = dt + timedelta(hours=8)
                            display_time = dt_local.strftime("%Y-%m-%d %H:%M")
                        except:
                            display_time = created_at.replace('T', ' ').replace('Z', '')[:16]
                        st.caption(f"生成时间：{display_time}")
                    st.caption(f"状态：{status_display}")
                with col3:
                    if st.button("📝 练习", key=f"history_{h.get('id', h.get('created_at', ''))}"):
                        with st.spinner("加载题目..."):
                            try:
                                response = requests.get(
                                    f"{BACKEND_URL}/questions/{h.get('question_id')}",
                                    headers={"Authorization": f"Bearer {access_token}"},
                                    timeout=10
                                )
                                if response.status_code == 200:
                                    question_data = response.json()
                                    st.session_state.current_question = question_data
                                    st.switch_page("pages/do_question.py")
                                else:
                                    st.error("获取题目失败")
                            except Exception as e:
                                st.error(f"错误：{str(e)}")
                st.markdown("---")