<template>
  <!-- 外观码直达页（2026-09-04）：好友点开 /theme?code=xxx 即见预览 + 一键应用，免登录 -->
  <div class="ts-page">
    <div class="ts-card">
      <div class="ts-head">
        <span class="ts-logo" :style="{ background: headBrand, color: headInk }">基</span>
        <div>
          <h1>一份外观礼包 🌈</h1>
          <p>好友分享了一份基智「外观码」给你</p>
        </div>
      </div>

      <!-- 无码 / 校验失败：粘贴输入 -->
      <template v-if="!decoded">
        <textarea
          v-model="codeInput"
          class="ts-input"
          rows="3"
          placeholder="粘贴外观码，例如：JZ1-space 或 JZ1-0d1220-16233c-409eff-paper-CK2F8"></textarea>
        <div v-if="errMsg" class="ts-err">⚠️ {{ errMsg }}</div>
      </template>

      <!-- 有效码：预览 + 适配度 + 一键应用 -->
      <template v-else>
        <div class="ts-tagrow">
          <span v-if="decoded.setName" class="ts-tag">「{{ decoded.setName }}」官方套装</span>
          <span class="ts-score" :class="fit.cls">适配度 {{ fit.pct }}%</span>
        </div>
        <ThemePreviewWindow
          :bg="decoded.payload.bg"
          :surface="decoded.payload.surface"
          :brand="decoded.payload.brand"
          :text="previewText" />
        <div v-if="fit.cls === 'bad'" class="ts-warn">⚠️ 这份外观的对比度偏弱，应用后文字可能看不清</div>

        <div class="ts-actions">
          <el-button type="primary" size="large" :disabled="applied" @click="apply">
            {{ applied ? '✓ 已应用' : '应用这份外观' }}
          </el-button>
          <el-button size="large" @click="goApp">{{ applied ? '去设置里看看' : '暂不应用，进去逛逛' }}</el-button>
        </div>
        <p class="ts-hint">
          <template v-if="applied">
            {{ authStore.isLoggedIn ? '已应用到本机并同步到账号，换设备外观不变' : '已应用到本机。登录后保存到账号，换设备不丢' }}
          </template>
          <template v-else>应用后全站四轴（背景 / 组件 / 主题 / 字体）都会换成这份外观</template>
        </p>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore, resolveText, computeFit, luminance } from '@/stores/theme'
import { decodeAppearance } from '@/utils/appearanceCode'
import { updateUserTheme } from '@/api/auth'
import ThemePreviewWindow from '@/components/ThemePreviewWindow.vue'

const router = useRouter()
const authStore = useAuthStore()
const themeStore = useThemeStore()

// 来自分享链接 /theme?code=xxx（重复参数时取第一个）
const _qc = router.currentRoute.value.query.code
const codeInput = ref(Array.isArray(_qc) ? _qc[0] : (_qc || ''))
const applied = ref(false)

const decoded = computed(() => {
  const t = String(codeInput.value || '').trim()
  if (!t) return null
  const r = decodeAppearance(t)
  return r.ok ? r : null
})
const errMsg = computed(() => {
  const t = String(codeInput.value || '').trim()
  if (!t) return ''
  const r = decodeAppearance(t)
  return r.ok ? '' : r.error
})

const previewText = computed(() => {
  const p = decoded.value?.payload
  return p ? resolveText(p.textScheme, p.textOverrides, p.bg) : null
})
const fit = computed(() => {
  const p = decoded.value?.payload
  return p && previewText.value ? computeFit(p.bg, p.surface, p.brand, previewText.value) : { pct: 0, cls: '' }
})
const headBrand = computed(() => decoded.value?.payload?.brand || '#409EFF')
const headInk = computed(() => luminance(headBrand.value) > 0.5 ? '#1a1a2e' : '#ffffff')

async function apply() {
  const p = decoded.value?.payload
  if (!p) return
  themeStore.applyAppearance(p)
  applied.value = true
  if (authStore.user?.id) {
    try {
      await updateUserTheme(authStore.user.id, {
        brand_color: p.brand, text_scheme: p.textScheme, text_overrides: p.textOverrides,
        bg_color: p.bg, surface_color: p.surface,
      })
    } catch { /* 本机已应用，账号同步失败静默（settings 里可再存） */ }
  }
}

function goApp() {
  if (authStore.isLoggedIn) {
    router.push(applied.value ? '/settings' : '/home')
  } else {
    router.push('/')
  }
}
</script>

<style scoped>
.ts-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px 16px;
}
.ts-card {
  width: 100%;
  max-width: 520px;
  padding: 24px;
  border-radius: 18px;
  background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid var(--line-soft);
  box-shadow: 0 12px 48px rgba(0,0,0,.2);
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.ts-head { display: flex; align-items: center; gap: 12px; }
.ts-logo {
  display: flex; align-items: center; justify-content: center;
  width: 42px; height: 42px; border-radius: 12px;
  font-size: 20px; font-weight: 700;
  box-shadow: 0 4px 18px rgba(0,0,0,.25);
  flex: none;
}
.ts-head h1 { font-size: 17px; font-weight: 700; color: var(--text-primary); }
.ts-head p { font-size: 12px; color: var(--text-muted); margin-top: 2px; }

.ts-input {
  width: 100%;
  padding: 12px 14px;
  border-radius: 12px;
  font-size: 13px;
  font-family: 'Consolas', 'Menlo', monospace;
  line-height: 1.5;
  min-height: 72px;
  resize: vertical;
  color: var(--text-primary);
  background: color-mix(in srgb, var(--surface, #ffffff) 5%, transparent);
  border: 1px solid var(--line-soft);
  outline: none;
  box-sizing: border-box;
}
.ts-input::placeholder { color: var(--text-muted); opacity: 0.45; }
.ts-input:focus {
  border-color: color-mix(in srgb, var(--brand) 30%, transparent);
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--brand) 5%, transparent);
}
.ts-err {
  font-size: 12px; color: #f56c6c;
  padding: 8px 12px; border-radius: 8px;
  background: rgba(245,108,108,.08);
  border: 1px solid rgba(245,108,108,.2);
}

.ts-tagrow { display: flex; align-items: center; justify-content: space-between; }
.ts-tag {
  font-size: 12px; font-weight: 600; color: var(--brand-bright);
  padding: 3px 12px; border-radius: 999px;
  background: color-mix(in srgb, var(--brand) 12%, transparent);
  border: 1px solid color-mix(in srgb, var(--brand) 30%, transparent);
}
.ts-score { font-size: 14px; font-weight: 700; }
.ts-score.good { color: #67c23a; }
.ts-score.warn { color: #e6a23c; }
.ts-score.bad { color: #f56c6c; }
.ts-warn {
  font-size: 12px; color: #e6a23c;
  padding: 8px 12px; border-radius: 8px;
  background: rgba(230,162,60,.08);
  border: 1px solid rgba(230,162,60,.2);
}

.ts-actions { display: flex; gap: 10px; flex-wrap: wrap; }
.ts-actions :deep(.el-button) {
  background: color-mix(in srgb, var(--surface, #ffffff) 6%, transparent);
  border: 1px solid rgba(255,255,255,0.06);
  color: var(--text-secondary);
  border-radius: 10px;
}
.ts-actions :deep(.el-button--primary) {
  background: var(--brand);
  border-color: var(--brand);
  color: var(--brand-on);
  font-weight: 600;
}
.ts-hint { font-size: 11.5px; color: var(--text-muted); line-height: 1.6; text-align: center; }
</style>