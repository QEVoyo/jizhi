<template>
  <div class="chat-area">
    <div class="chat-header">
      <h1>
          <img src="/logo.png" alt="基智" class="chat-header-logo" />
          基智 · 多智能体学习助手
       </h1>
      <p>多智能体协作 · 个性化学习 · 自适应难度</p>
    </div>

    <div class="chat-messages-wrapper">
      <div class="chat-messages" ref="messagesRef">
        <div
          v-for="(msg, index) in messages"
          :key="index"
          class="message"
          :class="msg.role"
        >
          <div class="message-content">{{ msg.content }}</div>
        </div>

        <!-- ===== 调用 Agent 状态（显示1秒后消失） ===== -->
        <div v-if="callingAgent" class="message assistant calling-message">
          <div class="message-content">
            <div class="calling-indicator">
              <span class="calling-icon">{{ callingIcon }}</span>
              <span class="calling-text">{{ callingText }}</span>
              <span class="calling-dots">
                <span></span><span></span><span></span>
              </span>
            </div>
          </div>
        </div>

        <!-- ===== 加载中（备用） ===== -->
        <div v-else-if="isLoading" class="message assistant">
          <div class="message-content loading-dots">
            <span></span><span></span><span></span>
          </div>
        </div>
      </div>
    </div>

    <!-- ===== 图片预览 ===== -->
    <div v-if="uploadedImages.length" class="image-preview-bar">
      <div
        v-for="(img, idx) in uploadedImages"
        :key="idx"
        class="image-thumb"
      >
        <img :src="img.url" alt="上传图片" />
        <button class="thumb-remove" @click="removeImage(idx)">
          <i class="fas fa-times"></i>
        </button>
      </div>
    </div>

    <!-- ===== 输入框 ===== -->
    <div class="chat-input-wrapper">
      <el-input
        v-model="inputText"
        placeholder="输入你的问题..."
        size="large"
        @keyup.enter="sendMessage"
      >
        <template #prefix>
          <el-upload
            :show-file-list="false"
            :before-upload="handleImageUpload"
            accept="image/*"
            class="image-upload-inline"
          >
            <el-icon class="upload-icon"><Picture /></el-icon>
          </el-upload>
        </template>
        <template #append>
          <el-button :loading="isLoading" @click="sendMessage">
            发送
          </el-button>
        </template>
      </el-input>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useSessionStore } from '@/stores/session'
import { sendChatMessage, saveLog } from '@/api/chat'
import { recordAction } from '@/api/career'
import { ElMessage } from 'element-plus'
import { Picture } from '@element-plus/icons-vue'

const authStore = useAuthStore()
const sessionStore = useSessionStore()

const inputText = ref('')
const isLoading = ref(false)
const callingAgent = ref(false)
const callingIcon = ref('')
const callingText = ref('')
const messagesRef = ref(null)
const uploadedImages = ref([])

const messages = computed(() => {
  return sessionStore.getMessages(sessionStore.currentSessionId) || []
})

function scrollToBottom() {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

// ===== 降级关键词匹配（仅当 AI 意图分类失败时使用） =====
function fallbackDetectIntent(text) {
  const planKeywords = ['规划', '计划', '安排', '学习路径', '该怎么学', '先学什么', '学习路线', '给我规划', '怎么学习', '学习计划', '路径规划', '学习方案', '怎么开始']
  const generateKeywords = ['生成', '出题', '给我一道题', '练习题', '题目', '给我出', '出一道', '生成题目', '高数题', '数学题', '物理题', '英语题', '编程题', '算法题', '数据结构题', '给我题', '来道题', '来一题', '练练手', '做题', '练习', '试卷', '考题']
  const evaluateKeywords = ['评估', '评价', '批改', '看看我写', '帮我改', '检查一下', '帮我评估', '觉得我', '怎么样', '水平', '怎么样的人', '什么水平', '帮我看看']

  if (planKeywords.some(k => text.includes(k))) return 'plan'
  if (generateKeywords.some(k => text.includes(k))) return 'generate'
  if (evaluateKeywords.some(k => text.includes(k))) return 'evaluate'
  return 'chat'
}

// ===== 调用后端 AI 意图分类 =====
async function detectIntent(text) {
  try {
    const response = await fetch(`${import.meta.env.VITE_BACKEND_URL || 'https://api.jizhi-learn.com'}/chat/detect-intent`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authStore.token}`
      },
      body: JSON.stringify({ text: text.slice(0, 200) })
    })
    const data = await response.json()
    if (data.intent && ['plan', 'generate', 'evaluate', 'chat'].includes(data.intent)) {
      return data.intent
    }
    return fallbackDetectIntent(text)
  } catch {
    return fallbackDetectIntent(text)
  }
}

function getAgentInfo(intent) {
  const map = {
    'plan': { icon: '📋', label: '调用规划 Agent' },
    'generate': { icon: '📖', label: '调用生成 Agent' },
    'evaluate': { icon: '🔍', label: '调用评估 Agent' },
    'chat': { icon: '💬', label: '调用 Chat Agent' }
  }
  return map[intent] || map['chat']
}

function getAgentDone(intent) {
  const map = {
    'plan': '✅ 规划 Agent 已完成',
    'generate': '✅ 生成 Agent 已完成',
    'evaluate': '✅ 评估 Agent 已完成',
    'chat': '✅ Chat Agent 已完成'
  }
  return map[intent] || map['chat']
}

function handleImageUpload(file) {
  const reader = new FileReader()
  reader.onload = (e) => {
    uploadedImages.value.push({
      url: e.target.result,
      file: file,
      name: file.name
    })
  }
  reader.readAsDataURL(file)
  return false
}

function removeImage(index) {
  uploadedImages.value.splice(index, 1)
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text && !uploadedImages.value.length) return

  let messageContent = text
  if (uploadedImages.value.length) {
    messageContent = text ? `${text}\n\n📷 已上传 ${uploadedImages.value.length} 张图片` : `📷 已上传 ${uploadedImages.value.length} 张图片`
  }

  // ===== AI 意图分类 =====
  const intent = await detectIntent(text || '图片')
  const agentInfo = getAgentInfo(intent)
  const doneLabel = getAgentDone(intent)

  // 添加用户消息
  sessionStore.addMessage(sessionStore.currentSessionId, 'user', messageContent)
  inputText.value = ''
  const images = [...uploadedImages.value]
  uploadedImages.value = []
  scrollToBottom()

  // ===== 显示调用 Agent 状态 =====
  isLoading.value = true
  callingAgent.value = true
  callingIcon.value = agentInfo.icon
  callingText.value = agentInfo.label
  scrollToBottom()

  // 等待1秒后开始流式输出
  await new Promise(resolve => setTimeout(resolve, 1000))

  // 隐藏调用状态，准备流式输出
  callingAgent.value = false

  try {
    const history = sessionStore
      .getMessages(sessionStore.currentSessionId)
      .filter(m => m.role !== 'system')
      .slice(-20)
      .map(m => ({ role: m.role, content: m.content }))

    let finalMessages = history
    if (images.length) {
      const lastUserMsg = finalMessages[finalMessages.length - 1]
      if (lastUserMsg && lastUserMsg.role === 'user') {
        const imageData = images.map(img => img.url).join(',')
        lastUserMsg.content = `${lastUserMsg.content}\n\n[图片数据: ${imageData}]`
      }
    }

    const response = await sendChatMessage(finalMessages, authStore.user.id, 0.7, intent)

    // ===== 流式读取 =====
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let fullContent = ''

    // 创建助手消息占位
    sessionStore.addMessage(sessionStore.currentSessionId, 'assistant', '')
    const msgs = sessionStore.getMessages(sessionStore.currentSessionId)
    const lastIndex = msgs.length - 1

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      const chunk = decoder.decode(value, { stream: true })
      fullContent += chunk
      msgs[lastIndex].content = fullContent
      sessionStore.saveSessions()
      scrollToBottom()
    }

    // ===== 内容输出完成后，追加"已完成"标记 =====
    msgs[lastIndex].content = fullContent + `\n\n${doneLabel}`
    sessionStore.saveSessions()
    scrollToBottom()

    // ===== 后处理 =====
    const allMsgs = sessionStore.getMessages(sessionStore.currentSessionId)
    if (allMsgs.length === 2) {
      try {
        const titleRes = await fetch(`${import.meta.env.VITE_BACKEND_URL || 'https://api.jizhi-learn.com'}/chat/title`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authStore.token}`
          },
          body: JSON.stringify({
            user_id: authStore.user.id,
            content: text || '图片分析',
            response: fullContent
          })
        })
        const titleData = await titleRes.json()
        if (titleData.title) {
          sessionStore.updateSessionTitle(sessionStore.currentSessionId, titleData.title)
        }
      } catch {
        const title = (text || '图片分析').slice(0, 20) + ((text || '图片分析').length > 20 ? '...' : '')
        sessionStore.updateSessionTitle(sessionStore.currentSessionId, title)
      }
    }

    const actionMap = {
      'plan': 'use_plan_agent',
      'generate': 'use_generate_agent',
      'evaluate': 'use_evaluate_agent',
      'chat': 'chat'
    }
    await recordAction(authStore.user.id, actionMap[intent] || 'chat')

    // 【仅生成 Agent】提取摘要写入学习日志
    if (intent === 'generate' && fullContent.length > 20) {
    console.log('=== 进入生成日志写入逻辑 ===')
    console.log('=== fullContent 长度:', fullContent.length)
      try {
        const summaryRes = await fetch(`${import.meta.env.VITE_BACKEND_URL || 'https://api.jizhi-learn.com'}/chat/summary`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authStore.token}`
          },
          body: JSON.stringify({
            content: fullContent,
            user_id: authStore.user.id
          })
        })
        const summaryData = await summaryRes.json()
        console.log('=== 摘要结果:', summaryData)
        if (summaryData.summary) {
          await saveLog(authStore.user.id, summaryData.summary)
        }
      } catch (error) {
        console.error('提取摘要或写入日志失败:', error)
        const fallbackSummary = fullContent.replace(/\n/g, ' ').slice(0, 50) + (fullContent.length > 50 ? '...' : '')
        await saveLog(authStore.user.id, fallbackSummary)
      }
    }

  } catch (error) {
    console.error('发送失败:', error)
    callingAgent.value = false
    isLoading.value = false
    ElMessage.error('发送失败: ' + (error.message || '网络错误'))
    const msgs = sessionStore.getMessages(sessionStore.currentSessionId)
    if (msgs.length > 0 && msgs[msgs.length - 1].content === '') {
      msgs.pop()
      sessionStore.saveSessions()
    }
  } finally {
    isLoading.value = false
    callingAgent.value = false
    scrollToBottom()
  }
}

onMounted(() => {
  sessionStore.loadSessions()
  if (!sessionStore.sessions.length) {
    sessionStore.createSession('新对话')
  }
  if (!sessionStore.currentSessionId && sessionStore.sessions.length) {
    sessionStore.switchSession(sessionStore.sessions[0].id)
  }
  scrollToBottom()
})
</script>

<style scoped>
.chat-area {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding-bottom: 12px;
  background: transparent !important;
}

.chat-header-logo {
  width: 28px;
  height: 28px;
  object-fit: contain;
  vertical-align: middle;
  margin-right: 8px;
}
.chat-header {
  margin-bottom: 16px;
  flex-shrink: 0;
}
.chat-header h1 {
  font-size: 24px;
  color: var(--text-primary);
}
.chat-header p {
  color: var(--text-secondary);
  font-size: 14px;
  opacity: 0.6;
}

.chat-messages-wrapper {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  position: relative;
}

.chat-messages {
  height: 100%;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 12px 4px 16px;
}

.message {
  max-width: 80%;
  padding: 12px 18px;
  border-radius: 14px;
  font-size: 15px;
  line-height: 1.6;
  animation: fadeIn 0.3s ease;
  flex-shrink: 0;
}

.message.user {
  align-self: flex-end;
  background: rgba(128, 128, 128, 0.08);
  color: var(--text-primary);
}

.message.assistant {
  align-self: flex-start;
  background: rgba(128, 128, 128, 0.04);
  color: var(--text-primary);
}

.message-content {
  white-space: pre-wrap;
  word-break: break-word;
}

/* ===== 调用 Agent 状态 ===== */
.calling-message {
  background: rgba(128, 128, 128, 0.03) !important;
  border: 1px solid var(--border-color);
}
.calling-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
}
.calling-icon {
  font-size: 18px;
}
.calling-text {
  font-size: 14px;
  color: var(--text-secondary);
}
.calling-dots {
  display: flex;
  gap: 3px;
  align-items: center;
}
.calling-dots span {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--text-muted);
  animation: thinkingBounce 1.4s infinite both;
}
.calling-dots span:nth-child(1) { animation-delay: -0.32s; }
.calling-dots span:nth-child(2) { animation-delay: -0.16s; }
.calling-dots span:nth-child(3) { animation-delay: 0s; }

@keyframes thinkingBounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

.loading-dots {
  display: flex;
  gap: 4px;
  padding: 4px 0;
}
.loading-dots span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--text-muted);
  animation: bounce 1.4s infinite both;
}
.loading-dots span:nth-child(1) { animation-delay: -0.32s; }
.loading-dots span:nth-child(2) { animation-delay: -0.16s; }
.loading-dots span:nth-child(3) { animation-delay: 0s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ===== 图片预览 ===== */
.image-preview-bar {
  display: flex;
  gap: 10px;
  padding: 10px 14px;
  margin-bottom: 8px;
  flex-wrap: wrap;
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}
[data-theme="dark"] .image-preview-bar {
  background: rgba(0, 0, 0, 0.25);
  border-color: rgba(255, 255, 255, 0.04);
}
.image-thumb {
  position: relative;
  width: 72px;
  height: 72px;
  border-radius: 10px;
  overflow: hidden;
  border: 2px solid var(--border-color);
  flex-shrink: 0;
  background: rgba(128, 128, 128, 0.04);
}
.image-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.image-thumb .thumb-remove {
  position: absolute;
  top: 4px;
  right: 4px;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  border: none;
  color: #fff;
  border-radius: 50%;
  width: 20px;
  height: 20px;
  cursor: pointer;
  font-size: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}
.image-thumb .thumb-remove:hover {
  background: rgba(239, 68, 68, 0.85);
}

/* ===== 输入框 ===== */
.chat-input-wrapper {
  flex-shrink: 0;
  padding: 4px 0 18px 0;
  margin: 0;
  background: transparent !important;
}
.image-upload-inline {
  display: inline-flex;
  align-items: center;
  cursor: pointer;
  margin-right: 4px;
}
.upload-icon {
  font-size: 18px;
  color: var(--text-muted);
  transition: color 0.3s ease;
}
.upload-icon:hover {
  color: var(--text-primary);
}
.chat-input-wrapper :deep(.el-input__wrapper) {
  border-radius: 12px;
  background: rgba(128, 128, 128, 0.04);
  border: 1px solid var(--border-color);
  padding: 2px 8px;
  min-height: 40px;
}
.chat-input-wrapper :deep(.el-input__wrapper:hover) {
  border-color: rgba(128, 128, 128, 0.15);
}
.chat-input-wrapper :deep(.el-input__prefix) {
  margin-right: 4px;
}
.chat-input-wrapper :deep(.el-input-group__append) {
  border-radius: 12px;
  background: rgba(128, 128, 128, 0.04);
  border: 1px solid var(--border-color);
  border-left: none;
  padding: 0 16px;
}

[data-theme="dark"] .chat-input-wrapper :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.05) !important;
  border-color: rgba(255, 255, 255, 0.08) !important;
}
[data-theme="dark"] .chat-input-wrapper :deep(.el-input__wrapper:hover) {
  border-color: rgba(255, 255, 255, 0.14) !important;
}
[data-theme="dark"] .chat-input-wrapper :deep(.el-input-group__append) {
  background: rgba(255, 255, 255, 0.05) !important;
  border-color: rgba(255, 255, 255, 0.08) !important;
}
[data-theme="dark"] .message.user {
  background: rgba(255, 255, 255, 0.08) !important;
  color: var(--text-primary) !important;
}
[data-theme="dark"] .message.assistant {
  background: rgba(255, 255, 255, 0.04) !important;
  color: var(--text-primary) !important;
}
[data-theme="dark"] .calling-message {
  background: rgba(255, 255, 255, 0.02) !important;
}

.chat-messages::-webkit-scrollbar {
  width: 4px;
}
.chat-messages::-webkit-scrollbar-track {
  background: transparent;
}
.chat-messages::-webkit-scrollbar-thumb {
  background: rgba(128, 128, 128, 0.2);
  border-radius: 2px;
}
.chat-messages::-webkit-scrollbar-thumb:hover {
  background: rgba(128, 128, 128, 0.3);
}
</style>