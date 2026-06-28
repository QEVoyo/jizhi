import streamlit as st
import requests
import random

BACKEND_URL = "https://ingenious-rejoicing-production-90b7.up.railway.app"

st.set_page_config(
    page_title="勤耕",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="auto"
)

st.markdown("""
<style>
    .stApp { background: var(--background-color); }
    .main .block-container { background: transparent; }

    h1, h2, h3, h4, h5, h6, p, span, div, label, .stMarkdown, .stCaption,
    .stButton button, .stAlert {
        text-shadow: 0 2px 8px rgba(0,0,0,0.08), 0 4px 16px rgba(0,0,0,0.04);
    }

    .stButton button {
        background: transparent !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 10px !important;
        color: var(--text-color) !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.04) !important;
        transition: all 0.3s ease !important;
        font-weight: 500 !important;
    }
    .stButton button:hover {
        background: rgba(128,128,128,0.04) !important;
        border-color: rgba(128,128,128,0.2) !important;
        box-shadow: 0 4px 16px rgba(0,0,0,0.08) !important;
        transform: translateY(-2px);
    }

    .track {
        background: rgba(128,128,128,0.2);
        border-radius: 4px;
        height: 8px;
        box-shadow: inset 0 1px 4px rgba(0,0,0,0.08);
        overflow: hidden;
        border: 1px solid rgba(128,128,128,0.08);
    }
    .track-fill {
        height: 100%;
        border-radius: 4px;
        transition: width 0.6s ease;
        box-shadow: 0 0 16px rgba(255,255,255,0.04);
    }

    .streamlit-expanderHeader {
        background: transparent !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 10px !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.04) !important;
        text-shadow: 0 2px 8px rgba(0,0,0,0.08), 0 4px 16px rgba(0,0,0,0.04) !important;
    }
    .streamlit-expanderHeader:hover {
        background: rgba(128,128,128,0.02) !important;
        border-color: rgba(128,128,128,0.15) !important;
        box-shadow: 0 4px 16px rgba(0,0,0,0.08) !important;
    }
    .streamlit-expanderContent {
        background: transparent !important;
        border: none !important;
    }

    hr { border-color: var(--border-color) !important; opacity: 0.3 !important; }
    .stAlert { background: transparent !important; border: 1px solid var(--border-color) !important; box-shadow: 0 2px 10px rgba(0,0,0,0.04) !important; }
</style>
""", unsafe_allow_html=True)

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("请先登录")
    st.stop()

user_id = st.session_state.user_id
access_token = st.session_state.access_token


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
    colors = {1: "#8B8B8B", 2: "#66CC66", 3: "#4CAF50", 4: "#26A69A",
              5: "#42A5F5", 6: "#7E57C2", 7: "#FF9800", 8: "#FF5722",
              9: "#F44336", 10: "#FFD700"}
    return colors.get(value, "#888")


def get_stars(value):
    return "★" * value


def progress_bar_html(progress, bar_color, show_label=True):
    pct = min(max(progress, 0), 100)
    label = f'<span style="font-size:11px; color:#888; text-shadow:0 1px 4px rgba(0,0,0,0.04); min-width:36px; text-align:right;">{pct}%</span>' if show_label else ""
    return f"""
    <div style="display:flex; align-items:center; gap:8px;">
        <div class="track" style="flex:1;">
            <div class="track-fill" style="width:{pct}%; background:{bar_color};"></div>
        </div>
        {label}
    </div>
    """


if st.button("← 返回学程"):
    st.switch_page("pages/career.py")

st.title("🌾 勤耕")
st.caption("日积月累，勤耕不辍")
st.markdown("---")

try:
    response = requests.get(f"{BACKEND_URL}/career/stats/{user_id}",
                            headers={"Authorization": f"Bearer {access_token}"}, timeout=10)
    stats = response.json() if response.status_code == 200 else {}
except:
    stats = {}

user_achievements = stats.get("achievements", [])

# ====== 🌰 播种 ======
st.markdown("### 🌰 播种")
st.caption("新手引导 · 第一次使用各项功能")

col1, col2, col3, col4, col5 = st.columns([1.2, 2.8, 1, 1, 2])
with col1: st.markdown("**状态**")
with col2: st.markdown("**种子**")
with col3: st.markdown("**收获**")
with col4: st.markdown("**价值**")
with col5: st.markdown("**进度**")
st.markdown("---")

seed_tasks = [
    {"name": "第一次登录", "reward": 5, "value": 1, "done": True, "progress": 100},
    {"name": "第一次修改昵称", "reward": 10, "value": 1, "done": True, "progress": 100},
    {"name": "第一次上传头像", "reward": 15, "value": 2, "done": False, "progress": 0},
    {"name": "第一次保存简介", "reward": 10, "value": 1, "done": False, "progress": 0},
    {"name": "第一次发送消息", "reward": 10, "value": 1, "done": False, "progress": 0},
    {"name": "第一次使用规划 Agent", "reward": 15, "value": 2, "done": False, "progress": 0},
    {"name": "第一次使用生成 Agent", "reward": 15, "value": 2, "done": False, "progress": 0},
    {"name": "第一次使用评估 Agent", "reward": 15, "value": 2, "done": False, "progress": 0},
    {"name": "第一次完成打卡", "reward": 15, "value": 2, "done": False, "progress": 0},
    {"name": "第一次使用计时器", "reward": 10, "value": 1, "done": False, "progress": 0},
    {"name": "第一次生成题目", "reward": 20, "value": 3, "done": False, "progress": 0},
    {"name": "第一次完成题目", "reward": 20, "value": 3, "done": False, "progress": 0},
    {"name": "第一次创建题集", "reward": 20, "value": 3, "done": False, "progress": 0},
    {"name": "第一次加入题目到题集", "reward": 15, "value": 2, "done": False, "progress": 0},
    {"name": "第一次攻克错题", "reward": 25, "value": 4, "done": False, "progress": 0},
    {"name": "第一次查看学情报告", "reward": 10, "value": 1, "done": False, "progress": 0},
    {"name": "第一次查看学程总览", "reward": 10, "value": 1, "done": False, "progress": 0},
    {"name": "第一次分享题目", "reward": 20, "value": 3, "done": False, "progress": 0},
]

done_count_seed = len([t for t in seed_tasks if t["done"]])
st.caption(f"进度：{done_count_seed}/{len(seed_tasks)}")

for i, task in enumerate(seed_tasks):
    col1, col2, col3, col4, col5 = st.columns([1.2, 2.8, 1, 1, 2])
    stars = get_stars(task["value"])
    star_color = get_star_color(task["value"])
    progress = task["progress"]
    bar_color = get_color_by_progress(progress)
    with col1:
        if task["done"]:
            st.button("✅", key=f"seed_done_{i}", disabled=True)
        elif progress >= 100:
            if st.button("🎁", key=f"seed_claim_{i}"):
                task["done"] = True
                st.rerun()
        else:
            st.button("⏳", key=f"seed_incomplete_{i}", disabled=True)
    with col2:
        st.markdown(f"{task['name']}")
    with col3:
        st.markdown(f"+{task['reward']}")
    with col4:
        st.markdown(f'<span style="color:{star_color}; text-shadow:0 0 12px {star_color}33;">{stars}</span>',
                    unsafe_allow_html=True)
    with col5:
        st.markdown(progress_bar_html(progress, bar_color), unsafe_allow_html=True)
st.markdown("---")

# ====== 🌱 施肥 ======
st.markdown("### 🌱 施肥")
st.caption("每日任务 · 完成获得收获")

col1, col2, col3, col4, col5 = st.columns([1.2, 2.8, 1, 1, 2])
with col1: st.markdown("**状态**")
with col2: st.markdown("**肥料**")
with col3: st.markdown("**收获**")
with col4: st.markdown("**价值**")
with col5: st.markdown("**进度**")
st.markdown("---")

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

if "daily_tasks" not in st.session_state:
    st.session_state.daily_tasks = random.sample(daily_task_pool, 5)
    st.session_state.daily_tasks_done = [False] * 5
    st.session_state.daily_tasks_progress = [random.randint(0, 100) for _ in range(5)]

if "refresh_used" not in st.session_state:
    st.session_state.refresh_used = False
if "daily_all_done" not in st.session_state:
    st.session_state.daily_all_done = False

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

for i, task in enumerate(st.session_state.daily_tasks):
    col1, col2, col3, col4, col5 = st.columns([1.2, 2.8, 1, 1, 2])
    done = st.session_state.daily_tasks_done[i]
    progress = st.session_state.daily_tasks_progress[i]
    stars = get_stars(task["value"])
    star_color = get_star_color(task["value"])
    bar_color = get_color_by_progress(progress)
    with col1:
        if done:
            st.button("✅", key=f"daily_done_{i}", disabled=True)
        elif progress >= 100:
            if st.button("🎁", key=f"daily_claim_{i}"):
                st.session_state.daily_tasks_done[i] = True
                st.rerun()
        else:
            st.button("⏳", key=f"daily_incomplete_{i}", disabled=True)
    with col2:
        st.markdown(f"{task['name']}")
    with col3:
        st.markdown(f"+{task['reward']}")
    with col4:
        st.markdown(f'<span style="color:{star_color}; text-shadow:0 0 12px {star_color}33;">{stars}</span>',
                    unsafe_allow_html=True)
    with col5:
        st.markdown(progress_bar_html(progress, bar_color), unsafe_allow_html=True)

st.markdown("---")

col1, col2, col3, col4, col5 = st.columns([1.2, 2.8, 1, 1, 2])
with col1:
    all_done = all(st.session_state.daily_tasks_done)
    if all_done and st.session_state.daily_all_done:
        st.button("✅", key="tasks_all_done", disabled=True)
    elif all_done and not st.session_state.daily_all_done:
        if st.button("🎁", key="tasks_all_claim"):
            st.session_state.daily_all_done = True
            st.rerun()
    else:
        st.button("⏳", key="tasks_all_incomplete", disabled=True)
with col2:
    st.markdown("🎯 完成全部每日任务")
with col3:
    st.markdown("+50")
with col4:
    st.markdown(f'<span style="color:{get_star_color(5)}; text-shadow:0 0 12px {get_star_color(5)}33;">★★★★★</span>',
                unsafe_allow_html=True)
with col5:
    done_count = sum(1 for d in st.session_state.daily_tasks_done if d)
    total = len(st.session_state.daily_tasks_done)
    pct = int(done_count / total * 100) if total > 0 else 0
    bar_color = get_color_by_progress(pct)
    st.markdown(progress_bar_html(pct, bar_color), unsafe_allow_html=True)

st.markdown("---")

# ====== 🌿 发芽 ======
st.markdown("### 🌿 发芽")
st.caption("长期耕耘 · 持续积累 · 阶梯解锁")

col1, col2, col3, col4, col5 = st.columns([1.2, 1.8, 1, 1, 2])
with col1: st.markdown("**状态**")
with col2: st.markdown("**扎根**")
with col3: st.markdown("**收获**")
with col4: st.markdown("**价值**")
with col5: st.markdown("**进度**")
st.markdown("---")

long_tasks = [
    {"name": "累计打卡 3 天", "reward": 20, "value": 2, "progress": 66, "done": False},
    {"name": "累计打卡 7 天", "reward": 30, "value": 2, "progress": 28, "locked": True, "done": False},
    {"name": "累计打卡 30 天", "reward": 100, "value": 3, "progress": 6, "locked": True, "done": False},
    {"name": "累计做 10 道题", "reward": 20, "value": 2, "progress": 80, "done": False},
    {"name": "累计做 50 道题", "reward": 50, "value": 2, "progress": 16, "locked": True, "done": False},
    {"name": "累计做 200 道题", "reward": 150, "value": 3, "progress": 4, "locked": True, "done": False},
]

for i, task in enumerate(long_tasks):
    col1, col2, col3, col4, col5 = st.columns([1.2, 1.8, 1, 1, 2])
    stars = get_stars(task["value"])
    star_color = get_star_color(task["value"])
    progress = task["progress"]
    bar_color = get_color_by_progress(progress)
    is_locked = task.get("locked", False)
    name_display = f"🔒 {task['name']}" if is_locked else task['name']
    with col1:
        if is_locked:
            st.button("🔒", key=f"long_locked_{i}", disabled=True)
        elif task["done"]:
            st.button("✅", key=f"long_done_{i}", disabled=True)
        elif progress >= 100:
            if st.button("🎁", key=f"long_claim_{i}"):
                task["done"] = True
                st.rerun()
        else:
            st.button("⏳", key=f"long_incomplete_{i}", disabled=True)
    with col2:
        st.markdown(name_display)
    with col3:
        st.markdown(f"+{task['reward']}")
    with col4:
        st.markdown(f'<span style="color:{star_color}; text-shadow:0 0 12px {star_color}33;">{stars}</span>',
                    unsafe_allow_html=True)
    with col5:
        st.markdown(progress_bar_html(progress, bar_color), unsafe_allow_html=True)

st.markdown("---")

# ====== 🌾 丰收 ======
st.markdown("### 🌾 丰收")
st.caption("最接近完成的成就 · 加把劲就能收获")

all_achievements = [
    {"id": "first_checkin", "name": "初入书海", "condition": "完成第 1 次打卡", "reward": 20, "value": 5,
     "progress": 100},
    {"id": "checkin_7", "name": "持之以恒", "condition": "连续打卡 7 天", "reward": 50, "value": 6, "progress": 85},
    {"id": "checkin_30", "name": "勤耕不辍", "condition": "累计打卡 30 天", "reward": 150, "value": 7, "progress": 45},
    {"id": "first_chat", "name": "初试锋芒", "condition": "第 1 次使用对话", "reward": 15, "value": 4, "progress": 100},
    {"id": "first_plan", "name": "思维缜密", "condition": "第 1 次使用规划 Agent", "reward": 20, "value": 5,
     "progress": 60},
    {"id": "first_generate", "name": "妙笔生花", "condition": "第 1 次使用生成 Agent", "reward": 20, "value": 5,
     "progress": 30},
    {"id": "first_evaluate", "name": "明察秋毫", "condition": "第 1 次使用评估 Agent", "reward": 20, "value": 5,
     "progress": 0},
    {"id": "questions_100", "name": "百题斩", "condition": "累计做 100 道题", "reward": 100, "value": 6,
     "progress": 92},
    {"id": "questions_1000", "name": "千题斩", "condition": "累计做 1000 道题", "reward": 300, "value": 9,
     "progress": 8},
    {"id": "mistakes_10", "name": "错题猎手", "condition": "攻克 10 道错题", "reward": 80, "value": 6, "progress": 65},
    {"id": "mistakes_100", "name": "错题克星", "condition": "攻克 100 道错题", "reward": 200, "value": 9,
     "progress": 12},
    {"id": "sets_5", "name": "题集收藏家", "condition": "创建 5 个题集", "reward": 50, "value": 6, "progress": 40},
    {"id": "sets_20", "name": "题集达人", "condition": "创建 20 个题集", "reward": 150, "value": 7, "progress": 10},
    {"id": "rank_mingli", "name": "学有所成", "condition": "晋升到「明理」段位", "reward": 100, "value": 7,
     "progress": 0},
    {"id": "rank_zhizhi", "name": "融会贯通", "condition": "晋升到「致知」段位", "reward": 150, "value": 8,
     "progress": 0},
    {"id": "rank_duxing", "name": "独当一面", "condition": "晋升到「笃行」段位", "reward": 200, "value": 8,
     "progress": 0},
    {"id": "rank_zhenjing", "name": "臻于至善", "condition": "晋升到「臻境」段位", "reward": 300, "value": 9,
     "progress": 0},
    {"id": "legend", "name": "传说", "condition": "晋升到「传说」称号", "reward": 500, "value": 10, "progress": 0},
    {"id": "share_10", "name": "分享达人", "condition": "分享 10 道题", "reward": 80, "value": 6, "progress": 20},
    {"id": "study_7", "name": "学习狂人", "condition": "连续学习 7 天", "reward": 100, "value": 7, "progress": 70},
    {"id": "timer_10h", "name": "时间管理", "condition": "使用计时器累计 10 小时", "reward": 120, "value": 7,
     "progress": 35},
    {"id": "logs_50", "name": "知识沉淀", "condition": "记录 50 条学习日志", "reward": 100, "value": 6, "progress": 15},
    {"id": "report_10", "name": "学海无涯", "condition": "查看学情报告 10 次", "reward": 80, "value": 6,
     "progress": 10},
    {"id": "share_receive_10", "name": "社交达人", "condition": "接受好友分享 10 次", "reward": 100, "value": 6,
     "progress": 0},
    {"id": "sets_50", "name": "筑梦者", "condition": "创建 50 个题集", "reward": 300, "value": 8, "progress": 0},
    {"id": "messages_500", "name": "对话大师", "condition": "累计发送 500 条消息", "reward": 150, "value": 7,
     "progress": 25},
]

for ach in all_achievements:
    ach["done"] = ach["progress"] >= 100

sorted_achievements = sorted(all_achievements, key=lambda x: x["progress"], reverse=True)
display_achievements = sorted_achievements[:8]

col1, col2, col3, col4, col5 = st.columns([1.2, 1.8, 1, 1, 2])
with col1: st.markdown("**状态**")
with col2: st.markdown("**果实**")
with col3: st.markdown("**收获**")
with col4: st.markdown("**价值**")
with col5: st.markdown("**进度**")
st.markdown("---")

for i, ach in enumerate(display_achievements):
    col1, col2, col3, col4, col5 = st.columns([1.2, 1.8, 1, 1, 2])
    stars = get_stars(ach["value"])
    star_color = get_star_color(ach["value"])
    progress = ach["progress"]
    bar_color = get_color_by_progress(progress)
    with col1:
        if ach["done"]:
            st.button("✅", key=f"ach_done_{i}", disabled=True)
        elif progress >= 100:
            if st.button("🎁", key=f"ach_claim_{i}"):
                ach["done"] = True
                st.rerun()
        else:
            st.button("⏳", key=f"ach_incomplete_{i}", disabled=True)
    with col2:
        st.markdown(f"{ach['name']}")
        st.caption(ach["condition"])
    with col3:
        st.markdown(f"+{ach['reward']}")
    with col4:
        st.markdown(f'<span style="color:{star_color}; text-shadow:0 0 12px {star_color}33;">{stars}</span>',
                    unsafe_allow_html=True)
    with col5:
        st.markdown(progress_bar_html(progress, bar_color), unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("📋 查看全部成就 →", use_container_width=True):
        st.switch_page("pages/career_achievements.py")