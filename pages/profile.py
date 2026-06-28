import streamlit as st
from utils.auth import update_nickname, update_password, sign_in, upload_avatar, get_avatar_url, update_avatar_url, \
    get_user_nickname, get_user_bio, update_user_bio, ensure_profile_exists
from utils.llm_client import call_llm
import time
import json
import os
import requests

BACKEND_URL = "https://ingenious-rejoicing-production-90b7.up.railway.app"


# ========== 带缓存的后端 API 调用 ==========
@st.cache_data(ttl=60, show_spinner=False)
def get_checkin_via_backend(user_id, access_token):
    try:
        response = requests.get(
            f"{BACKEND_URL}/tools/checkin/{user_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        if response.status_code == 200:
            return response.json().get("projects", []), None
        return [], response.json().get("detail", "获取失败")
    except Exception as e:
        return [], str(e)


@st.cache_data(ttl=60, show_spinner=False)
def get_learning_logs_via_backend(user_id, access_token):
    try:
        response = requests.get(
            f"{BACKEND_URL}/tools/learning-logs/{user_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        if response.status_code == 200:
            return response.json().get("logs", []), None
        return [], response.json().get("detail", "获取失败")
    except Exception as e:
        return [], str(e)


@st.cache_data(ttl=60, show_spinner=False)
def get_mistakes_via_backend(user_id, access_token):
    return [], None


def upload_avatar_via_backend(user_id, image_bytes, access_token):
    try:
        files = {"file": ("avatar.png", image_bytes, "image/png")}
        response = requests.post(
            f"{BACKEND_URL}/auth/upload-avatar/{user_id}",
            files=files,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=30
        )
        if response.status_code == 200:
            return response.json().get("avatar_url"), None
        else:
            error = response.json().get("detail", "上传失败")
            return None, error
    except requests.exceptions.ConnectionError:
        return None, "无法连接到服务器"
    except Exception as e:
        return None, str(e)


def update_bio_via_backend(user_id, bio, access_token):
    try:
        response = requests.put(
            f"{BACKEND_URL}/auth/update-bio",
            json={"user_id": user_id, "bio": bio},
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        if response.status_code == 200:
            return response.json(), None
        else:
            error = response.json().get("detail", "更新失败")
            return None, error
    except requests.exceptions.ConnectionError:
        return None, "无法连接到服务器"
    except Exception as e:
        return None, str(e)


def update_nickname_via_backend(user_id, nickname, access_token):
    try:
        response = requests.put(
            f"{BACKEND_URL}/auth/update-nickname",
            json={"user_id": user_id, "nickname": nickname},
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        if response.status_code == 200:
            return response.json(), None
        else:
            error = response.json().get("detail", "更新失败")
            return None, error
    except requests.exceptions.ConnectionError:
        return None, "无法连接到服务器"
    except Exception as e:
        return None, str(e)


st.set_page_config(
    page_title="个人中心",
    page_icon="👤",
    layout="centered",
    initial_sidebar_state="collapsed",
    menu_items={'Get Help': None, 'Report a bug': None, 'About': None}
)

# ====== 全局样式 ======
st.markdown("""
<style>
    .stApp { background: var(--background-color); }
    .main .block-container { background: transparent; }
    .stApp header { display: none; }

    h1, h2, h3, h4, h5, h6, p, span, div, label, .stMarkdown, .stCaption,
    .stButton button, .stAlert, .stInfo, .stWarning, .stSuccess,
    .stTextInput label, .stSelectbox label, .stNumberInput label,
    .stTextInput input, .stSelectbox select, .stNumberInput input,
    .stTextArea label, .stTextArea textarea {
        text-shadow: 0 1px 4px rgba(0,0,0,0.06), 0 2px 8px rgba(0,0,0,0.03);
    }

    .stButton button {
        background: rgba(128,128,128,0.06) !important;
        border: none !important;
        border-radius: 12px !important;
        color: var(--text-color) !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04), inset 0 1px 0 rgba(255,255,255,0.06) !important;
        transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
        font-weight: 500 !important;
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
    }
    .stButton button:hover {
        background: rgba(128,128,128,0.10) !important;
        box-shadow: 0 6px 24px rgba(0,0,0,0.10), inset 0 1px 0 rgba(255,255,255,0.08) !important;
        transform: translateY(-3px) !important;
    }
    .stButton button:active {
        transform: translateY(0px) !important;
    }
    .stButton button:disabled {
        opacity: 0.35 !important;
        cursor: not-allowed !important;
        transform: none !important;
    }

    .stTextInput input, .stSelectbox select, .stNumberInput input,
    .stTextArea textarea {
        background: rgba(128,128,128,0.05) !important;
        border: none !important;
        border-radius: 12px !important;
        color: var(--text-color) !important;
        box-shadow: inset 0 2px 8px rgba(0,0,0,0.06), 0 1px 0 rgba(255,255,255,0.04) !important;
        transition: all 0.3s ease !important;
        backdrop-filter: blur(4px);
        -webkit-backdrop-filter: blur(4px);
    }
    .stTextInput input:focus, .stSelectbox select:focus,
    .stNumberInput input:focus, .stTextArea textarea:focus {
        background: rgba(128,128,128,0.08) !important;
        box-shadow: inset 0 2px 12px rgba(0,0,0,0.10), 0 0 30px rgba(128,128,128,0.04) !important;
    }

    .stAlert {
        background: rgba(128,128,128,0.05) !important;
        border: none !important;
        border-radius: 12px !important;
        box-shadow: 0 2px 12px rgba(0,0,0,0.04) !important;
        text-shadow: 0 1px 4px rgba(0,0,0,0.06), 0 2px 8px rgba(0,0,0,0.03) !important;
        backdrop-filter: blur(4px);
        -webkit-backdrop-filter: blur(4px);
    }

    .stProgress > div > div {
        background: rgba(128,128,128,0.10) !important;
        border-radius: 6px !important;
        height: 8px !important;
        border: none !important;
        box-shadow: inset 0 1px 4px rgba(0,0,0,0.06) !important;
    }
    .stProgress > div > div > div {
        border-radius: 6px !important;
        box-shadow: 0 0 20px rgba(255,255,255,0.04) !important;
        transition: width 0.6s ease !important;
    }

    hr { border: none !important; height: 1px !important; background: rgba(128,128,128,0.10) !important; margin: 16px 0 !important; }

    .stFileUploader {
        border: none !important;
        border-radius: 12px !important;
        padding: 4px !important;
        background: rgba(128,128,128,0.03) !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.03) !important;
    }
    .stFileUploader > div {
        border: none !important;
        box-shadow: none !important;
    }
    .stFileUploader label {
        border: none !important;
        box-shadow: none !important;
    }
    .stFileUploader .stFileUploaderDropzone {
        border: 1px dashed rgba(128,128,128,0.15) !important;
        border-radius: 12px !important;
        background: rgba(128,128,128,0.03) !important;
        padding: 24px !important;
        box-shadow: inset 0 2px 8px rgba(0,0,0,0.04) !important;
        transition: all 0.3s ease !important;
    }
    .stFileUploader .stFileUploaderDropzone:hover {
        background: rgba(128,128,128,0.06) !important;
        box-shadow: inset 0 2px 12px rgba(0,0,0,0.08) !important;
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

# ========== 用户信息 ==========
user_email = st.session_state.user_email
user_id = st.session_state.user_id
user_account = st.session_state.get("user_account", "未设置")

nickname = get_user_nickname(user_id) or st.session_state.get("username", "用户")

# ========== 头像 ==========
st.subheader("🖼️ 头像")

if "avatar_url" not in st.session_state:
    st.session_state.avatar_url = get_avatar_url(user_id)

col_avatar1, col_avatar2 = st.columns([1, 3])
with col_avatar1:
    if st.session_state.avatar_url:
        st.image(st.session_state.avatar_url, width=80)
    else:
        st.markdown(
            '<div style="width:80px;height:80px;border-radius:50%;background:rgba(128,128,128,0.06);display:flex;align-items:center;justify-content:center;font-size:32px;box-shadow:inset 0 2px 8px rgba(0,0,0,0.06);">👤</div>',
            unsafe_allow_html=True)

with col_avatar2:
    uploader_key = st.session_state.get("avatar_uploader_key", 0)
    uploaded_avatar = st.file_uploader(
        "更换头像",
        type=["png", "jpg", "jpeg"],
        label_visibility="collapsed",
        key=f"avatar_uploader_{uploader_key}"
    )

    if uploaded_avatar:
        with st.spinner("上传中..."):
            avatar_url, err = upload_avatar_via_backend(
                user_id,
                uploaded_avatar.getvalue(),
                st.session_state.access_token
            )
            if avatar_url:
                st.session_state.avatar_url = avatar_url
                st.session_state.avatar_uploader_key = uploader_key + 1
                st.toast("✅ 头像已更新", icon="✅")
                time.sleep(0.3)
                st.rerun()
            else:
                st.error(f"上传失败：{err}")

st.markdown("---")

# ========== 在线状态 ==========
st.subheader("🟢 在线状态")

from utils.auth import get_user_status, update_user_status

current_status = get_user_status(user_id)

status_options = {
    "online": "🟢 在线（好友可见）",
    "invisible": "🔘 隐身（好友不可见）"
}

selected_status = st.selectbox(
    "选择状态",
    options=list(status_options.keys()),
    format_func=lambda x: status_options[x],
    index=0 if current_status == "online" else 1
)

if selected_status != current_status:
    if update_user_status(user_id, selected_status):
        st.toast(f"✅ 已切换为 {status_options[selected_status]}", icon="✅")
        st.rerun()
    else:
        st.error("切换失败")

st.caption("💡 提示：隐身模式可以让好友看不到你的在线状态")
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
        success, err = update_nickname_via_backend(user_id, new_nickname, st.session_state.access_token)
        if success:
            st.session_state.username = new_nickname
            st.toast("✅ 昵称已更新", icon="✅")
            time.sleep(0.3)
            st.rerun()
        else:
            st.error(f"更新失败：{err}")

st.markdown("---")

# ========== 个人简介 ==========
st.subheader("📝 个人简介")

if "user_bio" not in st.session_state:
    st.session_state.user_bio = get_user_bio(user_id) or ""

user_bio = st.text_area("", value=st.session_state.user_bio, placeholder="介绍一下自己...", height=100,
                        label_visibility="collapsed")
if st.button("保存简介", use_container_width=True):
    success, err = update_bio_via_backend(user_id, user_bio, st.session_state.access_token)
    if success:
        st.session_state.user_bio = user_bio
        st.toast("✅ 简介已保存", icon="✅")
        time.sleep(0.3)
        st.rerun()
    else:
        st.error(f"保存失败：{err}")

st.markdown("---")

# ========== 用户画像 ==========
st.subheader("🎯 用户画像")

access_token = st.session_state.access_token

projects, _ = get_checkin_via_backend(user_id, access_token)
total_checkin_days = sum(p.get("completed_days", 0) for p in projects)

logs, _ = get_learning_logs_via_backend(user_id, access_token)
log_keywords = list(set([log.get("keyword", "") for log in logs]))[:10]

mistakes, _ = get_mistakes_via_backend(user_id, access_token)
learning_cnt = len([m for m in mistakes if m.get("status") == "learning"])
conquered_cnt = len([m for m in mistakes if m.get("status") == "conquered"])

mastery_file = f"mastery_{user_id}.json"
if os.path.exists(mastery_file):
    with open(mastery_file, "r") as f:
        mastery_data = json.load(f)
else:
    mastery_data = {"python_basics": 65}
    with open(mastery_file, "w") as f:
        json.dump(mastery_data, f)

mastery_score = mastery_data.get("python_basics", 65)

st.markdown(f"**📊 Python 基础语法掌握程度**")
st.progress(mastery_score / 100)
st.caption(f"当前掌握度：{mastery_score}%")

st.markdown("**🏷️ 学习标签**")
col_tag1, col_tag2, col_tag3 = st.columns(3)
with col_tag1:
    st.markdown(f"- 连续打卡 {total_checkin_days} 天")
    st.markdown(f"- 攻克 {conquered_cnt} 道错题")
with col_tag2:
    st.markdown(f"- 学习 {len(log_keywords)} 个知识点")
with col_tag3:
    st.markdown(f"- 专注时长待统计")

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
    from utils.auth import update_user_status

    update_user_status(user_id, "offline")
    for key in ["logged_in", "user_email", "user_id", "username", "access_token",
                "session_mgr", "user_memory", "checkin_manager", "mistake_manager",
                "learning_log_manager", "countdown_manager", "timer_manager",
                "user_bio", "user_avatar", "user_account", "avatar_url"]:
        if key in st.session_state:
            del st.session_state[key]
    st.switch_page("app.py")

st.caption("💡 提示：邮箱暂不可修改")