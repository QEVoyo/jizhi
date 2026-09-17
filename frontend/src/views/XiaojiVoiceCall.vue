<template>
  <div class="voice-call-page" @click="ensurePlayContext">
    <!-- ===== 顶栏 ===== -->
    <div class="call-topbar">
      <el-button text class="top-btn" @click="hangUp" title="挂断返回">
        <i class="fas fa-arrow-left"></i>
      </el-button>
      <div class="topbar-center">
        <span class="call-title">语音通话</span>
        <span class="call-timer">{{ timerText }}</span>
      </div>
      <span class="topbar-spacer"></span>
    </div>

    <!-- ===== 小基形象 ===== -->
    <div class="avatar-zone">
      <div class="pulse-ring ring-1" :class="{ active: connected }"></div>
      <div class="pulse-ring ring-2" :class="{ active: connected }"></div>
      <img
        :src="avatarUrl"
        alt="小基"
        class="call-avatar"
        :class="{ speaking: state === 'speaking' }"
      />
      <div class="call-name">{{ xiaojiName }}</div>
      <div class="call-status" :class="state">
        <span v-if="state === 'listening'" class="status-wave"><i></i><i></i><i></i><i></i></span>
        {{ statusText }}
      </div>
    </div>

    <!-- ===== 字幕区 ===== -->
    <div class="caption-zone" ref="captionRef">
      <div v-if="!captions.length" class="caption-hint">说话后，这里会实时显示对话文字</div>
      <div v-for="(c, i) in captions" :key="i" class="caption-item" :class="c.who">
        <span class="caption-who">{{ c.who === 'me' ? '我' : xiaojiName }}</span>
        <span class="caption-text">{{ c.text }}</span>
      </div>
      <div v-if="liveMeText" class="caption-item me live">
        <span class="caption-who">我</span>
        <span class="caption-text">{{ liveMeText }}</span>
      </div>
      <div v-if="state === 'thinking'" class="caption-item xiaoji live">
        <span class="caption-who">{{ xiaojiName }}</span>
        <span class="typing-dots"><span></span><span></span><span></span></span>
      </div>
    </div>

    <!-- ===== 底部控制 ===== -->
    <div class="control-zone">
      <button
        class="ctrl-btn"
        :class="{ muted: isMuted }"
        @click="toggleMute"
        :title="isMuted ? '取消静音' : '静音'"
      >
        <i :class="isMuted ? 'fas fa-microphone-slash' : 'fas fa-microphone'"></i>
      </button>
      <button class="hangup-btn" @click="hangUp" title="挂断">
        <i class="fas fa-phone-slash"></i>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { getXiaojiConfig } from '@/api/xiaoji'
import { BACKEND_URL } from '@/utils/constants'

const router = useRouter()
const authStore = useAuthStore()

// ===== 通话状态机 =====
// connecting → listening（听用户说）→ thinking（模型思考）→ speaking（小基播报）→ listening …
const state = ref('connecting')
const connected = ref(false)
const isMuted = ref(false)
const captions = ref([])
const liveMeText = ref('')   // 服务端 VAD 实时识别渐进文本（我说话的字幕）
const captionRef = ref(null)

const xiaojiName = ref('小基')
const voiceVolume = ref(5)

// ===== 计时 =====
const timerSeconds = ref(0)
let timerId = null
const timerText = computed(() => {
  const m = String(Math.floor(timerSeconds.value / 60)).padStart(2, '0')
  const s = String(timerSeconds.value % 60).padStart(2, '0')
  return `${m}:${s}`
})

const statusText = computed(() => {
  const map = {
    connecting: '正在连接…',
    listening: isMuted.value ? '已静音' : '正在聆听，请说话…',
    thinking: '正在思考…',
    speaking: '小基正在说…'
  }
  return map[state.value] || '通话中'
})

const avatarUrl = computed(() => {
  const map = {
    connecting: '/images/xiaoji/xiaoji_sleeping.png',
    listening: '/images/xiaoji/xiaoji_idle.png',
    thinking: '/images/xiaoji/xiaoji_thinking.png',
    speaking: '/images/xiaoji/xiaoji_speaking.png'
  }
  return map[state.value] || '/images/xiaoji/xiaoji_idle.png'
})

// ===== 音频与 WS =====
let ws = null
let audioCtx = null
let scriptNode = null
let mediaStream = null
let manualClosed = false
let loudChunks = 0
let expectSilence = false  // 抢话打断后：丢弃在途的 ai_text/ai_audio，直到本轮结束或新一轮开始

// ===== 播放（千问输出 24k PCM16 裸流 → 单源顺序队列，绝不重叠） =====
// 曾用「排期 + 积压重置」方案：积压超限重置起点会让新块与已排期旧块重叠播放，
// 出现「说下一句时上一句没读完的又冒出来」的乱音，且 isPlaying 状态错乱引发误抢话。
// 改为单源队列：同一时刻只有一块在播，前一块播完才取下一块；积压超限丢最旧整块。
let playCtx = null
let gainNode = null
let currentSrc = null
const pendingChunks = []          // Float32Array 队列（24k）
const MAX_QUEUE_SECONDS = 3.0     // 积压上限：超过丢最旧整块（防止延迟无限累积）

function ensurePlayContext() {
  if (!playCtx) {
    playCtx = new (window.AudioContext || window.webkitAudioContext)()
    gainNode = playCtx.createGain()
    gainNode.gain.value = Math.min(1, Math.max(0.1, (voiceVolume.value || 5) / 9))
    gainNode.connect(playCtx.destination)
  }
  if (playCtx.state === 'suspended') playCtx.resume().catch(() => {})
}

function base64ToBytes(b64) {
  const bin = atob(b64)
  const bytes = new Uint8Array(bin.length)
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i)
  return bytes
}

// 千问音频帧（base64 PCM16 24k 小端）→ 入队
function enqueueAiAudio(b64) {
  ensurePlayContext()
  const bytes = base64ToBytes(b64)
  if (!bytes.length || bytes.length % 2) return
  const pcm = new Int16Array(bytes.buffer)
  const f32 = new Float32Array(pcm.length)
  for (let i = 0; i < pcm.length; i++) f32[i] = pcm[i] / 32768
  pendingChunks.push(f32)
  // 积压控制：超过上限丢最旧的整块（整块丢，绝不与在播块重叠）
  let total = 0
  for (const c of pendingChunks) total += c.length
  while (total > MAX_QUEUE_SECONDS * 24000 && pendingChunks.length > 1) {
    total -= pendingChunks.shift().length
  }
  pumpPlayback()
}

// 单源播放泵：没有在播块时才取队列下一块
function pumpPlayback() {
  if (currentSrc || manualClosed) return
  const chunk = pendingChunks.shift()
  if (!chunk) return
  ensurePlayContext()
  const buf = playCtx.createBuffer(1, chunk.length, 24000)
  buf.getChannelData(0).set(chunk)
  const src = playCtx.createBufferSource()
  src.buffer = buf
  src.connect(gainNode)
  src.onended = () => {
    if (currentSrc === src) currentSrc = null
    pumpPlayback()
  }
  currentSrc = src
  if (playCtx.state === 'suspended') {
    playCtx.resume().then(() => src.start()).catch(() => {})
  } else {
    src.start()
  }
}

function isPlaying() {
  return !!currentSrc || pendingChunks.length > 0
}

function stopPlayback() {
  if (currentSrc) {
    try { currentSrc.stop() } catch {}
  }
  currentSrc = null
  pendingChunks.length = 0
}

// ===== 字幕 =====
function pushCaption(who, text) {
  captions.value.push({ who, text })
  scrollCaptions()
}

function appendXiaojiCaption(text) {
  const last = captions.value[captions.value.length - 1]
  if (last && last.who === 'xiaoji') {
    last.text += text
  } else {
    pushCaption('xiaoji', text)
  }
  scrollCaptions()
}

function scrollCaptions() {
  requestAnimationFrame(() => {
    if (captionRef.value) captionRef.value.scrollTop = captionRef.value.scrollHeight
  })
}

// ===== WS =====
function callWsUrl() {
  const wsBase = BACKEND_URL.replace(/^http/, 'ws')
  return `${wsBase}/xiaoji/call-ws?user_id=${encodeURIComponent(authStore.user.id)}&token=${encodeURIComponent(authStore.token)}`
}

function handleServerMessage(e) {
  let d
  try { d = JSON.parse(e.data) } catch { return }
  const t = d.type
  if (t === 'ready') {
    state.value = 'listening'
  } else if (t === 'speech_started') {
    // 用户开始说话（服务端 VAD）→ 新一轮开始，取消丢弃状态
    expectSilence = false
    state.value = 'listening'
  } else if (t === 'partial_text') {
    // 我说话中的实时识别字幕
    liveMeText.value = d.text || ''
    scrollCaptions()
  } else if (t === 'user_text') {
    expectSilence = false
    liveMeText.value = ''
    pushCaption('me', d.text)
    state.value = 'thinking'
  } else if (t === 'ai_text') {
    if (expectSilence) return
    appendXiaojiCaption(d.delta || '')
  } else if (t === 'ai_audio') {
    if (expectSilence) return
    state.value = 'speaking'
    enqueueAiAudio(d.delta || '')
  } else if (t === 'interrupted') {
    // 被抢话：清空未播放音频，回聆听态
    expectSilence = false
    stopPlayback()
    if (state.value === 'speaking') state.value = 'listening'
  } else if (t === 'done') {
    // 本轮结束，取消丢弃状态；播报自然排空后由状态轮询切回 listening
    expectSilence = false
  } else if (t === 'error') {
    ElMessage.error(d.message || '通话出错')
    hangUp()
  }
}

// ===== 抢话打断：小基播报期间检测到用户持续说话 → 打断 =====
// 千问的 cancel 只停生成、不停已生成音频的发送，所以打断后要丢弃在途音频
// （expectSilence），直到收到 done/interrupted 或新一轮 user_text/speech_started
function bargeIn() {
  expectSilence = true
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'interrupt' }))
  }
  stopPlayback()
  state.value = 'listening'
}

// ===== 麦克风 PCM 流 → WS =====
function gateAllowed() {
  return !isPlaying() && !isMuted.value && ws && ws.readyState === WebSocket.OPEN && !manualClosed
}

// Float32（16k）→ Int16 PCM
function floatToPcm16(floats) {
  const pcm = new Int16Array(floats.length)
  for (let i = 0; i < floats.length; i++) {
    const s = Math.max(-1, Math.min(1, floats[i]))
    pcm[i] = s < 0 ? s * 0x8000 : s * 0x7FFF
  }
  return pcm
}

// Int16 PCM → 小端字节流 base64（Uint8Array 值域 0-255，btoa 安全）
function pcm16ToBase64(pcm) {
  const bytes = new Uint8Array(pcm.buffer)
  let binary = ''
  const CHUNK = 0x8000
  for (let i = 0; i < bytes.length; i += CHUNK) {
    binary += String.fromCharCode.apply(null, bytes.subarray(i, i + CHUNK))
  }
  return btoa(binary)
}

// 浏览器未按 16k 建上下文时线性降采样
function resampleTo16k(floats, srcRate) {
  const ratio = srcRate / 16000
  const out = new Float32Array(Math.floor(floats.length / ratio))
  for (let i = 0; i < out.length; i++) {
    const pos = i * ratio
    const i0 = Math.floor(pos)
    const i1 = Math.min(i0 + 1, floats.length - 1)
    const frac = pos - i0
    out[i] = floats[i0] * (1 - frac) + floats[i1] * frac
  }
  return out
}

function startMicPump() {
  scriptNode.onaudioprocess = (e) => {
    if (manualClosed) return
    let floats = e.inputBuffer.getChannelData(0)
    if (audioCtx.sampleRate !== 16000) {
      floats = resampleTo16k(floats, audioCtx.sampleRate)
    }
    // RMS：播报期间检测到持续说话 → 抢话打断（防回声：播报期间不发帧）
    let sum = 0
    for (let i = 0; i < floats.length; i++) sum += floats[i] * floats[i]
    const rms = Math.sqrt(sum / floats.length)
    if (isPlaying() && rms > 0.03) {
      loudChunks++
      if (loudChunks >= 3) {
        loudChunks = 0
        bargeIn()
        return
      }
    } else {
      loudChunks = 0
    }
    if (!gateAllowed()) return
    const b64 = pcm16ToBase64(floatToPcm16(floats))
    try {
      ws.send(JSON.stringify({ status: 0, audio: b64 }))
    } catch { /* 连接已死：onclose 会接管清理 */ }
  }
}

// ===== 状态轮询：播报自然结束后切回聆听态 =====
let statePollId = null

// ===== 挂断 =====
function hangUp() {
  if (manualClosed) return
  manualClosed = true
  try {
    if (ws && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ type: 'bye' }))
  } catch {}
  cleanup()
  router.back()
}

function releaseMedia() {
  if (scriptNode) { try { scriptNode.disconnect() } catch {}; scriptNode = null }
  if (audioCtx) { audioCtx.close().catch(() => {}); audioCtx = null }
  if (mediaStream) { mediaStream.getTracks().forEach(t => t.stop()); mediaStream = null }
}

function cleanup() {
  manualClosed = true
  stopTimer()
  stopPlayback()
  if (statePollId) { clearInterval(statePollId); statePollId = null }
  try { if (ws) ws.close() } catch {}
  ws = null
  releaseMedia()
}

function stopTimer() {
  if (timerId) { clearInterval(timerId); timerId = null }
}

function toggleMute() {
  isMuted.value = !isMuted.value
}

// ===== 挂载 =====
onMounted(async () => {
  // 1) 读配置（名称显示 + 播报音量）
  try {
    const cfg = await getXiaojiConfig(authStore.user.id)
    if (cfg) {
      xiaojiName.value = cfg.name || '小基'
      voiceVolume.value = cfg.voice_volume || 5
    }
  } catch { /* 用默认值 */ }

  // 2) 麦克风（AEC 回声消除 + 降噪，播报期间还会停止发送帧双保险）
  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({
      audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true }
    })
  } catch (e) {
    ElMessage.error('无法访问麦克风，请检查浏览器权限')
    router.back()
    return
  }
  const Ctx = window.AudioContext || window.webkitAudioContext
  audioCtx = new Ctx({ sampleRate: 16000 })
  scriptNode = audioCtx.createScriptProcessor(1024, 1, 1)
  const source = audioCtx.createMediaStreamSource(mediaStream)
  source.connect(scriptNode)
  scriptNode.connect(audioCtx.destination)
  startMicPump()

  // 3) 连接通话 WS
  ws = new WebSocket(callWsUrl())
  ws.onopen = () => {
    connected.value = true
    timerId = setInterval(() => { timerSeconds.value++ }, 1000)
  }
  ws.onmessage = handleServerMessage
  ws.onclose = () => {
    connected.value = false
    if (!manualClosed) {
      manualClosed = true
      stopTimer()
      releaseMedia()
      ElMessage.warning('通话已断开')
      router.back()
    }
  }
  ws.onerror = () => { /* 统一在 onclose 处理 */ }

  // 播报排空后自动回聆听态
  statePollId = setInterval(() => {
    if (manualClosed) return
    if (state.value === 'speaking' && !isPlaying()) state.value = 'listening'
  }, 250)
})

onUnmounted(() => {
  cleanup()
})
</script>

<style scoped>
.voice-call-page {
  position: relative;
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
  background:
    radial-gradient(ellipse 80% 50% at 50% -10%, color-mix(in srgb, var(--brand) 14%, transparent) 0%, transparent 70%),
    radial-gradient(ellipse 60% 40% at 50% 110%, rgba(139,92,246,0.10) 0%, transparent 70%),
    var(--bg-color);
  color: var(--text-primary);
}

/* ===== 顶栏 ===== */
.call-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  flex-shrink: 0;
  z-index: 5;
}
.top-btn {
  color: color-mix(in srgb, var(--text-primary) 70%, transparent) !important;
  font-size: 18px;
}
.top-btn:hover {
  color: var(--text-primary) !important;
}
.topbar-center {
  display: flex;
  align-items: center;
  gap: 10px;
}
.call-title {
  font-size: 16px;
  font-weight: 600;
}
.call-timer {
  font-size: 13px;
  color: color-mix(in srgb, var(--text-primary) 55%, transparent);
  font-variant-numeric: tabular-nums;
  letter-spacing: 1px;
}
.topbar-spacer {
  width: 32px;
}

/* ===== 形象区 ===== */
.avatar-zone {
  position: relative;
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 0;
}
.pulse-ring {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  border-radius: 50%;
  border: 1px solid color-mix(in srgb, var(--brand) 15%, transparent);
  pointer-events: none;
  opacity: 0.5;
}
.ring-1 { width: 230px; height: 230px; }
.ring-2 { width: 330px; height: 330px; border-color: color-mix(in srgb, var(--brand) 7%, transparent); }
.pulse-ring.active {
  animation: ringPulse 2.6s ease-in-out infinite;
}
.pulse-ring.active.ring-2 {
  animation: ringPulse 2.6s ease-in-out 1.3s infinite;
}
@keyframes ringPulse {
  0%, 100% { transform: translate(-50%, -50%) scale(1); opacity: 0.5; }
  50% { transform: translate(-50%, -50%) scale(1.12); opacity: 1; }
}

.call-avatar {
  width: 170px;
  height: 170px;
  object-fit: contain;
  filter: drop-shadow(0 0 40px color-mix(in srgb, var(--brand) 25%, transparent));
  transition: transform 0.3s ease;
  z-index: 2;
}
.call-avatar.speaking {
  animation: avatarTalk 0.6s ease-in-out infinite;
}
@keyframes avatarTalk {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.04); }
}

.call-name {
  margin-top: 10px;
  font-size: 20px;
  font-weight: 600;
  z-index: 2;
}
.call-status {
  margin-top: 6px;
  font-size: 13px;
  color: color-mix(in srgb, var(--text-primary) 60%, transparent);
  display: flex;
  align-items: center;
  gap: 8px;
  z-index: 2;
}
.call-status.speaking { color: var(--brand-bright); }

/* 聆听态声波动画 */
.status-wave {
  display: inline-flex;
  align-items: flex-end;
  gap: 3px;
  height: 14px;
}
.status-wave i {
  width: 3px;
  height: 6px;
  border-radius: 2px;
  background: var(--brand-bright);
  animation: waveBounce 1s ease-in-out infinite;
}
.status-wave i:nth-child(2) { animation-delay: 0.15s; }
.status-wave i:nth-child(3) { animation-delay: 0.3s; }
.status-wave i:nth-child(4) { animation-delay: 0.45s; }
@keyframes waveBounce {
  0%, 100% { height: 5px; }
  50% { height: 14px; }
}

/* ===== 字幕区 ===== */
.caption-zone {
  flex-shrink: 0;
  max-height: 26vh;
  overflow-y: auto;
  margin: 0 auto;
  width: min(640px, 92%);
  padding: 12px 16px;
  border-radius: 16px;
  background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent);
  border: 1px solid var(--line-soft);
  backdrop-filter: blur(12px);
  scroll-behavior: smooth;
}
.caption-zone::-webkit-scrollbar { width: 3px; }
.caption-zone::-webkit-scrollbar-thumb {
  background: rgba(128,128,128,0.2);
  border-radius: 2px;
}
.caption-hint {
  text-align: center;
  font-size: 12px;
  color: color-mix(in srgb, var(--text-primary) 35%, transparent);
  padding: 6px 0;
}
.caption-item {
  display: flex;
  gap: 8px;
  padding: 3px 0;
  font-size: 14px;
  line-height: 1.6;
  align-items: baseline;
}
.caption-item.me { color: color-mix(in srgb, var(--text-primary) 85%, transparent); }
.caption-item.xiaoji { color: var(--brand-glow); }
.caption-who {
  flex-shrink: 0;
  font-size: 12px;
  padding: 0 8px;
  border-radius: 8px;
  background: rgba(128,128,128,0.12);
  color: inherit;
  opacity: 0.9;
}
.caption-text {
  word-break: break-word;
  white-space: pre-wrap;
}

.typing-dots {
  display: inline-flex;
  gap: 4px;
  align-items: center;
  padding: 3px 0;
}
.typing-dots span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--brand-glow);
  animation: typingBounce 1.4s infinite both;
}
.typing-dots span:nth-child(2) { animation-delay: 0.16s; }
.typing-dots span:nth-child(3) { animation-delay: 0.32s; }
@keyframes typingBounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

/* ===== 底部控制 ===== */
.control-zone {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 48px;
  padding: 24px 0 36px;
}
.ctrl-btn {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  border: 1px solid var(--line);
  background: color-mix(in srgb, var(--surface, #ffffff) 5%, transparent);
  color: color-mix(in srgb, var(--text-primary) 80%, transparent);
  font-size: 18px;
  cursor: pointer;
  transition: all 0.25s ease;
  backdrop-filter: blur(8px);
}
.ctrl-btn:hover {
  background: color-mix(in srgb, var(--surface, #ffffff) 10%, transparent);
  transform: scale(1.05);
}
.ctrl-btn.muted {
  background: rgba(245,108,108,0.15);
  border-color: rgba(245,108,108,0.4);
  color: #f56c6c;
}
.hangup-btn {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  border: none;
  background: linear-gradient(135deg, #ef4444, #dc2626);
  color: #fff;
  font-size: 24px;
  cursor: pointer;
  box-shadow: 0 6px 24px rgba(239,68,68,0.4);
  transition: all 0.25s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}
.hangup-btn:hover {
  transform: scale(1.06);
  box-shadow: 0 8px 32px rgba(239,68,68,0.55);
}

@media (max-width: 640px) {
  .call-avatar { width: 130px; height: 130px; }
  .ring-1 { width: 180px; height: 180px; }
  .ring-2 { width: 260px; height: 260px; }
  .control-zone { gap: 36px; }
}
</style>
