import { ref, computed } from 'vue'

// 2026-10-30：从静态 PNG 换成带 alpha 的动画 WebP。
// 这 5 条是从 _devtools/xiaoji_anim/dist 的 MP4 用静态 alpha 遮罩转出来的，
// 页面驻扎/主页/桌宠共用同一套资产；加载失败时页面小基会回落静态图。
const avatarPath = '/xiaoji/'

export function useXiaojiAvatar() {
  const status = ref('idle')
  const agentLabel = ref('')

  const avatarUrl = computed(() => {
    const map = {
      idle: `${avatarPath}xiaoji_idle_loop.webp`,
      thinking: `${avatarPath}xiaoji_thinking_loop.webp`,
      speaking: `${avatarPath}xiaoji_speaking_loop.webp`,
      happy: `${avatarPath}xiaoji_happy_loop.webp`,
      sleeping: `${avatarPath}xiaoji_sleeping_loop.webp`
    }
    return map[status.value] || map.idle
  })

  // ===== 待机随机动作（2026-10-30）=====
  // 用户明确要「待机的随机动作」，不是一条循环播到底。
  // 只在真实状态是 idle 时生效；一旦进入 thinking/speaking 等真实状态，
  // 随机动作立即让位，不会和 Agent 的真实状态打架。
  const idleAction = ref('')
  // 点击/打招呼触发的「说话」不依赖 status —— 否则 loadMessages 之类的
  // setIdle 晚到会把说话动画直接抹掉。override 优先于 status。
  const speechOverride = ref('')
  const displayStatus = computed(() => {
    if (speechOverride.value) return speechOverride.value
    if (status.value !== 'idle') return status.value
    return idleAction.value || 'idle'
  })
  let speechTimer = null

  function speakFor(ms = 3000) {
    speechOverride.value = 'speaking'
    if (speechTimer) clearTimeout(speechTimer)
    speechTimer = setTimeout(() => {
      speechOverride.value = ''
      speechTimer = null
    }, Math.max(800, ms))
  }
  // 透明 WebP（角色的 alpha 边直接落在页面背景上；已去掉 3D 球）
  const WEBP_MAP = {
    idle: `${avatarPath}xiaoji_idle_loop.webp`,
    thinking: `${avatarPath}xiaoji_thinking_loop.webp`,
    speaking: `${avatarPath}xiaoji_speaking_loop.webp`,
    happy: `${avatarPath}xiaoji_happy_loop.webp`,
    sleeping: `${avatarPath}xiaoji_sleeping_loop.webp`
  }
  const avatarWebpUrl = computed(() => WEBP_MAP[displayStatus.value] || WEBP_MAP.idle)

  let idleTimer = null
  let actionTimer = null

  function scheduleIdleAction() {
    if (idleTimer) clearTimeout(idleTimer)
    const delay = 7000 + Math.random() * 7000
    idleTimer = setTimeout(() => {
      if (status.value !== 'idle') {
        scheduleIdleAction()
        return
      }
      const pool = ['happy', 'thinking', 'sleeping']
      const pick = pool[Math.floor(Math.random() * pool.length)]
      idleAction.value = pick
      const dur = pick === 'happy' ? 2000 : (pick === 'thinking' ? 3000 : 3500)
      actionTimer = setTimeout(() => {
        idleAction.value = ''
        scheduleIdleAction()
      }, dur)
    }, delay)
  }

  function startIdleActions() {
    if (idleTimer || actionTimer) return
    scheduleIdleAction()
  }

  function stopIdleActions() {
    if (idleTimer) clearTimeout(idleTimer)
    if (actionTimer) clearTimeout(actionTimer)
    idleTimer = null
    actionTimer = null
    idleAction.value = ''
  }

  function stopSpeech() {
    if (speechTimer) clearTimeout(speechTimer)
    speechTimer = null
    speechOverride.value = ''
  }

  const statusText = computed(() => {
    // ⚠️ 用 displayStatus，不是 status：球里的随机待机动作（开心/思考/打盹）
    //    也要让下面的状态签跟着变，不能一直挂「在线」。
    const thinkingLabel = (status.value === 'thinking' && agentLabel.value)
      ? agentLabel.value
      : '思考中…'
    const map = {
      idle: '待机',
      thinking: thinkingLabel,
      speaking: '说话中…',
      happy: '开心',
      sleeping: '打盹'
    }
    return map[displayStatus.value] || map.idle
  })

  const statusTagType = computed(() => ({
    idle: 'info',
    thinking: 'warning',
    speaking: 'success',
    happy: 'success',
    sleeping: 'info'
  }[displayStatus.value] || 'info'))

  // 真实阶段（2026-09-10）：取代原来那套写死的「理解/评估/生成/规划 Agent」假进度——
  // 它由 setInterval 每 1.5s 推进一格，与后端实际在干什么毫无关系，纯表演。
  // 现在阶段文案由调用方按实际动作设置（如「正在出第 2/3 道题…」），
  // 进度百分比已知才显示，未知就只显示文案。
  const stage = ref('')
  const stagePercent = ref(null)

  function setStage(text, percent = null) {
    stage.value = text || ''
    stagePercent.value = percent
    if (text) {
      status.value = 'thinking'
      agentLabel.value = ''
    }
  }

  const isProcessing = computed(() => {
    return status.value === 'thinking' || status.value === 'speaking'
  })

  function setStatus(newStatus) {
    status.value = newStatus
  }

  function setIdle() {
    status.value = 'idle'
    agentLabel.value = ''
    stage.value = ''
    stagePercent.value = null
  }

  function setThinking(label = '思考中...') {
    status.value = 'thinking'
    agentLabel.value = label
  }

  function setSpeaking() {
    status.value = 'speaking'
    agentLabel.value = ''
    stage.value = ''
    stagePercent.value = null
  }

  function setHappy() {
    status.value = 'happy'
    agentLabel.value = ''
    stage.value = ''
    stagePercent.value = null
    setTimeout(() => {
      if (status.value === 'happy') {
        status.value = 'idle'
      }
    }, 2000)
  }

  function setSleeping() {
    status.value = 'sleeping'
    agentLabel.value = ''
    stage.value = ''
    stagePercent.value = null
  }

  return {
    status,
    avatarUrl,
    displayStatus,
    avatarWebpUrl,
    statusText,
    statusTagType,
    agentLabel,
    stage,
    stagePercent,
    isProcessing,
    startIdleActions,
    stopIdleActions,
    speakFor,
    stopSpeech,
    setStatus,
    setIdle,
    setThinking,
    setStage,
    setSpeaking,
    setHappy,
    setSleeping
  }
}