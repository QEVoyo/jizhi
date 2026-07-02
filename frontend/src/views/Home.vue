<template>
  <div class="home-page">
    <AppLayout>
      <template #sidebar>
        <Sidebar />
      </template>
      <template #main>
        <ChatArea />
      </template>
    </AppLayout>
  </div>
</template>

<script setup>
import AppLayout from '@/components/AppLayout.vue'
import Sidebar from '@/components/Sidebar.vue'
import ChatArea from '@/components/ChatArea.vue'
</script>

<style scoped>
.home-page {
  min-height: 100vh;
}
</style>