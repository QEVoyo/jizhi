import streamlit as st
import requests

BACKEND_URL = "https://ingenious-rejoicing-production-90b7.up.railway.app"

st.set_page_config(
    page_title="登攀",
    page_icon="⛰️",
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


# ====== 20种颜色渐变 ======
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


# ====== 返回学程 ======
col_back, col_title = st.columns([1, 5])
with col_back:
    if st.button("← 返回", use_container_width=True):
        st.switch_page("pages/career.py")
with col_title:
    st.title("⛰️ 登攀")
    st.caption("学如登山，步步高升")

st.markdown("---")

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
rank = stats.get("rank", "启程")
sub_rank = stats.get("sub_rank", 1)
is_legend = stats.get("is_legend", False)
rank_history = stats.get("rank_history", [])

symbol = sub_symbols.get(sub_rank, "○")
icon = rank_icons.get(rank, "◈")
color = rank_colors.get(rank, "#FFFFFF")

# ====== 当前段位 ======
st.markdown(f"""
<div style="color:{color}; font-size:32px; font-weight:bold;">
    {icon} {rank} {symbol}
</div>
<div style="color:{color}; font-size:22px; margin-top:4px;">
    {points} 分
</div>
""", unsafe_allow_html=True)

# 段位进度
rank_order = ["启程", "求索", "明理", "致知", "笃行", "臻境", "传说"]
rank_index = rank_order.index(rank) if rank in rank_order else 0
base_points = rank_index * 500
sub_start = base_points + (sub_rank - 1) * 100
sub_end = base_points + sub_rank * 100
progress = max(0, min((points - sub_start) / 100, 1))
bar_color = get_color_by_progress(progress * 100)

st.markdown(f"""
<div style="width:100%; height:8px; background:#2a2a3a; border-radius:4px; overflow:hidden; margin:12px 0 6px 0;">
    <div style="width:{progress * 100}%; height:100%; background:{bar_color}; border-radius:4px;"></div>
</div>
""", unsafe_allow_html=True)
st.caption(f"距离下一小段还需 {sub_end - points} 分")

st.markdown("---")

# ====== 段位日志 ======
if rank_history:
    st.markdown("### 📜 攀登足迹")
    cols = st.columns(min(len(rank_history[:6]), 6))
    for i, h in enumerate(rank_history[:6]):
        with cols[i]:
            date_str = h.get('date', '')[:10]
            rank_name = h.get('rank', '')
            sub = h.get('sub_rank', 1)
            pts = h.get('points', 0)
            sym = sub_symbols.get(sub, "○")
            r_color = rank_colors.get(rank_name, "#888")
            st.markdown(f"""
            <div style="background:#1e1e2e; border-radius:8px; padding:12px; text-align:center; border-left:3px solid {r_color};">
                <div style="font-size:12px; color:#888;">{date_str}</div>
                <div style="font-size:16px; font-weight:bold; color:{r_color};">{rank_name} {sym}</div>
                <div style="font-size:12px; color:#666;">{pts}分</div>
            </div>
            """, unsafe_allow_html=True)
    if len(rank_history) > 6:
        st.caption(f"...还有 {len(rank_history) - 6} 条记录")
else:
    st.info("📭 暂无攀登足迹，继续努力！")

st.markdown("---")

# ====== 段位说明 ======
with st.expander("📖 段位说明", expanded=False):
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 🎨 主题色")
        st.markdown("""
        | 段位 | 符号 | 颜色 |
        |------|------|------|
        | 启程 | ◈ | 🟤 |
        | 求索 | ❖ | 🔵 |
        | 明理 | ✧ | 🟢 |
        | 致知 | ✦ | 🟡 |
        | 笃行 | ✹ | 🟠 |
        | 臻境 | ❋ | 🟣 |
        | 传说 | ★ | 🔴 |
        """)

    with col2:
        st.markdown("### 🗺️ 山阶")
        st.markdown("""
        | 段位 | V | IV | III | II | I |
        |------|---|---|-----|----|---|
        | 启程 | ○ | ◌ | ◎ | ◍ | ● |
        | 求索 | ○ | ◌ | ◎ | ◍ | ● |
        | 明理 | ○ | ◌ | ◎ | ◍ | ● |
        | 致知 | ○ | ◌ | ◎ | ◍ | ● |
        | 笃行 | ○ | ◌ | ◎ | ◍ | ● |
        | 臻境 | ○ | ◌ | ◎ | ◍ | ● |
        | 传说 | — | — | — | — | ★ |
        """)

    with col3:
        st.markdown("### 🔍 小段位")
        st.markdown("""
        | 符号 | 小段位 | 含义 |
        |------|--------|------|
        | ○ | V | 空环（起步） |
        | ◌ | IV | 半环（成长） |
        | ◎ | III | 双环（进步） |
        | ◍ | II | 实半环（将成） |
        | ● | I | 实心环（圆满） |
        """)