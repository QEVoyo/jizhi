<template>
  <div class="post-card">
    <!-- ===== 顶部：头像 + 昵称 + 时间 ===== -->
    <div class="post-header">
      <div class="post-user" @click="emit('user-click', post.user_id)">
        <el-avatar :size="36" :src="post.profiles?.avatar_url || ''" class="post-avatar">
          {{ post.profiles?.nickname?.[0] || 'U' }}
        </el-avatar>
        <div class="post-user-info">
          <span class="post-nickname">{{ post.profiles?.nickname || '用户' }}</span>
          <span class="post-time">{{ formatTime(post.created_at) }}</span>
        </div>
      </div>
      <div class="post-actions-top">
        <el-dropdown trigger="click" @command="handleMenuCommand">
          <i class="fas fa-ellipsis-h post-more-btn"></i>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="report">🚩 举报</el-dropdown-item>
              <el-dropdown-item v-if="post.user_id === authStore.user.id" command="delete">🗑️ 删除</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- ===== 标题 ===== -->
    <div v-if="post.title && post.title.trim()" class="post-title">{{ post.title }}</div>

    <!-- ===== 正文内容 ===== -->
    <div class="post-content">{{ post.content }}</div>

    <!-- ===== 标签 ===== -->
    <div v-if="post.tags && post.tags.length" class="post-tags">
      <span v-for="tag in post.tags" :key="tag" class="post-tag">#{{ tag }}</span>
    </div>

    <!-- ===== 图片（缩略图，点击放大预览） ===== -->
    <div v-if="post.images && post.images.length" class="post-images">
      <div
        v-for="(img, idx) in post.images"
        :key="idx"
        class="post-image-wrapper"
        @click="previewImage(img)"
      >
        < img :src="img" :alt="'图片' + (idx+1)" class="post-image" loading="lazy" />
      </div>
    </div>

    <!-- ===== 底部操作栏：点赞/收藏/评论 ===== -->
    <div class="post-footer">
      <!-- 点赞 -->
      <div class="post-action" @click="emit('like', post)">
        <i class="fas fa-heart" :class="{ 'liked': post.is_liked }"></i>
        <span>{{ post.like_count || 0 }}</span>
      </div>

      <!-- 评论 -->
      <div class="post-action" @click="toggleComments">
        <i class="fas fa-comment"></i>
        <span>{{ post.comment_count || 0 }}</span>
      </div>

      <!-- 收藏 -->
      <div class="post-action" @click="emit('collect', post)">
        <i class="fas fa-bookmark" :class="{ 'collected': post.is_collected }"></i>
        <span>{{ post.collect_count || 0 }}</span>
      </div>
    </div>

    <!-- ===== 评论区域（展开后显示） ===== -->
    <div v-if="showComments" class="post-comments">
      <el-divider style="margin: 8px 0;" />
      <div v-if="post.comments && post.comments.length" class="comment-list">
        <div v-for="c in post.comments" :key="c.id" class="comment-item">
          <span class="comment-nickname">{{ c.profiles?.nickname || '用户' }}：</span>
          <span class="comment-content">{{ c.content }}</span>
        </div>
      </div>
      <div v-else class="comment-empty">暂无评论</div>

      <div class="comment-input-area">
        <el-input
          v-model="commentText"
          placeholder="写下你的评论..."
          size="small"
          @keyup.enter="submitComment"
        />
        <el-button type="primary" size="small" @click="submitComment">发送</el-button>
      </div>
    </div>

    <!-- ===== 图片放大预览弹窗 ===== -->
    <el-image-viewer
      v-if="previewVisible"
      :url-list="[previewImageUrl]"
      @close="previewVisible = false"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const authStore = useAuthStore()
const props = defineProps({
  post: { type: Object, required: true }
})
const emit = defineEmits(['like', 'collect', 'comment', 'user-click', 'report', 'delete'])

// ===== 评论展开/收起 =====
const showComments = ref(false)
const commentText = ref('')

function toggleComments() {
  showComments.value = !showComments.value
}

async function submitComment() {
  if (!commentText.value.trim()) return
  // TODO: 这里稍后接入后端评论接口
  ElMessage.success('评论功能即将上线')
  commentText.value = ''
}

// ===== 图片预览 =====
const previewVisible = ref(false)
const previewImageUrl = ref('')

function previewImage(url) {
  previewImageUrl.value = url
  previewVisible.value = true
}

// ===== 更多操作 =====
function handleMenuCommand(command) {
  if (command === 'report') {
    emit('report', props.post)
  } else if (command === 'delete') {
    emit('delete', props.post)
  }
}

// ===== 时间格式化 =====
function formatTime(timeStr) {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  const now = new Date()
  const diff = Math.floor((now - date) / 1000)
  if (diff < 60) return '刚刚'
  if (diff < 3600) return Math.floor(diff / 60) + '分钟前'
  if (diff < 86400) return Math.floor(diff / 3600) + '小时前'
  if (diff < 604800) return Math.floor(diff / 86400) + '天前'
  return date.toLocaleDateString()
}
</script>

<style scoped>
.post-card {
  padding: 16px 18px;
  border-radius: 12px;
  border: 1px solid var(--border-color);
  background: var(--card-bg);
  margin-bottom: 12px;
  transition: all 0.3s ease;
}
.post-card:hover {
  border-color: rgba(255,255,255,0.08);
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0,0,0,0.04);
}

/* ===== 头部 ===== */
.post-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
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
.post-nickname {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}
.post-nickname:hover {
  color: #409EFF;
}
.post-time {
  font-size: 12px;
  color: var(--text-muted);
}
.post-more-btn {
  color: var(--text-muted);
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.3s ease;
}
.post-more-btn:hover {
  color: var(--text-primary);
  background: rgba(255,255,255,0.06);
}

/* ===== 标题 ===== */
.post-title {
  font-size: 17px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 6px;
}

/* ===== 正文 ===== */
.post-content {
  font-size: 15px;
  color: var(--text-secondary);
  line-height: 1.8;
  white-space: pre-wrap;
  margin-bottom: 8px;
}

/* ===== 标签 ===== */
.post-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 10px;
}
.post-tag {
  font-size: 13px;
  color: #409EFF;
  cursor: pointer;
}
.post-tag:hover {
  text-decoration: underline;
}

/* ===== 图片 ===== */
.post-images {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
}
.post-image-wrapper {
  width: 100px;
  height: 100px;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  border: 1px solid rgba(255,255,255,0.06);
  transition: all 0.3s ease;
}
.post-image-wrapper:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
.post-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* ===== 底部操作 ===== */
.post-footer {
  display: flex;
  gap: 24px;
  padding-top: 10px;
  border-top: 1px solid rgba(255,255,255,0.04);
}
.post-action {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  color: var(--text-muted);
  font-size: 14px;
  transition: all 0.3s ease;
}
.post-action:hover {
  color: var(--text-primary);
}
.post-action i {
  font-size: 16px;
  transition: transform 0.2s ease;
}
.post-action:active i {
  transform: scale(1.2);
}
/* 点赞状态 */
.fa-heart.liked {
  color: #f56c6c;
  font-weight: 900;
}
/* 收藏状态 */
.fa-bookmark.collected {
  color: #f59e0b;
  font-weight: 900;
}

/* ===== 评论区域 ===== */
.post-comments {
  margin-top: 10px;
  padding-top: 4px;
}
.comment-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 8px;
}
.comment-item {
  font-size: 14px;
  color: var(--text-secondary);
}
.comment-nickname {
  font-weight: 500;
  color: var(--text-primary);
}
.comment-empty {
  font-size: 13px;
  color: var(--text-muted);
  padding: 4px 0;
}
.comment-input-area {
  display: flex;
  gap: 8px;
}
.comment-input-area .el-input {
  flex: 1;
}

/* ===== 深色适配 ===== */
[data-theme="dark"] .post-card {
  background: rgba(255,255,255,0.02);
  border-color: rgba(255,255,255,0.06);
}
</style>