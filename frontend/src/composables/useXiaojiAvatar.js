import { ref, computed } from 'vue'

const avatarPath = '/images/xiaoji/'

export function useXiaojiAvatar() {
  const status = ref('idle')
  const agentLabel = ref('')

  const avatarUrl = computed(() => {
    const map = {
      idle: `${avatarPath}xiaoji_idle.png`,
      thinking: `${avatarPath}xiaoji_thinking.png`,
      speaking: `${avatarPath}xiaoji_speaking.png`,
      happy: `${avatarPath}xiaoji_happy.png`,
      sleeping: `${avatarPath}xiaoji_sleeping.png`
    }
    return map[status.value] || map.idle
  })

  const statusText = computed(() => {
    const map = {
      idle: '在线',
      thinking: agentLabel.value || '思考中...',
      speaking: '输出中...',
      happy: '已完成',
      sleeping: '离线'
    }
    return map[status.value] || map.idle
  })

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
    statusText,
    agentLabel,
    stage,
    stagePercent,
    isProcessing,
    setStatus,
    setIdle,
    setThinking,
    setStage,
    setSpeaking,
    setHappy,
    setSleeping
  }
}