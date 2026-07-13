<template>
  <div class="rank-page">
    <div class="rank-header">
      <h2>🏆 好友排行榜</h2>
      <span class="rank-subtitle">看看谁在学习路上走得更远</span>
    </div>

    <el-divider />

    <div v-if="loading" class="loading-state">
      <i class="fas fa-spinner fa-spin"></i> 加载中...
    </div>

    <div v-else-if="!rankList.length" class="empty-state">
      <i class="fas fa-trophy" style="font-size: 48px; opacity: 0.3;"></i>
      <p>暂无好友</p >
      <span>添加好友后，这里会显示排行榜</span>
    </div>

    <div v-else class="rank-list">
      <div
        v-for="(item, index) in rankList"
        :key="item.user_id"
        class="rank-item"
        :class="{
          top1: index === 0,
          top2: index === 1,
          top3: index === 2,
          'is-self': item.is_self
        }"
        @click="goUserProfile(item.user_id)"
      >
        <div class="rank-number">
          <span v-if="index === 0">🥇</span>
          <span v-else-if="index === 1">🥈</span>
          <span v-else-if="index === 2">🥉</span>
          <span v-else>{{ index + 1 }}</span>
        </div>

        <el-avatar :size="44" :src="item.avatar_url || ''" class="rank-avatar">
          {{ item.nickname?.[0] || 'U' }}
        </el-avatar>

        <div class="rank-info">
          <div class="rank-name">
            {{ item.nickname || '用户' }}
            <span v-if="item.is_self" class="self-tag">（我）</span>
          </div>
          <div class="rank-account">{{ item.user_account || '' }}</div>
        </div>

        <div class="rank-stats">
          <span class="rank-badge" :style="{ color: getRankColor(item.rank) }">
            {{ getRankIcon(item.rank) }} {{ item.rank }}
            <span class="rank-sub">{{ getSubSymbol(item.sub_rank) }}</span>
          </span>
          <span class="rank-points">⭐ {{ item.points }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import { getFriendsRank } from '@/api/community'
import { RANK_ICONS, RANK_COLORS, SUB_SYMBOLS } from '@/utils/constants'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const rankList = ref([])

function getRankIcon(rank) {
  return RANK_ICONS[rank] || '◈'
}

function getRankColor(rank) {
  return RANK_COLORS[rank] || '#888'
}

function getSubSymbol(subRank) {
  return SUB_SYMBOLS[subRank] || '○'
}

async function loadRank() {
  loading.value = true
  try {
    const res = await getFriendsRank(authStore.user.id)
    rankList.value = res.rank || []
  } catch {
    ElMessage.error('加载排行榜失败')
  } finally {
    loading.value = false
  }
}

function goUserProfile(userId) {
  router.push(`/community/user/${userId}`)
}

onMounted(() => {
  loadRank()
})
</script>

<style scoped>
.rank-page {
  padding: 0 4px;
}

.rank-header {
  display: flex;
  align-items: center;
  gap: 16px;
}
.rank-header h2 {
  font-size: 22px;
  color: var(--text-primary);
  margin: 0;
}
.rank-subtitle {
  font-size: 14px;
  color: var(--text-muted);
  opacity: 0.6;
}

.el-divider {
  margin: 12px 0;
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
.empty-state span {
  font-size: 14px;
  opacity: 0.6;
}

.rank-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.rank-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 16px;
  border-radius: 12px;
  border: 1px solid var(--border-color);
  background: var(--card-bg);
  cursor: pointer;
  transition: all 0.3s ease;
}
.rank-item:hover {
  background: var(--hover-bg);
  border-color: var(--border-hover);
  transform: translateX(4px);
}

.rank-item.top1 {
  border-color: rgba(255, 215, 0, 0.4);
  background: rgba(255, 215, 0, 0.06);
}
.rank-item.top2 {
  border-color: rgba(192, 192, 192, 0.4);
  background: rgba(192, 192, 192, 0.06);
}
.rank-item.top3 {
  border-color: rgba(205, 127, 50, 0.4);
  background: rgba(205, 127, 50, 0.06);
}

.rank-item.is-self {
  border-color: var(--el-color-primary) !important;
  background: rgba(64, 158, 255, 0.08) !important;
}

.rank-number {
  font-size: 20px;
  font-weight: 700;
  min-width: 36px;
  text-align: center;
  color: var(--text-secondary);
}
.rank-number span {
  font-size: 20px;
}

.rank-avatar {
  flex-shrink: 0;
}

.rank-info {
  flex: 1;
  min-width: 0;
}
.rank-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}
.self-tag {
  font-size: 12px;
  font-weight: 400;
  color: var(--el-color-primary);
}
.rank-account {
  font-size: 12px;
  color: var(--text-muted);
}

.rank-stats {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
}
.rank-badge {
  font-size: 14px;
  font-weight: 600;
}
.rank-sub {
  font-size: 13px;
}
.rank-points {
  font-size: 12px;
  color: var(--text-muted);
}
</style>