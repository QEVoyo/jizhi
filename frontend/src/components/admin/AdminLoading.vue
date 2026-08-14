<template>
  <div class="admin-loading" v-if="visible">
    <div class="loading-core">
      <div class="loading-ring"></div>
      <div class="loading-inner"></div>
    </div>
    <p class="loading-text" v-if="text">{{ text }}</p>
  </div>
</template>

<script setup>
defineProps({
  visible: { type: Boolean, default: true },
  text: { type: String, default: '' }
})
</script>

<style scoped>
.admin-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  gap: 16px;
}

.loading-core {
  position: relative;
  width: 40px;
  height: 40px;
}

/* 外圈旋转 */
.loading-ring {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 2px solid transparent;
  border-top-color: rgba(64, 158, 255, 0.6);
  border-right-color: rgba(64, 158, 255, 0.3);
  animation: ring-spin 0.8s linear infinite;
}

/* 内圈反向旋转 */
.loading-inner {
  position: absolute;
  inset: 6px;
  border-radius: 50%;
  border: 2px solid transparent;
  border-bottom-color: rgba(245, 158, 11, 0.5);
  border-left-color: rgba(245, 158, 11, 0.2);
  animation: ring-spin 1.2s linear infinite reverse;
}

@keyframes ring-spin {
  to { transform: rotate(360deg); }
}

.loading-text {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.3);
  letter-spacing: 0.5px;
  animation: text-pulse 2s ease-in-out infinite;
}

@keyframes text-pulse {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 0.7; }
}
</style>
