<template>
  <div class="pd-page">
    <div class="pd-container">
      <div class="pd-head">
        <button class="g-btn" @click="goBack">← 返回</button>
        <h1>动态详情</h1>
      </div>

      <div v-if="loading" class="pd-state">加载中…</div>
      <div v-else-if="!post" class="pd-state">动态不存在或已被删除</div>

      <template v-else>
        <!-- 帖子本体 -->
        <div class="pd-post">
          <div class="pd-author" @click="goUser">
            <img v-if="post.profiles?.avatar_url" :src="post.profiles.avatar_url" class="pd-avatar" />
            <span v-else class="pd-avatar ph">{{ (post.profiles?.nickname || 'U')[0] }}</span>
            <div>
              <div class="pd-nick">{{ post.profiles?.nickname || post.profiles?.user_account || '用户' }}</div>
              <div class="pd-time">{{ fmt(post.created_at) }}</div>
            </div>
          </div>
          <h2 v-if="post.title" class="pd-title">{{ post.title }}</h2>
          <div class="pd-text">{{ post.content }}</div>
          <div v-if="post.images && post.images.length" class="pd-imgs">
            <img v-for="(img, i) in post.images" :key="i" :src="img" />
          </div>
          <div class="pd-actions">
            <button class="pd-act" :class="{ on: post.is_liked }" @click="toggleLike">
              <i class="fas fa-heart"></i> {{ post.like_count || 0 }}
            </button>
            <button class="pd-act" :class="{ on: post.is_collected }" @click="toggleCollect">
              <i class="fas fa-star"></i> {{ post.collect_count || 0 }}
            </button>
            <span class="pd-act static"><i class="fas fa-comment"></i> {{ comments.length }}</span>
          </div>
        </div>

        <!-- 评论列表（消息里带 ?comment=xxx 时滚到这里并高亮） -->
        <div class="pd-comments">
          <h3>评论 {{ comments.length }}</h3>
          <div v-for="c in comments" :key="c.id" class="pd-comment"
               :class="{ target: c.id === targetComment }" :id="'c-' + c.id">
            <span class="pd-cnick">{{ c.profiles?.nickname || '用户' }}：</span>
            <span class="pd-ctext">{{ c.content }}</span>
          </div>
          <div v-if="!comments.length" class="pd-state small">还没有评论</div>

          <div class="pd-input">
            <input v-model="draft" class="glass-input" placeholder="说点什么…"
                   @keyup.enter="submitComment" />
            <button class="g-btn primary" :disabled="!draft.trim()" @click="submitComment">发送</button>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { getPost, likePost, unlikePost, collectPost, uncollectPost, createPost } from '@/api/community'
import request from '@/utils/request'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const post = ref(null)
const comments = ref([])
const loading = ref(true)
const draft = ref('')
const targetComment = ref('')

async function load() {
  loading.value = true
  try {
    const data = await getPost(route.params.id, authStore.user?.id)
    post.value = data
    comments.value = data.comments || []
    targetComment.value = route.query.comment || ''
    if (targetComment.value) {
      await nextTick()
      const el = document.getElementById('c-' + targetComment.value)
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  } catch (e) {
    post.value = null
  } finally {
    loading.value = false
  }
}

async function toggleLike() {
  const uid = authStore.user?.id
  if (!uid) return
  try {
    if (post.value.is_liked) { await unlikePost(post.value.id, uid); post.value.like_count-- }
    else { await likePost(post.value.id, uid); post.value.like_count++ }
    post.value.is_liked = !post.value.is_liked
  } catch { ElMessage.error('操作失败') }
}

async function toggleCollect() {
  const uid = authStore.user?.id
  if (!uid) return
  try {
    if (post.value.is_collected) { await uncollectPost(post.value.id, uid); post.value.collect_count-- }
    else { await collectPost(post.value.id, uid); post.value.collect_count++ }
    post.value.is_collected = !post.value.is_collected
  } catch { ElMessage.error('操作失败') }
}

async function submitComment() {
  const uid = authStore.user?.id
  const text = draft.value.trim()
  if (!uid || !text) return
  try {
    await request.post(`/community/post/${post.value.id}/comment`,
      { content: text, user_id: uid }, { params: { user_id: uid } })
    draft.value = ''
    await load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '评论失败')
  }
}

function goUser() {
  const uid = post.value?.user_id
  if (uid) router.push(`/community/user/${uid}`)
}
function goBack() { router.back() }

function fmt(t) {
  if (!t) return ''
  const d = new Date(t.endsWith('Z') || t.includes('+') ? t : t + 'Z')
  return isNaN(d) ? '' : d.toLocaleString('zh-CN')
}

onMounted(load)
</script>

<style scoped>
.pd-page { height: calc(100vh - var(--jz-top, 0px)); overflow-y: auto;
  display: flex; justify-content: center; padding: 28px 20px; }
.pd-container { max-width: 720px; width: 100%; }
.pd-head { display: flex; align-items: center; gap: 14px; margin-bottom: 16px; }
.pd-head h1 { font-size: 18px; margin: 0; color: var(--text-primary); }
.g-btn { display: inline-flex; align-items: center; gap: 5px; padding: 7px 16px; font-size: 13px;
  color: var(--text-secondary); background: color-mix(in srgb, var(--surface,#fff) 4%, transparent);
  border: 1px solid var(--line-soft); border-radius: 10px; cursor: pointer; font-family: inherit; }
.g-btn.primary { color: #fff; border: none; background: var(--brand); font-weight: 600; }
.g-btn:disabled { opacity: .4; }
.pd-post, .pd-comments { padding: 20px 24px; border-radius: 16px; margin-bottom: 14px;
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent);
  backdrop-filter: blur(24px); -webkit-backdrop-filter: blur(24px);
  border: 1px solid var(--line-soft); }
.pd-author { display: flex; align-items: center; gap: 10px; cursor: pointer; }
.pd-avatar { width: 40px; height: 40px; border-radius: 50%; object-fit: cover; }
.pd-avatar.ph { display: flex; align-items: center; justify-content: center;
  background: var(--brand); color: #fff; font-weight: 700; }
.pd-nick { font-size: 14px; font-weight: 600; color: var(--text-primary); }
.pd-time { font-size: 11px; color: var(--text-muted); }
.pd-title { font-size: 17px; margin: 14px 0 6px; color: var(--text-primary); }
.pd-text { font-size: 14px; line-height: 1.8; color: var(--text-secondary); white-space: pre-wrap; }
.pd-imgs { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 8px; margin-top: 12px; }
.pd-imgs img { width: 100%; border-radius: 10px; }
.pd-actions { display: flex; gap: 8px; margin-top: 16px; }
.pd-act { display: inline-flex; align-items: center; gap: 5px; padding: 6px 14px; border-radius: 10px;
  font-size: 13px; cursor: pointer; font-family: inherit; color: var(--text-secondary);
  background: color-mix(in srgb, var(--surface,#fff) 3%, transparent); border: 1px solid var(--line-soft); }
.pd-act.on { color: var(--brand); border-color: color-mix(in srgb, var(--brand) 40%, transparent); }
.pd-act.static { cursor: default; }
.pd-comments h3 { font-size: 14px; margin: 0 0 12px; color: var(--text-primary); }
.pd-comment { padding: 9px 12px; border-radius: 10px; font-size: 13.5px; margin-bottom: 6px;
  background: color-mix(in srgb, var(--surface,#fff) 3%, transparent); }
.pd-comment.target { background: color-mix(in srgb, var(--brand) 14%, transparent);
  box-shadow: 0 0 0 1px color-mix(in srgb, var(--brand) 40%, transparent); }
.pd-cnick { color: var(--brand); font-weight: 600; }
.pd-ctext { color: var(--text-secondary); }
.pd-input { display: flex; gap: 8px; margin-top: 14px; }
.glass-input { flex: 1; padding: 9px 12px; border-radius: 10px; font-size: 13px; font-family: inherit;
  color: var(--text-primary); background: color-mix(in srgb, var(--surface,#fff) 4%, transparent);
  border: 1px solid var(--line-soft); outline: none; }
.pd-state { text-align: center; padding: 40px; color: var(--text-muted); }
.pd-state.small { padding: 16px; font-size: 13px; }
</style>
