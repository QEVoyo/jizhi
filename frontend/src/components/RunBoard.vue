<template>
  <section class="rb-card">
    <header class="rb-head">
      <div>
        <h2 class="rb-title">任务</h2>
        <p class="rb-sub">一次运行就是一次任务 · 排队可拖拽 · 与智能体中心同一份数据</p>
      </div>
      <div class="rb-head-right">
        <span v-if="activeRuns.length" class="rb-count">{{ activeRuns.length }} 未结束</span>
        <button class="rb-refresh" :disabled="runState.loading" @click="refresh">
          {{ runState.loading ? '刷新中…' : '刷新' }}
        </button>
      </div>
    </header>

    <p v-if="runState.error" class="rb-error">{{ runState.error }}</p>

    <!-- 排队 / 已暂停：只有这里能拖 -->
    <div v-if="queuedRuns.length" class="rb-queue">
      <div class="rb-section-head">
        <span>排队</span>
        <span class="rb-section-note">拖动调整顺序 · 同一时间只跑一个</span>
      </div>
      <div class="rb-queue-list">
        <div
          v-for="(r, i) in queuedRuns"
          :key="r.id"
          class="rb-queue-item"
          :class="{ dragging: dragIndex === i, over: overIndex === i && dragIndex !== i }"
          draggable="true"
          @dragstart="onDragStart(i, $event)"
          @dragover.prevent="onDragOver(i)"
          @drop.prevent="onDrop(i)"
          @dragend="onDragEnd"
        >
          <span class="rb-grip" title="拖动排序">⋮⋮</span>
          <span class="rb-pos">{{ i + 1 }}</span>
          <span class="rb-status" :class="r.status">{{ statusText(r.status) }}</span>
          <span class="rb-q-title">{{ titleOf(r) }}</span>
          <span class="rb-pct">{{ r.progress || 0 }}%</span>
          <div class="rb-q-actions">
            <button v-if="canResumeRun(r)" :disabled="busy[r.id]" @click="resume(r)">继续</button>
            <button v-else-if="canPauseRun(r)" :disabled="busy[r.id]" @click="pause(r)">暂停</button>
            <button class="ghost" :disabled="busy[r.id]" @click="$emit('open', r)">看轨迹</button>
            <button class="ghost" :disabled="busy[r.id]" @click="openCollab(r)">协作图</button>
            <button class="danger" :disabled="busy[r.id]" @click="remove(r)">删除</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 进行中 -->
    <div v-if="workingRuns.length" class="rb-active">
      <article v-for="r in workingRuns" :key="r.id" class="rb-run">
        <div class="rb-run-top">
          <span class="rb-status" :class="r.status">{{ statusText(r.status) }}</span>
          <span class="rb-wf">{{ workflowName(r) }}</span>
          <span class="rb-pct">{{ r.progress || 0 }}%</span>
        </div>
        <h3 class="rb-run-title">{{ titleOf(r) }}</h3>
        <p class="rb-stage">{{ stageText(r) }}</p>
        <div class="rb-bar"><span :style="{ width: (r.progress || 0) + '%' }"></span></div>
        <div class="rb-actions">
          <button v-if="r.status === 'awaiting_confirm'" @click="goConfirm(r)">去确认</button>
          <button v-else-if="r.link" @click="openLink(r)">查看结果</button>
          <button class="ghost" @click="$emit('open', r)">看轨迹</button>
          <button class="ghost" @click="openCollab(r)">协作图</button>
          <button
            v-if="canPauseRun(r)"
            class="ghost"
            :disabled="busy[r.id]"
            @click="pause(r)"
          >{{ r.stage === 'pausing' ? '暂停中…' : '暂停' }}</button>
          <button class="danger" :disabled="busy[r.id]" @click="cancel(r)">
            {{ busy[r.id] === 'cancel' ? '取消中…' : '取消' }}
          </button>
        </div>
      </article>
    </div>

    <!-- 空态 -->
    <div v-if="!activeRuns.length" class="rb-empty">
      <div class="rb-empty-icon">◎</div>
      <div>
        <p class="rb-empty-title">当前没有进行中的任务</p>
        <p class="rb-empty-sub">拖一份资料给小基，或者去工作流里跑一次团队出题。</p>
      </div>
      <div class="rb-empty-actions">
        <button @click="upload">传资料出题</button>
        <button class="ghost" @click="$emit('browse')">去工作流看看</button>
      </div>
    </div>

    <!-- 最近 -->
    <div v-if="recentRuns.length" class="rb-recent">
      <div class="rb-recent-head">
        <span>最近运行</span>
        <span class="rb-recent-note">点击看节点轨迹</span>
      </div>
      <div v-for="r in recentRuns" :key="r.id" class="rb-row-wrap">
        <button class="rb-row" @click="$emit('open', r)">
          <span class="rb-dot" :class="r.status"></span>
          <span class="rb-row-title">{{ titleOf(r) }}</span>
          <span class="rb-row-wf">{{ workflowName(r) }}</span>
          <span class="rb-row-time">{{ fmtTime(r.created_at) }}</span>
          <span class="rb-row-status" :class="r.status">{{ statusText(r.status) }}</span>
        </button>
        <div class="rb-row-actions">
          <button v-if="r.link" class="ghost" @click="openLink(r)">看结果</button>
          <button class="ghost" @click="openCollab(r)">协作图</button>
          <button v-if="canRetryRun(r)" class="ghost" :disabled="busy[r.id]" @click="retry(r)">重试</button>
          <button v-if="canDeleteRun(r)" class="ghost danger-text" :disabled="busy[r.id]" @click="remove(r)">删除</button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { reactive, ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  runState, activeRuns, queuedRuns, workingRuns, recentRuns,
  refresh, startRunPolling, cancelRunById, pauseRunById, resumeRunById,
  retryRunById, deleteRunById, reorderRunIds,
  canPauseRun, canResumeRun, canDeleteRun, canRetryRun,
} from '@/stores/runStore'
import { openXiaojiPopup } from '@/xiaoji/popupStore'
import { openAgentPanel } from '@/stores/agentPanel'

const props = defineProps({ userId: { type: String, default: '' } })
defineEmits(['open', 'browse'])

const router = useRouter()
const busy = reactive({})
const dragIndex = ref(-1)
const overIndex = ref(-1)

onMounted(() => { if (props.userId) startRunPolling(props.userId) })
watch(() => props.userId, (v) => { if (v) startRunPolling(v) })

const KIND_NAMES = {
  upload_parse: '资料解析',
  upload_generate: '资料出题',
  file_to_questions: '上传出题',
  question_gen: '团队出题',
  evaluate: '团队评估',
  tuning_debate: '调参圆桌',
  video_generate: '视频生成',
}

function workflowName(r) {
  return KIND_NAMES[r.kind] || KIND_NAMES[r.workflow_key] || r.workflow_key || '任务'
}

function titleOf(r) {
  return r.title || workflowName(r)
}

const STATUS_TEXT = {
  queued: '排队中',
  paused: '已暂停',
  running: '运行中',
  awaiting_confirm: '待确认',
  confirmed: '已确认',
  completed: '已完成',
  failed: '失败',
  cancelled: '已取消',
}

function statusText(s) { return STATUS_TEXT[s] || s || '' }

const STAGE_TEXT = {
  queued: '等待前面的任务完成',
  paused: '已暂停，点「继续」重新排队',
  pausing: '正在暂停，等当前题完成',
  extracting: '提取文字 / 识别扫描页',
  profiling: '判断资料类型与可出题比例',
  seeding: '抽象可出题点',
  awaiting_confirm: '等你确认要生成哪些点',
  confirmed: '已确认，等待生成',
  generating: '生成题目中',
  crosschecking: '独立复核中',
  saving: '建题集 / 写生成历史',
  cancelling: '正在取消',
  ready: '已完成',
  failed: '失败',
  cancelled: '已取消',
}

function stageText(r) {
  return STAGE_TEXT[r.stage] || STAGE_TEXT[r.status] || ''
}

function fmtTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ''
  const now = Date.now()
  const diff = now - d.getTime()
  if (diff < 60_000) return '刚刚'
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)} 分钟前`
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)} 小时前`
  return d.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' })
}

function goConfirm(r) {
  const jobId = r.input?.job_id
  if (jobId) openXiaojiPopup({ mode: 'upload', jobId })
  else ElMessage.warning('这条任务没有关联的上传文件')
}

function upload() {
  openXiaojiPopup({ mode: 'upload' })
}

function openLink(r) {
  if (r.link) router.push(r.link)
}

function openCollab(r) {
  if (r?.id) openAgentPanel(r.id)
}

function apiError(e, fallback) {
  return e?.response?.data?.detail || fallback
}

async function runAction(r, key, fn, okText) {
  if (!r?.id || busy[r.id]) return
  busy[r.id] = key
  try {
    const res = await fn(r.id)
    ElMessage.success(res?.status === 'pausing'
      ? '已请求暂停，等当前题完成后停下'
      : (okText || '已完成'))
  } catch (e) {
    ElMessage.error(apiError(e, '操作失败'))
  } finally {
    busy[r.id] = ''
  }
}

const cancel = (r) => runAction(r, 'cancel', cancelRunById, '已请求取消')
const pause = (r) => runAction(r, 'pause', pauseRunById, '已暂停')
const resume = (r) => runAction(r, 'resume', resumeRunById, '已继续，重新进入队列')
const retry = (r) => runAction(r, 'retry', retryRunById, '已重新排队')

async function remove(r) {
  if (!r?.id || busy[r.id]) return
  try {
    await ElMessageBox.confirm(
      '只删除任务记录，已经生成的题目/题集不会被删除。确定删除吗？',
      '删除任务',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' },
    )
  } catch {
    return
  }
  busy[r.id] = 'delete'
  try {
    await deleteRunById(r.id)
    ElMessage.success('任务已删除')
  } catch (e) {
    ElMessage.error(apiError(e, '删除失败'))
  } finally {
    busy[r.id] = ''
  }
}

// ---------- 拖拽排序（只在排队区） ----------
function onDragStart(i, e) {
  dragIndex.value = i
  overIndex.value = i
  if (e?.dataTransfer) {
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('text/plain', String(i))
  }
}

function onDragOver(i) {
  if (dragIndex.value >= 0) overIndex.value = i
}

function onDragEnd() {
  dragIndex.value = -1
  overIndex.value = -1
}

async function onDrop(i) {
  const from = dragIndex.value
  onDragEnd()
  if (from < 0 || from === i) return
  const list = [...queuedRuns.value]
  if (!list[from]) return
  const [item] = list.splice(from, 1)
  list.splice(i, 0, item)
  // 乐观更新：先把 queue_pos 改掉，请求失败再整体刷新
  list.forEach((r, idx) => {
    const target = runState.runs.find(x => x.id === r.id)
    if (target) target.queue_pos = idx
  })
  try {
    await reorderRunIds(list.map(r => r.id))
  } catch (e) {
    ElMessage.error(apiError(e, '排序失败，已刷新'))
    refresh()
  }
}
</script>

<style scoped>
.rb-card {
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent);
  border: 1px solid rgba(255, 255, 255, .08);
  border-radius: 18px;
  padding: 20px 22px;
  backdrop-filter: blur(20px);
  margin-bottom: 18px;
}
[data-theme="dark"] .rb-card { background: color-mix(in srgb, var(--surface, #ffffff) 2%, transparent); }
.rb-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }
.rb-title { font-size: 17px; font-weight: 700; color: var(--text-primary); margin: 0; }
.rb-sub { font-size: 12px; color: var(--text-muted); margin: 4px 0 0; }
.rb-head-right { display: flex; align-items: center; gap: 8px; }
.rb-count {
  font-size: 11.5px; font-weight: 700; color: var(--brand-bright);
  background: color-mix(in srgb, var(--brand) 14%, transparent);
  padding: 3px 10px; border-radius: 999px;
}
.rb-refresh {
  font-size: 12px; font-family: inherit; cursor: pointer;
  padding: 5px 12px; border-radius: 8px; color: var(--text-secondary);
  border: 1px solid var(--border-color); background: transparent;
}
.rb-refresh:disabled { opacity: .5; cursor: not-allowed; }
.rb-error { margin: 10px 0 0; font-size: 12px; color: #f56c6c; }

.rb-queue { margin-top: 16px; }
.rb-section-head {
  display: flex; align-items: center; justify-content: space-between;
  font-size: 12px; font-weight: 650; color: var(--text-secondary); margin-bottom: 8px;
}
.rb-section-note { font-size: 11px; font-weight: 400; color: var(--text-muted); }
.rb-queue-list { display: flex; flex-direction: column; gap: 7px; }
.rb-queue-item {
  display: flex; align-items: center; gap: 9px;
  border: 1px solid var(--line-soft); border-radius: 11px;
  background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent);
  padding: 8px 10px; transition: border-color .15s, opacity .15s, transform .15s;
}
.rb-queue-item.dragging { opacity: .45; }
.rb-queue-item.over { border-color: var(--brand); transform: translateY(-1px); }
.rb-grip {
  cursor: grab; color: var(--text-muted); font-size: 12px;
  letter-spacing: -2px; user-select: none;
}
.rb-pos {
  width: 18px; text-align: center; font-size: 11px; color: var(--text-muted);
  font-variant-numeric: tabular-nums;
}
.rb-q-title {
  flex: 1; min-width: 0; font-size: 12.5px; color: var(--text-primary);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.rb-q-actions { display: flex; gap: 6px; flex-wrap: wrap; }
.rb-q-actions button {
  font-size: 11px; font-family: inherit; cursor: pointer;
  padding: 4px 9px; border-radius: 7px; font-weight: 600;
  border: 1px solid color-mix(in srgb, var(--brand) 34%, transparent);
  background: color-mix(in srgb, var(--brand) 12%, transparent);
  color: var(--brand-bright);
}
.rb-q-actions button.ghost {
  border-color: var(--border-color); background: transparent; color: var(--text-secondary);
}
.rb-q-actions button.danger {
  border-color: rgba(245, 108, 108, .3); background: rgba(245, 108, 108, .08); color: #f56c6c;
}
.rb-q-actions button:disabled { opacity: .5; cursor: not-allowed; }

.rb-active {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 12px; margin-top: 16px;
}
.rb-run {
  border: 1px solid var(--line-soft); border-radius: 14px;
  background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent);
  padding: 14px 15px;
}
.rb-run-top { display: flex; align-items: center; gap: 8px; }
.rb-status {
  font-size: 11px; padding: 2px 8px; border-radius: 999px;
  color: var(--text-secondary); background: rgba(128, 128, 128, .12);
}
.rb-status.running { color: #d48806; background: rgba(250, 178, 25, .14); }
.rb-status.paused { color: #8b5cf6; background: rgba(139, 92, 246, .14); }
.rb-status.awaiting_confirm { color: var(--brand-bright); background: color-mix(in srgb, var(--brand) 14%, transparent); }
.rb-status.completed { color: #0ca30c; background: rgba(12, 163, 12, .12); }
.rb-status.failed { color: #f56c6c; background: rgba(245, 108, 108, .12); }
.rb-wf { font-size: 11px; color: var(--text-muted); }
.rb-pct { margin-left: auto; font-size: 12px; font-weight: 700; color: var(--text-primary); font-variant-numeric: tabular-nums; }
.rb-run-title {
  margin: 9px 0 3px; font-size: 14px; font-weight: 650; color: var(--text-primary);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.rb-stage { margin: 0 0 9px; font-size: 11.5px; color: var(--text-muted); min-height: 17px; }
.rb-bar { height: 6px; border-radius: 3px; overflow: hidden; background: rgba(128, 128, 128, .12); }
.rb-bar span {
  display: block; height: 100%; border-radius: 3px;
  background: linear-gradient(90deg, var(--brand), var(--brand-bright));
  transition: width .5s cubic-bezier(.4, 0, .2, 1);
}
.rb-actions { display: flex; gap: 7px; margin-top: 11px; flex-wrap: wrap; }
.rb-actions button {
  font-size: 11.5px; font-family: inherit; cursor: pointer;
  padding: 5px 11px; border-radius: 7px; font-weight: 600;
  border: 1px solid color-mix(in srgb, var(--brand) 38%, transparent);
  background: color-mix(in srgb, var(--brand) 13%, transparent);
  color: var(--brand-bright);
}
.rb-actions button.ghost {
  border-color: var(--border-color); background: transparent; color: var(--text-secondary);
}
.rb-actions button.danger {
  border-color: rgba(245, 108, 108, .3); background: rgba(245, 108, 108, .08); color: #f56c6c;
}
.rb-actions button:disabled { opacity: .5; cursor: not-allowed; }

.rb-empty {
  display: flex; align-items: center; gap: 14px; flex-wrap: wrap;
  margin-top: 16px; padding: 16px; border-radius: 14px;
  border: 1px dashed var(--line-soft);
  background: color-mix(in srgb, var(--surface, #ffffff) 2%, transparent);
}
.rb-empty-icon { font-size: 26px; color: var(--text-muted); }
.rb-empty-title { margin: 0; font-size: 13.5px; font-weight: 650; color: var(--text-primary); }
.rb-empty-sub { margin: 3px 0 0; font-size: 12px; color: var(--text-muted); }
.rb-empty-actions { margin-left: auto; display: flex; gap: 8px; }
.rb-empty-actions button {
  font-size: 12px; font-family: inherit; cursor: pointer; padding: 6px 13px;
  border-radius: 8px; font-weight: 600;
  border: 1px solid color-mix(in srgb, var(--brand) 38%, transparent);
  background: color-mix(in srgb, var(--brand) 13%, transparent);
  color: var(--brand-bright);
}
.rb-empty-actions button.ghost { border-color: var(--border-color); background: transparent; color: var(--text-secondary); }

.rb-recent { margin-top: 16px; border-top: 1px solid var(--line-soft); padding-top: 12px; }
.rb-recent-head { display: flex; justify-content: space-between; font-size: 11.5px; color: var(--text-muted); margin-bottom: 6px; }
.rb-recent-note { font-size: 11px; color: var(--text-muted); }
.rb-row-wrap { display: flex; align-items: center; gap: 6px; }
.rb-row {
  flex: 1; min-width: 0; display: flex; align-items: center; gap: 9px;
  border: none; background: transparent; font-family: inherit;
  padding: 8px 6px; border-radius: 8px; cursor: pointer; text-align: left;
}
.rb-row:hover { background: color-mix(in srgb, var(--surface, #ffffff) 5%, transparent); }
[data-theme="light"] .rb-row:hover { background: rgba(15, 23, 42, .04); }
.rb-dot { width: 7px; height: 7px; border-radius: 50%; background: rgba(128, 128, 128, .45); flex-shrink: 0; }
.rb-dot.completed { background: #0ca30c; }
.rb-dot.failed { background: #f56c6c; }
.rb-dot.cancelled { background: rgba(128, 128, 128, .45); }
.rb-row-title { font-size: 12.5px; color: var(--text-primary); flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.rb-row-wf { font-size: 11px; color: var(--text-muted); width: 68px; flex-shrink: 0; }
.rb-row-time { font-size: 11px; color: var(--text-muted); width: 62px; flex-shrink: 0; text-align: right; }
.rb-row-status { font-size: 11px; color: var(--text-secondary); width: 54px; flex-shrink: 0; text-align: right; }
.rb-row-status.failed { color: #f56c6c; }
.rb-row-status.completed { color: #0ca30c; }
.rb-row-actions { display: flex; gap: 4px; flex-shrink: 0; }
.rb-row-actions button {
  font-size: 10.5px; font-family: inherit; cursor: pointer;
  padding: 3px 7px; border-radius: 6px; color: var(--text-secondary);
  border: 1px solid var(--border-color); background: transparent;
}
.rb-row-actions button:disabled { opacity: .5; cursor: not-allowed; }
.rb-row-actions .danger-text { color: #f56c6c; border-color: rgba(245, 108, 108, .25); }
</style>
