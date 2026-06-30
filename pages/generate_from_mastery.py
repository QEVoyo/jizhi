import streamlit as st
import requests
import time
import base64
import os

BACKEND_URL = "https://ingenious-rejoicing-production-90b7.up.railway.app"

st.set_page_config(
    page_title="生成题目",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ====== 背景图 ======
def get_base64_image(img_path):
    with open(img_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

img_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "generate_from_mastery_bg.jpg")
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
    .stButton button, .stAlert, .stInfo, .stWarning, .stSuccess,
    .stTextInput label, .stSelectbox label, .stNumberInput label,
    .stTextInput input, .stSelectbox select, .stNumberInput input,
    .stTextArea label, .stTextArea textarea {{
        text-shadow: 0 1px 4px rgba(0,0,0,0.06), 0 2px 8px rgba(0,0,0,0.03);
    }}

    .stButton button {{
        background: rgba(128,128,128,0.06) !important;
        border: none !important;
        border-radius: 12px !important;
        color: var(--text-color) !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04), inset 0 1px 0 rgba(255,255,255,0.06) !important;
        transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
        font-weight: 500 !important;
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
    }}
    .stButton button:hover {{
        background: rgba(128,128,128,0.10) !important;
        box-shadow: 0 6px 24px rgba(0,0,0,0.10), inset 0 1px 0 rgba(255,255,255,0.08) !important;
        transform: translateY(-3px) !important;
    }}
    .stButton button:active {{
        transform: translateY(0px) !important;
    }}

    .stTextInput input, .stSelectbox select, .stNumberInput input,
    .stTextArea textarea {{
        background: rgba(128,128,128,0.05) !important;
        border: none !important;
        border-radius: 12px !important;
        color: var(--text-color) !important;
        box-shadow: inset 0 2px 8px rgba(0,0,0,0.06), 0 1px 0 rgba(255,255,255,0.04) !important;
        transition: all 0.3s ease !important;
        backdrop-filter: blur(4px);
        -webkit-backdrop-filter: blur(4px);
    }}
    .stTextInput input:focus, .stSelectbox select:focus,
    .stNumberInput input:focus, .stTextArea textarea:focus {{
        background: rgba(128,128,128,0.08) !important;
        box-shadow: inset 0 2px 12px rgba(0,0,0,0.10), 0 0 30px rgba(128,128,128,0.04) !important;
    }}

    .stAlert {{
        background: rgba(128,128,128,0.05) !important;
        border: none !important;
        border-radius: 12px !important;
        box-shadow: 0 2px 12px rgba(0,0,0,0.04) !important;
        text-shadow: 0 1px 4px rgba(0,0,0,0.06), 0 2px 8px rgba(0,0,0,0.03) !important;
        backdrop-filter: blur(4px);
        -webkit-backdrop-filter: blur(4px);
    }}

    hr {{ border: none !important; height: 1px !important; background: rgba(128,128,128,0.10) !important; margin: 12px 0 !important; }}
</style>
""", unsafe_allow_html=True)

# 登录检查
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("请先登录")
    st.stop()

user_id = st.session_state.user_id
access_token = st.session_state.access_token

practice_topic = st.session_state.get("practice_topic", "")
if not practice_topic:
    st.warning("未指定知识点方向")
    st.stop()

st.title("📝 生成题目")

with st.form("generate_from_mastery"):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**方向：**")
        st.markdown(f"**{practice_topic}** 🔒")
        sub_topic = st.text_input("细化知识点（可选）", placeholder=f"例：在「{practice_topic}」下细分...")
    with col2:
        question_type = st.selectbox("题型", [
            "选择题", "填空题", "判断题", "简答题", "计算题", "论述题", "编程题"
        ])
        difficulty = st.selectbox("难度", ["简单", "中等", "困难"])

    extra = st.text_area("补充说明（可选）", placeholder="例：需要包含实际代码示例...", height=60)
    submitted = st.form_submit_button("✨ 生成题目", use_container_width=True)

    if submitted:
        final_topic = practice_topic + (f" - {sub_topic}" if sub_topic else "")

        with st.spinner("AI 正在生成题目..."):
            try:
                response = requests.post(
                    f"{BACKEND_URL}/questions/generate",
                    json={
                        "user_id": user_id,
                        "category": practice_topic,
                        "topic": final_topic,
                        "question_type": question_type,
                        "difficulty": difficulty,
                        "extra": extra
                    },
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=60
                )

                if response.status_code == 200:
                    question_data = response.json()

                    try:
                        requests.post(
                            f"{BACKEND_URL}/questions/history/save",
                            json={
                                "user_id": user_id,
                                "question_id": question_data.get("id"),
                                "title": question_data.get("title"),
                                "question_type": question_data.get("type"),
                                "category": question_data.get("category"),
                                "topic": question_data.get("topic")
                            },
                            headers={"Authorization": f"Bearer {access_token}"},
                            timeout=10
                        )
                    except:
                        pass

                    st.session_state.practice_mode = None
                    st.session_state.practice_topic = None
                    st.session_state.current_question = question_data
                    st.success("✅ 题目生成成功！")
                    time.sleep(0.5)
                    st.switch_page("pages/do_question.py")
                else:
                    st.error(f"生成失败：{response.json().get('detail', '未知错误')}")
            except Exception as e:
                st.error(f"错误：{str(e)}")

if st.button("← 返回掌握度看板", use_container_width=True):
    st.session_state.practice_mode = None
    st.session_state.practice_topic = None
    st.switch_page("pages/mastery_board.py")