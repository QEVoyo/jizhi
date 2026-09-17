<template>
  <div class="profile-page">
    <!-- 顶部返回 -->
    <div class="profile-topbar">
      <button class="back-btn" @click="$router.push('/')">
        <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M19 12H5M12 19l-7-7 7-7"/>
        </svg>
        返回主界面
      </button>
      <h1>个人中心</h1>
    </div>

    <div class="profile-container">
      <!-- ===== 新个人中心（2026-09-03 用户拍板）：资料卡为主体——卡内只放展示内容（给好友/陌生人看），
           个人动作与数据入口一律在卡外 ===== -->
      <CommunityProfileCard :hide-title="true" />

      <div class="pc-page-actions">
        <button class="page-btn primary" @click="router.push('/settings')">⚙ 编辑资料与设置</button>
        <button class="page-btn" @click="router.push('/onboarding?edit=true')">✍ 重新填写偏好问卷</button>
        <button class="page-btn danger" @click="handleLogout">⏻ 退出登录</button>
      </div>

      <div class="page-quick">
        <span class="page-quick-title">🧭 学习数据</span>
        <div class="page-quick-grid">
          <router-link to="/evaluation-report" class="page-quick-card">📊 学情报告</router-link>
          <router-link to="/evaluation-table" class="page-quick-card">📋 评估表</router-link>
          <router-link to="/profile-card" class="page-quick-card">🌌 维度宇宙</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessageBox, ElMessage } from 'element-plus'
import CommunityProfileCard from '@/components/community/CommunityProfileCard.vue'

const router = useRouter()
const authStore = useAuthStore()

async function handleLogout() {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '确认退出', {
      confirmButtonText: '确认', cancelButtonText: '取消', type: 'warning'
    })
    await authStore.logout()
    ElMessage.success('已退出')
    router.push('/login')
  } catch (e) { /* 用户取消 */ }
}
</script>

<style scoped>
.profile-page {
  min-height: 100vh;
  padding: 20px 28px;
}

.profile-topbar {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 24px;
}
.profile-topbar h1 {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 18px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  font-family: inherit;
  color: var(--text-secondary);
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent);
  border: 1px solid var(--line-soft);
  cursor: pointer;
  transition: all 0.25s ease;
}
.back-btn:hover {
  background: color-mix(in srgb, var(--surface, #ffffff) 8%, transparent);
  border-color: var(--line);
  transform: translateY(-1px);
}
.back-btn .icon { width: 20px; height: 20px; }

.profile-container {
  max-width: 620px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* ====== 卡外个人动作（编辑/问卷/退出：个人操作，不进卡） ====== */
.pc-page-actions { display: flex; gap: 10px; flex-wrap: wrap; }
.page-btn {
  flex: 1; min-width: 150px;
  display: inline-flex; align-items: center; justify-content: center; gap: 6px;
  padding: 10px 14px; border-radius: 12px;
  font-size: 13px; font-weight: 600; font-family: inherit;
  color: var(--text-secondary);
  background: color-mix(in srgb, var(--surface, #ffffff) 5%, transparent);
  border: 1px solid var(--line-soft);
  cursor: pointer;
  transition: all .2s ease;
}
.page-btn:hover {
  background: color-mix(in srgb, var(--surface, #ffffff) 10%, transparent);
  border-color: var(--line);
  transform: translateY(-1px);
}
.page-btn.primary {
  color: var(--brand);
  background: color-mix(in srgb, var(--brand) 10%, transparent);
  border-color: color-mix(in srgb, var(--brand) 22%, transparent);
}
.page-btn.primary:hover { background: color-mix(in srgb, var(--brand) 18%, transparent); }
.page-btn.danger {
  color: color-mix(in srgb, #ef4444 70%, var(--text-primary));
  background: rgba(245,108,108,0.08);
  border-color: rgba(245,108,108,0.25);
}
.page-btn.danger:hover { background: rgba(245,108,108,0.16); }

/* ====== 卡外学习数据入口 ====== */
.page-quick {
  padding: 16px 18px; border-radius: 16px;
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent);
  border: 1px solid var(--line-soft);
}
.page-quick-title { font-size: 13px; font-weight: 600; color: var(--text-secondary); display: block; margin-bottom: 10px; }
.page-quick-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
.page-quick-card {
  display: flex; align-items: center; justify-content: center; gap: 6px;
  padding: 12px 8px; border-radius: 10px;
  font-size: 12.5px; font-weight: 600;
  color: var(--text-secondary);
  background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent);
  border: 1px solid var(--line-soft);
  text-decoration: none;
  transition: all .2s ease;
}
.page-quick-card:hover {
  background: color-mix(in srgb, var(--brand) 8%, transparent);
  border-color: color-mix(in srgb, var(--brand) 20%, transparent);
  color: var(--brand-bright);
  transform: translateY(-1px);
}

@media (max-width: 600px) {
  .profile-page { padding: 12px 16px; }
  .profile-topbar { flex-wrap: wrap; }
  .page-quick-grid { grid-template-columns: 1fr; }
  .pc-page-actions { flex-direction: column; }
}
</style>