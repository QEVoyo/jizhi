<template>
  <div class="community-user-profile">
    <!-- ===== 顶部标题 ===== -->
    <div class="profile-header">
      <el-button text class="back-btn" @click="goBack">
        <i class="fas fa-arrow-left"></i> 返回
      </el-button>
      <h2>👤 用户资料</h2>
    </div>

    <el-divider />

    <div v-if="loading" class="loading-state">
      <i class="fas fa-spinner fa-spin"></i> 加载中...
    </div>

    <div v-else-if="!userData" class="empty-state">
      <p>用户不存在</p >
    </div>

    <div v-else class="user-profile-content">
      <!-- 用户信息 -->
      <div class="user-section">
        <el-avatar :size="80" :src="userData.profile?.avatar_url || ''" class="user-avatar">
          {{ userData.profile?.nickname?.[0] || 'U' }}
        </el-avatar>
        <div class="user-info">
          <div class="user-name">{{ userData.profile?.nickname || '用户' }}</div>
          <div class="user-meta">
            <span class="user-level">Lv.{{ userLevel }}</span>
            <span class="user-rank" :style="{ color: rankColor }">
              {{ rankIcon }} {{ rankName }} {{ rankSubSymbol }}
            </span>
            <span class="user-account">账号：{{ userData.profile?.account || '' }}</span>
          </div>
          <div class="user-stats">
            积分：{{ userData.profile?.points || 0 }}
            <span class="stat-divider">|</span>
            成就：{{ userData.achievement_count || 0 }}
            <span class="stat-divider">|</span>
            掌握度：{{ userData.avg_mastery || 0 }}%
          </div>
          <div class="user-actions">
            <el-button
              v-if="isFriend"
              size="small"
              type="primary"
              plain
              @click="goChat"
            >
              <i class="fas fa-comment"></i> 聊天
            </el-button>
            <el-button
              v-else-if="requestStatus === 'pending'"
              size="small"
              disabled
            >
              已发送请求
            </el-button>
            <el-button
              v-else
              size="small"
              type="primary"
              @click="sendRequest"
            >
              <i class="fas fa-user-plus"></i> 添加好友
            </el-button>
            <el-button
              v-if="isFriend"
              size="small"
              type="danger"
              plain
              @click="removeFriend"
            >
              <i class="fas fa-user-minus"></i> 删除好友
            </el-button>
          </div>
        </div>
      </div>

      <el-divider />

      <!-- 近期动态 -->
      <div class="activities-section">
        <h4>📈 近期动态</h4>
        <div v-if="!userData.activities?.length" class="activity-empty">
          暂无动态
        </div>
        <div v-for="act in userData.activities" :key="act.id" class="activity-item">
          <span class="activity-icon">{{ getActivityIcon(act.type) }}</span>
          <span class="activity-text">{{ act.content?.text || act.type }}</span>
          <span class="activity-time">{{ formatTime(act.created_at) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getProfileCard, sendFriendRequest, deleteFriend } from '@/api/community'
import { RANK_ICONS, RANK_COLORS, SUB_SYMBOLS } from '@/utils/constants'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const userId = route.params.userId
const loading = ref(false)
const userData = ref(null)
const isFriend = ref(false)
const requestStatus = ref('none')

const userLevel = computed(() => {
  if (!userData.value?.profile) return 1
  return Math.floor((userData.value.profile.points || 0) / 100) + 1
})
const rankName = computed(() => userData.value?.profile?.rank || '启程')
const rankIcon = computed(() => RANK_ICONS[rankName.value] || '◈')
const rankColor = computed(() => RANK_COLORS[rankName.value] || '#888')
const rankSubSymbol = computed(() => {
  const sub = userData.value?.profile?.sub_rank || 1
  return SUB_SYMBOLS[sub] || '○'
})

function getActivityIcon(type) {
  const map = {
    checkin: '✅',
    question_completed: '📝',
    achievement_unlocked: '🏆',
    note_published: '📖',
    set_created: '📁',
    timer_completed: '⏱️',
    mistake_conquered: '🎯',
    level_up: '⬆️',
    rank_up: '🏅'
  }
  return map[type] || '📌'
}

function formatTime(time) {
  if (!time) return ''
  const t = new Date(time)
  return t.toLocaleDateString()
}

async function loadData() {
  loading.value = true
  try {
    const res = await getProfileCard(userId, authStore.user.id)
    userData.value = res
    isFriend.value = res.is_friend || false
    requestStatus.value = res.request_status || 'none'
  } catch {
    ElMessage.error('加载用户资料失败')
  } finally {
    loading.value = false
  }
}

function goBack() {
  router.back()
}

function goChat() {
  router.push(`/community/chat/${userId}`)
}

async function sendRequest() {
  try {
    await sendFriendRequest(authStore.user.id, userId)
    ElMessage.success('好友请求已发送')
    requestStatus.value = 'pending'
  } catch {
    ElMessage.error('发送失败')
  }
}

function removeFriend() {
  ElMessageBox.confirm('确定要删除这个好友吗？', '确认删除')
    .then(async () => {
      try {
        await deleteFriend(authStore.user.id, userId)
        ElMessage.success('已删除')
        isFriend.value = false
      } catch {
        ElMessage.error('删除失败')
      }
    })
    .catch(() => {})
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.community-user-profile {
  padding: 0 4px;
}

.profile-header {
  display: flex;
  align-items: center;
  gap: 12px;
}
.back-btn {
  color: var(--text-secondary) !important;
  font-size: 15px;
  padding: 4px 8px;
}
.back-btn:hover {
  color: var(--text-primary) !important;
  transform: translateX(-2px);
}
.profile-header h2 {
  font-size: 22px;
  color: var(--text-primary);
  margin: 0;
}

.el-divider {
  margin: 12px 0;
}

.user-profile-content {
  max-width: 700px;
  margin: 0 auto;
}

.user-section {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 8px 0;
}
.user-avatar {
  flex-shrink: 0;
}
.user-info {
  flex: 1;
}
.user-name {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
}
.user-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  color: var(--text-secondary);
  margin: 2px 0;
}
.user-level {
  font-weight: 600;
}
.user-rank {
  font-weight: 600;
}
.user-account {
  color: var(--text-muted);
}
.user-stats {
  font-size: 14px;
  color: var(--text-secondary);
}
.stat-divider {
  color: var(--text-muted);
  margin: 0 6px;
}
.user-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}
.user-actions .el-button {
  border-radius: 8px !important;
  transition: all 0.3s ease !important;
}
.user-actions .el-button:hover {
  transform: translateY(-2px);
}

.activities-section {
  padding: 8px 0;
}
.activities-section h4 {
  font-size: 15px;
  color: var(--text-primary);
  margin: 0 0 10px 0;
}

.activity-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 0;
  font-size: 14px;
}
.activity-icon {
  font-size: 16px;
}
.activity-text {
  color: var(--text-secondary);
}
.activity-time {
  margin-left: auto;
  font-size: 12px;
  color: var(--text-muted);
}
.activity-empty {
  color: var(--text-muted);
  font-size: 13px;
}

.loading-state,
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-muted);
}
.empty-state p {
  font-size: 16px;
  color: var(--text-secondary);
  margin: 4px 0;
}

@media (max-width: 640px) {
  .user-section {
    flex-direction: column;
    text-align: center;
  }
  .user-meta {
    justify-content: center;
    flex-wrap: wrap;
  }
  .user-actions {
    justify-content: center;
    flex-wrap: wrap;
  }
}
</style>