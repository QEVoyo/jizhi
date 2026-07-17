<template>
  <div class="xiaoji-call-page">
    <!-- ===== 顶部导航 ===== -->
    <div class="call-nav">
      <el-button text class="nav-back" @click="goBack">
        <i class="fas fa-arrow-left"></i>
      </el-button>
      <div class="nav-center">
        <div class="nav-avatar-wrapper">
          <img :src="avatarUrl" alt="小基" class="nav-avatar" />
        </div>
        <div>
          <div class="nav-name">小基</div>
          <div class="nav-status">{{ statusText }}</div>
        </div>
      </div>
      <div class="nav-actions">
        <el-button text class="nav-action" @click="clearHistory" title="清空记录">
          <i class="fas fa-trash-alt"></i>
        </el-button>
        <el-button text class="nav-action" @click="goSettings">
          <i class="fas fa-cog"></i>
        </el-button>
      </div>
    </div>

    <!-- ===== 小基形象 ===== -->
    <div class="xiaoji-area">
      <div class="xiaoji-glow-ring"></div>
      <div class="xiaoji-glow-ring-2"></div>
      <div
        class="xiaoji-click-area"
        @click="onAvatarClick"
        @dblclick="onAvatarDoubleClick"
        @mouseenter="onAvatarHover(true)"
        @mouseleave="onAvatarHover(false)"
      >
        <div class="xiaoji-shadow"></div>
        <img :src="avatarUrl" alt="小基" class="xiaoji-image" :class="{ hover: isHover }" />
        <div class="xiaoji-status-area">
          <el-tag :type="statusTagType" size="default" effect="plain" class="status-tag">
            {{ statusText }}
          </el-tag>
          <div v-if="isProcessing && currentAgent" class="agent-progress">
            <el-progress
              :percentage="agentProgressPercent"
              :stroke-width="3"
              :show-text="false"
              class="agent-progress-bar"
            />
            <div class="agent-info">
              <el-tag size="small" type="warning" class="agent-tag">
                {{ currentAgent.label }}
              </el-tag>
              <span class="agent-desc">{{ currentAgent.desc }}</span>
            </div>
          </div>
        </div>
      </div>
      <div
        v-if="showDialog"
        class="xiaoji-dialog"
        :style="dialogStyle"
        :class="{ pop: dialogPop }"
      >
        {{ dialogText }}
        <div class="dialog-tail"></div>
      </div>
    </div>

    <!-- ===== 聊天区域 ===== -->
    <div class="chat-area-wrapper">
      <div class="chat-cylinder-wrapper">
        <div class="chat-cylinder-glow"></div>
        <div class="chat-roll" ref="chatRollRef" @scroll="onScroll">
          <div v-if="loading" class="roll-loading">
            <i class="fas fa-spinner fa-spin"></i>
            <span>加载中...</span>
          </div>
          <div v-else-if="!messages.length" class="roll-empty">
            <span>💬 开始和小基聊天吧</span>
          </div>
          <div v-else class="roll-messages">
            <div
              v-for="(msg, index) in messages"
              :key="index"
              class="roll-item"
              :class="{
                user: msg.role === 'user',
                assistant: msg.role === 'assistant',
                isQuestion: msg.is_question,
                isSet: msg.is_set,
                isEvaluation: msg.is_evaluation
              }"
            >
              <div class="roll-avatar">
                <img
                  v-if="msg.role === 'user'"
                  :src="authStore.user?.avatar_url || '/default-avatar.png'"
                  class="user-avatar-img"
                />
                <img v-else :src="avatarUrl" class="xiaoji-avatar-img" />
              </div>
              <div class="roll-content">
                <!-- ===== 图片显示 ===== -->
                <div v-if="msg.image_url" class="message-image" @click="previewImage(msg.image_url)">
                  <img :src="msg.image_url" alt="图片" />
                </div>

                <!-- 题目卡片 -->
                <div v-if="msg.is_question" class="message-card question-card" @click="previewQuestion(msg.questionData)">
                  <div class="card-header">
                    <span class="card-icon">📝</span>
                    <span class="card-title">{{ msg.questionData?.title || '题目' }}</span>
                    <span class="card-badge">{{ getTypeName(msg.questionData?.question_type) }}</span>
                    <span class="card-difficulty-badge">难度 {{ msg.questionData?.difficulty_score || 5 }}</span>
                  </div>
                  <div class="card-body">
                    <div class="card-question">{{ msg.questionData?.question_content || msg.questionData?.title }}</div>
                    <div v-if="msg.questionData?.question_type === 'choice' && msg.questionData?.options" class="card-options">
                      <div v-for="(val, key) in msg.questionData.options" :key="key" class="card-option">
                        {{ key }}. {{ val }}
                      </div>
                    </div>
                  </div>
                  <div class="card-footer">
                    <span class="card-hint">点击查看详情</span>
                  </div>
                </div>

                <!-- 题集卡片 -->
                <div v-else-if="msg.is_set" class="message-card set-card" @click="previewSet(msg.setData)">
                  <div class="card-header">
                    <span class="card-icon">📚</span>
                    <span class="card-title">{{ msg.setData?.name || '题集' }}</span>
                    <span class="card-badge">{{ msg.setData?.question_ids?.length || 0 }} 道题</span>
                  </div>
                  <div class="card-body">
                    <span class="card-preview">{{ msg.setData?.description || '点击查看题集详情' }}</span>
                  </div>
                  <div class="card-footer">
                    <span class="card-hint">点击查看题集详情</span>
                  </div>
                </div>

                <!-- 评价结果 -->
                <div v-else-if="msg.is_evaluation" class="evaluation-content">
                  <div class="eval-badge">📊 小基评价</div>
                  <div class="eval-text" v-html="formatEvalText(msg.content)"></div>
                </div>

                <!-- 普通文本 -->
                <template v-else>
                  {{ msg.content }}
                </template>
              </div>
              <span class="roll-time">{{ formatTime(msg.created_at) }}</span>
            </div>

            <!-- 正在输入 -->
            <div v-if="sending" class="roll-item assistant">
              <div class="roll-avatar">
                <img :src="avatarUrl" class="xiaoji-avatar-img" />
              </div>
              <div class="roll-content">
                <span class="typing-dots-inline">
                  <span></span><span></span><span></span>
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ===== 输入框 ===== -->
    <div class="call-input-area">
      <div class="input-tools">
        <button class="tool-btn" @click="triggerImageUpload" title="上传图片">
          <i class="fas fa-image"></i>
        </button>
        <button class="tool-btn" @click="openSendQuestion" title="发送题目">
          <i class="fas fa-paper-plane"></i>
        </button>
        <button class="tool-btn disabled" @click="showDeveloping" title="语音输入开发中">
          <i class="fas fa-microphone"></i>
        </button>
        <button class="tool-btn" @click="toggleVoice" :class="{ active: voiceEnabled }" title="语音播报">
          <i :class="voiceEnabled ? 'fas fa-volume-up' : 'fas fa-volume-mute'"></i>
        </button>
      </div>
      <input ref="fileInputRef" type="file" accept="image/*" style="display:none" @change="handleImageSelect" />

      <div class="input-row">
        <el-input
          v-model="inputText"
          :placeholder="uploadedImage ? '输入图片描述...' : '输入消息...'"
          size="large"
          @keyup.enter="sendMessage()"
          class="chat-input"
        >
          <template #append>
            <el-button :loading="sending" @click="sendMessage">
              <i class="fas fa-paper-plane"></i>
            </el-button>
          </template>
        </el-input>
      </div>

      <div v-if="uploadedImage" class="image-preview">
        <img :src="uploadedImage" alt="待发送图片" />
        <button class="remove-image" @click="removeImage">
          <i class="fas fa-times"></i>
        </button>
      </div>
    </div>

    <!-- ===== 发送题目弹窗 ===== -->
    <el-dialog
      v-model="showQuestionDialog"
      title="📤 发送给小基"
      width="560px"
      destroy-on-close
      class="custom-glass-dialog"
    >
      <div class="question-dialog">
        <el-tabs v-model="questionTab" class="custom-glass-tabs">
          <el-tab-pane label="生成历史" name="history">
            <div v-if="historyQuestions.length === 0" class="empty-tip">
              暂无生成历史
            </div>
            <div
              v-for="q in historyQuestions"
              :key="q.id"
              class="question-item"
              @click="sendSingleQuestion(q)"
            >
              <span class="q-title">{{ q.title || q.question_content || '未命名题目' }}</span>
              <span class="q-type">{{ getTypeName(q.question_type) }}</span>
              <el-button size="small" type="primary">发送</el-button>
            </div>
          </el-tab-pane>

          <el-tab-pane label="题集" name="sets">
            <div v-if="questionSets.length === 0" class="empty-tip">
              暂无题集
            </div>
            <div
              v-for="s in questionSets"
              :key="s.id"
              class="set-item-wrapper"
            >
              <div class="set-item" @click="toggleSetExpand(s.id)">
                <div class="set-info">
                  <span class="set-name">{{ s.name }}</span>
                  <span class="set-count">{{ s.question_ids?.length || 0 }} 道题</span>
                  <el-icon :class="{ expanded: expandedSetId === s.id }" class="set-expand-icon">
                    <i class="fas fa-chevron-down"></i>
                  </el-icon>
                </div>
              </div>
              <div v-if="expandedSetId === s.id" class="set-questions-list">
                <div v-if="setQuestionsMap[s.id] === null" class="loading-tip">
                  <i class="fas fa-spinner fa-spin"></i> 加载中...
                </div>
                <div v-else-if="setQuestionsMap[s.id]?.length === 0" class="empty-tip">
                  该题集暂无题目
                </div>
                <div
                  v-for="q in setQuestionsMap[s.id] || []"
                  :key="q.id"
                  class="set-question-item"
                  @click="sendSingleQuestion(q)"
                >
                  <div class="sq-info">
                    <span class="sq-title">{{ q.title || q.question_content || '未命名题目' }}</span>
                    <span v-if="q.question_content && q.question_content !== q.title" class="sq-preview">
                      {{ q.question_content.slice(0, 40) }}{{ q.question_content.length > 40 ? '...' : '' }}
                    </span>
                  </div>
                  <span class="sq-type">{{ getTypeName(q.question_type) }}</span>
                  <el-button size="small" type="primary">发送</el-button>
                </div>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-dialog>

    <!-- ===== 预览弹窗 ===== -->
    <el-dialog
      v-model="showPreviewDialog"
      :title="previewTitle"
      width="600px"
      destroy-on-close
      class="custom-glass-dialog"
    >
      <div class="preview-content">
        <div v-if="previewType === 'question'">
          <div class="preview-question">
            <h4>{{ previewData?.title }}</h4>
            <p><strong>题型：</strong>{{ getTypeName(previewData?.question_type) }}</p>
            <p><strong>难度：</strong>{{ previewData?.difficulty_score || 5 }}</p>
            <p><strong>内容：</strong>{{ previewData?.question_content || previewData?.title }}</p>

            <div v-if="previewData?.question_type === 'choice' && previewData?.options">
              <p><strong>选项：</strong></p>
              <div v-for="(val, key) in previewData.options" :key="key" class="option-item">
                {{ key }}. {{ val }}
              </div>
            </div>

            <div v-if="previewData?.question_type === 'coding' && previewData?.starter_code">
              <p><strong>代码模板：</strong></p>
              <pre class="code-block">{{ previewData.starter_code }}</pre>
            </div>
          </div>
        </div>
        <div v-else-if="previewType === 'set'">
          <div class="preview-set">
            <p><strong>题集名称：</strong>{{ previewData?.name }}</p>
            <p><strong>描述：</strong>{{ previewData?.description || '无描述' }}</p>
            <p><strong>题目数量：</strong>{{ previewData?.question_ids?.length || 0 }}</p>
            <div v-if="previewQuestions.length > 0" class="set-questions-list">
              <p><strong>包含题目：</strong></p>
              <div v-for="(q, idx) in previewQuestions" :key="idx" class="set-question-item">
                <span class="sq-index">{{ idx + 1 }}.</span>
                <span class="sq-title">{{ q.title || q.question_content || '未命名题目' }}</span>
                <span class="sq-type">{{ getTypeName(q.question_type) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- ===== 图片预览 ===== -->
    <el-dialog v-model="imagePreviewVisible" width="80%" class="image-preview-dialog" destroy-on-close>
      <img :src="previewImageUrl" alt="预览" class="preview-image" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getXiaojiMessages,
  sendXiaojiMessage,
  xiaojiVision,
  clearXiaojiMessages,
  evaluateQuestion,
  evaluateSet
} from '@/api/xiaoji'
import { getGenerationHistory, getQuestionSets, getQuestionDetail } from '@/api/questions'
import { useXiaojiAvatar } from '@/composables/useXiaojiAvatar'

const router = useRouter()
const authStore = useAuthStore()
const {
  avatarUrl,
  statusText,
  statusTagType,
  currentAgent,
  isProcessing,
  agentProgressPercent,
  setThinking,
  setSpeaking,
  setHappy,
  setIdle,
  setSleeping,
  startAgentFlow,
  nextAgent,
  resetAgentFlow,
  getAgentProgress
} = useXiaojiAvatar()

// ===== 状态 =====
const messages = ref([])
const inputText = ref('')
const sending = ref(false)
const loading = ref(false)
const voiceEnabled = ref(true)
const chatRollRef = ref(null)
const fileInputRef = ref(null)
const uploadedImage = ref(null)
const imagePreviewVisible = ref(false)
const previewImageUrl = ref('')

const isHover = ref(false)
const showDialog = ref(false)
const dialogText = ref('')
const dialogPop = ref(false)
const dialogTimer = ref(null)
const dialogStyle = ref({})

const showQuestionDialog = ref(false)
const questionTab = ref('history')
const historyQuestions = ref([])
const questionSets = ref([])

const showPreviewDialog = ref(false)
const previewTitle = ref('')
const previewType = ref('')
const previewData = ref(null)
const previewQuestions = ref([])

// ===== 题集展开 =====
const expandedSetId = ref(null)
const setQuestionsMap = ref({})

// ===== 话语库 =====
const greetPhrases = [
  '你好呀~ 😊 今天想学点什么？',
  '嘿嘿，你来啦！ 🎉 我正等着你呢！',
  '嗨！好久不见~ 最近学习怎么样？ 📚',
  '欢迎回来！ 🤗 小基随时准备帮你！',
  '哟！你来啦！ 💪 今天也要加油哦！',
  '哈喽~ 有什么我可以帮你的吗？ ✨',
  '嘿嘿，看到你来我特别开心！ 😄',
  '今天状态怎么样？ 🌟 想聊点什么？'
]

const clickPhrases = [
  '嘿嘿，干嘛~ 😄 想跟我聊天吗？',
  '我在听呢 👂 继续说，我认真的！',
  '继续继续！ 💬 我超喜欢听你说话！',
  '你戳到我啦！ 😆 好痒！',
  '哈哈哈，别闹！ 🤣 我快笑死了！',
  '嗯嗯？ 👀 你叫我干嘛？',
  '我在我在！ 🙋 有什么吩咐？',
  '嘿嘿，被你发现了！ 😏 我正想找你呢！'
]

const doubleClickPhrases = [
  '哈哈，别戳啦！ 🤣 我快受不了了！',
  '好痒！ 😆 你再戳我也要戳你了！',
  '你手不累吗？ 😏 要不要休息一下？',
  '哎呀！ 😂 你是不是太无聊了！',
  '救命！ 🆘 我被戳到不行了！',
  '嘿嘿，这么喜欢戳我吗？ 😊 那就多聊聊天吧！',
  '别戳了别戳了！ 🙈 我投降！'
]

const hoverPhrases = [
  '你好呀~ 😊 有什么想聊的？',
  '我在听呢 👂 随时都在！',
  '今天想学什么？ 📚 我来帮你！',
  '这个问题有意思！ 🤔 让我想想！',
  '哈哈，继续继续！ 😄 我喜欢听你说话！',
  '嗯嗯，然后呢？ 💬 我在认真听！',
  '好棒！继续加油！ 💪 你是最棒的！',
  '我来帮你！ ✨ 有什么问题尽管说！',
  '嘿嘿，你看起来心情不错呀！ 🌟',
  '今天有什么新收获？ 🎯 跟我分享分享！'
]

const thinkingPhrases = [
  '让我想想... 🤔 这个问题有点意思！',
  '嗯... 我在认真思考！ 💭 等等我！',
  '稍等哦~ 🧠 我在整理思路！',
  '哈哈，这个问题问得好！ 🤔 让我好好想想！',
  '嗯嗯，我在想！ 💡 马上回答你！',
  '等一下哦~ ⏳ 我在组织语言！'
]

// ===== 工具函数 =====
function getTypeName(type) {
  const map = { choice: '选择题', fill: '填空题', judge: '判断题', essay: '简答题', calculation: '计算题', coding: '编程题' }
  return map[type] || type || '题目'
}

function getQuestionPreview(q) {
  const content = q?.question_content || q?.title || ''
  return content.length > 50 ? content.slice(0, 50) + '...' : content
}

function formatEvalText(text) {
  if (!text) return ''
  return text.replace(/\n/g, '<br/>')
}

function scrollToBottom() {
  if (chatRollRef.value) {
    chatRollRef.value.scrollTop = chatRollRef.value.scrollHeight
  }
}

function forceScrollToBottom() {
  if (chatRollRef.value) {
    chatRollRef.value.scrollTop = chatRollRef.value.scrollHeight
  }
}

// ===== 半球体效果 =====
function updateScale() {
  const container = chatRollRef.value
  if (!container) return
  const items = container.querySelectorAll('.roll-item')
  const containerHeight = container.clientHeight

  items.forEach((el) => {
    const rect = el.getBoundingClientRect()
    const containerRect = container.getBoundingClientRect()
    const itemBottom = rect.bottom - containerRect.top
    const distanceFromBottom = containerHeight - itemBottom

    const maxDistance = containerHeight
    const factor = Math.max(0.1, 1 - (distanceFromBottom / maxDistance) * 0.9)
    const opacity = 0.1 + factor * 0.9

    el.style.opacity = opacity
    el.style.transition = 'transform 0.1s ease, opacity 0.1s ease'
    el.style.transformOrigin = 'center center'
    el.style.filter = `brightness(${0.15 + factor * 0.85})`
  })
}

function onScroll() {
  updateScale()
}

watch(messages, () => {
  nextTick(() => {
    updateScale()
    forceScrollToBottom()
  })
})

// ===== 语音 =====
function speakText(text) {
  if (!voiceEnabled.value) return
  if (!window.speechSynthesis) return
  window.speechSynthesis.cancel()
  const utterance = new SpeechSynthesisUtterance(text)
  utterance.lang = 'zh-CN'
  utterance.rate = 1.0
  utterance.pitch = 1.0
  window.speechSynthesis.speak(utterance)
}

function randomPick(arr) {
  return arr[Math.floor(Math.random() * arr.length)]
}

// ===== 对话框 =====
async function showDialogBubble(text, addToChat = true) {
  const offsetX = (Math.random() - 0.5) * 80
  const offsetY = (Math.random() - 0.5) * 60 - 20
  dialogStyle.value = {
    transform: `translate(calc(-50% + ${offsetX}px), calc(-100% + ${offsetY}px))`
  }
  dialogText.value = text
  showDialog.value = true
  dialogPop.value = false

  await nextTick()
  setTimeout(() => {
    dialogPop.value = true
  }, 50)

  if (addToChat) {
    const assistantMsg = {
      role: 'assistant',
      content: text,
      image_url: null,
      created_at: new Date().toISOString()
    }
    messages.value.push(assistantMsg)
    await nextTick()
    forceScrollToBottom()
    setTimeout(updateScale, 50)
  }

  if (dialogTimer.value) clearTimeout(dialogTimer.value)
  dialogTimer.value = setTimeout(() => {
    showDialog.value = false
  }, 3000)
}

// ===== 交互 =====
function onAvatarClick() {
  const msg = randomPick(clickPhrases)
  showDialogBubble(msg, true)
  speakText(msg)
  setHappy()
  setTimeout(() => setIdle(), 1500)
}

function onAvatarDoubleClick() {
  const msg = randomPick(doubleClickPhrases)
  showDialogBubble(msg, true)
  speakText(msg)
  setHappy()
  setTimeout(() => setIdle(), 1500)
}

function onAvatarHover(val) {
  isHover.value = val
  if (val) {
    const phrase = randomPick(hoverPhrases)
    showDialogBubble(phrase, false)
  }
}

// ===== 加载消息 =====
async function loadMessages() {
  loading.value = true
  try {
    const res = await getXiaojiMessages(authStore.user.id)
    messages.value = res.messages || []
    await nextTick()
    forceScrollToBottom()
    setTimeout(() => {
      updateScale()
    }, 100)
    setIdle()
    setTimeout(() => {
      const phrase = randomPick(greetPhrases)
      showDialogBubble(phrase, false)
    }, 600)
  } catch (error) {
    console.error('加载消息失败:', error)
    messages.value = []
  } finally {
    loading.value = false
  }
}

function formatTime(time) {
  if (!time) return ''
  const t = new Date(time)
  return t.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

// ===== 发送消息 =====
async function sendMessage() {
  const text = inputText.value.trim()
  const image = uploadedImage.value

  if (!text && !image) {
    ElMessage.warning('请输入内容或上传图片')
    return
  }

  inputText.value = ''

  const userMsg = {
    role: 'user',
    content: text || '图片',
    image_url: image || null,
    is_question: false,
    is_set: false,
    created_at: new Date().toISOString()
  }
  messages.value.push(userMsg)
  const currentImage = image
  if (image) {
    removeImage()
  }
  await nextTick()
  forceScrollToBottom()
  setTimeout(updateScale, 50)

  sending.value = true
  setThinking('思考中...')

  try {
    let reply = ''
    if (currentImage) {
      const res = await xiaojiVision({
        user_id: authStore.user.id,
        image_url: currentImage,
        question: text || '这张图片里有什么？'
      })
      reply = res.reply || '图片理解失败，请重试'
    } else {
      const res = await sendXiaojiMessage({
        user_id: authStore.user.id,
        content: text
      })
      reply = res.reply || '嗯嗯，我在听~'
    }

    setSpeaking()
    await showDialogBubble(reply, true)
    speakText(reply)
    setHappy()

  } catch (error) {
    console.error('发送失败:', error)
    ElMessage.error('发送失败，请重试')
    setIdle()
  } finally {
    sending.value = false
  }
}

// ===== 切换题集展开 =====
async function toggleSetExpand(setId) {
  if (expandedSetId.value === setId) {
    expandedSetId.value = null
    return
  }
  expandedSetId.value = setId

  if (setQuestionsMap.value[setId] !== undefined) {
    return
  }

  setQuestionsMap.value[setId] = null
  const s = questionSets.value.find(item => item.id === setId)
  if (s) {
    const ids = s.question_ids || []
    const qs = []
    for (const id of ids) {
      try {
        const q = await getQuestionDetail(id)
        if (q) qs.push(q)
      } catch (e) {}
    }
    setQuestionsMap.value[setId] = qs
  } else {
    setQuestionsMap.value[setId] = []
  }
}

// ===== 发送题目 =====
async function sendSingleQuestion(q) {
  showQuestionDialog.value = false
  expandedSetId.value = null

  const userMsg = {
    role: 'user',
    content: `📝 ${q.title || q.question_content || '未命名题目'}`,
    is_question: true,
    questionData: q,
    created_at: new Date().toISOString()
  }
  messages.value.push(userMsg)
  await nextTick()
  forceScrollToBottom()
  setTimeout(updateScale, 50)

  sending.value = true

  startAgentFlow()
  const statusInterval = setInterval(() => {
    const next = nextAgent()
    if (!next) {
      clearInterval(statusInterval)
    }
  }, 1500)

  try {
    const res = await evaluateQuestion(authStore.user.id, q)
    const reply = res.reply || '好的，我来看看这道题~'

    clearInterval(statusInterval)
    setSpeaking()

    const assistantMsg = {
      role: 'assistant',
      content: reply,
      is_evaluation: true,
      created_at: new Date().toISOString()
    }
    messages.value.push(assistantMsg)
    await nextTick()
    forceScrollToBottom()
    setTimeout(updateScale, 50)
    speakText(reply)
    setHappy()

  } catch (error) {
    console.error('评价失败:', error)
    clearInterval(statusInterval)
    ElMessage.error('评价失败，请重试')
    setIdle()
  } finally {
    sending.value = false
  }
}

// ===== 发送题集 =====
async function sendWholeSet(s) {
  showQuestionDialog.value = false

  let questions = []
  const ids = s.question_ids || []
  for (const id of ids) {
    try {
      const q = await getQuestionDetail(id)
      if (q) questions.push(q)
    } catch (e) {}
  }

  const userMsg = {
    role: 'user',
    content: `📚 题集：${s.name}（${questions.length} 道题）`,
    is_set: true,
    setData: s,
    created_at: new Date().toISOString()
  }
  messages.value.push(userMsg)
  await nextTick()
  forceScrollToBottom()
  setTimeout(updateScale, 50)

  sending.value = true
  setThinking('分析题集中...')

  try {
    const res = await evaluateSet(authStore.user.id, s, questions)
    const reply = res.reply || '好的，我来看看这个题集~'

    setSpeaking()

    const assistantMsg = {
      role: 'assistant',
      content: reply,
      is_evaluation: true,
      created_at: new Date().toISOString()
    }
    messages.value.push(assistantMsg)
    await nextTick()
    forceScrollToBottom()
    setTimeout(updateScale, 50)
    speakText(reply)
    setHappy()

  } catch (error) {
    console.error('评价题集失败:', error)
    ElMessage.error('评价失败，请重试')
    setIdle()
  } finally {
    sending.value = false
  }
}

// ===== 预览 =====
function previewQuestion(q) {
  previewType.value = 'question'
  previewTitle.value = '📝 题目详情'
  previewData.value = q
  showPreviewDialog.value = true
}

async function previewSet(s) {
  previewType.value = 'set'
  previewData.value = s
  previewTitle.value = '📚 题集详情'

  const ids = s.question_ids || []
  const qs = []
  for (const id of ids) {
    try {
      const q = await getQuestionDetail(id)
      if (q) qs.push(q)
    } catch (e) {}
  }
  previewQuestions.value = qs
  showPreviewDialog.value = true
}

async function openSendQuestion() {
  showQuestionDialog.value = true
  expandedSetId.value = null
  setQuestionsMap.value = {}
  try {
    const res = await getGenerationHistory(authStore.user.id)
    historyQuestions.value = res || []
  } catch {
    historyQuestions.value = []
  }
  try {
    const res = await getQuestionSets(authStore.user.id)
    questionSets.value = res || []
  } catch {
    questionSets.value = []
  }
}

// ===== 图片 =====
function triggerImageUpload() {
  fileInputRef.value?.click()
}

function handleImageSelect(event) {
  const file = event.target.files[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = (e) => {
    uploadedImage.value = e.target.result
  }
  reader.readAsDataURL(file)
  event.target.value = ''
}

function removeImage() {
  uploadedImage.value = null
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
}

function toggleVoice() {
  voiceEnabled.value = !voiceEnabled.value
  if (!voiceEnabled.value && window.speechSynthesis) {
    window.speechSynthesis.cancel()
  }
  ElMessage.info(voiceEnabled.value ? '语音播报已开启' : '语音播报已关闭')
}

async function clearHistory() {
  try {
    await ElMessageBox.confirm('确定要清空所有聊天记录吗？', '确认清空', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await clearXiaojiMessages(authStore.user.id)
    messages.value = []
    ElMessage.success('已清空')
  } catch {}
}

function goBack() {
  setSleeping()
  router.back()
}

function goSettings() {
  router.push('/xiaoji/settings')
}

function showDeveloping() {
  ElMessage.info('功能开发中，敬请期待')
}

function handleResize() {
  updateScale()
}

watch(messages, () => {
  nextTick(() => {
    forceScrollToBottom()
    setTimeout(updateScale, 50)
  })
})

onMounted(() => {
  loadMessages()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.xiaoji-call-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--bg-color);
  color: var(--text-primary);
  overflow: hidden;
}

.call-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 20px;
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
  background: rgba(255,255,255,0.03);
  backdrop-filter: blur(12px);
}
.nav-back {
  font-size: 18px;
  color: var(--text-secondary) !important;
}
.nav-back:hover {
  color: var(--text-primary) !important;
}
.nav-center {
  display: flex;
  align-items: center;
  gap: 10px;
}
.nav-avatar-wrapper {
  width: 40px;
  height: 40px;
  flex-shrink: 0;
}
.nav-avatar {
  width: 40px;
  height: 40px;
  border-radius: 0;
  object-fit: contain;
  display: block;
}
.nav-name {
  font-size: 15px;
  font-weight: 600;
}
.nav-status {
  font-size: 12px;
  color: var(--text-muted);
}
.nav-actions {
  display: flex;
  gap: 4px;
}
.nav-action {
  font-size: 16px;
  color: var(--text-secondary) !important;
}
.nav-action:hover {
  color: var(--text-primary) !important;
}

.xiaoji-area {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 8px 0 2px;
  flex-shrink: 0;
}
.xiaoji-glow-ring {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 160px;
  height: 160px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(64,158,255,0.08) 0%, transparent 70%);
  pointer-events: none;
  animation: glowPulse 3s ease-in-out infinite;
}
.xiaoji-glow-ring-2 {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 200px;
  height: 200px;
  border-radius: 50%;
  border: 1px solid rgba(64,158,255,0.04);
  pointer-events: none;
  animation: ringRotate 20s linear infinite;
}
@keyframes glowPulse {
  0%, 100% { opacity: 0.4; transform: translate(-50%, -50%) scale(1); }
  50% { opacity: 1; transform: translate(-50%, -50%) scale(1.05); }
}
@keyframes ringRotate {
  0% { transform: translate(-50%, -50%) rotate(0deg); }
  100% { transform: translate(-50%, -50%) rotate(360deg); }
}

.xiaoji-click-area {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  padding: 8px;
  border-radius: 20px;
  transition: all 0.3s ease;
  z-index: 2;
}
.xiaoji-click-area:hover .xiaoji-image {
  transform: scale(1.04) rotate(2deg);
  filter: drop-shadow(0 0 40px rgba(64,158,255,0.25));
}

.xiaoji-shadow {
  position: absolute;
  bottom: 4px;
  left: 50%;
  transform: translateX(-50%);
  width: 50%;
  height: 12px;
  border-radius: 50%;
  background: radial-gradient(ellipse, rgba(0,0,0,0.12) 0%, transparent 70%);
  pointer-events: none;
}
.xiaoji-image {
  width: 130px;
  height: 130px;
  object-fit: contain;
  display: block;
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  filter: drop-shadow(0 4px 30px rgba(64,158,255,0.08));
}
.xiaoji-image.hover {
  transform: scale(1.04);
  filter: drop-shadow(0 0 50px rgba(64,158,255,0.2));
}

.xiaoji-status-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  margin-top: 2px;
}
.status-tag {
  font-size: 12px !important;
  font-weight: 500 !important;
}
.agent-progress {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  width: 100%;
  max-width: 200px;
}
.agent-progress-bar {
  width: 100%;
}
.agent-info {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-secondary);
}
.agent-tag {
  font-size: 11px !important;
}
.agent-desc {
  font-size: 11px;
  color: var(--text-muted);
}

.xiaoji-status-badge {
  font-size: 12px;
  color: var(--text-muted);
  background: rgba(128,128,128,0.06);
  padding: 2px 14px;
  border-radius: 10px;
  margin-top: 2px;
  backdrop-filter: blur(4px);
}

.xiaoji-dialog {
  position: absolute;
  top: 0;
  left: 50%;
  transform: translate(-50%, -100%);
  background: rgba(255,255,255,0.08);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 16px;
  padding: 8px 18px;
  font-size: 14px;
  color: var(--text-primary);
  white-space: nowrap;
  box-shadow: 0 8px 40px rgba(0,0,0,0.12);
  opacity: 0;
  transform-origin: bottom center;
  pointer-events: none;
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  z-index: 10;
}
.xiaoji-dialog.pop {
  opacity: 1;
  transform: translate(-50%, calc(-100% - 12px));
}
.dialog-tail {
  position: absolute;
  bottom: -6px;
  left: 50%;
  transform: translateX(-50%) rotate(45deg);
  width: 12px;
  height: 12px;
  background: rgba(255,255,255,0.08);
  border-right: 1px solid rgba(255,255,255,0.08);
  border-bottom: 1px solid rgba(255,255,255,0.08);
  backdrop-filter: blur(20px);
}

.chat-area-wrapper {
  flex: 1;
  display: flex;
  justify-content: center;
  padding: 0 24px;
  min-height: 0;
}

.chat-cylinder-wrapper {
  flex: 1;
  max-width: 800px;
  position: relative;
  padding: 4px 0;
  border-radius: 24px;
  background: radial-gradient(ellipse at center, rgba(64,158,255,0.02) 0%, transparent 80%);
  overflow: hidden;
}
.chat-cylinder-glow {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 80%;
  height: 60%;
  border-radius: 50%;
  background: radial-gradient(ellipse, rgba(64,158,255,0.03) 0%, transparent 70%);
  pointer-events: none;
}

.chat-roll {
  height: 100%;
  padding: 8px 16px 4px;
  overflow-y: auto;
  scroll-behavior: smooth;
}
.chat-roll::-webkit-scrollbar {
  width: 3px;
}
.chat-roll::-webkit-scrollbar-thumb {
  background: rgba(128,128,128,0.12);
  border-radius: 2px;
}

.roll-loading,
.roll-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-muted);
  font-size: 15px;
}
.roll-empty {
  opacity: 0.4;
}

.roll-messages {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 4px 0 8px;
  align-items: center;
  justify-content: flex-end;
  min-height: 100%;
}

.roll-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 20px;
  border-radius: 16px;
  max-width: 70%;
  width: auto;
  transition: transform 0.1s ease, opacity 0.1s ease, filter 0.1s ease;
  transform-origin: center center;
  will-change: transform, opacity, filter;
  box-shadow: 0 2px 16px rgba(0,0,0,0.02);
}
.roll-item.user {
  align-self: flex-end;
  flex-direction: row-reverse;
  background: rgba(64,158,255,0.08);
  border: 1px solid rgba(64,158,255,0.06);
}
.roll-item.assistant {
  align-self: flex-start;
  background: rgba(128,128,128,0.03);
  border: 1px solid rgba(128,128,128,0.04);
}

.roll-avatar {
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  border-radius: 50%;
  overflow: hidden;
}
.user-avatar-img {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
}
.xiaoji-avatar-img {
  width: 100%;
  height: 100%;
  border-radius: 0;
  object-fit: contain;
  display: block;
}

.roll-content {
  font-size: 17px;
  line-height: 1.7;
  word-break: break-word;
  flex: 1;
}
.roll-time {
  font-size: 11px;
  color: var(--text-muted);
  flex-shrink: 0;
  margin-top: 2px;
  align-self: flex-end;
}

/* ===== 图片样式 ===== */
.message-image {
  max-width: 200px;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  margin-bottom: 6px;
}
.message-image img {
  width: 100%;
  height: auto;
  display: block;
  max-height: 180px;
  object-fit: cover;
}

.message-card {
  padding: 12px 16px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: rgba(255,255,255,0.04);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255,255,255,0.06);
  min-width: 220px;
}
.message-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0,0,0,0.06);
  border-color: rgba(64,158,255,0.15);
}

.question-card .card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}
.question-card .card-icon { font-size: 18px; }
.question-card .card-title { font-weight: 600; font-size: 15px; flex: 1; }
.question-card .card-badge {
  font-size: 11px;
  padding: 2px 10px;
  border-radius: 10px;
  background: rgba(64,158,255,0.08);
  color: #409eff;
}
.question-card .card-difficulty-badge {
  font-size: 11px;
  padding: 2px 10px;
  border-radius: 10px;
  background: rgba(128,128,128,0.06);
  color: var(--text-muted);
}
.question-card .card-body {
  margin: 4px 0;
}
.question-card .card-question {
  font-size: 14px;
  color: var(--text-primary);
  line-height: 1.6;
  margin-bottom: 4px;
}
.question-card .card-options {
  margin: 2px 0 4px;
  padding-left: 8px;
}
.question-card .card-option {
  font-size: 13px;
  color: var(--text-secondary);
  padding: 2px 0;
}
.question-card .card-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: 4px;
}
.question-card .card-hint {
  font-size: 11px;
  color: #409eff;
  opacity: 0.6;
}

.set-card .card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}
.set-card .card-icon { font-size: 18px; }
.set-card .card-title { font-weight: 600; font-size: 15px; flex: 1; }
.set-card .card-badge {
  font-size: 11px;
  padding: 2px 10px;
  border-radius: 10px;
  background: rgba(139,92,246,0.08);
  color: #8b5cf6;
}
.set-card .card-body {
  margin: 6px 0 4px;
  color: var(--text-primary);
  font-size: 14px;
}
.set-card .card-footer {
  display: flex;
  justify-content: flex-end;
  font-size: 12px;
  color: var(--text-muted);
}
.set-card .card-hint {
  color: #8b5cf6;
  opacity: 0.6;
}

.evaluation-content {
  width: 100%;
}
.eval-badge {
  font-size: 12px;
  font-weight: 600;
  color: #f59e0b;
  background: rgba(245,158,11,0.08);
  padding: 2px 12px;
  border-radius: 10px;
  display: inline-block;
  margin-bottom: 6px;
}
.eval-text {
  font-size: 15px;
  line-height: 1.8;
  white-space: pre-wrap;
}

.typing-dots-inline {
  display: inline-flex;
  gap: 4px;
  align-items: center;
  padding: 0 4px;
}
.typing-dots-inline span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--text-muted);
  animation: typingBounce 1.4s infinite both;
}
.typing-dots-inline span:nth-child(1) { animation-delay: -0.32s; }
.typing-dots-inline span:nth-child(2) { animation-delay: -0.16s; }
.typing-dots-inline span:nth-child(3) { animation-delay: 0s; }
@keyframes typingBounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

.call-input-area {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px 24px 14px;
  border-top: 1px solid var(--border-color);
  background: rgba(255,255,255,0.02);
  backdrop-filter: blur(12px);
}
.input-tools {
  display: flex;
  gap: 4px;
  margin-bottom: 4px;
  width: 100%;
  max-width: 600px;
}
.tool-btn {
  width: 34px;
  height: 34px;
  border: none;
  border-radius: 50%;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 15px;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}
.tool-btn:hover:not(.disabled) {
  background: rgba(128,128,128,0.06);
  color: var(--text-primary);
}
.tool-btn.active {
  color: #409eff;
}
.tool-btn.disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.input-row {
  display: flex;
  gap: 8px;
  width: 100%;
  max-width: 600px;
}
.chat-input {
  flex: 1;
}
.chat-input :deep(.el-input__wrapper) {
  background: rgba(128,128,128,0.03);
  border-color: var(--border-color);
  border-radius: 12px;
}
.chat-input :deep(.el-input-group__append) {
  background: rgba(64,158,255,0.06);
  border-color: var(--border-color);
  border-radius: 0 12px 12px 0;
}

.image-preview {
  position: relative;
  display: inline-block;
  margin-top: 4px;
  width: 100%;
  max-width: 600px;
}
.image-preview img {
  width: 44px;
  height: 44px;
  border-radius: 8px;
  object-fit: cover;
}
.remove-image {
  position: absolute;
  top: -4px;
  right: -4px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: none;
  background: rgba(239,68,68,0.9);
  color: #fff;
  cursor: pointer;
  font-size: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* ===== 弹窗 ===== */
.custom-glass-dialog :deep(.el-dialog) {
  background: rgba(255,255,255,0.04) !important;
  backdrop-filter: blur(24px) !important;
  -webkit-backdrop-filter: blur(24px) !important;
  border: 1px solid rgba(255,255,255,0.06) !important;
  border-radius: 20px !important;
  box-shadow: 0 8px 40px rgba(0,0,0,0.08) !important;
}
[data-theme="dark"] .custom-glass-dialog :deep(.el-dialog) {
  background: rgba(0,0,0,0.35) !important;
  border-color: rgba(255,255,255,0.04) !important;
}
.custom-glass-dialog :deep(.el-dialog__title) {
  color: var(--text-primary) !important;
  font-weight: 600 !important;
}
.custom-glass-dialog :deep(.el-dialog__body) {
  padding: 16px 24px 24px !important;
}
.custom-glass-dialog :deep(.el-dialog__header) {
  padding: 16px 24px 8px !important;
  border-bottom: 1px solid rgba(255,255,255,0.04) !important;
}
.custom-glass-dialog :deep(.el-dialog__headerbtn) {
  color: var(--text-secondary) !important;
}
.custom-glass-dialog :deep(.el-dialog__headerbtn:hover) {
  color: var(--text-primary) !important;
}

.custom-glass-tabs :deep(.el-tabs__header) {
  border-bottom: 1px solid rgba(255,255,255,0.04) !important;
}
.custom-glass-tabs :deep(.el-tabs__item) {
  color: var(--text-secondary) !important;
  font-size: 14px !important;
}
.custom-glass-tabs :deep(.el-tabs__item.is-active) {
  color: var(--text-primary) !important;
}
.custom-glass-tabs :deep(.el-tabs__item:hover) {
  color: var(--text-primary) !important;
}
.custom-glass-tabs :deep(.el-tabs__active-bar) {
  background: #409eff !important;
}

.preview-content {
  max-height: 400px;
  overflow-y: auto;
}

/* ===== 预览弹窗（蓝色） ===== */
.preview-question h4 {
  margin: 0 0 12px;
  color: #409eff;
  font-size: 17px;
}
.preview-question p {
  margin: 6px 0;
  font-size: 14px;
  color: #409eff;
  line-height: 1.7;
}
.preview-question p strong {
  color: #409eff;
  font-weight: 600;
}
.option-item {
  padding: 4px 12px;
  margin: 2px 0;
  border-radius: 6px;
  background: rgba(64,158,255,0.06);
  font-size: 14px;
  color: #409eff;
}
.code-block {
  background: rgba(0,0,0,0.06);
  padding: 12px;
  border-radius: 8px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  white-space: pre-wrap;
  overflow-x: auto;
  margin: 4px 0;
  color: #409eff;
}

.preview-set p {
  margin: 6px 0;
  font-size: 14px;
  color: var(--text-secondary);
}
.preview-set p strong {
  color: var(--text-primary);
}

.set-questions-list {
  margin-top: 4px;
  padding: 6px 8px;
  border-radius: 8px;
  background: rgba(128,128,128,0.02);
  border: 1px solid var(--border-color);
  max-height: 200px;
  overflow-y: auto;
}

.loading-tip {
  text-align: center;
  padding: 12px 0;
  color: var(--text-muted);
  font-size: 13px;
}

.set-question-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  border-bottom: 1px solid rgba(128,128,128,0.04);
}
.set-question-item:hover {
  background: rgba(64,158,255,0.04);
}
.set-question-item:last-child {
  border-bottom: none;
}
.sq-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.sq-title {
  font-size: 13px;
  color: var(--text-primary);
  font-weight: 500;
}
.sq-preview {
  font-size: 12px;
  color: var(--text-muted);
  opacity: 0.7;
}
.sq-type {
  font-size: 11px;
  color: var(--text-muted);
  padding: 0 8px;
  border-radius: 4px;
  background: rgba(128,128,128,0.04);
}

.question-dialog {
  max-height: 420px;
  overflow-y: auto;
}
.question-dialog::-webkit-scrollbar {
  width: 3px;
}
.question-dialog::-webkit-scrollbar-thumb {
  background: rgba(128,128,128,0.12);
  border-radius: 2px;
}

.question-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  border-radius: 10px;
  border: 1px solid var(--border-color);
  margin-bottom: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: rgba(255,255,255,0.02);
}
.question-item:hover {
  background: rgba(64,158,255,0.04);
  border-color: rgba(64,158,255,0.12);
}
.q-title {
  flex: 1;
  font-size: 14px;
  color: #409eff;
}
.q-type {
  font-size: 12px;
  color: var(--text-muted);
  margin: 0 12px;
}

/* ===== 题集弹窗（蓝色） ===== */
.set-item-wrapper {
  margin-bottom: 6px;
}
.set-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  border-radius: 10px;
  border: 1px solid var(--border-color);
  cursor: pointer;
  transition: all 0.3s ease;
  background: rgba(255,255,255,0.02);
}
.set-item:hover {
  background: rgba(139,92,246,0.04);
  border-color: rgba(139,92,246,0.12);
}
.set-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}
.set-name {
  font-size: 14px;
  font-weight: 500;
  color: #409eff;
}
.set-count {
  font-size: 12px;
  color: var(--text-muted);
}
.set-expand-icon {
  transition: transform 0.3s ease;
  color: var(--text-muted);
  font-size: 14px;
}
.set-expand-icon.expanded {
  transform: rotate(180deg);
}

.empty-tip {
  text-align: center;
  color: var(--text-muted);
  padding: 30px 0;
}

.image-preview-dialog :deep(.el-dialog) {
  background: rgba(0,0,0,0.8) !important;
  border: none !important;
}
.image-preview-dialog :deep(.el-dialog__body) {
  padding: 0 !important;
}
.preview-image {
  width: 100%;
  max-height: 80vh;
  object-fit: contain;
}

[data-theme="dark"] .xiaoji-call-page {
  background: rgba(0,0,0,0.06);
}
[data-theme="dark"] .roll-item.user {
  background: rgba(64,158,255,0.06);
}
[data-theme="dark"] .xiaoji-dialog {
  background: rgba(0,0,0,0.4);
}
[data-theme="dark"] .chat-cylinder-wrapper {
  background: radial-gradient(ellipse at center, rgba(64,158,255,0.02) 0%, transparent 80%);
}
[data-theme="dark"] .message-card {
  background: rgba(255,255,255,0.02);
  border-color: rgba(255,255,255,0.04);
}
[data-theme="dark"] .call-nav {
  background: rgba(0,0,0,0.2);
}
[data-theme="dark"] .call-input-area {
  background: rgba(0,0,0,0.15);
}
[data-theme="dark"] .question-item {
  border-color: rgba(255,255,255,0.04);
}
[data-theme="dark"] .question-item:hover {
  background: rgba(64,158,255,0.04);
}
[data-theme="dark"] .set-item {
  border-color: rgba(255,255,255,0.04);
}
[data-theme="dark"] .set-item:hover {
  background: rgba(139,92,246,0.04);
}
[data-theme="dark"] .set-questions-list {
  background: rgba(255,255,255,0.02);
  border-color: rgba(255,255,255,0.04);
}
[data-theme="dark"] .set-name {
  color: #66b1ff;
}
[data-theme="dark"] .q-title {
  color: #66b1ff;
}
[data-theme="dark"] .preview-question h4 {
  color: #66b1ff;
}
[data-theme="dark"] .preview-question p {
  color: #66b1ff;
}
[data-theme="dark"] .preview-question p strong {
  color: #66b1ff;
}
[data-theme="dark"] .option-item {
  color: #66b1ff;
  background: rgba(64,158,255,0.08);
}
[data-theme="dark"] .code-block {
  color: #66b1ff;
}
[data-theme="dark"] .sq-title {
  color: rgba(255,255,255,0.8);
}

@media (max-width: 640px) {
  .call-nav {
    padding: 8px 14px;
  }
  .xiaoji-image {
    width: 96px;
    height: 96px;
  }
  .xiaoji-glow-ring {
    width: 120px;
    height: 120px;
  }
  .xiaoji-glow-ring-2 {
    width: 150px;
    height: 150px;
  }
  .chat-area-wrapper {
    padding: 0 12px;
  }
  .chat-cylinder-wrapper {
    border-radius: 16px;
  }
  .chat-roll {
    padding: 6px 10px 2px;
  }
  .roll-item {
    max-width: 82%;
    padding: 8px 14px;
    gap: 8px;
  }
  .roll-content {
    font-size: 15px;
  }
  .roll-avatar {
    width: 32px;
    height: 32px;
  }
  .call-input-area {
    padding: 6px 14px 10px;
  }
  .input-tools {
    max-width: 100%;
  }
  .input-row {
    max-width: 100%;
  }
  .xiaoji-dialog {
    font-size: 12px;
    padding: 4px 12px;
  }
  .message-card {
    min-width: 160px;
    padding: 8px 12px;
  }
  .question-dialog {
    max-height: 320px;
  }
  .custom-glass-dialog :deep(.el-dialog) {
    width: 92% !important;
    margin: 0 auto !important;
  }
  .message-image {
    max-width: 140px;
  }
}
</style>