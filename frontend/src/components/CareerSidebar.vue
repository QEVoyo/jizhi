<template>
  <div class="career-sidebar">
    <h2>🗺️ 学程</h2>
    <el-menu :default-active="activeMenu" @select="handleMenuSelect">
      <el-menu-item index="/career/rank">
        <span>⛰️ 登攀</span>
      </el-menu-item>
      <el-menu-item index="/career/tasks">
        <span>🌾 勤耕</span>
      </el-menu-item>
      <el-menu-item index="/career/achievements">
        <span>🐚 拾贝</span>
      </el-menu-item>
    </el-menu>
    <el-button text @click="goHome" class="back-home">
      ← 返回主界面
    </el-button>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

const activeMenu = computed(() => route.path)

function handleMenuSelect(index) {
  router.push(index)
}

function goHome() {
  router.push('/')
}
</script>

<style scoped>
.career-sidebar {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.career-sidebar h2 {
  font-size: 18px;
  color: var(--text-primary);
}
:deep(.el-menu) {
  border: none;
  background: transparent !important;
}
:deep(.el-menu-item) {
  border-radius: 10px;
  color: var(--text-secondary);
  transition: all 0.3s ease;
}
:deep(.el-menu-item:hover) {
  background: rgba(128, 128, 128, 0.06);
  color: var(--text-primary);
}
:deep(.el-menu-item.is-active) {
  background: rgba(128, 128, 128, 0.08);
  color: var(--text-primary);
}
.back-home {
  margin-top: 12px;
  color: var(--text-muted);
}
</style>