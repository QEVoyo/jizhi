import { reactive, computed } from 'vue'
import {
  listRuns, cancelRun, pauseRun, resumeRun, retryRun, deleteRun, reorderRuns,
} from '@/api/agents'

/**
 * 统一的运行/任务状态（2026-11-02 任务控制层）
 *
 * 一条 agent_run 就是一次任务。这里负责：
 *   1. 轮询 /agents/runs；
 *   2. 派生「排队 / 进行中 / 最近」三个列表；
 *   3. 暂停、继续、取消、删除、重试、拖拽排序；
 *   4. 状态从活跃 → 终态时派发一次事件，给小基弹窗用。
 *
 * 不新建 /tasks 接口，也不新建任务中心页面。
 */

export const ACTIVE_STATUSES = ['queued', 'paused', 'running', 'awaiting_confirm', 'confirmed']
export const TERMINAL_STATUSES = ['completed', 'failed', 'cancelled']
export const QUEUE_STATUSES = ['queued', 'paused']

const ACTIVE = new Set(ACTIVE_STATUSES)
const TERMINAL = new Set(TERMINAL_STATUSES)
const QUEUEABLE = new Set(QUEUE_STATUSES)

export const runState = reactive({
  userId: '',
  runs: [],
  loading: false,
  error: '',
  updatedAt: 0,
})

export const activeRuns = computed(() =>
  runState.runs.filter(r => ACTIVE.has(r.status)))

// 拖拽只在这两个状态里生效；排序以 queue_pos 为准
export const queuedRuns = computed(() =>
  runState.runs
    .filter(r => QUEUEABLE.has(r.status))
    .sort((a, b) => (Number(a.queue_pos) || 0) - (Number(b.queue_pos) || 0)
      || String(a.created_at || '').localeCompare(String(b.created_at || ''))))

export const workingRuns = computed(() =>
  activeRuns.value.filter(r => !QUEUEABLE.has(r.status)))

export const recentRuns = computed(() =>
  runState.runs.filter(r => !ACTIVE.has(r.status)).slice(0, 20))

const seen = new Map()
let timer = null
let polling = false
let refreshSeq = 0

function schedule(delay) {
  if (!runState.userId) return
  clearTimeout(timer)
  timer = setTimeout(tick, delay)
}

async function tick() {
  if (!runState.userId) return
  await refresh()
  // 有活跃任务时 3s 一刷，闲时 12s —— 不让空闲页一直打接口
  schedule(activeRuns.value.length ? 3000 : 12000)
}

export async function refresh() {
  if (!runState.userId || polling) return
  const uid = runState.userId
  const seq = ++refreshSeq
  polling = true
  runState.loading = true
  try {
    // 50 条足够覆盖「最近完成」；也避免活跃任务被一批旧 run 挤出列表
    const runs = await listRuns(uid, 50)
    if (seq !== refreshSeq || runState.userId !== uid) return
    const firstLoad = seen.size === 0
    for (const r of runs || []) {
      const before = seen.get(r.id)
      if (!firstLoad && before && ACTIVE.has(before) && TERMINAL.has(r.status)) {
        window.dispatchEvent(new CustomEvent('xiaoji-run-done', { detail: r }))
      }
      seen.set(r.id, r.status)
    }
    runState.runs = Array.isArray(runs) ? runs : []
    runState.error = ''
    runState.updatedAt = Date.now()
  } catch (e) {
    if (seq === refreshSeq) runState.error = '任务状态读取失败'
  } finally {
    polling = false
    if (seq === refreshSeq) runState.loading = false
  }
}

export function startRunPolling(userId) {
  if (!userId) return
  if (runState.userId !== userId) {
    refreshSeq += 1
    runState.userId = userId
    runState.runs = []
    runState.loading = false
    polling = false
    seen.clear()
    clearTimeout(timer)
    timer = null
  }
  if (!timer) tick()
}

export function stopRunPolling() {
  refreshSeq += 1
  clearTimeout(timer)
  timer = null
  polling = false
  runState.userId = ''
  runState.runs = []
  runState.loading = false
  runState.error = ''
  seen.clear()
}

/** 服务端返回的旧状态不能覆盖新状态；trackRun 也不能把进度回退 */
function mergeRun(existing, incoming) {
  if (!existing) return { ...incoming }
  const next = { ...incoming }
  // 终态不能被合成数据改回活跃；已开跑也不能被改回排队
  if (TERMINAL.has(existing.status) && !TERMINAL.has(next.status)) {
    next.status = existing.status
    next.stage = existing.stage
    next.progress = existing.progress
  } else if (existing.status === 'running' && next.status === 'queued') {
    next.status = 'running'
    next.stage = existing.stage
  }
  if (!TERMINAL.has(next.status) && next.status !== 'paused'
      && (Number(existing.progress) || 0) > (Number(next.progress) || 0)) {
    next.progress = existing.progress
  }
  return { ...existing, ...next }
}

/** 上传/生成接口返回后立刻把这条 run 放进列表，不必等下一次轮询 */
export function trackRun(run) {
  if (!run?.id) return
  const i = runState.runs.findIndex(r => r.id === run.id)
  const merged = mergeRun(i >= 0 ? runState.runs[i] : null,
    { status: 'queued', progress: 0, ...run })
  if (i >= 0) runState.runs[i] = merged
  else runState.runs.unshift(merged)
  seen.set(merged.id, merged.status || 'queued')
}

export function isActiveRun(run) {
  return !!run && ACTIVE.has(run.status)
}

export function isPausedRun(run) {
  return run?.status === 'paused'
}

export function canPauseRun(run) {
  if (!run) return false
  if (run.stage === 'pausing') return false
  if (run.status === 'queued' || run.status === 'confirmed') return true
  // 只有「上传生成」支持在题目边界暂停；解析和单次调用只能取消
  return run.status === 'running' && run.kind === 'upload_generate'
}

export function canResumeRun(run) {
  return run?.status === 'paused'
}

export function canDeleteRun(run) {
  return !!run && ['queued', 'paused', 'awaiting_confirm', 'confirmed',
    'completed', 'failed', 'cancelled'].includes(run.status)
}

export function canRetryRun(run) {
  return !!run && ['failed', 'cancelled'].includes(run.status)
}

async function act(fn, runId) {
  if (!runState.userId || !runId) return false
  await fn(runId, runState.userId)
  await refresh()
  return true
}

export const cancelRunById = (runId) => act(cancelRun, runId)
export const pauseRunById = (runId) => act(pauseRun, runId)
export const resumeRunById = (runId) => act(resumeRun, runId)
export const retryRunById = (runId) => act(retryRun, runId)
export const deleteRunById = (runId) => act(deleteRun, runId)

export async function reorderRunIds(ids) {
  if (!runState.userId || !ids?.length) return false
  await reorderRuns(ids, runState.userId)
  await refresh()
  return true
}
