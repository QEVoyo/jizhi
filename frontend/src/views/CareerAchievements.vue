<template>
  <div class="achievements-page">
    <AppLayout>
      <template #sidebar>
        <CareerSidebar />
      </template>
      <template #main>
        <div class="achievements-content">
          <el-button text @click="goBack" class="back-btn">← 返回</el-button>
          <h1>🐚 拾贝</h1>
          <p class="subtitle">学海拾贝，采撷成果</p>
          <el-divider />

          <div class="stats-bar">
            <span>已拾取：{{ doneCount }} / {{ totalCount }}</span>
            <el-progress
              :percentage="totalProgress"
              :color="totalProgress >= 80 ? '#6BCB77' : '#FFB74D'"
              :stroke-width="8"
              style="flex:1; max-width:300px;"
            />
          </div>

          <el-divider />

          <div class="achievement-grid">
            <div
              v-for="ach in achievements"
              :key="ach.id"
              class="ach-card"
              :class="{ locked: !ach.done }"
              @click="showDetail(ach)"
            >
              <div class="ach-icon" :style="{ color: ach.done ? ach.themeColor : '#666' }">
                <el-icon><Trophy /></el-icon>
              </div>
              <div class="ach-name">{{ ach.name }}</div>
              <div class="ach-condition">{{ ach.condition }}</div>
              <div class="ach-reward">+{{ ach.reward }}</div>
              <div class="ach-status">{{ ach.done ? '✅ 已拾取' : '🔒 未拾取' }}</div>
            </div>
          </div>
        </div>
      </template>
    </AppLayout>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AppLayout from '@/components/AppLayout.vue'
import CareerSidebar from '@/components/CareerSidebar.vue'
import { getTaskProgress } from '@/api/career'
import { ElDialog } from 'element-plus'
import { Trophy } from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()

const achievements = ref([])
const loading = ref(true)

const doneCount = computed(() => achievements.value.filter(a => a.done).length)
const totalCount = computed(() => achievements.value.length)
const totalProgress = computed(() => {
  if (!totalCount.value) return 0
  return Math.round((doneCount.value / totalCount.value) * 100)
})

const colors = [
  '#FF6B6B', '#FF8E53', '#FFB74D', '#FFD93D', '#A8E06C',
  '#6BCB77', '#4ECDC4', '#45B7D1', '#4A9FF5', '#7C6DF0',
  '#9B59B6', '#E040FB', '#EC407A', '#F06292', '#FF8A80'
]

async function loadData() {
  loading.value = true
  try {
    const data = await getTaskProgress(authStore.user.id)
    achievements.value = (data.achievements || []).map((a, i) => ({
      ...a,
      themeColor: colors[i % colors.length]
    }))
  } catch (error) {
    console.error('加载成就失败', error)
  } finally {
    loading.value = false
  }
}

function showDetail(ach) {
  // 简单弹窗显示详情
  const msg = `
🏆 ${ach.name}
📝 ${ach.condition}
🎁 +${ach.reward} 收获
${ach.done ? '✅ 已拾取' : '🔒 未拾取'}
${ach.unlock_time ? `📅 ${ach.unlock_time}` : ''}
  `
  ElMessageBox.alert(msg, '成就详情', {
    confirmButtonText: '知道了'
  })
}

function goBack() {
  router.push('/career')
}

onMounted(loadData)
</script>

<style scoped>
.achievements-content {
  padding: 8px 4px;
}
.back-btn {
  margin-bottom: 12px;
  color: var(--text-secondary);
}
h1 {
  font-size: 28px;
  color: var(--text-primary);
}
.subtitle {
  color: var(--text-secondary);
  font-size: 14px;
  opacity: 0.6;
}

.stats-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}
.stats-bar span {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.achievement-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
  margin-top: 8px;
}

.ach-card {
  padding: 18px 12px;
  border-radius: 12px;
  border: 1px solid var(--border-color);
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background: var(--card-bg);
}
.ach-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-hover);
}
.ach-card.locked {
  opacity: 0.5;
}
.ach-card.locked:hover {
  opacity: 0.7;
}

.ach-icon {
  font-size: 32px;
}
.ach-name {
  font-weight: 600;
  font-size: 15px;
  margin: 6px 0 2px;
}
.ach-condition {
  font-size: 12px;
  color: var(--text-muted);
}
.ach-reward {
  font-size: 14px;
  font-weight: 500;
  margin: 4px 0;
}
.ach-status {
  font-size: 12px;
  color: var(--text-muted);
}
</style>