import streamlit as st
import requests
import random

BACKEND_URL = "https://ingenious-rejoicing-production-90b7.up.railway.app"

st.set_page_config(
    page_title="学程",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="auto"
)

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("请先登录")
    st.stop()

user_id = st.session_state.user_id
access_token = st.session_state.access_token

# ====== 段位配置 ======
rank_icons = {
    "启程": "◈",
    "求索": "❖",
    "明理": "✧",
    "致知": "✦",
    "笃行": "✹",
    "臻境": "❋",
    "传说": "★"
}
rank_colors = {
    "启程": "#8B8B8B",
    "求索": "#4FC3F7",
    "明理": "#4CAF50",
    "致知": "#FFB300",
    "笃行": "#FF6F00",
    "臻境": "#9C27B0",
    "传说": "#FF6B6B"
}
sub_symbols = {1: "○", 2: "◌", 3: "◎", 4: "◍", 5: "●"}


def get_color_by_progress(score):
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


def get_star_color(value):
    colors = {
        1: "#8B8B8B",
        2: "#66CC66",
        3: "#4CAF50",
        4: "#26A69A",
        5: "#42A5F5",
        6: "#7E57C2",
        7: "#FF9800",
        8: "#FF5722",
        9: "#F44336",
        10: "#FFD700"
    }
    return colors.get(value, "#888")


def get_stars(value):
    return "★" * value


# ====== 每日任务池 ======
daily_task_pool = [
    {"name": "发送 5 条消息", "reward": 10, "value": 1},
    {"name": "发送 10 条消息", "reward": 15, "value": 2},
    {"name": "使用计时器 15 分钟", "reward": 10, "value": 1},
    {"name": "使用计时器 30 分钟", "reward": 15, "value": 2},
    {"name": "生成 2 道题目", "reward": 15, "value": 2},
    {"name": "生成 3 道题目", "reward": 20, "value": 3},
    {"name": "做 5 道题", "reward": 25, "value": 3},
    {"name": "做 8 道题", "reward": 35, "value": 4},
    {"name": "攻克 1 道错题", "reward": 20, "value": 3},
    {"name": "攻克 2 道错题", "reward": 30, "value": 4},
    {"name": "分享 1 道题", "reward": 10, "value": 1},
    {"name": "分享 2 道题", "reward": 15, "value": 2},
    {"name": "创建 1 个题集", "reward": 15, "value": 2},
    {"name": "练习 1 个题集", "reward": 15, "value": 2},
    {"name": "完成 1 次打卡", "reward": 10, "value": 1},
    {"name": "查看学情报告", "reward": 10, "value": 1},
    {"name": "使用规划 Agent 1 次", "reward": 10, "value": 1},
    {"name": "使用生成 Agent 3 次", "reward": 15, "value": 2},
    {"name": "使用评估 Agent 1 次", "reward": 10, "value": 1},
]

# ====== 初始化每日任务（与勤耕共用 session_state）======
if "daily_tasks" not in st.session_state:
    st.session_state.daily_tasks = random.sample(daily_task_pool, 5)
    st.session_state.daily_tasks_done = [False] * 5
    st.session_state.daily_tasks_progress = [random.randint(0, 100) for _ in range(5)]

if "refresh_used" not in st.session_state:
    st.session_state.refresh_used = False

if "daily_all_done" not in st.session_state:
    st.session_state.daily_all_done = False


# ====== 获取用户数据 ======
try:
    response = requests.get(
        f"{BACKEND_URL}/career/stats/{user_id}",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10
    )
    if response.status_code == 200:
        stats = response.json()
    else:
        stats = {}
except:
    stats = {}

points = stats.get("points", 0)
weight_points = stats.get("weight_points", 0)
rank = stats.get("rank", "启程")
sub_rank = stats.get("sub_rank", 1)
is_legend = stats.get("is_legend", False)

symbol = sub_symbols.get(sub_rank, "○")
icon = rank_icons.get(rank, "◈")
color = rank_colors.get(rank, "#FFFFFF")

# 计算等级
level = 1
total_needed = 0
while True:
    total_needed += level
    if weight_points < total_needed:
        break
    level += 1


# ====== 左侧菜单 ======
with st.sidebar:
    st.markdown("## 🗺️ 学程")

    st.page_link("pages/career_rank.py", label="⛰️ 登攀")
    st.page_link("pages/career_tasks.py", label="🌾 勤耕")
    st.page_link("pages/career_achievements.py", label="🐚 拾贝")

    if st.button("← 返回主界面", use_container_width=True):
        st.switch_page("app.py")


# ====== 主内容 ======
st.title("🗺️ 学程")
st.caption("学习旅程总览")

st.markdown("---")

# 第一行：段位 + 等级
col1, col2 = st.columns(2)

with col1:
    st.markdown(f"""
    <div style="color:{color}; font-size:28px; font-weight:bold;">
        {icon} {rank} {symbol}
    </div>
    <div style="color:{color}; font-size:18px; margin-top:4px;">
        {points} 分
    </div>
    """, unsafe_allow_html=True)

    rank_order = ["启程", "求索", "明理", "致知", "笃行", "臻境", "传说"]
    rank_index = rank_order.index(rank) if rank in rank_order else 0
    base_points = rank_index * 500
    sub_start = base_points + (sub_rank - 1) * 100
    sub_end = base_points + sub_rank * 100
    progress = max(0, min((points - sub_start) / 100, 1))
    bar_color = get_color_by_progress(progress * 100)

    st.markdown(f"""
    <div style="width:100%; height:8px; background:#2a2a3a; border-radius:4px; overflow:hidden; margin:8px 0;">
        <div style="width:{progress * 100}%; height:100%; background:{bar_color}; border-radius:4px;"></div>
    </div>
    """, unsafe_allow_html=True)
    st.caption(f"距离下一小段还需 {sub_end - points} 分")

with col2:
    st.markdown(f"### ⭐ Lv.{level}")
    st.markdown(f"**权重积分: {weight_points}**")

    next_needed = level
    next_total = total_needed + next_needed
    level_progress = max(0, min((weight_points - total_needed) / next_needed, 1))
    level_color = get_color_by_progress(level_progress * 100)

    st.markdown(f"""
    <div style="width:100%; height:8px; background:#2a2a3a; border-radius:4px; overflow:hidden; margin:8px 0;">
        <div style="width:{level_progress * 100}%; height:100%; background:{level_color}; border-radius:4px;"></div>
    </div>
    """, unsafe_allow_html=True)
    st.caption(f"距离 Lv.{level + 1} 还需 {next_total - weight_points} 分")

st.markdown("---")

# ====== 今日施肥（与勤耕共用 session_state）======
st.markdown("### 🌱 今日施肥")
st.caption("每日任务 · 完成获得收获")

# 表头
col1, col2, col3, col4, col5 = st.columns([1.2, 2.8, 1, 1, 2])
with col1:
    st.markdown("**状态**")
with col2:
    st.markdown("**肥料**")
with col3:
    st.markdown("**收获**")
with col4:
    st.markdown("**价值**")
with col5:
    st.markdown("**进度**")
st.markdown("---")

# 换一批按钮（与勤耕共用 refresh_used）
col_refresh, _ = st.columns([1, 5])
with col_refresh:
    if st.session_state.refresh_used:
        st.button("🔄 已使用", use_container_width=True, disabled=True)
    else:
        if st.button("🔄 换一批", use_container_width=True):
            st.session_state.daily_tasks = random.sample(daily_task_pool, 5)
            st.session_state.daily_tasks_done = [False] * 5
            st.session_state.daily_tasks_progress = [random.randint(0, 100) for _ in range(5)]
            st.session_state.refresh_used = True
            st.session_state.daily_all_done = False
            st.rerun()

# 显示任务列表
for i, task in enumerate(st.session_state.daily_tasks):
    col1, col2, col3, col4, col5 = st.columns([1.2, 2.8, 1, 1, 2])
    done = st.session_state.daily_tasks_done[i]
    progress = st.session_state.daily_tasks_progress[i]
    stars = get_stars(task["value"])
    star_color = get_star_color(task["value"])
    bar_color = get_color_by_progress(progress)

    with col1:
        if done:
            st.button("✅", key=f"career_daily_done_{i}", disabled=True)
        elif progress >= 100:
            if st.button("🎁", key=f"career_daily_claim_{i}"):
                st.session_state.daily_tasks_done[i] = True
                st.rerun()
        else:
            st.button("⏳", key=f"career_daily_incomplete_{i}", disabled=True)
    with col2:
        st.markdown(f"{task['name']}")
    with col3:
        st.markdown(f"+{task['reward']}")
    with col4:
        st.markdown(f'<span style="color:{star_color};">{stars}</span>', unsafe_allow_html=True)
    with col5:
        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:6px;">
            <div style="flex:1; height:6px; background:#2a2a3a; border-radius:3px; overflow:hidden;">
                <div style="width:{progress}%; height:100%; background:{bar_color}; border-radius:3px;"></div>
            </div>
            <span style="font-size:11px; color:#888;">{progress}%</span>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# ====== 全部完成奖励 ======
col1, col2, col3, col4, col5 = st.columns([1.2, 2.8, 1, 1, 2])
with col1:
    all_done = all(st.session_state.daily_tasks_done)
    if all_done and st.session_state.daily_all_done:
        st.button("✅", key="career_all_done", disabled=True)
    elif all_done and not st.session_state.daily_all_done:
        if st.button("🎁", key="career_all_claim"):
            st.session_state.daily_all_done = True
            st.rerun()
    else:
        st.button("⏳", key="career_all_incomplete", disabled=True)
with col2:
    st.markdown("🎯 完成全部每日任务")
with col3:
    st.markdown("+50")
with col4:
    st.markdown(f'<span style="color:{get_star_color(5)};">★★★★★</span>', unsafe_allow_html=True)
with col5:
    done_count = sum(1 for d in st.session_state.daily_tasks_done if d)
    total = len(st.session_state.daily_tasks_done)
    pct = int(done_count / total * 100) if total > 0 else 0
    bar_color = get_color_by_progress(pct)
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:6px;">
        <div style="flex:1; height:6px; background:#2a2a3a; border-radius:3px; overflow:hidden;">
            <div style="width:{pct}%; height:100%; background:{bar_color}; border-radius:3px;"></div>
        </div>
        <span style="font-size:11px; color:#888;">{done_count}/{total}</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ====== 即将拾贝 ======
st.markdown("### 🎯 即将拾贝")
st.caption("最接近完成的成就")

achievements = [
    {"name": "百题斩", "progress": 47, "total": 100},
    {"name": "错题猎手", "progress": 3, "total": 10},
    {"name": "持之以恒", "progress": 5, "total": 7},
]

for ach in achievements:
    pct = int(ach["progress"] / ach["total"] * 100)
    bar_color = get_color_by_progress(pct)
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:8px; margin-bottom:6px;">
        <span style="font-size:13px; width:80px;">{ach['name']}</span>
        <div style="flex:1; height:6px; background:#2a2a3a; border-radius:3px; overflow:hidden;">
            <div style="width:{pct}%; height:100%; background:{bar_color}; border-radius:3px;"></div>
        </div>
        <span style="font-size:11px; color:#888;">{ach['progress']}/{ach['total']}</span>
    </div>
    """, unsafe_allow_html=True)