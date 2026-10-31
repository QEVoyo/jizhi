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
          <span
            class="chat-status"
            :class="{ online: chatPartner?.status === 'online' || (chatConnected && !isXiaoji) }"
          >
            {{ chatPartner?.status === 'online' ? '在线' : '离线' }}
            <template v-if="chatConnected && !isXiaoji"> · 实时</template>
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
            <!-- 表情包（GIF 走 public/stickers，不落库文件本身，只存路径） -->
            <div
              v-if="isSticker(msg)"
              class="message-sticker"
              @click="previewImage(messageImage(msg))"
            >
              <img :src="messageImage(msg)" alt="表情" loading="lazy" decoding="async" />
            </div>
            <!-- 图片：2026-10-30 起落库字段是 media_url，旧的 image_url 仅作兼容 -->
            <div v-else-if="messageImage(msg)" class="message-image" @click="previewImage(messageImage(msg))">
              <img :src="messageImage(msg)" alt="图片" loading="lazy" decoding="async" @error="onImageError" />
              <span v-if="imageCaption(msg)" class="image-caption">{{ imageCaption(msg) }}</span>
            </div>
            <!-- 题集卡片 -->
            <div v-else-if="msg.question_set_id" class="message-card set-card" @click="openSetCard(msg)">
              <div class="card-header">
                <span class="card-icon">📚</span>
                <span class="card-title">{{ setInfo(msg).name }}</span>
                <span class="card-badge">题集</span>
              </div>
              <div class="card-body">
                <span class="card-preview">{{ setInfo(msg).summary }}</span>
              </div>
              <div class="card-footer">
                <span class="card-hint">点击查看题集 →</span>
              </div>
            </div>
            <!-- 题目卡片：优先读 question_data（后端私有消息已带 jsonb） -->
            <div v-else-if="msg.question_id" class="message-card question-card" @click="goDoQuestion(msg)">
              <div class="card-header">
                <span class="card-icon">📝</span>
                <span class="card-title">{{ questionTitle(msg) }}</span>
                <span class="card-badge">{{ questionTypeName(msg) }}</span>
              </div>
              <div class="card-body">
                <span class="card-preview">{{ questionPreview(msg) }}</span>
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
                <div class="set-actions" @click.stop>
                  <el-button size="small" text @click="openSetPreview(s)">预览</el-button>
                  <el-button size="small" type="primary" @click="sendQuestionSet(s)">发送题集</el-button>
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
          <p><strong>题目数量：</strong>{{ previewSetQuestions.length || previewSetData?.question_ids?.length || 0 }}</p>
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
        <div class="thumb-wrapper" :class="{ uploading: uploadingImage }" @click="!uploadingImage && previewImage(uploadedImage)">
          <img :src="uploadedImage" alt="待发送图片" />
          <span v-if="uploadingImage" class="thumb-uploading">
            <i class="fas fa-spinner fa-spin"></i>
          </span>
        </div>
        <span v-if="uploadingImage" class="thumb-hint">上传中…</span>
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
          <el-popover
            v-if="!isXiaoji"
            v-model:visible="showStickerPanel"
            placement="top-start"
            :width="336"
            :popper-style="{ padding: '10px' }"
            :show-arrow="false"
            trigger="click"
            popper-class="sticker-popper"
          >
            <template #reference>
              <button class="tool-btn" :class="{ active: showStickerPanel }" title="表情包">
                <i class="fas fa-face-smile"></i>
              </button>
            </template>
            <div class="sticker-popup">
              <div class="sticker-panel-head">
                <button
                  class="sticker-tab"
                  :class="{ active: stickerTab === 'anim' }"
                  @click="stickerTab = 'anim'"
                >动态</button>
                <button
                  class="sticker-tab"
                  :class="{ active: stickerTab === 'static' }"
                  @click="stickerTab = 'static'"
                >静态</button>
                <span class="sticker-count">{{ stickerGroups[stickerTab].length }}</span>
              </div>
              <div class="sticker-panel-grid">
                <button
                  v-for="s in stickerGroups[stickerTab]"
                  :key="s.src"
                  class="sticker-cell"
                  :title="s.label"
                  @click="sendSticker(s)"
                >
                  <img :src="s.src" :alt="s.label" loading="lazy" />
                </button>
              </div>
            </div>
          </el-popover>
          <button v-if="!isXiaoji" class="tool-btn" @click="openSendQuestion">
            <i class="fas fa-paper-plane"></i>
          </button>
          <input ref="fileInputRef" type="file" accept="image/*" style="display: none" @change="handleImageSelect" />
        </div>

        <div class="chat-input-field">
          <input
            v-model="inputContent"
            :placeholder="isXiaoji ? '给小基发消息...' : '输入消息...'"
            class="input-field"
            @focus="showStickerPanel = false"
            @keyup.enter="handleSendMessage"
          />
          <button class="send-btn" :disabled="sending || uploadingImage" @click="handleSendMessage">
            <i v-if="!sending" class="fas fa-paper-plane"></i>
            <i v-else class="fas fa-spinner fa-spin"></i>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import {
  getMessages,
  sendMessage,
  xiaojiVision,
  getXiaojiMessages,
  getFriends,
  markPrivateRead
} from '@/api/community'
import { BACKEND_URL } from '@/utils/constants'
import { getGenerationHistory, getQuestionSets, getQuestionDetail } from '@/api/questions'
import { uploadImage } from '@/api/upload'
import { useLiveAsr } from '@/composables/useLiveAsr'
import { useChatSocket } from '@/composables/useChatSocket'
import stickerManifest from '@/xiaoji/stickerManifest.json'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const friendId = route.params.friendId
const isXiaoji = computed(() => friendId === 'xiaoji')

// 社区表情包：清单由 _devtools/xiaoji_anim/make_transparent_assets.py 生成
const stickerGroups = stickerManifest

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
const voiceEnabled = ref(true)
const fileInputRef = ref(null)
const messageListRef = ref(null)
const uploadedImage = ref(null)      // 本地预览（blob: URL），发送前就被 uploadImage 换成公网地址
const uploadedImageUrl = ref(null)   // Supabase Storage 公共地址，真正落库的是它
const uploadingImage = ref(false)
const showStickerPanel = ref(false)
const stickerTab = ref('anim')
const imagePreviewVisible = ref(false)
const previewImageUrl = ref('')

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

// ===== 语音输入（同 XiaojiCall：16k PCM → /xiaoji/asr-ws，逐字回填） =====
const {
  isRecording: voiceInputActive,
  start: startVoiceInput,
  stop: stopVoiceInput,
} = useLiveAsr({
  getBaseText: () => inputContent.value.trim(),
  onText: (text) => { inputContent.value = text },
  onError: (msg) => ElMessage.warning(msg),
})

// ===== 私聊实时推送（一个聊天框一条连接，只订阅当前好友）=====
let readMarkTimer = null
function scheduleMarkRead() {
  if (readMarkTimer) clearTimeout(readMarkTimer)
  readMarkTimer = setTimeout(() => {
    readMarkTimer = null
    markPrivateRead(authStore.user.id, friendId).catch(() => {})
  }, 300)
}

const { connected: chatConnected } = useChatSocket({
  peerId: isXiaoji.value ? '' : String(friendId),
  enabled: !isXiaoji.value,
  onMessage: (msg) => {
    if (!msg || msg.sender_id !== friendId) return
    if (msg.id && messages.value.some(m => m.id === msg.id)) return
    const stick = isNearBottom()
    messages.value.push(msg)
    if (stick) nextTick(scrollToBottom)
    // 聊天框正开着，收到就算已读（连续来消息时合并成一次请求）
    scheduleMarkRead()
  },
  // 断线重连成功后补拉一次，把断线期间的消息补齐
  onReconnect: () => loadMessages(),
})

function isNearBottom() {
  const el = document.getElementById('messageList')
  if (!el) return true
  return el.scrollHeight - el.scrollTop - el.clientHeight < 80
}

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

// ===== 富消息：字段归一化（私有消息的 question_data 是 jsonb，老数据可能是字符串） =====
function parseMaybeJson(v) {
  if (!v) return null
  if (typeof v === 'object') return v
  try { return JSON.parse(v) } catch { return null }
}

function questionData(msg) {
  return parseMaybeJson(msg.question_data)
}

function questionTitle(msg) {
  const qd = questionData(msg)
  return qd?.title || msg.question_title || (msg.question_content || '').slice(0, 30) || '题目'
}

function questionTypeName(msg) {
  const qd = questionData(msg)
  return getTypeName(qd?.question_type || msg.question_type)
}

function questionPreview(msg) {
  const qd = questionData(msg)
  return qd?.question_content || msg.question_content || questionTitle(msg)
}

function messageImage(msg) {
  return msg.media_url || msg.image_url || ''
}

function isSticker(msg) {
  // message_type 可能被库里的约束/旧数据抹成 image，路径也认一遍
  return msg.message_type === 'sticker' ||
    /^\/stickers\/(anim|static)\/.+\.(gif|png|webp)$/i.test(messageImage(msg))
}

function imageCaption(msg) {
  if (!msg.content || msg.content === '[图片]' || msg.content === '[表情]') return ''
  return msg.content
}

function onImageError(e) {
  e.target.src = '/images/placeholder.png'
  e.target.onerror = null
}

function setInfo(msg) {
  const d = questionData(msg) || {}
  const ids = Array.isArray(d.question_ids) ? d.question_ids : []
  const questions = Array.isArray(d.questions) ? d.questions : []
  const n = ids.length || questions.length
  return {
    name: d.name || msg.question_set_name || '题集',
    summary: d.description || (n ? `${n} 道题` : '点击查看题集'),
    question_ids: ids,
    questions,
  }
}

function goBack() {
  router.push('/community/friends')
}

function goUserProfile() {
  if (isXiaoji.value) {
    router.push('/xiaoji/settings')
    return
  }
  router.push(`/community/user/${friendId}`)
}

function goSettings() {
  router.push('/xiaoji/settings')
}

function goCall() {
  router.push('/home')
}

function goDoQuestion(msg) {
  // 如果消息里带了完整的题目数据，通过 URL 参数传递
  const qd = questionData(msg)
  if (qd) {
    const encoded = encodeURIComponent(JSON.stringify(qd))
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
  if (uploadedImage.value?.startsWith('blob:')) {
    URL.revokeObjectURL(uploadedImage.value)
  }
  uploadedImage.value = null
  uploadedImageUrl.value = null
  uploadingImage.value = false
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
}

function triggerImageUpload() {
  fileInputRef.value?.click()
}

// 选图即上传：本地只留 objectURL 预览，落库和发送用的都是 Supabase 公共地址。
// 之前存 base64 直接进 media_url，一条图就是几百 KB 的 JSON，列表一拉就卡。
async function handleImageSelect(event) {
  const file = event.target.files?.[0]
  event.target.value = ''
  if (!file) return
  if (!file.type.startsWith('image/')) {
    ElMessage.warning('请选择图片文件')
    return
  }
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.warning('图片不能超过 10MB')
    return
  }

  removeImage()
  uploadedImage.value = URL.createObjectURL(file)
  uploadingImage.value = true
  try {
    uploadedImageUrl.value = await uploadImage(file)
  } catch (e) {
    console.error('图片上传失败:', e)
    ElMessage.error('图片上传失败，请重试')
    removeImage()
  } finally {
    uploadingImage.value = false
  }
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

async function loadQuestionsForSet(setId, ids) {
  if (setQuestionsMap.value[setId] !== undefined && setQuestionsMap.value[setId] !== null) {
    return setQuestionsMap.value[setId]
  }
  setQuestionsMap.value[setId] = null
  const qs = []
  for (const id of ids || []) {
    try {
      const q = await getQuestionDetail(id)
      if (q) qs.push(q)
    } catch (e) {}
  }
  setQuestionsMap.value[setId] = qs
  return qs
}

async function toggleSetExpand(setId) {
  if (expandedSetId.value === setId) {
    expandedSetId.value = null
    return
  }
  expandedSetId.value = setId
  const s = questionSets.value.find(item => item.id === setId)
  await loadQuestionsForSet(setId, s?.question_ids || [])
}

// ===== 题集预览 / 发送题集 =====
function openSetPreview(s) {
  previewSetData.value = s
  previewSetQuestions.value = setQuestionsMap.value[s.id] || []
  showPreviewDialog.value = true
  if (setQuestionsMap.value[s.id] === undefined) {
    loadQuestionsForSet(s.id, s.question_ids || []).then(qs => {
      if (previewSetData.value?.id === s.id) previewSetQuestions.value = qs
    })
  }
}

async function openSetCard(msg) {
  const info = setInfo(msg)
  const d = questionData(msg) || {}
  previewSetData.value = {
    id: msg.question_set_id,
    name: info.name,
    description: d.description || '',
    question_ids: info.question_ids,
  }
  previewSetQuestions.value = info.questions
  showPreviewDialog.value = true
  if (!info.questions.length && info.question_ids.length) {
    const qs = await loadQuestionsForSet(msg.question_set_id, info.question_ids)
    if (previewSetData.value?.id === msg.question_set_id) previewSetQuestions.value = qs
  }
}

async function sendQuestionSet(s) {
  showQuestionDialog.value = false
  expandedSetId.value = null

  const loaded = setQuestionsMap.value[s.id] || []
  const snapshot = {
    kind: 'question_set',
    id: s.id,
    name: s.name,
    description: s.description || '',
    question_ids: s.question_ids || [],
    questions: loaded.map(q => ({
      id: q.id,
      title: q.title || q.question_content || '未命名题目',
      question_type: q.question_type || 'choice',
    })),
  }
  const content = `📚 题集《${s.name}》`

  const userMsg = {
    id: Date.now().toString(),
    sender_id: authStore.user.id,
    content,
    message_type: 'set',
    question_set_id: s.id,
    question_data: snapshot,
    created_at: new Date().toISOString(),
  }
  messages.value.push(userMsg)
  await nextTick()
  scrollToBottom()

  sending.value = true
  try {
    await sendMessage(authStore.user.id, {
      receiver_id: friendId,
      message_type: 'set',
      content,
      question_set_id: s.id,
      question_data: snapshot,
    })
  } catch {
    ElMessage.error('发送失败')
    messages.value = messages.value.filter(m => m.id !== userMsg.id)
  } finally {
    sending.value = false
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

// ===== 表情包 =====
async function sendSticker(sticker) {
  if (sending.value) return
  showStickerPanel.value = false

  const userMsg = {
    id: Date.now().toString(),
    sender_id: authStore.user.id,
    content: '[表情]',
    message_type: 'sticker',
    media_url: sticker.src,
    created_at: new Date().toISOString()
  }
  messages.value.push(userMsg)
  await nextTick()
  scrollToBottom()

  sending.value = true
  try {
    await sendMessage(authStore.user.id, {
      receiver_id: friendId,
      message_type: 'sticker',
      content: '[表情]',
      media_url: sticker.src,
    })
  } catch {
    ElMessage.error('发送失败')
    messages.value = messages.value.filter(m => m.id !== userMsg.id)
  } finally {
    sending.value = false
  }
}

// ===== 小基文字聊天：流式收字 + 50ms 批量刷 UI =====
// 后端按块吐字；如果每个 chunk 都写一次响应式 content，Vue 会被重绘打爆。
// force_chat=true 是因为社区聊天框没有「派活卡片」，固定走闲聊链路。
async function streamXiaojiReply(text) {
  const response = await fetch(
    `${BACKEND_URL}/community/xiaoji/chat-stream?user_id=${encodeURIComponent(authStore.user.id)}`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authStore.token}`,
      },
      body: JSON.stringify({ content: text, force_chat: true }),
    }
  )
  if (!response.ok) {
    const err = await response.json().catch(() => null)
    throw new Error(err?.detail || `HTTP ${response.status}`)
  }

  const replyMsg = {
    id: `local-${Date.now()}-xiaoji`,
    sender_id: 'xiaoji',
    content: '',
    created_at: new Date().toISOString(),
  }
  messages.value.push(replyMsg)
  await nextTick()
  scrollToBottom()

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let full = ''
  let flushTimer = null
  let lastFlush = 0

  const flush = () => {
    flushTimer = null
    if (replyMsg.content === full) return
    replyMsg.content = full
    lastFlush = performance.now()
    nextTick(scrollToBottom)
  }
  const scheduleFlush = () => {
    if (flushTimer) return
    const wait = Math.max(0, 50 - (performance.now() - lastFlush))
    flushTimer = setTimeout(flush, wait)
  }

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    full += decoder.decode(value, { stream: true })
    scheduleFlush()
  }
  if (flushTimer) { clearTimeout(flushTimer); flushTimer = null }
  flush()

  if (!full.trim()) {
    messages.value = messages.value.filter(m => m !== replyMsg)
    throw new Error('空回复')
  }
  return full
}

// ===== 发送消息 =====
async function handleSendMessage() {
  const content = inputContent.value.trim()
  const imagePreview = uploadedImage.value
  const imageUrl = uploadedImageUrl.value

  if (!content && !imagePreview) {
    ElMessage.warning('请输入内容或选择图片')
    return
  }
  // 选图即上传：没拿到公网地址就不让发，避免又把 base64 塞进 media_url
  if (imagePreview && !imageUrl) {
    ElMessage.warning(uploadingImage.value ? '图片还在上传，稍等一下' : '图片上传失败，请重新选择')
    return
  }
  if (voiceInputActive.value) stopVoiceInput()

  const currentContent = content
  const currentImage = imageUrl

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
    message_type: currentImage ? 'image' : 'text',
    media_url: currentImage || null,
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
      const reply = await streamXiaojiReply(currentContent)
      if (voiceEnabled.value) speakText(reply)
    } catch (e) {
      console.error('小基流式回复失败:', e)
      ElMessage.error(e?.message || '发送失败')
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
        media_url: currentImage || null,
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
    ElMessage.info('请说话，说完自动结束（再点一次可提前结束）')
  }
}

onMounted(() => {
  loadPartnerInfo()
  loadMessages()
})

onUnmounted(() => {
  if (readMarkTimer) { clearTimeout(readMarkTimer); readMarkTimer = null }
  if (voiceInputActive.value) stopVoiceInput()
  if (uploadedImage.value?.startsWith('blob:')) {
    URL.revokeObjectURL(uploadedImage.value)
  }
})
</script>

<style scoped>
.community-chat {
  display: flex;
  flex-direction: column;
  height: calc(100vh - var(--jz-top, 0px));
  max-height: calc(100vh - var(--jz-top, 0px));
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
  color: color-mix(in srgb, #22c55e 65%, var(--text-primary));
}
.xiaoji-badge {
  font-size: 11px;
  font-weight: 500;
  background: color-mix(in srgb, var(--brand) 12%, transparent);
  color: var(--brand);
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
  color: var(--brand) !important;
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
  background: color-mix(in srgb, var(--surface, #ffffff) 10%, transparent);
  border: 1px solid rgba(255, 255, 255, 0.04);
  word-break: break-word;
}
.message-item.sent .message-bubble {
  background: color-mix(in srgb, var(--brand) 12%, transparent);
  border-color: color-mix(in srgb, var(--brand) 10%, transparent);
}
[data-theme="dark"] .message-bubble {
  background: color-mix(in srgb, var(--surface, #ffffff) 6%, transparent);
}
[data-theme="dark"] .message-item.sent .message-bubble {
  background: color-mix(in srgb, var(--brand) 10%, transparent);
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

/* 表情包：只走 public/stickers，消息里存路径 */
.message-sticker {
  cursor: pointer;
  line-height: 0;
}
.message-sticker img {
  width: 96px;
  height: 96px;
  object-fit: contain;
  display: block;
}
.message-item.sent .message-sticker img {
  margin-left: auto;
}

/* 表情包小弹窗：锚定在表情按钮上方，浮层盖在消息上，不挤压聊天区 */
.sticker-popup {
  width: 316px;
}
.sticker-panel-head {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 6px;
}
.sticker-tab {
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-size: 13px;
  padding: 3px 10px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}
.sticker-tab:hover {
  color: var(--text-primary);
}
.sticker-tab.active {
  background: color-mix(in srgb, var(--brand) 12%, transparent);
  color: var(--brand);
  font-weight: 600;
}
.sticker-count {
  font-size: 11px;
  color: var(--text-muted);
  margin-left: 2px;
}
.sticker-panel-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 4px;
  max-height: 224px;
  overflow-y: auto;
  padding-right: 2px;
}
.sticker-panel-grid::-webkit-scrollbar {
  width: 3px;
}
.sticker-panel-grid::-webkit-scrollbar-thumb {
  background: rgba(128, 128, 128, 0.2);
  border-radius: 2px;
}

/* popover 内容被 teleport 到 body，样式要提成全局的 */
:global(.sticker-popper.el-popover) {
  background: var(--surface, #ffffff) !important;
  border: 1px solid rgba(128, 128, 128, 0.14) !important;
  border-radius: 14px !important;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.14) !important;
  max-width: calc(100vw - 24px);
}
.sticker-cell {
  border: none;
  background: transparent;
  border-radius: 12px;
  padding: 6px;
  cursor: pointer;
  transition: background 0.2s ease, transform 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}
.sticker-cell:hover {
  background: color-mix(in srgb, var(--brand) 8%, transparent);
  transform: translateY(-1px);
}
.sticker-cell img {
  width: 100%;
  aspect-ratio: 1;
  object-fit: contain;
}

/* ===== 题目卡片 ===== */
.message-card {
  padding: 12px 16px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  min-width: 180px;
}
.message-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0,0,0,0.06);
  border-color: color-mix(in srgb, var(--brand) 15%, transparent);
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
  background: color-mix(in srgb, var(--brand) 8%, transparent);
  color: var(--brand);
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
  color: var(--brand);
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
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent);
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
  position: relative;
  width: 48px;
  height: 48px;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  border: 1px solid var(--line-soft);
  flex-shrink: 0;
}
.thumb-wrapper img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.thumb-wrapper.uploading {
  cursor: progress;
}
.thumb-uploading {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.45);
  color: #fff;
  font-size: 14px;
}
.thumb-hint {
  font-size: 12px;
  color: var(--text-muted);
}
.remove-image-btn {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  border: none;
  background: color-mix(in srgb, var(--surface, #ffffff) 8%, transparent);
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
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent);
  color: var(--text-muted);
  font-size: 15px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}
.tool-btn:hover {
  background: color-mix(in srgb, var(--surface, #ffffff) 8%, transparent);
  color: var(--text-primary);
}
.tool-btn.active {
  color: var(--brand);
  background: color-mix(in srgb, var(--brand) 10%, transparent);
}

.chat-input-field {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent);
  border: 1px solid var(--line-soft);
  border-radius: 12px;
  padding: 2px 4px 2px 14px;
  transition: all 0.3s ease;
  backdrop-filter: blur(8px);
}
.chat-input-field:focus-within {
  border-color: color-mix(in srgb, var(--brand) 35%, transparent);
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--brand) 6%, transparent);
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
  background: color-mix(in srgb, var(--brand) 10%, transparent);
  color: var(--brand);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.send-btn:hover:not(:disabled) {
  background: color-mix(in srgb, var(--brand) 20%, transparent);
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
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent) !important;
  backdrop-filter: blur(24px) !important;
  -webkit-backdrop-filter: blur(24px) !important;
  border: 1px solid rgba(255, 255, 255, 0.06) !important;
  border-radius: 20px !important;
  box-shadow: 0 8px 40px rgba(0,0,0,0.08) !important;
}
[data-theme="dark"] .custom-glass-dialog :deep(.el-dialog) {
  background: var(--well) !important;
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
  background: var(--brand) !important;
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
  background: color-mix(in srgb, var(--surface, #ffffff) 2%, transparent);
}
.question-item:hover {
  background: color-mix(in srgb, var(--brand) 4%, transparent);
  border-color: color-mix(in srgb, var(--brand) 12%, transparent);
}
.q-title {
  flex: 1;
  font-size: 14px;
  color: var(--brand);
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
  background: color-mix(in srgb, var(--surface, #ffffff) 2%, transparent);
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
  color: var(--brand);
}
.set-count {
  font-size: 12px;
  color: var(--brand);
}
.set-expand-icon {
  transition: transform 0.3s ease;
  color: var(--brand);
  font-size: 14px;
}
.set-expand-icon.expanded {
  transform: rotate(180deg);
}
.set-actions {
  display: flex;
  align-items: center;
  gap: 2px;
  flex-shrink: 0;
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
  background: color-mix(in srgb, var(--brand) 4%, transparent);
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
  color: var(--brand);
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
    height: calc(100vh - var(--jz-top, 0px));
    max-height: calc(100vh - var(--jz-top, 0px));
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
  .message-sticker img {
    width: 84px;
    height: 84px;
  }
  .sticker-panel-grid {
    max-height: 200px;
    gap: 3px;
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