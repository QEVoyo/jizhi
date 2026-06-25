import streamlit as st
import requests
import time

BACKEND_URL = "https://ingenious-rejoicing-production-90b7.up.railway.app"

st.set_page_config(
    page_title="生成题目",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="collapsed"
)

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
        sub_topic = st.text_input("细化知识点（可选）", placeholder=f"例：在「{practice_topic}」下细分...")  # 第二行
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

if st.button("← 返回掌握度看板"):
    st.session_state.practice_mode = None
    st.session_state.practice_topic = None
    st.switch_page("pages/mastery_board.py")