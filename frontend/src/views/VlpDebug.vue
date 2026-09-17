<template>
  <div style="max-width: 820px; margin: 24px auto; padding: 0 12px;">
    <div style="font-family: monospace; color: #7ee0ff; background: #0d1220; padding: 10px 14px; border-radius: 10px; line-height: 1.7; font-size: 13px;">
      <b style="color:#fff">VLP 自检页（打开后把下面数字发我）</b>
      <div>页面报错: {{ err || '无' }}</div>
      <div>video: {{ video ? '已加载 ' + (video.title || video.knowledge_name || '') : '加载中…' }}</div>
      <div>舞台尺寸: {{ stageInfo }}</div>
      <div>加载角标/横幅/被拦层/缓冲: {{ maskInfo }}</div>
      <div>音频元素: {{ audioInfo }}</div>
      <div>浏览器能力: aspect-ratio={{ feats.ar }} · color-mix={{ feats.cm }} · backdrop-filter={{ feats.bf }} · lookbehind={{ feats.lb }}</div>
    </div>
    <div v-if="video" style="margin-top: 14px;">
      <VideoLessonPlayer :video="video" :autoplay="true" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import VideoLessonPlayer from '@/components/VideoLessonPlayer.vue'
import request from '@/utils/request'

const video = ref(null)
const err = ref('')
const stageInfo = ref('…')
const maskInfo = ref('…')
const audioInfo = ref('…')
const feats = ref({ ar: '?', cm: '?', bf: '?', lb: '?' })
let timer = null

function probe() {
  try {
    const stage = document.querySelector('.vlp-stage')
    if (stage) {
      const r = stage.getBoundingClientRect()
      const cs = getComputedStyle(stage)
      stageInfo.value = `${Math.round(r.width)} × ${Math.round(r.height)}px (overflow=${cs.overflow})`
      if (r.width < 10 || r.height < 10) stageInfo.value += ' ⚠️尺寸塌陷'
    } else {
      stageInfo.value = 'DOM 里没有 .vlp-stage'
    }
    const pill = document.querySelector('.vlp-load-pill')
    const banner = document.querySelector('.vlp-audio-banner')
    const blockedEl = document.querySelector('.vlp-blocked')
    const buff = document.querySelector('.vlp-buff')
    const parts = []
    if (pill) parts.push('加载角标[在]')
    if (banner) parts.push('出错误幅[在]')
    if (blockedEl) parts.push('被拦层[在]')
    if (buff) parts.push('缓冲[在]')
    maskInfo.value = parts.length ? parts.join(' / ') : '无任何提示层'
    const a = document.querySelector('audio')
    if (a) {
      audioInfo.value = `src存在=${!!a.getAttribute('src')} readyState=${a.readyState} paused=${a.paused} currentTime=${a.currentTime.toFixed(1)}s duration=${isFinite(a.duration) ? a.duration.toFixed(1) : '?'}`
    } else {
      audioInfo.value = 'DOM 里没有 <audio>'
    }
  } catch (e) {
    console.error('probe', e)
  }
}

async function loadVideo() {
  try {
    let id = new URLSearchParams(location.search).get('id')
    if (!id) {
      const sq = await request.get('/video/square')
      const items = sq.data?.items || sq.data?.videos || sq.data?.list || []
      const hit = items.find(v => v.status === 'ready') || items[0]
      if (!hit) { err.value = '视频广场没有数据'; return }
      id = hit.id
    }
    const d = await request.get(`/video/${id}/detail`, { params: { user_id: '' } })
    video.value = d.data?.video || d.data
    if (!video.value) err.value = err.value || 'detail 返回无 video'
  } catch (e) {
    err.value = err.value || (e?.response?.data?.detail || e?.message || String(e))
  }
}

onMounted(async () => {
  window.addEventListener('error', e => { err.value = err.value || String(e.message) })
  window.addEventListener('unhandledrejection', e => { err.value = err.value || 'Promise: ' + String(e.reason) })
  try {
    feats.value.ar = CSS.supports('aspect-ratio', '16/9')
    feats.value.cm = CSS.supports('color', 'color-mix(in srgb, red 50%, blue)')
    feats.value.bf = CSS.supports('backdrop-filter', 'blur(2px)')
    feats.value.lb = (() => { try { 'ab'.split(/(?<=a)/); return true } catch { return false } })()
  } catch { /* CSS.supports 不可用则保持 ? */ }
  timer = setInterval(probe, 800)
  await loadVideo()
  setTimeout(probe, 300)
})

onUnmounted(() => clearInterval(timer))
</script>