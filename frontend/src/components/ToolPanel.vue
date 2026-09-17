<template>
  <Teleport to="body">
    <transition name="panel-slide">
      <div v-if="panelTool" class="tool-panel-overlay" @click.self="closeToolPanel">
        <div class="tool-panel">
          <div class="tp-header">
            <span class="tp-title">{{ panelTitle }}</span>
            <button class="tp-close" @click="closeToolPanel">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
            </button>
          </div>
          <div class="tp-body">
            <!-- 打卡 -->
            <template v-if="panelTool === 'checkin'">
              <div v-if="checkinProjects.length" class="tp-list">
                <div v-for="p in checkinProjects" :key="p.name" class="tp-item">
                  <div class="tp-item-info">
                    <span class="tp-item-name">{{ p.name }}</span>
                    <span class="tp-item-meta">{{ p.completed_days }} / {{ p.target_days }} 天</span>
                    <el-progress :percentage="Math.round((p.completed_days / p.target_days) * 100)" :stroke-width="5" :color="p.completed_days >= p.target_days ? '#67c23a' : themeStore.brandColor" />
                  </div>
                  <el-button size="small" :type="p.last_checkin === today ? 'info' : 'success'" :disabled="p.last_checkin === today" @click="doCheckin(p.name)">{{ p.last_checkin === today ? '已打卡' : '打卡' }}</el-button>
                </div>
              </div>
              <div v-else class="tp-empty">暂无打卡项目</div>
              <div class="tp-add">
                <el-input v-model="newCheckinName" placeholder="项目名称" size="small" style="width:110px" />
                <el-input-number v-model="newCheckinTarget" :min="1" :max="365" size="small" style="width:80px" />
                <el-button size="small" type="primary" @click="addCheckin">添加</el-button>
              </div>
            </template>
            <!-- 时间胶囊（2026-08-26 倒计时改版） -->
            <template v-if="panelTool === 'countdown'">
              <div class="tp-capsule">
                <!-- 新建胶囊 -->
                <div class="tp-cap-create">
                  <div class="tp-cap-create-head">
                    <span class="tp-cap-create-title">✍️ 写一颗时间胶囊</span>
                    <span class="tp-cap-limit" :class="{ full: capsulesFull }">{{ countdownEvents.length }} / 50</span>
                  </div>
                  <el-input v-model="newCapTitle" placeholder="胶囊标题（如：考研上岸那天）" size="small" maxlength="30" show-word-limit />
                  <el-date-picker v-model="newCapDate" type="date" placeholder="开启日期（须选未来某天）" size="small" style="width:100%" value-format="YYYY-MM-DD" :disabled-date="disablePastDates" />
                  <el-input v-model="newCapMsg" type="textarea" :rows="3" maxlength="500" show-word-limit placeholder="写下第一条留言（可选）……" />
                  <el-button type="primary" size="small" class="tp-cap-seal-btn" :disabled="!canCreateCapsule" @click="createCapsule">🔒 封存胶囊</el-button>
                </div>

                <!-- 封存动画舞台（方向：写留言 → 壳闭合 → 封印盖下 → 落入列表） -->
                <div v-if="sealStage" class="tp-cap-stage" :class="'phase-' + sealStage.phase">
                  <div class="tp-cap-shell">
                    <div class="tp-cap-half tp-cap-top"></div>
                    <div class="tp-cap-sparkles"><i v-for="n in 6" :key="n"></i></div>
                    <div class="tp-cap-seal-ring"></div>
                    <div class="tp-cap-half tp-cap-bottom"></div>
                  </div>
                  <div class="tp-cap-stage-title">{{ sealStage.title }}</div>
                  <div class="tp-cap-stage-hint">{{ sealHint }}</div>
                </div>

                <!-- 胶囊列表 -->
                <div v-if="countdownEvents.length" class="tp-capsule-list">
                  <transition-group name="cap-list">
                    <div v-for="c in sortedCapsules" :key="c.id" class="tp-cap-card" :class="capsuleState(c)">
                      <!-- 密封中：只看倒计时，只能追加留言 -->
                      <template v-if="capsuleState(c) === 'sealed'">
                        <div class="tp-cap-card-head">
                          <span class="tp-cap-card-title">{{ c.title }}</span>
                          <span class="tp-cap-badge">🔒 密封中</span>
                        </div>
                        <div class="tp-cap-countdown">{{ countdownText(c) }}</div>
                        <div class="tp-cap-meta">创建于 {{ fmtDate(c.created_at) }} · 已写 {{ c.entries.length }} 条</div>
                        <div class="tp-cap-sealed-area">🔒 内容已密封，共 {{ c.entries.length }} 条留言，{{ fmtOpenDate(c.target_date) }}开启后可见</div>
                        <el-button size="small" class="tp-cap-add-msg" :disabled="animBusy" @click="toggleAppend(c)">{{ appendingId === c.id ? '收起' : '＋ 添加留言' }}</el-button>
                        <div v-if="appendingId === c.id" class="tp-cap-append">
                          <el-input v-model="appendMsg" type="textarea" :rows="2" maxlength="500" placeholder="写下想对未来的自己说的话…" />
                          <div class="tp-cap-append-btns">
                            <el-button size="small" @click="cancelAppend">取消</el-button>
                            <el-button size="small" type="primary" :disabled="!appendMsg.trim()" @click="appendEntry(c)">🔒 封存留言</el-button>
                          </div>
                        </div>
                      </template>
                      <!-- 待开启：到期未开启，橙色高亮 + 开启仪式 -->
                      <template v-else-if="capsuleState(c) === 'due'">
                        <div class="tp-cap-card-head">
                          <span class="tp-cap-card-title">{{ c.title }}</span>
                          <span class="tp-cap-badge due">⏰ 待开启</span>
                        </div>
                        <div class="tp-cap-meta">开启日期 {{ c.target_date }} 已到 · 共 {{ c.entries.length }} 条留言</div>
                        <div v-if="openingId !== c.id" class="tp-cap-sealed-area">🔒 内容已密封，点击下方按钮开启</div>
                        <!-- 破封动画（方向：封印破裂 → 光缝涌出 → 壳展开） -->
                        <div v-else class="tp-cap-open-stage" :class="'ophase-' + openPhase">
                          <div class="tp-cap-shell mini">
                            <div class="tp-cap-half tp-cap-top"></div>
                            <div class="tp-cap-rays"></div>
                            <div class="tp-cap-crack"></div>
                            <div class="tp-cap-seal-ring"></div>
                            <div class="tp-cap-half tp-cap-bottom"></div>
                          </div>
                          <div class="tp-cap-open-hint">{{ openHint }}</div>
                        </div>
                        <el-button v-if="openingId !== c.id" size="small" type="warning" class="tp-cap-open-btn" :disabled="animBusy" @click="openCapsule(c)">✨ 开启胶囊</el-button>
                      </template>
                      <!-- 已开启：全部留言展开（时间戳），可删除 -->
                      <template v-else>
                        <div class="tp-cap-card-head">
                          <span class="tp-cap-card-title">{{ c.title }}</span>
                          <div class="tp-cap-head-right">
                            <span class="tp-cap-badge opened">✅ 已开启</span>
                            <button class="tp-del" title="删除胶囊" @click="delCapsule(c)"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg></button>
                          </div>
                        </div>
                        <div class="tp-cap-meta">开启于 {{ fmtDateTime(c.opened_at) }}</div>
                        <div class="tp-cap-entries">
                          <div v-for="(en, i) in c.entries" :key="i" class="tp-cap-entry" :class="{ 'cap-just-opened': justOpenedId === c.id }" :style="{ '--i': i }">
                            <div class="tp-cap-entry-time">{{ fmtDateTime(en.created_at) }}</div>
                            <div class="tp-cap-entry-text">{{ en.content }}</div>
                          </div>
                          <div v-if="!c.entries.length" class="tp-cap-entry-empty">这颗胶囊没有留言</div>
                        </div>
                      </template>
                    </div>
                  </transition-group>
                </div>
                <div v-else class="tp-empty">还没有时间胶囊，写下第一颗吧</div>
              </div>
            </template>
            <!-- 计时器 -->
            <template v-if="panelTool === 'timer'">
              <div v-if="activeTimerComp" class="tp-timer-active">
                <div class="tp-timer-display">
                  <span class="tp-timer-name">{{ activeTimerComp.name }}</span>
                  <span class="tp-timer-time">{{ formatTimeComp(activeTimerComp.displaySeconds) }}</span>
                </div>
                <div class="tp-timer-ctls">
                  <el-button size="small" @click="pauseTimerComp">{{ activeTimerComp.paused ? '继续' : '暂停' }}</el-button>
                  <el-button size="small" type="danger" @click="stopTimerComp">取消</el-button>
                  <el-button v-if="activeTimerComp.type === 'stopwatch'" size="small" type="success" @click="completeStopwatchComp">完成</el-button>
                </div>
              </div>
              <div v-if="timerTemplates.length" class="tp-list">
                <div v-for="t in timerTemplates" :key="t.id" class="tp-item">
                  <div class="tp-item-info">
                    <span class="tp-item-name">{{ t.name }}</span>
                    <span class="tp-item-meta">{{ t.type === 'countdown' ? '⏳ 倒计时 ' + t.duration_minutes + '分钟' : '⏱️ 正向计时' }}</span>
                  </div>
                  <el-button size="small" type="primary" :disabled="!!activeTimerComp" @click="startTimerComp(t)">开始</el-button>
                </div>
              </div>
              <div v-else class="tp-empty">暂无计时器模板</div>
              <div class="tp-add">
                <el-input v-model="newTimerName" placeholder="任务名称" size="small" style="width:100px" />
                <el-select v-model="newTimerType" size="small" style="width:90px">
                  <el-option label="倒计时" value="countdown" />
                  <el-option label="正向计时" value="stopwatch" />
                </el-select>
                <el-input-number v-if="newTimerType === 'countdown'" v-model="newTimerDuration" :min="1" :max="180" size="small" style="width:80px" />
                <el-button size="small" type="primary" @click="addTimer">添加</el-button>
              </div>
            </template>
          </div>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<script setup>
// ===== 工具面板（2026-08-25 从 Sidebar 抽出，主界面中枢与学程/社区侧边栏共用）
// 打卡 / 倒计时 / 计时器；使用数据打点 xiaoji_tool 归小基
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useToolsStore } from '@/stores/tools'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import { recordAction } from '@/api/career'

onMounted(() => {
  // 预加载工具数据（打卡/倒计时/计时器）
  if (!authStore.user?.id) return
  toolsStore.loadCheckin(authStore.user.id)
  toolsStore.loadCountdown(authStore.user.id)
  toolsStore.loadTimer(authStore.user.id)
})

onUnmounted(() => {
  if (capTickInt) clearInterval(capTickInt)
  sealTimers.forEach(clearTimeout)
  openTimers.forEach(clearTimeout)
})

const toolsStore = useToolsStore()
const authStore = useAuthStore()
const themeStore = useThemeStore()

const panelTool = ref(null)
const panelTitle = computed(() => ({ checkin: '打卡', countdown: '时间胶囊', timer: '计时器' }[panelTool.value] || ''))

const today = new Date().toISOString().slice(0, 10)

function openTool(tool) {
  if (panelTool.value === tool) { closeToolPanel(); return }
  panelTool.value = tool
}
function closeToolPanel() { panelTool.value = null }

// 打卡
const checkinProjects = computed(() => toolsStore.checkinProjects)
const newCheckinName = ref('')
const newCheckinTarget = ref(30)
function doCheckin(name) { toolsStore.doCheckin(name); toolsStore.saveCheckinData(authStore.user.id, toolsStore.checkinProjects); recordAction(authStore.user.id, 'checkin'); recordAction(authStore.user.id, 'xiaoji_tool', { tool: 'checkin' }) }
function addCheckin() { if (!newCheckinName.value) return; toolsStore.addCheckinProject(newCheckinName.value, newCheckinTarget.value); toolsStore.saveCheckinData(authStore.user.id, toolsStore.checkinProjects); newCheckinName.value = '' }

// ===== 时间胶囊（2026-08-26 倒计时改版）=====
// 状态：密封中（未到期）/ 待开启（到期未开）/ 已开启（opened_at 非空）
const countdownEvents = computed(() => toolsStore.countdownEvents)
const CAP_LIMIT = 50
const capsulesFull = computed(() => countdownEvents.value.length >= CAP_LIMIT)

const newCapTitle = ref('')
const newCapDate = ref('')
const newCapMsg = ref('')
const canCreateCapsule = computed(() => !!newCapTitle.value.trim() && !!newCapDate.value && !animBusy.value && !capsulesFull.value)

// 实时秒针：驱动倒计时文本与密封→待开启状态翻转（面板打开倒计时时每秒一跳）
const nowTick = ref(Date.now())
let capTickInt = null
watch(panelTool, (t) => {
  if (t === 'countdown' && !capTickInt) capTickInt = setInterval(() => { nowTick.value = Date.now() }, 1000)
  else if (t !== 'countdown' && capTickInt) { clearInterval(capTickInt); capTickInt = null }
})

const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches

function todayStr() {
  void nowTick.value
  const d = new Date()
  const pad = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

function capsuleState(c) {
  if (c.opened_at) return 'opened'
  return c.target_date <= todayStr() ? 'due' : 'sealed'
}

// 排序：待开启 > 密封中（临近在前）> 已开启（最近开启在前）
const sortedCapsules = computed(() => {
  const rank = { due: 0, sealed: 1, opened: 2 }
  return [...countdownEvents.value].sort((a, b) => {
    const r = rank[capsuleState(a)] - rank[capsuleState(b)]
    if (r) return r
    if (capsuleState(a) === 'opened') return new Date(b.opened_at) - new Date(a.opened_at)
    return a.target_date.localeCompare(b.target_date)
  })
})

function countdownText(c) {
  const target = new Date(c.target_date + 'T00:00:00')
  const diff = target.getTime() - nowTick.value
  if (diff <= 0) return '已到开启时间'
  const days = Math.floor(diff / 86400000)
  const h = Math.floor((diff % 86400000) / 3600000)
  const m = Math.floor((diff % 3600000) / 60000)
  const s = Math.floor((diff % 60000) / 1000)
  const pad = n => String(n).padStart(2, '0')
  return `${days}天 ${pad(h)}:${pad(m)}:${pad(s)}`
}

function fmtDate(iso) { return (iso || '').slice(0, 10) }
function fmtDateTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const pad = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}
function fmtOpenDate(dateStr) {
  const parts = (dateStr || '').split('-')
  return parts.length === 3 ? `${parseInt(parts[1])}月${parseInt(parts[2])}日` : dateStr
}
// 今天及过去不可选：胶囊须有密封期，新封存的胶囊必定显示「密封中」
function disablePastDates(d) { return d.getTime() < new Date(todayStr() + 'T00:00:00').getTime() + 86400000 }

// ===== 封存动画 =====
const sealStage = ref(null)
const animBusy = ref(false)
let sealTimers = []
const sealHint = computed(() => ({ approach: '正在书写…', close: '壳身合拢…', seal: '封印盖上…', drop: '落入胶囊库…' }[sealStage.value?.phase] || ''))

function createCapsule() {
  if (!canCreateCapsule.value) {
    if (capsulesFull.value) ElMessage.warning('胶囊已达上限 50 颗，先开启一些旧的吧')
    else if (!newCapTitle.value.trim() || !newCapDate.value) ElMessage.warning('请填写胶囊标题和开启日期')
    else if (newCapDate.value <= todayStr()) ElMessage.warning('开启日期必须是未来的某天')
    return
  }
  const title = newCapTitle.value.trim()
  const date = newCapDate.value
  const msg = newCapMsg.value.trim()
  animBusy.value = true
  const finish = () => {
    toolsStore.addCapsule(title, date, msg)
    toolsStore.saveCountdownData(authStore.user.id, toolsStore.countdownEvents)
    recordAction(authStore.user.id, 'xiaoji_tool', { tool: 'countdown', action: 'create' })
    newCapTitle.value = ''; newCapDate.value = ''; newCapMsg.value = ''
    animBusy.value = false
    ElMessage.success('胶囊已封存')
  }
  if (reducedMotion) { finish(); return }
  sealStage.value = { title, phase: 'approach' }
  sealTimers = [
    setTimeout(() => { sealStage.value.phase = 'close' }, 550),
    setTimeout(() => { sealStage.value.phase = 'seal' }, 1100),
    setTimeout(() => { sealStage.value.phase = 'drop' }, 1700),
    setTimeout(() => { sealStage.value = null; finish() }, 2350)
  ]
}

// ===== 追加留言（仅密封期，每条带时间戳） =====
const appendingId = ref(null)
const appendMsg = ref('')
function toggleAppend(c) { appendingId.value = appendingId.value === c.id ? null : c.id; appendMsg.value = '' }
function cancelAppend() { appendingId.value = null; appendMsg.value = '' }
function appendEntry(c) {
  if (!appendMsg.value.trim()) return
  toolsStore.appendCapsuleEntry(c.id, appendMsg.value.trim())
  toolsStore.saveCountdownData(authStore.user.id, toolsStore.countdownEvents)
  recordAction(authStore.user.id, 'xiaoji_tool', { tool: 'countdown', action: 'append' })
  appendingId.value = null; appendMsg.value = ''
  ElMessage.success('留言已封存')
}

// ===== 开启仪式（手动开启：破封 → 光缝 → 壳展开 → 留言逐条浮现） =====
const openingId = ref(null)
const openPhase = ref('crack')
const justOpenedId = ref(null)
let openTimers = []
const openHint = computed(() => ({ crack: '封印破裂…', leak: '光芒涌出…', open: '壳身展开…' }[openPhase.value] || ''))

function openCapsule(c) {
  if (animBusy.value) return
  animBusy.value = true
  const finish = () => {
    toolsStore.openCapsule(c.id)
    toolsStore.saveCountdownData(authStore.user.id, toolsStore.countdownEvents)
    recordAction(authStore.user.id, 'xiaoji_tool', { tool: 'countdown', action: 'open' })
    justOpenedId.value = c.id
    setTimeout(() => { justOpenedId.value = null }, 3200)
    animBusy.value = false
    ElMessage.success('胶囊已开启')
  }
  if (reducedMotion) { finish(); return }
  openingId.value = c.id
  openPhase.value = 'crack'
  openTimers = [
    setTimeout(() => { openPhase.value = 'leak' }, 500),
    setTimeout(() => { openPhase.value = 'open' }, 1000),
    setTimeout(() => { openingId.value = null; finish() }, 1550)
  ]
}

// ===== 删除（仅已开启，清理用） =====
function delCapsule(c) {
  ElMessageBox.confirm(`确定删除「${c.title}」吗？留言将无法找回`, '删除胶囊', { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' })
    .then(() => {
      toolsStore.deleteCountdownEvent(c.id)
      toolsStore.saveCountdownData(authStore.user.id, toolsStore.countdownEvents)
      ElMessage.success('胶囊已删除')
    })
    .catch(() => {})
}

// 计时器
const timerTemplates = computed(() => toolsStore.timerTemplates)
const activeTimerComp = ref(null)
let timerInt = null
const newTimerName = ref('')
const newTimerType = ref('countdown')
const newTimerDuration = ref(25)
function formatTimeComp(s) { return `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}` }
function startTimerComp(t) { if (activeTimerComp.value) return; recordAction(authStore.user.id, 'xiaoji_tool', { tool: 'timer' }); const total = t.type === 'countdown' ? t.duration_minutes * 60 : 0; activeTimerComp.value = { id: t.id, name: t.name, type: t.type, displaySeconds: total, paused: false }; timerInt = setInterval(() => { if (!activeTimerComp.value || activeTimerComp.value.paused) return; if (activeTimerComp.value.type === 'countdown') { activeTimerComp.value.displaySeconds--; if (activeTimerComp.value.displaySeconds <= 0) { clearInterval(timerInt); activeTimerComp.value.displaySeconds = 0 } } else { activeTimerComp.value.displaySeconds++ } }, 1000) }
function pauseTimerComp() { if (!activeTimerComp.value) return; activeTimerComp.value.paused = !activeTimerComp.value.paused }
function stopTimerComp() { clearInterval(timerInt); timerInt = null; activeTimerComp.value = null }
async function completeStopwatchComp() { if (!activeTimerComp.value || activeTimerComp.value.type !== 'stopwatch') return; if (activeTimerComp.value.displaySeconds > 0) { recordAction(authStore.user.id, 'xiaoji_tool', { tool: 'stopwatch' }) } stopTimerComp() }
function addTimer() { if (!newTimerName.value) return; toolsStore.addTimerTemplate(newTimerName.value, newTimerType.value, newTimerDuration.value); toolsStore.saveTimerData(authStore.user.id, toolsStore.timerTemplates); newTimerName.value = '' }

defineExpose({ openTool, closeToolPanel })
</script>

<style>
/* ===== 工具面板（右侧滑出毛玻璃，2026-08-25 随组件从 Sidebar 迁入） ===== */
.tool-panel-overlay {
  position: fixed; inset: 0; z-index: 200;
  background: rgba(0,0,0,.25);
  display: flex; justify-content: flex-end;
}
.tool-panel {
  width: 380px; max-width: 90vw; height: 100vh;
  background: linear-gradient(170deg, rgba(255,255,255,.06), rgba(255,255,255,.02));
  backdrop-filter: blur(28px) saturate(1.2);
  -webkit-backdrop-filter: blur(28px) saturate(1.2);
  border-left: 1px solid rgba(255,255,255,.06);
  display: flex; flex-direction: column;
  padding: 20px;
  overflow-y: auto;
}
.tp-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
.tp-title { font-size: 18px; font-weight: 700; color: var(--text-primary); }
.tp-close {
  width: 32px; height: 32px; border-radius: 8px; border: 1px solid var(--line-soft);
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent); color: var(--text-secondary); cursor: pointer;
  display: flex; align-items: center; justify-content: center; transition: all .2s;
}
.tp-close:hover { background: color-mix(in srgb, var(--surface, #ffffff) 10%, transparent); color: var(--text-primary); }
.tp-close svg { width: 16px; height: 16px; }
.tp-body { flex: 1; overflow-y: auto; }
.tp-list { display: flex; flex-direction: column; gap: 8px; }
.tp-item {
  display: flex; align-items: center; gap: 12px; padding: 12px 14px;
  border-radius: 10px; background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent); border: 1px solid var(--line-soft);
}
.tp-item-info { flex: 1; min-width: 0; }
.tp-item-name { font-size: 13px; font-weight: 600; color: var(--text-primary); }
.tp-item-meta { font-size: 11px; color: var(--text-muted); margin-top: 2px; display: block; }
.tp-empty { text-align: center; padding: 40px 0; color: var(--text-muted); font-size: 14px; }
.tp-add { display: flex; gap: 8px; margin-top: 16px; flex-wrap: wrap; align-items: center; }
.tp-del {
  width: 24px; height: 24px; border: none; background: transparent; color: var(--text-muted);
  cursor: pointer; border-radius: 4px; display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; transition: all .2s;
}
.tp-del:hover { color: #ef4444; background: rgba(239,68,68,.08); }
.tp-del svg { width: 12px; height: 12px; }
.tp-timer-active {
  padding: 16px; border-radius: 12px; margin-bottom: 16px;
  background: rgba(168,85,247,.08); border: 1px solid rgba(168,85,247,.15);
}
.tp-timer-display { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.tp-timer-name { font-size: 14px; color: var(--text-primary); }
.tp-timer-time { font-size: 28px; font-weight: 700; color: color-mix(in srgb, #a78bfa 62%, var(--text-primary)); font-variant-numeric: tabular-nums; }
.tp-timer-ctls { display: flex; gap: 6px; }

/* ===== 时间胶囊（2026-08-26 倒计时改版） ===== */
.tp-capsule { display: flex; flex-direction: column; gap: 12px; }
.tp-cap-create {
  padding: 12px; border-radius: 12px; display: flex; flex-direction: column; gap: 8px;
  background: rgba(139,92,246,.06); border: 1px solid rgba(139,92,246,.14);
}
.tp-cap-create-head { display: flex; align-items: center; justify-content: space-between; }
.tp-cap-create-title { font-size: 13px; font-weight: 600; color: color-mix(in srgb, #c4b5fd 62%, var(--text-primary)); }
.tp-cap-limit { font-size: 11px; color: var(--text-muted); font-variant-numeric: tabular-nums; }
.tp-cap-limit.full { color: color-mix(in srgb, #f59e0b 70%, var(--text-primary)); }
.tp-cap-seal-btn { align-self: flex-end; }

/* 胶囊卡 */
.tp-capsule-list { display: flex; flex-direction: column; gap: 10px; }
.tp-cap-card {
  position: relative; padding: 12px 14px; border-radius: 12px;
  background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent); border: 1px solid var(--line-soft);
  transition: border-color .3s, box-shadow .3s;
}
.tp-cap-card.due { border-color: rgba(245,158,11,.45); box-shadow: 0 0 18px rgba(245,158,11,.12); }
.tp-cap-card-head { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 6px; }
.tp-cap-head-right { display: flex; align-items: center; gap: 6px; }
.tp-cap-card-title { font-size: 14px; font-weight: 600; color: var(--text-primary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.tp-cap-badge { font-size: 11px; color: color-mix(in srgb, #a78bfa 62%, var(--text-primary)); background: rgba(139,92,246,.12); padding: 2px 8px; border-radius: 999px; flex-shrink: 0; }
.tp-cap-badge.due { color: color-mix(in srgb, #f59e0b 70%, var(--text-primary)); background: rgba(245,158,11,.14); animation: capBadgePulse 1.6s ease-in-out infinite; }
.tp-cap-badge.opened { color: color-mix(in srgb, #67c23a 62%, var(--text-primary)); background: rgba(103,194,58,.12); }
@keyframes capBadgePulse { 50% { opacity: .55; } }
.tp-cap-countdown {
  font-size: 20px; font-weight: 700; color: color-mix(in srgb, #c4b5fd 62%, var(--text-primary)); font-variant-numeric: tabular-nums;
  letter-spacing: .5px; margin-bottom: 4px; text-shadow: 0 0 14px rgba(139,92,246,.45);
}
.tp-cap-meta { font-size: 11px; color: var(--text-muted); margin-bottom: 8px; }
.tp-cap-sealed-area {
  font-size: 12px; color: var(--text-muted); padding: 10px 12px; border-radius: 8px;
  background: var(--well); border: 1px dashed var(--line-strong);
  margin-bottom: 10px; line-height: 1.6;
}
.tp-cap-add-msg { width: 100%; margin-bottom: 8px; }
.tp-cap-append { display: flex; flex-direction: column; gap: 8px; margin-bottom: 4px; }
.tp-cap-append-btns { display: flex; justify-content: flex-end; gap: 6px; }
.tp-cap-open-btn { width: 100%; }
.tp-cap-entries { display: flex; flex-direction: column; gap: 8px; }
.tp-cap-entry {
  padding: 9px 11px; border-radius: 8px; font-size: 12px; color: var(--text-secondary);
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent); border-left: 2px solid rgba(139,92,246,.5);
  line-height: 1.6; word-break: break-word;
}
.tp-cap-entry.cap-just-opened { animation: capEntryIn .55s cubic-bezier(.34,1.4,.64,1) both; animation-delay: calc(var(--i, 0) * 130ms); }
@keyframes capEntryIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: none; } }
.tp-cap-entry-time { font-size: 10px; color: var(--text-muted); margin-bottom: 3px; }
.tp-cap-entry-empty { font-size: 12px; color: var(--text-muted); text-align: center; padding: 8px 0; }

/* ===== 封存动画舞台 ===== */
.tp-cap-stage {
  position: relative; height: 170px; border-radius: 12px; overflow: hidden;
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8px;
  background: radial-gradient(ellipse at 50% 55%, rgba(139,92,246,.14), transparent 70%);
  border: 1px solid rgba(139,92,246,.16);
}
.tp-cap-stage-title { font-size: 13px; font-weight: 600; color: var(--text-primary); max-width: 80%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.tp-cap-stage-hint { font-size: 11px; color: color-mix(in srgb, #8b5cf6 60%, var(--text-primary)); }

/* 胶囊壳（两瓣 + 封印环） */
.tp-cap-shell { position: relative; width: 64px; height: 116px; margin: 12px 0 2px; }
.tp-cap-half {
  position: absolute; left: 0; width: 64px; height: 58px;
  background: linear-gradient(160deg, rgba(196,181,253,.30), rgba(139,92,246,.12));
  border: 1.5px solid rgba(196,181,253,.55);
  backdrop-filter: blur(4px);
  box-shadow: inset 0 0 16px rgba(167,139,250,.28);
  transition: transform .5s cubic-bezier(.4,0,.2,1), opacity .4s;
}
.tp-cap-top { top: 0; border-radius: 32px 32px 6px 6px; }
.tp-cap-bottom { bottom: 0; border-radius: 6px 6px 32px 32px; }
.tp-cap-seal-ring {
  position: absolute; left: 50%; top: 50%; width: 72px; height: 13px; z-index: 3;
  transform: translate(-50%, -50%);
  background: linear-gradient(90deg, transparent 4%, rgba(250,204,21,.95) 18%, rgba(253,224,71,1) 50%, rgba(250,204,21,.95) 82%, transparent 96%);
  border-radius: 7px; box-shadow: 0 0 16px rgba(250,204,21,.85);
  transition: transform .45s cubic-bezier(.3,1.3,.4,1), opacity .3s;
}
/* approach：壳分开 + 封印环悬于上方 */
.tp-cap-stage.phase-approach .tp-cap-top { transform: translateY(-24px); }
.tp-cap-stage.phase-approach .tp-cap-bottom { transform: translateY(24px); }
.tp-cap-stage.phase-approach .tp-cap-seal-ring { transform: translate(-50%, -70px); opacity: 0; }
/* close：壳合拢（封印环仍悬于上方等待落下） */
.tp-cap-stage.phase-close .tp-cap-top,
.tp-cap-stage.phase-close .tp-cap-bottom { transform: translateY(0); }
.tp-cap-stage.phase-close .tp-cap-seal-ring { transform: translate(-50%, -70px); opacity: 0; }
/* seal：封印环落下锁定 + 火花迸发 */
.tp-cap-stage.phase-seal .tp-cap-seal-ring { transform: translate(-50%, -50%); animation: capRingLock .4s ease-out; }
@keyframes capRingLock {
  0% { transform: translate(-50%, -70px); }
  60% { transform: translate(-50%, -46%) scale(1.12); }
  100% { transform: translate(-50%, -50%) scale(1); }
}
.tp-cap-stage.phase-seal .tp-cap-shell { animation: capSquash .35s ease-out; }
@keyframes capSquash { 40% { transform: scaleY(.94); } }
.tp-cap-sparkles { position: absolute; left: 50%; top: 50%; z-index: 4; width: 0; height: 0; }
.tp-cap-sparkles i {
  position: absolute; width: 5px; height: 5px; border-radius: 50%;
  background: #fde047; box-shadow: 0 0 8px #fde047;
  opacity: 0; transform: translate(-50%, -50%);
}
.tp-cap-stage.phase-seal .tp-cap-sparkles i { animation: capSpark .7s ease-out forwards; }
.tp-cap-stage.phase-seal .tp-cap-sparkles i:nth-child(1) { --dx: -34px; --dy: -10px; animation-delay: 0ms; }
.tp-cap-stage.phase-seal .tp-cap-sparkles i:nth-child(2) { --dx: 34px; --dy: -10px; animation-delay: 40ms; }
.tp-cap-stage.phase-seal .tp-cap-sparkles i:nth-child(3) { --dx: -26px; --dy: 8px; animation-delay: 80ms; }
.tp-cap-stage.phase-seal .tp-cap-sparkles i:nth-child(4) { --dx: 26px; --dy: 8px; animation-delay: 120ms; }
.tp-cap-stage.phase-seal .tp-cap-sparkles i:nth-child(5) { --dx: -12px; --dy: -22px; animation-delay: 160ms; }
.tp-cap-stage.phase-seal .tp-cap-sparkles i:nth-child(6) { --dx: 12px; --dy: -22px; animation-delay: 200ms; }
@keyframes capSpark {
  0% { opacity: 1; transform: translate(-50%, -50%) scale(1); }
  100% { opacity: 0; transform: translate(calc(-50% + var(--dx, 0px)), calc(-50% + var(--dy, 0px))) scale(.2); }
}
/* drop：落入胶囊库 */
.tp-cap-stage.phase-drop .tp-cap-shell { animation: capFall .6s cubic-bezier(.55,0,.85,.36) forwards; }
@keyframes capFall {
  0% { transform: translateY(0); opacity: 1; }
  100% { transform: translateY(64px) rotate(6deg); opacity: 0; }
}
.tp-cap-stage.phase-drop .tp-cap-stage-title,
.tp-cap-stage.phase-drop .tp-cap-stage-hint { opacity: 0; transition: opacity .3s; }

/* ===== 破封动画（开启仪式，卡片内） ===== */
.tp-cap-open-stage {
  position: relative; height: 130px; margin-bottom: 10px; border-radius: 10px; overflow: hidden;
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 6px;
  background: radial-gradient(ellipse at 50% 50%, rgba(245,158,11,.12), transparent 70%);
  border: 1px solid rgba(245,158,11,.16);
}
.tp-cap-shell.mini { width: 48px; height: 88px; margin: 6px 0 2px; }
.tp-cap-shell.mini .tp-cap-half { width: 48px; height: 44px; }
.tp-cap-shell.mini .tp-cap-top { border-radius: 24px 24px 4px 4px; }
.tp-cap-shell.mini .tp-cap-bottom { border-radius: 4px 4px 24px 24px; }
.tp-cap-shell.mini .tp-cap-seal-ring { width: 56px; height: 11px; }
.tp-cap-open-hint { font-size: 11px; color: color-mix(in srgb, #f59e0b 70%, var(--text-primary)); }
/* crack：颤抖 + 封印环闪断 + 裂纹光缝 */
.tp-cap-open-stage.ophase-crack .tp-cap-shell { animation: capShake .45s ease-in-out; }
@keyframes capShake {
  0%, 100% { transform: rotate(0); }
  20% { transform: rotate(-3deg); } 40% { transform: rotate(3deg); }
  60% { transform: rotate(-2deg); } 80% { transform: rotate(2deg); }
}
.tp-cap-open-stage.ophase-crack .tp-cap-seal-ring { animation: capRingCrack .45s ease-in forwards; }
@keyframes capRingCrack {
  0%, 60% { opacity: 1; transform: translate(-50%, -50%); }
  100% { opacity: 0; transform: translate(-50%, -50%) scaleX(.2); }
}
.tp-cap-crack {
  position: absolute; left: 50%; top: 50%; width: 2px; height: 88px; z-index: 5;
  transform: translate(-50%, -50%) scaleY(0);
  background: linear-gradient(180deg, transparent, #fde047, transparent);
  box-shadow: 0 0 10px #fde047;
}
.tp-cap-open-stage.ophase-crack .tp-cap-crack { animation: capCrackLine .45s ease-out .15s forwards; }
@keyframes capCrackLine { to { transform: translate(-50%, -50%) scaleY(1); } }
/* leak/open：封印环保持消失、裂纹保持可见（crack 动画移除后不回跳） */
.tp-cap-open-stage.ophase-leak .tp-cap-seal-ring,
.tp-cap-open-stage.ophase-open .tp-cap-seal-ring { opacity: 0; }
.tp-cap-open-stage.ophase-leak .tp-cap-crack { transform: translate(-50%, -50%) scaleY(1); }
.tp-cap-open-stage.ophase-open .tp-cap-crack { opacity: 0; transition: opacity .3s; }
/* leak：光缝涌出 */
.tp-cap-rays {
  position: absolute; left: 50%; top: 50%; width: 130px; height: 130px; z-index: 1;
  transform: translate(-50%, -50%); opacity: 0; filter: blur(2px);
  background: conic-gradient(from 0deg,
    rgba(253,224,71,0) 0deg, rgba(253,224,71,.55) 12deg, rgba(253,224,71,0) 26deg,
    rgba(253,224,71,0) 90deg, rgba(253,224,71,.45) 102deg, rgba(253,224,71,0) 116deg,
    rgba(253,224,71,0) 180deg, rgba(253,224,71,.5) 192deg, rgba(253,224,71,0) 206deg,
    rgba(253,224,71,0) 270deg, rgba(253,224,71,.45) 282deg, rgba(253,224,71,0) 296deg);
}
.tp-cap-open-stage.ophase-leak .tp-cap-rays { animation: capLeak .8s ease-out forwards; }
@keyframes capLeak {
  0% { opacity: 0; transform: translate(-50%, -50%) scale(.4); }
  35% { opacity: 1; }
  100% { opacity: .9; transform: translate(-50%, -50%) scale(1.35); }
}
.tp-cap-open-stage.ophase-leak .tp-cap-shell { animation: capGlow .8s ease-in-out; }
@keyframes capGlow { 0%, 100% { filter: none; } 50% { filter: brightness(1.5) drop-shadow(0 0 12px rgba(253,224,71,.8)); } }
/* open：壳身展开 */
.tp-cap-open-stage.ophase-open .tp-cap-top { transform: translateY(-38px); opacity: 0; }
.tp-cap-open-stage.ophase-open .tp-cap-bottom { transform: translateY(38px); opacity: 0; }
.tp-cap-open-stage.ophase-open .tp-cap-rays { animation: capLeakFade .4s ease-out forwards; }
@keyframes capLeakFade { to { opacity: 0; } }

/* 列表增删过渡 */
.cap-list-enter-active { transition: all .45s cubic-bezier(.34,1.56,.64,1); }
.cap-list-enter-from { opacity: 0; transform: translateY(-10px) scale(.95); }
.cap-list-leave-active { transition: all .25s ease; }
.cap-list-leave-to { opacity: 0; transform: scale(.9); }

@media (prefers-reduced-motion: reduce) {
  .tp-cap-stage .tp-cap-half, .tp-cap-stage .tp-cap-seal-ring,
  .tp-cap-open-stage .tp-cap-half, .tp-cap-open-stage .tp-cap-seal-ring,
  .tp-cap-shell, .tp-cap-entry.cap-just-opened { transition: none !important; animation: none !important; }
}

.panel-slide-enter-active { transition: all .3s ease; }
.panel-slide-leave-active { transition: all .25s ease; }
.panel-slide-enter-from .tool-panel { transform: translateX(100%); }
.panel-slide-enter-to .tool-panel { transform: translateX(0); }
.panel-slide-leave-from .tool-panel { transform: translateX(0); }
.panel-slide-leave-to .tool-panel { transform: translateX(100%); }
.panel-slide-enter-from { opacity: 0; }
.panel-slide-enter-to { opacity: 1; }
.panel-slide-leave-from { opacity: 1; }
.panel-slide-leave-to { opacity: 0; }
</style>
