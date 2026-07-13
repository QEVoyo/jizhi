<template>
  <div class="profile-page">
    <!-- 顶部返回 -->
    <div class="profile-topbar">
      <el-button text @click="goHome">
        <i class="fas fa-arrow-left"></i> 返回主界面
      </el-button>
      <h1>👤 个人中心</h1>
    </div>

    <div class="profile-container">
      <!-- ===== 头像 + 基本信息 ===== -->
      <div class="profile-card avatar-section">
        <div class="avatar-wrapper">
          <el-avatar :size="100" :src="user?.avatar_url || ''">
            {{ user?.nickname?.[0] || 'U' }}
          </el-avatar>
          <el-upload
            :show-file-list="false"
            :before-upload="handleAvatarUpload"
            accept="image/*"
          >
            <el-button size="small" type="primary">
              <i class="fas fa-camera"></i> 更换头像
            </el-button>
          </el-upload>
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
        <div class="field-label"><i class="fas fa-user"></i> 昵称</div>
        <div class="field-row">
          <el-input v-model="nickname" placeholder="请输入昵称" size="large" />
          <el-button type="primary" @click="handleUpdateNickname">保存</el-button>
        </div>
      </div>

      <!-- ===== 简介 ===== -->
      <div class="profile-card">
        <div class="field-label"><i class="fas fa-edit"></i> 个人简介</div>
        <el-input
          v-model="bio"
          type="textarea"
          :rows="3"
          placeholder="介绍一下自己..."
        />
        <el-button type="primary" style="margin-top:8px;" @click="handleUpdateBio">保存简介</el-button>
      </div>

      <!-- ===== 修改密码 ===== -->
      <div class="profile-card">
        <div class="field-label"><i class="fas fa-lock"></i> 修改密码</div>
        <el-input
          v-model="oldPassword"
          type="password"
          placeholder="当前密码"
          size="large"
          show-password
          style="margin-bottom:10px;"
        />
        <el-input
          v-model="newPassword"
          type="password"
          placeholder="新密码（至少6位）"
          size="large"
          show-password
          style="margin-bottom:10px;"
        />
        <el-input
          v-model="confirmPassword"
          type="password"
          placeholder="确认新密码"
          size="large"
          show-password
        />
        <el-button type="warning" style="margin-top:10px;" @click="handleUpdatePassword">修改密码</el-button>
      </div>

      <el-divider />

      <!-- ===== 个人画像 ===== -->
      <div class="profile-card">
        <div class="field-label"><i class="fas fa-chart-pie"></i> 个人画像</div>
        <div v-if="loadingPortrait" class="loading-text">加载中...</div>
        <div v-else class="portrait-grid">
          <div v-for="item in portraitData" :key="item.label" class="portrait-item">
            <span class="portrait-label">{{ item.label }}</span>
            <el-progress
              :percentage="item.value"
              :color="item.value >= 70 ? '#6BCB77' : item.value >= 40 ? '#FFB74D' : '#FF6B6B'"
              :stroke-width="8"
            />
          </div>
        </div>
      </div>

      <!-- ===== 学习建议 ===== -->
      <div class="profile-card">
        <div class="field-label"><i class="fas fa-lightbulb"></i> 学习建议</div>
        <div v-if="learningAdvice" class="advice-text">{{ learningAdvice }}</div>
        <div v-else class="advice-placeholder">完成更多练习，AI 将为你生成个性化建议</div>
        <el-button type="primary" size="small" style="margin-top:8px;" :loading="generatingAdvice" @click="generateAdvice">
          <i class="fas fa-sync"></i> 生成建议
        </el-button>
      </div>

      <!-- ===== 退出登录 ===== -->
      <el-button type="danger" size="large" @click="handleLogout" class="logout-btn">
        <i class="fas fa-sign-out-alt"></i> 退出登录
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { updateNickname as apiUpdateNickname, updateBio as apiUpdateBio, uploadAvatar } from '@/api/auth'
import { getMastery } from '@/api/questions'
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
const learningAdvice = ref('')
const generatingAdvice = ref(false)
const loadingPortrait = ref(false)

// ===== 画像数据 =====
const portraitData = ref([])
const portraitLabels = ['知识基础', '认知风格', '易错点偏好', '学习目标', '学习进度', '兴趣领域']

// ===== 加载画像 =====
async function loadPortrait() {
  loadingPortrait.value = true
  try {
    const data = await getMastery(authStore.user.id)
    if (data && data.length > 0) {
      const mapped = data.slice(0, 6).map((item, index) => ({
        label: item.topic || portraitLabels[index] || '维度',
        value: item.mastery_score || 0
      }))
      while (mapped.length < 6) {
        mapped.push({
          label: portraitLabels[mapped.length] || '维度',
          value: 0
        })
      }
      portraitData.value = mapped
    } else {
      portraitData.value = portraitLabels.map(label => ({
        label,
        value: 0
      }))
    }
  } catch (error) {
    console.error('加载画像失败', error)
    portraitData.value = portraitLabels.map(label => ({
      label,
      value: 0
    }))
  } finally {
    loadingPortrait.value = false
  }
}

// ===== 头像上传 =====
async function handleAvatarUpload(file) {
  try {
    const result = await uploadAvatar(authStore.user.id, file)
    if (result.success) {
      authStore.user.avatar_url = result.avatar_url
      await recordAction(authStore.user.id, 'update_avatar')
      ElMessage.success('头像上传成功')
    }
  } catch (error) {
    ElMessage.error('上传失败')
  }
  return false
}

// ===== 更新昵称 =====
async function handleUpdateNickname() {
  if (!nickname.value) {
    ElMessage.warning('请输入昵称')
    return
  }
  try {
    await apiUpdateNickname(authStore.user.id, nickname.value)
    authStore.user.nickname = nickname.value
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
    await recordAction(authStore.user.id, 'update_bio')
    ElMessage.success('简介更新成功')
  } catch (error) {
    ElMessage.error('更新失败')
  }
}

// ===== 修改密码 =====
async function handleUpdatePassword() {
  if (!oldPassword.value) {
    ElMessage.warning('请输入当前密码')
    return
  }
  if (!newPassword.value || newPassword.value.length < 6) {
    ElMessage.warning('新密码至少6位')
    return
  }
  if (newPassword.value !== confirmPassword.value) {
    ElMessage.warning('两次密码不一致')
    return
  }
  try {
    const response = await fetch(`${import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'}/auth/update-password`, {
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

// ===== 生成学习建议 =====
async function generateAdvice() {
  generatingAdvice.value = true
  try {
    const response = await fetch(`${import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'}/chat/advice`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authStore.token}`
      },
      body: JSON.stringify({
        user_id: authStore.user.id
      })
    })
    const result = await response.json()
    if (result.advice) {
      learningAdvice.value = result.advice
    } else {
      ElMessage.warning('暂时无法生成建议，请先完成更多练习')
    }
  } catch (error) {
    ElMessage.error('生成建议失败')
  } finally {
    generatingAdvice.value = false
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

// ===== 返回主界面 =====
function goHome() {
  router.push('/')
}

// ===== 初始化 =====
onMounted(() => {
  nickname.value = user.value?.nickname || ''
  bio.value = user.value?.bio || ''
  loadPortrait()
})
</script>

<style scoped>
.profile-page {
  min-height: 100vh;
  padding: 20px 28px;
}

/* ===== 顶部 ===== */
.profile-topbar {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 24px;
}
.profile-topbar h1 {
  font-size: 24px;
  color: var(--text-primary);
  margin: 0;
}
.profile-topbar .el-button {
  color: var(--text-secondary);
}

/* ===== 容器 ===== */
.profile-container {
  max-width: 700px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* ===== 卡片 - 毛玻璃 ===== */
.profile-card {
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 20px 24px;
  transition: all 0.3s ease;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

[data-theme="dark"] .profile-card {
  background: rgba(0, 0, 0, 0.25);
  border-color: rgba(255, 255, 255, 0.04);
}

/* ===== 头像区块 ===== */
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
.avatar-wrapper :deep(.el-avatar) {
  border: 3px solid var(--border-color);
  background: var(--input-bg);
  color: var(--text-primary);
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
  background: rgba(128, 128, 128, 0.04);
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

/* ===== 字段 ===== */
.field-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 8px;
}
.field-label i {
  margin-right: 6px;
}
.field-row {
  display: flex;
  gap: 10px;
}
.field-row .el-input {
  flex: 1;
}

/* ===== 画像 ===== */
.portrait-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px 24px;
}
.portrait-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.portrait-label {
  font-size: 13px;
  color: var(--text-secondary);
}

/* ===== 学习建议 ===== */
.advice-text {
  font-size: 14px;
  line-height: 1.8;
  color: var(--text-primary);
  padding: 8px 12px;
  border-radius: 8px;
  background: rgba(128, 128, 128, 0.04);
}
.advice-placeholder {
  font-size: 14px;
  color: var(--text-muted);
  padding: 8px 0;
}
.loading-text {
  color: var(--text-muted);
  font-size: 14px;
  padding: 8px 0;
}

/* ===== 退出按钮 ===== */
.logout-btn {
  width: 100%;
  margin-top: 4px;
  border: 1px solid rgba(245, 108, 108, 0.2) !important;
  background: rgba(245, 108, 108, 0.05) !important;
  color: #f56c6c !important;
  border-radius: 12px !important;
}
.logout-btn:hover {
  background: rgba(245, 108, 108, 0.12) !important;
  border-color: rgba(245, 108, 108, 0.3) !important;
}

/* ===== 深色适配 ===== */
[data-theme="dark"] .basic-row {
  background: rgba(255, 255, 255, 0.03);
}
[data-theme="dark"] .advice-text {
  background: rgba(255, 255, 255, 0.03);
}

/* ===== 响应式 ===== */
@media (max-width: 600px) {
  .avatar-section {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }
  .portrait-grid {
    grid-template-columns: 1fr;
  }
  .field-row {
    flex-direction: column;
  }
  .profile-topbar {
    flex-wrap: wrap;
  }
}
</style>