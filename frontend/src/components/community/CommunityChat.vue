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
          <p class="empty-title">{{ isXiaoji ? '开始和小基聊天' : '暂无消息' }}</p >
          <p class="empty-desc">{{ isXiaoji ? '小基是一个温暖的学习伙伴，随时陪你聊天' : '开始你们的对话吧' }}</p >
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
            <div v-if="msg.image_url" class="message-image" @click="previewImage(msg.image_url)">
              <img :src="msg.image_url" alt="图片" />
              <span v-if="msg.content && msg.content !== '[图片]'" class="image-caption">{{ msg.content }}</span>
            </div>
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
          <button class="tool-btn" @click="showShareMenu = !showShareMenu">
            <i class="fas fa-share-alt"></i>
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

    <div v-if="showShareMenu" class="share-menu" @click.stop>
      <div class="share-options">
        <button class="share-option" @click="shareQuestion">
          <i class="fas fa-pen"></i> 分享题目
        </button>
        <button class="share-option" @click="shareSet">
          <i class="fas fa-folder"></i> 分享题集
        </button>
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
  getFriends  // 新增
} from '@/api/community'

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
      // 如果好友列表里没有，可能是还没刷新，用默认值
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

const messages = ref([])
const inputContent = ref('')
const loading = ref(false)
const sending = ref(false)
const voiceInputActive = ref(false)
const voiceEnabled = ref(true)
const showShareMenu = ref(false)
const fileInputRef = ref(null)
const messageListRef = ref(null)
const uploadedImage = ref(null)
const imagePreviewVisible = ref(false)
const previewImageUrl = ref('')
const recognition = ref(null)

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

function formatTime(time) {
  if (!time) return ''
  // 如果字符串没有 Z，手动加上 Z 强制按 UTC 解析
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

function scrollToBottom() {
  const el = document.getElementById('messageList')
  if (el) {
    el.scrollTop = el.scrollHeight
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

async function handleSendMessage() {
  const content = inputContent.value.trim()
  const image = uploadedImage.value

  if (!content && !image) {
    ElMessage.warning('请输入内容或选择图片')
    return
  }

  const currentContent = content
  const currentImage = image

  // 显示用户消息
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
    // ===== 小基聊天 =====
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
    // ===== 真人好友聊天 =====
    sending.value = true
    try {
      const res = await sendMessage(authStore.user.id, {
      receiver_id: friendId,
  message_type: currentImage ? 'image' : 'text',
  content: currentContent || '[图片]',
  media_url: currentImage || null
})
      // 真人消息后端会存，不需要前端再 push
      // 但为了显示，可以保持 userMsg 已经在列表里
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

function shareQuestion() {
  showShareMenu.value = false
  ElMessage.info('分享题目功能开发中')
}

function shareSet() {
  showShareMenu.value = false
  ElMessage.info('分享题集功能开发中')
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

/* ===== 输入区（上提 + 毛玻璃） ===== */
.chat-input-wrapper {
    position: fixed;
    bottom: 45px;
    left: 64px;
    right: 0;
    z-index: 100;
    padding: 12px 20px 16px 20px;   /* 👈 左右加 padding */
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

.share-menu {
  position: absolute;
  bottom: 90px;
  left: 16px;
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 6px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  z-index: 20;
}
.share-options {
  display: flex;
  gap: 4px;
}
.share-option {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  border-radius: 8px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.3s ease;
}
.share-option:hover {
  background: rgba(255, 255, 255, 0.06);
  color: var(--text-primary);
}
.share-option i {
  font-size: 14px;
}

.image-preview-dialog :deep(.el-dialog) {
  background: rgba(0, 0, 0, 0.8) !important;
  backdrop-filter: blur(12px) !important;
  border: none !important;
  border-radius: 12px !important;
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
  .share-menu {
    bottom: 84px;
    left: 10px;
  }
}
</style>