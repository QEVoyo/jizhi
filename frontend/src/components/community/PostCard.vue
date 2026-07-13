<template>
  <div class="post-card">
    <!-- ===== 用户信息 ===== -->
    <div class="post-header">
      <div class="post-user" @click.stop="emit('user-click', post.user_id)">
        <el-avatar :size="40" :src="post.profiles?.avatar_url || ''" class="post-avatar">
          {{ post.profiles?.nickname?.[0] || 'U' }}
        </el-avatar>
        <div class="post-user-info">
          <span class="post-username">{{ post.profiles?.nickname || '用户' }}</span>
          <span class="post-time">{{ formatTime(post.created_at) }}</span>
        </div>
      </div>
      <!-- ===== 三个点下拉菜单 ===== -->
      <div @click.stop>
        <el-dropdown @command="handleCommand" trigger="click">
          <el-button text class="more-btn">
            <i class="fas fa-ellipsis-h"></i>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="report">举报</el-dropdown-item>
              <el-dropdown-item v-if="post.user_id === authStore.user?.id" command="delete">删除</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- ===== 内容 ===== -->
    <div class="post-content">
      <p>{{ post.content }}</p >
      <span v-if="post.topic" class="post-topic" @click.stop="goTopic(post.topic)">
        #{{ post.topic }}
      </span>
    </div>

    <!-- ===== 互动按钮 ===== -->
    <div class="post-actions">
      <button class="action-btn" :class="{ active: post.is_liked }" @click.stop="emit('like', post)">
        <i :class="post.is_liked ? 'fas fa-heart' : 'far fa-heart'"></i>
        <span>{{ post.like_count || 0 }}</span>
      </button>
      <button class="action-btn" @click.stop="toggleComments">
        <i class="far fa-comment"></i>
        <span>{{ post.comment_count || 0 }}</span>
      </button>
      <button class="action-btn" :class="{ active: post.is_collected }" @click.stop="emit('collect', post)">
        <i :class="post.is_collected ? 'fas fa-bookmark' : 'far fa-bookmark'"></i>
        <span>{{ post.collect_count || 0 }}</span>
      </button>
    </div>

    <!-- ===== 评论区域 ===== -->
    <div v-if="showComments" class="comment-section">
      <div class="comment-list">
        <div v-for="comment in post.comments || []" :key="comment.id" class="comment-item">
          <div class="comment-user" @click.stop="emit('user-click', comment.user_id)">
            <el-avatar :size="24" :src="comment.profiles?.avatar_url || ''" class="comment-avatar">
              {{ comment.profiles?.nickname?.[0] || 'U' }}
            </el-avatar>
            <span class="comment-username">{{ comment.profiles?.nickname || '用户' }}</span>
          </div>
          <span class="comment-text">{{ comment.content }}</span>
          <span class="comment-time">{{ formatTime(comment.created_at) }}</span>
          <button
            v-if="comment.user_id === authStore.user?.id"
            class="comment-delete-btn"
            @click.stop="deleteComment(comment.id)"
          >
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div v-if="!post.comments?.length" class="comment-empty">暂无评论</div>
      </div>
      <div class="comment-input-wrapper">
        <el-input
          v-model="commentInput"
          placeholder="写评论..."
          size="small"
          @keyup.enter="submitComment"
        />
        <el-button size="small" type="primary" @click="submitComment">
          发送
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'
import { createComment, deleteComment as deleteCommentApi } from '@/api/community'

const props = defineProps({
  post: { type: Object, required: true }
})

const emit = defineEmits(['like', 'collect', 'comment', 'user-click', 'report', 'delete'])

const router = useRouter()
const authStore = useAuthStore()

const showComments = ref(false)
const commentInput = ref('')

function formatTime(time) {
  if (!time) return ''
  let utcStr = time
  if (!time.endsWith('Z') && !time.includes('+')) {
    utcStr = time + 'Z'
  }
  const t = new Date(utcStr)
  if (isNaN(t.getTime())) return ''
  const now = new Date()
  const diff = Math.floor((now - t) / 1000)
  if (diff < 60) return '刚刚'
  if (diff < 3600) return Math.floor(diff / 60) + '分钟前'
  if (diff < 86400) return Math.floor(diff / 3600) + '小时前'
  if (diff < 604800) return Math.floor(diff / 86400) + '天前'
  return t.toLocaleDateString('zh-CN')
}

function goTopic(topic) {
  router.push(`/community?topic=${topic}`)
}

function handleCommand(command) {
  if (command === 'report') {
    emit('report', props.post)
  } else if (command === 'delete') {
    emit('delete', props.post)
  }
}

function toggleComments() {
  showComments.value = !showComments.value
  if (showComments.value) {
    emit('comment', props.post.id)
  }
}

async function submitComment() {
  if (!commentInput.value.trim()) {
    ElMessage.warning('请输入评论')
    return
  }
  try {
    const res = await createComment({
      post_id: props.post.id,
      user_id: authStore.user.id,
      content: commentInput.value
    })
    ElMessage.success('评论成功')
    const newComment = {
      id: res.id || Date.now().toString(),
      content: commentInput.value,
      user_id: authStore.user.id,
      profiles: {
        nickname: authStore.user.nickname,
        avatar_url: authStore.user.avatar_url
      },
      created_at: new Date().toISOString()
    }
    if (!props.post.comments) props.post.comments = []
    props.post.comments.unshift(newComment)
    props.post.comment_count = (props.post.comment_count || 0) + 1
    commentInput.value = ''
  } catch {
    ElMessage.error('评论失败')
  }
}

async function deleteComment(commentId) {
  ElMessageBox.confirm('确定要删除这条评论吗？', '确认删除')
    .then(async () => {
      try {
        await deleteCommentApi(commentId, authStore.user.id)
        ElMessage.success('删除成功')
        props.post.comments = props.post.comments.filter(c => c.id !== commentId)
        props.post.comment_count = (props.post.comment_count || 1) - 1
      } catch {
        ElMessage.error('删除失败')
      }
    })
    .catch(() => {})
}
</script>

<style scoped>
.post-card {
  padding: 16px 18px;
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.04);
  background: rgba(255, 255, 255, 0.02);
  transition: all 0.3s ease;
}
.post-card:hover {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.08);
  transform: translateY(-2px);
}

.post-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.post-user {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}
.post-avatar {
  flex-shrink: 0;
}
.post-user-info {
  display: flex;
  flex-direction: column;
}
.post-username {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}
.post-time {
  font-size: 12px;
  color: var(--text-muted);
}
.more-btn {
  color: var(--text-muted) !important;
  padding: 4px 8px !important;
  font-size: 16px;
}
.more-btn:hover {
  color: var(--text-primary) !important;
}

.post-content {
  margin: 8px 0 10px;
}
.post-content p {
  font-size: 15px;
  color: var(--text-primary);
  line-height: 1.7;
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
}
.post-topic {
  display: inline-block;
  margin-top: 6px;
  font-size: 13px;
  color: #409eff;
  background: rgba(64, 158, 255, 0.08);
  padding: 2px 10px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
}
.post-topic:hover {
  background: rgba(64, 158, 255, 0.15);
}

.post-actions {
  display: flex;
  gap: 20px;
  padding-top: 10px;
  border-top: 1px solid rgba(255, 255, 255, 0.04);
}
.action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  background: none;
  border: none;
  color: var(--text-muted);
  font-size: 14px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 8px;
  transition: all 0.3s ease;
}
.action-btn:hover {
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.04);
}
.action-btn.active {
  color: #f56c6c;
}
.action-btn.active i {
  color: #f56c6c;
}
.action-btn span {
  font-size: 13px;
}

.comment-section {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.04);
}
.comment-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 10px;
}
.comment-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}
.comment-user {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
}
.comment-avatar {
  flex-shrink: 0;
}
.comment-username {
  font-weight: 500;
  color: var(--text-primary);
}
.comment-text {
  color: var(--text-secondary);
}
.comment-time {
  font-size: 11px;
  color: var(--text-muted);
}
.comment-delete-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 4px;
  transition: all 0.3s ease;
}
.comment-delete-btn:hover {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.10);
}
.comment-empty {
  color: var(--text-muted);
  font-size: 13px;
  padding: 4px 0;
}
.comment-input-wrapper {
  display: flex;
  gap: 8px;
}
.comment-input-wrapper :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.04) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  border-radius: 10px !important;
}
.comment-input-wrapper .el-button {
  border-radius: 10px !important;
  background: rgba(64, 158, 255, 0.10) !important;
  border: 1px solid rgba(64, 158, 255, 0.15) !important;
  color: #409eff !important;
}
</style>