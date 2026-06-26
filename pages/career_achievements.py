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
.ach-card {
    background: #1a1a2a;
    border-radius: 12px;
    padding: 16px 12px;
    text-align: center;
    margin-bottom: 12px;
    cursor: pointer;
    transition: all 0.3s ease;
    border: 2px solid #333;
}
.ach-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 30px rgba(0,0,0,0.4);
}
.ach-card-unlocked { opacity: 1; }
.ach-card-locked { opacity: 0.5; }
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
    colors = {
        1: "#8B8B8B", 2: "#A8D5BA", 3: "#4CAF50", 4: "#26A69A",
        5: "#42A5F5", 6: "#7E57C2", 7: "#FF9800", 8: "#FF6F00",
        9: "#F44336", 10: "#FFD700"
    }
    return colors.get(value, "#888")


def get_stars(value):
    return "★" * value


if st.button("← 返回学程"):
    st.switch_page("pages/career.py")

st.title("🐚 拾贝")
st.caption("学海拾贝，采撷成果")
st.markdown("---")

try:
    response = requests.get(
        f"{BACKEND_URL}/career/stats/{user_id}",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10
    )
    stats = response.json() if response.status_code == 200 else {}
except:
    stats = {}

user_achievements = stats.get("achievements", [])

# 成就解锁时间映射
achievement_times = stats.get("achievement_times", {})

# 26种主题色
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
progress_pct = (done_count / total) * 100
st.markdown(f"""
<div style="display:flex; align-items:center; gap:12px; margin-bottom:16px;">
    <span style="font-size:13px; color:#888;">进度</span>
    <div style="flex:1; height:8px; background:#2a2a3a; border-radius:4px; overflow:hidden;">
        <div style="width:{progress_pct}%; height:100%; background:#42A5F5; border-radius:4px;"></div>
    </div>
    <span style="font-size:13px; font-weight:bold; color:#42A5F5;">{done_count}/{total}</span>
</div>
""", unsafe_allow_html=True)

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

    # 解锁时间
    unlock_time = ach.get("unlock_time", None)
    time_text = unlock_time if unlock_time else "尚未解锁"

    st.markdown(f"""
    <div style="text-align:center;">
        <div style="font-size:48px; color:{display_color};">
            <i class="fas {ach['icon']}"></i>
        </div>
        <div style="font-size:22px; font-weight:bold; color:{display_color}; margin-top:6px;">
            {ach['name']}
        </div>
        <div style="font-size:13px; color:{display_color}; margin-top:2px;">
            {ach['condition']}
        </div>
        <div style="display:flex; justify-content:center; gap:28px; margin-top:14px;">
            <div>
                <div style="font-size:11px; color:#888;">收获</div>
                <div style="font-size:18px; font-weight:bold; color:{display_color};">+{ach['reward']}</div>
            </div>
            <div>
                <div style="font-size:11px; color:#888;">价值</div>
                <div style="font-size:18px; font-weight:bold; color:{star_color};">{stars}</div>
            </div>
            <div>
                <div style="font-size:11px; color:#888;">状态</div>
                <div style="font-size:14px; font-weight:bold; color:{status_color};">{status_text}</div>
            </div>
        </div>
        <div style="margin-top:12px;">
            <div style="font-size:11px; color:#888; margin-bottom:4px;">进度</div>
            <div style="width:100%; height:8px; background:#2a2a3a; border-radius:4px; overflow:hidden;">
                <div style="width:{ach['progress']}%; height:100%; background:{get_color_by_progress(ach['progress'])}; border-radius:4px;"></div>
            </div>
            <div style="font-size:12px; color:#888; margin-top:4px;">{ach['progress']}%</div>
        </div>
        <div style="margin-top:12px; font-size:12px; color:{'#4CAF50' if is_done else '#666'};">
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

        card_html = f"""
        <div class="ach-card {'ach-card-unlocked' if is_done else 'ach-card-locked'}" style="border-color:{border_color};">
            <div style="font-size:32px; color:{display_color};"><i class="fas {ach['icon']}"></i></div>
            <div style="font-size:14px; font-weight:bold; color:{display_color}; margin-top:4px;">{ach['name']}</div>
            <div style="font-size:11px; color:{display_color}; margin:2px 0;">{ach['condition']}</div>
            <div style="font-size:12px; color:{display_color};">+{ach['reward']} 收获</div>
            <div style="font-size:13px; color:{star_color};">{stars}</div>
            <div style="font-size:11px; color:{display_color}; margin-top:2px;">{status_text}</div>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)

        if st.button("查看详情", key=f"ach_btn_{i}_{ach['id']}", use_container_width=True):
            show_detail_dialog(ach)