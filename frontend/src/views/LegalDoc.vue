<template>
  <div class="legal-page">
    <div class="legal-topbar">
      <button class="legal-back" @click="goBack">
        <i class="fas fa-arrow-left"></i>
        <span>返回</span>
      </button>
      <nav class="legal-switch">
        <router-link to="/agreement" :class="{ on: type === 'service' }">用户服务协议</router-link>
        <router-link to="/privacy" :class="{ on: type === 'privacy' }">隐私政策</router-link>
      </nav>
    </div>

    <div class="legal-layout">
      <aside class="legal-toc">
        <div class="toc-title">目录</div>
        <a
          v-for="(sec, i) in doc.sections"
          :key="i"
          :href="'#legal-sec-' + i"
          class="toc-item"
          :class="{ active: activeSection === i }"
          @click="scrollTo(i)"
        >{{ sec.h }}</a>
        <div class="toc-foot">
          <span>更新于 {{ doc.updated }}</span>
        </div>
      </aside>

      <main class="legal-main">
        <LegalContent :doc="doc" />
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import LegalContent from '@/components/LegalContent.vue'
import { useAuthStore } from '@/stores/auth'
import { LEGAL_DOCS, SERVICE_AGREEMENT } from '@/utils/legalDocs'

const props = defineProps({
  type: { type: String, default: 'service' },
})

const router = useRouter()
const authStore = useAuthStore()
const doc = computed(() => LEGAL_DOCS[props.type] || SERVICE_AGREEMENT)
const activeSection = ref(0)

let observer = null

function scrollTo(i) {
  document.getElementById('legal-sec-' + i)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function goBack() {
  if (window.history.length > 1) router.back()
  else router.push(authStore.isLoggedIn ? '/settings' : '/login')
}

function setupObserver() {
  observer?.disconnect()
  const sections = doc.value.sections
    .map((_, i) => document.getElementById('legal-sec-' + i))
    .filter(Boolean)
  if (!sections.length) return

  observer = new IntersectionObserver((entries) => {
    const visible = entries
      .filter(e => e.isIntersecting)
      .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)
    if (visible.length) {
      const i = Number(visible[0].target.id.replace('legal-sec-', ''))
      if (!Number.isNaN(i)) activeSection.value = i
    }
  }, { rootMargin: '-12% 0px -72% 0px', threshold: 0 })

  sections.forEach(el => observer.observe(el))
}

function syncTitle() {
  document.title = `${doc.value.title} · 基智`
}

onMounted(async () => {
  syncTitle()
  await nextTick()
  setupObserver()
})

watch(() => props.type, async () => {
  activeSection.value = 0
  syncTitle()
  await nextTick()
  setupObserver()
  window.scrollTo({ top: 0, behavior: 'auto' })
})

onBeforeUnmount(() => {
  observer?.disconnect()
  document.title = '基智'
})
</script>

<style scoped>
.legal-page {
  min-height: 100vh;
  padding: 24px 28px 64px;
  background: var(--bg, #f7f9fd);
  box-sizing: border-box;
}

.legal-topbar {
  max-width: 1180px;
  margin: 0 auto 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}
.legal-back {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 9px 14px;
  border-radius: 10px;
  border: 1px solid var(--line-soft, rgba(128, 128, 128, .16));
  background: color-mix(in srgb, var(--surface, #fff) 6%, transparent);
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all .2s ease;
}
.legal-back:hover {
  color: var(--text-primary);
  border-color: color-mix(in srgb, var(--brand) 30%, transparent);
  transform: translateX(-2px);
}
.legal-switch {
  display: inline-flex;
  padding: 4px;
  border-radius: 10px;
  background: color-mix(in srgb, var(--surface, #fff) 5%, transparent);
  border: 1px solid var(--line-soft, rgba(128, 128, 128, .12));
}
.legal-switch a {
  padding: 7px 14px;
  border-radius: 7px;
  font-size: 12.5px;
  color: var(--text-muted);
  text-decoration: none;
  transition: all .2s ease;
}
.legal-switch a.on {
  background: var(--brand);
  color: #fff;
  font-weight: 600;
}

.legal-layout {
  max-width: 1180px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 208px minmax(0, 1fr);
  gap: 26px;
  align-items: start;
}

/* ===== 目录 ===== */
.legal-toc {
  position: sticky;
  top: 24px;
  padding: 18px 14px;
  border-radius: 14px;
  border: 1px solid var(--line-soft, rgba(128, 128, 128, .12));
  background: color-mix(in srgb, var(--surface, #fff) 4%, transparent);
  max-height: calc(100vh - 48px);
  overflow-y: auto;
  scrollbar-width: thin;
}
.toc-title {
  font-size: 11px;
  letter-spacing: 2px;
  color: var(--text-muted);
  font-weight: 600;
  padding: 0 8px 10px;
}
.toc-item {
  display: block;
  padding: 7px 8px;
  margin-bottom: 2px;
  border-radius: 7px;
  font-size: 12.5px;
  line-height: 1.5;
  color: var(--text-muted);
  text-decoration: none;
  transition: all .18s ease;
}
.toc-item:hover { color: var(--text-primary); background: color-mix(in srgb, var(--brand) 8%, transparent); }
.toc-item.active {
  color: var(--brand);
  background: color-mix(in srgb, var(--brand) 10%, transparent);
  font-weight: 600;
}
.toc-foot {
  margin-top: 12px;
  padding: 10px 8px 0;
  border-top: 1px solid var(--line-soft, rgba(128, 128, 128, .12));
  font-size: 11px;
  color: var(--text-muted);
}

/* ===== 正文卡片 ===== */
.legal-main {
  min-width: 0;
  padding: 44px 52px 46px;
  border-radius: 20px;
  border: 1px solid var(--line-soft, rgba(128, 128, 128, .12));
  background: var(--surface, #fff);
  box-shadow: 0 2px 4px rgba(22, 35, 58, .03), 0 18px 50px rgba(22, 35, 58, .06);
}

@media (max-width: 900px) {
  .legal-page { padding: 16px 14px 44px; }
  .legal-layout { grid-template-columns: 1fr; gap: 14px; }
  .legal-toc { display: none; }
  .legal-main { padding: 26px 20px 30px; border-radius: 16px; }
  .legal-switch a { padding: 6px 10px; }
}
</style>
