<template>
  <div class="adv">
    <h2 class="adv-title">视频库管理</h2>

    <!-- 概览 -->
    <div v-if="stats" class="adv-stats">
      <div class="adv-stat"><b>{{ stats.total }}</b><span>视频总数</span></div>
      <div class="adv-stat"><b>{{ stats.public_ready }}</b><span>广场在播</span></div>
      <div class="adv-stat"><b class="warn">{{ stats.pending_review }}</b><span>待审核</span></div>
      <div class="adv-stat"><b>{{ stats.generating }}</b><span>生成中</span></div>
      <div class="adv-stat"><b class="bad">{{ stats.failed }}</b><span>失败</span></div>
      <div class="adv-stat"><b>{{ fmt(stats.total_views) }}</b><span>总播放</span></div>
      <div class="adv-stat"><b class="warn">{{ stats.pending_reports }}</b><span>待处理举报</span></div>
    </div>

    <div class="adv-tabs">
      <button v-for="t in tabs" :key="t.key" class="adv-tab" :class="{ on: tab === t.key }" @click="tab = t.key">
        {{ t.label }}
      </button>
      <span class="adv-refresh" @click="reloadAll">刷新</span>
    </div>

    <!-- 视频列表 -->
    <div v-if="tab === 'list'" class="adv-block">
      <div class="adv-filters">
        <select v-model="fStatus" @change="loadVideos"><option value="">全部状态</option><option value="private">仅自留</option><option value="pending">待审核</option><option value="public">已公开</option><option value="rejected">已驳回</option></select>
        <input v-model="fQ" placeholder="搜标题 / 知识点" @keyup.enter="loadVideos" />
        <button class="adv-btn" @click="loadVideos">查询</button>
      </div>
      <table class="adv-table">
        <thead><tr><th>视频</th><th>学科</th><th>作者</th><th>状态</th><th>发布</th><th>播放/赞</th><th>时间</th><th>操作</th></tr></thead>
        <tbody>
          <tr v-for="v in videos" :key="v.id">
            <td class="cell-name">{{ v.title || v.knowledge_name }}<em v-if="v.error" class="err">{{ v.error.slice(0, 40) }}</em></td>
            <td>{{ v.subject || '-' }}</td>
            <td>{{ v.owner_user_id ? '用户生成' : '官方基智' }}</td>
            <td><span class="badge" :class="'st-' + v.status">{{ v.status }}</span></td>
            <td><span class="badge" :class="'ps-' + v.publish_status">{{ v.publish_status }}</span></td>
            <td>{{ v.views_count }} / {{ v.likes_count }}</td>
            <td class="cell-time">{{ (v.created_at || '').slice(0, 10) }}</td>
            <td class="cell-ops">
              <template v-if="v.publish_status === 'pending' && v.status === 'ready'">
                <button class="adv-btn ok" @click="review(v.id, 'approve')">通过</button>
                <button class="adv-btn bad" @click="review(v.id, 'reject')">驳回</button>
              </template>
              <button v-if="v.status === 'failed'" class="adv-btn" @click="retry(v)">重试</button>
              <button class="adv-btn bad" @click="remove(v)">下架</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 举报 -->
    <div v-else-if="tab === 'reports'" class="adv-block">
      <div v-for="r in reports" :key="r.id" class="adv-report">
        <div class="adv-report-head">
          <b>{{ r.video?.title || r.video?.knowledge_name || '视频已删除' }}</b>
          <span class="badge warn">{{ r.reason || '未说明' }}</span>
          <i>{{ (r.created_at || '').slice(0, 16).replace('T', ' ') }}</i>
        </div>
        <div class="adv-report-detail">{{ r.detail || '无补充说明' }}</div>
        <div class="adv-report-ops">
          <button class="adv-btn ok" @click="handleReport(r.id, 'dismiss')">驳回举报</button>
          <button class="adv-btn bad" @click="handleReport(r.id, 'remove')">下架视频</button>
        </div>
      </div>
      <div v-if="!reports.length" class="adv-empty">没有待处理的举报</div>
    </div>

    <!-- 批量生成 -->
    <div v-else class="adv-block">
      <div class="adv-warm">
        <label>考纲范围</label>
        <select v-model="warm.syllabus"><option value="">全部考纲</option><option v-for="s in warmSyllabi" :key="s.id" :value="s.id">{{ s.name }}</option></select>
        <label>每考纲知识点数</label>
        <input v-model.number="warm.per" type="number" min="1" max="50" />
        <label>每知识点角度数（goal）</label>
        <input v-model.number="warm.goal" type="number" min="1" max="6" />
        <button class="adv-btn ok" :disabled="warming" @click="doWarm">{{ warming ? '排产中…' : '开始批量生成' }}</button>
      </div>
      <div v-if="warmResult" class="adv-warm-result">{{ warmResult }}</div>
      <div class="adv-hint">批量生成 = 官方基智身份 + 随机角度/模板/音色；按考纲题库知识点热度排序（题多的先出）。串行生成，每条约 20~40 秒。</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getAdminVideos, reviewAdminVideo, removeAdminVideo, getAdminVideoReports,
         handleAdminVideoReport, adminVideoWarm, getAdminVideoStats, retryAdminVideo } from '@/api/admin'
import { getVideoSubjects } from '@/api/videoSocial'
import { ElMessage, ElMessageBox } from 'element-plus'

const tab = ref('list')
const tabs = [
  { key: 'list', label: '视频管理' },
  { key: 'reports', label: '举报处理' },
  { key: 'warm', label: '批量生成' },
]
const stats = ref(null)
const videos = ref([])
const reports = ref([])
const fStatus = ref('')
const fQ = ref('')
const warm = ref({ syllabus: '', per: 1, goal: 1 })
const warmSyllabi = ref([])
const warming = ref(false)
const warmResult = ref('')

function fmt(n) {
  n = Number(n || 0)
  if (n >= 10000) return (n / 10000).toFixed(1) + '万'
  return String(n)
}

async function loadStats() {
  try { stats.value = await getAdminVideoStats() } catch { stats.value = null }
}

async function loadVideos() {
  try {
    const res = await getAdminVideos({ publish_status: fStatus.value, q: fQ.value, page_size: 50 })
    videos.value = res.items || []
  } catch { videos.value = [] }
}

async function loadReports() {
  try {
    const res = await getAdminVideoReports({ status: 'pending' })
    reports.value = res.items || []
  } catch { reports.value = [] }
}

function reloadAll() { loadStats(); loadVideos(); loadReports() }

async function review(id, action) {
  try {
    await reviewAdminVideo(id, action)
    ElMessage.success(action === 'approve' ? '已通过发布' : '已驳回')
    reloadAll()
  } catch (e) { ElMessage.error(e?.response?.data?.detail || '操作失败') }
}

async function retry(v) {
  try {
    await retryAdminVideo(v.id)
    ElMessage.success('已重新排队')
    reloadAll()
  } catch (e) { ElMessage.error(e?.response?.data?.detail || '重试失败') }
}

async function remove(v) {
  try {
    await ElMessageBox.confirm(`确定下架「${v.title || v.knowledge_name}」？音轨会一并删除`, '下架确认', { type: 'warning' })
    await removeAdminVideo(v.id)
    ElMessage.success('已下架')
    reloadAll()
  } catch {}
}

async function handleReport(id, action) {
  try {
    await handleAdminVideoReport(id, action)
    ElMessage.success('已处理')
    loadReports(); loadStats()
  } catch (e) { ElMessage.error(e?.response?.data?.detail || '处理失败') }
}

async function doWarm() {
  warming.value = true
  warmResult.value = ''
  try {
    const res = await adminVideoWarm({
      syllabus_ids: warm.value.syllabus ? [warm.value.syllabus] : null,
      per: Number(warm.value.per) || 1,
      goal: Number(warm.value.goal) || 1,
    })
    warmResult.value = `规划 ${res.planned} 个知识点 → 新入队 ${res.enqueued} / 已有跳过 ${res.skipped}；队列 ${res.queue.queue_size}`
    ElMessage.success('批量排产完成')
    loadStats()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '请注意：需要先执行 fix_video_social.sql')
  } finally { warming.value = false }
}

onMounted(async () => {
  reloadAll()
  try { warmSyllabi.value = (await getVideoSubjects()).items || [] } catch {}
})
</script>

<style scoped>
.adv { padding: 8px 4px 60px; }
.adv-title { font-size: 19px; font-weight: 700; color: var(--text-primary); margin: 8px 0 16px; }
.adv-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 10px; margin-bottom: 18px; }
.adv-stat { display: flex; flex-direction: column; gap: 3px; padding: 12px 14px; border-radius: 12px; background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent); border: 1px solid rgba(255,255,255,0.06); }
.adv-stat b { font-size: 22px; color: var(--text-primary); }
.adv-stat b.warn { color: #e6a23c; }
.adv-stat b.bad { color: #f56c6c; }
.adv-stat span { font-size: 11.5px; color: var(--text-muted); }
.adv-tabs { display: flex; gap: 8px; align-items: center; margin-bottom: 16px; }
.adv-tab { padding: 7px 18px; border-radius: 10px; border: 1px solid var(--line-soft); background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent); color: var(--text-secondary); font-size: 13px; cursor: pointer; font-family: inherit; }
.adv-tab.on { background: color-mix(in srgb, var(--brand) 14%, transparent); border-color: color-mix(in srgb, var(--brand) 40%, transparent); color: var(--brand-bright); font-weight: 600; }
.adv-refresh { margin-left: auto; font-size: 12px; color: var(--text-muted); cursor: pointer; }
.adv-refresh:hover { color: var(--brand-bright); }
.adv-block { display: flex; flex-direction: column; gap: 10px; }
.adv-filters { display: flex; gap: 8px; }
.adv-filters select, .adv-filters input { padding: 7px 12px; border-radius: 9px; border: 1px solid var(--line-soft); background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent); color: var(--text-primary); font-size: 13px; font-family: inherit; outline: none; }
.adv-btn { padding: 6px 14px; border-radius: 9px; border: 1px solid var(--line-soft); background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent); color: var(--text-secondary); font-size: 12.5px; cursor: pointer; font-family: inherit; }
.adv-btn.ok { color: #67c23a; border-color: rgba(103,194,58,.4); }
.adv-btn.bad { color: color-mix(in srgb, #f56c6c 70%, var(--text-primary)); border-color: rgba(245,108,108,.35); }
.adv-table { width: 100%; border-collapse: collapse; font-size: 12.5px; }
.adv-table th { text-align: left; color: var(--text-muted); font-weight: 500; padding: 8px 8px; border-bottom: 1px solid rgba(128,128,128,.16); }
.adv-table td { padding: 9px 8px; color: var(--text-secondary); border-bottom: 1px solid rgba(128,128,128,.08); vertical-align: top; }
.cell-name { color: var(--text-primary); font-weight: 600; max-width: 220px; }
.cell-name .err { display: block; font-style: normal; font-size: 11px; color: #f56c6c; font-weight: 400; }
.cell-time { white-space: nowrap; }
.cell-ops { white-space: nowrap; display: flex; gap: 6px; }
.badge { font-size: 11px; padding: 1px 8px; border-radius: 999px; background: rgba(128,128,128,.14); color: var(--text-secondary); }
.badge.st-ready { color: #67c23a; background: rgba(103,194,58,.1); }
.badge.st-generating { color: #409EFF; background: rgba(64,158,255,.1); }
.badge.st-failed { color: #f56c6c; background: rgba(245,108,108,.1); }
.badge.ps-pending { color: #e6a23c; background: rgba(230,162,60,.1); }
.badge.ps-public { color: #67c23a; background: rgba(103,194,58,.1); }
.badge.ps-rejected { color: #f56c6c; background: rgba(245,108,108,.1); }
.badge.warn { color: #e6a23c; background: rgba(230,162,60,.1); }
.adv-report { padding: 12px 14px; border-radius: 12px; background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent); border: 1px solid rgba(255,255,255,0.06); display: flex; flex-direction: column; gap: 8px; }
.adv-report-head { display: flex; align-items: center; gap: 10px; font-size: 13px; color: var(--text-primary); }
.adv-report-head i { font-style: normal; font-size: 11.5px; color: var(--text-muted); margin-left: auto; }
.adv-report-detail { font-size: 12.5px; color: var(--text-secondary); }
.adv-report-ops { display: flex; gap: 8px; }
.adv-empty { text-align: center; color: var(--text-muted); font-size: 13px; padding: 30px 0; }
.adv-warm { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.adv-warm label { font-size: 12.5px; color: var(--text-secondary); }
.adv-warm select, .adv-warm input { padding: 7px 12px; border-radius: 9px; border: 1px solid var(--line-soft); background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent); color: var(--text-primary); font-size: 13px; outline: none; width: 140px; font-family: inherit; }
.adv-warm input { width: 76px; }
.adv-warm-result { font-size: 13px; color: #67c23a; }
.adv-hint { font-size: 12px; color: var(--text-muted); line-height: 1.7; }
</style>