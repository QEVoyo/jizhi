// ===== 分镜视频·离线快速导出（2026-09-05 用户定调：要快、画质要清）
// WebCodecs 离屏编码管线：渲染一帧交一帧，编码器满载跑，不受视频时长束缚——
// 45 秒视频十几秒出片（MediaRecorder 实时录制才≈视频时长，已降级为兜底）。
// 输出 webm:vp8 + opus(48k 单声道)。

import { drawFrame } from './videoRender'

export function supportsFastExport() {
  return typeof window !== 'undefined' &&
    typeof VideoEncoder !== 'undefined' &&
    typeof AudioEncoder !== 'undefined' &&
    (typeof window.AudioContext !== 'undefined' || typeof window.webkitAudioContext !== 'undefined')
}

const FPS = 15
const W = 1280
const H = 720
const VIDEO_BITRATE = 3_000_000
const AUDIO_BITRATE = 96_000

export async function exportStoryboardVideo(video, { onProgress } = {}) {
  if (!supportsFastExport()) throw new Error('浏览器不支持 WebCodecs 快速导出')
  const url = video.audio_url
  if (!url) throw new Error('音轨还没生成')

  onProgress && onProgress(1)

  // ① 音轨：fetch → 解码 → 重采样 48k 单声道（离线，不受实时限制）
  const resp = await fetch(url)
  if (!resp.ok) throw new Error('音轨拉取失败 HTTP ' + resp.status)
  const AC = window.AudioContext || window.webkitAudioContext
  const ac = new AC()
  const raw = await ac.decodeAudioData(await resp.arrayBuffer())
  const dur = raw.duration
  onProgress && onProgress(4)

  const offline = new OfflineAudioContext(1, Math.ceil(dur * 48000), 48000)
  const src = offline.createBufferSource()
  src.buffer = raw
  src.connect(offline.destination)
  src.start()
  const rendered = await offline.startRendering()   // 快于实时
  const pcm = rendered.getChannelData(0)            // Float32 单声道
  await ac.close()
  onProgress && onProgress(10)

  // ② muxer + 编码器
  const { Muxer, ArrayBufferTarget } = await import('webm-muxer')
  const muxer = new Muxer({
    target: new ArrayBufferTarget(),
    video: { codec: 'V_VP8', width: W, height: H, frameRate: FPS },
    audio: { codec: 'A_OPUS', sampleRate: 48000, numberOfChannels: 1 },
    firstTimestampBehavior: 'offset',
  })

  const vEnc = new VideoEncoder({
    output: (chunk, meta) => muxer.addVideoChunk(chunk, meta),
    error: (e) => console.error('VideoEncoder:', e),
  })
  vEnc.configure({ codec: 'vp8', width: W, height: H, bitrate: VIDEO_BITRATE, framerate: FPS })

  const aEnc = new AudioEncoder({
    output: (chunk, meta) => muxer.addAudioChunk(chunk, meta),
    error: (e) => console.error('AudioEncoder:', e),
  })
  aEnc.configure({ codec: 'opus', sampleRate: 48000, numberOfChannels: 1, bitrate: AUDIO_BITRATE })

  // ③ 音频分片编码（0.5s 一块，离屏速跑）
  const step = Math.floor(48000 * 0.5)
  for (let i = 0; i * step < pcm.length; i++) {
    const plane = new Float32Array(step)
    plane.set(pcm.subarray(i * step, Math.min(pcm.length, (i + 1) * step)))
    // 单声道用交织 f32（planar 在部分内核要求跨域隔离，实测 Edge152 headless 报 data 类型错）
    const ad = new AudioData({
      format: 'f32',
      sampleRate: 48000,
      numberOfFrames: plane.length,
      numberOfChannels: 1,
      timestamp: Math.round(i * step * 1e6 / 48000),
      data: plane,
    })
    aEnc.encode(ad)
    ad.close()
    if (aEnc.encodeQueueSize > 8) {
      await new Promise((res) => aEnc.addEventListener('dequeue', res, { once: true }))
    }
    if (i % 8 === 7) await new Promise((res) => setTimeout(res))
  }
  await aEnc.flush()
  aEnc.close()
  onProgress && onProgress(18)

  // ④ 视频逐帧渲染 + 编码（背压控制，比实时快）
  const canvas = document.createElement('canvas')
  canvas.width = W
  canvas.height = H
  const ctx = canvas.getContext('2d')
  const totalFrames = Math.max(1, Math.round(dur * FPS))
  const usPerFrame = Math.round(1e6 / FPS)
  const renderVideo = { ...video, audio_duration: dur }

  for (let i = 0; i < totalFrames; i++) {
    const t = Math.min(dur, (i + 0.5) / FPS)
    drawFrame(ctx, renderVideo, t, W, H)
    const vf = new VideoFrame(canvas, { timestamp: i * usPerFrame, duration: usPerFrame })
    vEnc.encode(vf, { keyFrame: i % (FPS * 2) === 0 })
    vf.close()
    if (vEnc.encodeQueueSize > 6) {
      await new Promise((res) => vEnc.addEventListener('dequeue', res, { once: true }))
    }
    if (i % 3 === 2) await new Promise((res) => setTimeout(res)) // 让出主线程给编码
    onProgress && onProgress(Math.round(18 + ((i + 1) / totalFrames) * 62))
  }
  await vEnc.flush()
  vEnc.close()

  // ⑤ 封包
  muxer.finalize()
  onProgress && onProgress(100)
  return new Blob([muxer.target.buffer], { type: 'video/webm' })
}