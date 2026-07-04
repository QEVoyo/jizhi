<template>
  <div class="community-page">
    <AppLayout locked>
      <template #sidebar>
        <CommunitySidebar />
      </template>
      <template #main>
        <router-view />
      </template>
    </AppLayout>
  </div>
</template>

<script setup>
import AppLayout from '@/components/AppLayout.vue'
import CommunitySidebar from '@/components/community/CommunitySidebar.vue'
</script>

<style scoped>
.community-page {
  min-height: 100vh;
}
</style>