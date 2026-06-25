import streamlit as st
import requests
import json
import time

BACKEND_URL = "http://localhost:8000"

st.set_page_config(
    page_title="练习",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="collapsed"
)
# 强制刷新触发器
if "refresh_question" in st.session_state:
    st.session_state.pop("refresh_question")
# 登录检查
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("请先登录")
    st.stop()

question = st.session_state.get("current_question")
if not question:
    st.warning("没有找到题目")
    st.stop()

user_id = st.session_state.user_id
access_token = st.session_state.access_token

# ========== 状态管理 ==========
if "evaluated" not in st.session_state:
    st.session_state.evaluated = False
if "evaluation_result" not in st.session_state:
    st.session_state.evaluation_result = None


# ========== 工具函数 ==========
def get_color_by_difficulty(score):
    if score < 3:
        return "#00CC66"
    elif score < 5:
        return "#A8D500"
    elif score < 7:
        return "#FFC400"
    elif score < 9:
        return "#FF6E00"
    else:
        return "#FF0000"


def get_difficulty_label(score):
    """根据难度分数获取中文标签"""
    if score < 4:
        return "简单"
    elif score < 7:
        return "中等"
    else:
        return "困难"


# ========== 顶部：返回 + 标题 ==========
# ========== 顶部：返回 + 标题 ==========
col_back, col_title = st.columns([1, 8])
with col_back:
    if st.button("← 返回", use_container_width=True):
        st.session_state.evaluated = False
        st.session_state.evaluation_result = None
        if st.session_state.get("from_mistake_book", False):
            st.session_state.from_mistake_book = False
            st.switch_page("pages/resource_lib.py")
        elif st.session_state.get("from_set_detail", False):
            st.session_state.from_set_detail = False
            st.switch_page("pages/set_detail.py")
        elif st.session_state.get("from_mastery_board", False):
            st.session_state.from_mastery_board = False
            st.switch_page("pages/mastery_board.py")
        else:
            st.switch_page("pages/resource_lib.py")
with col_title:
    st.title("📝 练习")

# ========== 题目信息行 ==========
difficulty = question.get("difficulty_score", 5.0)
color = get_color_by_difficulty(difficulty)
difficulty_label = get_difficulty_label(difficulty)

col_d1, col_d2, col_d3, col_d4 = st.columns([1, 2, 2, 3])

with col_d1:
    st.markdown(f"""
    <div style="text-align:center;">
        <div style="width:50px; height:50px; border-radius:50%; 
            background:conic-gradient({color} {difficulty / 10 * 100}%, #2a2a3a {difficulty / 10 * 100}%);
            display:flex; align-items:center; justify-content:center; margin:0 auto;">
            <div style="background:#1e1e2e; width:38px; height:38px; border-radius:50%; 
                display:flex; align-items:center; justify-content:center; font-size:16px; font-weight:bold; color:white;">
                {difficulty:.1f}
            </div>
        </div>
        <div style="font-size:10px; color:#888; margin-top:2px;">{difficulty_label}</div>
    </div>
    """, unsafe_allow_html=True)

with col_d2:
    st.markdown(f"**分类：** {question.get('category', '未分类')}")
    st.markdown(f"**知识点：** {question.get('normalized_topic', question.get('topic', '未知'))}")  # 👈 改这里

with col_d3:
    type_display = {
        "choice": "选择题",
        "fill": "填空题",
        "judge": "判断题",
        "essay": "简答题/论述题",
        "calculation": "计算题",
        "coding": "编程题"
    }
    st.markdown(f"**题型：** {type_display.get(question.get('question_type', ''), '未知')}")

st.markdown("<hr style='margin:8px 0;'>", unsafe_allow_html=True)

# ========== 题目内容 ==========
st.markdown(f"**{question.get('title', '题目内容')}**")

# ========== 根据题型显示答题区 ==========
q_type = question.get("question_type", "choice")
user_answer = ""

if q_type == "choice":
    options = question.get("options", {})
    if options:
        selected = st.radio(
            "请选择答案",
            options=[f"{k}. {v}" for k, v in options.items()],
            index=None,
            key="choice_answer",
            label_visibility="collapsed"
        )
        user_answer = selected.split(". ")[0] if selected else ""
    else:
        st.warning("选择题没有选项")

elif q_type == "judge":
    selected = st.radio(
        "请判断",
        ["正确", "错误"],
        index=None,
        key="judge_answer",
        label_visibility="collapsed"
    )
    user_answer = selected

elif q_type == "fill":
    user_answer = st.text_input("请填写答案", key="fill_answer", label_visibility="collapsed",
                                placeholder="请输入答案...")

elif q_type == "essay":
    user_answer = st.text_area("请作答", height=80, key="essay_answer", label_visibility="collapsed",
                               placeholder="请输入你的回答...")

elif q_type == "coding":
    starter_code = question.get("starter_code", "# 请在这里编写代码")
    user_answer = st.text_area(
        "请编写代码",
        value=starter_code,
        height=120,
        key="coding_answer",
        label_visibility="collapsed",
        help="编写你的代码"
    )
elif q_type == "calculation":
    user_answer = st.text_area(
        "请写出计算过程和答案",
        height=120,
        key="calculation_answer",
        label_visibility="collapsed",
        placeholder="请写出你的计算步骤和最终答案..."
    )
else:
    user_answer = st.text_input("请输入答案", key="default_answer", label_visibility="collapsed",
                                placeholder="请输入答案...")

st.markdown("<hr style='margin:8px 0;'>", unsafe_allow_html=True)

# ========== 如果已经评估，显示结果 ==========
if st.session_state.evaluated and st.session_state.evaluation_result:
    result = st.session_state.evaluation_result

    if result.get("is_correct"):
        st.success("✅ 回答正确！")
    else:
        st.error("❌ 回答错误")

    mastery = result.get("mastery_score", 50)
    color = "#00CC66" if mastery >= 70 else "#FFC400" if mastery >= 50 else "#FF0000"
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:12px; margin:8px 0;">
        <span style="font-weight:bold;">掌握程度：</span>
        <div style="flex:1; height:8px; background:#2a2a3a; border-radius:4px; overflow:hidden;">
            <div style="width:{mastery}%; height:100%; background:{color}; border-radius:4px;"></div>
        </div>
        <span style="font-weight:bold; color:{color};">{mastery}%</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"**📝 评估：** {result.get('evaluation', '')}")
    st.markdown(f"**💡 建议：** {result.get('suggestion', '')}")


    if st.button("继续练习 →", use_container_width=True):
        st.session_state.evaluated = False
        st.session_state.evaluation_result = None
        st.rerun()

    st.markdown("<hr style='margin:8px 0;'>", unsafe_allow_html=True)

# ========== 按钮区域 ==========
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    if st.button("📝 提交", use_container_width=True):
        if not user_answer:
            st.warning("请先作答")
        else:
            with st.spinner("AI 正在评估..."):
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/questions/evaluate",
                        json={
                            "question": question,
                            "user_answer": user_answer,
                            "user_id": user_id  # 👈 加上这行
                        },
                        headers={"Authorization": f"Bearer {access_token}"},
                        timeout=30
                    )

                    if response.status_code == 200:
                        result = response.json()
                        st.session_state.evaluated = True
                        st.session_state.evaluation_result = result
                        st.rerun()  # 只刷新页面，显示评估结果，不跳转
                    else:
                        st.error(f"评估失败：{response.json().get('detail', '未知错误')}")
                except Exception as e:
                    st.error(f"错误：{str(e)}")

with col2:
    if st.button("🔄 重新生成", use_container_width=True):
        current_category = question.get("category", "")
        if not current_category:
            st.warning("该题目没有分类，请先保存或重新生成")
            st.stop()
        current_topic = question.get("topic", "")
        current_type = question.get("question_type", "choice")

        type_map = {
            "choice": "选择题",
            "fill": "填空题",
            "judge": "判断题",
            "essay": "简答题",
            "calculation": "计算题",
            "coding": "编程题"
        }
        current_type_display = type_map.get(current_type, "选择题")

        current_score = question.get("difficulty_score", 5.0)
        if current_score < 4:
            current_difficulty = "简单"
        elif current_score < 7:
            current_difficulty = "中等"
        else:
            current_difficulty = "困难"

        with st.spinner("正在生成新题..."):
            response = requests.post(
                f"{BACKEND_URL}/questions/generate",
                json={
                    "user_id": user_id,
                    "category": current_category,
                    "topic": current_topic,
                    "question_type": current_type_display,
                    "difficulty": current_difficulty,
                    "extra": ""
                },
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=60
            )

        if response.status_code == 200:
            new_question = response.json()

            # 👇 保存到生成历史
            try:
                requests.post(
                    f"{BACKEND_URL}/questions/history/save",
                    json={
                        "user_id": user_id,
                        "question_id": new_question.get("id"),
                        "title": new_question.get("title"),
                        "question_type": new_question.get("type"),
                        "category": new_question.get("category"),
                        "topic": new_question.get("topic")
                    },
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=10
                )
            except:
                pass

            st.session_state.evaluated = False
            st.session_state.evaluation_result = None
            st.session_state.current_question = new_question
            st.rerun()
        else:
            st.error("重新生成失败")

with col3:
    if st.button("📁 加入题集", use_container_width=True):
        st.session_state.show_add_to_set = True
        st.rerun()

with col4:
    if st.button("🔄 换题型", use_container_width=True):
        st.session_state.show_change_type = True
        st.rerun()


with col5:
    with st.popover("❓ 提示"):
        hint = question.get("hint", "暂无提示")
        st.markdown(f"💡 {hint}")

st.markdown("<hr style='margin:8px 0;'>", unsafe_allow_html=True)
# ========== 换题型弹窗 ==========
if st.session_state.get("show_change_type", False):
    with st.popover("🔄 换题型", use_container_width=True):
        st.markdown("### 选择换题方式")

        # 获取当前参数
        current_category = question.get("category", "")
        if not current_category:
            st.warning("该题目没有分类，请先保存或重新生成")
            st.stop()
        current_topic = question.get("topic", "")
        current_score = question.get("difficulty_score", 5.0)

        if current_score < 4:
            current_difficulty = "简单"
        elif current_score < 7:
            current_difficulty = "中等"
        else:
            current_difficulty = "困难"

        # 当前题型（英文转中文）
        type_map_display = {
            "choice": "选择题",
            "fill": "填空题",
            "judge": "判断题",
            "essay": "简答题",
            "calculation": "计算题",
            "coding": "编程题"
        }
        current_type_display = type_map_display.get(question.get("question_type", "choice"), "选择题")

        all_types = ["选择题", "填空题", "判断题", "简答题", "计算题", "编程题"]
        available_types = [t for t in all_types if t != current_type_display]

        # 选择换题方式
        change_mode = st.radio(
            "选择方式",
            ["🎲 从选中的题型中随机", "📋 指定一个题型"],
            index=0,
            key="change_type_mode"
        )

        target_type = None
        selected_types = []

        if "随机" in change_mode:
            st.markdown("**勾选要参与随机的题型**（至少选一个）")
            cols = st.columns(3)
            for i, t in enumerate(available_types):
                with cols[i % 3]:
                    if st.checkbox(t, key=f"random_type_{t}", value=True):
                        selected_types.append(t)

            if not selected_types:
                st.warning("请至少选择一个题型")
        else:
            target_type = st.selectbox(
                "选择题型",
                available_types,
                key="change_type_target"
            )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ 确认换题", use_container_width=True):
                if "随机" in change_mode:
                    if not selected_types:
                        st.warning("请至少选择一个题型")
                    else:
                        import random

                        new_type = random.choice(selected_types)
                else:
                    new_type = target_type

                with st.spinner(f"正在切换为 {new_type}..."):
                    try:
                        response = requests.post(
                            f"{BACKEND_URL}/questions/generate",
                            json={
                                "user_id": user_id,
                                "category": current_category,
                                "topic": current_topic,
                                "question_type": new_type,
                                "difficulty": current_difficulty,
                                "extra": ""
                            },
                            headers={"Authorization": f"Bearer {access_token}"},
                            timeout=60
                        )

                        if response.status_code == 200:
                            new_question = response.json()

                            # 👇 保存到生成历史
                            try:
                                requests.post(
                                    f"{BACKEND_URL}/questions/history/save",
                                    json={
                                        "user_id": user_id,
                                        "question_id": new_question.get("id"),
                                        "title": new_question.get("title"),
                                        "question_type": new_question.get("type"),
                                        "category": new_question.get("category"),
                                        "topic": new_question.get("topic")
                                    },
                                    headers={"Authorization": f"Bearer {access_token}"},
                                    timeout=10
                                )
                            except:
                                pass

                            st.session_state.evaluated = False
                            st.session_state.evaluation_result = None
                            st.session_state.current_question = new_question
                            st.session_state.show_change_type = False
                            st.toast(f"✅ 已切换为 {new_type}", icon="🔄")
                            time.sleep(0.3)
                            st.rerun()
                        else:
                            st.error(f"换题型失败：{response.json().get('detail', '未知错误')}")
                    except Exception as e:
                        st.error(f"错误：{str(e)}")
        with col2:
            if st.button("❌ 取消", use_container_width=True):
                st.session_state.show_change_type = False
                st.rerun()
# ========== 使用说明 ==========
with st.expander("📖 使用说明", expanded=False):
    st.markdown("""
    | 按钮 | 功能 |
    |------|------|
    | 📝 提交 | 提交答案，触发 AI 评估 |
    | 🔄 重新生成 | 换一道同类型、同难度的新题 |
    | 📁 加入题集 | 保存到自定义题集 |
    | 🔄 换题型 | 切换成其他题型（如选择→判断） |
    | ❓ 提示 | 显示解题提示 |

    💡 点击「加入题集」后，该题会自动出现在资源库的「薄弱点卡片」区域。
    """)

# ========== 加入题集弹窗 ==========
if st.session_state.get("show_add_to_set", False):
    with st.popover("📁 加入题集", use_container_width=True):
        st.markdown("### 📁 选择题集")
        st.caption("将当前题目加入以下题集")

        # 获取用户的所有题集
        try:
            response = requests.get(
                f"{BACKEND_URL}/questions/set/list/{user_id}",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10
            )
            if response.status_code == 200:
                sets = response.json()
            else:
                sets = []
        except Exception as e:
            st.error(f"获取题集失败：{str(e)}")
            sets = []

        # 情况1：没有题集
        if not sets:
            st.info("📭 你还没有创建题集")
            st.caption("💡 请前往「资源库 → 我的题集」创建题集后再来添加")
            if st.button("🔗 前往创建题集", use_container_width=True):
                st.session_state.show_add_to_set = False
                st.switch_page("pages/resource_lib.py")

        # 情况2：有题集
        else:
            # 检查题目是否已有 id
            question_id = question.get("id")
            if not question_id:
                st.warning("⚠️ 当前题目尚未保存，请先提交答案或重新生成")
                if st.button("关闭", use_container_width=True):
                    st.session_state.show_add_to_set = False
                    st.rerun()
            else:
                # 显示题集列表
                for s in sets:
                    set_id = s.get("id")
                    set_name = s.get("name", "未命名题集")
                    set_desc = s.get("description", "")
                    question_ids = s.get("question_ids", [])
                    count = len(question_ids)
                    already_in = question_id in question_ids

                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        if already_in:
                            st.markdown(f"**{set_name}** ✅ 已加入")
                        else:
                            st.markdown(f"**{set_name}**")
                        st.caption(f"{set_desc if set_desc else '无描述'}  ·  {count} 道题")
                    with col2:
                        if already_in:
                            st.button("✅ 已加入", key=f"already_{set_id}", disabled=True, use_container_width=True)
                        else:
                            if st.button("📥 加入", key=f"add_to_set_{set_id}", use_container_width=True):
                                try:
                                    res = requests.post(
                                        f"{BACKEND_URL}/questions/set/{set_id}/add/{question_id}",
                                        headers={"Authorization": f"Bearer {access_token}"},
                                        timeout=10
                                    )
                                    if res.status_code == 200:
                                        st.toast(f"✅ 已加入「{set_name}」！", icon="✅")
                                        st.session_state.show_add_to_set = False
                                        time.sleep(0.5)
                                        st.rerun()
                                    else:
                                        st.error(f"加入失败：{res.json().get('detail', '未知错误')}")
                                except Exception as e:
                                    st.error(f"错误：{str(e)}")
                    with col3:
                        if st.button("📖 查看", key=f"view_set_{set_id}", use_container_width=True):
                            st.session_state.current_set_id = set_id
                            st.session_state.show_add_to_set = False
                            st.switch_page("pages/resource_lib.py")
                    st.markdown("---")

        # 关闭按钮
        if st.button("❌ 关闭", use_container_width=True):
            st.session_state.show_add_to_set = False
            st.rerun()