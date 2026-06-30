import streamlit as st
import requests
import time
import base64
import os

BACKEND_URL = "https://ingenious-rejoicing-production-90b7.up.railway.app"

st.set_page_config(
    page_title="掌握度看板",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ====== 背景图 ======
def get_base64_image(img_path):
    with open(img_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

img_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "mastery_board_bg.jpg")
img_base64 = get_base64_image(img_path)

# ====== 全局样式 ======
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

    h1, h2, h3, h4, h5, h6, p, span, div, label, .stMarkdown, .stCaption,
    .stButton button, .stAlert, .stInfo, .stWarning, .stSuccess,
    .stTextInput label, .stSelectbox label,
    .stTextInput input, .stSelectbox select {{
        text-shadow: 0 1px 4px rgba(0,0,0,0.06), 0 2px 8px rgba(0,0,0,0.03);
    }}

    .stButton button {{
        background: rgba(128,128,128,0.06) !important;
        border: none !important;
        border-radius: 12px !important;
        color: var(--text-color) !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04), inset 0 1px 0 rgba(255,255,255,0.06) !important;
        transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
        font-weight: 500 !important;
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
    }}
    .stButton button:hover {{
        background: rgba(128,128,128,0.10) !important;
        box-shadow: 0 6px 24px rgba(0,0,0,0.10), inset 0 1px 0 rgba(255,255,255,0.08) !important;
        transform: translateY(-3px) !important;
    }}
    .stButton button:active {{
        transform: translateY(0px) !important;
    }}

    .stTextInput input, .stSelectbox select {{
        background: rgba(128,128,128,0.05) !important;
        border: none !important;
        border-radius: 12px !important;
        color: var(--text-color) !important;
        box-shadow: inset 0 2px 8px rgba(0,0,0,0.06), 0 1px 0 rgba(255,255,255,0.04) !important;
        transition: all 0.3s ease !important;
        backdrop-filter: blur(4px);
        -webkit-backdrop-filter: blur(4px);
    }}
    .stTextInput input:focus, .stSelectbox select:focus {{
        background: rgba(128,128,128,0.08) !important;
        box-shadow: inset 0 2px 12px rgba(0,0,0,0.10), 0 0 30px rgba(128,128,128,0.04) !important;
    }}

    .stAlert {{
        background: rgba(128,128,128,0.05) !important;
        border: none !important;
        border-radius: 12px !important;
        box-shadow: 0 2px 12px rgba(0,0,0,0.04) !important;
        text-shadow: 0 1px 4px rgba(0,0,0,0.06), 0 2px 8px rgba(0,0,0,0.03) !important;
        backdrop-filter: blur(4px);
        -webkit-backdrop-filter: blur(4px);
    }}

    hr {{ border: none !important; height: 1px !important; background: rgba(128,128,128,0.10) !important; margin: 12px 0 !important; }}

    .stat-card {{
        background: rgba(128,128,128,0.04);
        border-radius: 12px;
        padding: 14px 12px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.03);
        transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
        backdrop-filter: blur(4px);
        -webkit-backdrop-filter: blur(4px);
    }}
    .stat-card:hover {{
        background: rgba(128,128,128,0.07);
        box-shadow: 0 6px 24px rgba(0,0,0,0.06);
        transform: translateY(-3px);
    }}
    .stat-card .stat-number {{
        font-size: 28px;
        font-weight: bold;
    }}
    .stat-card .stat-label {{
        font-size: 13px;
        color: #888;
    }}

    .mastery-card {{
        border-radius: 14px;
        padding: 18px 12px;
        text-align: center;
        min-height: 80px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
        cursor: pointer;
        position: relative;
        overflow: hidden;
    }}
    .mastery-card::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(180deg, rgba(255,255,255,0.08) 0%, transparent 100%);
        pointer-events: none;
    }}
    .mastery-card:hover {{
        transform: translateY(-6px);
        box-shadow: 0 12px 40px rgba(0,0,0,0.15);
    }}
    .mastery-card .card-topic {{
        font-size: 14px;
        font-weight: 600;
        margin-bottom: 4px;
        text-shadow: 0 1px 4px rgba(0,0,0,0.15);
        position: relative;
        z-index: 1;
    }}
    .mastery-card .card-score {{
        font-size: 26px;
        font-weight: 700;
        text-shadow: 0 1px 4px rgba(0,0,0,0.15);
        position: relative;
        z-index: 1;
    }}
    .mastery-card .card-status {{
        font-size: 11px;
        margin-top: 2px;
        opacity: 0.8;
        text-shadow: 0 1px 4px rgba(0,0,0,0.10);
        position: relative;
        z-index: 1;
    }}
</style>
""", unsafe_allow_html=True)

# 登录检查
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("请先登录")
    st.stop()

user_id = st.session_state.user_id
access_token = st.session_state.access_token


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


def load_mastery_data(user_id, access_token):
    try:
        response = requests.get(
            f"{BACKEND_URL}/questions/mastery/{user_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []


st.title("📊 掌握度看板")
st.caption("查看各知识点的掌握程度，针对性强化薄弱环节")

if st.button("← 返回资源库", use_container_width=True):
    st.switch_page("pages/resource_lib.py")

st.markdown("---")

mastery_data = load_mastery_data(user_id, access_token)

if not mastery_data:
    st.info("📭 暂无学习数据，去生成题目并练习吧！")
    st.stop()

weak_points = [p for p in mastery_data if p['mastery_score'] < 60]
consolidate_points = [p for p in mastery_data if 60 <= p['mastery_score'] < 80]
strong_points = [p for p in mastery_data if p['mastery_score'] >= 80]

# ====== 统计摘要 ======
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-number" style="color:#FF4444;">{len(weak_points)}</div>
        <div class="stat-label">🔴 薄弱</div>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-number" style="color:#FFC400;">{len(consolidate_points)}</div>
        <div class="stat-label">🟡 待巩固</div>
    </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-number" style="color:#00CC66;">{len(strong_points)}</div>
        <div class="stat-label">🟢 优势</div>
    </div>
    """, unsafe_allow_html=True)
with col4:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-number" style="color:var(--text-color);">{len(mastery_data)}</div>
        <div class="stat-label">📚 总计</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ====== 颜色图例 ======
st.markdown("""
<div style="display:flex; align-items:center; gap:6px; margin-bottom:16px;">
    <span style="font-size:11px; color:#888;">0%</span>
    <div style="flex:1; height:6px; border-radius:4px; background:linear-gradient(to right, 
        #FF0000, #FF1A00, #FF4400, #FF6E00, #FF9900, #FFC400, #D4E000, #A8D500, #66CC33, #00CC66);">
    </div>
    <span style="font-size:11px; color:#888;">100%</span>
</div>
""", unsafe_allow_html=True)

# ====== 搜索、筛选、排序 ======
col_search, col_filter, col_sort = st.columns([2, 1.2, 1.2])
with col_search:
    search = st.text_input("🔍 搜索知识点", placeholder="输入关键词...", key="search_mastery")
with col_filter:
    filter_options = ["全部", "薄弱 (<60%)", "待巩固 (60-80%)", "优势 (≥80%)"]
    filter_choice = st.selectbox("筛选", filter_options, key="filter_mastery")
with col_sort:
    sort_options = ["掌握度（低→高）", "掌握度（高→低）", "名称（A→Z）", "名称（Z→A）"]
    sort_choice = st.selectbox("排序", sort_options, key="sort_mastery")

# ====== 三组显示 ======

# ---- 根据筛选决定显示哪些组 ----
if filter_choice == "薄弱 (<60%)":
    display_weak = weak_points.copy()
    display_consolidate = []
    display_strong = []
elif filter_choice == "待巩固 (60-80%)":
    display_weak = []
    display_consolidate = consolidate_points.copy()
    display_strong = []
elif filter_choice == "优势 (≥80%)":
    display_weak = []
    display_consolidate = []
    display_strong = strong_points.copy()
else:  # "全部"
    display_weak = weak_points.copy()
    display_consolidate = consolidate_points.copy()
    display_strong = strong_points.copy()

# ---- 应用搜索过滤 ----
if search:
    display_weak = [p for p in display_weak if search.lower() in p.get('topic', '').lower()]
    display_consolidate = [p for p in display_consolidate if search.lower() in p.get('topic', '').lower()]
    display_strong = [p for p in display_strong if search.lower() in p.get('topic', '').lower()]


# ---- 排序函数 ----
def sort_list(data_list, sort_choice):
    if sort_choice == "掌握度（低→高）":
        data_list.sort(key=lambda x: x['mastery_score'])
    elif sort_choice == "掌握度（高→低）":
        data_list.sort(key=lambda x: x['mastery_score'], reverse=True)
    elif sort_choice == "名称（A→Z）":
        data_list.sort(key=lambda x: x.get('topic', ''))
    elif sort_choice == "名称（Z→A）":
        data_list.sort(key=lambda x: x.get('topic', ''), reverse=True)
    return data_list


# ---- 1. 薄弱 ----
if display_weak:
    st.markdown("### 🔴 薄弱")
    display_weak = sort_list(display_weak, sort_choice)
    cols = st.columns(4)
    for idx, p in enumerate(display_weak):
        with cols[idx % 4]:
            color = get_color_by_mastery(p['mastery_score'])
            st.markdown(f"""
            <div class="mastery-card" style="background:{color}; color:white;">
                <div class="card-topic">{p['topic']}</div>
                <div class="card-score">{p['mastery_score']}%</div>
                <div class="card-status">🔴 薄弱</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🎯 练习", key=f"weak_{p['topic']}_{idx}", use_container_width=True):
                st.session_state.practice_mode = "mastery_board"
                st.session_state.practice_topic = p['topic']
                st.switch_page("pages/generate_from_mastery.py")
    st.markdown("---")

# ---- 2. 待巩固 ----
if display_consolidate:
    st.markdown("### 🟡 待巩固")
    display_consolidate = sort_list(display_consolidate, sort_choice)
    cols = st.columns(4)
    for idx, p in enumerate(display_consolidate):
        with cols[idx % 4]:
            color = get_color_by_mastery(p['mastery_score'])
            st.markdown(f"""
            <div class="mastery-card" style="background:{color}; color:white;">
                <div class="card-topic">{p['topic']}</div>
                <div class="card-score">{p['mastery_score']}%</div>
                <div class="card-status">🟡 待巩固</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🎯 练习", key=f"consolidate_{p['topic']}_{idx}", use_container_width=True):
                st.session_state.practice_mode = "mastery_board"
                st.session_state.practice_topic = p['topic']
                st.switch_page("pages/generate_from_mastery.py")
    st.markdown("---")

# ---- 3. 优势 ----
if display_strong:
    st.markdown("### 🟢 优势")
    display_strong = sort_list(display_strong, sort_choice)
    cols = st.columns(4)
    for idx, p in enumerate(display_strong):
        with cols[idx % 4]:
            color = get_color_by_mastery(p['mastery_score'])
            st.markdown(f"""
            <div class="mastery-card" style="background:{color}; color:white;">
                <div class="card-topic">{p['topic']}</div>
                <div class="card-score">{p['mastery_score']}%</div>
                <div class="card-status">🟢 优势</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🎯 练习", key=f"strong_{p['topic']}_{idx}", use_container_width=True):
                st.session_state.practice_mode = "mastery_board"
                st.session_state.practice_topic = p['topic']
                st.switch_page("pages/generate_from_mastery.py")
    st.markdown("---")

# ---- 如果三组都为空 ----
if not display_weak and not display_consolidate and not display_strong:
    st.info("📭 没有匹配的知识点")