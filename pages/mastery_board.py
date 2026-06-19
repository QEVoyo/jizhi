import streamlit as st

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


def get_mock_knowledge_points():
    """模拟知识点掌握度数据"""
    return [
        {"topic": "装饰器", "mastery_score": 35, "question_id": "q1"},
        {"topic": "递归函数", "mastery_score": 42, "question_id": "q2"},
        {"topic": "GIL锁", "mastery_score": 55, "question_id": "q3"},
        {"topic": "列表推导式", "mastery_score": 68, "question_id": "q4"},
        {"topic": "lambda函数", "mastery_score": 72, "question_id": "q5"},
        {"topic": "闭包", "mastery_score": 65, "question_id": "q6"},
        {"topic": "生成器", "mastery_score": 48, "question_id": "q7"},
        {"topic": "类与对象", "mastery_score": 92, "question_id": "q8"},
        {"topic": "异常处理", "mastery_score": 88, "question_id": "q9"},
        {"topic": "文件操作", "mastery_score": 85, "question_id": "q10"},
        {"topic": "多线程", "mastery_score": 90, "question_id": "q11"},
        {"topic": "协程", "mastery_score": 86, "question_id": "q12"},
    ]


# ========== 页面标题 ==========
col_back, col_title = st.columns([1, 5])
with col_back:
    if st.button("← 返回", use_container_width=True):
        st.switch_page("pages/resource_lib.py")
with col_title:
    st.title("📊 掌握度看板")
    st.caption("全部知识点的掌握情况一目了然")

st.markdown("---")

# ========== 获取数据 ==========
all_points = get_mock_knowledge_points()

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
    # 按分类分组展示
    weak_points = [p for p in filtered_points if p['mastery_score'] < 60]
    consolidate_points = [p for p in filtered_points if 60 <= p['mastery_score'] < 80]
    strong_points = [p for p in filtered_points if p['mastery_score'] >= 80]

    # 薄弱点
    if weak_points:
        st.markdown("### 🔴 薄弱点")
        cols = st.columns(min(len(weak_points), 6))
        for i, wp in enumerate(weak_points):
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
                if st.button("🎯 攻克", key=f"weak_{wp['topic']}_{i}", use_container_width=True):
                    st.session_state.current_weak_point = wp
                    st.switch_page("pages/do_question.py")
        st.markdown("---")

    # 待巩固
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
                    st.session_state.current_weak_point = wp
                    st.switch_page("pages/do_question.py")
        st.markdown("---")

    # 优势点
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
                    st.session_state.current_weak_point = wp
                    st.switch_page("pages/do_question.py")

st.markdown("---")
st.caption("💡 点击卡片上的按钮可进入做题巩固")