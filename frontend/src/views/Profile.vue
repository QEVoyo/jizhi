<template>
  <div class="profile-page">
    <!-- 顶部返回 -->
    <div class="profile-topbar">
      <button class="glass-btn back-btn" @click="goHome">
        <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M19 12H5M12 19l-7-7 7-7"/>
        </svg>
        返回主界面
      </button>
      <h1>个人中心</h1>
    </div>

    <div class="profile-container">
      <!-- ===== 头像 ===== -->
      <div class="profile-card avatar-section">
        <div class="avatar-wrapper">
          <div class="avatar-ring">
            <img v-if="user?.avatar_url" :src="user.avatar_url" class="avatar-img" />
            <span v-else class="avatar-placeholder">{{ user?.nickname?.[0] || 'U' }}</span>
          </div>
          <label class="glass-btn primary small upload-btn">
            <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z"/>
              <path d="M12 11v6M9 14l3-3 3 3"/>
            </svg>
            更换头像
            <input type="file" accept="image/*" @change="handleAvatarUpload" style="display:none;" />
          </label>
        </div>
        <div class="user-basic">
          <div class="basic-row">
            <span class="label">账号</span>
            <span class="value">{{ user?.user_account || '未设置' }}</span>
          </div>
          <div class="basic-row">
            <span class="label">邮箱</span>
            <span class="value">{{ user?.email || '未设置' }}</span>
          </div>
        </div>
      </div>

      <!-- ===== 昵称 ===== -->
      <div class="profile-card">
        <div class="field-label">昵称</div>
        <div class="field-row">
          <input class="glass-input" v-model="nickname" placeholder="请输入昵称" />
          <button class="glass-btn primary" @click="handleUpdateNickname">保存</button>
        </div>
      </div>

      <!-- ===== 简介 ===== -->
      <div class="profile-card">
        <div class="field-label">个人简介</div>
        <textarea class="glass-input textarea" v-model="bio" rows="3" placeholder="介绍一下自己..."></textarea>
        <button class="glass-btn primary" style="margin-top:8px;" @click="handleUpdateBio">保存简介</button>
      </div>

      <!-- ===== 学习信息 ===== -->
      <div class="profile-card">
        <div class="field-label">学习信息</div>

        <div class="form-group">
          <label>学习阶段</label>
          <select class="glass-input" v-model="learningStage" @change="onStageChange">
            <option value="小学">小学</option>
            <option value="初中">初中</option>
            <option value="高中">高中</option>
            <option value="大学">大学</option>
            <option value="研究生">研究生</option>
            <option value="职场">职场</option>
          </select>
        </div>

        <div class="form-group">
          <label>年级</label>
          <select class="glass-input" v-model="grade">
            <option v-for="g in gradeOptions" :key="g" :value="g">{{ g }}</option>
          </select>
        </div>

        <div class="form-group">
          <label>专业 / 方向</label>
          <div class="search-wrapper">
            <input
              class="glass-input"
              v-model="majorInput"
              @input="onMajorInput"
              @focus="showSuggestions = true"
              @blur="handleBlur"
              placeholder="输入专业或方向名称"
            />
            <div v-if="showSuggestions && filteredMajors.length > 0" class="suggestions-dropdown">
              <div
                v-for="item in filteredMajors"
                :key="item"
                class="suggestion-item"
                @mousedown.prevent="selectMajor(item)"
              >
                <span class="suggestion-text">{{ item }}</span>
                <span class="suggestion-hint">点击填入</span>
              </div>
              <div v-if="filteredMajors.length === 0 && majorInput.length > 0" class="suggestion-item ai-suggest">
                <span class="suggestion-text">💡 未找到匹配，将作为自定义方向</span>
              </div>
            </div>
          </div>
          <span class="hint-text">输入关键词搜索，支持自定义输入</span>
        </div>

        <button class="glass-btn primary" style="margin-top:12px;" @click="handleUpdateLearningInfo" :disabled="saving">
          {{ saving ? '保存中...' : '保存学习信息' }}
        </button>
      </div>

      <!-- ===== 修改密码 ===== -->
      <div class="profile-card">
        <div class="field-label">修改密码</div>
        <input class="glass-input" v-model="oldPassword" type="password" placeholder="当前密码" style="margin-bottom:10px;" />
        <input class="glass-input" v-model="newPassword" type="password" placeholder="新密码（至少6位）" style="margin-bottom:10px;" />
        <input class="glass-input" v-model="confirmPassword" type="password" placeholder="确认新密码" />
        <button class="glass-btn warning" style="margin-top:10px;" @click="handleUpdatePassword">修改密码</button>
      </div>

      <!-- ===== 退出登录 ===== -->
      <button class="glass-btn danger logout-btn" @click="handleLogout">
        退出登录
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { setUser } from '@/utils/storage'
import { updateNickname as apiUpdateNickname, updateBio as apiUpdateBio, uploadAvatar } from '@/api/auth'
import { recordAction } from '@/api/career'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()

const user = computed(() => authStore.user)
const nickname = ref('')
const bio = ref('')
const oldPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const saving = ref(false)

// ===== 学习信息 =====
const learningStage = ref('大学')
const grade = ref('大一')
const majorInput = ref('')
const showSuggestions = ref(false)

// ===== 专业词库 =====
const majorDatabase = [
  '人工智能', '机器学习', '深度学习', '自然语言处理', '计算机视觉',
  '计算机科学', '软件工程', '数据科学', '大数据', '网络安全',
  '网络工程', '物联网', '嵌入式系统', '云计算', '区块链',
  '数学', '应用数学', '统计学', '运筹学',
  '物理学', '应用物理', '量子物理', '天体物理',
  '化学', '应用化学', '有机化学', '无机化学', '物理化学',
  '生物学', '分子生物学', '生物技术', '生物信息学', '生物医学',
  '英语', '翻译', '商务英语', '英语教育',
  '汉语言文学', '历史学', '哲学', '社会学', '心理学',
  '法学', '经济学', '金融学', '会计学', '财务管理',
  '工商管理', '市场营销', '人力资源管理', '电子商务',
  '医学', '临床医学', '药学', '护理学', '口腔医学',
  '建筑学', '土木工程', '机械工程', '电子工程', '电气工程',
  '艺术设计', '视觉传达', '环境设计', '产品设计', '服装设计',
  '音乐', '音乐表演', '音乐教育', '美术', '绘画', '雕塑', '舞蹈',
  '新闻传播', '广播电视', '广告学', '数字媒体',
  '教育学', '学前教育', '特殊教育', '体育教育',
  '地理', '地理信息科学', '环境科学', '生态学',
  '海洋科学', '大气科学', '地质学',
  '农学', '植物保护', '动物科学', '林学', '水产养殖'
]

const filteredMajors = ref([])

const stageGradeMap = {
  '小学': ['一年级', '二年级', '三年级', '四年级', '五年级', '六年级'],
  '初中': ['初一', '初二', '初三'],
  '高中': ['高一', '高二', '高三'],
  '大学': ['大一', '大二', '大三', '大四'],
  '研究生': ['研一', '研二', '研三'],
  '职场': ['初级', '中级', '高级']
}

const gradeOptions = ref(['大一', '大二', '大三', '大四'])

function onStageChange() {
  gradeOptions.value = stageGradeMap[learningStage.value] || ['大一', '大二', '大三', '大四']
  grade.value = gradeOptions.value[0] || ''
}

function onMajorInput() {
  const input = majorInput.value.trim().toLowerCase()
  if (input.length === 0) {
    filteredMajors.value = []
    showSuggestions.value = false
    return
  }
  const matched = majorDatabase
    .filter(m => m.toLowerCase().includes(input))
    .slice(0, 10)
  filteredMajors.value = matched
  showSuggestions.value = matched.length > 0
}

function selectMajor(item) {
  majorInput.value = item
  showSuggestions.value = false
}

function handleBlur() {
  setTimeout(() => {
    showSuggestions.value = false
  }, 200)
}

function loadLearningInfo() {
  const u = authStore.user
  if (u) {
    learningStage.value = u.learning_stage || '大学'
    grade.value = u.grade || '大一'
    majorInput.value = u.major || ''
    onStageChange()
  }
}

// ===== 保存学习信息 =====
async function handleUpdateLearningInfo() {
  if (!learningStage.value) { ElMessage.warning('请选择学习阶段'); return }
  if (!grade.value) { ElMessage.warning('请选择年级'); return }
  if (!majorInput.value.trim()) { ElMessage.warning('请输入专业/方向'); return }

  saving.value = true
  try {
    const response = await fetch(`${import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'}/auth/update-learning-info`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authStore.token}`
      },
      body: JSON.stringify({
        user_id: authStore.user.id,
        learning_stage: learningStage.value,
        grade: grade.value,
        major: majorInput.value.trim()
      })
    })
    const result = await response.json()
    if (result.success) {
      // ✅ 更新 authStore
      authStore.user.learning_stage = learningStage.value
      authStore.user.grade = grade.value
      authStore.user.major = majorInput.value.trim()
      // ✅ 写入 localStorage，防止刷新丢失
      setUser(authStore.user)
      ElMessage.success('学习信息已保存')
    } else {
      ElMessage.error(result.detail || '保存失败')
    }
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

// ===== 头像上传 =====
async function handleAvatarUpload(event) {
  const file = event.target.files[0]
  if (!file) return
  try {
    const result = await uploadAvatar(authStore.user.id, file)
    if (result.success) {
      authStore.user.avatar_url = result.avatar_url
      setUser(authStore.user)
      await recordAction(authStore.user.id, 'update_avatar')
      ElMessage.success('头像上传成功')
    }
  } catch (error) {
    ElMessage.error('上传失败')
  }
  event.target.value = ''
}

// ===== 更新昵称 =====
async function handleUpdateNickname() {
  if (!nickname.value) { ElMessage.warning('请输入昵称'); return }
  try {
    await apiUpdateNickname(authStore.user.id, nickname.value)
    authStore.user.nickname = nickname.value
    setUser(authStore.user)
    await recordAction(authStore.user.id, 'update_nickname')
    ElMessage.success('昵称更新成功')
  } catch (error) {
    ElMessage.error('更新失败')
  }
}

// ===== 更新简介 =====
async function handleUpdateBio() {
  try {
    await apiUpdateBio(authStore.user.id, bio.value)
    authStore.user.bio = bio.value
    setUser(authStore.user)
    await recordAction(authStore.user.id, 'update_bio')
    ElMessage.success('简介更新成功')
  } catch (error) {
    ElMessage.error('更新失败')
  }
}

// ===== 修改密码 =====
async function handleUpdatePassword() {
  if (!oldPassword.value) { ElMessage.warning('请输入当前密码'); return }
  if (!newPassword.value || newPassword.value.length < 6) { ElMessage.warning('新密码至少6位'); return }
  if (newPassword.value !== confirmPassword.value) { ElMessage.warning('两次密码不一致'); return }
  try {
    const response = await fetch(`${import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'}/auth/update-password?user_id=${authStore.user.id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authStore.token}`
      },
      body: JSON.stringify({
        old_password: oldPassword.value,
        new_password: newPassword.value
      })
    })
    const result = await response.json()
    if (result.success) {
      ElMessage.success('密码修改成功')
      oldPassword.value = ''
      newPassword.value = ''
      confirmPassword.value = ''
    } else {
      ElMessage.error(result.detail || '修改失败')
    }
  } catch (error) {
    ElMessage.error('修改失败，请检查网络')
  }
}

// ===== 退出登录 =====
function handleLogout() {
  ElMessageBox.confirm('确定要退出登录吗？', '确认退出')
    .then(async () => {
      await authStore.logout()
      ElMessage.success('已退出')
      router.push('/login')
    })
    .catch(() => {})
}

function goHome() {
  router.push('/')
}

onMounted(() => {
  nickname.value = user.value?.nickname || ''
  bio.value = user.value?.bio || ''
  loadLearningInfo()
})
</script>

<style scoped>
.profile-page {
  min-height: 100vh;
  padding: 20px 28px;
  background-size: cover;
  background-position: center;
  background-attachment: fixed;
}
[data-theme="light"] .profile-page {
  background-image: url('/assets/bg/profile_bg.jpg');
}
[data-theme="dark"] .profile-page {
  background-image: url('/assets/bg/profile_bl.jpg');
}

.profile-topbar {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 24px;
}
.profile-topbar h1 {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.profile-container {
  max-width: 700px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.profile-card {
  padding: 20px 24px;
  border-radius: 16px;
  background: rgba(255,255,255,0.04);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.06);
  box-shadow: 0 4px 24px rgba(0,0,0,0.04);
}
[data-theme="dark"] .profile-card {
  background: rgba(0,0,0,0.25);
  border-color: rgba(255,255,255,0.04);
}

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
  transition: all 0.3s ease;
}
.glass-btn:hover {
  background: rgba(255,255,255,0.08);
  border-color: rgba(255,255,255,0.10);
  transform: translateY(-2px);
}
.glass-btn:active { transform: scale(0.97); }
.glass-btn.primary {
  color: #409EFF;
  background: rgba(64,158,255,0.08);
  border-color: rgba(64,158,255,0.10);
}
.glass-btn.primary:hover {
  background: rgba(64,158,255,0.14);
  border-color: rgba(64,158,255,0.20);
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
.glass-btn.danger {
  color: #f56c6c;
  background: rgba(245,108,108,0.06);
  border-color: rgba(245,108,108,0.06);
}
.glass-btn.danger:hover {
  background: rgba(245,108,108,0.12);
  border-color: rgba(245,108,108,0.12);
}
.glass-btn .icon { width: 18px; height: 18px; }
.glass-btn.small { padding: 4px 14px; font-size: 13px; }
.back-btn .icon { width: 20px; height: 20px; }
.glass-btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none !important; }

.avatar-section {
  display: flex;
  align-items: center;
  gap: 32px;
  flex-wrap: wrap;
}
.avatar-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}
.avatar-ring {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  border: 3px solid var(--border-color);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255,255,255,0.04);
}
.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.avatar-placeholder {
  font-size: 40px;
  font-weight: 700;
  color: var(--text-primary);
}
.upload-btn {
  cursor: pointer;
}

.user-basic {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.basic-row {
  display: flex;
  gap: 16px;
  padding: 6px 12px;
  border-radius: 8px;
  background: rgba(128,128,128,0.04);
}
.basic-row .label {
  color: var(--text-muted);
  font-size: 13px;
  min-width: 60px;
}
.basic-row .value {
  color: var(--text-primary);
  font-size: 13px;
  font-weight: 500;
}

.field-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 8px;
}
.field-row {
  display: flex;
  gap: 10px;
}
.field-row .glass-input { flex: 1; }

.glass-input {
  width: 100%;
  padding: 10px 14px;
  border-radius: 10px;
  font-size: 14px;
  color: var(--text-primary);
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.04);
  transition: all 0.3s ease;
  outline: none;
  font-family: inherit;
}
.glass-input::placeholder { color: var(--text-muted); opacity: 0.4; }
.glass-input:focus {
  border-color: rgba(64,158,255,0.15);
  background: rgba(255,255,255,0.04);
  box-shadow: 0 0 0 4px rgba(64,158,255,0.04);
}
.glass-input.textarea { resize: vertical; min-height: 80px; }
select.glass-input { cursor: pointer; appearance: none; }
select.glass-input option { background: #1a1a2e; color: #fff; }

.form-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 12px;
}
.form-group label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
}
.search-wrapper {
  position: relative;
}
.suggestions-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  max-height: 200px;
  overflow-y: auto;
  background: rgba(20,20,40,0.95);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 10px;
  z-index: 100;
  box-shadow: 0 8px 32px rgba(0,0,0,0.2);
}
.suggestion-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 14px;
  cursor: pointer;
  transition: all 0.2s ease;
  border-bottom: 1px solid rgba(255,255,255,0.02);
}
.suggestion-item:hover {
  background: rgba(64,158,255,0.06);
}
.suggestion-item:last-child { border-bottom: none; }
.suggestion-text { color: var(--text-primary); font-size: 14px; }
.suggestion-hint { color: var(--text-muted); font-size: 11px; }
.suggestion-item.ai-suggest .suggestion-text { color: var(--text-muted); font-style: italic; }
.hint-text { font-size: 11px; color: var(--text-muted); margin-top: 2px; }

.logout-btn {
  width: 100%;
  margin-top: 4px;
  justify-content: center;
  border-color: rgba(245,108,108,0.2) !important;
}

@media (max-width: 600px) {
  .profile-page { padding: 12px 16px; }
  .profile-card { padding: 16px; }
  .avatar-section { flex-direction: column; align-items: center; text-align: center; }
  .field-row { flex-direction: column; }
  .profile-topbar { flex-wrap: wrap; }
}
</style>