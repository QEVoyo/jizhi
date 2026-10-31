import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'

// ============================================================
// 实时语音听写（2026-10-30 从 XiaojiCall.vue 抽出）
//
// 麦克风 16k PCM 帧 → /xiaoji/asr-ws → 讯飞 iat，逐字回传累计文本。
// 浏览器 WebSocket 不能自定义请求头，凭证只能走 query（后端先验签再 accept）。
// 讯飞 iat 按量计费，没有 token 就只会收到 403，这里不另做兜底。
//
// 用法：
//   const { isRecording, start, stop } = useLiveAsr({
//     getBaseText: () => input.value,   // 开始听写时已有的文本
//     onText: (text) => { input.value = text },
//     onDone: () => {},
//     onError: (msg) => ElMessage.error(msg),
//   })
// ============================================================

const SILENCE_CHUNKS_MAX = 40   // 1024 samples @16k ≈ 64ms/帧 × 40 ≈ 2.5s

export function useLiveAsr({ getBaseText, onText, onDone, onError } = {}) {
  const authStore = useAuthStore()
  const isRecording = ref(false)

  let audioCtx = null
  let scriptNode = null
  let mediaStream = null
  let asrWs = null
  let closeTimer = null
  let liveBaseText = ''

  function wsUrl() {
    const base = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'
    const token = authStore.token
    return base.replace(/^http/, 'ws') + '/xiaoji/asr-ws' +
      (token ? `?token=${encodeURIComponent(token)}` : '')
  }

  async function start() {
    if (isRecording.value) return
    const Ctx = window.AudioContext || window.webkitAudioContext
    if (!navigator.mediaDevices || !Ctx) {
      onError?.('当前浏览器不支持录音，请使用 Chrome / Edge')
      return
    }

    try {
      mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true })
      audioCtx = new Ctx({ sampleRate: 16000 })
      scriptNode = audioCtx.createScriptProcessor(1024, 1, 1)
      const source = audioCtx.createMediaStreamSource(mediaStream)
      source.connect(scriptNode)
      scriptNode.connect(audioCtx.destination)

      liveBaseText = getBaseText?.() || ''
      isRecording.value = true

      asrWs = new WebSocket(wsUrl())

      // 麦克风 PCM 持续发往后端 + 静音检测自动结束
      let silenceChunks = 0
      scriptNode.onaudioprocess = (e) => {
        if (!asrWs || asrWs.readyState !== WebSocket.OPEN) return
        let floats = e.inputBuffer.getChannelData(0)
        if (audioCtx.sampleRate !== 16000) {
          floats = resampleTo16k(floats, audioCtx.sampleRate)
        }
        let sum = 0
        for (let i = 0; i < floats.length; i++) sum += floats[i] * floats[i]
        const rms = Math.sqrt(sum / floats.length)
        silenceChunks = rms < 0.006 ? silenceChunks + 1 : 0
        if (silenceChunks >= SILENCE_CHUNKS_MAX) {
          silenceChunks = 0
          stop()
          return
        }
        asrWs.send(JSON.stringify({ status: 0, audio: pcm16ToBase64(floatToPcm16(floats)) }))
      }

      asrWs.onmessage = (e) => {
        try {
          const d = JSON.parse(e.data)
          if (d.error) {
            onError?.('识别失败：' + d.error)
            return
          }
          if (typeof d.text === 'string') {
            onText?.(liveBaseText ? liveBaseText + d.text : d.text)
          }
          if (d.done) stop()
        } catch { /* 忽略坏帧 */ }
      }
      asrWs.onerror = () => {
        if (isRecording.value) onError?.('语音识别连接失败，请重试')
      }
    } catch (e) {
      console.error('录音失败:', e)
      releaseMedia()
      isRecording.value = false
      onError?.('无法访问麦克风，请检查浏览器权限')
    }
  }

  function stop() {
    if (asrWs && asrWs.readyState === WebSocket.OPEN) {
      asrWs.send(JSON.stringify({ status: 2, audio: '' }))
    }
    isRecording.value = false
    releaseMedia()
    // 后端会在最终结果后关闭连接；兜底 4s 后强制关闭
    clearTimeout(closeTimer)
    closeTimer = setTimeout(() => {
      if (asrWs && asrWs.readyState !== WebSocket.CLOSED) {
        try { asrWs.close() } catch {}
      }
      asrWs = null
    }, 4000)
    onDone?.()
  }

  function releaseMedia() {
    if (scriptNode) { try { scriptNode.disconnect() } catch {} ; scriptNode = null }
    if (audioCtx) { audioCtx.close().catch(() => {}); audioCtx = null }
    if (mediaStream) { mediaStream.getTracks().forEach(t => t.stop()); mediaStream = null }
  }

  return { isRecording, start, stop }
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

// 浏览器未按 16k 建上下文时线性降采样（分块近似，对 ASR 足够）
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
