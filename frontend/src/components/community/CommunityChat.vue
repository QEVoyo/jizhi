<template>
  <div class="community-chat">
    <!-- ===== 聊天头部 ===== -->
    <div class="chat-header">
      <el-button text class="back-btn" @click="goBack">
        <i class="fas fa-arrow-left"></i>
      </el-button>
      <div class="chat-user" @click="goUserProfile">
        <el-avatar :size="36" :src="chatPartner?.avatar || ''" class="chat-avatar">
          {{ chatPartner?.name?.[0] || 'U' }}
        </el-avatar>
        <div class="chat-user-info">
          <span class="chat-username">{{ chatPartner?.name || '用户' }}</span>
          <span class="chat-status" :class="{ online: chatPartner?.status === 'online' }">
            {{ chatPartner?.status === 'online' ? '在线' : '离线' }}
          </span>
        </div>
        <span v-if="isXiaoji" class="xiaoji-badge">AI</span>
      </div>
      <div class="chat-actions">
        <el-button text class="action-btn" @click="toggleVoice" :class="{ active: voiceEnabled }">
          <i :class="voiceEnabled ? 'fas fa-volume-up' : 'fas fa-volume-mute'"></i>
        </el-button>
        <el-button v-if="isXiaoji" text class="action-btn" @click="goSettings">
          <i class="fas fa-cog"></i>
        </el-button>
        <el-button v-if="isXiaoji" text class="action-btn" @click="goCall">
          <i class="fas fa-phone"></i>
        </el-button>
      </div>
    </div>

    <el-divider />

    <div class="message-list-wrapper">
      <div class="message-list" ref="messageListRef" id="messageList">
        <div v-if="loading" class="loading-state">
          <i class="fas fa-spinner fa-spin"></i>
          <span>加载中...</span>
        </div>
        <div v-else-if="!messages.length" class="empty-state">
          <div class="empty-icon">
            <i class="fas fa-comment-dots"></i>
          </div>
          <p class="empty-title">{{ isXiaoji ? '开始和小基聊天' : '暂无消息' }}</p>
          <p class="empty-desc">{{ isXiaoji ? '小基是一个温暖的学习伙伴，随时陪你聊天' : '开始你们的对话吧' }}</p>
        </div>
        <div
          v-for="msg in messages"
          :key="msg.id"
          class="message-item"
          :class="{ sent: msg.sender_id === authStore.user.id }"
        >
          <div v-if="msg.sender_id !== authStore.user.id" class="message-avatar">
            <el-avatar
              :size="28"
              :src="isXiaoji ? '/logo.png' : (chatPartner?.avatar || '')"
            >
              {{ !isXiaoji && !chatPartner?.avatar ? (chatPartner?.name?.[0] || 'U') : '' }}
            </el-avatar>
          </div>

          <div class="message-content-wrapper">
            <!-- 图片 -->
        <div v-if="msg.image_url" class="message-image" @click="previewImage(msg.image_url)">
        <img
            :src="msg.image_url"
            alt="图片"
            @error="msg.image_url = '/images/placeholder.png'"
        />
        <span v-if="msg.content && msg.content !== '[图片]'" class="image-caption">{{ msg.content }}</span>
        </div>
            <!-- 题目卡片 -->
            <div v-else-if="msg.question_id" class="message-card question-card" @click="goDoQuestion(msg)">
              <div class="card-header">
                <span class="card-icon">📝</span>
                <span class="card-title">{{ msg.question_title || '题目' }}</span>
                <span class="card-badge">{{ msg.question_type || '题目' }}</span>
              </div>
              <div class="card-body">
                <span class="card-preview">{{ msg.question_content || msg.question_title || '点击查看题目详情' }}</span>
              </div>
              <div class="card-footer">
                <span class="card-hint">点击去做题 →</span>
              </div>
            </div>
            <!-- 文本 -->
            <div v-else class="message-bubble">
              <span class="message-text">{{ msg.content }}</span>
            </div>
            <span class="message-time">{{ formatTime(msg.created_at) }}</span>
          </div>
        </div>
      </div>
    </div>

    <el-dialog v-model="imagePreviewVisible" width="80%" class="image-preview-dialog" destroy-on-close>
      <img :src="previewImageUrl" alt="预览" class="preview-image" />
    </el-dialog>

    <!-- ===== 发送题目弹窗 ===== -->
    <el-dialog
      v-model="showQuestionDialog"
      title="📤 发送题目"
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
              @click="sendQuestionToFriend(q)"
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
                  @click="sendQuestionToFriend(q)"
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

    <!-- ===== 题集预览弹窗 ===== -->
    <el-dialog
      v-model="showPreviewDialog"
      title="📚 题集详情"
      width="600px"
      destroy-on-close
      class="custom-glass-dialog"
    >
      <div class="preview-content">
        <div class="preview-set">
          <p><strong>题集名称：</strong>{{ previewSetData?.name }}</p>
          <p><strong>描述：</strong>{{ previewSetData?.description || '无描述' }}</p>
          <p><strong>题目数量：</strong>{{ previewSetData?.question_ids?.length || 0 }}</p>
          <div v-if="previewSetQuestions.length > 0" class="set-questions-list">
            <p><strong>包含题目：</strong></p>
            <div v-for="(q, idx) in previewSetQuestions" :key="idx" class="set-question-item">
              <span class="sq-index">{{ idx + 1 }}.</span>
              <span class="sq-title">{{ q.title || q.question_content || '未命名题目' }}</span>
              <span class="sq-type">{{ getTypeName(q.question_type) }}</span>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>

    <div class="chat-input-wrapper">
      <div v-if="uploadedImage" class="image-preview-thumb">
        <div class="thumb-wrapper" @click="previewImage(uploadedImage)">
          <img :src="uploadedImage" alt="待发送图片" />
        </div>
        <button class="remove-image-btn" @click="removeImage">
          <i class="fas fa-times"></i>
        </button>
      </div>

      <div class="chat-input-row">
        <div class="chat-tools">
          <button class="tool-btn" :class="{ active: voiceInputActive }" @click="toggleVoiceInput">
            <i :class="voiceInputActive ? 'fas fa-microphone-slash' : 'fas fa-microphone'"></i>
          </button>
          <button class="tool-btn" @click="triggerImageUpload">
            <i class="fas fa-image"></i>
          </button>
          <button class="tool-btn" @click="openSendQuestion">
            <i class="fas fa-paper-plane"></i>
          </button>
          <input ref="fileInputRef" type="file" accept="image/*" style="display: none" @change="handleImageSelect" />
        </div>

        <div class="chat-input-field">
          <input v-model="inputContent" :placeholder="isXiaoji ? '给小基发消息...' : '输入消息...'" class="input-field" @keyup.enter="handleSendMessage" />
          <button class="send-btn" :disabled="sending" @click="handleSendMessage">
            <i v-if="!sending" class="fas fa-paper-plane"></i>
            <i v-else class="fas fa-spinner fa-spin"></i>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import {
  getMessages,
  sendMessage,
  sendXiaojiMessage,
  xiaojiVision,
  getXiaojiMessages,
  getFriends
} from '@/api/community'
import { getGenerationHistory, getQuestionSets, getQuestionDetail } from '@/api/questions'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const friendId = route.params.friendId
const isXiaoji = computed(() => friendId === 'xiaoji')

// ===== 好友信息 =====
const chatPartner = ref({
  name: '用户',
  avatar: '',
  status: 'offline'
})

// ===== 聊天 =====
const messages = ref([])
const inputContent = ref('')
const loading = ref(false)
const sending = ref(false)
const voiceInputActive = ref(false)
const voiceEnabled = ref(true)
const fileInputRef = ref(null)
const messageListRef = ref(null)
const uploadedImage = ref(null)
const imagePreviewVisible = ref(false)
const previewImageUrl = ref('')
const recognition = ref(null)

// ===== 发送题目 =====
const showQuestionDialog = ref(false)
const questionTab = ref('history')
const historyQuestions = ref([])
const questionSets = ref([])
const expandedSetId = ref(null)
const setQuestionsMap = ref({})
const showPreviewDialog = ref(false)
const previewSetData = ref(null)
const previewSetQuestions = ref([])

// ===== 加载好友信息 =====
async function loadPartnerInfo() {
  if (isXiaoji.value) {
    chatPartner.value = {
      name: '小基',
      avatar: '/logo.png',
      status: 'online'
    }
    return
  }

  try {
    const res = await getFriends(authStore.user.id)
    const friends = res.friends || []
    const friend = friends.find(f => f.id === friendId)
    if (friend) {
      chatPartner.value = {
        name: friend.nickname || '用户',
        avatar: friend.avatar_url || '',
        status: friend.status || 'offline'
      }
    } else {
      chatPartner.value = {
        name: '用户',
        avatar: '',
        status: 'offline'
      }
    }
  } catch {
    chatPartner.value = {
      name: '用户',
      avatar: '',
      status: 'offline'
    }
  }
}

function getTypeName(type) {
  const map = { choice: '选择题', fill: '填空题', judge: '判断题', essay: '简答题', calculation: '计算题', coding: '编程题' }
  return map[type] || type || '题目'
}

function goBack() {
  router.push('/community/friends')
}

function goUserProfile() {
  if (isXiaoji.value) {
    ElMessage.info('小基设置开发中')
    return
  }
  router.push(`/community/user/${friendId}`)
}

function goSettings() {
  router.push('/xiaoji/settings')
}

function goCall() {
  router.push('/xiaoji/call')
}

function goDoQuestion(msg) {
  // 如果消息里带了完整的题目数据，通过 URL 参数传递
  if (msg.question_data) {
    const encoded = encodeURIComponent(JSON.stringify(msg.question_data))
    router.push(`/do-question/${msg.question_id}?data=${encoded}`)
  } else if (msg.question_id) {
    // 兼容旧数据：只有 ID，没有完整数据
    router.push(`/do-question/${msg.question_id}`)
  } else {
    ElMessage.warning('题目数据不完整')
  }
}

function formatTime(time) {
  if (!time) return ''
  let utcStr = time
  if (!time.endsWith('Z') && !time.includes('+')) {
    utcStr = time + 'Z'
  }
  const t = new Date(utcStr)
  if (isNaN(t.getTime())) return ''
  return t.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

function previewImage(url) {
  previewImageUrl.value = url
  imagePreviewVisible.value = true
}

function scrollToBottom() {
  const el = document.getElementById('messageList')
  if (el) {
    el.scrollTop = el.scrollHeight
  }
}

async function loadMessages() {
  loading.value = true
  try {
    let res
    if (isXiaoji.value) {
      res = await getXiaojiMessages(authStore.user.id)
    } else {
      res = await getMessages(authStore.user.id, friendId)
    }
    messages.value = res.messages || []
    await nextTick()
    scrollToBottom()
  } catch {
    ElMessage.error('加载消息失败')
  } finally {
    loading.value = false
  }
}

function removeImage() {
  uploadedImage.value = null
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
}

function triggerImageUpload() {
  fileInputRef.value?.click()
}

import { uploadImage } from '@/api/upload'  // 文件顶部加上

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

// ===== 发送题目 =====
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

async function toggleSetExpand(setId) {
  if (expandedSetId.value === setId) {
    expandedSetId.value = null
    return
  }
  expandedSetId.value = setId
  if (setQuestionsMap.value[setId] !== undefined) return
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

// ===== 发送题目到好友（核心修复：携带完整题目数据） =====
async function sendQuestionToFriend(q) {
  showQuestionDialog.value = false
  expandedSetId.value = null

  // 构建完整的题目数据（不管来源是哪里）
  const questionData = {
    id: q.id,
    title: q.title || q.question_content || '未命名题目',
    question_type: q.question_type || 'choice',
    question_content: q.question_content || q.title || '',
    options: q.options || {},
    answer: q.answer || '',
    explanation: q.explanation || '',
    difficulty_score: q.difficulty_score || 5,
    category: q.category || '',
    topic: q.topic || '',
    source: q.source || 'generated'
  }

  const content = `📝 ${questionData.title}`

  // 本地消息列表里也存一份完整数据
  const userMsg = {
    id: Date.now().toString(),
    sender_id: authStore.user.id,
    content: content,
    question_id: q.id,
    question_data: questionData,
    question_title: questionData.title,
    question_type: getTypeName(q.question_type),
    question_content: q.question_content || q.title || '',
    created_at: new Date().toISOString()
  }
  messages.value.push(userMsg)
  await nextTick()
  scrollToBottom()

  sending.value = true
  try {
    // 发送给后端时也带上 question_data
    await sendMessage(authStore.user.id, {
      receiver_id: friendId,
      message_type: 'text',
      content: content,
      question_id: q.id,
      question_data: questionData
    })
  } catch {
    ElMessage.error('发送失败')
    messages.value = messages.value.filter(m => m.id !== userMsg.id)
  } finally {
    sending.value = false
  }
}

// ===== 发送消息 =====
async function handleSendMessage() {
  const content = inputContent.value.trim()
  const image = uploadedImage.value

  if (!content && !image) {
    ElMessage.warning('请输入内容或选择图片')
    return
  }

  const currentContent = content
  const currentImage = image

  let displayContent = currentContent
  if (currentImage && currentContent) {
    displayContent = currentContent + ' [图片]'
  } else if (currentImage) {
    displayContent = '[图片]'
  }

  const userMsg = {
    id: Date.now().toString(),
    sender_id: authStore.user.id,
    content: displayContent,
    image_url: currentImage || null,
    created_at: new Date().toISOString()
  }
  messages.value.push(userMsg)
  inputContent.value = ''
  removeImage()
  await nextTick()
  scrollToBottom()

  if (isXiaoji.value) {
    if (currentImage) {
      sending.value = true
      try {
        const res = await xiaojiVision({
          user_id: authStore.user.id,
          image_url: currentImage,
          question: currentContent || '这张图片里有什么？请用中文描述'
        })
        const reply = res.reply || '这张图片我看不太清楚呢~'
        messages.value.push({
          id: (Date.now() + 1).toString(),
          sender_id: 'xiaoji',
          content: reply,
          created_at: new Date().toISOString()
        })
        await nextTick()
        scrollToBottom()
        if (voiceEnabled.value) speakText(reply)
      } catch {
        ElMessage.error('图片理解失败')
      } finally {
        sending.value = false
      }
      return
    }

    sending.value = true
    try {
      const res = await sendXiaojiMessage({
        user_id: authStore.user.id,
        content: currentContent
      })
      const reply = res.reply || '嗯嗯，我在听~'
      messages.value.push({
        id: (Date.now() + 1).toString(),
        sender_id: 'xiaoji',
        content: reply,
        created_at: new Date().toISOString()
      })
      await nextTick()
      scrollToBottom()
      if (voiceEnabled.value) speakText(reply)
    } catch {
      ElMessage.error('发送失败')
      messages.value = messages.value.filter(m => m.id !== userMsg.id)
    } finally {
      sending.value = false
    }
  } else {
    sending.value = true
    try {
      await sendMessage(authStore.user.id, {
        receiver_id: friendId,
        message_type: currentImage ? 'image' : 'text',
        content: currentContent || '[图片]',
        media_url: currentImage || null,  // ← currentImage 本身没问题
        // 但你要确保 currentImage 存的是 URL，而不是 Base64
      })
    } catch {
      ElMessage.error('发送失败')
      messages.value = messages.value.filter(m => m.id !== userMsg.id)
    } finally {
      sending.value = false
    }
  }
}

function speakText(text) {
  if (!window.speechSynthesis || !text) return
  const utterance = new SpeechSynthesisUtterance(text)
  utterance.lang = 'zh-CN'
  utterance.rate = 1.0
  window.speechSynthesis.speak(utterance)
}

function toggleVoice() {
  voiceEnabled.value = !voiceEnabled.value
  if (!voiceEnabled.value) {
    window.speechSynthesis?.cancel()
  }
  ElMessage.success(voiceEnabled.value ? '语音播报已开启' : '语音播报已关闭')
}

function toggleVoiceInput() {
  if (voiceInputActive.value) {
    stopVoiceInput()
  } else {
    startVoiceInput()
  }
}

function startVoiceInput() {
  if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
    ElMessage.warning('当前浏览器不支持语音输入')
    return
  }

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
  recognition.value = new SpeechRecognition()
  recognition.value.lang = 'zh-CN'
  recognition.value.continuous = false
  recognition.value.interimResults = false

  recognition.value.onresult = (event) => {
    const result = event.results[0][0].transcript
    inputContent.value = result
    voiceInputActive.value = false
    handleSendMessage()
  }

  recognition.value.onerror = () => {
    ElMessage.warning('语音识别失败，请重试')
    voiceInputActive.value = false
  }

  recognition.value.onend = () => {
    voiceInputActive.value = false
  }

  recognition.value.start()
  voiceInputActive.value = true
  ElMessage.info('请说话...')
}

function stopVoiceInput() {
  if (recognition.value) {
    recognition.value.stop()
  }
  voiceInputActive.value = false
}

onMounted(() => {
  loadPartnerInfo()
  loadMessages()
})
</script>

<style scoped>
.community-chat {
  display: flex;
  flex-direction: column;
  height: 100vh;
  max-height: 100vh;
  padding: 0 4px;
  position: relative;
  overflow: hidden;
}

.chat-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0 4px 0;
  flex-shrink: 0;
}
.back-btn {
  color: var(--text-secondary) !important;
  font-size: 18px;
  padding: 4px 8px;
}
.back-btn:hover {
  color: var(--text-primary) !important;
}
.chat-user {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  flex: 1;
  min-width: 0;
}
.chat-avatar {
  flex-shrink: 0;
}
.chat-user-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.chat-username {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.chat-status {
  font-size: 12px;
  color: var(--text-muted);
}
.chat-status.online {
  color: #22c55e;
}
.xiaoji-badge {
  font-size: 11px;
  font-weight: 500;
  background: rgba(64, 158, 255, 0.12);
  color: #409eff;
  padding: 0 10px;
  border-radius: 12px;
  line-height: 20px;
  margin-left: 4px;
  flex-shrink: 0;
}
.chat-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}
.action-btn {
  color: var(--text-muted) !important;
  font-size: 16px;
  padding: 4px 8px;
}
.action-btn:hover {
  color: var(--text-primary) !important;
}
.action-btn.active {
  color: #409eff !important;
}

.el-divider {
  margin: 4px 0;
  flex-shrink: 0;
}

.message-list-wrapper {
  flex: 1;
  overflow: hidden;
  position: relative;
  min-height: 0;
}
.message-list {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow-y: auto;
  padding: 8px 4px 120px 4px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.message-list::-webkit-scrollbar {
  width: 3px;
}
.message-list::-webkit-scrollbar-thumb {
  background: rgba(128, 128, 128, 0.2);
  border-radius: 2px;
}

.loading-state,
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  gap: 8px;
  min-height: 200px;
}
.loading-state i {
  font-size: 24px;
}
.loading-state span {
  font-size: 14px;
}
.empty-icon {
  font-size: 48px;
  color: var(--text-muted);
  opacity: 0.2;
}
.empty-title {
  font-size: 16px;
  color: var(--text-secondary);
  margin: 0;
}
.empty-desc {
  font-size: 13px;
  color: var(--text-muted);
  opacity: 0.6;
  margin: 0;
}

.message-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  max-width: 80%;
}
.message-item.sent {
  align-self: flex-end;
  flex-direction: row-reverse;
}
.message-item.sent .message-content-wrapper {
  align-items: flex-end;
}
.message-item.sent .message-avatar {
  display: none;
}

.message-avatar {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  overflow: hidden;
  margin-top: 2px;
}
.message-avatar :deep(.el-avatar) {
  width: 28px !important;
  height: 28px !important;
}

.message-content-wrapper {
  display: flex;
  flex-direction: column;
  gap: 2px;
  max-width: 100%;
}
.message-item.sent .message-content-wrapper {
  align-items: flex-end;
}

.message-bubble {
  padding: 10px 14px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.10);
  border: 1px solid rgba(255, 255, 255, 0.04);
  word-break: break-word;
}
.message-item.sent .message-bubble {
  background: rgba(64, 158, 255, 0.12);
  border-color: rgba(64, 158, 255, 0.10);
}
[data-theme="dark"] .message-bubble {
  background: rgba(255, 255, 255, 0.06);
}
[data-theme="dark"] .message-item.sent .message-bubble {
  background: rgba(64, 158, 255, 0.10);
}

.message-text {
  font-size: 14px;
  color: var(--text-primary);
  line-height: 1.6;
}

.message-time {
  font-size: 11px;
  color: var(--text-muted);
  padding: 0 4px;
  margin-top: 2px;
}

.message-image {
  max-width: 200px;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  border: 1px solid rgba(255, 255, 255, 0.06);
  transition: all 0.3s ease;
}
.message-image:hover {
  transform: scale(1.02);
}
.message-image img {
  width: 100%;
  height: auto;
  display: block;
  max-height: 200px;
  object-fit: cover;
}
.image-caption {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 6px 10px;
  background: rgba(0, 0, 0, 0.55);
  color: #fff;
  font-size: 12px;
  text-align: left;
}

/* ===== 题目卡片 ===== */
.message-card {
  padding: 12px 16px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  min-width: 180px;
}
.message-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0,0,0,0.06);
  border-color: rgba(64, 158, 255, 0.15);
}
.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}
.card-icon {
  font-size: 18px;
}
.card-title {
  font-weight: 600;
  font-size: 15px;
  flex: 1;
}
.card-badge {
  font-size: 11px;
  padding: 2px 10px;
  border-radius: 10px;
  background: rgba(64, 158, 255, 0.08);
  color: #409eff;
}
.card-body {
  margin: 4px 0;
}
.card-preview {
  font-size: 13px;
  color: var(--text-secondary);
  opacity: 0.7;
}
.card-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: 4px;
}
.card-hint {
  font-size: 11px;
  color: #409eff;
  opacity: 0.6;
}

/* ===== 输入区 ===== */
.chat-input-wrapper {
  position: fixed;
  bottom: 45px;
  left: 64px;
  right: 0;
  z-index: 100;
  padding: 12px 20px 16px 20px;
  background: rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.image-preview-thumb {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 0 8px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  margin-bottom: 8px;
}
.thumb-wrapper {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  border: 1px solid rgba(255, 255, 255, 0.08);
  flex-shrink: 0;
}
.thumb-wrapper img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.remove-image-btn {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  border: none;
  background: rgba(255, 255, 255, 0.08);
  color: var(--text-muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  transition: all 0.3s ease;
}
.remove-image-btn:hover {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

.chat-input-row {
  display: flex;
  gap: 8px;
  align-items: center;
}
.chat-tools {
  display: flex;
  gap: 2px;
  flex-shrink: 0;
}
.tool-btn {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  border: none;
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-muted);
  font-size: 15px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}
.tool-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: var(--text-primary);
}
.tool-btn.active {
  color: #409eff;
  background: rgba(64, 158, 255, 0.10);
}

.chat-input-field {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 2px 4px 2px 14px;
  transition: all 0.3s ease;
  backdrop-filter: blur(8px);
}
.chat-input-field:focus-within {
  border-color: rgba(64, 158, 255, 0.35);
  box-shadow: 0 0 0 4px rgba(64, 158, 255, 0.06);
}

.input-field {
  flex: 1;
  border: none;
  background: transparent;
  color: var(--text-primary);
  font-size: 14px;
  outline: none;
  padding: 8px 0;
  min-height: 38px;
}
.input-field::placeholder {
  color: var(--text-muted);
}

.send-btn {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  border: none;
  background: rgba(64, 158, 255, 0.10);
  color: #409eff;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.send-btn:hover:not(:disabled) {
  background: rgba(64, 158, 255, 0.20);
  transform: scale(1.05);
}
.send-btn:active:not(:disabled) {
  transform: scale(0.95);
}
.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ===== 弹窗 ===== */
.custom-glass-dialog :deep(.el-dialog) {
  background: rgba(255, 255, 255, 0.04) !important;
  backdrop-filter: blur(24px) !important;
  -webkit-backdrop-filter: blur(24px) !important;
  border: 1px solid rgba(255, 255, 255, 0.06) !important;
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
  color: var(--text-primary);
}
.q-type {
  font-size: 12px;
  color: var(--text-muted);
  margin: 0 12px;
}

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
  color: var(--text-primary);
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

.preview-content {
  max-height: 400px;
  overflow-y: auto;
}
.preview-set p {
  margin: 6px 0;
  font-size: 14px;
  color: var(--text-secondary);
}
.preview-set p strong {
  color: var(--text-primary);
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

@media (max-width: 640px) {
  .community-chat {
    height: 100vh;
    max-height: 100vh;
    padding: 0 2px;
  }
  .chat-username {
    font-size: 14px;
  }
  .message-bubble {
    padding: 8px 12px;
  }
  .message-text {
    font-size: 13px;
  }
  .message-image {
    max-width: 140px;
  }
  .chat-input-row {
    gap: 6px;
  }
  .tool-btn {
    width: 32px;
    height: 32px;
    font-size: 14px;
  }
  .chat-input-field {
    padding: 2px 2px 2px 10px;
  }
  .input-field {
    font-size: 13px;
    padding: 6px 0;
    min-height: 34px;
  }
  .send-btn {
    width: 32px;
    height: 32px;
    font-size: 13px;
  }
  .thumb-wrapper {
    width: 40px;
    height: 40px;
  }
  .message-card {
    min-width: 140px;
    padding: 8px 12px;
  }
  .question-dialog {
    max-height: 320px;
  }
  .custom-glass-dialog :deep(.el-dialog) {
    width: 92% !important;
    margin: 0 auto !important;
  }
}
</style>