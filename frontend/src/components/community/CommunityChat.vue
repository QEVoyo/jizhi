<template>
  <div class="community-chat">
    <div class="chat-header">
      <el-button text class="back-btn" @click="goBack">
        <i class="fas fa-arrow-left"></i>
      </el-button>
      <div class="chat-user" @click="goUserProfile(friendId)">
        <el-avatar :size="36" :src="friend?.avatar_url || ''" class="chat-avatar">
          {{ friend?.nickname?.[0] || 'U' }}
        </el-avatar>
        <span class="chat-username">{{ friend?.nickname || '用户' }}</span>
        <span class="chat-status" :class="{ online: friend?.status === 'online' }">
          {{ friend?.status === 'online' ? '在线' : '离线' }}
        </span>
      </div>
    </div>

    <el-divider />

    <div class="message-list" ref="messageListRef">
      <div v-if="loading" class="loading-state">
        <i class="fas fa-spinner fa-spin"></i> 加载中...
      </div>
      <div v-else-if="!messages.length" class="empty-state">
        <i class="fas fa-comment-dots" style="font-size: 48px; opacity: 0.3;"></i>
        <p>暂无消息</p >
        <span>开始聊天吧！</span>
      </div>
      <div
        v-for="msg in messages"
        :key="msg.id"
        class="message-item"
        :class="{ sent: msg.sender_id === authStore.user.id }"
      >
        <div class="message-bubble">
          <span class="message-content">{{ msg.content }}</span>
          <span class="message-time">{{ formatTime(msg.created_at) }}</span>
        </div>
      </div>
    </div>

    <div class="chat-input-wrapper">
      <div class="chat-tools">
        <el-button text class="tool-btn" @click="showShareMenu = !showShareMenu">
          <i class="fas fa-share-alt"></i>
        </el-button>
        <el-button text class="tool-btn" @click="selectImage">
          <i class="fas fa-image"></i>
        </el-button>
        <input
          ref="fileInputRef"
          type="file"
          accept="image/*"
          style="display: none"
          @change="handleImageSelect"
        />
      </div>
      <div class="chat-input">
        <el-input
          v-model="inputContent"
          placeholder="输入消息..."
          size="large"
          @keyup.enter="handleSendMessage"
        />
        <el-button type="primary" :loading="sending" @click="handleSendMessage">
          <i class="fas fa-paper-plane"></i>
        </el-button>
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
import { ref, onMounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import { getMessages, sendMessage } from '@/api/community'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const friendId = route.params.friendId
const friend = ref(null)
const messages = ref([])
const inputContent = ref('')
const loading = ref(false)
const sending = ref(false)
const showShareMenu = ref(false)
const fileInputRef = ref(null)
const messageListRef = ref(null)

function goBack() {
  router.push('/community/friends')
}

function goUserProfile(userId) {
  router.push(`/community/user/${userId}`)
}

function formatTime(time) {
  if (!time) return ''
  const t = new Date(time)
  return t.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

async function loadMessages() {
  loading.value = true
  try {
    const res = await getMessages(authStore.user.id, friendId)
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
  if (messageListRef.value) {
    messageListRef.value.scrollTop = messageListRef.value.scrollHeight
  }
}

async function handleSendMessage() {
  if (!inputContent.value.trim()) {
    ElMessage.warning('请输入内容')
    return
  }
  sending.value = true
  try {
    await sendMessage({
      sender_id: authStore.user.id,
      receiver_id: friendId,
      message_type: 'text',
      content: inputContent.value
    })
    inputContent.value = ''
    await loadMessages()
  } catch {
    ElMessage.error('发送失败')
  } finally {
    sending.value = false
  }
}

function selectImage() {
  fileInputRef.value?.click()
}

function handleImageSelect(event) {
  const file = event.target.files[0]
  if (file) {
    ElMessage.info('图片上传功能开发中')
  }
  event.target.value = ''
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
  loadMessages()
})
</script>

<style scoped>
.community-chat {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 0 4px;
}

.chat-header {
  display: flex;
  align-items: center;
  gap: 12px;
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
  gap: 8px;
  cursor: pointer;
}
.chat-avatar {
  flex-shrink: 0;
}
.chat-username {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}
.chat-status {
  font-size: 12px;
  color: var(--text-muted);
}
.chat-status.online {
  color: #22c55e;
}

.el-divider {
  margin: 8px 0;
}

.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 400px;
}
.message-list::-webkit-scrollbar {
  width: 3px;
}
.message-list::-webkit-scrollbar-thumb {
  background: rgba(128, 128, 128, 0.2);
  border-radius: 2px;
}

.message-item {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}
.message-item.sent {
  align-items: flex-end;
}
.message-bubble {
  max-width: 70%;
  padding: 10px 14px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.06);
}
.message-item.sent .message-bubble {
  background: rgba(64, 158, 255, 0.12);
  border-color: rgba(64, 158, 255, 0.15);
}
.message-content {
  font-size: 14px;
  color: var(--text-primary);
  word-break: break-word;
}
.message-time {
  font-size: 11px;
  color: var(--text-muted);
  margin-left: 8px;
}

.loading-state,
.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: var(--text-muted);
}
.empty-state p {
  font-size: 16px;
  color: var(--text-secondary);
  margin: 4px 0;
}
.empty-state span {
  font-size: 14px;
  opacity: 0.6;
}

.chat-input-wrapper {
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  padding-top: 10px;
}
.chat-tools {
  display: flex;
  gap: 4px;
  margin-bottom: 6px;
}
.tool-btn {
  color: var(--text-muted) !important;
  font-size: 16px;
  padding: 4px 8px;
}
.tool-btn:hover {
  color: var(--text-primary) !important;
}
.chat-input {
  display: flex;
  gap: 8px;
}
.chat-input :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.04) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  border-radius: 12px !important;
}
.chat-input .el-button {
  border-radius: 12px !important;
  padding: 0 20px !important;
  background: rgba(64, 158, 255, 0.10) !important;
  border: 1px solid rgba(64, 158, 255, 0.15) !important;
  color: #409eff !important;
}
.chat-input .el-button:hover {
  background: rgba(64, 158, 255, 0.20) !important;
}

.share-menu {
  position: absolute;
  bottom: 80px;
  left: 20px;
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 8px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
}
.share-options {
  display: flex;
  gap: 6px;
}
.share-option {
  display: flex;
  align-items: center;
  gap: 6px;
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
</style>