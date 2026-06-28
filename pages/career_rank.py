import streamlit as st
import requests

BACKEND_URL = "https://ingenious-rejoicing-production-90b7.up.railway.app"

st.set_page_config(
    page_title="登攀",
    page_icon="⛰️",
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

    .glass-card {
        background: transparent;
        border-radius: 16px;
        padding: 24px 28px;
        border: 1px solid var(--border-color);
        box-shadow: 0 2px 12px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    }
    .glass-card:hover {
        border-color: rgba(128,128,128,0.15);
        box-shadow: 0 6px 24px rgba(0,0,0,0.08);
        transform: translateY(-1px);
    }

    .glass-small {
        background: transparent;
        border-radius: 12px;
        padding: 14px 10px;
        text-align: center;
        border: 1px solid var(--border-color);
        box-shadow: 0 2px 10px rgba(0,0,0,0.04);
        transition: all 0.3s ease;
    }
    .glass-small:hover {
        transform: translateY(-3px);
        border-color: rgba(128,128,128,0.15);
        box-shadow: 0 8px 28px rgba(0,0,0,0.08);
    }

    .glass-table {
        width: 100%;
        border-collapse: collapse;
        background: transparent !important;
    }
    .glass-table td, .glass-table th {
        padding: 6px 8px;
        border-bottom: 1px solid var(--border-color);
        background: transparent !important;
    }
    .glass-table tr:hover td {
        background: rgba(128,128,128,0.02) !important;
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


col_back, col_title = st.columns([1, 5])
with col_back:
    if st.button("← 返回", use_container_width=True):
        st.switch_page("pages/career.py")
with col_title:
    st.markdown('<h1 style="font-weight:700; letter-spacing:1px;">⛰️ 登攀</h1>', unsafe_allow_html=True)
    st.caption("学如登山，步步高升")
st.markdown("---")

try:
    response = requests.get(f"{BACKEND_URL}/career/stats/{user_id}",
                            headers={"Authorization": f"Bearer {access_token}"}, timeout=10)
    stats = response.json() if response.status_code == 200 else {}
except:
    stats = {}

points = stats.get("points", 0)
rank = stats.get("rank", "启程")
sub_rank = stats.get("sub_rank", 1)
rank_history = stats.get("rank_history", [])
symbol = sub_symbols.get(sub_rank, "○")
icon = rank_icons.get(rank, "◈")
color = rank_colors.get(rank, "#FFFFFF")

rank_index = rank_order.index(rank) if rank in rank_order else 0
base_points = rank_index * 500
sub_start = base_points + (sub_rank - 1) * 100
sub_end = base_points + sub_rank * 100
progress = max(0, min((points - sub_start) / 100, 1))

pct = int(progress * 100)
bar_color = color

st.markdown(f"""
<div class="glass-card">
    <div style="display:flex; align-items:center; gap:20px; flex-wrap:wrap;">
        <div style="font-size:36px; font-weight:bold; color:{color}; text-shadow:0 2px 16px {color}33, 0 4px 32px {color}15, 0 8px 48px {color}08;">
            {icon} {rank} {symbol}
        </div>
        <div style="font-size:24px; color:{color}; padding:4px 18px; border-radius:10px; border:1px solid {color}22; text-shadow:0 2px 16px {color}25, 0 4px 32px {color}10;">
            {points} 分
        </div>
    </div>
    <div style="margin-top:14px;">
        <div style="display:flex; align-items:center; gap:8px;">
            <div style="flex:1; background:rgba(128,128,128,0.2); border-radius:4px; height:8px; box-shadow:inset 0 1px 4px rgba(0,0,0,0.08); overflow:hidden; border:1px solid rgba(128,128,128,0.08);">
                <div style="width:{pct}%; height:100%; background:{bar_color}; border-radius:4px; transition:width 0.6s ease; box-shadow:0 0 16px rgba(255,255,255,0.04);"></div>
            </div>
        </div>
        <div style="font-size:13px; color:var(--text-color-secondary); margin-top:8px; opacity:0.6;">距离下一小段还需 {sub_end - points} 分</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

if rank_history:
    st.markdown('<h3 style="font-weight:600; letter-spacing:0.5px;">📜 攀登足迹</h3>', unsafe_allow_html=True)
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
            <div class="glass-small">
                <div style="font-size:11px; color:var(--text-color-secondary); opacity:0.5;">{date_str}</div>
                <div style="font-size:16px; font-weight:bold; color:{r_color}; margin:4px 0; text-shadow:0 2px 14px {r_color}30, 0 4px 28px {r_color}12;">
                    {rank_name} {sym}
                </div>
                <div style="font-size:12px; color:var(--text-color-secondary); opacity:0.5;">{pts}分</div>
            </div>
            """, unsafe_allow_html=True)
    if len(rank_history) > 6:
        st.caption(f"...还有 {len(rank_history) - 6} 条记录")
else:
    st.info("📭 暂无攀登足迹，继续努力！")

st.markdown("---")

with st.expander("📖 段位说明", expanded=False):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 🎨 主题色")
        st.markdown(f"""
        <table class="glass-table">
        <tr><th style="color:var(--text-color-secondary);font-weight:400;">段位</th><th style="color:var(--text-color-secondary);font-weight:400;">符号</th><th style="color:var(--text-color-secondary);font-weight:400;">颜色</th></tr>
        <tr><td style="color:{rank_colors['启程']};font-weight:500;text-shadow:0 2px 12px {rank_colors['启程']}25;">启程</td><td style="color:{rank_colors['启程']};text-shadow:0 2px 12px {rank_colors['启程']}20;">◈</td><td><span style="display:inline-block;width:18px;height:18px;border-radius:5px;background:radial-gradient(circle at 30% 30%, {rank_colors['启程']}, {rank_colors['启程']}99);box-shadow:0 2px 12px {rank_colors['启程']}35;"></span></td></tr>
        <tr><td style="color:{rank_colors['求索']};font-weight:500;text-shadow:0 2px 12px {rank_colors['求索']}25;">求索</td><td style="color:{rank_colors['求索']};text-shadow:0 2px 12px {rank_colors['求索']}20;">❖</td><td><span style="display:inline-block;width:18px;height:18px;border-radius:5px;background:radial-gradient(circle at 30% 30%, {rank_colors['求索']}, {rank_colors['求索']}99);box-shadow:0 2px 12px {rank_colors['求索']}35;"></span></td></tr>
        <tr><td style="color:{rank_colors['明理']};font-weight:500;text-shadow:0 2px 12px {rank_colors['明理']}25;">明理</td><td style="color:{rank_colors['明理']};text-shadow:0 2px 12px {rank_colors['明理']}20;">✧</td><td><span style="display:inline-block;width:18px;height:18px;border-radius:5px;background:radial-gradient(circle at 30% 30%, {rank_colors['明理']}, {rank_colors['明理']}99);box-shadow:0 2px 12px {rank_colors['明理']}35;"></span></td></tr>
        <tr><td style="color:{rank_colors['致知']};font-weight:500;text-shadow:0 2px 12px {rank_colors['致知']}25;">致知</td><td style="color:{rank_colors['致知']};text-shadow:0 2px 12px {rank_colors['致知']}20;">✦</td><td><span style="display:inline-block;width:18px;height:18px;border-radius:5px;background:radial-gradient(circle at 30% 30%, {rank_colors['致知']}, {rank_colors['致知']}99);box-shadow:0 2px 12px {rank_colors['致知']}35;"></span></td></tr>
        <tr><td style="color:{rank_colors['笃行']};font-weight:500;text-shadow:0 2px 12px {rank_colors['笃行']}25;">笃行</td><td style="color:{rank_colors['笃行']};text-shadow:0 2px 12px {rank_colors['笃行']}20;">✹</td><td><span style="display:inline-block;width:18px;height:18px;border-radius:5px;background:radial-gradient(circle at 30% 30%, {rank_colors['笃行']}, {rank_colors['笃行']}99);box-shadow:0 2px 12px {rank_colors['笃行']}35;"></span></td></tr>
        <tr><td style="color:{rank_colors['臻境']};font-weight:500;text-shadow:0 2px 12px {rank_colors['臻境']}25;">臻境</td><td style="color:{rank_colors['臻境']};text-shadow:0 2px 12px {rank_colors['臻境']}20;">❋</td><td><span style="display:inline-block;width:18px;height:18px;border-radius:5px;background:radial-gradient(circle at 30% 30%, {rank_colors['臻境']}, {rank_colors['臻境']}99);box-shadow:0 2px 12px {rank_colors['臻境']}35;"></span></td></tr>
        <tr><td style="color:{rank_colors['传说']};font-weight:500;text-shadow:0 2px 12px {rank_colors['传说']}25;">传说</td><td style="color:{rank_colors['传说']};text-shadow:0 2px 12px {rank_colors['传说']}20;">★</td><td><span style="display:inline-block;width:18px;height:18px;border-radius:5px;background:radial-gradient(circle at 30% 30%, {rank_colors['传说']}, {rank_colors['传说']}99);box-shadow:0 2px 12px {rank_colors['传说']}35;"></span></td></tr>
        </table>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("### 🗺️ 山阶")
        st.markdown(f"""
        <table class="glass-table">
        <tr><th style="color:var(--text-color-secondary);font-weight:400;">段位</th><th style="color:var(--text-color-secondary);font-weight:400;">V</th><th style="color:var(--text-color-secondary);font-weight:400;">IV</th><th style="color:var(--text-color-secondary);font-weight:400;">III</th><th style="color:var(--text-color-secondary);font-weight:400;">II</th><th style="color:var(--text-color-secondary);font-weight:400;">I</th></tr>
        <tr><td style="color:{rank_colors['启程']};text-shadow:0 2px 12px {rank_colors['启程']}20;">启程</td><td style="color:{rank_colors['启程']};">○</td><td style="color:{rank_colors['启程']};">◌</td><td style="color:{rank_colors['启程']};">◎</td><td style="color:{rank_colors['启程']};">◍</td><td style="color:{rank_colors['启程']};">●</td></tr>
        <tr><td style="color:{rank_colors['求索']};text-shadow:0 2px 12px {rank_colors['求索']}20;">求索</td><td style="color:{rank_colors['求索']};">○</td><td style="color:{rank_colors['求索']};">◌</td><td style="color:{rank_colors['求索']};">◎</td><td style="color:{rank_colors['求索']};">◍</td><td style="color:{rank_colors['求索']};">●</td></tr>
        <tr><td style="color:{rank_colors['明理']};text-shadow:0 2px 12px {rank_colors['明理']}20;">明理</td><td style="color:{rank_colors['明理']};">○</td><td style="color:{rank_colors['明理']};">◌</td><td style="color:{rank_colors['明理']};">◎</td><td style="color:{rank_colors['明理']};">◍</td><td style="color:{rank_colors['明理']};">●</td></tr>
        <tr><td style="color:{rank_colors['致知']};text-shadow:0 2px 12px {rank_colors['致知']}20;">致知</td><td style="color:{rank_colors['致知']};">○</td><td style="color:{rank_colors['致知']};">◌</td><td style="color:{rank_colors['致知']};">◎</td><td style="color:{rank_colors['致知']};">◍</td><td style="color:{rank_colors['致知']};">●</td></tr>
        <tr><td style="color:{rank_colors['笃行']};text-shadow:0 2px 12px {rank_colors['笃行']}20;">笃行</td><td style="color:{rank_colors['笃行']};">○</td><td style="color:{rank_colors['笃行']};">◌</td><td style="color:{rank_colors['笃行']};">◎</td><td style="color:{rank_colors['笃行']};">◍</td><td style="color:{rank_colors['笃行']};">●</td></tr>
        <tr><td style="color:{rank_colors['臻境']};text-shadow:0 2px 12px {rank_colors['臻境']}20;">臻境</td><td style="color:{rank_colors['臻境']};">○</td><td style="color:{rank_colors['臻境']};">◌</td><td style="color:{rank_colors['臻境']};">◎</td><td style="color:{rank_colors['臻境']};">◍</td><td style="color:{rank_colors['臻境']};">●</td></tr>
        <tr><td style="color:{rank_colors['传说']};text-shadow:0 2px 12px {rank_colors['传说']}20;">传说</td><td>—</td><td>—</td><td>—</td><td>—</td><td style="color:{rank_colors['传说']};">★</td></tr>
        </table>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("### 🔍 小段位")
        st.markdown("""
        <table class="glass-table">
        <tr><th style="color:var(--text-color-secondary);font-weight:400;">符号</th><th style="color:var(--text-color-secondary);font-weight:400;">小段位</th><th style="color:var(--text-color-secondary);font-weight:400;">含义</th></tr>
        <tr><td style="color:var(--text-color-secondary);font-size:18px;opacity:0.4;">○</td><td>V</td><td style="color:var(--text-color-secondary);opacity:0.5;">空环（起步）</td></tr>
        <tr><td style="color:var(--text-color-secondary);font-size:18px;opacity:0.4;">◌</td><td>IV</td><td style="color:var(--text-color-secondary);opacity:0.5;">半环（成长）</td></tr>
        <tr><td style="color:var(--text-color-secondary);font-size:18px;opacity:0.4;">◎</td><td>III</td><td style="color:var(--text-color-secondary);opacity:0.5;">双环（进步）</td></tr>
        <tr><td style="color:var(--text-color-secondary);font-size:18px;opacity:0.4;">◍</td><td>II</td><td style="color:var(--text-color-secondary);opacity:0.5;">实半环（将成）</td></tr>
        <tr><td style="color:var(--text-color-secondary);font-size:18px;opacity:0.4;">●</td><td>I</td><td style="color:var(--text-color-secondary);opacity:0.5;">实心环（圆满）</td></tr>
        </table>
        """, unsafe_allow_html=True)