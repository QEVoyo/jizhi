<template>
  <div class="share-card" @click="handleClick">
    <div class="share-card-content">
      <div class="share-card-type">
        <i :class="type === 'question' ? 'fas fa-pen' : 'fas fa-folder'"></i>
        {{ type === 'question' ? '分享题目' : '分享题集' }}
      </div>
      <div class="share-card-title">{{ title }}</div>
      <div class="share-card-meta">
        <span v-if="type === 'question'">{{ category }} · {{ typeLabel }} · {{ difficulty }}</span>
        <span v-else>{{ questionCount }} 道题 · 平均掌握度 {{ mastery }}%</span>
      </div>
      <div class="share-card-action">
        <span>{{ type === 'question' ? '点击查看题目 →' : '点击查看题集 →' }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  type: {
    type: String,
    required: true,
    validator: (val) => ['question', 'question_set'].includes(val)
  },
  questionId: String,
  setId: String,
  title: String,
  category: String,
  typeLabel: String,
  difficulty: String,
  questionCount: Number,
  mastery: Number
})

const emit = defineEmits(['click'])

const displayTitle = computed(() => {
  return props.title || (props.type === 'question' ? '题目分享' : '题集分享')
})

const displayMeta = computed(() => {
  if (props.type === 'question') {
    return `${props.category || '通用'} · ${props.typeLabel || '选择题'} · ${props.difficulty || '中等'}`
  }
  return `${props.questionCount || 0} 道题 · 平均掌握度 ${props.mastery || 0}%`
})

function handleClick() {
  emit('click')
}
</script>

<style scoped>
.share-card {
  max-width: 280px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(255, 255, 255, 0.03);
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s ease;
}
.share-card:hover {
  background: rgba(255, 255, 255, 0.06);
  transform: translateY(-2px);
  border-color: rgba(255, 255, 255, 0.12);
}
.share-card-content {
  padding: 10px 14px;
}
.share-card-type {
  font-size: 11px;
  color: var(--text-muted);
  margin-bottom: 4px;
}
.share-card-type i {
  margin-right: 4px;
}
.share-card-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.share-card-meta {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 4px;
}
.share-card-action {
  margin-top: 6px;
  font-size: 12px;
  color: #409eff;
}
</style>