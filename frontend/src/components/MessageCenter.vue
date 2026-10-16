<template>
  <div class="mc-page">
    <div class="mc-container">
      <!-- ===== Header ===== -->
      <div class="mc-header">
        <div class="header-left">
          <button class="g-btn" @click="goBack">
            <el-icon><ArrowLeft /></el-icon> 返回
          </button>
          <img src="/logo.png" class="header-logo" />
          <h1>消息中心</h1>
          <span v-if="totalUnread" class="total-badge">{{ totalUnread > 99 ? '99+' : totalUnread }}</span>
        </div>
        <div class="header-right">
          <button class="g-btn sm" @click="markAllCurrent" :disabled="!unreadInTab">全部已读</button>
          <button class="g-btn icon-only" title="消息设置" @click="goSettings">
            <el-icon><Setting /></el-icon>
          </button>
        </div>
      </div>

      <!-- ===== Tab 栏（由注册表生成，不再是写死的 10 个） ===== -->
      <div class="tab-bar">
        <button class="tab-btn" :class="{ active: activeTab === '' }"
                style="--c: var(--brand)" @click="switchTab('')">
          全部
          <span v-if="totalUnread" class="tab-badge">{{ totalUnread > 99 ? '99+' : totalUnread }}</span>
        </button>
        <button v-for="g in tabGroups" :key="g.key" class="tab-btn"
                :class="{ active: activeTab === g.key }"
                :style="{ '--c': g.color }" @click="switchTab(g.key)">
          <span class="tab-dot"></span>{{ g.label }}
          <span v-if="badges.groups?.[g.key]" class="tab-badge">{{ badges.groups[g.key] }}</span>
        </button>
      </div>

      <!-- ===== 列表 ===== -->
      <div class="mc-list" v-loading="loading">
        <div v-for="m in list" :key="m.id" class="mc-card"
             :class="{ unread: !m.is_read }"
             :style="{ '--c1': colorOf(m.type).c1, '--c2': colorOf(m.type).c2 }"
             @click="openDetail(m)">
          <div class="bar"></div>
          <div class="mc-icon">{{ labelOf(m.type).slice(0, 1) }}</div>
          <div class="mc-body">
            <div class="mc-top">
              <span class="mc-name">
                <span v-if="m.is_todo" class="todo-flag">待办</span>{{ m.title || labelOf(m.type) }}
              </span>
              <span class="mc-time">{{ formatTime(m.last_at || m.created_at) }}</span>
            </div>
            <div class="mc-preview">{{ m.content || labelOf(m.type) }}</div>
            <!-- ⚠️ 这里原本还有一个 `.type-key` 把消息点的**类型键**直接摊在用户面前
                 （`learning.daily_rec`、`system.capsule_due` 这种）——
                 那是排查用的，用户看不懂。2026-10-08 删掉，只留「N 条」这个有用的。 -->
            <div class="mc-extra" v-if="m.msg_count > 1">
              <span class="count-tag">{{ m.msg_count }} 条</span>
            </div>
          </div>
          <el-icon class="mc-arrow"><ArrowRight /></el-icon>
        </div>

        <div v-if="!loading && !list.length" class="mc-state">
          <el-icon :size="36"><Bell /></el-icon>
          <p>暂无消息</p>
        </div>
        <div v-if="hasMore && !loading" class="mc-more" @click="page++ && loadList()">加载更多</div>
      </div>
    </div>

    <!-- ===== 详情：居中毛玻璃弹层（与全站同一套观感，不是侧滑抽屉） ===== -->
    <div class="mc-mask" :class="{ on: detail }" @click.self="closeDetail">
      <div v-if="detail" class="mc-modal"
           :style="{ '--c1': colorOf(detail.type).c1, '--c2': colorOf(detail.type).c2 }">
        <div class="modal-bar"></div>
        <button class="modal-close" @click="closeDetail">✕</button>

        <div class="modal-head">
          <div class="modal-tag">
            <!-- ⚠️ 这里原本还有「· 组内第 N/M 个」—— 那是 2026-10-07 验配色派生
                 （derive_color 按组内序号铺色）时留下的调试信息，用户看不懂也不需要 -->
            <span class="dot"></span>{{ groupMeta(groupOf(detail.type)).label }}
          </div>
          <div class="modal-title">
            <div class="mc-icon lg">{{ labelOf(detail.type).slice(0, 1) }}</div>
            <div>
              <div class="modal-name">{{ detail.title || labelOf(detail.type) }}</div>
              <div class="modal-sub">
                {{ formatTime(detail.last_at || detail.created_at) }}
                <template v-if="detail.is_todo"> · 待办</template>
                <template v-else-if="detail.is_read"> · 已读</template>
              </div>
            </div>
          </div>
        </div>

        <!-- ===== 详情体：按「形态」分发（2026-10-08 重做）=====
             形态由**后端注册表**推导（`notification_registry._shape_of`），
             前端只认这几个名字。66 个消息点不必各写一套模板，
             「加消息点前端零改动」这个契约还成立。
             七个形态：rec / summary / actors / todo / notice / celebrate / plain -->
        <div class="modal-body" :class="'shape-' + shape">

          <!-- ① rec 学习推荐三合一 —— 真正的「做」在独立学习页 -->
          <template v-if="shape === 'rec'">
            <div class="rec-preview">
              <div class="rec-p-row">
                <span class="rec-p-no">①</span><span class="rec-p-name">学习内容</span>
                <span class="rec-p-meta">约 {{ recMinutes }} 分钟</span>
              </div>
              <div v-if="recQuestions.length" class="rec-p-row">
                <span class="rec-p-no">②</span><span class="rec-p-name">练习</span>
                <span class="rec-p-meta">{{ recQuestions.length }} 题</span>
              </div>
              <div v-if="recVideo.video_id" class="rec-p-row">
                <span class="rec-p-no">③</span><span class="rec-p-name">讲解视频</span>
                <span class="rec-p-meta">{{ recVideo.duration || '' }}</span>
              </div>
              <div v-if="recDoneLine" class="rec-p-done">{{ recDoneLine }}</div>
            </div>
            <div class="modal-text"><p v-for="(p, i) in bodyParagraphs" :key="i">{{ p }}</p></div>
            <button class="g-btn primary wide" @click="goLearn">去学习 →</button>
          </template>

          <!-- ② summary 昨日总结 —— 数字用卡片、知识点用标签、三段文字分开排 -->
          <template v-else-if="shape === 'summary'">
            <div v-if="sumStats.length" class="sum-stats">
              <div v-for="(s, i) in sumStats" :key="i" class="sum-stat">
                <b>{{ s.value }}<i v-if="s.unit">{{ s.unit }}</i></b>
                <span>{{ s.label }}</span>
                <!-- 口径说明（如「仅统计已批改的 8 道」）。数字的来源要能看见，
                     不然一个 30% 和一个 90% 看起来一样可信。 -->
                <em v-if="s.hint">{{ s.hint }}</em>
              </div>
            </div>
            <div v-if="sumWeak.length" class="sum-sec">
              <h5>需要加强</h5>
              <div class="sum-tags">
                <span v-for="t in sumWeak" :key="t" class="sum-tag weak">{{ t }}</span>
              </div>
            </div>
            <div v-if="sumStrong.length" class="sum-sec">
              <h5>掌握不错</h5>
              <div class="sum-tags">
                <span v-for="t in sumStrong" :key="t" class="sum-tag strong">{{ t }}</span>
              </div>
            </div>
            <!-- 学科计划链的知识点（EWMA）。与技术报告里的两条闭环链对应：
                 上面 weak/strong 是资源库链的逐题评分，这里是计划链的累计掌握度。 -->
            <div v-if="sumKp.length" class="sum-sec">
              <h5>计划知识点</h5>
              <div class="sum-tags">
                <span v-for="k in sumKp" :key="k.name" class="sum-tag"
                      :class="k.mastery >= 80 ? 'strong' : (k.mastery < 60 ? 'weak' : '')">
                  {{ k.name }} {{ k.mastery }}%
                </span>
              </div>
            </div>
            <p v-if="sumPayload.note" class="sum-note">{{ sumPayload.note }}</p>
            <div v-if="sumPayload.suggestion" class="sum-tip">
              <b>建议</b><span>{{ sumPayload.suggestion }}</span>
            </div>
            <p v-if="sumPayload.encouragement" class="sum-enc">{{ sumPayload.encouragement }}</p>
          </template>

          <!-- ③ actors 聚合型 —— 「谁做的」是这个形态存在的理由，
               改造前只把名字列成一行行灰块，和正文混在一起 -->
          <template v-else-if="shape === 'actors'">
            <div class="act-head">
              <span class="act-n">{{ actors.length }}</span>
              <span class="act-unit">{{ detail.msg_count > 1 ? `共 ${detail.msg_count} 条` : '条' }}</span>
            </div>
            <div v-if="actors.length" class="act-chips">
              <span v-for="(a, i) in actors" :key="i" class="act-chip">
                <span class="act-av">{{ String(a).slice(0, 1) }}</span>{{ a }}
              </span>
            </div>
            <div v-if="bodyParagraphs.length" class="modal-text">
              <p v-for="(p, i) in bodyParagraphs" :key="i">{{ p }}</p>
            </div>
          </template>

          <!-- ④ todo 待办 —— 说清「要做什么」+「为什么没已读」 -->
          <template v-else-if="shape === 'todo'">
            <div class="td-banner">
              <i class="fas fa-circle-exclamation"></i>
              <span>待办 —— <b>处理完才算已读</b>，看一眼不算</span>
            </div>
            <div class="modal-text"><p v-for="(p, i) in bodyParagraphs" :key="i">{{ p }}</p></div>
          </template>

          <!-- ⑤ notice 系统 / 账号类正式通知 -->
          <template v-else-if="shape === 'notice'">
            <div class="nt-head">
              <span class="nt-ic"><i class="fas" :class="iconOf(detail.type)"></i></span>
              <span class="nt-label">{{ labelOf(detail.type) }}</span>
            </div>
            <div class="modal-text"><p v-for="(p, i) in bodyParagraphs" :key="i">{{ p }}</p></div>
          </template>

          <!-- ⑥ celebrate 学程成就 / 晋升 -->
          <template v-else-if="shape === 'celebrate'">
            <div class="cb-badge"><i class="fas" :class="iconOf(detail.type)"></i></div>
            <div class="modal-text center"><p v-for="(p, i) in bodyParagraphs" :key="i">{{ p }}</p></div>
          </template>

          <!-- ⑦ plain 兜底 —— 分段正文。
               ⚠️ 以前是 `{{ detail.content }}` 一整块，而 `.modal-text` 上没有
               `white-space` —— 模型写的 `\n\n` 被 HTML 折叠成空格，多段并成一段。 -->
          <template v-else>
            <div class="modal-text"><p v-for="(p, i) in bodyParagraphs" :key="i">{{ p }}</p></div>
          </template>

          <!-- ⚠️ 这里原本有一块「这条消息 / 类型 / 点击去向 / 已读规则」——
               给开发和排查看的，用户看了既不懂也没用。2026-10-08 删掉。 -->
        </div>

        <div class="modal-foot">
          <button v-if="detail.is_todo" class="g-btn primary" @click="handleTodo">去处理</button>
          <button v-else-if="detail.link" class="g-btn primary" @click="goTarget">查看详情</button>
          <!-- ⚠️ 只在**还没读**的时候给这个按钮 —— `markRead()` 第一行就是
               `if (m.is_read) return`，已读时点了什么都不会发生，摆在那儿是死的。
               （非待办类型点开详情就已经自动标已读了，所以正常情况下它不出现。） -->
          <button v-if="!detail.is_read" class="g-btn" @click="markRead(detail)">标记已读</button>
          <button v-if="canDelete" class="g-btn danger" @click="removeOne(detail)">删除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, ArrowRight, Setting, Bell } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import {
  listMessages, getMessage, readOne, readMany,
  markHandled, deleteMessage, clearMessages,
} from '@/api/messages'
import {
  loadRegistry, getGroups, colorOf, groupOf, groupMeta,
  labelOf, isTodo, shapeOf, iconOf,
} from '@/utils/messageTypes'
import { useNotifications } from '@/composables/useNotifications'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const uid = () => authStore.user?.id

// 角标走**全站共享的那一份**（`composables/useNotifications.js`）——
// 2026-10-08 之前这里是自己的 `ref` + 自己的 30 秒计时器，
// 而 Sidebar / EdgeNavDock 也各有一份，首页同页面就是 3 份重复请求。
const { badges, refresh: refreshBadges } = useNotifications()

// ===== 状态 =====
const loading = ref(false)
const activeTab = ref('')          // '' = 全部；否则是大类 key
const list = ref([])
const page = ref(1)
const pageSize = 20
const hasMore = ref(false)
const tabGroups = ref([])

const totalUnread = computed(() => badges.value.total || 0)
const unreadInTab = computed(() =>
  activeTab.value ? (badges.value.groups?.[activeTab.value] || 0) : totalUnread.value)

// ===== 详情 =====
const detail = ref(null)

// ===== 详情形态（2026-10-08）=====
// 形态名由**后端注册表**给（`notification_registry._shape_of`），这里只读。
// ⚠️ 两处守卫：老的 rec / summary 行**没有 payload**（结构化是 10-08 才做的），
//    不守卫的话会渲染成「0 题 / 0%」和空的三块预览 —— 退回 plain 更诚实。
const shape = computed(() => {
  const s = shapeOf(detail.value?.type)
  if ((s === 'summary' || s === 'rec') && !detail.value?.payload) return 'plain'
  return s
})
/** 聚合型的触发者名单（`notify()` 累积的，最多留最近 5 个） */
const actors = computed(() => detail.value?.payload?.actors || [])

// ===== 学习总结：结构化 payload 的取用 =====
const sumPayload = computed(() => detail.value?.payload || {})

/** 数字卡片。**两种形状都要认**：
 *    · 2026-10-16 起：[{label, value, unit, hint?}, ...] —— 卡片由后端决定放哪几张
 *      （取不到的指标干脆不放，而不是填 0）
 *    · 之前：{questions, mastery} —— 库里还留着 19 条老通知，不兼容的话点开一片空白
 *
 *  ⚠️ 老形状照原样显示、**不替它修饰**。那批数字是用错误口径算出来的
 *     （mastery_score 的缺失值被当成 0 分平均），但它们是"当时发出去的内容"，
 *     改显示等于改写历史。新发的都走新形状。
 */
const sumStats = computed(() => {
  const s = sumPayload.value.stats
  if (Array.isArray(s)) return s
  if (s && typeof s === 'object') {
    return [
      { label: '完成题目', value: s.questions ?? 0, unit: '道' },
      { label: '整体掌握度', value: s.mastery ?? 0, unit: '%' },
    ]
  }
  return []
})
const sumWeak = computed(() => sumPayload.value.weak || [])
const sumStrong = computed(() => sumPayload.value.strong || [])
/** 学科计划链的知识点（EWMA 掌握度）。资源库链的薄弱/擅长走 weak/strong。 */
const sumKp = computed(() => sumPayload.value.kp || [])

/** 正文按**空行**分段。
 *  ⚠️ 以前直接 `{{ detail.content }}` 渲一整块，而 `.modal-text` 上没有
 *  `white-space` —— 模型写的 `\n\n` 被 HTML 折叠成空格，三段并成一段。
 *  段内保留单换行（`white-space: pre-line`），所以只按空行切。 */
const bodyParagraphs = computed(() => {
  const raw = detail.value?.content || detail.value?.title || ''
  return String(raw).split(/\n{2,}/).map(s => s.trim()).filter(Boolean)
})
const recQuestions = computed(() => detail.value?.payload?.questions || [])
const recVideo = computed(() => detail.value?.payload?.video || {})
const recMinutes = computed(() => detail.value?.payload?.content?.minutes || 0)
// 已完成几块 —— 进度由学习页写进 `payload.progress`
//（`PUT /daily-learn/{id}/progress`），这里只读来显示
const recDoneLine = computed(() => {
  const p = detail.value?.payload?.progress
  if (!p) return ''
  const n = ['content', 'questions', 'video'].filter(k => p[k]).length
  return n ? `已完成 ${n}/3 块` : ''
})
const canDelete = computed(() => groupOf(detail.value?.type || '') !== 'system')
// ===== 加载 =====
async function boot() {
  await loadRegistry()
  tabGroups.value = getGroups()
  await loadList()
}

async function loadList() {
  if (!uid()) return
  loading.value = true
  try {
    const res = await listMessages({
      user_id: uid(),
      group: activeTab.value || undefined,
      page: page.value,
      page_size: pageSize,
    })
    const items = res.items || []
    list.value = page.value === 1 ? items : [...list.value, ...items]
    hasMore.value = items.length === pageSize && (res.total == null || list.value.length < res.total)
  } catch (e) {
    ElMessage.error('消息加载失败：' + (e?.response?.data?.detail || e.message))
    list.value = []
  } finally {
    loading.value = false
  }
}

function switchTab(key) {
  activeTab.value = key
  page.value = 1
  loadList()
}

function goBack() { router.back() }
function goSettings() { router.push('/settings#sec-notify') }

// ===== 详情 =====
async function openDetail(m) {
  // 聊天不进详情，直接进会话（聊天是"用"，不是"看"）
  if (groupOf(m.type) === 'chat' && m.type !== 'chat.friend_request') {
    markRead(m)
    router.push(m.link || `/community/chat/${m.actor_id || m.source_id}`)
    return
  }
  try {
    detail.value = await getMessage(m.id, uid())
  } catch {
    detail.value = { ...m }        // 详情拉不到就用列表里的数据，别点不开
  }
  if (!detail.value.is_read && !isTodo(detail.value.type)) markRead(detail.value, true)
}

function closeDetail() { detail.value = null }

async function markRead(m, silent = false) {
  if (m.is_read) return
  try {
    await readOne(m.id, uid())
    m.is_read = true
    const inList = list.value.find(x => x.id === m.id)
    if (inList) inList.is_read = true
    refreshBadges()
  } catch (e) {
    if (!silent) ElMessage.error('标记已读失败：' + (e?.response?.data?.detail || e.message))
  }
}

async function handleTodo() {
  // 待办：真正的"已读"由处理动作驱动 —— 先去目标页处理，回来再敲这一下
  const link = detail.value.link
  closeDetail()
  if (link) router.push(link)
}

function goTarget() {
  const link = detail.value.link
  closeDetail()
  if (link) router.push(link)
}

// 去学习页。**带 id** —— 从消息中心点的是某一条具体的推荐，
// 看的就该是那一条，而不是「我最新的一条」。
function goLearn() {
  const id = detail.value?.id
  closeDetail()
  router.push(id ? `/daily-learn/${id}` : '/daily-learn')
}

async function removeOne(m) {
  try {
    await ElMessageBox.confirm('删除这条消息？（系统与安全类通知不可删除）', '确认', { type: 'warning' })
  } catch { return }
  try {
    await deleteMessage(m.id, uid())
    list.value = list.value.filter(x => x.id !== m.id)
    closeDetail()
    refreshBadges()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '删除失败')
  }
}

async function markAllCurrent() {
  try {
    await readMany(uid(), activeTab.value ? { group: activeTab.value } : { all: true })
    await Promise.all([loadList(), refreshBadges()])
    // 三合一那块也算读过了
    ElMessage.success('已标记为已读')
  } catch (e) {
    ElMessage.error('操作失败：' + (e?.response?.data?.detail || e.message))
  }
}

function formatTime(t) {
  if (!t) return ''
  const dt = new Date(t.endsWith('Z') || t.includes('+') ? t : t + 'Z')
  if (isNaN(dt.getTime())) return ''
  const diff = Math.floor((Date.now() - dt) / 1000)
  if (diff < 60) return '刚刚'
  if (diff < 3600) return Math.floor(diff / 60) + '分钟前'
  if (diff < 86400) return Math.floor(diff / 3600) + '小时前'
  if (diff < 604800) return Math.floor(diff / 86400) + '天前'
  return dt.toLocaleDateString('zh-CN')
}

/** 外部指定打开哪一条：桌面通知点击 → `/message?open=<id>`。
 *
 * 这条路径**只有 id、没有列表行**（通知来的时候列表可能还没加载），
 * 所以直接拉详情。拉不到就只是不展开 —— 列表还在那儿，别把页面搞崩。
 * 已读规则与点列表打开一致（非待办 → 打开即已读）。
 */
async function openById(id) {
  if (!id) return
  try {
    const m = await getMessage(id, uid())
    if (!m) return
    detail.value = m
    if (!m.is_read && !isTodo(m.type)) markRead(m, true)
  } catch { /* 详情拉不到就不展开，不打扰 */ }
}

// 角标与桌面通知的轮询**不在这里** —— 全站只有一个计时器，
// 在 `composables/useNotifications.js`，由 App.vue 启动。
onMounted(async () => {
  await boot()
  if (route.query.open) openById(route.query.open)
})
</script>

<style scoped>
.mc-page { height: calc(100vh - var(--jz-top, 0px)); overflow-y: auto;
  display: flex; justify-content: center; padding: 28px 20px; }
.mc-container { max-width: 820px; width: 100%; padding: 24px 30px; border-radius: 18px;
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent);
  backdrop-filter: blur(24px); -webkit-backdrop-filter: blur(24px);
  border: 1px solid var(--line-soft); box-shadow: 0 8px 32px rgba(0,0,0,.06);
  max-height: 92vh; overflow-y: auto; display: flex; flex-direction: column; }
.mc-container::-webkit-scrollbar { width: 4px; }
.mc-container::-webkit-scrollbar-thumb { background: rgba(128,128,128,.2); border-radius: 2px; }

.mc-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.header-left { display: flex; align-items: center; gap: 10px; }
.header-right { display: flex; align-items: center; gap: 8px; }
.header-logo { width: 28px; height: 28px; border-radius: 6px; }
.mc-header h1 { font-size: 20px; color: var(--text-primary); margin: 0; font-weight: 700; }
.total-badge { background: rgba(239,68,68,.15); color: #ef4444; font-size: 12px;
  font-weight: 700; padding: 1px 10px; border-radius: 12px; }

.g-btn { display: inline-flex; align-items: center; gap: 5px; padding: 7px 16px;
  font-size: 13px; font-weight: 500; color: var(--text-secondary);
  background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent);
  border: 1px solid rgba(255,255,255,.05); border-radius: 10px; cursor: pointer;
  transition: all .25s ease; font-family: inherit; }
.g-btn:hover:not(:disabled) { background: color-mix(in srgb, var(--surface, #ffffff) 8%, transparent);
  border-color: var(--line-soft); transform: translateY(-1px); }
.g-btn:disabled { opacity: .4; cursor: default; }
.g-btn.sm { padding: 5px 12px; font-size: 12px; }
.g-btn.icon-only { padding: 7px 10px; }
.g-btn.primary { color: #fff; border: none; font-weight: 600;
  background: linear-gradient(135deg, var(--c1, var(--brand)), var(--c2, var(--brand)));
  box-shadow: 0 4px 16px color-mix(in srgb, var(--c1, var(--brand)) 35%, transparent); }
.g-btn.danger { color: #f56c6c; }

/* Tab */
.tab-bar { display: flex; gap: 5px; flex-wrap: wrap; margin-bottom: 12px; }
.tab-btn { display: flex; align-items: center; gap: 6px; padding: 6px 14px; font-size: 13px;
  border-radius: 10px; border: 1px solid rgba(255,255,255,.05);
  background: color-mix(in srgb, var(--surface, #ffffff) 2%, transparent);
  color: var(--text-secondary); cursor: pointer; transition: all .25s ease; font-family: inherit; }
.tab-btn:hover { background: color-mix(in srgb, var(--surface, #ffffff) 6%, transparent); }
.tab-btn.active { color: var(--c); border-color: color-mix(in srgb, var(--c) 35%, transparent);
  background: color-mix(in srgb, var(--c) 12%, transparent); }
.tab-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--c); }
.tab-badge { background: color-mix(in srgb, var(--surface, #ffffff) 10%, transparent);
  color: var(--text-secondary); font-size: 10px; padding: 0 7px; border-radius: 8px;
  font-weight: 600; line-height: 18px; }
.tab-btn.active .tab-badge { background: var(--c); color: #fff; }

/* 列表 */
.mc-list { flex: 1; display: flex; flex-direction: column; gap: 8px; }
.mc-card { display: flex; align-items: flex-start; gap: 12px; padding: 13px 16px;
  border-radius: 12px; border: 1px solid rgba(255,255,255,.04);
  background: color-mix(in srgb, var(--surface, #ffffff) 2%, transparent);
  cursor: pointer; transition: all .2s ease; position: relative; overflow: hidden; }
.mc-card:hover { background: color-mix(in srgb, var(--surface, #ffffff) 5%, transparent);
  border-color: color-mix(in srgb, var(--c1) 40%, transparent); transform: translateX(3px); }
.mc-card .bar { position: absolute; left: 0; top: 0; bottom: 0; width: 3px; opacity: 0; }
.mc-card.unread { background: color-mix(in srgb, var(--c1) 5%, transparent); }
.mc-card.unread .bar { opacity: 1;
  background: linear-gradient(180deg, var(--c1), var(--c2)); }
.mc-card:not(.unread) { opacity: .78; }
.mc-icon { width: 38px; height: 38px; border-radius: 50%; flex: none; color: #fff;
  display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 15px;
  background: linear-gradient(135deg, var(--c1), var(--c2)); }
.mc-icon.lg { width: 44px; height: 44px; font-size: 17px;
  box-shadow: 0 4px 16px color-mix(in srgb, var(--c1) 40%, transparent); }
.mc-body { flex: 1; min-width: 0; }
.mc-top { display: flex; justify-content: space-between; align-items: center; gap: 10px; }
.mc-name { font-size: 14px; font-weight: 600; color: var(--text-primary); }
.todo-flag { font-size: 10px; color: #06B6D4; border: 1px solid rgba(6,182,212,.4);
  padding: 0 5px; border-radius: 6px; margin-right: 6px; vertical-align: 1px; }
.mc-time { font-size: 11px; color: var(--text-muted); flex-shrink: 0; }
.mc-preview { font-size: 13px; color: var(--text-secondary); margin-top: 3px;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
  overflow: hidden; line-height: 1.5; }
.mc-extra { display: flex; gap: 8px; align-items: center; margin-top: 8px; }
.count-tag { font-size: 11px; color: #fff; padding: 1px 8px; border-radius: 8px;
  background: linear-gradient(135deg, var(--c1), var(--c2)); font-weight: 700; }
.mc-arrow { flex-shrink: 0; color: var(--text-muted); opacity: .3; margin-top: 10px; }
.mc-card:hover .mc-arrow { opacity: 1; }
.mc-state { text-align: center; padding: 40px 20px; color: var(--text-muted); }
.mc-more { text-align: center; padding: 12px; font-size: 13px; color: var(--brand); cursor: pointer; }

/* ---- 详情：居中毛玻璃弹层 ---- */
.mc-mask { position: fixed; inset: 0; z-index: 3000; display: flex; align-items: center;
  justify-content: center; padding: 24px; background: rgba(6,6,14,.5);
  backdrop-filter: blur(6px); -webkit-backdrop-filter: blur(6px);
  opacity: 0; pointer-events: none; transition: opacity .2s; }
.mc-mask.on { opacity: 1; pointer-events: auto; }
.mc-modal { width: min(660px, 94vw); max-height: 84vh; display: flex; flex-direction: column;
  border-radius: 18px; overflow: hidden; position: relative;
  background: color-mix(in srgb, var(--surface, #ffffff) 92%, transparent);
  backdrop-filter: blur(24px) saturate(1.5); -webkit-backdrop-filter: blur(24px) saturate(1.5);
  border: 1px solid var(--line-soft); box-shadow: 0 24px 64px rgba(0,0,0,.35);
  transform: scale(.96) translateY(8px); transition: transform .22s ease; }
.mc-mask.on .mc-modal { transform: none; }
.modal-bar { height: 3px; flex: none;
  background: linear-gradient(90deg, var(--c1), var(--c2)); }
.modal-close { position: absolute; top: 10px; right: 12px; border: none; background: transparent;
  color: var(--text-muted); font-size: 17px; cursor: pointer; padding: 4px 8px; border-radius: 8px; }
.modal-close:hover { background: color-mix(in srgb, var(--surface, #ffffff) 8%, transparent); }
.modal-head { padding: 16px 22px 12px; border-bottom: 1px solid var(--line-soft); }
.modal-tag { display: flex; align-items: center; gap: 7px; font-size: 12px; color: var(--text-muted); }
.modal-tag .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--c1); }
.modal-title { display: flex; gap: 12px; align-items: center; margin-top: 12px; }
.modal-name { font-size: 17px; font-weight: 700; color: var(--text-primary); }
.modal-sub { font-size: 12px; color: var(--text-muted); margin-top: 2px; }
.modal-body { padding: 16px 22px; overflow-y: auto; flex: 1; }
.modal-text { font-size: 13.5px; line-height: 1.85; color: var(--text-primary);
  background: color-mix(in srgb, var(--c1) 7%, transparent);
  border-left: 3px solid var(--c1); padding: 12px 14px; border-radius: 0 10px 10px 0; }
/* 段落：段间留白，段内保留单换行（模型的正文常见「小标题\n正文」这种写法） */
.modal-text p { margin: 0; white-space: pre-line; }
.modal-text p + p { margin-top: 10px; }

/* ===== 昨日学习总结的结构化排版（2026-10-08）=====
   数字用卡片、知识点用标签、三段文字分开排 —— 改造前是一整块 150 字散文。 */
/* 卡片数量现在由后端决定（1~5 张），所以必须能换行 ——
   原来写死两列不换行，多出来的卡会挤成一条。 */
.sum-stats { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 16px; }
.sum-stat {
  flex: 1 1 calc(50% - 5px); min-width: 110px;
  padding: 14px 16px 12px; border-radius: 12px; text-align: center;
  background: color-mix(in srgb, var(--c1) 8%, transparent);
  border: 1px solid color-mix(in srgb, var(--c1) 18%, transparent);
}
.sum-stat b {
  display: block; font-size: 26px; font-weight: 700; line-height: 1.15;
  color: color-mix(in srgb, var(--c1) 78%, var(--text-primary));
  font-variant-numeric: tabular-nums;   /* 数字等宽，几个卡片才对得齐 */
}
.sum-stat b i { font-size: 15px; font-style: normal; margin-left: 1px; }
.sum-stat span { font-size: 12px; color: var(--text-muted); }
/* 口径说明（「仅统计已批改的 8 道」）。比正文小一档、更淡，
   是注解不是内容 —— 但它必须看得见。 */
.sum-stat em {
  display: block; margin-top: 4px; font-style: normal;
  font-size: 10px; line-height: 1.35; color: var(--text-muted); opacity: .75;
}

.sum-sec { margin-bottom: 14px; }
.sum-sec h5 { margin: 0 0 8px; font-size: 12px; color: var(--text-muted); font-weight: 600; }
.sum-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.sum-tag { font-size: 12px; padding: 4px 11px; border-radius: 20px; border: 1px solid transparent; }
.sum-tag.weak   { color: #F56C6C; background: rgba(245, 108, 108, .10); border-color: rgba(245, 108, 108, .22); }
.sum-tag.strong { color: #67C23A; background: rgba(103, 194, 58, .10); border-color: rgba(103, 194, 58, .22); }

.sum-note { margin: 14px 0 0; font-size: 13.5px; line-height: 1.85; color: var(--text-primary); }
.sum-tip {
  display: flex; gap: 10px; margin-top: 12px; padding: 12px 14px; border-radius: 0 10px 10px 0;
  border-left: 3px solid var(--c1);
  background: color-mix(in srgb, var(--c1) 9%, transparent);
  font-size: 13px; line-height: 1.8; color: var(--text-secondary);
}
.sum-tip b { flex: none; color: color-mix(in srgb, var(--c1) 78%, var(--text-primary)); }
.sum-enc { margin: 12px 0 0; font-size: 12.5px; color: var(--text-muted); text-align: right; }
/* ===== 详情体的七种形态（2026-10-08）=====
   形态由后端注册表给（`_shape_of`），前端按 `shape` 分发。
   （`.modal-sec` / `.actor-row` 是改造前聚合明细的朴素样式，已随新形态删掉。） */

/* --- ③ actors：聚合型。「谁做的」是这个形态存在的理由 --- */
.act-head { display: flex; align-items: baseline; gap: 6px; margin-bottom: 10px; }
.act-n { font-size: 28px; font-weight: 700; line-height: 1;
  color: color-mix(in srgb, var(--c1) 78%, var(--text-primary));
  font-variant-numeric: tabular-nums; }
.act-unit { font-size: 12.5px; color: var(--text-muted); }
.act-chips { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 14px; }
.act-chip {
  display: inline-flex; align-items: center; gap: 7px;
  padding: 4px 12px 4px 4px; border-radius: 20px; font-size: 12.5px;
  color: var(--text-secondary);
  background: color-mix(in srgb, var(--surface, #ffffff) 5%, transparent);
  border: 1px solid var(--line-soft);
}
.act-av {
  width: 20px; height: 20px; border-radius: 50%; flex: none;
  display: flex; align-items: center; justify-content: center;
  font-size: 10px; font-weight: 600; color: #fff;
  background: linear-gradient(135deg, var(--c1), var(--c2));
}

/* --- ④ todo：待办。说清「为什么还没已读」 --- */
.td-banner {
  display: flex; align-items: center; gap: 9px; margin-bottom: 12px;
  padding: 10px 14px; border-radius: 10px; font-size: 12.5px;
  color: #B88230; background: rgba(230, 162, 60, .12);
  border: 1px solid rgba(230, 162, 60, .25);
}
.td-banner b { color: #E6A23C; }

/* --- ⑤ notice：系统 / 账号类正式通知 --- */
.nt-head { display: flex; align-items: center; gap: 9px; margin-bottom: 12px; }
.nt-ic {
  width: 28px; height: 28px; border-radius: 9px; flex: none;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; color: #fff;
  background: linear-gradient(135deg, var(--c1), var(--c2));
}
.nt-label { font-size: 12.5px; color: var(--text-muted); letter-spacing: .02em; }

/* --- ⑥ celebrate：学程成就 / 晋升 --- */
.cb-badge {
  width: 56px; height: 56px; margin: 4px auto 14px; border-radius: 18px;
  display: flex; align-items: center; justify-content: center;
  font-size: 24px; color: #fff;
  background: linear-gradient(135deg, var(--c1), var(--c2));
  box-shadow: 0 8px 24px color-mix(in srgb, var(--c1) 40%, transparent);
}
.modal-text.center { text-align: center; border-left: none; border-radius: 10px; }

/* --- 通用：详情里的通栏按钮 --- */
.g-btn.wide { width: 100%; justify-content: center; margin-top: 14px; }
.modal-foot { padding: 12px 22px; border-top: 1px solid var(--line-soft);
  display: flex; gap: 8px; flex: none; }
.modal-foot .g-btn { flex: 1; justify-content: center; }

/* ---- 每日推荐：详情里只做预览，真正的「做」在 /daily-learn ----
   ⚠️ 这一块换掉了原来那套 .rec-tabs/.rec-panel/.rec-q/.rec-opt（就地执行面板）。
   那套面板的「提交」是空壳，2026-10-08 改成独立学习页后它就没用了 ——
   规则一并删掉，不留死 CSS（这个项目对「定义了没人用」的规则栽过跟头）。 */
.rec-preview { display: flex; flex-direction: column; gap: 6px; margin-bottom: 12px; }
.rec-p-row {
  display: flex; align-items: center; gap: 9px;
  padding: 9px 12px; border-radius: 10px; font-size: 13px;
  color: var(--text-secondary);
  background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent);
  border: 1px solid var(--line-soft);
}
.rec-p-no { color: var(--c1); font-size: 12px; }
.rec-p-name { flex: 1; }
.rec-p-meta { font-size: 12px; color: var(--text-muted); }
.rec-p-done { font-size: 11.5px; color: var(--text-muted); padding-left: 2px; }

@media (max-width: 640px) {
  .mc-page { padding: 10px 8px; }
  .mc-container { padding: 14px 12px; max-height: 96vh; }
  .mc-header h1 { font-size: 17px; }
  .mc-modal { width: 96vw; max-height: 92vh; }
}
</style>
