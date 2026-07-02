<template>
  <div class="tasks-page">
    <AppLayout>
      <template #sidebar>
        <CareerSidebar />
      </template>
      <template #main>
        <div class="tasks-content">
          <el-button text @click="goBack" class="back-btn">← 返回</el-button>
          <h1>🌾 勤耕</h1>
          <p class="subtitle">日积月累，勤耕不辍</p>
          <el-divider />

          <!-- 播种 -->
          <h2>🌰 播种</h2>
          <p class="subtitle">新手引导 · 第一次使用各项功能</p>
          <div class="task-table" v-if="seedTasks.length">
            <div class="task-row header">
              <span>状态</span>
              <span>种子</span>
              <span>收获</span>
              <span>价值</span>
              <span>进度</span>
            </div>
            <div class="task-row" v-for="(task, idx) in seedTasks" :key="idx">
              <span class="status-icon">
                <el-icon v-if="task.done" color="#67c23a"><Check /></el-icon>
                <el-icon v-else-if="task.progress >= 100" color="#e6a23c"><Present /></el-icon>
                <el-icon v-else color="#909399"><Clock /></el-icon>
              </span>
              <span>{{ task.name }}</span>
              <span>+{{ task.reward }}</span>
              <span>
                <span v-for="s in task.value" :key="s" class="star">★</span>
              </span>
              <span>
                <el-progress :percentage="task.progress" :color="getColor(task.progress)" :stroke-width="6" />
              </span>
            </div>
          </div>
          <div v-else class="empty-state">暂无播种任务</div>

          <el-divider />

          <!-- 施肥 -->
          <h2>🌱 施肥</h2>
          <p class="subtitle">每日任务 · 完成获得收获</p>
          <div class="task-table" v-if="dailyTasks.length">
            <div class="task-row header">
              <span>状态</span>
              <span>肥料</span>
              <span>收获</span>
              <span>价值</span>
              <span>进度</span>
            </div>
            <div class="task-row" v-for="(task, idx) in dailyTasks" :key="idx">
              <span class="status-icon">
                <el-icon v-if="task.done" color="#67c23a"><Check /></el-icon>
                <el-icon v-else-if="task.progress >= 100" color="#e6a23c"><Present /></el-icon>
                <el-icon v-else color="#909399"><Clock /></el-icon>
              </span>
              <span>{{ task.name }}</span>
              <span>+{{ task.reward }}</span>
              <span>
                <span v-for="s in task.value" :key="s" class="star">★</span>
              </span>
              <span>
                <el-progress :percentage="task.progress" :color="getColor(task.progress)" :stroke-width="6" />
              </span>
            </div>
          </div>
          <div v-else class="empty-state">暂无每日任务</div>

          <el-divider />

          <!-- 发芽 -->
          <h2>🌿 发芽</h2>
          <p class="subtitle">长期耕耘 · 持续积累 · 阶梯解锁</p>
          <div class="task-table" v-if="longTasks.length">
            <div class="task-row header">
              <span>状态</span>
              <span>扎根</span>
              <span>收获</span>
              <span>价值</span>
              <span>进度</span>
            </div>
            <div class="task-row" v-for="(task, idx) in longTasks" :key="idx">
              <span class="status-icon">
                <el-icon v-if="task.done" color="#67c23a"><Check /></el-icon>
                <el-icon v-else-if="task.progress >= 100" color="#e6a23c"><Present /></el-icon>
                <el-icon v-else color="#909399"><Clock /></el-icon>
              </span>
              <span>{{ task.name }}</span>
              <span>+{{ task.reward }}</span>
              <span>
                <span v-for="s in task.value" :key="s" class="star">★</span>
              </span>
              <span>
                <el-progress :percentage="task.progress" :color="getColor(task.progress)" :stroke-width="6" />
              </span>
            </div>
          </div>
          <div v-else class="empty-state">暂无发芽任务</div>

          <el-divider />

          <!-- 丰收 -->
          <h2>🌾 丰收</h2>
          <p class="subtitle">最接近完成的成就 · 加把劲就能收获</p>
          <div v-if="pendingAchievements.length">
            <div
              v-for="ach in pendingAchievements.slice(0, 8)"
              :key="ach.id"
              class="ach-row"
            >
              <span>{{ ach.name }}</span>
              <span class="ach-status">⏳ 未解锁</span>
              <el-progress :percentage="0" :stroke-width="4" />
            </div>
          </div>
          <div v-else class="empty-state">🎉 所有成就已解锁！继续加油！</div>

          <el-button class="view-all-btn" @click="goAchievements">
            📋 查看全部成就 →
          </el-button>
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
import { ElMessage } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()

const taskData = ref({ seed: [], daily: [], long: [], achievements: [] })
const loading = ref(true)

const seedTasks = computed(() => taskData.value.seed || [])
const dailyTasks = computed(() => taskData.value.daily || [])
const longTasks = computed(() => taskData.value.long || [])
const achievements = computed(() => taskData.value.achievements || [])
const pendingAchievements = computed(() => achievements.value.filter(a => !a.done))

function getColor(progress) {
  if (progress < 30) return '#FF6B6B'
  if (progress < 60) return '#FFB74D'
  if (progress < 80) return '#FFD93D'
  return '#6BCB77'
}

async function loadData() {
  loading.value = true
  try {
    taskData.value = await getTaskProgress(authStore.user.id)
  } catch (error) {
    ElMessage.error('加载任务失败')
  } finally {
    loading.value = false
  }
}

function goBack() {
  router.push('/career')
}

function goAchievements() {
  router.push('/career/achievements')
}

onMounted(loadData)
</script>

<style scoped>
.tasks-content {
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

.task-table {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 8px;
}
.task-row {
  display: grid;
  grid-template-columns: 50px 1fr 60px 70px 1fr;
  gap: 8px;
  align-items: center;
  padding: 4px 8px;
  font-size: 14px;
}
.task-row.header {
  font-weight: 600;
  color: var(--text-muted);
  font-size: 12px;
}
.task-row:hover {
  background: rgba(128, 128, 128, 0.04);
  border-radius: 6px;
}
.status-icon {
  display: flex;
  justify-content: center;
}
.star {
  color: #FFD700;
  font-size: 12px;
}
.empty-state {
  color: var(--text-muted);
  padding: 16px 0;
  text-align: center;
}

.ach-row {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 6px 0;
  font-size: 14px;
}
.ach-status {
  font-size: 12px;
  color: var(--text-muted);
  min-width: 70px;
}

.view-all-btn {
  margin-top: 16px;
  width: 100%;
  border: 1px solid var(--border-color) !important;
  border-radius: 10px !important;
  background: transparent !important;
  color: var(--text-secondary) !important;
}
</style>