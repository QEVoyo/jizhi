<template>
  <div class="settings-page">
    <!-- Toast -->
    <Teleport to="body">
      <TransitionGroup name="toast" tag="div" class="toast-stack">
        <div v-for="t in toasts" :key="t.id" :class="['toast-item', 'toast-' + t.type]">
          <span class="toast-icon">{{ t.type === 'success' ? '✓' : t.type === 'error' ? '✕' : '!' }}</span>
          <span class="toast-msg">{{ t.msg }}</span>
        </div>
      </TransitionGroup>
    </Teleport>

    <!-- 顶部 -->
    <div class="settings-topbar">
      <button class="glass-btn back-btn" @click="$router.push('/')">
        <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M19 12H5M12 19l-7-7 7-7"/>
        </svg>
        返回主界面
      </button>
      <h1>⚙ 设置</h1>
    </div>

    <div class="settings-container">
      <!-- ====== 1. 个人信息 ====== -->
      <div class="settings-card">
        <div class="card-header">
          <span class="card-icon">👤</span>
          <span class="card-title">个人信息</span>
        </div>
        <div class="card-body">
          <div class="field">
            <label class="field-label">昵称</label>
            <div class="field-row">
              <input class="glass-input" v-model="form.nickname" placeholder="请输入昵称" />
              <button class="glass-btn primary" @click="saveNickname">保存</button>
            </div>
          </div>
          <div class="field">
            <label class="field-label">个人简介</label>
            <textarea class="glass-input textarea" v-model="form.bio" rows="2" placeholder="介绍一下自己..."></textarea>
            <button class="glass-btn primary" style="margin-top:8px" @click="saveBio">保存简介</button>
          </div>
          <div class="field">
            <label class="field-label">头像</label>
            <div class="avatar-row">
              <div class="avatar-ring">
                <img v-if="user?.avatar_url" :src="user.avatar_url" class="avatar-img" />
                <span v-else class="avatar-placeholder">{{ user?.nickname?.[0] || 'U' }}</span>
              </div>
              <label class="glass-btn primary small">
                <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z"/>
                  <path d="M12 11v6M9 14l3-3 3 3"/>
                </svg>
                更换头像
                <input type="file" accept="image/*" @change="handleAvatarUpload" style="display:none" />
              </label>
            </div>
          </div>
        </div>
      </div>

      <!-- ====== 2. 学习偏好 ====== -->
      <div class="settings-card">
        <div class="card-header">
          <span class="card-icon">🎯</span>
          <span class="card-title">学习偏好</span>
          <span class="card-hint">帮助基智提供更精准的学习建议</span>
        </div>
        <div class="card-body prefs-grid">
          <div class="pref-field">
            <label class="field-label">学习阶段</label>
            <select class="glass-input" v-model="form.learning_stage" @change="onStageChange">
              <option value="">未设置</option>
              <option v-for="o in stageOptions" :key="o" :value="o">{{ o }}</option>
            </select>
          </div>
          <div class="pref-field">
            <label class="field-label">年级</label>
            <select class="glass-input" v-model="form.grade">
              <option value="">未设置</option>
              <option v-for="o in gradeOptions" :key="o" :value="o">{{ o }}</option>
            </select>
          </div>
          <div class="pref-field">
            <label class="field-label">专业/方向</label>
            <input class="glass-input" v-model="form.major" placeholder="如：计算机科学" list="major-list" />
            <datalist id="major-list">
              <option v-for="m in majorOptions" :key="m" :value="m" />
            </datalist>
          </div>
          <div class="pref-field">
            <label class="field-label">学习目标</label>
            <select class="glass-input" v-model="form.learning_goal">
              <option value="">未设置</option>
              <option v-for="o in goalOptions" :key="o" :value="o">{{ o }}</option>
            </select>
          </div>
          <div class="pref-field">
            <label class="field-label">题目难度</label>
            <select class="glass-input" v-model="form.difficulty_preference">
              <option value="">未设置</option>
              <option v-for="o in difficultyOptions" :key="o" :value="o">{{ o }}</option>
            </select>
          </div>
          <div class="pref-field">
            <label class="field-label">讲解方式</label>
            <select class="glass-input" v-model="form.learning_style">
              <option value="">未设置</option>
              <option v-for="o in styleOptions" :key="o" :value="o">{{ o }}</option>
            </select>
          </div>
          <div class="pref-field">
            <label class="field-label">每日学习时长</label>
            <select class="glass-input" v-model="form.daily_study_time">
              <option value="">未设置</option>
              <option v-for="o in timeOptions" :key="o" :value="o">{{ o }}</option>
            </select>
          </div>
        </div>
        <div class="card-footer">
          <button class="glass-btn primary" :disabled="savingPrefs" @click="savePreferences">
            {{ savingPrefs ? '保存中...' : '保存学习偏好' }}
          </button>
        </div>
      </div>

      <!-- ====== 3. 外观 ====== -->
      <div class="settings-card">
        <div class="card-header">
          <span class="card-icon">🎨</span>
          <span class="card-title">外观</span>
        </div>
        <div class="card-body">
          <div class="toggle-group">
            <div
              v-for="opt in themeOptions" :key="opt.value"
              class="toggle-card"
              :class="{ active: themeStore.mode === opt.value }"
              @click="themeStore.setMode(opt.value)"
            >
              <span class="toggle-icon">{{ opt.icon }}</span>
              <span class="toggle-label">{{ opt.label }}</span>
              <span class="toggle-check" v-if="themeStore.mode === opt.value">✓</span>
            </div>
          </div>
        </div>
      </div>

      <!-- ====== 4. 隐私 ====== -->
      <div class="settings-card">
        <div class="card-header">
          <span class="card-icon">🔒</span>
          <span class="card-title">隐私</span>
        </div>
        <div class="card-body">
          <div class="toggle-group">
            <div
              v-for="opt in statusOptions" :key="opt.value"
              class="toggle-card"
              :class="{ active: userStatus === opt.value }"
              @click="changeStatus(opt.value)"
            >
              <span class="toggle-icon">{{ opt.icon }}</span>
              <span class="toggle-label">{{ opt.label }}</span>
              <span class="toggle-desc">{{ opt.desc }}</span>
              <span class="toggle-check" v-if="userStatus === opt.value">✓</span>
            </div>
          </div>
        </div>
      </div>

      <!-- ====== 5. 通知设置 ====== -->
      <div class="settings-card">
        <div class="card-header">
          <span class="card-icon">🔔</span>
          <span class="card-title">通知设置</span>
        </div>
        <div class="card-body">
          <div class="notif-grid">
            <div v-for="item in notifItems" :key="item.key" class="notif-row">
              <div class="notif-info">
                <span class="notif-label">{{ item.label }}</span>
                <span class="notif-desc">{{ item.desc }}</span>
              </div>
              <label class="switch">
                <input type="checkbox" v-model="notifSettings[item.key]" @change="saveNotifSettings" />
                <span class="switch-slider"></span>
              </label>
            </div>
          </div>
          <div class="notif-time-row">
            <div class="notif-time-field">
              <label class="field-label">每日推荐时间</label>
              <input type="time" class="glass-input" v-model="notifSettings.daily_rec_time" @change="saveNotifSettings" style="width:160px" />
            </div>
            <div class="notif-time-field">
              <label class="field-label">每日总结时间</label>
              <input type="time" class="glass-input" v-model="notifSettings.daily_summary_time" @change="saveNotifSettings" style="width:160px" />
            </div>
          </div>
        </div>
      </div>

      <!-- ====== 6. 账号安全 ====== -->
      <div class="settings-card">
        <div class="card-header">
          <span class="card-icon">🔐</span>
          <span class="card-title">账号安全</span>
        </div>
        <div class="card-body">
          <!-- 修改密码 -->
          <div class="field">
            <label class="field-label">修改密码</label>
            <div class="pw-fields">
              <input class="glass-input" v-model="pw.old" type="password" placeholder="当前密码" />
              <input class="glass-input" v-model="pw.new1" type="password" placeholder="新密码（至少6位）" />
              <input class="glass-input" v-model="pw.new2" type="password" placeholder="确认新密码" />
            </div>
            <button class="glass-btn warning" style="margin-top:10px" :disabled="changingPw" @click="changePassword">
              {{ changingPw ? '修改中...' : '修改密码' }}
            </button>
          </div>

          <div class="divider"></div>

          <!-- 微信绑定 -->
          <div class="field">
            <label class="field-label">微信绑定</label>
            <div v-if="user?.wechat_openid" class="wechat-bound">
              <i class="fab fa-weixin" style="color:#07c160;font-size:20px"></i>
              <span>已绑定微信</span>
            </div>
            <template v-else>
              <button v-if="!wechat.qrcode" class="glass-btn wechat-btn" :disabled="wechat.loading" @click="startWechatBind">
                <i class="fab fa-weixin"></i> {{ wechat.loading ? '获取中...' : '绑定微信' }}
              </button>
              <div v-if="wechat.qrcode" class="wechat-panel">
                <img :src="wechat.qrcode" class="wechat-qr" alt="微信扫码" />
                <p class="wechat-tip">{{ wechat.status }}</p>
                <button class="glass-btn small" @click="cancelWechatBind">取消</button>
              </div>
            </template>
          </div>
        </div>
      </div>

      <!-- ====== 7. AI 与 API ====== -->
      <div class="settings-card">
        <div class="card-header">
          <img src="/images/xiaoji/xiaoji_idle.png" alt="小基" class="xiaoji-section-icon" />
          <span class="card-title">AI 与 API</span>
        </div>
        <div class="card-body">
          <div class="link-grid">
            <router-link to="/xiaoji/settings" class="link-card">
              <img src="/images/xiaoji/xiaoji_idle.png" alt="小基" class="link-icon-img" />
              <span class="link-label">小基 AI 设置</span>
              <span class="link-desc">AI 助手名称、语音、性格</span>
              <svg class="link-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>
            </router-link>
            <router-link to="/api-center" class="link-card">
              <span class="link-icon">🔑</span>
              <span class="link-label">API 管理中心</span>
              <span class="link-desc">管理第三方 API 密钥</span>
              <svg class="link-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>
            </router-link>
          </div>
        </div>
      </div>

      <!-- 底部间距 -->
      <div style="height:40px"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import { setUser } from '@/utils/storage'
import { updateNickname, updateBio, uploadAvatar } from '@/api/auth'
import { getNotificationSettings, updateNotificationSettings } from '@/api/community'
import { recordAction } from '@/api/career'

const authStore = useAuthStore()
const themeStore = useThemeStore()

const user = computed(() => authStore.user)
const userStatus = ref(authStore.user?.status || 'online')
const savingPrefs = ref(false)
const changingPw = ref(false)

// ===== Form =====
const form = reactive({
  nickname: '',
  bio: '',
  learning_stage: '',
  grade: '',
  major: '',
  learning_goal: '',
  difficulty_preference: '',
  learning_style: '',
  daily_study_time: '',
})

// ===== Password =====
const pw = reactive({ old: '', new1: '', new2: '' })

// ===== Toast =====
const toasts = ref([])
let toastId = 0
function toast(msg, type = 'success') {
  const id = ++toastId
  toasts.value.push({ id, msg, type })
  setTimeout(() => { toasts.value = toasts.value.filter(t => t.id !== id) }, 2800)
}

// ===== 选项 =====
const stageOptions = ['初中', '高中', '大学', '考研', '在职', '其他']
const gradeMap = {
  '初中': ['初一', '初二', '初三'],
  '高中': ['高一', '高二', '高三'],
  '大学': ['大一', '大二', '大三', '大四', '大五'],
  '考研': ['备考中', '已上岸'],
  '在职': ['初级', '中级', '高级'],
  '其他': []
}
const gradeOptions = computed(() => gradeMap[form.learning_stage] || [])
function onStageChange() { form.grade = '' }
const majorOptions = ['计算机科学与技术', '软件工程', '人工智能', '数据科学', '电子信息工程', '通信工程', '自动化', '数学', '物理', '化学', '生物', '医学', '法学', '经济学', '管理学', '会计学', '金融学', '英语', '日语', '汉语言文学', '历史', '哲学', '教育学', '心理学', '机械工程', '土木工程', '建筑学', '环境工程', '材料科学', '其他']
const goalOptions = ['考试备考', '兴趣学习', '补课提升', '考研复习', '工作提升', '其他']
const difficultyOptions = ['基础巩固', '适中练习', '挑战难题']
const styleOptions = ['详细讲解', '精简要点', '举例说明']
const timeOptions = ['30分钟内', '1小时左右', '2小时左右', '2小时以上']

// ===== 主题 =====
const themeOptions = [
  { value: 'light', label: '浅色', icon: '☀️' },
  { value: 'dark', label: '深色', icon: '🌙' },
  { value: 'system', label: '跟随系统', icon: '💻' },
]

// ===== 在线状态 =====
const statusOptions = [
  { value: 'online', label: '在线', icon: '🟢', desc: '对其他用户可见' },
  { value: 'invisible', label: '隐身', icon: '🟣', desc: '不显示在线状态' },
]

async function changeStatus(status) {
  userStatus.value = status
  await authStore.setUserStatus(status)
  recordAction(authStore.user.id, 'change_status')
  toast('状态已更新')
}

// ===== 个人信息保存 =====
async function saveNickname() {
  if (!form.nickname) { toast('请输入昵称', 'error'); return }
  try {
    await updateNickname(authStore.user.id, form.nickname)
    authStore.user.nickname = form.nickname
    setUser(authStore.user)
    recordAction(authStore.user.id, 'update_nickname')
    toast('昵称已更新')
  } catch { toast('更新失败', 'error') }
}

async function saveBio() {
  try {
    await updateBio(authStore.user.id, form.bio)
    authStore.user.bio = form.bio
    setUser(authStore.user)
    recordAction(authStore.user.id, 'update_bio')
    toast('简介已更新')
  } catch { toast('更新失败', 'error') }
}

async function handleAvatarUpload(e) {
  const file = e.target.files[0]
  if (!file) return
  try {
    const result = await uploadAvatar(authStore.user.id, file)
    if (result.success) {
      authStore.user.avatar_url = result.avatar_url
      setUser(authStore.user)
      recordAction(authStore.user.id, 'update_avatar')
      toast('头像已更新')
    }
  } catch { toast('上传失败', 'error') }
  e.target.value = ''
}

// ===== 学习偏好保存 =====
async function savePreferences() {
  savingPrefs.value = true
  try {
    const prefs = {
      learning_stage: form.learning_stage,
      grade: form.grade,
      major: form.major,
      learning_goal: form.learning_goal,
      difficulty_preference: form.difficulty_preference,
      learning_style: form.learning_style,
      daily_study_time: form.daily_study_time,
    }
    const res = await authStore.updatePreferences(prefs)
    if (res.success) {
      recordAction(authStore.user.id, 'update_preferences')
      toast('学习偏好已保存')
    } else {
      toast(res.detail || '保存失败', 'error')
    }
  } catch { toast('保存失败，请检查网络', 'error') }
  finally { savingPrefs.value = false }
}

// ===== 修改密码 =====
async function changePassword() {
  if (!pw.old) { toast('请输入当前密码', 'error'); return }
  if (!pw.new1 || pw.new1.length < 6) { toast('新密码至少6位', 'error'); return }
  if (pw.new1 !== pw.new2) { toast('两次密码不一致', 'error'); return }
  changingPw.value = true
  try {
    const res = await fetch(`${import.meta.env.VITE_BACKEND_URL || 'https://api.jizhi-learn.com'}/auth/update-password?user_id=${authStore.user.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${authStore.token}` },
      body: JSON.stringify({ old_password: pw.old, new_password: pw.new1 })
    })
    const data = await res.json()
    if (data.success) {
      toast('密码修改成功')
      pw.old = ''; pw.new1 = ''; pw.new2 = ''
      recordAction(authStore.user.id, 'change_password')
    } else {
      toast(data.detail || '修改失败', 'error')
    }
  } catch { toast('修改失败，请检查网络', 'error') }
  finally { changingPw.value = false }
}

// ===== 微信绑定 =====
const wechat = reactive({ qrcode: '', status: '', loading: false })
let wechatTimer = null

async function startWechatBind() {
  wechat.loading = true
  const result = await authStore.bindWechat()
  wechat.loading = false
  if (result.success) {
    wechat.qrcode = result.qrcode
    wechat.status = '请用微信扫描二维码'
    let attempts = 0
    wechatTimer = setInterval(async () => {
      attempts++
      if (attempts > 150) {
        clearInterval(wechatTimer); wechatTimer = null
        wechat.status = '已过期，请重新获取'
        setTimeout(() => { wechat.qrcode = '' }, 2000)
        return
      }
      const pr = await authStore.bindWechatPoll(result.pollToken)
      if (pr.success) {
        clearInterval(wechatTimer); wechatTimer = null
        wechat.status = '绑定成功！'
        if (authStore.user) authStore.user.wechat_openid = 'bound'
        toast('微信绑定成功！')
        recordAction(authStore.user.id, 'bind_wechat')
        setTimeout(() => { wechat.qrcode = '' }, 1500)
      } else if (pr.message) {
        clearInterval(wechatTimer); wechatTimer = null
        wechat.status = pr.message
        setTimeout(() => { wechat.qrcode = '' }, 2000)
      }
    }, 2000)
  } else {
    toast(result.message || '获取绑定二维码失败', 'error')
  }
}

function cancelWechatBind() {
  if (wechatTimer) { clearInterval(wechatTimer); wechatTimer = null }
  wechat.qrcode = ''
  wechat.status = ''
}

// ===== 通知设置 =====
const notifSettings = reactive({
  chat_enabled: true,
  social_enabled: true,
  learning_enabled: true,
  plan_reminder_enabled: true,
  evaluation_enabled: true,
  daily_rec_enabled: true,
  daily_summary_enabled: true,
  system_enabled: true,
  daily_rec_time: '08:00',
  daily_summary_time: '07:00',
})

const notifItems = [
  { key: 'chat_enabled', label: '对话通知', desc: 'AI 对话完成、新消息提醒' },
  { key: 'social_enabled', label: '社交通知', desc: '好友请求、评论、点赞' },
  { key: 'learning_enabled', label: '学习提醒', desc: '每日任务、学习进度提醒' },
  { key: 'plan_reminder_enabled', label: '计划提醒', desc: '学习计划到期提醒' },
  { key: 'evaluation_enabled', label: '评估通知', desc: '诊断结果、学情报告生成' },
  { key: 'daily_rec_enabled', label: '每日推荐', desc: '每日个性化题目推荐' },
  { key: 'daily_summary_enabled', label: '每日总结', desc: '学习数据日报' },
  { key: 'system_enabled', label: '系统通知', desc: '公告、维护、活动通知' },
]

async function loadNotifSettings() {
  if (!authStore.user?.id) return
  try {
    const data = await getNotificationSettings(authStore.user.id)
    if (data && data.settings) {
      Object.assign(notifSettings, data.settings)
    }
  } catch { /* 使用默认值 */ }
}

let notifSaveTimer = null
function saveNotifSettings() {
  clearTimeout(notifSaveTimer)
  notifSaveTimer = setTimeout(async () => {
    try {
      await updateNotificationSettings({ data: { ...notifSettings }, user_id: authStore.user.id })
    } catch { /* 静默失败 */ }
  }, 400)
}

// ===== 初始化 =====
onMounted(() => {
  const u = authStore.user
  if (u) {
    form.nickname = u.nickname || ''
    form.bio = u.bio || ''
    form.learning_stage = u.learning_stage || ''
    form.grade = u.grade || ''
    form.major = u.major || ''
    form.learning_goal = u.learning_goal || ''
    form.difficulty_preference = u.difficulty_preference || ''
    form.learning_style = u.learning_style || ''
    form.daily_study_time = u.daily_study_time || ''
    userStatus.value = u.status || 'online'
  }
  loadNotifSettings()
})

onUnmounted(() => {
  if (wechatTimer) clearInterval(wechatTimer)
  if (notifSaveTimer) clearTimeout(notifSaveTimer)
})
</script>

<style scoped>
.settings-page {
  min-height: 100vh;
  padding: 20px 28px;
  background-size: cover;
  background-position: center;
  background-attachment: fixed;
}
[data-theme="light"] .settings-page { background-image: url('/assets/bg/profile_bg.jpg'); }
[data-theme="dark"]  .settings-page { background-image: url('/assets/bg/profile_bl.jpg'); }

.settings-topbar {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 24px;
}
.settings-topbar h1 {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.settings-container {
  max-width: 760px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* ====== 卡片 ====== */
.settings-card {
  border-radius: 16px;
  background: rgba(255,255,255,0.04);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.06);
  transition: all 0.3s ease;
  overflow: hidden;
}
.settings-card:hover {
  border-color: rgba(255,255,255,0.10);
}
[data-theme="dark"] .settings-card {
  background: rgba(0,0,0,0.25);
  border-color: rgba(255,255,255,0.04);
}
[data-theme="dark"] .settings-card:hover {
  border-color: rgba(255,255,255,0.08);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 18px 24px 0;
}
.card-icon { font-size: 18px; }
.card-title { font-size: 16px; font-weight: 600; color: var(--text-primary); }
.card-hint { font-size: 12px; color: var(--text-muted); margin-left: auto; }
.card-body { padding: 16px 24px 20px; }
.card-footer { padding: 0 24px 18px; }

/* ====== 按钮 ====== */
.glass-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 18px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.04);
  cursor: pointer;
  transition: all 0.25s ease;
  font-family: inherit;
}
.glass-btn:hover {
  background: rgba(255,255,255,0.08);
  border-color: rgba(255,255,255,0.10);
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(0,0,0,0.06);
}
.glass-btn:active { transform: scale(0.97); }
.glass-btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none !important; box-shadow: none !important; }
.glass-btn .icon { width: 18px; height: 18px; }
.glass-btn.small { padding: 4px 14px; font-size: 13px; }
.back-btn .icon { width: 20px; height: 20px; }

.glass-btn.primary {
  color: #409EFF;
  background: rgba(64,158,255,0.08);
  border-color: rgba(64,158,255,0.10);
}
.glass-btn.primary:hover {
  background: rgba(64,158,255,0.15);
  border-color: rgba(64,158,255,0.22);
  box-shadow: 0 4px 20px rgba(64,158,255,0.12);
}
.glass-btn.warning {
  color: #F59E0B;
  background: rgba(245,158,11,0.08);
  border-color: rgba(245,158,11,0.10);
}
.glass-btn.warning:hover {
  background: rgba(245,158,11,0.14);
  border-color: rgba(245,158,11,0.20);
}

/* ====== 表单 ====== */
.field { margin-bottom: 16px; }
.field:last-child { margin-bottom: 0; }
.field-label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 8px;
}
.field-row { display: flex; gap: 10px; }
.field-row .glass-input { flex: 1; }

.glass-input {
  width: 100%;
  padding: 10px 14px;
  border-radius: 10px;
  font-size: 14px;
  color: var(--text-primary);
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.04);
  transition: all 0.25s ease;
  outline: none;
  font-family: inherit;
  box-sizing: border-box;
}
.glass-input::placeholder { color: var(--text-muted); opacity: 0.4; }
.glass-input:focus {
  border-color: rgba(64,158,255,0.20);
  background: rgba(255,255,255,0.04);
  box-shadow: 0 0 0 4px rgba(64,158,255,0.04);
}
.glass-input.textarea { resize: vertical; min-height: 60px; }
select.glass-input { cursor: pointer; appearance: none; }

.pw-fields { display: flex; flex-direction: column; gap: 10px; }

/* ====== 头像 ====== */
.avatar-row { display: flex; align-items: center; gap: 16px; }
.avatar-ring {
  width: 64px; height: 64px;
  border-radius: 50%;
  border: 2px solid var(--border-color);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255,255,255,0.04);
  flex-shrink: 0;
}
.avatar-img { width: 100%; height: 100%; object-fit: cover; }
.avatar-placeholder { font-size: 24px; font-weight: 700; color: var(--text-primary); }

/* ====== 学习偏好 ====== */
.prefs-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}
.pref-field { display: flex; flex-direction: column; gap: 6px; }

/* ====== 外观 & 隐私 ====== */
.toggle-group {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 10px;
}
.toggle-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 16px 12px;
  border-radius: 12px;
  background: rgba(255,255,255,0.02);
  border: 2px solid rgba(255,255,255,0.04);
  cursor: pointer;
  transition: all 0.25s ease;
  position: relative;
}
.toggle-card:hover {
  background: rgba(255,255,255,0.05);
  border-color: rgba(255,255,255,0.10);
  transform: translateY(-2px);
}
.toggle-card.active {
  background: rgba(64,158,255,0.08);
  border-color: rgba(64,158,255,0.25);
}
.toggle-icon { font-size: 24px; }
.toggle-label { font-size: 14px; font-weight: 600; color: var(--text-primary); }
.toggle-desc { font-size: 11px; color: var(--text-muted); text-align: center; }
.toggle-check {
  position: absolute; top: 8px; right: 10px;
  width: 20px; height: 20px; border-radius: 50%;
  background: #409EFF; color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 700;
}

/* ====== 通知设置 ====== */
.notif-grid { display: flex; flex-direction: column; gap: 4px; }
.notif-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  border-radius: 10px;
  transition: background 0.2s;
}
.notif-row:hover { background: rgba(255,255,255,0.03); }
.notif-info { display: flex; flex-direction: column; gap: 2px; }
.notif-label { font-size: 14px; color: var(--text-primary); font-weight: 500; }
.notif-desc { font-size: 12px; color: var(--text-muted); }
.notif-time-row { display: flex; gap: 24px; margin-top: 16px; padding-top: 16px; border-top: 1px solid rgba(255,255,255,0.04); }
.notif-time-field { display: flex; flex-direction: column; gap: 6px; }

/* Switch */
.switch { position: relative; display: inline-block; width: 44px; height: 24px; flex-shrink: 0; }
.switch input { opacity: 0; width: 0; height: 0; }
.switch-slider {
  position: absolute; cursor: pointer;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(255,255,255,0.10);
  border-radius: 24px;
  transition: all 0.3s ease;
}
.switch-slider::before {
  content: ""; position: absolute;
  height: 18px; width: 18px;
  left: 3px; bottom: 3px;
  background: #fff;
  border-radius: 50%;
  transition: all 0.3s ease;
}
.switch input:checked + .switch-slider { background: #409EFF; }
.switch input:checked + .switch-slider::before { transform: translateX(20px); }

/* ====== 分隔线 ====== */
.divider { height: 1px; background: rgba(255,255,255,0.05); margin: 18px 0; }

/* ====== 微信 ====== */
.wechat-bound { display: flex; align-items: center; gap: 10px; padding: 10px 0; font-size: 15px; color: var(--text-primary); }
.wechat-btn {
  display: inline-flex; align-items: center; gap: 8px;
  background: linear-gradient(135deg, #07c160, #06ad56) !important;
  color: #fff !important; border: none !important;
}
.wechat-btn:hover { box-shadow: 0 4px 16px rgba(7,193,96,0.3); }
.wechat-panel {
  display: flex; flex-direction: column; align-items: center; gap: 12px;
  padding: 16px; background: #fff; border-radius: 14px; border: 2px solid #07c160;
}
.wechat-qr { width: 180px; height: 180px; border-radius: 8px; }
.wechat-tip { font-size: 14px; color: #333; margin: 0; font-weight: 500; }

/* ====== AI 链接 ====== */
.link-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 10px; }
.link-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 12px;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.04);
  text-decoration: none;
  cursor: pointer;
  transition: all 0.25s ease;
}
.link-card:hover {
  background: rgba(255,255,255,0.06);
  border-color: rgba(64,158,255,0.15);
  transform: translateY(-2px);
}
.link-icon { font-size: 22px; flex-shrink: 0; }
.link-label { font-size: 14px; font-weight: 600; color: var(--text-primary); }
.link-desc { font-size: 12px; color: var(--text-muted); flex: 1; }
.link-arrow { width: 18px; height: 18px; color: var(--text-muted); flex-shrink: 0; }

/* 小基图标 */
.xiaoji-section-icon {
  width: 24px;
  height: 24px;
  object-fit: contain;
  border-radius: 6px;
}
.link-icon-img {
  width: 28px;
  height: 28px;
  object-fit: contain;
  border-radius: 7px;
  flex-shrink: 0;
}

/* ====== Toast ====== */
.toast-stack {
  position: fixed; top: 24px; right: 24px; z-index: 9999;
  display: flex; flex-direction: column; gap: 8px;
  pointer-events: none;
}
.toast-item {
  display: flex; align-items: center; gap: 10px;
  padding: 12px 18px; border-radius: 12px;
  background: rgba(20,20,40,0.92);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255,255,255,0.08);
  box-shadow: 0 8px 32px rgba(0,0,0,0.2);
  pointer-events: auto;
  font-size: 14px;
  color: var(--text-primary);
}
.toast-success .toast-icon { color: #67c23a; font-weight: 700; }
.toast-error .toast-icon { color: #f56c6c; font-weight: 700; }
.toast-warning .toast-icon { color: #e6a23c; font-weight: 700; }
.toast-enter-active { transition: all 0.3s ease-out; }
.toast-leave-active { transition: all 0.2s ease-in; }
.toast-enter-from { opacity: 0; transform: translateX(40px); }
.toast-leave-to { opacity: 0; transform: translateX(40px); }

@media (max-width: 600px) {
  .settings-page { padding: 12px 16px; }
  .prefs-grid { grid-template-columns: 1fr; }
  .toggle-group { grid-template-columns: repeat(2, 1fr); }
  .notif-time-row { flex-direction: column; }
  .link-grid { grid-template-columns: 1fr; }
}
</style>
