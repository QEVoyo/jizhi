<template>
  <div class="resource-sidebar">
    <h2>📚 资源库</h2>
    <el-button text @click="goHome" class="back-home">← 返回主界面</el-button>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

function goHome() {
  router.push('/')
}
</script>

<style scoped>
.resource-sidebar {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.resource-sidebar h2 {
  font-size: 18px;
  color: var(--text-primary);
}
.back-home {
  color: var(--text-muted);
}
</style>