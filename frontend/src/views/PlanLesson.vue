<!--
  自定义计划 · 学习内容页（2026-10-01）

  计划详情里那条「学习内容」原本只显示一段 100-200 字的概述（AI prompt 里
  写死就是这个长度）—— 用户的原话是「应该是要详细教学，而不是概述知识点」。

  所以：列表里只露**前两行**，点进来才是**完整教学正文**。
  正文**按需生成**（`GET /learning-plan/task/{id}/lesson`，首次生成后缓存），
  不在建计划时一次生成 N 天 —— 那会撑爆响应（这条链路前端 90 秒超时）。

  读完点「学完了」→ 把这行任务标 completed → 回计划详情。
-->
<template>
  <div class="pl-page">
    <div class="pl-topbar">
      <button class="glass-btn" @click="goBack">
        <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M19 12H5M12 19l-7-7 7-7"/>
        </svg>
        返回计划
      </button>
      <h1>📖 {{ topic || '学习内容' }}</h1>
    </div>

    <div v-if="loading" class="pl-card glass-panel">
      <div class="pl-loading">
        <div class="loading-pulse"></div>
        <div>
          <b>正在为你写这一份讲解…</b>
          <p>第一次打开需要现生成（约十几秒），生成后会存下来，下次秒开。</p>
        </div>
      </div>
    </div>

    <div v-else-if="lesson" class="pl-card glass-panel">
      <p v-if="lesson.summary" class="pl-summary">{{ lesson.summary }}</p>

      <section v-for="(s, i) in (lesson.sections || [])" :key="i" class="pl-sec">
        <h3><span class="pl-no">{{ i + 1 }}</span>{{ s.heading }}</h3>
        <p class="pl-body">{{ s.body }}</p>
        <div v-if="s.example" class="pl-example">
          <span class="pl-example-tag">例</span>
          <p>{{ s.example }}</p>
        </div>
      </section>

      <section v-if="(lesson.key_points || []).length" class="pl-sec">
        <h3>🔑 必须记住</h3>
        <ul class="pl-list"><li v-for="(k, i) in lesson.key_points" :key="i">{{ k }}</li></ul>
      </section>

      <section v-if="(lesson.common_mistakes || []).length" class="pl-sec">
        <h3>⚠️ 常见错误</h3>
        <ul class="pl-list pl-warn"><li v-for="(m, i) in lesson.common_mistakes" :key="i">{{ m }}</li></ul>
      </section>

      <div class="pl-actions">
        <button class="btn-primary" :disabled="marking" @click="finish">
          {{ marking ? '保存中…' : '✅ 学完了，返回计划' }}
        </button>
      </div>
    </div>

    <div v-else class="pl-card glass-panel pl-fail">
      <p>正文没能生成出来。</p>
      <button class="glass-btn" @click="load">重试一次</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'
import { updateTaskStatus } from '@/api/learningPlan'

const route = useRoute()
const router = useRouter()

const taskId = route.params.taskId
const planId = route.query.plan_id || ''
const returnTo = route.query.return_to || (planId ? `/plan-detail/${planId}` : '/learning-plan')

const loading = ref(true)
const lesson = ref(null)
const topic = ref('')
const marking = ref(false)

async function load() {
  loading.value = true
  lesson.value = null
  try {
    const res = await request.get(`/learning-plan/task/${taskId}/lesson`, { timeout: 120000 })
    lesson.value = res.data?.lesson || null
    topic.value = res.data?.topic || ''
  } catch (e) {
    console.error('学习正文加载失败:', e)
    ElMessage.error(e?.response?.data?.detail || '正文生成失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

function goBack() { router.push(returnTo) }

async function finish() {
  marking.value = true
  try {
    // 标完成 —— 用已有的 task/status 端点（它会顺带重算计划进度）
    if (planId) {
      await updateTaskStatus({ task_id: taskId, status: 'completed', plan_id: planId })
    }
    router.push(returnTo)
  } catch (e) {
    console.error('标记完成失败:', e)
    ElMessage.warning('没能标记完成，稍后再试')
  } finally {
    marking.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.pl-page { height: calc(100vh - var(--jz-top, 0px)); overflow-y: auto; padding: 20px 28px 60px; max-width: 860px; margin: 0 auto; }
.pl-topbar { display: flex; align-items: center; gap: 14px; margin-bottom: 18px; flex-wrap: wrap; }
.pl-topbar h1 { font-size: 20px; font-weight: 700; color: var(--text-primary); margin: 0; }

.pl-card { padding: 26px 30px; border-radius: 16px; }

.pl-loading { display: flex; align-items: center; gap: 16px; color: var(--text-secondary); }
.pl-loading b { color: var(--text-primary); }
.pl-loading p { margin-top: 6px; font-size: 12.5px; color: var(--text-muted); }
.loading-pulse { width: 34px; height: 34px; border-radius: 50%; flex: none;
  background: color-mix(in srgb, var(--brand) 35%, transparent); animation: pl-pulse 1.4s ease-in-out infinite; }
@keyframes pl-pulse { 0%,100% { transform: scale(.8); opacity: .5 } 50% { transform: scale(1.1); opacity: 1 } }

.pl-summary { font-size: 14px; color: var(--brand-bright); margin: 0 0 20px; padding-left: 12px;
  border-left: 3px solid var(--brand); }

.pl-sec { margin-bottom: 26px; }
.pl-sec h3 { display: flex; align-items: center; gap: 9px; font-size: 16px; font-weight: 700;
  color: var(--text-primary); margin: 0 0 10px; }
.pl-no { display: inline-flex; align-items: center; justify-content: center; width: 22px; height: 22px;
  border-radius: 7px; font-size: 12px; background: color-mix(in srgb, var(--brand) 20%, transparent);
  color: var(--brand-bright); flex: none; }
/* 正文行高放宽 —— 这是要读的东西，不是 UI 文案 */
.pl-body { font-size: 14.5px; line-height: 1.95; color: var(--text-secondary); margin: 0;
  white-space: pre-wrap; }

.pl-example { margin-top: 12px; padding: 12px 16px; border-radius: 10px;
  background: color-mix(in srgb, var(--brand) 7%, transparent);
  border-left: 3px solid color-mix(in srgb, var(--brand) 45%, transparent); }
.pl-example-tag { font-size: 11px; font-weight: 700; color: var(--brand-bright); }
.pl-example p { margin: 4px 0 0; font-size: 14px; line-height: 1.9; color: var(--text-secondary); white-space: pre-wrap; }

.pl-list { margin: 0; padding-left: 20px; }
.pl-list li { font-size: 14px; line-height: 1.9; color: var(--text-secondary); }
.pl-warn li { color: #e6a23c; }

.pl-actions { display: flex; justify-content: center; margin-top: 30px; }
.pl-fail { text-align: center; color: var(--text-muted); }
</style>
