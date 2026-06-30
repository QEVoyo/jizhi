import streamlit as st
import requests
import base64
import os

BACKEND_URL = "https://ingenious-rejoicing-production-90b7.up.railway.app"

st.set_page_config(
    page_title="拾贝",
    page_icon="🐚",
    layout="wide",
    initial_sidebar_state="auto"
)

# ====== 背景图 ======
def get_base64_image(img_path):
    with open(img_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

img_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "career_achievements_bg.jpg")
img_base64 = get_base64_image(img_path)

st.markdown(f"""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
<style>
    .stApp {{
        background: var(--background-color);
        background-image: 
            linear-gradient(rgba(255,255,255,0.5), rgba(255,255,255,0.5)),
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

    .ach-card {{
        background: transparent;
        border-radius: 12px;
        padding: 16px 12px;
        text-align: center;
        margin-bottom: 12px;
        cursor: pointer;
        transition: all 0.3s ease;
        border: 1px solid var(--border-color);
        box-shadow: 0 2px 10px rgba(0,0,0,0.04);
    }}
    .ach-card:hover {{
        transform: translateY(-3px);
        border-color: rgba(128,128,128,0.2);
        box-shadow: 0 8px 28px rgba(0,0,0,0.08);
    }}
    .ach-card-unlocked {{ opacity: 1; }}
    .ach-card-locked {{ opacity: 0.5; }}

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
    colors = {1: "#8B8B8B", 2: "#A8D5BA", 3: "#4CAF50", 4: "#26A69A",
              5: "#42A5F5", 6: "#7E57C2", 7: "#FF9800", 8: "#FF6F00",
              9: "#F44336", 10: "#FFD700"}
    return colors.get(value, "#888")


def get_stars(value):
    return "★" * value


def progress_bar_html(progress, bar_color):
    pct = min(max(progress, 0), 100)
    return '<div style="display:flex; align-items:center; gap:8px;"><div style="flex:1; background:rgba(128,128,128,0.15); border-radius:4px; height:6px; overflow:hidden;"><div style="width:' + str(pct) + '%; height:100%; background:' + bar_color + '; border-radius:4px;"></div></div><span style="font-size:11px; color:#888;">' + str(pct) + '%</span></div>'


def claim_reward(user_id, access_token, reward_points):
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
        return response.status_code == 200
    except:
        return False


# ====== 获取成就数据 ======
try:
    response = requests.get(
        f"{BACKEND_URL}/career/task-progress/{user_id}",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10
    )
    if response.status_code == 200:
        task_data = response.json()
        achievements_data = task_data.get("achievements", [])
    else:
        achievements_data = []
except:
    achievements_data = []

# ====== 返回按钮 ======
if st.button("← 返回学程"):
    st.switch_page("pages/career.py")

st.title("🐚 拾贝")
st.caption("学海拾贝，采撷成果")
st.markdown("---")

# 成就颜色
achievement_colors = [
    "#FF6B6B", "#FF8E53", "#FFB74D", "#FFD93D", "#A8E06C",
    "#6BCB77", "#4ECDC4", "#45B7D1", "#4A9FF5", "#7C6DF0",
    "#9B59B6", "#E040FB", "#EC407A", "#F06292", "#FF8A80",
    "#FF6F00", "#F9A825", "#AFB42B", "#388E3C", "#00695C",
    "#00838F", "#0D47A1", "#4A148C", "#880E4F", "#BF360C",
    "#1A237E",
]

for i, ach in enumerate(achievements_data):
    ach["theme_color"] = achievement_colors[i % len(achievement_colors)]

done_count = len([a for a in achievements_data if a.get("done", False)])
total = len(achievements_data)

st.markdown(f"**已拾取：{done_count} / {total}**")
pct_total = (done_count / total) * 100 if total > 0 else 0
total_bar_color = get_color_by_progress(pct_total)
st.markdown(progress_bar_html(pct_total, total_bar_color), unsafe_allow_html=True)

st.markdown("---")


@st.dialog("🏆 成就详情", width="small")
def show_detail_dialog(ach):
    star_color = get_star_color(ach.get("value", 1))
    stars = get_stars(ach.get("value", 1))
    is_done = ach.get("done", False)
    theme_color = ach.get("theme_color", "#888")
    display_color = theme_color
    status_text = "✅ 已拾取" if is_done else "🔒 未拾取"
    status_color = "#4CAF50" if is_done else "#888"
    unlock_time = ach.get("unlock_time", None)
    time_text = unlock_time if unlock_time else "尚未解锁"
    progress = 100 if is_done else 0
    bar_color = get_color_by_progress(progress)

    icon_map = {
        "first_checkin": "fa-book-open",
        "checkin_7": "fa-fire",
        "checkin_30": "fa-calendar-check",
        "first_chat": "fa-comment",
        "first_plan": "fa-sitemap",
        "first_generate": "fa-pen-fancy",
        "first_evaluate": "fa-search",
        "questions_100": "fa-scroll",
        "questions_1000": "fa-crown",
        "mistakes_10": "fa-bullseye",
        "mistakes_100": "fa-shield-halved",
        "sets_5": "fa-folder-open",
        "sets_20": "fa-layer-group",
        "rank_mingli": "fa-graduation-cap",
        "rank_zhizhi": "fa-brain",
        "rank_duxing": "fa-rocket",
        "rank_zhenjing": "fa-star",
        "legend": "fa-crown",
        "share_10": "fa-share-alt",
        "study_7": "fa-sun",
        "timer_10h": "fa-clock",
        "logs_50": "fa-book",
        "report_10": "fa-chart-line",
        "sets_50": "fa-building",
        "messages_500": "fa-comments",
    }
    icon = icon_map.get(ach.get("id", ""), "fa-trophy")

    st.markdown(f"""
    <div style="text-align:center; padding:4px 0;">
        <div style="font-size:48px; color:{display_color}; text-shadow:0 2px 16px {display_color}33, 0 4px 32px {display_color}15;">
            <i class="fas {icon}"></i>
        </div>
        <div style="font-size:22px; font-weight:bold; color:{display_color}; margin-top:6px; text-shadow:0 2px 16px {display_color}33, 0 4px 32px {display_color}15;">
            {ach.get('name', '')}
        </div>
        <div style="font-size:13px; color:{display_color}; margin-top:2px; text-shadow:0 2px 12px {display_color}20;">
            {ach.get('condition', '')}
        </div>
        <div style="display:flex; justify-content:center; gap:28px; margin-top:14px;">
            <div>
                <div style="font-size:11px; color:#888;">收获</div>
                <div style="font-size:18px; font-weight:bold; color:{display_color}; text-shadow:0 2px 12px {display_color}20;">+{ach.get('reward', 0)}</div>
            </div>
            <div>
                <div style="font-size:11px; color:#888;">价值</div>
                <div style="font-size:18px; font-weight:bold; color:{star_color}; text-shadow:0 0 12px {star_color}33;">{stars}</div>
            </div>
            <div>
                <div style="font-size:11px; color:#888;">状态</div>
                <div style="font-size:14px; font-weight:bold; color:{status_color};">{status_text}</div>
            </div>
        </div>
        <div style="margin-top:14px;">
            {progress_bar_html(progress, bar_color)}
        </div>
        <div style="margin-top:12px; font-size:12px; color:{'#4CAF50' if is_done else '#888'};">
            {'🎉 ' + time_text if is_done else '⏳ ' + time_text}
        </div>
    </div>
    """, unsafe_allow_html=True)


# ====== 成就网格 ======
cols = st.columns(4)

for i, ach in enumerate(achievements_data):
    with cols[i % 4]:
        star_color = get_star_color(ach.get("value", 1))
        stars = get_stars(ach.get("value", 1))
        is_done = ach.get("done", False)
        theme_color = ach.get("theme_color", "#888")
        display_color = theme_color if is_done else "#555"
        border_color = theme_color if is_done else "#333"
        status_text = "✅ 已拾取" if is_done else "🔒 未拾取"
        progress = 100 if is_done else 0
        bar_color = get_color_by_progress(progress)

        icon_map = {
            "first_checkin": "fa-book-open",
            "checkin_7": "fa-fire",
            "checkin_30": "fa-calendar-check",
            "first_chat": "fa-comment",
            "first_plan": "fa-sitemap",
            "first_generate": "fa-pen-fancy",
            "first_evaluate": "fa-search",
            "questions_100": "fa-scroll",
            "questions_1000": "fa-crown",
            "mistakes_10": "fa-bullseye",
            "mistakes_100": "fa-shield-halved",
            "sets_5": "fa-folder-open",
            "sets_20": "fa-layer-group",
            "rank_mingli": "fa-graduation-cap",
            "rank_zhizhi": "fa-brain",
            "rank_duxing": "fa-rocket",
            "rank_zhenjing": "fa-star",
            "legend": "fa-crown",
            "share_10": "fa-share-alt",
            "study_7": "fa-sun",
            "timer_10h": "fa-clock",
            "logs_50": "fa-book",
            "report_10": "fa-chart-line",
            "sets_50": "fa-building",
            "messages_500": "fa-comments",
        }
        icon = icon_map.get(ach.get("id", ""), "fa-trophy")

        # 卡片
        st.markdown(f"""
        <div class="ach-card {'ach-card-unlocked' if is_done else 'ach-card-locked'}" style="border-color:{border_color};">
            <div style="font-size:32px; color:{display_color}; text-shadow:0 2px 16px {display_color}33, 0 4px 32px {display_color}15;">
                <i class="fas {icon}"></i>
            </div>
            <div style="font-size:14px; font-weight:bold; color:{display_color}; margin-top:4px; text-shadow:0 2px 12px {display_color}20;">
                {ach.get('name', '')}
            </div>
            <div style="font-size:11px; color:{display_color}; margin:2px 0; text-shadow:0 2px 12px {display_color}15;">
                {ach.get('condition', '')}
            </div>
            <div style="font-size:12px; color:{display_color}; text-shadow:0 2px 12px {display_color}15;">+{ach.get('reward', 0)} 收获</div>
            <div style="font-size:13px; color:{star_color}; text-shadow:0 0 12px {star_color}33;">{stars}</div>
            <div style="font-size:11px; color:{display_color}; margin-top:2px; text-shadow:0 2px 12px {display_color}15;">{status_text}</div>
            <div style="margin-top:8px;">
                {progress_bar_html(progress, bar_color)}
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("查看详情", key=f"ach_btn_{i}_{ach.get('id', i)}", use_container_width=True):
            show_detail_dialog(ach)