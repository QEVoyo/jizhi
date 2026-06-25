import streamlit as st
import requests

BACKEND_URL = "http://localhost:8000"

st.set_page_config(
    page_title="掌握度看板",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="auto"
)

# 登录检查
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("请先登录")
    st.stop()


# ========== 工具函数 ==========
def get_color_by_mastery(score):
    """根据掌握程度返回颜色（10种渐变）"""
    if score < 10:
        return "#FF0000"
    elif score < 20:
        return "#FF1A00"
    elif score < 30:
        return "#FF4400"
    elif score < 40:
        return "#FF6E00"
    elif score < 50:
        return "#FF9900"
    elif score < 60:
        return "#FFC400"
    elif score < 70:
        return "#D4E000"
    elif score < 80:
        return "#A8D500"
    elif score < 90:
        return "#66CC33"
    else:
        return "#00CC66"


def load_mastery_data(user_id, access_token):
    """从后端获取真实掌握度数据"""
    try:
        response = requests.get(
            f"{BACKEND_URL}/questions/mastery/{user_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"加载数据失败: {e}")
        return []


# ========== 页面标题 ==========
col_back, col_title = st.columns([1, 5])
with col_back:
    if st.button("← 返回", use_container_width=True):
        st.switch_page("pages/resource_lib.py")
with col_title:
    st.title("📊 掌握度看板")
    st.caption("全部知识点的掌握情况一目了然")

st.markdown("---")

# ========== 获取真实数据 ==========
user_id = st.session_state.user_id
access_token = st.session_state.access_token
all_points = load_mastery_data(user_id, access_token)

if not all_points:
    st.info("📭 暂无知识点数据，请先创建题集并练习")
    st.stop()

# ========== 排序选项 ==========
sort_options = {
    "按掌握度从低到高": lambda x: x['mastery_score'],
    "按掌握度从高到低": lambda x: -x['mastery_score'],
    "按分类排序": lambda x: (0 if x['mastery_score'] < 60 else 1 if x['mastery_score'] < 80 else 2, x['mastery_score']),
    "按名称 A-Z": lambda x: x['topic']
}

col_sort, col_filter = st.columns([1, 1])
with col_sort:
    selected_sort = st.selectbox("📌 排序", list(sort_options.keys()))
with col_filter:
    filter_options = {
        "全部": lambda x: True,
        "🔴 薄弱点": lambda x: x['mastery_score'] < 60,
        "🟡 待巩固": lambda x: 60 <= x['mastery_score'] < 80,
        "🟢 优势点": lambda x: x['mastery_score'] >= 80
    }
    selected_filter = st.selectbox("🔍 筛选", list(filter_options.keys()))

# 应用排序和筛选
sorted_points = sorted(all_points, key=sort_options[selected_sort])
filtered_points = [p for p in sorted_points if filter_options[selected_filter](p)]

# ========== 显示统计 ==========
total = len(filtered_points)
weak = len([p for p in filtered_points if p['mastery_score'] < 60])
consolidate = len([p for p in filtered_points if 60 <= p['mastery_score'] < 80])
strong = len([p for p in filtered_points if p['mastery_score'] >= 80])

st.markdown(f"""
<div style="display:flex; gap:20px; margin-bottom:16px; flex-wrap:wrap;">
    <span style="font-size:14px;">📊 共 <strong>{total}</strong> 个知识点</span>
    <span style="font-size:14px; color:#FF4444;">🔴 薄弱 <strong>{weak}</strong></span>
    <span style="font-size:14px; color:#FFB800;">🟡 待巩固 <strong>{consolidate}</strong></span>
    <span style="font-size:14px; color:#00CC66;">🟢 优势 <strong>{strong}</strong></span>
</div>
""", unsafe_allow_html=True)

# ========== 颜色图例 ==========
st.markdown("""
<div style="display:flex; align-items:center; gap:6px; margin-bottom:16px;">
    <span style="font-size:12px; color:#FF0000;">0%</span>
    <div style="flex:1; height:10px; border-radius:6px; background:linear-gradient(to right, 
        #FF0000, #FF1A00, #FF4400, #FF6E00, #FF9900, #FFC400, #D4E000, #A8D500, #66CC33, #00CC66);">
    </div>
    <span style="font-size:12px; color:#00CC66;">100%</span>
</div>
""", unsafe_allow_html=True)

# ========== 卡片展示 ==========
if not filtered_points:
    st.info("📭 没有匹配的知识点")
else:
    weak_points = [p for p in filtered_points if p['mastery_score'] < 60]
    consolidate_points = [p for p in filtered_points if 60 <= p['mastery_score'] < 80]
    strong_points = [p for p in filtered_points if p['mastery_score'] >= 80]

    if weak_points:
        st.markdown("### 🔴 薄弱点")
        # 每行显示 6 个，自动换行
        per_row = 6
        for i in range(0, len(weak_points), per_row):
            row_points = weak_points[i:i + per_row]
            cols = st.columns(len(row_points))
            for j, wp in enumerate(row_points):
                with cols[j]:
                    color = get_color_by_mastery(wp['mastery_score'])
                    st.markdown(f"""
                    <div style="background:{color}; color:white; border-radius:10px; padding:16px 12px; text-align:center; min-height:80px; display:flex; flex-direction:column; justify-content:center; box-shadow:0 2px 8px rgba(0,0,0,0.1);">
                        <div style="font-size:15px; font-weight:bold; margin-bottom:4px;">{wp['topic']}</div>
                        <div style="font-size:24px; font-weight:bold;">{wp['mastery_score']}%</div>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button("🎯 攻克", key=f"weak_{wp['topic']}_{i}", use_container_width=True):
                        st.session_state.practice_mode = "mastery_board"
                        st.session_state.practice_topic = wp['topic']
                        st.switch_page("pages/generate_from_mastery.py")  # 👈 跳转到新页面
            st.markdown("---")

    if consolidate_points:
        st.markdown("### 🟡 待巩固")
        cols = st.columns(min(len(consolidate_points), 6))
        for i, wp in enumerate(consolidate_points):
            if i >= len(cols):
                break
            with cols[i]:
                color = get_color_by_mastery(wp['mastery_score'])
                st.markdown(f"""
                <div style="background:{color}; color:white; border-radius:10px; padding:16px 12px; text-align:center; min-height:80px; display:flex; flex-direction:column; justify-content:center; box-shadow:0 2px 8px rgba(0,0,0,0.1);">
                    <div style="font-size:15px; font-weight:bold; margin-bottom:4px;">{wp['topic']}</div>
                    <div style="font-size:24px; font-weight:bold;">{wp['mastery_score']}%</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("📖 练习", key=f"cons_{wp['topic']}_{i}", use_container_width=True):
                    st.session_state.practice_mode = "mastery_board"
                    st.session_state.practice_topic = wp['topic']
                    st.switch_page("pages/generate_from_mastery.py")
        st.markdown("---")

    if strong_points:
        st.markdown("### 🟢 优势点")
        cols = st.columns(min(len(strong_points), 6))
        for i, wp in enumerate(strong_points):
            if i >= len(cols):
                break
            with cols[i]:
                color = get_color_by_mastery(wp['mastery_score'])
                st.markdown(f"""
                <div style="background:{color}; color:white; border-radius:10px; padding:16px 12px; text-align:center; min-height:80px; display:flex; flex-direction:column; justify-content:center; box-shadow:0 2px 8px rgba(0,0,0,0.1);">
                    <div style="font-size:15px; font-weight:bold; margin-bottom:4px;">{wp['topic']}</div>
                    <div style="font-size:24px; font-weight:bold;">{wp['mastery_score']}%</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("⭐ 复习", key=f"strong_{wp['topic']}_{i}", use_container_width=True):
                    st.session_state.practice_mode = "mastery_board"
                    st.session_state.practice_topic = wp['topic']
                    st.switch_page("pages/generate_from_mastery.py")

st.markdown("---")
st.caption("💡 点击卡片上的按钮可进入做题巩固")