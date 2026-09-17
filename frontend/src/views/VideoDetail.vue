<template>
  <!-- 单一稳定根元素（2026-09-05 修：原来 v-if/v-else-if 两个并排根，
       数据加载后根元素被整体换掉，路由进场过渡卡死在 enter-from，
       整页永久 opacity:0 —— 骨架改到根内部切换） -->
  <div class="vd-page">
    <!-- 页面骨架（加载中先见结构，不白屏） -->
    <div v-if="loading && !video" class="vd-skeleton">
      <div class="sk sk-player"></div>
      <div class="sk sk-title"></div>
      <div class="sk sk-sub"></div>
      <div class="sk sk-bars"><i></i><i></i><i></i></div>
      <div class="sk sk-line l80"></div>
      <div class="sk sk-line l60"></div>
      <div class="sk sk-box"></div>
      <div class="sk sk-box short"></div>
    </div>

    <template v-else-if="video">
    <div class="vd-topbar">
      <button class="glass-btn" @click="$router.back()">
        <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
        返回
      </button>
      <span class="vd-crumb">视频库 / {{ video.knowledge_name }}</span>
    </div>

    <div class="vd-layout">
      <!-- 左：播放器 + 操作 -->
      <div class="vd-main">
        <VideoLessonPlayer ref="playerRef" v-if="video.status === 'ready'" :video="video" :autoplay="true" />
        <div v-else class="vd-notready">
          <span class="vd-nr-pen">✍️</span>
          <div class="vd-nr-text">{{ video.status === 'generating' ? '讲解师正在写讲稿…' : '生成失败，作者可以重试' }}</div>
          <div v-if="video.status === 'generating'" class="vd-nr-sub">写完会自动呈现，稍等一下</div>
        </div>

        <div class="vd-head">
          <h1>{{ video.title || video.knowledge_name }}</h1>
          <div class="vd-sub">
            <span class="vd-author">
              <img v-if="video.author_avatar" :src="video.author_avatar" alt="" @error="e => e.target.style.display='none'" />
              {{ video.author_name || '基智' }}
              <i v-if="!video.owner_user_id" class="vd-official">官方</i>
            </span>
            <span class="vd-tags">
              <span class="chip">{{ ANGLE_LABELS[video.angle] || '讲解' }}</span>
              <span class="chip">{{ video.subject ? '学科计划 · ' + video.subject : '通用' }}</span>
            </span>
          </div>
        </div>

        <div class="vd-actions">
          <button class="vd-act" :class="{ on: state.liked }" @click="like">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M20.8 4.6a5.5 5.5 0 00-7.8 0L12 5.6l-1-1a5.5 5.5 0 00-7.8 7.8l1 1L12 21l7.8-7.6 1-1a5.5 5.5 0 000-7.8z"/></svg>
            {{ fmt(video.likes_count) }}
          </button>
          <button class="vd-act" :class="{ on: state.favorited }" @click="fav">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M19 21l-7-5-7 5V5a2 2 0 012-2h10a2 2 0 012 2z"/></svg>
            {{ state.favorited ? '已收藏' : '收藏' }} {{ fmt(video.favorites_count) }}
          </button>
          <button class="vd-act" @click="dlVisible = true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v12"/><path d="M8 11l4 4 4-4"/><path d="M4 21h16"/></svg>
            下载
          </button>
          <button class="vd-act" @click="openShare">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12v8a2 2 0 002 2h12a2 2 0 002-2v-8"/><path d="M16 6l-4-4-4 4"/><path d="M12 2v13"/></svg>
            分享
          </button>
          <button class="vd-act practice" :disabled="practiceLoading" @click="openPracticeList">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg>
            {{ practiceLoading ? '找题中…' : '做题' }}
          </button>
          <button class="vd-act danger" @click="reportVisible = true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.3 3.9L1.8 18a2 2 0 001.7 3h17a2 2 0 001.7-3L13.7 3.9a2 2 0 00-3.4 0z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>
            举报
          </button>
        </div>

        <!-- 评论 -->
        <div class="vd-comments">
          <div class="vd-comments-head">评论 {{ fmt(video.comments_count) }}</div>
          <div class="vd-comment-input">
            <textarea v-model="commentText" rows="2" placeholder="写点学习心得，和大家交流…"></textarea>
            <button class="glass-btn primary" :disabled="!commentText.trim() || posting" @click="postComment">发表</button>
          </div>
          <div v-for="c in comments" :key="c.id" class="vd-comment">
            <img v-if="c.user_avatar" :src="c.user_avatar" alt="" class="vd-comment-avatar" />
            <span v-else class="vd-comment-avatar ph">{{ (c.user_name || '友')[0] }}</span>
            <div class="vd-comment-body">
              <div class="vd-comment-meta">
                <b>{{ c.user_name || '同学' }}</b>
                <i>{{ timeAgo(c.created_at) }}</i>
                <button v-if="c.user_id === myId" class="vd-comment-del" @click="delComment(c)">删除</button>
              </div>
              <div class="vd-comment-text">{{ c.content }}</div>
            </div>
          </div>
          <div v-if="!comments.length" class="vd-comments-empty">还没有评论，来抢沙发</div>
        </div>
      </div>

      <!-- 右：相关推荐 -->
      <aside class="vd-side">
        <div class="vd-side-title">相关讲解</div>
        <div v-for="v in related" :key="v.id" class="vd-rel" @click="$router.push(`/video/${v.id}`)">
          <div class="vd-rel-poster">
            <VideoPoster :video="v" />
            <span>{{ ANGLE_LABELS[v.angle] || '讲解' }}</span>
          </div>
          <div class="vd-rel-info">
            <div class="vd-rel-name">{{ v.title || v.knowledge_name }}</div>
            <div class="vd-rel-meta">{{ v.author_name || '基智' }} · {{ Math.round(v.audio_duration || 90) }}s</div>
          </div>
        </div>
        <div v-if="!related.length" class="vd-side-empty">暂无相关</div>
      </aside>
    </div>

    <!-- 举报弹窗 -->
    <el-dialog v-model="reportVisible" title="举报视频" width="440px" class="vp-dialog" destroy-on-close>
      <div class="vd-report">
        <label>举报原因</label>
        <div class="vd-report-reasons">
          <button v-for="r in reportReasons" :key="r" class="chip" :class="{ on: reportForm.reason === r }" @click="reportForm.reason = r">{{ r }}</button>
        </div>
        <label>详细说明（选填）</label>
        <textarea v-model="reportForm.detail" class="glass-input" rows="2" placeholder="描述一下具体情况"></textarea>
      </div>
      <template #footer>
        <el-button size="small" @click="reportVisible = false">取消</el-button>
        <el-button size="small" type="primary" :disabled="!reportForm.reason" @click="submitReport">提交举报</el-button>
      </template>
    </el-dialog>

    <!-- 分享弹窗（2026-09-05：给好友分享链接） -->
    <el-dialog v-model="shareVisible" title="分享这个讲解给好友" width="460px" class="vp-dialog" destroy-on-close>
      <div class="vd-share">
        <label>分享链接</label>
        <div class="vd-share-row">
          <input :value="shareUrl" readonly class="glass-input" @focus="$event.target.select()" />
          <el-button size="small" type="primary" @click="copyShareLink">复制</el-button>
        </div>
        <div class="vd-share-tip">
          📱 把链接粘贴到微信 / QQ 发给好友，对方打开就能看到这条讲解（画面 + 音频）。
        </div>
        <el-button v-if="canSystemShare" size="small" class="glass-btn" style="margin-top:4px" @click="systemShare">
          📤 调用系统分享
        </el-button>
      </div>
    </el-dialog>

    <!-- 下载弹窗（2026-09-05：视频带画面 webm / 纯音频 mp3 二选一） -->
    <el-dialog v-model="dlVisible" title="下载这份讲解" width="440px" class="vp-dialog" destroy-on-close>
      <div class="vd-share">
        <button class="vd-dl-row" :disabled="dlBusy" @click="doExportVideo">
          <i>🎬</i>
          <div>
            <b>{{ dlBusy ? '正在合成视频…（约 1 分钟）' : '导出视频' }}</b>
            <span>画面 + 声音，合成 .webm 视频文件</span>
          </div>
        </button>
        <button class="vd-dl-row" @click="doDownloadMp3">
          <i>🎧</i>
          <div>
            <b>只下载音频</b>
            <span>讲稿朗读 .mp3，可离线播放</span>
          </div>
        </button>
      </div>
    </el-dialog>

    <!-- 做题选题弹窗（2026-09-05 用户定调：列表自选，题目标注 学科计划 / AI 生成） -->
    <el-dialog v-model="practiceVisible" :title="'练一练 · ' + (video?.knowledge_name || '本知识点')" width="520px" class="vp-dialog" destroy-on-close>
      <div class="vd-practice">
        <div v-if="planItems.length" class="vd-practice-group">
          <div class="vd-pg-head"><i>📚 学科计划</i><span>本知识点推荐题</span></div>
          <button v-for="q in planItems" :key="q.id" class="vd-pq" @click="pickQuestion(q, 'plan')">
            <span class="vd-pq-type">{{ qTypeLabel(q) }}</span>
            <span class="vd-pq-stem">{{ plainStem(q).slice(0, 52) }}</span>
            <span class="vd-pq-src plan">学科计划</span>
          </button>
        </div>
        <div class="vd-practice-group">
          <div class="vd-pg-head"><i>✨ AI 生成</i><span>随堂出题</span></div>
          <button v-for="(q, i) in aiItems" :key="'ai' + i" class="vd-pq" @click="pickQuestion(q, 'ai')">
            <span class="vd-pq-type">{{ qTypeLabel(q) }}</span>
            <span class="vd-pq-stem">{{ plainStem(q).slice(0, 52) }}</span>
            <span class="vd-pq-src ai">AI 生成</span>
          </button>
          <div v-if="aiLoading" class="vd-pq-loading">✦ AI 正在出题…</div>
          <div v-else-if="!aiItems.length" class="vd-pq-retry" @click="genAiItems">AI 出题没赶上趟，点这里再生成 2 道</div>
        </div>
      </div>
    </el-dialog>
    </template>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getVideoDetail, toggleVideoLike, toggleVideoFavorite, getVideoComments,
         postVideoComment, deleteVideoComment, reportVideo, reportVideoPlay,
         getVideoQuestions } from '@/api/videoSocial'
import { generateQuestion } from '@/api/questions'
import { ANGLE_LABELS } from '@/utils/videoLib'
import VideoLessonPlayer from '@/components/VideoLessonPlayer.vue'
import VideoPoster from '@/components/VideoPoster.vue'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const video = ref(null)
const playerRef = ref(null)
const loading = ref(true)
const state = ref({ liked: false, favorited: false })
const related = ref([])
const comments = ref([])
const commentText = ref('')
const posting = ref(false)
const reportVisible = ref(false)
const reportReasons = ['内容有错误', '讲解不清', '与知识点不符', '广告或垃圾内容', '侵权或不适宜', '其他']
const reportForm = reactive({ reason: '', detail: '' })

const myId = computed(() => authStore.user?.id || '')

function fmt(n) {
  n = Number(n || 0)
  if (n >= 10000) return (n / 10000).toFixed(1) + '万'
  return String(n)
}

function timeAgo(iso) {
  if (!iso) return ''
  const diff = (Date.now() - new Date(iso).getTime()) / 1000
  if (diff < 60) return '刚刚'
  if (diff < 3600) return Math.floor(diff / 60) + ' 分钟前'
  if (diff < 86400) return Math.floor(diff / 3600) + ' 小时前'
  return Math.floor(diff / 86400) + ' 天前'
}

async function load() {
  loading.value = true
  clearStatusPoll()
  try {
    const res = await getVideoDetail(route.params.id, myId.value)
    video.value = res.video
    state.value = res.state || {}
    related.value = res.related || []
  } catch (e) {
    loading.value = false
    ElMessage.error('视频不存在或不可访问')
    router.push('/video-square')
    return
  }
  loading.value = false
  loadComments()
  // 浏览量（2026-09-05 用户定调：进入视频页满 10 秒才 +1 次，中间离开不计）
  scheduleViewCount(video.value.id)
  // 还在生成中 → 自动轮询，写完了自己浮出来
  if (video.value && video.value.status === 'generating') scheduleStatusPoll(true)
}

let statusPollTimer = null
let viewTimer = null
function scheduleViewCount(videoId) {
  if (viewTimer) clearTimeout(viewTimer)
  // 满 10 秒才计一次浏览量（停留在页面上；离开即取消）
  viewTimer = setTimeout(async () => {
    try {
      await reportVideoPlay(videoId, {
        user_id: myId.value,
        knowledge_key: video.value?.knowledge_key,
        subject: video.value?.subject,
      })
      if (video.value && video.value.views_count !== undefined) video.value.views_count += 1
    } catch {}
  }, 10000)
}
function scheduleStatusPoll(first) {
  clearStatusPoll()
  statusPollTimer = setTimeout(async () => {
    try {
      const res = await getVideoDetail(route.params.id, myId.value)
      if (res.video) {
        video.value = res.video
        state.value = res.state || {}
        related.value = res.related || []
      }
      if (video.value && video.value.status === 'generating') scheduleStatusPoll(false)
    } catch {
      if (video.value && video.value.status === 'generating') scheduleStatusPoll(false)
    }
  }, first ? 3000 : 8000)
}
function clearStatusPoll() {
  if (statusPollTimer) { clearTimeout(statusPollTimer); statusPollTimer = null }
}

async function loadComments() {
  try {
    const res = await getVideoComments(route.params.id, 1)
    comments.value = res.items || []
  } catch { comments.value = [] }
}

async function like() {
  try {
    const r = await toggleVideoLike(video.value.id, myId.value)
    state.value.liked = r.active
    video.value.likes_count = r.count
  } catch (e) { ElMessage.error(e?.response?.data?.detail || '操作失败') }
}

async function fav() {
  try {
    const r = await toggleVideoFavorite(video.value.id, myId.value)
    state.value.favorited = r.active
    video.value.favorites_count = r.count
  } catch (e) { ElMessage.error(e?.response?.data?.detail || '操作失败') }
}

async function postComment() {
  posting.value = true
  try {
    await postVideoComment(video.value.id, {
      user_id: myId.value,
      content: commentText.value.trim(),
      user_name: authStore.user?.nickname || '同学',
      user_avatar: authStore.user?.avatar_url || '',
    })
    commentText.value = ''
    video.value.comments_count = Number(video.value.comments_count || 0) + 1
    ElMessage.success('评论成功')
    loadComments()
  } catch (e) { ElMessage.error(e?.response?.data?.detail || '评论失败') } finally { posting.value = false }
}

async function delComment(c) {
  try {
    await deleteVideoComment(c.id, myId.value)
    video.value.comments_count = Math.max(0, Number(video.value.comments_count || 0) - 1)
    loadComments()
  } catch (e) { ElMessage.error(e?.response?.data?.detail || '删除失败') }
}

// ===== 分享（2026-09-05：给好友分享链接）=====
const shareVisible = ref(false)
const shareUrl = computed(() => `${location.origin}/video/${video.value?.id || ''}`)
const canSystemShare = computed(() => !!(typeof navigator !== 'undefined' && navigator.share))
function openShare() { shareVisible.value = true }
async function copyShareLink() {
  try {
    await navigator.clipboard.writeText(shareUrl.value)
    ElMessage.success('链接已复制，发给好友一起看')
  } catch { ElMessage.warning('复制失败，请长按链接手动复制') }
}
async function systemShare() {
  try {
    await navigator.share({
      title: video.value?.title || '基智讲题视频',
      text: `${video.value?.knowledge_name || ''} 的讲解视频，一起看`,
      url: shareUrl.value,
    })
  } catch { /* 用户取消分享 */ }
}

// ===== 做题（2026-09-05 用户定调：先弹题目列表自选——学科计划题 + AI 生成题两组标注，点谁跳谁）=====
const practiceLoading = ref(false)
const practiceVisible = ref(false)
const planItems = ref([])
const aiItems = ref([])
const aiLoading = ref(false)

const QTYPE_LABELS = { choice: '选择', fill: '填空', cloze: '完形', translation: '翻译', essay: '作文', calculation: '计算', programming: '编程', analysis: '分析', judgement: '判断', reading: '阅读' }
function qTypeLabel(q) {
  const t = q && (q.question_type || q.type || '')
  return QTYPE_LABELS[t] || t || '题目'
}
// 题干展平：选择题 stem 是字符串；填空/完形 stem 是分段数组或 content.stem 包裹对象
function plainStem(q) {
  let raw = q && (q.stem || q.content || q.question_stem)
  if (raw && typeof raw === 'object' && !Array.isArray(raw)) {
    raw = raw.stem || raw.text || raw.sentence || raw.question || raw.title
  }
  if (Array.isArray(raw)) {
    raw = raw.map((seg) => {
      if (seg && typeof seg === 'object') return seg.text ?? seg.blank ?? seg.content ?? seg.blank_text ?? '____'
      return seg
    }).join(' ')
  }
  return String(raw || (q && q.topic) || '').trim() || '（查看题目详情）'
}

async function openPracticeList() {
  const v = video.value
  if (!v) return
  practiceLoading.value = true
  practiceVisible.value = true
  planItems.value = []
  aiItems.value = []
  try {
    const data = await getVideoQuestions(v.id, 8)
    planItems.value = (data && data.items) || []
  } catch (e) {
    console.error('推荐题目拉取失败:', e)
    planItems.value = []
  } finally {
    practiceLoading.value = false
  }
  genAiItems()   // 两组一起呈现在列表里（学生可对照来源挑选）
}

async function genAiItems() {
  if (aiLoading.value) return
  const v = video.value
  if (!v) return
  const CACHE_KEY = `vd_ai_practice_${v.id}`
  // 会话内 10 分钟缓存：重复打开弹窗不重复烧 AI 出题钱
  try {
    const cached = JSON.parse(sessionStorage.getItem(CACHE_KEY) || 'null')
    if (cached && Array.isArray(cached.items) && cached.items.length && Date.now() - cached.ts < 10 * 60 * 1000) {
      aiItems.value = cached.items
      return
    }
  } catch {}
  aiLoading.value = true
  aiItems.value = []
  try {
    const [a, b] = await Promise.all([
      generateQuestion({ user_id: myId.value, category: v.subject || '通用', topic: v.knowledge_name || '' }),
      generateQuestion({ user_id: myId.value, category: v.subject || '通用', topic: v.knowledge_name || '' }),
    ])
    aiItems.value = [a, b].filter(Boolean)
    if (aiItems.value.length) {
      try {
        sessionStorage.setItem(CACHE_KEY, JSON.stringify({ items: aiItems.value, ts: Date.now() }))
      } catch {}
    }
  } catch (e) {
    console.error('AI 出题失败:', e)
    aiItems.value = []
  } finally {
    aiLoading.value = false
  }
}

function pickQuestion(q, src) {
  sessionStorage.setItem('current_question', JSON.stringify(q))
  practiceVisible.value = false
  router.push('/do-question')
}

// ===== 下载（2026-09-05）=====
const dlVisible = ref(false)
const dlBusy = ref(false)
async function doExportVideo() {
  if (!playerRef.value) { ElMessage.warning('播放器还没准备好'); return }
  dlBusy.value = true
  try {
    await playerRef.value.downloadVideo()
    dlVisible.value = false
    ElMessage.success('视频已导出，请查看浏览器下载')
  } catch (e) {
    console.error('导出失败:', e)
    ElMessage.error('导出失败：' + ((e && e.message) || '请重试'))
  } finally {
    dlBusy.value = false
  }
}
function doDownloadMp3() {
  dlVisible.value = false
  downloadAudio()
}
async function downloadAudio() {
  const url = video.value?.audio_url
  if (!url) { ElMessage.warning('音频还没生成好'); return }
  const tip = ElMessage({ message: '正在准备音频文件…', duration: 0 })
  try {
    const res = await fetch(url)
    if (!res.ok) throw new Error('HTTP ' + res.status)
    const blob = await res.blob()
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = `${(video.value.title || video.value.knowledge_name || '讲解音频')}.mp3`
    document.body.appendChild(a)
    a.click()
    a.remove()
    setTimeout(() => URL.revokeObjectURL(a.href), 4000)
    ElMessage.success('mp3 音频已开始下载')
  } catch (e) {
    console.error('下载失败:', e)
    ElMessage.error('下载失败，请检查网络')
  } finally {
    tip.close()
  }
}

async function submitReport() {
  try {
    await reportVideo(video.value.id, { user_id: myId.value, reason: reportForm.reason, detail: reportForm.detail })
    reportVisible.value = false
    ElMessage.success('举报已提交，平台会尽快处理')
  } catch (e) { ElMessage.error(e?.response?.data?.detail || '提交失败') }
}

onMounted(load)

// 点「相关讲解」跳转同一组件（路由参数变化，实例复用）→ 停旧音轨 + 骨架 + 重新加载并计一次播放
watch(() => route.params.id, (id, oldId) => {
  if (id && id !== oldId) {
    if (viewTimer) clearTimeout(viewTimer)
    if (playerRef.value) playerRef.value.stop()
    video.value = null
    load()
  }
})

onUnmounted(() => {
  clearStatusPoll()
  if (viewTimer) clearTimeout(viewTimer)
})
</script>

<style scoped>
.vd-page { min-height: 100vh; padding: 20px 28px 60px; max-width: 1200px; margin: 0 auto; }
.vd-topbar { display: flex; align-items: center; gap: 14px; margin-bottom: 16px; }
.vd-crumb { font-size: 12.5px; color: var(--text-muted); }
.vd-layout { display: grid; grid-template-columns: 1fr 300px; gap: 18px; }
.vd-main { display: flex; flex-direction: column; gap: 14px; min-width: 0; }
.vd-notready { aspect-ratio: 16/9; display: flex; flex-direction: column; gap: 10px; align-items: center; justify-content: center; border-radius: 14px; border: 1px dashed var(--line-soft); color: var(--text-muted); font-size: 14px; animation: vd-pulse 1.8s ease-in-out infinite; }
.vd-nr-pen { font-size: 26px; }
.vd-nr-text { font-size: 14px; color: var(--text-secondary); }
.vd-nr-sub { font-size: 12px; color: var(--text-muted); }
@keyframes vd-pulse { 0%, 100% { opacity: .72; } 50% { opacity: 1; } }

/* 详情页骨架（2026-09-04 晚） */
.vd-skeleton { display: flex; flex-direction: column; gap: 14px; }
.sk {
  border-radius: 12px;
  background: linear-gradient(100deg, rgba(128,128,128,.09) 30%, rgba(128,128,128,.19) 50%, rgba(128,128,128,.09) 70%);
  background-size: 220% 100%;
  animation: sk-shim 1.4s ease-in-out infinite;
}
.sk-player { aspect-ratio: 16/9; }
.sk-title { height: 22px; width: 46%; }
.sk-sub { height: 14px; width: 30%; }
.sk-bars { display: flex; gap: 10px; background: none; animation: none; }
.sk-bars i { flex: 1; max-width: 120px; height: 34px; border-radius: 999px;
  background: linear-gradient(100deg, rgba(128,128,128,.09) 30%, rgba(128,128,128,.19) 50%, rgba(128,128,128,.09) 70%);
  background-size: 220% 100%; animation: sk-shim 1.4s ease-in-out infinite; }
.sk-line { height: 13px; }
.sk-line.l80 { width: 80%; }
.sk-line.l60 { width: 60%; }
.sk-box { height: 72px; }
.sk-box.short { height: 48px; }
@keyframes sk-shim { from { background-position: 130% 0; } to { background-position: -130% 0; } }
.vd-head h1 { font-size: 19px; font-weight: 700; color: var(--text-primary); }
.vd-sub { display: flex; align-items: center; gap: 12px; margin-top: 8px; flex-wrap: wrap; }
.vd-author { display: inline-flex; align-items: center; gap: 6px; font-size: 13px; color: var(--text-secondary); }
.vd-author img { width: 20px; height: 20px; border-radius: 50%; object-fit: cover; background: #fff; }
.vd-official { font-style: normal; font-size: 10px; padding: 1px 7px; border-radius: 999px; background: color-mix(in srgb, var(--brand) 12%, transparent); color: var(--brand-bright); border: 1px solid color-mix(in srgb, var(--brand) 30%, transparent); }
.vd-tags { display: inline-flex; gap: 6px; }
.chip { padding: 3px 11px; border-radius: 999px; font-size: 11.5px; color: var(--text-secondary); background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent); border: 1px solid var(--line-soft); }
.vd-actions { display: flex; gap: 10px; flex-wrap: wrap; }
.vd-act { display: inline-flex; align-items: center; gap: 6px; padding: 8px 18px; border-radius: 999px; font-size: 13px; color: var(--text-secondary); background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent); border: 1px solid var(--line-soft); cursor: pointer; transition: all .2s ease; font-family: inherit; }
.vd-act svg { width: 15px; height: 15px; }
.vd-act:hover { border-color: var(--brand); color: var(--brand-bright); }
.vd-act.on { background: color-mix(in srgb, var(--brand) 12%, transparent); border-color: color-mix(in srgb, var(--brand) 40%, transparent); color: var(--brand-bright); }
.vd-act.danger { color: color-mix(in srgb, #f56c6c 70%, var(--text-primary)); }
.vd-act.practice {
  color: var(--brand-bright);
  background: color-mix(in srgb, var(--brand) 14%, transparent);
  border-color: color-mix(in srgb, var(--brand) 45%, transparent);
  font-weight: 700;
}
.vd-act.practice:hover { background: color-mix(in srgb, var(--brand) 22%, transparent); }
.vd-act.practice[disabled] { opacity: .6; cursor: wait; }

.vd-comments { margin-top: 6px; display: flex; flex-direction: column; gap: 12px; }
.vd-comments-head { font-size: 14px; font-weight: 700; color: var(--text-primary); }
.vd-comment-input { display: flex; gap: 10px; }
.vd-comment-input textarea { flex: 1; padding: 10px 13px; border-radius: 12px; font-size: 13px; color: var(--text-primary); background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent); border: 1px solid var(--line-soft); outline: none; resize: vertical; min-height: 48px; font-family: inherit; }
.vd-comment-input textarea:focus { border-color: color-mix(in srgb, var(--brand) 40%, transparent); }
.vd-comment { display: flex; gap: 10px; }
.vd-comment-avatar { width: 34px; height: 34px; border-radius: 50%; object-fit: cover; flex: none; background: color-mix(in srgb, var(--surface, #ffffff) 10%, transparent); }
.vd-comment-avatar.ph { display: flex; align-items: center; justify-content: center; color: var(--brand-bright); font-weight: 700; font-size: 14px; }
.vd-comment-body { flex: 1; min-width: 0; border-bottom: 1px solid rgba(128,128,128,.1); padding-bottom: 10px; }
.vd-comment-meta { display: flex; align-items: center; gap: 8px; font-size: 12px; }
.vd-comment-meta b { color: var(--text-primary); font-size: 12.5px; }
.vd-comment-meta i { color: var(--text-muted); font-style: normal; }
.vd-comment-del { margin-left: auto; background: none; border: none; color: var(--text-muted); font-size: 11px; cursor: pointer; font-family: inherit; }
.vd-comment-del:hover { color: #f56c6c; }
.vd-comment-text { margin-top: 4px; font-size: 13px; color: var(--text-secondary); line-height: 1.65; word-break: break-word; }
.vd-comments-empty { color: var(--text-muted); font-size: 12.5px; text-align: center; padding: 16px 0; }

.vd-side { position: sticky; top: 20px; align-self: start; display: flex; flex-direction: column; gap: 10px; }
.vd-side-title { font-size: 14px; font-weight: 700; color: var(--text-primary); }
.vd-rel { display: flex; gap: 9px; padding: 8px; border-radius: 12px; cursor: pointer; background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent); border: 1px solid rgba(255,255,255,0.05); transition: all .2s ease; }
.vd-rel:hover { border-color: color-mix(in srgb, var(--brand) 33%, transparent); transform: translateX(3px); }
.vd-rel-poster { position: relative; width: 104px; aspect-ratio: 16/9; border-radius: 8px; flex: none; display: flex; align-items: flex-start; }
.vd-rel-poster.tpl-chalkboard { background: linear-gradient(160deg, #0f1722, #142030); }
.vd-rel-poster.tpl-cards { background: linear-gradient(160deg, #f4f6fb, #e9eef7); }
.vd-rel-poster span { font-size: 9.5px; padding: 1px 7px; border-radius: 999px; margin: 5px 0 0 5px; background: rgba(10,14,24,.55); color: #dfe7f5; }
.vd-rel-info { min-width: 0; display: flex; flex-direction: column; justify-content: center; gap: 3px; }
.vd-rel-name { font-size: 12.5px; font-weight: 600; color: var(--text-primary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.vd-rel-meta { font-size: 11px; color: var(--text-muted); }
.vd-side-empty { color: var(--text-muted); font-size: 12px; text-align: center; padding: 20px 0; }

.vd-report { display: flex; flex-direction: column; gap: 10px; }
.vd-report label { font-size: 12.5px; color: var(--text-secondary); }
.vd-share { display: flex; flex-direction: column; gap: 10px; }
.vd-share label { font-size: 12.5px; color: var(--text-secondary); }
.vd-share-row { display: flex; gap: 8px; }
.vd-share-row input { flex: 1; }
.vd-share-tip { font-size: 12px; color: var(--text-muted); line-height: 1.6; }
.vd-dl-row {
  display: flex; align-items: center; gap: 12px;
  padding: 13px 15px; border-radius: 14px; text-align: left;
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent);
  border: 1px solid var(--line-soft);
  cursor: pointer; font-family: inherit; transition: all .2s ease;
}
.vd-dl-row:hover { border-color: var(--brand); transform: translateY(-1px); }
.vd-dl-row[disabled] { opacity: .6; cursor: wait; }
.vd-dl-row i { font-size: 22px; font-style: normal; }
.vd-dl-row b { font-size: 13.5px; color: var(--text-primary); display: block; }
.vd-dl-row span { font-size: 11.5px; color: var(--text-muted); }
.vd-practice { display: flex; flex-direction: column; gap: 14px; max-height: 60vh; overflow: auto; }
.vd-practice-group { display: flex; flex-direction: column; gap: 8px; }
.vd-pg-head { display: flex; align-items: center; gap: 8px; font-size: 13px; font-weight: 700; color: var(--text-primary); }
.vd-pg-head i { font-style: normal; color: var(--brand-bright); }
.vd-pg-head span { font-weight: 400; font-size: 11.5px; color: var(--text-muted); }
.vd-pq {
  display: flex; align-items: center; gap: 10px; width: 100%;
  padding: 10px 12px; border-radius: 12px; text-align: left; font-family: inherit;
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent);
  border: 1px solid var(--line-soft); cursor: pointer; transition: all .2s ease;
}
.vd-pq:hover { border-color: var(--brand); transform: translateX(3px); }
.vd-pq-type {
  flex: none; font-size: 11px; font-weight: 700; color: var(--text-secondary);
  padding: 2px 8px; border-radius: 6px; background: color-mix(in srgb, var(--surface, #ffffff) 6%, transparent);
  border: 1px solid var(--line-soft);
}
.vd-pq-stem { flex: 1; min-width: 0; font-size: 12.5px; color: var(--text-primary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.vd-pq-src { flex: none; font-size: 10.5px; font-weight: 700; padding: 2px 8px; border-radius: 999px; }
.vd-pq-src.plan { color: #7db8ff; background: rgba(77, 141, 255, .14); border: 1px solid rgba(148, 205, 255, .35); }
.vd-pq-src.ai { color: #d9b8ff; background: rgba(139, 92, 255, .14); border: 1px solid rgba(186, 148, 255, .35); }
.vd-pq-loading { font-size: 12px; color: var(--text-muted); padding: 8px 4px; }
.vd-pq-retry { font-size: 12px; color: var(--brand-bright); padding: 8px 4px; cursor: pointer; }
.vd-report-reasons { display: flex; gap: 6px; flex-wrap: wrap; }
.vd-report .chip { cursor: pointer; font-family: inherit; }
.vd-report .chip.on { background: color-mix(in srgb, #f56c6c 12%, transparent); border-color: rgba(245,108,108,.45); color: #f56c6c; }
.vp-dialog :deep(.el-dialog) { background: var(--well) !important; border: 1px solid var(--line-soft) !important; border-radius: 16px !important; }
.vp-dialog :deep(.el-dialog__title) { color: var(--text-primary) !important; }
.glass-input { width: 100%; padding: 9px 13px; border-radius: 10px; font-size: 13px; color: var(--text-primary); background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent); border: 1px solid var(--line-soft); outline: none; font-family: inherit; box-sizing: border-box; }
.glass-btn { display: inline-flex; align-items: center; gap: 6px; padding: 7px 15px; border-radius: 10px; font-size: 13px; color: var(--text-secondary); background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent); border: 1px solid rgba(255,255,255,0.05); cursor: pointer; font-family: inherit; }
.glass-btn.primary { color: var(--brand-bright); background: color-mix(in srgb, var(--brand) 12%, transparent); border-color: color-mix(in srgb, var(--brand) 25%, transparent); }
.glass-btn .icon { width: 17px; height: 17px; }

@media (max-width: 860px) {
  .vd-layout { grid-template-columns: 1fr; }
  .vd-side { position: static; display: grid; grid-template-columns: repeat(2, 1fr); }
  .vd-side-title { grid-column: 1/-1; }
}
</style>