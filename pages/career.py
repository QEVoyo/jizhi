import streamlit as st
import requests
import random
import base64
import os

BACKEND_URL = "https://ingenious-rejoicing-production-90b7.up.railway.app"

st.set_page_config(
    page_title="学程",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="auto"
)

# ====== 背景图 Base64 ======
def get_base64_image(img_path):
    with open(img_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# pages/career.py 在 pages/ 目录下，assets 在根目录，所以用 ../assets/
img_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "career_bg.png")
img_base64 = get_base64_image(img_path)

st.markdown(f"""
<style>
     .stApp {{
        background: var(--background-color);
        background-image: 
            linear-gradient(rgba(255,255,255,0.60), rgba(255,255,255,0.60)),
            url("data:image/png;base64,{img_base64}");
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

    .glass-card {{
        background: transparent;
        border-radius: 16px;
        padding: 24px 28px;
        border: 1px solid var(--border-color);
        box-shadow: 0 2px 12px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    }}
    .glass-card:hover {{
        border-color: rgba(128,128,128,0.15);
        box-shadow: 0 6px 24px rgba(0,0,0,0.08);
        transform: translateY(-1px);
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

# ====== 记录查看学程（仅第一次） ======
if "career_recorded" not in st.session_state:
    try:
        requests.post(
            f"{BACKEND_URL}/career/actions/record",
            json={
                "user_id": st.session_state.user_id,
                "action_type": "view_career",
                "metadata": {}
            },
            timeout=3
        )
        st.session_state.career_recorded = True
    except:
        pass

rank_icons = {
    "启程": "◈", "求索": "❖", "明理": "✧",
    "致知": "✦", "笃行": "✹", "臻境": "❋", "传说": "★"
}
rank_colors = {
    "启程": "#8B8B8B", "求索": "#4FC3F7", "明理": "#4CAF50",
    "致知": "#FFB300", "笃行": "#FF6F00", "臻境": "#9C27B0", "传说": "#FF6B6B"
}
sub_symbols = {1: "○", 2: "◌", 3: "◎", 4: "◍", 5: "●"}
rank_order = ["启程", "求索", "明理", "致知", "笃行", "臻境", "传说"]


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

# 获取 stats（段位数据）
try:
    stats_res = requests.get(f"{BACKEND_URL}/career/stats/{user_id}",
                             headers={"Authorization": f"Bearer {access_token}"}, timeout=10)
    stats = stats_res.json() if stats_res.status_code == 200 else {}
except:
    stats = {}

points = stats.get("points", 0)
weight_points = stats.get("weight_points", 0)
rank = stats.get("rank", "启程")
sub_rank = stats.get("sub_rank", 1)
symbol = sub_symbols.get(sub_rank, "○")
icon = rank_icons.get(rank, "◈")
color = rank_colors.get(rank, "#FFFFFF")

level = 1
total_needed = 0
while True:
    total_needed += level
    if weight_points < total_needed:
        break
    level += 1

with st.sidebar:
    st.markdown("## 🗺️ 学程")
    st.page_link("pages/career_rank.py", label="⛰️ 登攀")
    st.page_link("pages/career_tasks.py", label="🌾 勤耕")
    st.page_link("pages/career_achievements.py", label="🐚 拾贝")
    if st.button("← 返回主界面", use_container_width=True):
        st.switch_page("app.py")

st.title("🗺️ 学程")
st.caption("学习旅程总览")
st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    st.markdown(f"""
    <div style="font-size:28px; font-weight:bold; color:{color}; text-shadow:0 2px 16px {color}33, 0 4px 32px {color}15;">
        {icon} {rank} {symbol}
    </div>
    <div style="font-size:18px; color:{color}; margin-top:4px; text-shadow:0 2px 12px {color}20;">
        {points} 分
    </div>
    """, unsafe_allow_html=True)
    rank_index = rank_order.index(rank) if rank in rank_order else 0
    base_points = rank_index * 500
    sub_start = base_points + (sub_rank - 1) * 100
    sub_end = base_points + sub_rank * 100
    progress = max(0, min((points - sub_start) / 100, 1))
    bar_color = get_color_by_progress(progress * 100)
    st.markdown(progress_bar_html(progress * 100, bar_color, show_label=False), unsafe_allow_html=True)
    st.caption(f"距离下一小段还需 {sub_end - points} 分")

with col2:
    st.markdown(f"### ⭐ Lv.{level}")
    st.markdown(f"**权重积分: {weight_points}**")
    next_needed = level
    next_total = total_needed + next_needed
    level_progress = max(0, min((weight_points - total_needed) / next_needed, 1))
    level_color = get_color_by_progress(level_progress * 100)
    st.markdown(progress_bar_html(level_progress * 100, level_color, show_label=False), unsafe_allow_html=True)
    st.caption(f"距离 Lv.{level + 1} 还需 {next_total - weight_points} 分")

st.markdown("---")

st.markdown("### 🌱 今日施肥")
st.caption("每日任务 · 完成获得收获")

if not daily_tasks:
    st.info("暂无每日任务")
else:
    col1, col2, col3, col4, col5 = st.columns([1.2, 2.8, 1, 1, 2])
    with col1: st.markdown("**状态**")
    with col2: st.markdown("**肥料**")
    with col3: st.markdown("**收获**")
    with col4: st.markdown("**价值**")
    with col5: st.markdown("**进度**")
    st.markdown("---")

    # 换一批按钮（存 session_state 控制）
    if "daily_refresh_used" not in st.session_state:
        st.session_state.daily_refresh_used = False

    col_refresh, _ = st.columns([1, 5])
    with col_refresh:
        if st.session_state.daily_refresh_used:
            st.button("🔄 已使用", use_container_width=True, disabled=True)
        else:
            if st.button("🔄 换一批", use_container_width=True):
                st.session_state.daily_refresh_used = True
                st.rerun()

    # 随机显示5个任务（从接口取，但接口可能返回很多，取前5个或随机5个）
    display_daily = daily_tasks[:5]
    if len(daily_tasks) > 5:
        # 如果接口返回很多，随机取5个
        import random
        display_daily = random.sample(daily_tasks, 5)

    for i, task in enumerate(display_daily):
        col1, col2, col3, col4, col5 = st.columns([1.2, 2.8, 1, 1, 2])
        progress = task.get("progress", 0)
        bar_color = get_color_by_progress(progress)
        stars = get_stars(task.get("value", 1))
        star_color = get_star_color(task.get("value", 1))
        done = task.get("done", False)

        with col1:
            if done:
                st.button("✅", key=f"career_daily_done_{i}", disabled=True)
            elif progress >= 100:
                if st.button("🎁", key=f"career_daily_claim_{i}"):
                    # 领取奖励
                    try:
                        resp = requests.post(
                            f"{BACKEND_URL}/career/stats/update",
                            json={"user_id": user_id, "points_change": task.get("reward", 0)},
                            headers={"Authorization": f"Bearer {access_token}"},
                            timeout=10
                        )
                        if resp.status_code == 200:
                            st.toast(f"✅ 获得 {task.get('reward', 0)} 分！", icon="🎉")
                            st.rerun()
                        else:
                            st.error("领取失败")
                    except:
                        st.error("网络错误")
            else:
                st.button("⏳", key=f"career_daily_incomplete_{i}", disabled=True)
        with col2:
            st.markdown(f"{task.get('name', '')}")
        with col3:
            st.markdown(f"+{task.get('reward', 0)}")
        with col4:
            st.markdown(f'<span style="color:{star_color}; text-shadow:0 0 12px {star_color}33;">{stars}</span>', unsafe_allow_html=True)
        with col5:
            st.markdown(progress_bar_html(progress, bar_color), unsafe_allow_html=True)

    st.markdown("---")

    # 全部完成奖励
    col1, col2, col3, col4, col5 = st.columns([1.2, 2.8, 1, 1, 2])
    with col1:
        all_done = all(t.get("done", False) for t in display_daily)
        if "daily_all_done" not in st.session_state:
            st.session_state.daily_all_done = False
        if all_done and st.session_state.daily_all_done:
            st.button("✅", key="career_all_done", disabled=True)
        elif all_done and not st.session_state.daily_all_done:
            if st.button("🎁", key="career_all_claim"):
                try:
                    resp = requests.post(
                        f"{BACKEND_URL}/career/stats/update",
                        json={"user_id": user_id, "points_change": 50},
                        headers={"Authorization": f"Bearer {access_token}"},
                        timeout=10
                    )
                    if resp.status_code == 200:
                        st.session_state.daily_all_done = True
                        st.toast("✅ 获得 50 分！", icon="🎉")
                        st.rerun()
                    else:
                        st.error("领取失败")
                except:
                    st.error("网络错误")
        else:
            st.button("⏳", key="career_all_incomplete", disabled=True)
    with col2:
        st.markdown("🎯 完成全部每日任务")
    with col3:
        st.markdown("+50")
    with col4:
        st.markdown(f'<span style="color:{get_star_color(5)}; text-shadow:0 0 12px {get_star_color(5)}33;">★★★★★</span>', unsafe_allow_html=True)
    with col5:
        done_count = sum(1 for t in display_daily if t.get("done", False))
        total = len(display_daily)
        pct = int(done_count / total * 100) if total > 0 else 0
        bar_color = get_color_by_progress(pct)
        st.markdown(progress_bar_html(pct, bar_color), unsafe_allow_html=True)

st.markdown("---")

st.markdown("### 🌱 播种")
st.caption("新手引导 · 第一次使用各项功能")

if not seed_tasks:
    st.info("暂无播种任务")
else:
    col1, col2, col3, col4, col5 = st.columns([1.2, 2.8, 1, 1, 2])
    with col1: st.markdown("**状态**")
    with col2: st.markdown("**种子**")
    with col3: st.markdown("**收获**")
    with col4: st.markdown("**价值**")
    with col5: st.markdown("**进度**")
    st.markdown("---")

    done_count_seed = len([t for t in seed_tasks if t.get("done", False)])
    st.caption(f"进度：{done_count_seed}/{len(seed_tasks)}")

    for i, task in enumerate(seed_tasks[:20]):  # 最多显示20个
        col1, col2, col3, col4, col5 = st.columns([1.2, 2.8, 1, 1, 2])
        progress = task.get("progress", 0)
        bar_color = get_color_by_progress(progress)
        stars = get_stars(task.get("value", 1))
        star_color = get_star_color(task.get("value", 1))
        done = task.get("done", False)

        with col1:
            if done:
                st.button("✅", key=f"seed_done_{i}", disabled=True)
            elif progress >= 100:
                if st.button("🎁", key=f"seed_claim_{i}"):
                    try:
                        resp = requests.post(
                            f"{BACKEND_URL}/career/stats/update",
                            json={"user_id": user_id, "points_change": task.get("reward", 0)},
                            headers={"Authorization": f"Bearer {access_token}"},
                            timeout=10
                        )
                        if resp.status_code == 200:
                            st.toast(f"✅ 获得 {task.get('reward', 0)} 分！", icon="🎉")
                            st.rerun()
                        else:
                            st.error("领取失败")
                    except:
                        st.error("网络错误")
            else:
                st.button("⏳", key=f"seed_incomplete_{i}", disabled=True)
        with col2:
            st.markdown(f"{task.get('name', '')}")
        with col3:
            st.markdown(f"+{task.get('reward', 0)}")
        with col4:
            st.markdown(f'<span style="color:{star_color}; text-shadow:0 0 12px {star_color}33;">{stars}</span>', unsafe_allow_html=True)
        with col5:
            st.markdown(progress_bar_html(progress, bar_color), unsafe_allow_html=True)

    st.markdown("---")

st.markdown("### 🌿 发芽")
st.caption("长期耕耘 · 持续积累 · 阶梯解锁")

if not long_tasks:
    st.info("暂无发芽任务")
else:
    col1, col2, col3, col4, col5 = st.columns([1.2, 1.8, 1, 1, 2])
    with col1: st.markdown("**状态**")
    with col2: st.markdown("**扎根**")
    with col3: st.markdown("**收获**")
    with col4: st.markdown("**价值**")
    with col5: st.markdown("**进度**")
    st.markdown("---")

    for i, task in enumerate(long_tasks[:20]):  # 最多显示20个
        col1, col2, col3, col4, col5 = st.columns([1.2, 1.8, 1, 1, 2])
        progress = task.get("progress", 0)
        bar_color = get_color_by_progress(progress)
        stars = get_stars(task.get("value", 1))
        star_color = get_star_color(task.get("value", 1))
        done = task.get("done", False)

        with col1:
            if done:
                st.button("✅", key=f"long_done_{i}", disabled=True)
            elif progress >= 100:
                if st.button("🎁", key=f"long_claim_{i}"):
                    try:
                        resp = requests.post(
                            f"{BACKEND_URL}/career/stats/update",
                            json={"user_id": user_id, "points_change": task.get("reward", 0)},
                            headers={"Authorization": f"Bearer {access_token}"},
                            timeout=10
                        )
                        if resp.status_code == 200:
                            st.toast(f"✅ 获得 {task.get('reward', 0)} 分！", icon="🎉")
                            st.rerun()
                        else:
                            st.error("领取失败")
                    except:
                        st.error("网络错误")
            else:
                st.button("⏳", key=f"long_incomplete_{i}", disabled=True)
        with col2:
            st.markdown(f"{task.get('name', '')}")
        with col3:
            st.markdown(f"+{task.get('reward', 0)}")
        with col4:
            st.markdown(f'<span style="color:{star_color}; text-shadow:0 0 12px {star_color}33;">{stars}</span>', unsafe_allow_html=True)
        with col5:
            st.markdown(progress_bar_html(progress, bar_color), unsafe_allow_html=True)

    st.markdown("---")

st.markdown("### 🎯 即将拾贝")
st.caption("最接近完成的成就")

if not achievements:
    st.info("暂无成就数据")
else:
    # 按是否完成排序，未完成的排前面
    sorted_achievements = sorted(achievements, key=lambda x: x.get("done", False))
    # 取前5个
    display_achievements = sorted_achievements[:5]

    for ach in display_achievements:
        done = ach.get("done", False)
        # 如果是已完成的，显示"✅ 已解锁"
        status_text = "✅ 已解锁" if done else "⏳ 未解锁"
        pct = 100 if done else 0
        bar_color = get_color_by_progress(pct)
        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:8px; margin-bottom:6px;">
            <span style="font-size:13px; width:100px; color:var(--text-color); text-shadow:0 1px 4px rgba(0,0,0,0.04);">{ach.get('name', '')}</span>
            <span style="font-size:11px; width:60px; color:{'#4CAF50' if done else '#888'}; text-shadow:0 1px 4px rgba(0,0,0,0.04);">{status_text}</span>
            <div style="flex:1;">
                <div class="track" style="height:6px;">
                    <div class="track-fill" style="width:{pct}%; background:{bar_color};"></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)