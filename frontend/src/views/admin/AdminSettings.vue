<!--
  系统信息

  后端 `GET /admin/settings` 一直存在（返回题库总量 / 考纲数 / 各 API 提供方是否已配置），
  但前端此前**连封装都没有、全站零调用**，后台侧边栏也没有入口 ——
  一个能用的端点等于废的。2026-09-30 补上这一页。

  注意这里**只读**：不提供任何"在这里改配置"的入口。
  密钥类配置走服务器 .env（改了要重启服务），放在后台页面上改既不安全也不生效。
-->
<template>
  <div class="admin-settings">
    <div class="page-header">
      <h2 class="page-title">系统信息</h2>
      <el-button size="small" text @click="load" :loading="loading">
        <i class="fas fa-rotate-right"></i> 刷新
      </el-button>
    </div>

    <AdminLoading :visible="loading" text="读取系统信息..." />

    <template v-if="!loading">
      <div class="info-grid">
        <div class="info-card">
          <span class="info-label">题库总量</span>
          <span class="info-value">{{ settings.question_bank_count ?? '-' }}</span>
          <span class="info-hint">全部考纲合计</span>
        </div>
        <div class="info-card">
          <span class="info-label">已加载考纲</span>
          <span class="info-value">{{ settings.syllabus_count ?? '-' }}</span>
          <span class="info-hint">个</span>
        </div>
      </div>

      <h3 class="section-title">API 提供方</h3>
      <div class="provider-list">
        <div v-for="p in providers" :key="p.key" class="provider-row">
          <span class="provider-name">{{ p.label }}</span>
          <span class="provider-usage">{{ p.usage }}</span>
          <span class="provider-status" :class="p.ok ? 'on' : 'off'">
            <i :class="p.ok ? 'fas fa-circle-check' : 'fas fa-circle-xmark'"></i>
            {{ p.ok ? '已配置' : '未配置' }}
          </span>
        </div>
      </div>

      <p class="footnote">
        这里的开关状态来自服务器端 <code>.env</code>。要变更请改配置文件并重启服务 ——
        后台页面上改既不安全、也不会生效。
      </p>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getSystemSettings } from '@/api/admin'
import AdminLoading from '@/components/admin/AdminLoading.vue'

const loading = ref(false)
const settings = ref({})

// 后端只回 { deepseek: bool, volc: bool, xunfei: bool }，文案在前端补
const PROVIDER_META = [
  { key: 'deepseek', label: 'DeepSeek', usage: '文本生成 / 出题 / 批改' },
  { key: 'volc', label: '火山引擎', usage: '（已收编至 DeepSeek，保留备查）' },
  { key: 'xunfei', label: '讯飞', usage: '语音识别 ASR' },
]

const providers = computed(() =>
  PROVIDER_META.map(p => ({ ...p, ok: !!settings.value.api_providers?.[p.key] }))
)

async function load() {
  loading.value = true
  try {
    settings.value = await getSystemSettings()
  } catch (e) {
    // 后端现在对上游故障会明确报 502，把原因透出来，别只说"加载失败"
    ElMessage.error(e?.response?.data?.detail || '读取系统信息失败')
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.admin-settings { max-width: 760px; }

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
}
.page-title { font-size: 20px; font-weight: 600; color: var(--text-primary); margin: 0; }

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 14px;
  margin-bottom: 26px;
}
.info-card {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 18px 20px;
  border-radius: 14px;
  background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent);
  border: 1px solid color-mix(in srgb, var(--text-primary) 6%, transparent);
}
.info-label { font-size: 12px; color: var(--text-muted); }
.info-value { font-size: 26px; font-weight: 600; color: var(--text-primary); line-height: 1.2; }
.info-hint { font-size: 11px; color: var(--text-muted); }

.section-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  margin: 0 0 10px;
}

.provider-list {
  border-radius: 14px;
  overflow: hidden;
  border: 1px solid color-mix(in srgb, var(--text-primary) 6%, transparent);
  background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent);
}
.provider-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 18px;
  border-bottom: 1px solid color-mix(in srgb, var(--text-primary) 4%, transparent);
}
.provider-row:last-child { border-bottom: none; }
.provider-name { font-size: 13px; color: var(--text-primary); width: 96px; flex-shrink: 0; }
.provider-usage { font-size: 12px; color: var(--text-muted); flex: 1; min-width: 0; }
.provider-status { font-size: 12px; display: flex; align-items: center; gap: 5px; flex-shrink: 0; }
.provider-status.on { color: #67c23a; }
.provider-status.off { color: var(--text-muted); }

.footnote {
  margin-top: 16px;
  font-size: 12px;
  line-height: 1.7;
  color: var(--text-muted);
}
.footnote code {
  padding: 1px 5px;
  border-radius: 4px;
  background: color-mix(in srgb, var(--surface, #ffffff) 8%, transparent);
}
</style>
