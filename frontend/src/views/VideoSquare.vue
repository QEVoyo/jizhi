<template>
  <div class="vs-page">
    <!-- 顶栏 -->
    <div class="vs-topbar">
      <button class="glass-btn back-btn" @click="$router.push('/home')">
        <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M19 12H5M12 19l-7-7 7-7"/>
        </svg>
        返回
      </button>
      <h1>
        <svg class="icon title-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="2" y="4" width="20" height="16" rx="3"/>
          <path d="M10 9l5 3-5 3V9z"/>
        </svg>
        视频库
      </h1>
      <div class="vs-actions">
        <button class="glass-btn vs-refresh" :class="{ spinning: refreshing }" title="刷新列表" @click="reloadAll">
          <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 12a9 9 0 11-2.64-6.36"/><path d="M21 3v5h-5"/>
          </svg>
          刷新
        </button>
        <span class="vs-tabs">
          <span :class="{ on: tab === 'square' }" @click="switchTab('square')">推荐</span>
          <span :class="{ on: tab === 'fav' }" @click="switchTab('fav')">我的收藏</span>
          <span :class="{ on: tab === 'mine' }" @click="switchTab('mine')">我的视频</span>
        </span>
      </div>
    </div>

    <!-- 筛选行（广场） -->
    <div v-if="tab === 'square'" class="vs-filter">
      <button class="chip" :class="{ on: !subject }" @click="setSubject('')">全部</button>
      <button v-for="s in subjects" :key="s.id" class="chip" :class="{ on: subject === s.id }" @click="setSubject(s.id)">{{ s.name }}</button>
      <span class="vs-spacer"></span>
      <input v-model="q" class="vs-search" placeholder="搜索视频 / 知识点" @keyup.enter="reload" />
      <div class="vs-sort">
        <button class="chip" :class="{ on: sort === 'hot' }" @click="setSort('hot')">最热</button>
        <button class="chip" :class="{ on: sort === 'new' }" @click="setSort('new')">最新</button>
        <button class="chip" :class="{ on: sort === 'like' }" @click="setSort('like')">点赞榜</button>
      </div>
    </div>

    <!-- 广场流 -->
    <div v-if="tab === 'square'" class="vs-grid">
      <template v-if="loading">
        <div v-for="i in 8" :key="'sk' + i" class="vs-card vs-sk">
          <div class="vs-poster sk"></div>
          <div class="vs-info">
            <div class="sk sk-line w70"></div>
            <div class="vs-meta"><div class="sk sk-line w45"></div></div>
          </div>
        </div>
      </template>
      <div v-for="v in items" :key="v.id" class="vs-card" @click="open(v)">
        <div class="vs-poster">
          <VideoPoster :video="v" />
          <div v-if="!v.script" class="vs-poster-body"><div class="vs-poster-t">{{ v.title || v.knowledge_name }}</div></div>
          <span class="vs-play">
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
          </span>
          <span class="vs-angle">{{ ANGLE_LABELS[v.angle] || '讲解' }}</span>
          <span class="vs-dur">{{ Math.round(v.audio_duration || 90) }}s</span>
          <span class="vs-source">{{ v.subject ? '学科计划' : '资源库' }}</span>
        </div>
        <div class="vs-info">
          <div class="vs-name">{{ v.title || v.knowledge_name }}</div>
          <div class="vs-meta">
            <span class="vs-author">
              <img v-if="v.author_avatar" :src="v.author_avatar" alt="" @error="e => e.target.style.display='none'" />
              {{ v.author_name || '基智' }}
            </span>
            <span class="vs-stats">
              <i class="svg">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8S1 12 1 12z"/><circle cx="12" cy="12" r="3"/></svg>
              </i>{{ fmt(v.views_count) }}
              <i class="svg">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M20.8 4.6a5.5 5.5 0 00-7.8 0L12 5.6l-1-1a5.5 5.5 0 00-7.8 7.8l1 1L12 21l7.8-7.6 1-1a5.5 5.5 0 000-7.8z"/></svg>
              </i>{{ fmt(v.likes_count) }}
            </span>
          </div>
        </div>
      </div>
      <div v-if="!loading && !items.length" class="vs-empty">
        广场还是空的——第一批讲解视频正在生成，几分钟后再来看看
      </div>
    </div>

    <!-- 我的收藏 -->
    <div v-else-if="tab === 'fav'" class="vs-grid">
      <template v-if="favLoading">
        <div v-for="i in 4" :key="'fsk' + i" class="vs-card vs-sk">
          <div class="vs-poster sk"></div>
          <div class="vs-info">
            <div class="sk sk-line w70"></div>
            <div class="vs-meta"><div class="sk sk-line w45"></div></div>
          </div>
        </div>
      </template>
      <div v-for="v in favItems" :key="v.id" class="vs-card" @click="open(v)">
        <div class="vs-poster" :class="'tpl-' + (v.template_key || 'chalkboard')">
          <div v-if="v.script && v.script.sections && v.script.sections.length" class="vs-poster-body">
            <div class="vs-poster-t">{{ v.script.sections[0].heading }}</div>
            <div class="vs-poster-l">{{ (v.script.sections[0].lines || [])[0] || '' }}</div>
          </div>
          <span class="vs-play">
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
          </span>
          <span class="vs-angle">{{ ANGLE_LABELS[v.angle] || '讲解' }}</span>
        </div>
        <div class="vs-info">
          <div class="vs-name">{{ v.title || v.knowledge_name }}</div>
          <div class="vs-meta">
            <span class="vs-author">
              <img v-if="v.author_avatar" :src="v.author_avatar" alt="" />
              {{ v.author_name || '基智' }}
            </span>
          </div>
        </div>
      </div>
      <div v-if="!favLoading && !favItems.length" class="vs-empty">还没有收藏，看视频时点一下「收藏」就能在这里找到</div>
    </div>

    <!-- 我的视频 -->
    <div v-else class="vs-grid">
      <template v-if="myLoading">
        <div v-for="i in 4" :key="'msk' + i" class="vs-card vs-sk">
          <div class="vs-poster sk"></div>
          <div class="vs-info">
            <div class="sk sk-line w70"></div>
            <div class="vs-meta"><div class="sk sk-line w45"></div></div>
          </div>
        </div>
      </template>
      <button class="vs-card vs-gen-card" @click="genVisible = true">
        <div class="vs-gen-plus">+</div>
        <div class="vs-name">生成我的讲解视频</div>
        <div class="vs-meta">选学科 + 知识点，模板引擎帮你讲</div>
      </button>
      <div v-for="v in myItems" :key="v.id" class="vs-card" :class="{ dim: v.status !== 'ready' }" @click="myCardClick(v)">
        <div class="vs-poster" :class="'tpl-' + (v.template_key || 'chalkboard')">
          <div v-if="v.status === 'generating'" class="vs-poster-body">
            <div class="vs-poster-t">讲解师正在写讲稿…</div>
            <div class="vs-poster-l">完成后就可以播放</div>
          </div>
          <span v-if="v.status === 'ready'" class="vs-play">
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
          </span>
          <span class="vs-angle">{{ statusLabel(v) }}</span>
        </div>
        <div class="vs-info">
          <div class="vs-name">{{ v.title || v.knowledge_name }}</div>
          <div class="vs-ops">
            <template v-if="v.status === 'ready' && v.publish_status === 'private'">
              <button class="chip act" @click.stop="publish(v)">发布到广场</button>
            </template>
            <template v-else-if="v.publish_status === 'pending'">
              <span class="chip wait">审核中</span>
            </template>
            <span v-else-if="v.publish_status === 'rejected'" class="chip bad">未通过</span>
            <button v-if="v.status === 'failed'" class="chip act" @click.stop="retry(v)">重试</button>
            <button class="chip danger" @click.stop="remove(v)">删除</button>
          </div>
        </div>
      </div>
      <div v-if="!myLoading && !myItems.length" class="vs-empty">还没有自己的视频，点左上「生成我的讲解视频」试试</div>
    </div>

    <!-- 生成弹窗 -->
    <el-dialog v-model="genVisible" title="生成我的讲解视频" width="520px" class="vs-dialog" destroy-on-close>
      <div class="vs-gen-form">
        <label>学科</label>
        <el-select v-model="genForm.subject" placeholder="选择学科" style="width:100%">
          <el-option v-for="s in subjects" :key="s.id" :label="s.name" :value="s.id" />
        </el-select>
        <label>知识点（要讲什么）</label>
        <input v-model="genForm.knowledge_name" class="glass-input" placeholder="例如：定语从句 / 二次函数最值" />
        <label>讲解角度（默认随机，也可以自己点）</label>
        <div class="chip-row">
          <button v-for="(label, k) in ANGLE_LABELS" :key="k" class="chip"
                  :class="{ on: genForm.angle === k }" @click="genForm.angle = genForm.angle === k ? '' : k">{{ label }}</button>
        </div>
        <div class="vs-gen-hint">生成中可自由退出，完成后在「我的视频」查看，可发布到广场（需审核）</div>
      </div>
      <template #footer>
        <el-button size="small" @click="genVisible = false">取消</el-button>
        <el-button size="small" type="primary" :disabled="!genForm.subject || !genForm.knowledge_name || genning" @click="doGen">
          {{ genning ? '排队中…' : '开始生成' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getVideoSquare, getVideoSubjects, getMyVideos, getMyFavoriteVideos,
         generateMyVideo, publishMyVideo, retryMyVideo, deleteMyVideo } from '@/api/videoSocial'
import { ANGLE_LABELS } from '@/utils/videoLib'
import VideoPoster from '@/components/VideoPoster.vue'
import { ElMessage } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()

const tab = ref('square')
const subject = ref('')
const sort = ref('hot')
const q = ref('')
const items = ref([])
const subjects = ref([])
const loading = ref(false)
const refreshing = ref(false)
const favItems = ref([])
const favLoading = ref(false)
const myItems = ref([])
const myLoading = ref(false)
const genVisible = ref(false)
const genning = ref(false)
const genForm = reactive({ subject: '', knowledge_name: '', angle: '' })

let myTimer = null

function fmt(n) {
  n = Number(n || 0)
  if (n >= 10000) return (n / 10000).toFixed(1) + '万'
  return String(n)
}

function statusLabel(v) {
  if (v.status === 'generating') return '生成中…'
  if (v.status === 'failed') return '生成失败'
  if (v.publish_status === 'public') return '已公开'
  if (v.publish_status === 'pending') return '审核中'
  if (v.publish_status === 'rejected') return '未通过'
  return '仅自己可见'
}

function open(v) { router.push(`/video/${v.id}`) }

function myCardClick(v) {
  if (v.status === 'ready') { open(v); return }
  if (v.status === 'generating') ElMessage.info('还在生成中，完成后就能播放（列表会自动刷新）')
  else if (v.status === 'failed') ElMessage.warning('生成失败了，点卡片的「重试」再试一次')
}
function setSubject(id) { subject.value = id; reload() }
function setSort(s) { sort.value = s; reload() }
function switchTab(t) {
  tab.value = t
  if (t === 'fav') loadFav()
  if (t === 'mine') loadMine()
}

async function reload() {
  loading.value = true
  try {
    const res = await getVideoSquare({ subject: subject.value, sort: sort.value, q: q.value.trim(), page: 1, page_size: 24 })
    items.value = res.items || []
  } catch { items.value = [] } finally { loading.value = false }
}

async function loadSubjects() {
  try {
    const res = await getVideoSubjects()
    subjects.value = res.items || []
  } catch { subjects.value = [] }
}

async function loadFav() {
  favLoading.value = true
  try {
    const res = await getMyFavoriteVideos(authStore.user.id)
    favItems.value = res.items || []
  } catch { favItems.value = [] } finally { favLoading.value = false }
}

async function loadMine() {
  myLoading.value = true
  try {
    const res = await getMyVideos(authStore.user.id)
    myItems.value = res.items || []
  } catch { myItems.value = [] } finally { myLoading.value = false }
  // 生成中的自动刷新
  clearMyTimer()
  myTimer = setInterval(() => {
    if (myItems.value.some(v => v.status === 'generating') && tab.value === 'mine') loadMine()
  }, 8000)
}

function clearMyTimer() { if (myTimer) { clearInterval(myTimer); myTimer = null } }

async function doGen() {
  genning.value = true
  try {
    await generateMyVideo({
      user_id: authStore.user.id,
      subject: genForm.subject,
      knowledge_name: genForm.knowledge_name,
      angle: genForm.angle,
      author_name: authStore.user.nickname || '我',
      author_avatar: authStore.user.avatar_url || '',
    })
    ElMessage.success('已排队生成，几分钟后在「我的视频」查看')
    genVisible.value = false
    switchTab('mine')
  } catch (e) {
    ElMessage.error('生成失败: ' + (e?.response?.data?.detail || '请检查是否已执行建表 SQL'))
  } finally { genning.value = false }
}

async function publish(v) {
  try {
    await publishMyVideo(v.id, authStore.user.id)
    ElMessage.success('已提交审核')
    loadMine()
  } catch (e) { ElMessage.error(e?.response?.data?.detail || '发布失败') }
}

async function retry(v) {
  try {
    await retryMyVideo(v.id, authStore.user.id)
    ElMessage.success('已重新生成')
    loadMine()
  } catch (e) { ElMessage.error(e?.response?.data?.detail || '重试失败') }
}

async function remove(v) {
  try {
    await deleteMyVideo(v.id, authStore.user.id)
    ElMessage.success('已删除')
    loadMine()
  } catch (e) { ElMessage.error(e?.response?.data?.detail || '删除失败') }
}

// 全量刷新当前 Tab（2026-09-05：后台重生成视频后，旧列表不返回就永不更新——
// 补「返回/切换回本页自动刷新 + 手动刷新按钮」）
async function reloadAll() {
  refreshing.value = true
  try { await Promise.all([reload(), loadSubjects(), reloadCurrentTab()]) } finally { refreshing.value = false }
}
function reloadCurrentTab() {
  if (tab.value === 'fav') return loadFav()
  if (tab.value === 'mine') return loadMine()
  return Promise.resolve()
}

let lastFocusReload = 0
function onWindowFocus() {
  const now = Date.now()
  if (now - lastFocusReload < 2000) return   // 聚焦抖动节流
  lastFocusReload = now
  reloadAll()
}

onMounted(() => {
  reload()
  loadSubjects()
  window.addEventListener('focus', onWindowFocus)
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) reloadAll()
  })
})

onUnmounted(() => {
  clearMyTimer()
  window.removeEventListener('focus', onWindowFocus)
})
</script>

<style scoped>
.vs-page { min-height: 100vh; padding: 20px 28px 60px; }
.vs-topbar { display: flex; align-items: center; gap: 16px; margin-bottom: 18px; flex-wrap: wrap; }
.vs-topbar h1 { display: inline-flex; align-items: center; gap: 8px; font-size: 22px; font-weight: 700; color: var(--text-primary); margin: 0; }
.title-icon { width: 22px; height: 22px; color: var(--brand-bright); }
.glass-btn { display: inline-flex; align-items: center; gap: 6px; padding: 8px 16px; border-radius: 10px; font-size: 14px; color: var(--text-secondary); background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent); border: 1px solid rgba(255,255,255,0.05); cursor: pointer; transition: all .25s ease; font-family: inherit; }
.glass-btn:hover { background: color-mix(in srgb, var(--surface, #ffffff) 8%, transparent); border-color: var(--line-soft); }
.glass-btn .icon { width: 18px; height: 18px; }
.vs-actions { margin-left: auto; }
.vs-tabs { display: inline-flex; gap: 4px; padding: 4px; border-radius: 12px; background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent); border: 1px solid rgba(255,255,255,0.05); }
.vs-tabs span { padding: 6px 14px; border-radius: 9px; font-size: 13px; color: var(--text-secondary); cursor: pointer; transition: all .2s ease; }
.vs-tabs span.on { background: color-mix(in srgb, var(--brand) 14%, transparent); color: var(--brand-bright); font-weight: 600; }

.vs-filter { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 18px; }
.vs-spacer { flex: 1; }
.chip { padding: 5px 13px; border-radius: 999px; font-size: 12.5px; color: var(--text-secondary); background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent); border: 1px solid var(--line-soft); cursor: pointer; transition: all .2s ease; font-family: inherit; white-space: nowrap; }
.chip:hover { border-color: var(--brand); color: var(--brand-bright); }
.chip.on { background: color-mix(in srgb, var(--brand) 14%, transparent); border-color: color-mix(in srgb, var(--brand) 45%, transparent); color: var(--brand-bright); font-weight: 600; }
.chip.act { color: #67c23a; border-color: rgba(103,194,58,.35); }
.chip.wait { color: #e6a23c; border-color: rgba(230,162,60,.3); }
.chip.bad { color: #f56c6c; border-color: rgba(245,108,108,.3); cursor: default; }
.chip.danger { color: color-mix(in srgb, #f56c6c 70%, var(--text-primary)); }
.vs-search { min-width: 200px; padding: 7px 14px; border-radius: 999px; font-size: 13px; color: var(--text-primary); background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent); border: 1px solid var(--line-soft); outline: none; font-family: inherit; }
.vs-search:focus { border-color: color-mix(in srgb, var(--brand) 40%, transparent); }
.vs-sort { display: inline-flex; gap: 6px; }

.vs-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 16px; }
/* 列表骨架（2026-09-04 晚） */
.vs-sk { pointer-events: none; }
.vs-poster.sk, .sk {
  border-radius: 10px;
  background: linear-gradient(100deg, rgba(128,128,128,.09) 30%, rgba(128,128,128,.2) 50%, rgba(128,128,128,.09) 70%);
  background-size: 220% 100%;
  animation: vs-sk-shim 1.4s ease-in-out infinite;
}
.sk-line { height: 13px; }
.sk-line.w70 { width: 70%; }
.sk-line.w45 { width: 45%; }
@keyframes vs-sk-shim { from { background-position: 130% 0; } to { background-position: -130% 0; } }
.vs-card { border-radius: 14px; overflow: hidden; cursor: pointer; background: color-mix(in srgb, var(--surface, #ffffff) 5%, transparent); border: 1px solid rgba(255,255,255,0.06); transition: all .25s cubic-bezier(.34,1.56,.64,1); text-align: left; }
.vs-card:hover { transform: translateY(-4px); border-color: color-mix(in srgb, var(--brand) 35%, transparent); box-shadow: 0 10px 28px rgba(0,0,0,.14); }
.vs-card.dim { opacity: .8; cursor: pointer; }
.vs-poster { position: relative; aspect-ratio: 16/9; display: flex; align-items: center; justify-content: center; overflow: hidden; }
.vs-refresh { margin-left: 6px; }
.vs-refresh.spinning .icon { animation: vs-spin .8s linear infinite; }
@keyframes vs-spin { to { transform: rotate(360deg); } }
.vs-poster.tpl-chalkboard { background: linear-gradient(160deg, #0f1722 0%, #142030 60%, #101a28 100%); }
.vs-poster.tpl-cards { background: linear-gradient(160deg, #f4f6fb 0%, #e9eef7 100%); }
.vs-poster-body { display: flex; flex-direction: column; align-items: center; gap: 5px; padding: 0 14px; text-align: center; width: 100%; }
.vs-poster-t { font-size: 14px; font-weight: 700; color: #e8edf7; }
.vs-poster-l { font-size: 10.5px; color: rgba(201, 214, 234, .72); max-width: 90%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.tpl-cards .vs-poster-t { color: #1c2b45; }
.tpl-cards .vs-poster-l { color: rgba(69, 83, 110, .75); }
.tpl-cards .vs-play { background: rgba(255,255,255,.16); color: #2f6fe0; }
.vs-play { position: absolute; right: 10px; top: 50%; transform: translateY(-50%); width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; background: rgba(255,255,255,.14); color: #5ed0ff; backdrop-filter: blur(4px); transition: transform .2s ease; }
.vs-play svg { width: 14px; height: 14px; margin-left: 2px; }
.vs-card:hover .vs-play { transform: translateY(-50%) scale(1.15); }
.vs-angle { position: absolute; left: 10px; top: 10px; font-size: 11px; padding: 2px 9px; border-radius: 999px; background: rgba(10,14,24,.55); color: #dfe7f5; border: 1px solid rgba(255,255,255,.14); }
.vs-dur { position: absolute; right: 10px; bottom: 10px; font-size: 11px; padding: 1px 8px; border-radius: 6px; background: rgba(10,14,24,.6); color: #dfe7f5; }
.vs-source { position: absolute; left: 10px; bottom: 10px; font-size: 10.5px; padding: 1px 8px; border-radius: 6px; background: rgba(77, 141, 255, .28); color: #cfe4ff; border: 1px solid rgba(148, 205, 255, .35); }
.vs-info { padding: 10px 12px 12px; }
.vs-name { font-size: 13.5px; font-weight: 600; color: var(--text-primary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.vs-meta { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-top: 6px; font-size: 11.5px; color: var(--text-muted); }
.vs-author { display: inline-flex; align-items: center; gap: 5px; color: var(--text-secondary); min-width: 0; overflow: hidden; }
.vs-author img { width: 16px; height: 16px; border-radius: 50%; object-fit: cover; background: #fff; flex: none; }
.vs-stats { display: inline-flex; align-items: center; gap: 8px; flex: none; }
.vs-stats .svg { display: inline-flex; margin-right: 3px; }
.vs-stats svg { width: 12px; height: 12px; }
.vs-ops { display: flex; gap: 6px; margin-top: 8px; flex-wrap: wrap; }
.vs-ops .chip { padding: 3px 10px; font-size: 11.5px; }
.vs-empty { grid-column: 1/-1; padding: 60px 20px; text-align: center; color: var(--text-muted); font-size: 13px; }
.vs-gen-card { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 6px; min-height: 150px; cursor: pointer; font-family: inherit; }
.vs-gen-plus { width: 44px; height: 44px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 24px; color: var(--brand-bright); background: color-mix(in srgb, var(--brand) 12%, transparent); border: 1px dashed color-mix(in srgb, var(--brand) 45%, transparent); }
.vs-gen-form { display: flex; flex-direction: column; gap: 10px; }
.vs-gen-form label { font-size: 12.5px; color: var(--text-secondary); margin-top: 2px; }
.chip-row { display: flex; gap: 6px; flex-wrap: wrap; }
.vs-gen-hint { font-size: 11.5px; color: var(--text-muted); margin-top: 6px; line-height: 1.6; }
.glass-input { width: 100%; padding: 9px 13px; border-radius: 10px; font-size: 13.5px; color: var(--text-primary); background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent); border: 1px solid var(--line-soft); outline: none; font-family: inherit; box-sizing: border-box; }
.glass-input:focus { border-color: color-mix(in srgb, var(--brand) 40%, transparent); }
.vs-dialog :deep(.el-dialog) { background: var(--well) !important; border: 1px solid var(--line-soft) !important; border-radius: 16px !important; }
.vs-dialog :deep(.el-dialog__title) { color: var(--text-primary) !important; }
.vs-dialog :deep(.el-select), .vs-dialog :deep(.el-input__wrapper) { background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent) !important; }
@media (max-width: 600px) { .vs-page { padding: 12px 14px 50px; } .vs-grid { grid-template-columns: repeat(2, 1fr); } .vs-search { min-width: 130px; } }
</style>