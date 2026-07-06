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
      <p>用户不存在</p>
    </div>

    <div v-else class="user-profile-content">
      <!-- ===== 用户信息 ===== -->
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
            <span class="user-account">账号：{{ userData.profile?.user_account || '' }}</span>
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

      <!-- ===== 知识点掌握（新增） ===== -->
      <div class="mastery-section" v-if="masteryData.length">
        <div class="section-header">
          <h4>📚 知识点掌握</h4>
        </div>
        <div class="topic-grid">
          <div
            v-for="item in masteryData.slice(0, 10)"
            :key="item.topic"
            class="topic-card"
            :style="{
              background: `linear-gradient(145deg, ${getColor(item.mastery_score)}, ${getColorDark(item.mastery_score)})`,
              boxShadow: `0 4px 20px ${getColor(item.mastery_score)}60`
            }"
          >
            <span class="topic-name">{{ item.topic }}</span>
            <span class="topic-score">{{ item.mastery_score }}%</span>
            <span class="topic-badge">{{ getBadge(item.mastery_score) }}</span>
          </div>
        </div>
      </div>

      <!-- ===== 成就展示（新增） ===== -->
      <div class="achievement-section" v-if="achievements.length">
        <div class="section-header">
          <h4>🏆 成就展示</h4>
        </div>
        <div class="achievement-grid">
          <div
            v-for="ach in achievements.slice(0, 8)"
            :key="ach.id"
            class="achievement-item"
            :style="{ color: ach.themeColor || '#888' }"
          >
            <i :class="ach.icon || 'fas fa-trophy'"></i>
            <span class="ach-name">{{ ach.name }}</span>
          </div>
        </div>
      </div>

      <!-- ===== 近期动态 ===== -->
      <div class="activities-section">
        <h4>📈 近期动态</h4>
        <div v-if="!userData.activities?.length" class="activity-empty">
          暂无动态
        </div>
        <div v-for="act in userData.activities" :key="act.id" class="activity-item">
          <span class="activity-icon">{{ getActivityIcon(act.action || act.type) }}</span>
          <span class="activity-text">{{ act.details?.text || act.content?.text || act.action || act.type || '学习记录' }}</span>
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
const masteryData = ref([])
const achievements = ref([])

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

// ===== 掌握度颜色 =====
const MASTERY_COLORS = [
  '#FF0000', '#FF1A00', '#FF3300', '#FF4D00', '#FF6600',
  '#FF8000', '#FF9900', '#FFB300', '#FFCC00', '#FFE600',
  '#D4E000', '#A8D500', '#7DCC00', '#52C200', '#26B800',
  '#00AD00', '#00A300', '#009900', '#008000', '#006600'
]
const MASTERY_COLORS_DARK = [
  '#CC0000', '#CC1500', '#CC2A00', '#CC3E00', '#CC5200',
  '#CC6600', '#CC7A00', '#CC8F00', '#CCA300', '#CCB800',
  '#A9B300', '#86AA00', '#64A100', '#419800', '#1E8F00',
  '#008A00', '#008200', '#007A00', '#006600', '#005200'
]

function getColor(score) {
  const index = Math.min(Math.floor(score / 5), 19)
  return MASTERY_COLORS[index] || '#888'
}
function getColorDark(score) {
  const index = Math.min(Math.floor(score / 5), 19)
  return MASTERY_COLORS_DARK[index] || '#666'
}
function getBadge(score) {
  if (score < 60) return '🔴 薄弱'
  if (score < 80) return '🟡 待巩固'
  return '🟢 优势'
}

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
    rank_up: '🏅',
    answer_question: '📝',
    generate_question: '✏️',
    create_set: '📁',
    conquer_mistake: '🎯',
    chat: '💬',
    view_report: '📊',
    share: '📤'
  }
  return map[type] || '📌'
}

function formatTime(time) {
  if (!time) return ''
  const t = new Date(time)
  const now = new Date()
  const diff = Math.floor((now - t) / 1000)
  if (diff < 60) return '刚刚'
  if (diff < 3600) return Math.floor(diff / 60) + '分钟前'
  if (diff < 86400) return Math.floor(diff / 3600) + '小时前'
  if (diff < 604800) return Math.floor(diff / 86400) + '天前'
  return t.toLocaleDateString()
}

async function loadData() {
  loading.value = true
  try {
    const res = await getProfileCard(userId, authStore.user.id)
    userData.value = res
    isFriend.value = res.is_friend || false
    requestStatus.value = res.request_status || 'none'
    masteryData.value = res.mastery_data || []
    achievements.value = res.achievements || []
  } catch {
    ElMessage.error('加载用户资料失败')
  } finally {
    loading.value = false
  }
}

function goBack() {
  const from = route.query.from
  if (from === 'list' || from === 'requests' || from === 'search') {
    router.push({
      path: '/community/friends',
      query: { tab: from }
    })
  } else {
    router.back()
  }
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

/* ===== 知识点 ===== */
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
.section-header h4 {
  font-size: 15px;
  color: var(--text-primary);
  margin: 0;
}
.mastery-section {
  padding: 8px 0;
}
.topic-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 10px;
}
.topic-card {
  padding: 12px 10px;
  border-radius: 12px;
  color: #fff;
  text-align: center;
  transition: all 0.3s ease;
  min-height: 80px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.topic-card:hover {
  transform: translateY(-4px);
}
.topic-name {
  font-size: 13px;
  font-weight: 500;
  text-shadow: 0 1px 4px rgba(0,0,0,0.15);
}
.topic-score {
  font-size: 22px;
  font-weight: 700;
  text-shadow: 0 1px 4px rgba(0,0,0,0.15);
}
.topic-badge {
  font-size: 11px;
  opacity: 0.85;
  text-shadow: 0 1px 4px rgba(0,0,0,0.15);
}

/* ===== 成就 ===== */
.achievement-section {
  padding: 8px 0;
}
.achievement-grid {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
.achievement-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px 6px 10px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.05);
  font-size: 14px;
  transition: all 0.3s ease;
}
.achievement-item:hover {
  transform: translateY(-2px);
  background: rgba(255, 255, 255, 0.07);
}
.achievement-item i {
  font-size: 20px;
}
.ach-name {
  font-size: 13px;
  color: var(--text-secondary);
}

/* ===== 动态 ===== */
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
  .topic-grid {
    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  }
  .topic-card {
    min-height: 70px;
    padding: 8px;
  }
  .topic-score {
    font-size: 18px;
  }
}
</style>