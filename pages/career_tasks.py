import streamlit as st
import requests
import random
import base64
import os

BACKEND_URL = "https://ingenious-rejoicing-production-90b7.up.railway.app"

st.set_page_config(
    page_title="勤耕",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="auto"
)

# ====== 背景图 ======
def get_base64_image(img_path):
    with open(img_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

img_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "career_tasks_bg.jpg")
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
    .stButton button, .stAlert {{
        text-shadow: 0 2px 8px rgba(0,0,0,0.08), 0 4px 16px rgba(0,0,0,0.04);
    }}

    .stButton button {{
        background: transparent !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 10px !important;
        color: var(--text-color) !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.04) !important;
        transition: all 0.3s ease !important;
        font-weight: 500 !important;
        text-shadow: 0 2px 8px rgba(0,0,0,0.08), 0 4px 16px rgba(0,0,0,0.04) !important;
    }}
    .stButton button:hover {{
        background: rgba(128,128,128,0.04) !important;
        border-color: rgba(128,128,128,0.2) !important;
        box-shadow: 0 4px 16px rgba(0,0,0,0.08) !important;
        transform: translateY(-2px);
    }}

    .track {{
        background: rgba(128,128,128,0.2);
        border-radius: 4px;
        height: 8px;
        box-shadow: inset 0 1px 4px rgba(0,0,0,0.08);
        overflow: hidden;
        border: 1px solid rgba(128,128,128,0.08);
    }}
    .track-fill {{
        height: 100%;
        border-radius: 4px;
        transition: width 0.6s ease;
        box-shadow: 0 0 16px rgba(255,255,255,0.04);
    }}

    .streamlit-expanderHeader {{
        background: transparent !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 10px !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.04) !important;
        text-shadow: 0 2px 8px rgba(0,0,0,0.08), 0 4px 16px rgba(0,0,0,0.04) !important;
    }}
    .streamlit-expanderHeader:hover {{
        background: rgba(128,128,128,0.02) !important;
        border-color: rgba(128,128,128,0.15) !important;
        box-shadow: 0 4px 16px rgba(0,0,0,0.08) !important;
    }}
    .streamlit-expanderContent {{
        background: transparent !important;
        border: none !important;
    }}

    hr {{ border-color: var(--border-color) !important; opacity: 0.3 !important; }}
    .stAlert {{ background: transparent !important; border: 1px solid var(--border-color) !important; box-shadow: 0 2px 10px rgba(0,0,0,0.04) !important; }}
</style>
""", unsafe_allow_html=True)

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("请先登录")
    st.stop()

user_id = st.session_state.user_id
access_token = st.session_state.access_token


# ====== 工具函数 ======
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
    label = f'<span style="font-size:11px; color:#888; min-width:36px; text-align:right;">{pct}%</span>' if show_label else ""
    return f'''
    <div style="display:flex; align-items:center; gap:8px;">
        <div style="flex:1; background:rgba(128,128,128,0.15); border-radius:4px; height:8px; box-shadow:inset 0 1px 4px rgba(0,0,0,0.06); overflow:hidden;">
            <div style="width:{pct}%; height:100%; background:{bar_color}; border-radius:4px; transition:width 0.6s ease; box-shadow:0 0 16px rgba(255,255,255,0.04);"></div>
        </div>
        {label}
    </div>
    '''


def claim_reward(user_id, access_token, reward_points, task_name):
    """领取奖励，调用后端加分接口"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/career/stats/update",
            json={
                "user_id": user_id,
                "points_change": reward_points
            },
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        if response.status_code == 200:
            st.toast(f"✅ 获得 {reward_points} 分！", icon="🎉")
            return True
        else:
            st.error("领取失败，请稍后重试")
            return False
    except Exception as e:
        st.error(f"网络错误：{e}")
        return False


# ====== 返回按钮 ======
if st.button("← 返回学程"):
    st.switch_page("pages/career.py")

st.title("🌾 勤耕")
st.caption("日积月累，勤耕不辍")
st.markdown("---")

# ====== 获取任务数据 ======
try:
    response = requests.get(
        f"{BACKEND_URL}/career/task-progress/{user_id}",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10
    )
    if response.status_code == 200:
        task_data = response.json()
    else:
        task_data = {"seed": [], "daily": [], "long": [], "achievements": []}
except:
    task_data = {"seed": [], "daily": [], "long": [], "achievements": []}

seed_tasks = task_data.get("seed", [])
daily_tasks = task_data.get("daily", [])
long_tasks = task_data.get("long", [])
achievements = task_data.get("achievements", [])

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

done_count_seed = len([t for t in seed_tasks if t.get("done", False)])
st.caption(f"进度：{done_count_seed}/{len(seed_tasks)}")

for i, task in enumerate(seed_tasks):
    col1, col2, col3, col4, col5 = st.columns([1.2, 2.8, 1, 1, 2])
    stars = get_stars(task.get("value", 1))
    star_color = get_star_color(task.get("value", 1))
    progress = task.get("progress", 0)
    bar_color = get_color_by_progress(progress)
    done = task.get("done", False)

    with col1:
        if done:
            st.button("✅", key=f"seed_done_{i}", disabled=True)
        elif progress >= 100:
            if st.button("🎁", key=f"seed_claim_{i}"):
                reward = task.get("reward", 0)
                if claim_reward(user_id, access_token, reward, task.get("name", "")):
                    # 标记为已领取（前端暂存，刷新后从后端重新获取）
                    st.session_state[f"seed_claimed_{i}"] = True
                    st.rerun()
        else:
            st.button("⏳", key=f"seed_incomplete_{i}", disabled=True)
    with col2:
        st.markdown(f"{task.get('name', '')}")
    with col3:
        st.markdown(f"+{task.get('reward', 0)}")
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

# 换一批按钮
col_refresh, _ = st.columns([1, 5])
with col_refresh:
    if "refresh_used" not in st.session_state:
        st.session_state.refresh_used = False
    if st.session_state.refresh_used:
        st.button("🔄 已使用", use_container_width=True, disabled=True)
    else:
        if st.button("🔄 换一批", use_container_width=True):
            # 重新随机选择每日任务
            st.session_state.refresh_used = True
            st.rerun()

# 显示每日任务（从接口获取，但前端做随机选择）
if "daily_task_pool" not in st.session_state:
    # 从接口数据中提取每日任务定义
    daily_task_defs = [
        {"name": "发送 5 条消息", "action": "chat", "target": 5, "reward": 10, "value": 1},
        {"name": "发送 10 条消息", "action": "chat", "target": 10, "reward": 15, "value": 2},
        {"name": "发送 20 条消息", "action": "chat", "target": 20, "reward": 25, "value": 3},
        {"name": "使用计时器 15 分钟", "action": "use_timer", "target": 1, "reward": 10, "value": 1},
        {"name": "使用计时器 30 分钟", "action": "use_timer", "target": 2, "reward": 15, "value": 2},
        {"name": "使用计时器 60 分钟", "action": "use_timer", "target": 4, "reward": 25, "value": 3},
        {"name": "生成 2 道题目", "action": "generate_question", "target": 2, "reward": 15, "value": 2},
        {"name": "生成 3 道题目", "action": "generate_question", "target": 3, "reward": 20, "value": 3},
        {"name": "生成 5 道题目", "action": "generate_question", "target": 5, "reward": 30, "value": 4},
        {"name": "做 5 道题", "action": "complete_question", "target": 5, "reward": 25, "value": 3},
        {"name": "做 8 道题", "action": "complete_question", "target": 8, "reward": 35, "value": 4},
        {"name": "做 15 道题", "action": "complete_question", "target": 15, "reward": 50, "value": 5},
        {"name": "攻克 1 道错题", "action": "conquer_mistake", "target": 1, "reward": 20, "value": 3},
        {"name": "攻克 2 道错题", "action": "conquer_mistake", "target": 2, "reward": 30, "value": 4},
        {"name": "攻克 5 道错题", "action": "conquer_mistake", "target": 5, "reward": 50, "value": 5},
        {"name": "创建 1 个题集", "action": "create_set", "target": 1, "reward": 15, "value": 2},
        {"name": "创建 2 个题集", "action": "create_set", "target": 2, "reward": 25, "value": 3},
        {"name": "创建 3 个题集", "action": "create_set", "target": 3, "reward": 35, "value": 4},
        {"name": "加入 1 道题到题集", "action": "add_to_set", "target": 1, "reward": 10, "value": 1},
        {"name": "加入 3 道题到题集", "action": "add_to_set", "target": 3, "reward": 20, "value": 2},
        {"name": "加入 5 道题到题集", "action": "add_to_set", "target": 5, "reward": 30, "value": 3},
        {"name": "完成 1 次打卡", "action": "checkin", "target": 1, "reward": 10, "value": 1},
        {"name": "完成 2 次打卡", "action": "checkin", "target": 2, "reward": 15, "value": 2},
        {"name": "完成 3 次打卡", "action": "checkin", "target": 3, "reward": 20, "value": 3},
        {"name": "查看学情报告 1 次", "action": "view_report", "target": 1, "reward": 10, "value": 1},
        {"name": "查看学情报告 2 次", "action": "view_report", "target": 2, "reward": 15, "value": 2},
        {"name": "查看学情报告 3 次", "action": "view_report", "target": 3, "reward": 20, "value": 3},
        {"name": "使用规划 Agent 1 次", "action": "use_plan_agent", "target": 1, "reward": 10, "value": 1},
        {"name": "使用规划 Agent 2 次", "action": "use_plan_agent", "target": 2, "reward": 15, "value": 2},
        {"name": "使用规划 Agent 3 次", "action": "use_plan_agent", "target": 3, "reward": 20, "value": 3},
        {"name": "使用生成 Agent 3 次", "action": "use_generate_agent", "target": 3, "reward": 15, "value": 2},
        {"name": "使用生成 Agent 5 次", "action": "use_generate_agent", "target": 5, "reward": 25, "value": 3},
        {"name": "使用生成 Agent 10 次", "action": "use_generate_agent", "target": 10, "reward": 40, "value": 4},
        {"name": "使用评估 Agent 1 次", "action": "use_evaluate_agent", "target": 1, "reward": 10, "value": 1},
        {"name": "使用评估 Agent 2 次", "action": "use_evaluate_agent", "target": 2, "reward": 15, "value": 2},
        {"name": "使用评估 Agent 3 次", "action": "use_evaluate_agent", "target": 3, "reward": 20, "value": 3},
    ]
    st.session_state.daily_task_pool = daily_task_defs
    st.session_state.daily_tasks = random.sample(daily_task_defs, 5)
    st.session_state.daily_tasks_done = [False] * 5
    st.session_state.daily_tasks_progress = [0] * 5

# 更新每日任务进度（从接口数据中获取）
if daily_tasks:
    for i, task in enumerate(st.session_state.daily_tasks):
        # 从接口数据中匹配同名任务
        for dt in daily_tasks:
            if dt.get("name") == task.get("name"):
                st.session_state.daily_tasks_progress[i] = dt.get("progress", 0)
                if dt.get("done", False):
                    st.session_state.daily_tasks_done[i] = True
                break

for i, task in enumerate(st.session_state.daily_tasks):
    col1, col2, col3, col4, col5 = st.columns([1.2, 2.8, 1, 1, 2])
    done = st.session_state.daily_tasks_done[i] if i < len(st.session_state.daily_tasks_done) else False
    progress = st.session_state.daily_tasks_progress[i] if i < len(st.session_state.daily_tasks_progress) else 0
    stars = get_stars(task.get("value", 1))
    star_color = get_star_color(task.get("value", 1))
    bar_color = get_color_by_progress(progress)

    with col1:
        if done:
            st.button("✅", key=f"daily_done_{i}", disabled=True)
        elif progress >= 100:
            if st.button("🎁", key=f"daily_claim_{i}"):
                reward = task.get("reward", 0)
                if claim_reward(user_id, access_token, reward, task.get("name", "")):
                    st.session_state.daily_tasks_done[i] = True
                    st.rerun()
        else:
            st.button("⏳", key=f"daily_incomplete_{i}", disabled=True)
    with col2:
        st.markdown(f"{task.get('name', '')}")
    with col3:
        st.markdown(f"+{task.get('reward', 0)}")
    with col4:
        st.markdown(f'<span style="color:{star_color}; text-shadow:0 0 12px {star_color}33;">{stars}</span>',
                    unsafe_allow_html=True)
    with col5:
        st.markdown(progress_bar_html(progress, bar_color), unsafe_allow_html=True)

st.markdown("---")

# ====== 全部完成奖励 ======
col1, col2, col3, col4, col5 = st.columns([1.2, 2.8, 1, 1, 2])
with col1:
    all_done = all(st.session_state.daily_tasks_done) if st.session_state.daily_tasks_done else False
    if "daily_all_done" not in st.session_state:
        st.session_state.daily_all_done = False
    if all_done and st.session_state.daily_all_done:
        st.button("✅", key="tasks_all_done", disabled=True)
    elif all_done and not st.session_state.daily_all_done:
        if st.button("🎁", key="tasks_all_claim"):
            if claim_reward(user_id, access_token, 50, "完成全部每日任务"):
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
    done_count = sum(1 for d in st.session_state.daily_tasks_done if d) if st.session_state.daily_tasks_done else 0
    total = len(st.session_state.daily_tasks_done) if st.session_state.daily_tasks_done else 1
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

for i, task in enumerate(long_tasks):
    col1, col2, col3, col4, col5 = st.columns([1.2, 1.8, 1, 1, 2])
    stars = get_stars(task.get("value", 1))
    star_color = get_star_color(task.get("value", 1))
    progress = task.get("progress", 0)
    bar_color = get_color_by_progress(progress)
    done = task.get("done", False)

    with col1:
        if done:
            st.button("✅", key=f"long_done_{i}", disabled=True)
        elif progress >= 100:
            if st.button("🎁", key=f"long_claim_{i}"):
                reward = task.get("reward", 0)
                if claim_reward(user_id, access_token, reward, task.get("name", "")):
                    st.rerun()
        else:
            st.button("⏳", key=f"long_incomplete_{i}", disabled=True)
    with col2:
        st.markdown(f"{task.get('name', '')}")
    with col3:
        st.markdown(f"+{task.get('reward', 0)}")
    with col4:
        st.markdown(f'<span style="color:{star_color}; text-shadow:0 0 12px {star_color}33;">{stars}</span>',
                    unsafe_allow_html=True)
    with col5:
        st.markdown(progress_bar_html(progress, bar_color), unsafe_allow_html=True)

st.markdown("---")

# ====== 🌾 丰收 ======
st.markdown("### 🌾 丰收")
st.caption("最接近完成的成就 · 加把劲就能收获")

# 显示未完成的成就（按进度排序，取前8个）
pending_achievements = [a for a in achievements if not a.get("done", False)]
pending_achievements.sort(key=lambda x: 0)  # 可以按进度排序

# 从已完成成就中取一些接近完成的
# 实际上所有成就都在 achievements 里，我们只显示未完成的
display_achievements = pending_achievements[:8]

if not display_achievements:
    st.info("🎉 所有成就已解锁！继续加油！")
else:
    col1, col2, col3, col4, col5 = st.columns([1.2, 1.8, 1, 1, 2])
    with col1:
        st.markdown("**状态**")
    with col2:
        st.markdown("**果实**")
    with col3:
        st.markdown("**收获**")
    with col4:
        st.markdown("**价值**")
    with col5:
        st.markdown("**进度**")
    st.markdown("---")

    for i, ach in enumerate(display_achievements):
        col1, col2, col3, col4, col5 = st.columns([1.2, 1.8, 1, 1, 2])
        stars = get_stars(ach.get("value", 1))
        star_color = get_star_color(ach.get("value", 1))
        progress = 0  # 成就进度需要另外计算，暂时用0
        bar_color = get_color_by_progress(progress)

        with col1:
            if ach.get("done", False):
                st.button("✅", key=f"ach_done_{i}", disabled=True)
            else:
                st.button("⏳", key=f"ach_incomplete_{i}", disabled=True)
        with col2:
            st.markdown(f"{ach.get('name', '')}")
        with col3:
            st.markdown(f"+{ach.get('reward', 0)}")
        with col4:
            st.markdown(f'<span style="color:{star_color}; text-shadow:0 0 12px {star_color}33;">{stars}</span>',
                        unsafe_allow_html=True)
        with col5:
            st.markdown(progress_bar_html(progress, bar_color), unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("📋 查看全部成就 →", use_container_width=True):
        st.switch_page("pages/career_achievements.py")