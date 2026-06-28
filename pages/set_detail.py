import streamlit as st
import requests
import time
from datetime import datetime, timedelta

BACKEND_URL = "https://ingenious-rejoicing-production-90b7.up.railway.app"

st.set_page_config(
    page_title="题集详情",
    page_icon="📁",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ====== 全局样式 ======
st.markdown("""
<style>
    .stApp { background: var(--background-color); }
    .main .block-container { background: transparent; }

    h1, h2, h3, h4, h5, h6, p, span, div, label, .stMarkdown, .stCaption,
    .stButton button, .stAlert, .stInfo, .stWarning, .stSuccess,
    .stTextInput label, .stSelectbox label,
    .stTextInput input, .stSelectbox select {
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

    .stTextInput input, .stSelectbox select {
        background: rgba(128,128,128,0.05) !important;
        border: none !important;
        border-radius: 12px !important;
        color: var(--text-color) !important;
        box-shadow: inset 0 2px 8px rgba(0,0,0,0.06), 0 1px 0 rgba(255,255,255,0.04) !important;
        transition: all 0.3s ease !important;
        backdrop-filter: blur(4px);
        -webkit-backdrop-filter: blur(4px);
    }
    .stTextInput input:focus, .stSelectbox select:focus {
        background: rgba(128,128,128,0.08) !important;
        box-shadow: inset 0 2px 12px rgba(0,0,0,0.10), 0 0 30px rgba(128,128,128,0.04) !important;
    }

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
        border-radius: 10px;
        padding: 10px 8px;
        text-align: center;
        min-height: 60px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
    }
    .mastery-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.10);
    }

    hr { border: none !important; height: 1px !important; background: rgba(128,128,128,0.10) !important; margin: 12px 0 !important; }

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
</style>
""", unsafe_allow_html=True)

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("请先登录")
    st.stop()

user_id = st.session_state.user_id
access_token = st.session_state.access_token

set_id = st.session_state.get("view_set_id")
if not set_id:
    st.warning("没有找到题集")
    st.stop()


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


def progress_bar_html(progress, bar_color, show_label=True):
    pct = min(max(progress, 0), 100)
    label = f'<span style="font-size:11px; color:#888; min-width:36px; text-align:right;">{pct}%</span>' if show_label else ""
    return f'''
    <div style="display:flex; align-items:center; gap:8px;">
        <div style="flex:1; background:rgba(128,128,128,0.15); border-radius:4px; height:8px; box-shadow:inset 0 1px 4px rgba(0,0,0,0.06); overflow:hidden;">
            <div style="width:{pct}%; height:100%; background:{bar_color}; border-radius:4px; transition:width 0.6s ease; box-shadow:0 0 16px rgba(255,255,255,0.04);"></div>
        </div>
        {label}
    </div>
    '''


def get_set_detail(set_id):
    try:
        response = requests.get(
            f"{BACKEND_URL}/questions/set/{set_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None


def get_question_detail(question_id):
    try:
        response = requests.get(
            f"{BACKEND_URL}/questions/{question_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None


def remove_question_from_set(set_id, question_id):
    try:
        response = requests.post(
            f"{BACKEND_URL}/questions/set/{set_id}/remove/{question_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        return response.status_code in [200, 204]
    except:
        return False


set_detail = get_set_detail(set_id)
if not set_detail:
    st.warning("题集不存在或已被删除")
    st.stop()

question_ids = set_detail.get('question_ids', [])

questions = []
for q_id in question_ids:
    q = get_question_detail(q_id)
    if q:
        questions.append(q)

if questions:
    mastery_scores = [q.get('mastery_score', 0) for q in questions]
    avg_mastery = sum(mastery_scores) / len(mastery_scores)
    strong_count = len([s for s in mastery_scores if s >= 70])
    weak_count = len([s for s in mastery_scores if s < 50])
    mid_count = len([s for s in mastery_scores if 50 <= s < 70])
else:
    avg_mastery = 0
    strong_count = 0
    weak_count = 0
    mid_count = 0

# ====== 顶部 ======
col_left, col_right = st.columns([1, 2])

with col_left:
    if st.button("← 返回", use_container_width=True):
        st.session_state.view_set_id = None
        st.switch_page("pages/resource_lib.py")

    st.markdown(f"### 📁 {set_detail.get('name')}")
    st.caption(f"{set_detail.get('description', '无描述')}")

    created_at = set_detail.get('created_at', '')
    if created_at:
        try:
            clean_time = created_at.replace('Z', '').split('+')[0]
            dt = datetime.fromisoformat(clean_time)
            dt_local = dt + timedelta(hours=8)
            create_time = dt_local.strftime("%Y-%m-%d %H:%M")
        except:
            create_time = created_at.replace('T', ' ').replace('Z', '')[:16]
    else:
        create_time = "未知时间"
    st.caption(f"📅 创建时间：{create_time}  ·  📝 {len(question_ids)} 道题")

with col_right:
    st.markdown("**📊 平均掌握度**")
    if avg_mastery >= 70:
        color = "#00CC66"
        label = "良好"
    elif avg_mastery >= 50:
        color = "#FFC400"
        label = "一般"
    else:
        color = "#FF4444"
        label = "待加强"

    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:10px; margin-bottom:4px;">
        <span style="font-size:24px; font-weight:bold; color:{color};">{avg_mastery:.0f}%</span>
        <span style="font-size:14px; color:#888;">{label}</span>
    </div>
    {progress_bar_html(avg_mastery, color)}
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="display:flex; gap:20px; margin-top:8px;">
        <span style="font-size:13px; color:#00CC66;">🟢 优势 {strong_count}</span>
        <span style="font-size:13px; color:#FFC400;">🟡 一般 {mid_count}</span>
        <span style="font-size:13px; color:#FF4444;">🔴 薄弱 {weak_count}</span>
    </div>
    """, unsafe_allow_html=True)

    if questions:
        st.markdown("---")
        display_questions = questions[:5]
        remaining = len(questions) - 5
        card_cols = st.columns(min(len(display_questions) + 1, 6))

        for i, q in enumerate(display_questions):
            with card_cols[i]:
                topic = q.get('normalized_topic', q.get('topic', '未知'))
                mastery = q.get('mastery_score', 0)
                if mastery >= 70:
                    color_card = "#00CC66"
                elif mastery >= 50:
                    color_card = "#FFC400"
                else:
                    color_card = "#FF4444"

                st.markdown(f"""
                <div class="mastery-card" style="background:{color_card}; color:white;">
                    <div style="font-size:13px; font-weight:bold; margin-bottom:2px; text-shadow:0 1px 4px rgba(0,0,0,0.15);">{topic}</div>
                    <div style="font-size:20px; font-weight:bold; text-shadow:0 1px 4px rgba(0,0,0,0.15);">{mastery}%</div>
                </div>
                """, unsafe_allow_html=True)

                if st.button("练习", key=f"card_practice_{q.get('id')}", use_container_width=True):
                    st.session_state.current_question = q
                    st.switch_page("pages/do_question.py")

        with card_cols[-1] if len(display_questions) < 6 else card_cols:
            if remaining > 0:
                st.markdown(f"""
                <div style="background:rgba(128,128,128,0.04); border:2px dashed rgba(128,128,128,0.10); border-radius:10px; padding:10px 6px; text-align:center; min-height:60px; display:flex; flex-direction:column; justify-content:center; box-shadow:0 2px 8px rgba(0,0,0,0.03);">
                    <div style="font-size:13px; color:#888;">全部卡片</div>
                    <div style="font-size:11px; color:#666;">+{remaining}</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("📋 查看全部", key="view_all_cards", use_container_width=True):
                    st.session_state.view_all_cards = True
                    st.rerun()
            else:
                st.markdown("""
                <div style="background:rgba(128,128,128,0.04); border:2px dashed rgba(128,128,128,0.10); border-radius:10px; padding:10px 6px; text-align:center; min-height:60px; display:flex; flex-direction:column; justify-content:center; box-shadow:0 2px 8px rgba(0,0,0,0.03);">
                    <div style="font-size:13px; color:#888;">已全部显示</div>
                </div>
                """, unsafe_allow_html=True)

st.markdown("---")

# ====== 下方：题目列表 ======
show_all = st.session_state.get("view_all_cards", False)

if show_all:
    st.subheader("📋 全部卡片")
    search_q = st.text_input("🔍 搜索题目", placeholder="输入关键词...", key="search_q_all")
    filter_options = ["全部", "选择题", "填空题", "判断题", "简答题", "计算题", "编程题"]
    filter_type = st.selectbox("筛选题型", filter_options, key="filter_type_all")

    type_map_filter = {
        "选择题": "choice",
        "填空题": "fill",
        "判断题": "judge",
        "简答题": "essay",
        "计算题": "calculation",
        "编程题": "coding"
    }

    filtered_q = questions
    if search_q:
        filtered_q = [q for q in filtered_q if search_q.lower() in q.get("title", "").lower()]
    if filter_type != "全部":
        filter_type_en = type_map_filter.get(filter_type)
        filtered_q = [q for q in filtered_q if q.get("question_type") == filter_type_en]

    if not filtered_q:
        st.info("📭 没有匹配的题目")
    else:
        cols = st.columns(4)
        for idx, q in enumerate(filtered_q):
            with cols[idx % 4]:
                topic = q.get('normalized_topic', q.get('topic', '未知'))
                mastery = q.get('mastery_score', 0)
                q_type = q.get('question_type', '未知')
                if mastery >= 70:
                    color = "#00CC66"
                elif mastery >= 50:
                    color = "#FFC400"
                else:
                    color = "#FF4444"

                st.markdown(f"""
                <div class="mastery-card" style="background:{color}; color:white;">
                    <div style="font-size:15px; font-weight:bold; margin-bottom:2px; text-shadow:0 1px 4px rgba(0,0,0,0.15);">{topic}</div>
                    <div style="font-size:24px; font-weight:bold; text-shadow:0 1px 4px rgba(0,0,0,0.15);">{mastery}%</div>
                    <div style="font-size:11px; opacity:0.7;">{q_type}</div>
                </div>
                """, unsafe_allow_html=True)

                if st.button("练习", key=f"all_practice_{q.get('id')}", use_container_width=True):
                    st.session_state.current_question = q
                    st.switch_page("pages/do_question.py")

    if st.button("收起", use_container_width=True):
        st.session_state.view_all_cards = False
        st.rerun()
else:
    search_q = st.text_input("🔍 搜索题目", placeholder="输入关键词...", key="search_q_normal")
    filter_options = ["全部", "选择题", "填空题", "判断题", "简答题", "计算题", "编程题"]
    filter_type = st.selectbox("筛选题型", filter_options, key="filter_type_normal")

    type_map_filter = {
        "选择题": "choice",
        "填空题": "fill",
        "判断题": "judge",
        "简答题": "essay",
        "计算题": "calculation",
        "编程题": "coding"
    }

    filtered_q = questions
    if search_q:
        filtered_q = [q for q in filtered_q if search_q.lower() in q.get("title", "").lower()]
    if filter_type != "全部":
        filter_type_en = type_map_filter.get(filter_type)
        filtered_q = [q for q in filtered_q if q.get("question_type") == filter_type_en]

    if not filtered_q:
        st.info("📭 没有匹配的题目")
    else:
        for q in filtered_q:
            q_id = q.get('id')
            q_title = q.get('title', '无题目')[:80]
            q_type = q.get('question_type', '未知')
            mastery = q.get('mastery_score', 0)
            difficulty_score = q.get('difficulty_score', 5.0)

            if difficulty_score < 3:
                diff_color = "#00CC66"
                diff_label = "简单"
            elif difficulty_score < 6:
                diff_color = "#FFC400"
                diff_label = "中等"
            else:
                diff_color = "#FF6E00"
                diff_label = "困难"

            if mastery >= 70:
                color = "#00CC66"
                status = "🟢 优势"
            elif mastery >= 50:
                color = "#FFC400"
                status = "🟡 一般"
            else:
                color = "#FF4444"
                status = "🔴 薄弱"

            col1, col2, col3 = st.columns([4, 1, 1])
            with col1:
                st.markdown(f"**{q_title}**")
                st.markdown(f"""
                <div style="display:flex; gap:15px; font-size:13px; color:#888; margin-top:2px;">
                    <span>📝 {q_type}</span>
                    <span style="color:{diff_color};">📊 难度 {difficulty_score:.1f}（{diff_label}）</span>
                    <span style="color:{color};">📈 {status} {mastery}%</span>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                if st.button("📝 练习", key=f"q_practice_{q_id}"):
                    st.session_state.current_question = q
                    st.session_state.from_set_detail = True
                    st.switch_page("pages/do_question.py")
            with col3:
                if st.button("❌ 移除", key=f"q_remove_{q_id}"):
                    if remove_question_from_set(set_id, q_id):
                        st.success("✅ 已从题集移除")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("移除失败")
            st.markdown("---")

    if question_ids:
        if st.button("🎯 全部练习", use_container_width=True):
            st.session_state.practice_set_id = set_id
            st.session_state.practice_questions = question_ids
            st.session_state.practice_index = 0
            st.switch_page("pages/do_question.py")