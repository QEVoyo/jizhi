import streamlit as st
import requests

BACKEND_URL = "https://ingenious-rejoicing-production-90b7.up.railway.app"

st.set_page_config(
    page_title="拾贝",
    page_icon="🐚",
    layout="wide",
    initial_sidebar_state="auto"
)

st.markdown("""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
<style>
    .stApp { background: var(--background-color); }
    .main .block-container { background: transparent; }

    /* ===== 所有文字凹凸立体感 ===== */
    h1, h2, h3, h4, h5, h6, p, span, div, label, .stMarkdown, .stCaption,
    .stButton button, .stAlert, .stInfo, .stWarning, .stSuccess {
        text-shadow: 0 2px 8px rgba(0,0,0,0.08), 0 4px 16px rgba(0,0,0,0.04);
    }

    /* ===== 所有按钮 ===== */
    .stButton button {
        background: transparent !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 10px !important;
        color: var(--text-color) !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.04) !important;
        transition: all 0.3s ease !important;
        text-shadow: 0 2px 8px rgba(0,0,0,0.08), 0 4px 16px rgba(0,0,0,0.04) !important;
        font-weight: 500 !important;
    }
    .stButton button:hover {
        background: rgba(128,128,128,0.04) !important;
        border-color: rgba(128,128,128,0.2) !important;
        box-shadow: 0 4px 16px rgba(0,0,0,0.08) !important;
        transform: translateY(-2px);
    }

    /* ===== 进度条 - 清晰可见 ===== */
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

    /* ===== 卡片凹凸立体 ===== */
    .ach-card {
        background: transparent;
        border-radius: 12px;
        padding: 16px 12px 40px 12px;
        text-align: center;
        border: 1px solid var(--border-color);
        box-shadow: 0 2px 10px rgba(0,0,0,0.04);
        transition: all 0.3s ease;
        position: relative;
    }
    .ach-card:hover {
        transform: translateY(-3px);
        border-color: rgba(128,128,128,0.2);
        box-shadow: 0 8px 28px rgba(0,0,0,0.08);
    }
    .ach-card-unlocked { opacity: 1; }
    .ach-card-locked { opacity: 0.5; }

    /* ===== 卡片内查看详情按钮 ===== */
    .card-wrapper {
        position: relative;
    }
    .card-wrapper .stButton button {
        position: absolute !important;
        bottom: 8px !important;
        left: 50% !important;
        transform: translateX(-50%) !important;
        width: auto !important;
        height: auto !important;
        min-height: 0 !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 4px 16px !important;
        margin: 0 !important;
        color: var(--text-color) !important;
        z-index: 10 !important;
        cursor: pointer !important;
        font-size: 12px !important;
        font-weight: 400 !important;
        opacity: 0.4 !important;
        text-shadow: 0 2px 8px rgba(0,0,0,0.08), 0 4px 16px rgba(0,0,0,0.04) !important;
        border: 1px solid rgba(128,128,128,0.1) !important;
        border-radius: 6px !important;
    }
    .card-wrapper .stButton button:hover {
        background: rgba(128,128,128,0.04) !important;
        border-color: rgba(128,128,128,0.2) !important;
        opacity: 0.8 !important;
        transform: translateX(-50%) translateY(-1px) !important;
        box-shadow: none !important;
    }

    hr { border-color: var(--border-color) !important; opacity: 0.3 !important; }

    .stAlert {
        background: transparent !important;
        border: 1px solid var(--border-color) !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.04) !important;
        text-shadow: 0 2px 8px rgba(0,0,0,0.08), 0 4px 16px rgba(0,0,0,0.04) !important;
    }
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
    colors = {1: "#8B8B8B", 2: "#A8D5BA", 3: "#4CAF50", 4: "#26A69A",
              5: "#42A5F5", 6: "#7E57C2", 7: "#FF9800", 8: "#FF6F00",
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

st.title("🐚 拾贝")
st.caption("学海拾贝，采撷成果")
st.markdown("---")

try:
    response = requests.get(f"{BACKEND_URL}/career/stats/{user_id}",
                            headers={"Authorization": f"Bearer {access_token}"}, timeout=10)
    stats = response.json() if response.status_code == 200 else {}
except:
    stats = {}

user_achievements = stats.get("achievements", [])
achievement_times = stats.get("achievement_times", {})

achievement_colors = [
    "#FF6B6B", "#FF8E53", "#FFB74D", "#FFD93D", "#A8E06C",
    "#6BCB77", "#4ECDC4", "#45B7D1", "#4A9FF5", "#7C6DF0",
    "#9B59B6", "#E040FB", "#EC407A", "#F06292", "#FF8A80",
    "#FF6F00", "#F9A825", "#AFB42B", "#388E3C", "#00695C",
    "#00838F", "#0D47A1", "#4A148C", "#880E4F", "#BF360C",
    "#1A237E",
]

all_achievements = [
    {"id": "first_checkin", "name": "初入书海", "icon": "fa-book-open", "condition": "完成第 1 次打卡", "reward": 20,
     "value": 5, "progress": 100},
    {"id": "checkin_7", "name": "持之以恒", "icon": "fa-fire", "condition": "连续打卡 7 天", "reward": 50, "value": 6,
     "progress": 85},
    {"id": "checkin_30", "name": "勤耕不辍", "icon": "fa-calendar-check", "condition": "累计打卡 30 天", "reward": 150,
     "value": 7, "progress": 45},
    {"id": "first_chat", "name": "初试锋芒", "icon": "fa-comment", "condition": "第 1 次使用对话", "reward": 15,
     "value": 4, "progress": 100},
    {"id": "first_plan", "name": "思维缜密", "icon": "fa-sitemap", "condition": "第 1 次使用规划 Agent", "reward": 20,
     "value": 5, "progress": 60},
    {"id": "first_generate", "name": "妙笔生花", "icon": "fa-pen-fancy", "condition": "第 1 次使用生成 Agent",
     "reward": 20, "value": 5, "progress": 30},
    {"id": "first_evaluate", "name": "明察秋毫", "icon": "fa-search", "condition": "第 1 次使用评估 Agent",
     "reward": 20, "value": 5, "progress": 0},
    {"id": "questions_100", "name": "百题斩", "icon": "fa-scroll", "condition": "累计做 100 道题", "reward": 100,
     "value": 6, "progress": 92},
    {"id": "questions_1000", "name": "千题斩", "icon": "fa-crown", "condition": "累计做 1000 道题", "reward": 300,
     "value": 9, "progress": 8},
    {"id": "mistakes_10", "name": "错题猎手", "icon": "fa-bullseye", "condition": "攻克 10 道错题", "reward": 80,
     "value": 6, "progress": 65},
    {"id": "mistakes_100", "name": "错题克星", "icon": "fa-shield-halved", "condition": "攻克 100 道错题",
     "reward": 200, "value": 9, "progress": 12},
    {"id": "sets_5", "name": "题集收藏家", "icon": "fa-folder-open", "condition": "创建 5 个题集", "reward": 50,
     "value": 6, "progress": 40},
    {"id": "sets_20", "name": "题集达人", "icon": "fa-layer-group", "condition": "创建 20 个题集", "reward": 150,
     "value": 7, "progress": 10},
    {"id": "rank_mingli", "name": "学有所成", "icon": "fa-graduation-cap", "condition": "晋升到「明理」段位",
     "reward": 100, "value": 7, "progress": 0},
    {"id": "rank_zhizhi", "name": "融会贯通", "icon": "fa-brain", "condition": "晋升到「致知」段位", "reward": 150,
     "value": 8, "progress": 0},
    {"id": "rank_duxing", "name": "独当一面", "icon": "fa-rocket", "condition": "晋升到「笃行」段位", "reward": 200,
     "value": 8, "progress": 0},
    {"id": "rank_zhenjing", "name": "臻于至善", "icon": "fa-star", "condition": "晋升到「臻境」段位", "reward": 300,
     "value": 9, "progress": 0},
    {"id": "legend", "name": "传说", "icon": "fa-crown", "condition": "晋升到「传说」称号", "reward": 500, "value": 10,
     "progress": 0},
    {"id": "share_10", "name": "分享达人", "icon": "fa-share-alt", "condition": "分享 10 道题", "reward": 80,
     "value": 6, "progress": 20},
    {"id": "study_7", "name": "学习狂人", "icon": "fa-sun", "condition": "连续学习 7 天", "reward": 100, "value": 7,
     "progress": 70},
    {"id": "timer_10h", "name": "时间管理", "icon": "fa-clock", "condition": "使用计时器累计 10 小时", "reward": 120,
     "value": 7, "progress": 35},
    {"id": "logs_50", "name": "知识沉淀", "icon": "fa-book", "condition": "记录 50 条学习日志", "reward": 100,
     "value": 6, "progress": 15},
    {"id": "report_10", "name": "学海无涯", "icon": "fa-chart-line", "condition": "查看学情报告 10 次", "reward": 80,
     "value": 6, "progress": 10},
    {"id": "share_receive_10", "name": "社交达人", "icon": "fa-user-friends", "condition": "接受好友分享 10 次",
     "reward": 100, "value": 6, "progress": 0},
    {"id": "sets_50", "name": "筑梦者", "icon": "fa-building", "condition": "创建 50 个题集", "reward": 300, "value": 8,
     "progress": 0},
    {"id": "messages_500", "name": "对话大师", "icon": "fa-comments", "condition": "累计发送 500 条消息", "reward": 150,
     "value": 7, "progress": 25},
]

for i, ach in enumerate(all_achievements):
    ach["theme_color"] = achievement_colors[i % len(achievement_colors)]

for ach in all_achievements:
    ach["done"] = ach["id"] in user_achievements
    ach["unlock_time"] = achievement_times.get(ach["id"], None)

done_count = len([a for a in all_achievements if a["done"]])
total = len(all_achievements)

st.markdown(f"**已拾取：{done_count} / {total}**")
pct_total = (done_count / total) * 100
total_bar_color = get_color_by_progress(pct_total)
st.markdown(progress_bar_html(pct_total, total_bar_color, show_label=True), unsafe_allow_html=True)

st.markdown("---")


@st.dialog("🏆 成就详情", width="small")
def show_detail_dialog(ach):
    star_color = get_star_color(ach["value"])
    stars = get_stars(ach["value"])
    is_done = ach.get("done", False)
    theme_color = ach["theme_color"]
    display_color = theme_color
    status_text = "✅ 已拾取" if is_done else "🔒 未拾取"
    status_color = "#4CAF50" if is_done else "#888"
    unlock_time = ach.get("unlock_time", None)
    time_text = unlock_time if unlock_time else "尚未解锁"
    pct = ach['progress']
    bar_color = get_color_by_progress(pct)

    st.markdown(f"""
    <div style="text-align:center; padding:4px 0;">
        <div style="font-size:48px; color:{display_color}; text-shadow:0 2px 16px {display_color}33, 0 4px 32px {display_color}15;">
            <i class="fas {ach['icon']}"></i>
        </div>
        <div style="font-size:22px; font-weight:bold; color:{display_color}; margin-top:6px; text-shadow:0 2px 16px {display_color}33, 0 4px 32px {display_color}15;">
            {ach['name']}
        </div>
        <div style="font-size:13px; color:{display_color}; margin-top:2px; text-shadow:0 2px 12px {display_color}20;">
            {ach['condition']}
        </div>
        <div style="display:flex; justify-content:center; gap:28px; margin-top:16px;">
            <div>
                <div style="font-size:11px; color:#888;">收获</div>
                <div style="font-size:18px; font-weight:bold; color:{display_color}; text-shadow:0 2px 12px {display_color}20;">+{ach['reward']}</div>
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
        <div style="margin-top:16px;">
            <div style="font-size:11px; color:#888; margin-bottom:4px;">进度</div>
            <div style="display:flex; align-items:center; gap:8px;">
                <div style="flex:1; background:rgba(128,128,128,0.2); border-radius:4px; height:8px; box-shadow:inset 0 1px 4px rgba(0,0,0,0.08); overflow:hidden; border:1px solid rgba(128,128,128,0.08);">
                    <div style="width:{pct}%; height:100%; background:{bar_color}; border-radius:4px; transition:width 0.6s ease; box-shadow:0 0 16px rgba(255,255,255,0.04);"></div>
                </div>
                <span style="font-size:11px; color:#888; min-width:36px; text-align:right;">{pct}%</span>
            </div>
        </div>
        <div style="margin-top:14px; font-size:12px; color:{'#4CAF50' if is_done else '#888'};">
            {'🎉 ' + time_text if is_done else '⏳ ' + time_text}
        </div>
    </div>
    """, unsafe_allow_html=True)


# ====== 成就网格 ======
cols = st.columns(4)

for i, ach in enumerate(all_achievements):
    with cols[i % 4]:
        star_color = get_star_color(ach["value"])
        stars = get_stars(ach["value"])
        is_done = ach.get("done", False)
        theme_color = ach["theme_color"]
        display_color = theme_color if is_done else "#555"
        border_color = theme_color if is_done else "#333"
        status_text = "✅ 已拾取" if is_done else "🔒 未拾取"
        card_class = "ach-card-unlocked" if is_done else "ach-card-locked"

        st.markdown(f"""
        <div class="card-wrapper">
            <div class="ach-card {card_class}" style="border-color:{border_color};">
                <div style="font-size:32px; color:{display_color}; text-shadow:0 2px 16px {display_color}33, 0 4px 32px {display_color}15;">
                    <i class="fas {ach['icon']}"></i>
                </div>
                <div style="font-size:14px; font-weight:bold; color:{display_color}; margin-top:4px; text-shadow:0 2px 12px {display_color}20;">
                    {ach['name']}
                </div>
                <div style="font-size:11px; color:{display_color}; margin:2px 0; text-shadow:0 2px 12px {display_color}15;">
                    {ach['condition']}
                </div>
                <div style="font-size:12px; color:{display_color}; text-shadow:0 2px 12px {display_color}15;">+{ach['reward']} 收获</div>
                <div style="font-size:13px; color:{star_color}; text-shadow:0 0 12px {star_color}33;">{stars}</div>
                <div style="font-size:11px; color:{display_color}; margin-top:2px; text-shadow:0 2px 12px {display_color}15;">{status_text}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("查看详情", key=f"ach_btn_{i}_{ach['id']}", use_container_width=True):
            show_detail_dialog(ach)