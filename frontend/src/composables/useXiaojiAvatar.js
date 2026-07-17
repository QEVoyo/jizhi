import { ref, computed } from 'vue'

const avatarPath = '/images/xiaoji/'

export function useXiaojiAvatar() {
  const status = ref('idle')
  const agentLabel = ref('')
  const agentStep = ref(0)

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

  // 智能体状态列表（用于显示进度）
  const agentSteps = [
    { label: '理解 Agent', desc: '分析题目知识点', status: 'processing' },
    { label: '评估 Agent', desc: '评估难度与水平', status: 'processing' },
    { label: '生成 Agent', desc: '生成解析思路', status: 'processing' },
    { label: '规划 Agent', desc: '制定学习规划', status: 'processing' }
  ]

  const currentAgent = computed(() => {
    if (agentStep.value >= 0 && agentStep.value < agentSteps.length) {
      return agentSteps[agentStep.value]
    }
    return null
  })

  const isProcessing = computed(() => {
    return status.value === 'thinking' || status.value === 'speaking'
  })

  function setStatus(newStatus) {
    status.value = newStatus
  }

  function setIdle() {
    status.value = 'idle'
    agentLabel.value = ''
    agentStep.value = 0
  }

  function setThinking(label = '思考中...') {
    status.value = 'thinking'
    agentLabel.value = label
  }

  function setSpeaking() {
    status.value = 'speaking'
    agentLabel.value = ''
  }

  function setHappy() {
    status.value = 'happy'
    agentLabel.value = ''
    agentStep.value = 0
    setTimeout(() => {
      if (status.value === 'happy') {
        status.value = 'idle'
      }
    }, 2000)
  }

  function setSleeping() {
    status.value = 'sleeping'
    agentLabel.value = ''
    agentStep.value = 0
  }

  // 推进到下一个智能体
  function nextAgent() {
    if (agentStep.value < agentSteps.length - 1) {
      agentStep.value++
      const step = agentSteps[agentStep.value]
      status.value = 'thinking'
      agentLabel.value = step.label
      return step
    } else {
      // 所有智能体完成
      return null
    }
  }

  // 开始智能体流程（从头开始）
  function startAgentFlow() {
    agentStep.value = 0
    status.value = 'thinking'
    agentLabel.value = agentSteps[0].label
    return agentSteps[0]
  }

  // 重置智能体流程
  function resetAgentFlow() {
    agentStep.value = 0
    agentLabel.value = ''
    status.value = 'idle'
  }

  // 获取当前智能体进度（用于显示）
  function getAgentProgress() {
    return {
      current: agentStep.value + 1,
      total: agentSteps.length,
      label: agentSteps[agentStep.value]?.label || '',
      desc: agentSteps[agentStep.value]?.desc || ''
    }
  }

  return {
    status,
    avatarUrl,
    statusText,
    agentLabel,
    agentStep,
    agentSteps,
    currentAgent,
    isProcessing,
    setStatus,
    setIdle,
    setThinking,
    setSpeaking,
    setHappy,
    setSleeping,
    nextAgent,
    startAgentFlow,
    resetAgentFlow,
    getAgentProgress
  }
}