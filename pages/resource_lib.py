import streamlit as st
import requests
import time
import json
from datetime import datetime

# 后端 API 地址
BACKEND_URL = "http://localhost:8000"

st.set_page_config(
    page_title="资源库",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="auto"
)

# 登录检查
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("请先登录")
    st.stop()

user_id = st.session_state.user_id
access_token = st.session_state.access_token

def get_question_detail(question_id):
    try:
        response = requests.get(
            f"{BACKEND_URL}/questions/{question_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None
# ========== 工具函数 ==========
def get_color_by_mastery(score):
    """根据掌握程度返回颜色（20种渐变）"""
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


def load_mastery_data(user_id, access_token):
    try:
        response = requests.get(
            f"{BACKEND_URL}/questions/mastery/{user_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []


# ========== 顶部布局：左侧标题 + 右侧掌握度看板入口 ==========
col_left, col_right = st.columns([1, 2])

with col_left:
    st.title("📚 资源库")
    st.caption("生成题目 · 管理题集 · 错题本 · 薄弱点巩固")
    if st.button("← 返回主界面"):
        st.switch_page("app.py")

with col_right:
    # 获取所有知识点
    all_points = load_mastery_data(user_id, access_token)

    # 统计
    weak_count = len([p for p in all_points if p['mastery_score'] < 60])
    consolidate_count = len([p for p in all_points if 60 <= p['mastery_score'] < 80])
    strong_count = len([p for p in all_points if p['mastery_score'] >= 80])

    # 显示统计摘要
    st.markdown(f"""
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
        <span style="font-size:15px; font-weight:bold;">📊 掌握度看板</span>
        <span style="font-size:13px;">
            🔴 薄弱 {weak_count}  &nbsp;|&nbsp; 🟡 待巩固 {consolidate_count}  &nbsp;|&nbsp; 🟢 优势 {strong_count}
        </span>
    </div>
    """, unsafe_allow_html=True)

    # 显示前 4 个薄弱点卡片
    weak_points = [p for p in all_points if p['mastery_score'] < 60]
    weak_points.sort(key=lambda x: x['mastery_score'])

    if weak_points:
        # 颜色图例
        st.markdown("""
        <div style="display:flex; align-items:center; gap:6px; margin-bottom:10px;">
            <span style="font-size:11px; color:#FF0000;">0%</span>
            <div style="flex:1; height:6px; border-radius:4px; background:linear-gradient(to right, 
                #FF0000, #FF1A00, #FF4400, #FF6E00, #FF9900, #FFC400, #D4E000, #A8D500, #66CC33, #00CC66);">
            </div>
            <span style="font-size:11px; color:#00CC66;">100%</span>
            <span style="font-size:11px; margin-left:6px; color:#888;">薄弱 &lt;60%</span>
        </div>
        """, unsafe_allow_html=True)

        display_count = min(len(weak_points), 4)
        card_cols = st.columns(display_count)
        for i in range(display_count):
            with card_cols[i]:
                wp = weak_points[i]
                color = get_color_by_mastery(wp['mastery_score'])
                st.markdown(f"""
                <div style="background:{color}; color:white; border-radius:10px; padding:10px 8px; text-align:center; min-height:60px; display:flex; flex-direction:column; justify-content:center; box-shadow:0 2px 6px rgba(0,0,0,0.1);">
                    <div style="font-size:12px; font-weight:bold; margin-bottom:2px;">{wp['topic']}</div>
                    <div style="font-size:18px; font-weight:bold;">{wp['mastery_score']}%</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("🎯", key=f"conquer_{wp['topic']}_{i}", use_container_width=True):
                    st.session_state.practice_mode = "mastery_board"
                    st.session_state.practice_topic = wp['topic']
                    st.switch_page("pages/generate_from_mastery.py")

        # 查看全部按钮
        if st.button("📋 查看全部知识点", use_container_width=True):
            st.switch_page("pages/mastery_board.py")
    else:
        st.info("🎉 暂无薄弱点，继续保持！")
        if st.button("📋 查看全部知识点", use_container_width=True):
            st.switch_page("pages/mastery_board.py")

st.markdown("---")

# ========== Tab 切换 ==========
tab1, tab2, tab3, tab4 = st.tabs([
    "🤖 生成题目",
    "📁 我的题集",
    "📖 错题本",
    "📜 生成历史"
])

# ========== Tab1: 生成题目 ==========
with tab1:
    st.subheader("🤖 生成新题目")

    # 检查是否来自掌握度看板
    practice_mode = st.session_state.get("practice_mode")
    practice_topic = st.session_state.get("practice_topic", "")

    with st.form("generate_question_form"):
        col1, col2 = st.columns(2)
        with col1:
            if practice_mode == "mastery_board" and practice_topic:
                # 来自掌握度看板：大方向锁定
                st.markdown(f"**📌 大类方向：** {practice_topic} 🔒")
                category = st.text_input("学科/领域", placeholder="例：Python、数学、语文、英语、物理...")
                # 隐藏的 topic 占位，用 final_topic 代替
                topic_hint = st.text_input(
                    "细化知识点（可选）",
                    placeholder=f"例：在「{practice_topic}」下细分，如列表推导式、三角函数..."
                )
                # 组合最终知识点
                final_topic = practice_topic + (f" - {topic_hint}" if topic_hint else "")
                # 用 hidden 字段存最终值
                st.session_state._final_topic = final_topic
            else:
                category = st.text_input("学科/领域", placeholder="例：Python、数学、语文、英语、物理...")
                topic = st.text_input("具体知识点", placeholder="例：列表推导式、三角函数、古诗词鉴赏、牛顿定律...")
                st.session_state._final_topic = topic

        with col2:
            question_type = st.selectbox("题型", [
                "选择题",
                "填空题",
                "判断题",
                "简答题",
                "计算题",
                "论述题",
                "编程题"
            ])
            difficulty = st.selectbox("难度", ["简单", "中等", "困难"])

        extra = st.text_area("补充说明（可选）", placeholder="例：需要包含实际代码示例 / 结合生活场景...", height=60)
        submitted = st.form_submit_button("✨ 一键生成", use_container_width=True)

        if submitted:
            # 获取最终知识点
            if practice_mode == "mastery_board" and practice_topic:
                final_topic = st.session_state.get("_final_topic", practice_topic)
                if not final_topic or final_topic == practice_topic:
                    st.warning("请至少填写细化知识点或确认大类方向")
                    st.stop()
            else:
                final_topic = topic
                if not final_topic:
                    st.warning("请填写具体知识点")
                    st.stop()

            with st.spinner("AI 正在生成题目..."):
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/questions/generate",
                        json={
                            "user_id": user_id,
                            "category": category if category else "通用",
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

                        # 保存生成历史
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

                        # 清除看板模式
                        if practice_mode == "mastery_board":
                            st.session_state.practice_mode = None
                            st.session_state.practice_topic = None
                            st.session_state._final_topic = None

                        st.session_state.current_question = question_data
                        st.success("✅ 题目生成成功！")
                        time.sleep(0.5)
                        st.switch_page("pages/do_question.py")
                    else:
                        error = response.json().get("detail", "生成失败")
                        st.error(f"❌ 生成失败：{error}")
                except requests.exceptions.Timeout:
                    st.error("⏰ 请求超时，请重试")
                except Exception as e:
                    st.error(f"❌ 错误：{str(e)}")

# ========== Tab2: 我的题集 ==========
# ========== Tab2: 我的题集 ==========
with tab2:
    st.subheader("📁 我的题集")


    # 获取题集列表
    # 获取题集列表
    def load_question_sets():
        try:
            response = requests.get(
                f"{BACKEND_URL}/questions/set/list/{user_id}",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10
            )
            if response.status_code == 200:
                sets = response.json()
                # 计算每个题集的平均掌握度
                for s in sets:
                    question_ids = s.get('question_ids', [])
                    if question_ids:
                        total = 0
                        count = 0
                        for q_id in question_ids:
                            q = get_question_detail(q_id)
                            if q:
                                total += q.get('mastery_score', 0)
                                count += 1
                        s['avg_mastery'] = round(total / count) if count > 0 else 0
                    else:
                        s['avg_mastery'] = 0
                return sets
            return []
        except:
            return []


    # 创建题集
    def create_question_set(name, desc):
        try:
            response = requests.post(
                f"{BACKEND_URL}/questions/set/create?user_id={user_id}",
                json={
                    "name": name,
                    "description": desc,
                    "set_type": "custom"
                },
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10
            )
            return response.status_code in [200, 201, 204], response.text
        except Exception as e:
            return False, str(e)


    # 删除题集
    def delete_question_set(set_id):
        try:
            response = requests.delete(
                f"{BACKEND_URL}/questions/set/{set_id}",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10
            )
            return response.status_code in [200, 204]
        except:
            return False


    # 从题集移除题目
    def remove_question_from_set(set_id, question_id):
        try:
            response = requests.post(
                f"{BACKEND_URL}/questions/set/{set_id}/remove/{question_id}",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10
            )
            return response.status_code in [200, 204]
        except:
            return False


    # 获取题目详情
    def get_question_detail(question_id):
        try:
            response = requests.get(
                f"{BACKEND_URL}/questions/{question_id}",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None


    # 创建题集（放在最上面）
    with st.expander("➕ 创建新题集", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            new_set_name = st.text_input("题集名称", placeholder="例：Python基础", key="new_set_name")
        with col2:
            new_set_desc = st.text_input("描述（可选）", placeholder="例：Python核心知识点", key="new_set_desc")

        if st.button("✨ 创建题集", key="create_set_btn", use_container_width=True):
            if new_set_name:
                success, msg = create_question_set(new_set_name, new_set_desc)
                if success:
                    st.success(f"✅ 题集「{new_set_name}」创建成功")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error(f"创建失败：{msg}")
            else:
                st.warning("请输入题集名称")

    st.markdown("---")

    # 获取并显示题集列表
    question_sets = load_question_sets()

    # 搜索题集
    search_set = st.text_input("🔍 搜索题集", placeholder="输入题集名称搜索...", key="search_set")

    # 过滤题集
    filtered_sets = question_sets
    if search_set:
        filtered_sets = [s for s in filtered_sets if search_set.lower() in s.get("name", "").lower()]

    if not filtered_sets:
        if search_set:
            st.info("📭 没有匹配的题集")
        else:
            st.info("📭 暂无题集，点击上方创建")
    else:
        for s in filtered_sets:
            set_id = s.get('id')
            set_name = s.get('name', '未命名')
            set_desc = s.get('description', '')
            question_ids = s.get('question_ids', [])

            created_at = s.get('created_at', '')
            if created_at:
                try:
                    from datetime import datetime, timedelta

                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    dt_local = dt + timedelta(hours=8)
                    create_time = dt_local.strftime("%Y-%m-%d %H:%M")
                except:
                    create_time = created_at[:16]
            else:
                create_time = "未知时间"

            col1, col2, col3, col4 = st.columns([3, 1.5, 1, 1])
            with col1:
                st.markdown(f"**{set_name}**")
                st.caption(f"{set_desc if set_desc else '无描述'}  ·  📅 {create_time}  ·  📝 {len(question_ids)} 道题")

                # 平均掌握度进度条
                avg_mastery = s.get('avg_mastery', 0)
                bar_color = get_color_by_mastery(avg_mastery)

                st.markdown(f"""
                <div style="display:flex; align-items:center; gap:10px; margin-top:4px;">
                    <span style="font-size:12px; color:#888;">平均掌握度</span>
                    <div style="flex:1; height:6px; background:#2a2a3a; border-radius:3px; overflow:hidden;">
                        <div style="width:{avg_mastery}%; height:100%; background:{bar_color}; border-radius:3px;"></div>
                    </div>
                    <span style="font-size:13px; font-weight:bold; color:{bar_color};">{avg_mastery}%</span>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                if st.button("📖 查看", key=f"view_{set_id}"):
                    st.session_state.view_set_id = set_id
                    st.switch_page("pages/set_detail.py")
            with col3:
                if st.button("🗑️ 删除", key=f"del_{set_id}"):
                    if delete_question_set(set_id):
                        st.success(f"✅ 题集「{set_name}」已删除")
                        # 直接从列表移除
                        question_sets = [s for s in question_sets if s.get('id') != set_id]
                        filtered_sets = [s for s in filtered_sets if s.get('id') != set_id]
                        time.sleep(0.3)
                        st.rerun()
                    else:
                        st.error("删除失败")
            with col4:
                if question_ids:
                    if st.button("🎯 练习", key=f"practice_{set_id}"):
                        st.session_state.practice_set_id = set_id
                        st.session_state.practice_questions = question_ids
                        st.session_state.practice_index = 0
                        st.switch_page("pages/do_question.py")
            st.markdown("---")

# ========== Tab3: 错题本 ==========
# ========== Tab3: 错题本 ==========
with tab3:
    st.subheader("📖 错题本")
    # 👇 把 filter_options 定义在这里
    filter_options = ["全部", "选择题", "填空题", "判断题", "简答题", "计算题", "论述题", "编程题"]
    type_map = {
        "选择题": "choice",
        "填空题": "fill",
        "判断题": "judge",
        "简答题": "essay",
        "计算题": "calculation",
        "论述题": "essay",
        "编程题": "coding"
    }
    type_display_map = {
        "choice": "选择题",
        "fill": "填空题",
        "judge": "判断题",
        "essay": "简答题/论述题",
        "calculation": "计算题",
        "coding": "编程题"
    }
    # 获取错题列表
    try:
        response = requests.get(
            f"{BACKEND_URL}/questions/mistakes/{user_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        if response.status_code == 200:
            mistakes = response.json()
        else:
            mistakes = []
    except:
        mistakes = []

    # 按状态分组
    learning = [m for m in mistakes if m.get('mistake_status') == 'learning']
    conquered = [m for m in mistakes if m.get('mistake_status') == 'conquered']

    # 统计
    st.caption(f"📚 学习中：{len(learning)}  |  ✅ 已攻克：{len(conquered)}")
    st.markdown("---")

    if not mistakes:
        st.info("🎉 暂无错题，继续保持！")
    else:
        # 两个 Tab：学习中 + 已攻克
        tab_learning, tab_conquered = st.tabs(["📖 学习中", "✅ 已攻克"])

        # ====== Tab1: 学习中 ======
        with tab_learning:
            if not learning:
                st.info("🎉 没有学习中的错题，继续加油！")
            else:
                # 搜索和筛选
                col_search, col_filter = st.columns([3, 1])
                with col_search:
                    search_learning = st.text_input("🔍 搜索题目", placeholder="输入关键词...", key="search_learning")
                with col_filter:
                    filter_options = ["全部", "选择题", "填空题", "判断题", "简答题", "计算题", "论述题", "编程题"]
                    filter_learning = st.selectbox("筛选题型", filter_options, key="filter_learning")

                # 题型映射
                type_map = {
                    "选择题": "choice",
                    "填空题": "fill",
                    "判断题": "judge",
                    "简答题": "essay",
                    "计算题": "calculation",
                    "论述题": "essay",
                    "编程题": "coding"
                }
                type_display_map = {
                    "choice": "选择题",
                    "fill": "填空题",
                    "judge": "判断题",
                    "essay": "简答题/论述题",
                    "calculation": "计算题",
                    "coding": "编程题"
                }

                # 过滤
                filtered = learning
                if search_learning:
                    filtered = [m for m in filtered if search_learning.lower() in m.get("title", "").lower()]
                if filter_learning != "全部":
                    filter_en = type_map.get(filter_learning)
                    filtered = [m for m in filtered if m.get("question_type") == filter_en]

                if not filtered:
                    st.info("📭 没有匹配的错题")
                else:
                    for m in filtered:
                        title = m.get('title', '无题目')[:60]
                        mastery = m.get('mastery_score', 0)
                        q_type = type_display_map.get(m.get('question_type', ''), '未知')
                        added_at = m.get('mistake_added_at', '')

                        if added_at:
                            try:
                                from datetime import datetime

                                # 直接显示，不加 8 小时
                                dt = datetime.fromisoformat(added_at.replace('Z', '+00:00'))
                                added_time = dt.strftime("%Y-%m-%d %H:%M")
                            except:
                                added_time = added_at[:16]
                        else:
                            added_time = "未知时间"

                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.markdown(f"**{title}**")
                            st.caption(f"掌握度：{mastery}%  |  题型：{q_type}  |  加入时间：{added_time}")
                        with col2:
                            if st.button("📝 复习", key=f"conquered_practice_{m.get('id')}"):
                                st.session_state.current_question = m
                                st.session_state.from_mistake_book = True  # 👈 加上
                                st.switch_page("pages/do_question.py")
                        st.markdown("---")

        # ====== Tab2: 已攻克 ======
        with tab_conquered:
            if not conquered:
                st.info("📭 暂无已攻克的错题")
            else:
                col_search, col_filter = st.columns([3, 1])
                with col_search:
                    search_conquered = st.text_input("🔍 搜索题目", placeholder="输入关键词...", key="search_conquered")
                with col_filter:
                    filter_conquered = st.selectbox("筛选题型", filter_options, key="filter_conquered")

                filtered = conquered
                if search_conquered:
                    filtered = [m for m in filtered if search_conquered.lower() in m.get("title", "").lower()]
                if filter_conquered != "全部":
                    filter_en = type_map.get(filter_conquered)
                    filtered = [m for m in filtered if m.get("question_type") == filter_en]

                if not filtered:
                    st.info("📭 没有匹配的错题")
                else:
                    for m in filtered:
                        title = m.get('title', '无题目')[:60]
                        mastery = m.get('mastery_score', 0)
                        q_type = type_display_map.get(m.get('question_type', ''), '未知')

                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.markdown(f"**{title}**")
                            st.caption(f"掌握度：{mastery}%  |  题型：{q_type}")
                        with col2:
                            if st.button("📝 复习", key=f"conquered_practice_{m.get('id')}"):
                                st.session_state.current_question = m
                                st.switch_page("pages/do_question.py")
                        st.markdown("---")

# ========== Tab4: 生成历史 ==========
with tab4:
    st.subheader("📜 生成历史")

    # 从后端获取历史
    try:
        response = requests.get(
            f"{BACKEND_URL}/questions/history/{user_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        if response.status_code == 200:
            history = response.json()
        else:
            history = []
    except:
        history = []

    if not history:
        st.info("📭 暂无生成记录，去生成一道题目吧！")
    else:
        # 搜索框
        search = st.text_input("🔍 搜索题目", placeholder="输入关键词搜索...")

        # 筛选
        filter_options = ["全部", "选择题", "填空题", "判断题", "简答题", "计算题", "编程题"]
        filter_type = st.selectbox("筛选题型", filter_options, key="history_filter")

        # 题型映射（中文 → 英文）
        type_map = {
            "选择题": "choice",
            "填空题": "fill",
            "判断题": "judge",
            "简答题": "essay",
            "计算题": "calculation",
            "编程题": "coding"
        }

        # 过滤
        filtered = history
        if search:
            filtered = [h for h in filtered if search.lower() in h.get("title", "").lower()]
        if filter_type != "全部":
            filter_type_en = type_map.get(filter_type)
            filtered = [h for h in filtered if h.get("question_type") == filter_type_en]

        if not filtered:
            st.info("📭 没有匹配的记录")
        else:
            for h in filtered:
                status_map = {
                    "pending": "🔄 待练习",
                    "practiced": "📖 已练习",
                    "mastered": "✅ 已掌握"
                }
                status_display = status_map.get(h.get("status", "pending"), "🔄 待练习")

                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.markdown(f"**{h.get('title', '')[:50]}**")
                    # 把英文题型转成中文显示
                    type_display_map = {
                        "choice": "选择题",
                        "fill": "填空题",
                        "judge": "判断题",
                        "essay": "简答题",
                        "calculation": "计算题",
                        "coding": "编程题"
                    }
                    q_type_display = type_display_map.get(h.get('question_type', ''), h.get('question_type', '未知'))
                    st.caption(
                        f"{q_type_display}  |  {h.get('category', '未分类')}  |  {h.get('topic', '')}")
                with col2:
                    created_at = h.get('created_at', '')
                    if created_at:
                        try:
                            from datetime import datetime, timedelta

                            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                            dt_local = dt + timedelta(hours=8)
                            display_time = dt_local.strftime("%Y-%m-%d %H:%M")
                        except:
                            display_time = created_at.replace('T', ' ').replace('Z', '')[:16]
                        st.caption(f"生成时间：{display_time}")
                    st.caption(f"状态：{status_display}")
                with col3:
                    if st.button("📝 练习", key=f"history_{h.get('id', h.get('created_at', ''))}"):
                        with st.spinner("加载题目..."):
                            try:
                                response = requests.get(
                                    f"{BACKEND_URL}/questions/{h.get('question_id')}",
                                    headers={"Authorization": f"Bearer {access_token}"},
                                    timeout=10
                                )
                                if response.status_code == 200:
                                    question_data = response.json()
                                    st.session_state.current_question = question_data
                                    st.switch_page("pages/do_question.py")
                                else:
                                    st.error("获取题目失败")
                            except Exception as e:
                                st.error(f"错误：{str(e)}")
                st.markdown("---")
