import streamlit as st
from utils.auth import update_nickname, update_password, sign_in
from utils.llm_client import call_llm
import time
import json
import os

st.set_page_config(
    page_title="个人中心",
    page_icon="👤",
    layout="centered",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

st.markdown("""
<style>
    .stApp header {
        display: none;
    }
    /* 头像圆形样式 */
    .avatar-container {
        display: flex;
        justify-content: center;
        margin-bottom: 20px;
    }
    .avatar-img {
        width: 100px;
        height: 100px;
        border-radius: 50%;
        object-fit: cover;
        border: 3px solid #6c63ff;
    }
</style>
""", unsafe_allow_html=True)

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("请先登录")
    st.stop()

st.title("👤 个人中心")
st.caption("管理你的账号信息")
if st.button("← 返回主界面", use_container_width=True):
    st.switch_page("app.py")
# 获取用户信息
user_email = st.session_state.user_email
user_id = st.session_state.user_id
nickname = st.session_state.username
user_account = st.session_state.get("user_account", "未设置")

# 初始化个人简介和头像（如果不存在）
if "user_bio" not in st.session_state:
    st.session_state.user_bio = ""
if "user_avatar" not in st.session_state:
    st.session_state.user_avatar = None

# ========== 头像 ==========
st.subheader("🖼️ 头像")
col_avatar1, col_avatar2 = st.columns([1, 3])
with col_avatar1:
    if st.session_state.user_avatar:
        st.image(st.session_state.user_avatar, width=80, output_format="PNG")
    else:
        st.markdown('<div class="avatar-container"><div style="width:80px;height:80px;border-radius:50%;background:#2a2a3a;display:flex;align-items:center;justify-content:center;font-size:32px;">👤</div></div>', unsafe_allow_html=True)
with col_avatar2:
    uploaded_avatar = st.file_uploader("更换头像", type=["png", "jpg", "jpeg"], label_visibility="collapsed")
    if uploaded_avatar:
        st.session_state.user_avatar = uploaded_avatar
        st.rerun()

st.markdown("---")

# ========== 账号信息 ==========
st.subheader("📌 账号信息")
st.text_input("账号", value=user_account, disabled=True)
st.text_input("邮箱", value=user_email, disabled=True)

st.markdown("---")

# ========== 昵称 ==========
st.subheader("✏️ 昵称")
new_nickname = st.text_input("新昵称", value=nickname, label_visibility="collapsed")
if st.button("保存昵称", use_container_width=True):
    if not new_nickname:
        st.warning("昵称不能为空")
    elif new_nickname == nickname:
        st.info("昵称没有变化")
    else:
        success = update_nickname(user_id, new_nickname)
        if success:
            st.session_state.username = new_nickname
            st.success("昵称已更新")
            time.sleep(0.5)
            st.rerun()
        else:
            st.error("更新失败")

st.markdown("---")

# ========== 个人简介 ==========
st.subheader("📝 个人简介")
user_bio = st.text_area("", value=st.session_state.user_bio, placeholder="介绍一下自己...", height=100, label_visibility="collapsed")
if st.button("保存简介", use_container_width=True):
    st.session_state.user_bio = user_bio
    st.success("简介已保存")

st.markdown("---")

# ========== 用户画像 ==========
st.subheader("🎯 用户画像")

# 获取学习数据
from datetime import datetime
log_mgr = st.session_state.learning_log_manager
mistake_mgr = st.session_state.mistake_manager
checkin_mgr = st.session_state.checkin_manager

logs = log_mgr.get_recent_logs(limit=50)
log_keywords = list(set([log["keyword"] for log in logs]))[:10]
learning_cnt, conquered_cnt = mistake_mgr.count_by_status()
projects = checkin_mgr.get_projects()
total_checkin_days = sum(p["completed_days"] for p in projects)

# 计算掌握程度（示例：从 mastery.json 读取，如果没有则默认）
mastery_file = f"mastery_{user_id}.json"
if os.path.exists(mastery_file):
    with open(mastery_file, "r") as f:
        mastery_data = json.load(f)
else:
    mastery_data = {"python_basics": 65}

mastery_score = mastery_data.get("python_basics", 65)

# 展示进度条
st.markdown(f"**📊 Python 基础语法掌握程度**")
st.progress(mastery_score / 100)
st.caption(f"当前掌握度：{mastery_score}%")

# 展示标签
st.markdown("**🏷️ 学习标签**")
col_tag1, col_tag2, col_tag3 = st.columns(3)
with col_tag1:
    st.markdown(f"- 连续打卡 {total_checkin_days} 天")
    st.markdown(f"- 攻克 {conquered_cnt} 道错题")
with col_tag2:
    st.markdown(f"- 学习 {len(log_keywords)} 个知识点")
with col_tag3:
    st.markdown(f"- 专注时长待统计")

# 正面分析（一句话）
st.markdown("**📝 一句话总结**")
if mastery_score >= 70:
    st.success(f"你已掌握 Python 基础语法的 {mastery_score}%，基础扎实，继续保持！")
elif mastery_score >= 50:
    st.info(f"你已掌握 Python 基础语法的 {mastery_score}%，再努力一下就能突破！")
else:
    st.warning(f"你已掌握 Python 基础语法的 {mastery_score}%，建议多练习巩固基础。")

st.markdown("---")

# ========== 一键生成建议 ==========
st.subheader("💡 学习建议")
if st.button("📈 一键生成建议", use_container_width=True):
    with st.spinner("正在分析你的学习数据..."):
        prompt = f"""请根据以下学习数据，给用户生成一份简短的学习建议（100字以内）：

- 已攻克错题：{conquered_cnt} 个
- 学习中错题：{learning_cnt} 个
- 累计打卡天数：{total_checkin_days} 天
- 掌握程度：{mastery_score}%
- 近期学习内容：{'、'.join(log_keywords[:5]) if log_keywords else '暂无'}

要求：语气温暖、正向激励，可适当指出薄弱点，给出具体建议。"""
        report = call_llm([{"role": "user", "content": prompt}], temperature=0.7)
        st.info(report)

st.markdown("---")

# ========== 修改密码 ==========
st.subheader("🔒 修改密码")
old_password = st.text_input("当前密码", type="password")
new_password = st.text_input("新密码", type="password")
confirm_password = st.text_input("确认新密码", type="password")

if st.button("修改密码", use_container_width=True):
    if not old_password or not new_password:
        st.warning("请填写当前密码和新密码")
    elif new_password != confirm_password:
        st.warning("两次输入的新密码不一致")
    elif len(new_password) < 6:
        st.warning("密码长度至少6位")
    else:
        verify_user, err = sign_in(user_email, old_password)
        if not verify_user:
            st.error("当前密码错误")
        else:
            access_token = st.session_state.get("access_token")
            if not access_token:
                st.error("请重新登录后再试")
            else:
                success = update_password(access_token, new_password)
                if success:
                    st.success("密码已修改，请重新登录")
                    time.sleep(1)
                    for key in ["logged_in", "user_email", "user_id", "username", "access_token"]:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()
                else:
                    st.error("修改失败")

st.markdown("---")

# ========== 退出登录 ==========
if st.button("🚪 退出登录", use_container_width=True):
    for key in ["logged_in", "user_email", "user_id", "username", "access_token",
                "session_mgr", "user_memory", "checkin_manager", "mistake_manager",
                "learning_log_manager", "countdown_manager", "timer_manager",
                "user_bio", "user_avatar", "user_account"]:
        if key in st.session_state:
            del st.session_state[key]
    st.switch_page("app.py")

st.caption("💡 提示：邮箱暂不可修改")