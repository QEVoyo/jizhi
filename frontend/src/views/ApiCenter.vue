<template>
  <div class="api-center-page">
    <div class="ac-wrap">
      <!-- ===== 返回 ===== -->
      <button class="back-btn" @click="goBack">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg>
        返回主界面
      </button>

      <!-- ===== 页头 ===== -->
      <div class="ac-header">
        <div>
          <h1 class="ac-title">API 模型中心</h1>
          <p class="ac-subtitle">本站 AI 能力背后的模型一览 · 官方已接入的无需配置 · 点击卡片展开详情，可重播演示</p>
        </div>
      </div>

      <!-- ===== 概览条 ===== -->
      <div class="ac-overview">
        <div class="ov-tile">
          <span class="ov-label">已接入平台</span>
          <strong class="ov-value">{{ officialCount }} / {{ models.length }}</strong>
        </div>
        <div class="ov-tile">
          <span class="ov-label">文本主力</span>
          <strong class="ov-value">DeepSeek V4.1 Flash</strong>
        </div>
        <div class="ov-tile">
          <span class="ov-label">视觉模型</span>
          <strong class="ov-value">V4.1 Flash（原生多模态）</strong>
        </div>
        <div class="ov-tile">
          <span class="ov-label">语音 / 视频</span>
          <strong class="ov-value">千问 · 讯飞 · 腾讯</strong>
        </div>
      </div>

      <!-- ===== 模型画廊（预览形式） ===== -->
      <div class="model-grid">
        <article
          v-for="m in models" :key="m.id"
          class="model-card"
          :class="{ expanded: expanded === m.id, official: m.official }"
          @click="toggle(m.id)"
        >
          <div class="mc-head">
            <div class="mc-badge" :style="{ background: m.grad }">{{ m.badge }}</div>
            <div class="mc-id">
              <div class="mc-name-row">
                <h3 class="mc-name">{{ m.name }}</h3>
                <span class="mc-status" :class="m.official ? 'on' : 'self'">{{ m.official ? '官方已接入' : '可自配 Key' }}</span>
              </div>
              <span class="mc-model-id">{{ m.modelId }} · {{ m.vendor }}</span>
            </div>
            <span class="mc-expand">{{ expanded === m.id ? '收起 ▲' : '详情 ▼' }}</span>
          </div>

          <!-- 能力标签 -->
          <div class="mc-chips">
            <span v-for="c in m.capabilities" :key="c" class="mc-chip">{{ c }}</span>
          </div>

          <p class="mc-desc">{{ m.desc }}</p>

          <!-- 预览 -->
          <div class="mc-preview">
            <span class="mp-label">预览 · {{ m.preview.label }}</span>

            <!-- 对话式（展开时打字重播） -->
            <template v-if="m.preview.type === 'chat'">
              <div class="pv-msg q">
                <span class="pv-avatar pv-me">我</span>
                <div class="pv-bubble pv-q">{{ m.preview.question }}</div>
              </div>
              <div class="pv-msg a">
                <img class="pv-avatar pv-xj" :src="isTyping(m) ? '/images/xiaoji/xiaoji_speaking.png' : '/images/xiaoji/xiaoji_idle.png'" alt="小基" />
                <div class="pv-bubble pv-a">
                  {{ answerOf(m) }}<span v-if="isTyping(m)" class="pv-caret">▌</span>
                </div>
              </div>
              <div class="pv-hint" v-if="expanded !== m.id">点击卡片展开，小基演示打字回答</div>
            </template>

            <!-- 识图 -->
            <template v-else-if="m.preview.type === 'vision'">
              <div class="pv-vision">
                <div class="pv-photo">
                  <p>Scientists have long known that sleep plays a key role in memory.</p>
                  <p>New research shows that during deep sleep, the brain replays the day's events…</p>
                  <p class="pv-photo-q">Q3. What does the study mainly tell us?</p>
                  <span class="pv-photo-foot">📷 示例题目截图 · 第 3 题</span>
                </div>
                <div class="pv-msg a">
                  <img class="pv-avatar pv-xj" src="/images/xiaoji/xiaoji_idle.png" alt="小基" />
                  <div class="pv-bubble pv-a">{{ m.preview.output }}</div>
                </div>
              </div>
            </template>

            <!-- 语音合成（真实小基声音） -->
            <template v-else-if="m.preview.type === 'tts'">
              <div class="pv-tts">
                <span class="pv-io">输入："{{ m.preview.text }}"</span>
                <button class="pv-play" :class="{ playing: tts.playing }" @click.stop="playTTS(m)">
                  <span class="pv-play-icon">{{ tts.playing ? '❚❚' : (tts.loading ? '…' : '▶') }}</span>
                  <span class="pv-wave" v-if="tts.playing"><i></i><i></i><i></i><i></i></span>
                  <span class="pv-dur">{{ durLabel }}</span>
                </button>
                <span class="pv-tts-note">真实小基声音 · 千问在线合成</span>
              </div>
            </template>

            <!-- 状态 -->
            <template v-else-if="m.preview.type === 'status'">
              <div class="pv-status">
                <span v-for="l in m.preview.lines" :key="l" class="pv-status-line">{{ l }}</span>
              </div>
            </template>

            <!-- 数字人视频 -->
            <template v-else>
              <span class="pv-io">输入：{{ m.preview.text }}</span>
              <div class="pv-video-frame" @click.stop="ElMessage.info('数字人视频能力占位中，上线后启用')">
                <span class="pv-video-play">▶</span>
                <span class="pv-video-tip">数字人讲解视频 · 上线后展示</span>
              </div>
            </template>
          </div>

          <!-- 自配 Key 详情（可自配模型） -->
          <div v-if="expanded === m.id && !m.official" class="mc-config" @click.stop>
            <template v-for="f in m.configFields" :key="f.key">
              <div class="cfg-row">
                <span class="cfg-label">{{ f.label }}</span>
                <el-input
                  v-model="keys[m.id][f.key]"
                  :type="f.secret ? 'password' : 'text'"
                  :placeholder="f.placeholder"
                  size="small"
                  class="cfg-input"
                  show-password
                />
              </div>
            </template>
            <div class="cfg-actions">
              <el-button size="small" type="primary" plain @click="saveKeys(m)">保存到本地</el-button>
              <span class="cfg-note">演示说明：实际 AI 调用走后端 .env 配置的官方 Key，此处配置留作备用通道</span>
            </div>
          </div>

          <!-- 官方模型详情 -->
          <div v-if="expanded === m.id && m.official" class="mc-config official-note" @click.stop>
            <p>✅ 该模型由平台官方 Key 统一接入（后端 .env），全站功能开箱即用，无需单独配置。</p>
          </div>
        </article>
      </div>

      <!-- ===== 底部 ===== -->
      <div class="ac-footer">
        <p>💡 语音输入转文字使用浏览器内置能力，无需配置</p>
        <p>不知道怎么获取 Key？<span class="link" @click="goQA">查看 Q&A 指南 →</span></p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

const router = useRouter()

// ===== 模型清单（与后端实际接入保持一致） =====
const models = ref([
  {
    id: 'deepseek-chat', name: 'DeepSeek V4.1 Flash', vendor: 'DeepSeek',
    badge: 'DS', modelId: 'deepseek-flash（V4.1 Flash）',
    grad: 'linear-gradient(145deg, rgba(71,118,230,.45), rgba(142,84,233,.45))',
    official: true,
    capabilities: ['AI 对话', '学习规划', '题目生成', '评估批改', '小基聊天'],
    desc: '全站文本任务主力模型：对话答疑、备考规划、出题、批改全部由它驱动。2026-09-10 升级至 V4.1 Flash（思考模式默认关，首字约 0.6s）。',
    preview: {
      type: 'chat', label: '示例（对话）',
      question: '定语从句和同位语从句怎么区分？',
      answer: '看引导词在从句中是否作成分——作成分是定语从句（that/which 可省），不作成分是同位语从句（that 不可省）。例：The news that he won made us happy 中 that 无成分，是同位语从句。',
    },
  },
  {
    id: 'deepseek-vision', name: 'DeepSeek 识图', vendor: 'DeepSeek',
    badge: 'V', modelId: 'deepseek-flash（原生多模态）',
    grad: 'linear-gradient(145deg, rgba(38,208,206,.45), rgba(71,118,230,.45))',
    official: true,
    capabilities: ['图片理解', '拍题识别', '小基识图'],
    desc: '与文本同一个模型（V4.1 Flash 原生多模态，2026-09-10 由 V4-Flash-Vision 实验版切换）：图文混合输入，图片按 Token 计费（单张最多 384 tokens）。',
    preview: {
      type: 'vision', label: '示例（识图）',
      output: '这是关于「睡眠与记忆巩固」的说明文，第 3 题问的是实验结论：睡眠会巩固白天的记忆。',
    },
  },
  {
    id: 'volc', name: '豆包（火山方舟）', vendor: '火山引擎',
    badge: '豆', modelId: 'Ark endpoint 接入',
    grad: 'linear-gradient(145deg, rgba(251,146,60,.45), rgba(250,204,21,.40))',
    official: true,
    capabilities: ['对话备用通道'],
    desc: '历史对话通道保留，作为 DeepSeek 不可用时的降级备用。视觉通道已于 09-10 并入 DeepSeek V4.1 Flash（文本与识图同一模型）。',
    preview: {
      type: 'status', label: '状态',
      lines: ['⚡ 主链路：DeepSeek V4.1 Flash', '🛡️ 待命备用 · 主链路正常时不被调用'],
    },
  },
  {
    id: 'qwen-voice', name: '千问语音', vendor: '阿里云',
    badge: '千', modelId: 'TTS-Plus / Realtime',
    grad: 'linear-gradient(145deg, rgba(168,85,247,.45), rgba(236,72,153,.40))',
    official: true,
    capabilities: ['语音合成', '语音通话', '小基语音'],
    desc: '小基语音的声音来源：文字转语音（qwen-audio-3.0-tts-plus）与实时语音通话（qwen-audio-3.0-realtime-plus）。语音输入听写仍走讯飞 iat。',
    preview: {
      type: 'tts', label: '示例（TTS）',
      text: '今天也要加油哦！',
    },
  },
  {
    id: 'tencent', name: '腾讯云数字人', vendor: '腾讯云',
    badge: '腾', modelId: '数字人视频生成',
    grad: 'linear-gradient(145deg, rgba(99,102,241,.45), rgba(38,208,206,.45))',
    official: false,
    capabilities: ['数字人视频'],
    desc: '每日任务「视频推送」的数字人讲解视频生成能力（功能占位中，上线后启用）。',
    preview: {
      type: 'video', label: '示例',
      text: '今日学习讲解文本',
    },
    configFields: [
      { key: 'secretId', label: 'SecretId', secret: false, placeholder: 'AKIDxxxx' },
      { key: 'secretKey', label: 'SecretKey', secret: true, placeholder: 'xxxx' },
    ],
  },
  {
    id: 'zhipu', name: '智谱 GLM', vendor: '智谱 AI',
    badge: '智', modelId: 'GLM 系列',
    grad: 'linear-gradient(145deg, rgba(19,78,94,.45), rgba(113,178,128,.45))',
    official: false,
    capabilities: ['出题备用通道'],
    desc: '题目生成的备用通道：配置自己的 Key 后可作为 DeepSeek 之外的第二选择。',
    preview: {
      type: 'chat', label: '示例（出题）',
      question: '知识点「时态语态」· 难度 5 · 来一道四选一',
      answer: 'By the time he arrives, the meeting ____ for an hour.\nA. has begun  B. will have begun  C. had begun  D. will have been on\n答案 B。by the time 从句用一般现在时表将来，主句用将来完成时 will have done。',
    },
    configFields: [
      { key: 'apiKey', label: 'API Key', secret: true, placeholder: 'xxxxxxxx' },
    ],
  },
])

const officialCount = computed(() => models.value.filter(m => m.official).length)
const expanded = ref('')

// ===== 打字动画（展开卡片时重播演示） =====
const typing = ref({})
const timers = {}
function startTyping(m) {
  const full = m.preview?.answer || ''
  stopTyping(m.id)
  typing.value[m.id] = ''
  let i = 0
  timers[m.id] = setInterval(() => {
    i = Math.min(i + 2, full.length)
    typing.value[m.id] = full.slice(0, i)
    if (i >= full.length) stopTyping(m.id)
  }, 20)
}
function stopTyping(id) {
  clearInterval(timers[id])
  delete timers[id]
}
function isTyping(m) {
  return expanded.value === m.id && (typing.value[m.id] ?? '') !== (m.preview?.answer || '')
}
function answerOf(m) {
  return expanded.value === m.id ? (typing.value[m.id] ?? '') : (m.preview?.answer || '')
}
function toggle(id) {
  const wasOpen = expanded.value === id
  expanded.value = wasOpen ? '' : id
  const m = models.value.find(x => x.id === id)
  if (!wasOpen && m?.preview?.type === 'chat') startTyping(m)
  else if (wasOpen) stopTyping(id)
}

// ===== 自配 Key（localStorage 持久化，演示用） =====
const STORAGE_KEY = 'apicenter-keys'
const keys = ref({})
onMounted(() => {
  try {
    keys.value = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}')
  } catch {
    keys.value = {}
  }
  models.value.forEach(m => {
    if (!keys.value[m.id]) keys.value[m.id] = {}
  })
})

function saveKeys(m) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(keys.value))
  ElMessage.success(`${m.name} 配置已保存到本地（演示）`)
}

// ===== 千问 TTS 预览（真实小基声音，取回后缓存复用） =====
const tts = ref({ loading: false, playing: false, url: null, duration: null })
const ttsAudio = new Audio()
async function playTTS(m) {
  if (tts.value.loading) return
  if (tts.value.playing) {
    ttsAudio.pause()
    tts.value.playing = false
    return
  }
  if (tts.value.url) {
    try { await ttsAudio.play(); tts.value.playing = true } catch { /* 忽略 */ }
    return
  }
  tts.value.loading = true
  try {
    const res = await request.post('/xiaoji/tts', { text: m.preview.text })
    const base64 = res.data?.audio_base64
    if (!base64) throw new Error('empty audio')
    const bin = atob(base64)
    const bytes = new Uint8Array(bin.length)
    for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i)
    const url = URL.createObjectURL(new Blob([bytes], { type: 'audio/mpeg' }))
    tts.value.url = url
    ttsAudio.src = url
    ttsAudio.onloadedmetadata = () => { tts.value.duration = ttsAudio.duration }
    ttsAudio.onended = () => { tts.value.playing = false }
    await ttsAudio.play()
    tts.value.playing = true
  } catch {
    tts.value.playing = false
    ElMessage.error('语音预览加载失败，请稍后再试')
  } finally {
    tts.value.loading = false
  }
}
function fmtDur(s) {
  s = Math.round(s)
  return `0:${String(s).padStart(2, '0')}`
}
const durLabel = computed(() => tts.value.duration ? fmtDur(tts.value.duration) : '0:03')

onBeforeUnmount(() => {
  Object.keys(timers).forEach(id => stopTyping(id))
  ttsAudio.pause()
  if (tts.value.url) URL.revokeObjectURL(tts.value.url)
})

function goBack() {
  router.push('/home')
}

function goQA() {
  router.push('/qa')
}
</script>

<style scoped>
.api-center-page {
  min-height: 100vh;
  padding: 30px 20px;
  }

.ac-wrap {
  max-width: 1000px;
  margin: 0 auto;
  padding: 24px 28px 32px;
  border-radius: 18px;
  background: color-mix(in srgb, var(--surface, #ffffff) 6%, transparent);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid var(--line-soft);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.06);
}
[data-theme="dark"] .ac-wrap { background: var(--well); }
[data-theme="light"] .ac-wrap { background: color-mix(in srgb, var(--surface, #ffffff) 82%, transparent); }

.back-btn {
  display: inline-flex; align-items: center; gap: 6px;
  background: transparent; border: none; color: var(--text-secondary);
  font-size: 13px; cursor: pointer; padding: 4px 8px; border-radius: 8px;
  transition: all .2s ease; font-family: inherit; margin-bottom: 14px;
}
.back-btn svg { width: 16px; height: 16px; }
.back-btn:hover { color: var(--text-primary); background: color-mix(in srgb, var(--surface, #ffffff) 6%, transparent); transform: translateX(-2px); }
[data-theme="light"] .back-btn:hover { background: rgba(15,23,42,.05); }

.ac-title { font-size: 24px; font-weight: 700; color: var(--text-primary); margin: 0; }
.ac-subtitle { font-size: 13px; color: var(--text-secondary); margin: 6px 0 0; }

/* 概览条 */
.ac-overview { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 20px 0; }
.ov-tile {
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent); border: 1px solid rgba(255,255,255,.06);
  border-radius: 12px; padding: 12px 14px; display: flex; flex-direction: column; gap: 4px;
}
[data-theme="light"] .ov-tile { background: rgba(15,23,42,.02); border-color: rgba(15,23,42,.07); }
.ov-label { font-size: 11px; color: var(--text-muted); }
.ov-value { font-size: 15px; font-weight: 700; color: var(--text-primary); }

/* 模型画廊 */
.model-grid { display: flex; flex-direction: column; gap: 14px; }
.model-card {
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent); border: 1px solid rgba(255,255,255,.06);
  border-radius: 14px; padding: 16px 18px; cursor: pointer;
  transition: border-color .2s ease, transform .2s ease;
}
[data-theme="light"] .model-card { background: rgba(15,23,42,.02); border-color: rgba(15,23,42,.07); }
.model-card:hover { border-color: var(--line); }
[data-theme="light"] .model-card:hover { border-color: rgba(15,23,42,.16); }
.model-card.expanded { border-color: color-mix(in srgb, var(--brand) 40%, transparent); }
.model-card.official:hover { transform: none; }

.mc-head { display: flex; align-items: center; gap: 12px; }
.mc-badge {
  width: 42px; height: 42px; border-radius: 11px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 16px; font-weight: 700; color: #fff;
  border: 1px solid rgba(255,255,255,.12);
}
.mc-id { flex: 1; min-width: 0; }
.mc-name-row { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.mc-name { font-size: 15px; font-weight: 700; color: var(--text-primary); margin: 0; }
.mc-status {
  font-size: 11px; font-weight: 600; padding: 1px 8px; border-radius: 8px;
}
.mc-status.on { color: var(--viz-good, #0ca30c); background: rgba(12,163,12,.10); }
.mc-status.self { color: var(--brand-bright); background: color-mix(in srgb, var(--brand) 10%, transparent); }
.mc-model-id { font-size: 11px; color: var(--text-muted); display: block; margin-top: 2px; font-variant-numeric: tabular-nums; }
.mc-expand { font-size: 12px; color: var(--text-muted); flex-shrink: 0; }

.mc-chips { display: flex; flex-wrap: wrap; gap: 6px; margin: 10px 0 8px; }
.mc-chip {
  font-size: 11px; color: var(--text-secondary); padding: 2px 10px;
  border-radius: 20px; background: color-mix(in srgb, var(--surface, #ffffff) 5%, transparent); border: 1px solid var(--line-soft);
}
[data-theme="light"] .mc-chip { background: rgba(15,23,42,.04); border-color: rgba(15,23,42,.08); }

.mc-desc { font-size: 12px; color: var(--text-secondary); line-height: 1.6; margin: 0 0 10px; }

/* 预览 */
.mc-preview {
  background: rgba(0,0,0,.18); border: 1px solid rgba(255,255,255,.06);
  border-radius: 10px; padding: 10px 12px;
}
[data-theme="light"] .mc-preview { background: rgba(15,23,42,.03); border-color: rgba(15,23,42,.06); }
.mp-label { font-size: 10px; color: var(--text-muted); display: block; margin-bottom: 8px; letter-spacing: .04em; }

/* 对话气泡 */
.pv-msg { display: flex; align-items: flex-start; gap: 8px; margin-bottom: 8px; }
.pv-msg:last-child { margin-bottom: 0; }
.pv-msg.q { justify-content: flex-end; }
.pv-msg.q .pv-avatar { order: 2; }
.pv-avatar {
  width: 26px; height: 26px; border-radius: 50%; flex-shrink: 0;
  display: inline-flex; align-items: center; justify-content: center;
}
.pv-me {
  background: linear-gradient(145deg, #5b8cff, #7a5bff); color: #fff;
  font-size: 11px; font-weight: 700;
}
.pv-xj { border: 1px solid var(--line-strong); background: color-mix(in srgb, var(--surface, #ffffff) 8%, transparent); object-fit: cover; }
.pv-bubble {
  max-width: 82%; font-size: 12px; line-height: 1.65; padding: 7px 11px;
  border-radius: 12px; white-space: pre-line; word-break: break-word;
}
.pv-q {
  background: linear-gradient(145deg, rgba(91,140,255,.28), rgba(122,91,255,.22));
  border: 1px solid rgba(91,140,255,.35); border-bottom-right-radius: 4px;
  color: var(--text-primary);
}
.pv-a {
  background: color-mix(in srgb, var(--surface, #ffffff) 7%, transparent); border: 1px solid var(--line-soft);
  border-bottom-left-radius: 4px; color: var(--viz-ink-2, #c3c2b7); min-height: 20px;
}
[data-theme="light"] .pv-a { background: rgba(15,23,42,.04); border-color: rgba(15,23,42,.08); color: var(--text-secondary); }
.pv-caret { animation: pv-blink 1s steps(1) infinite; color: var(--brand-bright); }
@keyframes pv-blink { 50% { opacity: 0; } }
.pv-hint { font-size: 10px; color: var(--text-muted); margin-top: 8px; text-align: right; }

/* 识图 */
.pv-vision { display: flex; gap: 10px; align-items: flex-start; flex-wrap: wrap; }
.pv-photo {
  background: #f5f1e8; color: #4a4238; border-radius: 10px; padding: 12px 14px;
  box-shadow: 0 4px 14px rgba(0,0,0,.25); transform: rotate(-1.2deg);
  max-width: 46%; min-width: 220px; border: 1px solid rgba(0,0,0,.08);
}
.pv-photo p {
  font-family: Georgia, 'Times New Roman', serif; font-size: 12px;
  line-height: 1.7; margin: 0 0 6px;
}
.pv-photo .pv-photo-q { font-weight: 700; color: #2c3e50; margin: 0; }
.pv-photo-foot { font-size: 10px; color: #a89f8e; margin-top: 6px; display: block; letter-spacing: .05em; }
.pv-vision .pv-msg { flex: 1; min-width: 200px; margin-bottom: 0; }

/* TTS */
.pv-tts { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.pv-io { font-size: 12px; color: var(--text-secondary); }
.pv-play {
  display: inline-flex; align-items: center; gap: 8px; cursor: pointer;
  background: linear-gradient(145deg, rgba(168,85,247,.35), rgba(236,72,153,.30));
  border: 1px solid rgba(216,99,245,.45); color: #fff;
  font-size: 12px; font-weight: 600; padding: 6px 14px; border-radius: 20px;
  transition: all .2s ease; font-family: inherit;
}
.pv-play:hover { transform: translateY(-1px); box-shadow: 0 4px 14px rgba(216,99,245,.35); }
.pv-play-icon { font-size: 11px; }
.pv-wave { display: inline-flex; align-items: flex-end; gap: 2px; height: 14px; }
.pv-wave i { width: 2px; background: #fff; border-radius: 1px; animation: pv-eq .9s ease-in-out infinite; }
.pv-wave i:nth-child(1) { height: 6px; }
.pv-wave i:nth-child(2) { height: 12px; animation-delay: .15s; }
.pv-wave i:nth-child(3) { height: 9px; animation-delay: .3s; }
.pv-wave i:nth-child(4) { height: 14px; animation-delay: .45s; }
@keyframes pv-eq { 0%, 100% { transform: scaleY(.5); } 50% { transform: scaleY(1); } }
.pv-dur { font-size: 11px; opacity: .85; font-variant-numeric: tabular-nums; }
.pv-tts-note { font-size: 10px; color: var(--text-muted); }

/* 状态 */
.pv-status { display: flex; flex-direction: column; gap: 6px; }
.pv-status-line { font-size: 12px; color: var(--viz-ink-2, #c3c2b7); }

/* 数字人视频 */
.pv-video .pv-io { display: block; margin-bottom: 8px; }
.pv-video-frame {
  aspect-ratio: 16 / 9; border-radius: 10px; position: relative; overflow: hidden;
  background: linear-gradient(145deg, #1e2440 0%, #31205a 55%, #123a46 100%);
  display: flex; align-items: center; justify-content: center; cursor: pointer;
  border: 1px solid rgba(255,255,255,.10);
}
.pv-video-frame::before {
  content: ''; position: absolute; inset: 0;
  background: radial-gradient(circle at 30% 40%, rgba(99,102,241,.35), transparent 60%),
              radial-gradient(circle at 75% 65%, rgba(38,208,206,.25), transparent 55%);
}
.pv-video-play {
  width: 46px; height: 46px; border-radius: 50%; position: relative;
  background: color-mix(in srgb, var(--surface, #ffffff) 14%, transparent); border: 1px solid rgba(255,255,255,.35);
  backdrop-filter: blur(6px); display: flex; align-items: center; justify-content: center;
  font-size: 16px; color: var(--text-primary); transition: all .2s ease;
}
.pv-video-frame:hover .pv-video-play { background: color-mix(in srgb, var(--surface, #ffffff) 25%, transparent); transform: scale(1.08); }
.pv-video-tip {
  position: absolute; bottom: 8px; left: 0; right: 0; text-align: center;
  font-size: 10px; color: rgba(255,255,255,.75);
}

/* 配置详情 */
.mc-config { margin-top: 12px; border-top: 1px dashed rgba(128,128,128,.2); padding-top: 12px; }
.cfg-row { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.cfg-label { font-size: 12px; color: var(--text-secondary); width: 80px; flex-shrink: 0; }
.cfg-input { flex: 1; }
.cfg-actions { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.cfg-note { font-size: 11px; color: var(--text-muted); flex: 1; min-width: 200px; line-height: 1.5; }
.official-note p { font-size: 12px; color: var(--text-secondary); margin: 0; line-height: 1.6; }

/* 底部 */
.ac-footer { margin-top: 20px; text-align: center; font-size: 12px; color: var(--text-muted); line-height: 1.8; }
.link { color: var(--brand-bright); cursor: pointer; }
.link:hover { text-decoration: underline; }

@media (max-width: 700px) {
  .ac-wrap { padding: 16px 14px 24px; }
  .ac-overview { grid-template-columns: repeat(2, 1fr); }
}
</style>
