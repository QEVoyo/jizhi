// ===== 分镜视频·原生 canvas 渲染器（2026-09-05）
// 不依赖 DOM / html2canvas：拿 scenes 脚本直接在 canvas 上矢量绘制每一帧，
// 导出画质锐利、性能接近实时（上一版截屏方案已废弃）。
// 时间轴口径与 VideoLessonPlayer 完全一致（字数加权分镜时间轴 + 6.2 字/秒语速校准）。

const MOOD_ACCENT = {
  lecture: { color: '#5ed0ff', glow: 'rgba(94,208,255,.35)' },
  story: { color: '#ffb84d', glow: 'rgba(255,184,77,.35)' },
  highlight: { color: '#ff5c7a', glow: 'rgba(255,92,122,.35)' },
  demo: { color: '#b48cff', glow: 'rgba(180,140,255,.35)' },
}

// 10 套皮肤调色板（与播放器 CSS 皮肤同源）
export const SKIN_PALETTES = {
  chalkboard: { bgA: '#1e5637', bgB: '#0c251a', ink: '#f2f7e8', dim: 'rgba(232,240,218,.72)', panel: 'rgba(255,255,255,.08)', line: 'rgba(240,246,228,.6)', font: '"KaiTi","STKaiti","楷体","SimSun",serif', deco: 'chalk', border: '#6b4a2a' },
  paper: { bgA: '#faf4e8', bgB: '#f2ead6', ink: '#3a3226', dim: 'rgba(58,50,38,.72)', panel: 'rgba(255,252,240,.85)', line: '#d8c9a8', font: '"KaiTi","STKaiti","楷体","SimSun",serif', deco: 'paper', border: 'rgba(229,120,120,.45)' },
  whiteboard: { bgA: '#f6f9fd', bgB: '#eef3fa', ink: '#1d2c4c', dim: 'rgba(35,54,92,.75)', panel: '#ffffff', line: '#b9cdf0', font: '"Microsoft YaHei","PingFang SC",sans-serif', deco: 'plain', border: '#b9cdf0' },
  chat: { bgA: '#e9edf3', bgB: '#dfe5ee', ink: '#1f2733', dim: 'rgba(31,39,51,.75)', panel: '#ffffff', line: '#c9d4e2', font: '"Microsoft YaHei","PingFang SC",sans-serif', deco: 'chat', border: '#4d8dff' },
  qa: { bgA: '#241b52', bgB: '#0d0926', ink: '#efeaff', dim: 'rgba(239,234,255,.7)', panel: 'rgba(255,255,255,.08)', line: 'rgba(255,255,255,.25)', font: '"Microsoft YaHei","PingFang SC",sans-serif', deco: 'bigq', border: '#8b5cff' },
  fun: { bgA: '#ffe9c7', bgB: '#ffd9e8', ink: '#4a2f55', dim: 'rgba(61,42,85,.75)', panel: '#ffffff', line: '#7c5cff', font: '"Microsoft YaHei","PingFang SC",sans-serif', deco: 'sparkle', border: '#7c5cff' },
  neon: { bgA: '#04060f', bgB: '#04060f', ink: '#d9f6ff', dim: 'rgba(160,220,240,.66)', panel: 'rgba(8,18,30,.85)', line: 'rgba(94,208,255,.55)', font: '"Microsoft YaHei","PingFang SC",sans-serif', deco: 'grid', border: 'rgba(94,208,255,.5)' },
  mindmap: { bgA: '#f6f8f3', bgB: '#eef3ea', ink: '#2c4233', dim: 'rgba(44,66,51,.78)', panel: '#ffffff', line: '#7fb98c', font: '"Microsoft YaHei","PingFang SC",sans-serif', deco: 'mind', border: '#7fb98c' },
  glass: { bgA: '#0d1220', bgB: '#0d1220', ink: '#eef2fb', dim: 'rgba(223,231,245,.6)', panel: 'rgba(255,255,255,.1)', line: 'rgba(255,255,255,.24)', font: '"Microsoft YaHei","PingFang SC",sans-serif', deco: 'glass', border: 'rgba(255,255,255,.24)' },
  compare: { bgA: '#0d1220', bgB: '#0d1220', ink: '#eef2fb', dim: 'rgba(223,231,245,.6)', panel: 'rgba(255,255,255,.08)', line: 'rgba(255,255,255,.2)', font: '"Microsoft YaHei","PingFang SC",sans-serif', deco: 'split', border: 'rgba(255,255,255,.25)' },
}

// 与播放器同款的皮肤配对（双皮肤交替）
const SKIN_PAIRS = {
  chalkboard: 'paper', paper: 'chalkboard',
  whiteboard: 'mindmap', mindmap: 'whiteboard',
  chat: 'qa', qa: 'fun', fun: 'paper',
  neon: 'glass', glass: 'neon', compare: 'glass',
}

function skinOf(video, t, hookActive) {
  const key = (['chalkboard', 'paper', 'whiteboard', 'chat', 'qa', 'fun', 'neon', 'mindmap', 'glass', 'compare'].includes(video.template_key))
    ? video.template_key : (video.template_key === 'cards' ? 'glass' : 'glass')
  if (hookActive) return SKIN_PAIRS[key] || 'glass'
  const times = sceneTimes(video)
  const idx = sceneIdxAt(t, times)
  return (idx % 2 === 0) ? key : (SKIN_PAIRS[key] || 'glass')
}

// ==================== 时间轴（与播放器同口径）====================
export function sceneTimes(video) {
  const script = video.script || {}
  const scenes = Array.isArray(script.scenes) ? script.scenes : []
  if (!scenes.length) return []
  const dur = duration(video)
  const chars = scenes.map(s => Math.max(1, String(s.narration || '').length))
  const total = chars.reduce((a, b) => a + b, 0)
  let acc = 0
  return chars.map(c => {
    const start = (acc / total) * dur
    acc += c
    return { start, end: (acc / total) * dur }
  })
}
function sceneIdxAt(t, times) {
  let i = 0
  while (i < times.length - 1 && t >= times[i].end) i++
  return i
}
export function duration(video) {
  return Number(video.audio_duration) || 90
}

// ==================== 文本工具 ====================
function wrapText(ctx, text, maxW) {
  const out = []
  let line = ''
  for (const ch of String(text || '')) {
    const test = line + ch
    if (ctx.measureText(test).width > maxW && line) {
      out.push(line)
      line = ch
    } else line = test
  }
  if (line) out.push(line)
  return out
}
function roundRect(ctx, x, y, w, h, r) {
  const rr = Math.min(r, w / 2, h / 2)
  ctx.beginPath()
  ctx.moveTo(x + rr, y)
  ctx.arcTo(x + w, y, x + w, y + h, rr)
  ctx.arcTo(x + w, y + h, x, y + h, rr)
  ctx.arcTo(x, y + h, x, y, rr)
  ctx.arcTo(x, y, x + w, y, rr)
  ctx.closePath()
}
function withFont(p, size, weight = '') {
  return `${weight} ${size}px ${p.font}`
}

// ==================== 主入口：绘制一帧 ====================
export function drawFrame(ctx, video, t, W, H) {
  const script = video.script || {}
  const scenes = Array.isArray(script.scenes) ? script.scenes : []
  const times = sceneTimes(video)
  const hookActive = scenes.length > 0 && t < 2.2

  const pal = SKIN_PALETTES[skinOf(video, t, hookActive)] || SKIN_PALETTES.glass
  drawStage(ctx, pal, W, H, video)

  if (!scenes.length) {
    // 旧 sections 脚本：板书化降级
    drawLegacySections(ctx, script.sections || [], video, W, H)
  } else if (hookActive) {
    drawHook(ctx, script.hook || '', pal, t, W, H)
  } else {
    const idx = sceneIdxAt(t, times)
    const sc = scenes[idx] || scenes[0]
    const tt = times[idx] || { start: 0, end: 1 }
    const p = Math.max(0, Math.min(1, (t - tt.start) / Math.max(0.1, tt.end - tt.start)))
    drawScene(ctx, sc, p, pal, video, W, H)
  }

  drawSubtitle(ctx, subtitleAt(video, t), pal, W, H)
  drawLetterbox(ctx, W, H)
}

// ==================== 舞台底 + 装饰 ====================
function drawStage(ctx, pal, W, H, video) {
  const g = ctx.createLinearGradient(0, 0, 0, H)
  g.addColorStop(0, pal.bgA)
  g.addColorStop(1, pal.bgB)
  ctx.fillStyle = g
  ctx.fillRect(0, 0, W, H)

  // 玻璃/霓虹等暗色皮肤沿用视频身份背景光斑
  if (pal.bgA === '#0d1220' || pal.deco === 'grid' || pal.deco === 'glass' || pal.deco === 'split' || pal.deco === 'bigq') {
    const seed = hashOf(`${video.subject}:${video.knowledge_key}:${video.angle}`)
    const spots = [
      ['rgba(94,208,255,.20)', 'rgba(80,96,235,.18)', 'rgba(94,208,255,.05)'],
      ['rgba(255,148,84,.22)', 'rgba(255,84,130,.16)', 'rgba(255,196,110,.06)'],
      ['rgba(52,224,170,.18)', 'rgba(64,160,255,.16)', 'rgba(52,224,170,.04)'],
      ['rgba(180,140,255,.22)', 'rgba(255,110,200,.16)', 'rgba(120,220,255,.05)'],
    ][seed % 4]
    const rad = (x, y, r, c) => {
      const rg = ctx.createRadialGradient(x, y, 0, x, y, r)
      rg.addColorStop(0, c)
      rg.addColorStop(1, 'rgba(0,0,0,0)')
      ctx.fillStyle = rg
      ctx.fillRect(0, 0, W, H)
    }
    rad(W * 0.82, -H * 0.05, W * 0.55, spots[0])
    rad(W * 0.05, H * 1.05, W * 0.6, spots[1])
    rad(W * 0.3, H * 0.5, W * 0.4, spots[2])
  }

  switch (pal.deco) {
    case 'chalk': {
      ctx.strokeStyle = pal.border
      ctx.lineWidth = Math.max(10, W * 0.014)
      ctx.strokeRect(ctx.lineWidth / 2, ctx.lineWidth / 2, W - ctx.lineWidth, H - ctx.lineWidth)
      for (let i = 0; i < 40; i++) {
        const x = hashOf('d' + i) % W, y = hashOf('e' + i) % H
        ctx.fillStyle = 'rgba(255,255,255,.05)'
        ctx.beginPath(); ctx.arc(x, y, 1.2, 0, Math.PI * 2); ctx.fill()
      }
      break
    }
    case 'paper': {
      ctx.strokeStyle = pal.border
      ctx.lineWidth = 2
      ctx.beginPath(); ctx.moveTo(W * 0.065, 0); ctx.lineTo(W * 0.065, H); ctx.stroke()
      ctx.strokeStyle = 'rgba(58,50,38,.08)'
      ctx.lineWidth = 1
      for (let y = 26; y < H; y += 34) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke() }
      break
    }
    case 'grid': {
      ctx.strokeStyle = 'rgba(94,208,255,.05)'
      ctx.lineWidth = 1
      for (let x = 0; x < W; x += 44) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke() }
      for (let y = 0; y < H; y += 44) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke() }
      break
    }
    case 'bigq': {
      ctx.fillStyle = 'rgba(255,255,255,.055)'
      ctx.font = `900 ${H * 0.9}px sans-serif`
      ctx.textAlign = 'right'
      ctx.fillText('?', W * 0.96, H * 0.82)
      ctx.textAlign = 'center'
      break
    }
    case 'chat': {
      ctx.fillStyle = pal.border
      ctx.fillRect(0, 0, W, 5)
      break
    }
    case 'sparkle': {
      ctx.fillStyle = 'rgba(255,255,255,.55)'
      ctx.font = `${H * 0.16}px sans-serif`
      ctx.textAlign = 'right'
      ctx.save(); ctx.translate(W * 0.92, H * 0.12); ctx.rotate(0.25)
      ctx.fillText('✨', 0, 0); ctx.restore()
      ctx.textAlign = 'center'
      break
    }
    case 'mind': {
      ctx.strokeStyle = 'rgba(63,140,88,.3)'
      ctx.lineWidth = 3
      ctx.beginPath(); ctx.moveTo(W * 0.12, H * 0.5); ctx.lineTo(W * 0.88, H * 0.5); ctx.stroke()
      ctx.beginPath(); ctx.arc(W * 0.12, H * 0.5, 12, 0, Math.PI * 2); ctx.fillStyle = 'rgba(63,140,88,.35)'; ctx.fill()
      break
    }
    case 'glass': {
      const lg = ctx.createLinearGradient(0, 0, W, H)
      lg.addColorStop(0.44, 'rgba(255,255,255,0)')
      lg.addColorStop(0.5, 'rgba(255,255,255,.07)')
      lg.addColorStop(0.56, 'rgba(255,255,255,0)')
      ctx.fillStyle = lg
      ctx.fillRect(0, 0, W, H)
      break
    }
    case 'split': {
      const lg = ctx.createLinearGradient(0, 0, W, 0)
      lg.addColorStop(0, 'rgba(255,90,95,.12)')
      lg.addColorStop(0.5, 'rgba(0,0,0,0)')
      lg.addColorStop(1, 'rgba(69,224,138,.1)')
      ctx.fillStyle = lg; ctx.fillRect(0, 0, W, H)
      ctx.strokeStyle = 'rgba(255,255,255,.22)'
      ctx.lineWidth = 2
      ctx.beginPath(); ctx.moveTo(W / 2, 0); ctx.lineTo(W / 2, H); ctx.stroke()
      break
    }
  }
}

function hashOf(s) {
  let h = 0
  for (let i = 0; i < String(s).length; i++) h = (h * 31 + String(s).charCodeAt(i)) | 0
  return Math.abs(h)
}

// ==================== 各构件 ====================
function accentFor(sc) {
  const m = sc.mood
  return MOOD_ACCENT[m] || MOOD_ACCENT.lecture
}

function drawHook(ctx, text, pal, t, W, H) {
  const a = Math.min(1, t / 0.5)
  ctx.save()
  ctx.globalAlpha = a
  if (pal.deco === 'chat') {
    ctx.fillStyle = '#4d8dff'
    roundRect(ctx, W * 0.12, H * 0.36, W * 0.76, H * 0.28, 26)
    ctx.fill()
    ctx.fillStyle = '#ffffff'
  } else {
    ctx.fillStyle = pal.ink
    ctx.shadowColor = pal.deco === 'grid' ? 'rgba(94,208,255,.8)' : 'rgba(0,0,0,.45)'
    ctx.shadowBlur = pal.bgB.startsWith('#0') ? 22 : 0
  }
  ctx.font = withFont(pal, Math.min(44, W * 0.042), '800')
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  const lines = wrapText(ctx, text, W * 0.72)
  const lh = Math.min(62, W * 0.058)
  const y0 = H * 0.5 - (lines.length - 1) * lh / 2
  lines.forEach((l, i) => ctx.fillText(l, W * 0.5, y0 + i * lh))
  ctx.restore()
}

function drawScene(ctx, sc, p, pal, video, W, H) {
  const ac = accentFor(sc)
  switch (sc.widget) {
    case 'point': {
      const prm = (sc.params || {})
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      if (pal.deco === 'chat') {
        ctx.fillStyle = '#ffffff'
        roundRect(ctx, W * 0.18, H * 0.4, W * 0.64, H * 0.2, 18)
        ctx.fill()
        ctx.fillStyle = '#1f2733'
      } else if (pal.deco === 'fun') {
        ctx.fillStyle = '#fff'
        roundRect(ctx, W * 0.2, H * 0.38, W * 0.6, H * 0.24, 16)
        ctx.fill()
        ctx.strokeStyle = '#7c5cff'; ctx.lineWidth = 4
        roundRect(ctx, W * 0.2, H * 0.38, W * 0.6, H * 0.24, 16)
        ctx.stroke()
        ctx.fillStyle = pal.ink
      } else {
        ctx.fillStyle = pal.ink
      }
      ctx.globalAlpha = Math.min(1, p * 3)
      ctx.font = withFont(pal, Math.min(40, W * 0.04), '800')
      ctx.fillText(String(prm.text || '讲解要点'), W * 0.5, H * 0.5)
      ctx.globalAlpha = 1
      break
    }
    case 'balance': {
      const left = (sc.params && sc.params.left) || { title: '错误做法', lines: [] }
      const right = (sc.params && sc.params.right) || { title: '正确做法', lines: [] }
      const win = p > 0.55
      const cx = W / 2
      const panelW = W * 0.4
      const xL = cx - panelW - W * 0.03
      const xR = cx + W * 0.03
      const y0 = H * 0.2
      const ph = H * 0.58
      drawPanel(ctx, xL, y0, panelW, ph, pal)
      drawPanel(ctx, xR, y0, panelW, ph, pal)
      if (win) {
        ctx.save()
        ctx.shadowColor = 'rgba(69,224,138,.4)'; ctx.shadowBlur = 24
        drawPanel(ctx, xR, y0, panelW, ph, pal)
        ctx.restore()
        ctx.globalAlpha = 0.55
        ctx.fillStyle = 'rgba(255,90,95,.06)'
        ctx.fillRect(xL, y0, panelW, ph)
        ctx.globalAlpha = 1
      }
      // 标题 + 行 + 印章
      ctx.textAlign = 'center'
      ctx.fillStyle = pal.ink
      ctx.font = withFont(pal, Math.min(30, W * 0.026), '800')
      ctx.fillText(String(left.title), xL + panelW / 2, y0 + 44)
      ctx.fillText(String(right.title), xR + panelW / 2, y0 + 44)
      ctx.font = withFont(pal, Math.min(24, W * 0.02))
      ctx.fillStyle = pal.dim
      const ll = (left.lines || [])
      const rl = (right.lines || [])
      ll.forEach((l, i) => ctx.fillText(String(l), xL + panelW / 2, y0 + 96 + i * 42))
      rl.forEach((l, i) => ctx.fillText(String(l), xR + panelW / 2, y0 + 96 + i * 42))
      // VS 徽章
      ctx.fillStyle = pal.ink
      ctx.font = withFont(pal, Math.min(30, W * 0.026), '800')
      ctx.fillText('VS', cx, H * 0.5)
      if (win) {
        ctx.fillStyle = '#ff6b81'
        roundRect(ctx, xL + panelW - 66, y0 + 12, 48, 48, 24)
        ctx.fill()
        ctx.fillStyle = '#fff'
        ctx.font = `800 26px sans-serif`
        ctx.fillText('✗', xL + panelW - 42, y0 + 36)
        ctx.fillStyle = '#45e08a'
        roundRect(ctx, xR + 18, y0 + 12, 48, 48, 24)
        ctx.fill()
        ctx.fillStyle = '#fff'
        ctx.fillText('✓', xR + 42, y0 + 36)
      }
      break
    }
    case 'example': {
      const prm = sc.params || {}
      const cx = W * 0.5
      const cw = Math.min(W * 0.74, 760)
      const x = cx - cw / 2
      let y = H * 0.16
      // 题干卡
      ctx.fillStyle = pal.panel
      roundRect(ctx, x, y, cw, 74, 14)
      ctx.fill()
      ctx.strokeStyle = ac.color
      ctx.lineWidth = 3
      ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x, y + 74); ctx.stroke()
      ctx.fillStyle = pal.ink
      ctx.textAlign = 'left'
      ctx.textBaseline = 'middle'
      ctx.font = withFont(pal, Math.min(28, W * 0.024), '700')
      ctx.fillText(String(prm.stem || '例题'), x + 22, y + 37)
      // 步骤
      const work = (prm.work || []).slice(0, Math.min(4, 1 + Math.floor(p * 3.5)))
      work.forEach((w, i) => {
        const yy = y + 90 + i * 56
        ctx.fillStyle = pal.deco === 'chat' ? '#b9dcff' : pal.panel
        roundRect(ctx, x + (pal.deco === 'chat' ? cw * 0.3 : 0), yy, pal.deco === 'chat' ? cw * 0.7 : cw, 46, 12)
        ctx.fill()
        if (pal.deco === 'chat') {
          ctx.fillStyle = '#0c2c4a'
        } else {
          ctx.strokeStyle = pal.line
          ctx.lineWidth = 1.5
          roundRect(ctx, x + (pal.deco === 'chat' ? cw * 0.3 : 0), yy, pal.deco === 'chat' ? cw * 0.7 : cw, 46, 12)
          ctx.stroke()
          ctx.fillStyle = pal.ink
        }
        ctx.fillText(String(w), x + (pal.deco === 'chat' ? cw * 0.3 : 0) + 22, yy + 23)
      })
      // 答案章
      if (p > 0.88 && prm.answer) {
        ctx.save()
        ctx.translate(cx, y + 90 + work.length * 56 + 26)
        ctx.scale(1 - (1 - Math.max(0, (p - 0.88) / 0.12)) * 0.2, 1 - (1 - Math.max(0, (p - 0.88) / 0.12)) * 0.2)
        ctx.fillStyle = '#47c87d'
        roundRect(ctx, -110, -26, 220, 52, 26)
        ctx.fill()
        ctx.fillStyle = '#123047'
        ctx.font = `800 26px sans-serif`
        ctx.textAlign = 'center'
        ctx.fillText(String(prm.answer), 0, 7)
        ctx.restore()
      }
      break
    }
    case 'array': {
      const prm = sc.params || {}
      const values = (prm.values || []).map(Number)
      const moves = prm.moves || []
      const target = prm.target === undefined ? undefined : Number(prm.target)
      const K = Math.max(1, moves.length)
      const fr = p * K
      const fk = Math.min(Math.floor(fr), K - 1)
      const ff = Math.min(1, fr - fk)
      const curMove = moves[fk] || {}
      const ease = (x) => (x < 0.5 ? 2 * x * x : 1 - Math.pow(-2 * x + 2, 2) / 2)
      let lp = curMove.l ?? -1, rp = curMove.r ?? -1
      if (fk < K - 1 && ff > 0.35) {
        const nx = moves[fk + 1]
        const et = Math.max(0, Math.min(1, (ff - 0.35) / 0.65))
        const ev = ease(et)
        lp = (curMove.l ?? -1) + ((nx.l ?? curMove.l ?? -1) - (curMove.l ?? -1)) * ev
        rp = (curMove.r ?? -1) + ((nx.r ?? curMove.r ?? -1) - (curMove.r ?? -1)) * ev
      }
      const n = values.length || 1
      const cellW = Math.min(86, W * 0.085)
      const gap = 14
      const totalW = n * cellW + (n - 1) * gap
      const x0 = (W - totalW) / 2
      const y0 = H * 0.34
      values.forEach((v, i) => {
        const xx = x0 + i * (cellW + gap)
        const active = i === Math.round(lp) || i === Math.round(rp)
        ctx.fillStyle = pal.panel || 'rgba(255,255,255,.07)'
        roundRect(ctx, xx, y0, cellW, cellW, 12)
        ctx.fill()
        ctx.strokeStyle = active && Math.round(lp) === i ? ac.color : (active && Math.round(rp) === i ? '#ffb84d' : pal.line)
        ctx.lineWidth = active ? 4 : 2
        roundRect(ctx, xx, y0, cellW, cellW, 12)
        ctx.stroke()
        ctx.fillStyle = pal.ink
        ctx.font = withFont(pal, Math.min(30, W * 0.028), '800')
        ctx.textAlign = 'center'
        ctx.textBaseline = 'middle'
        ctx.fillText(String(v), xx + cellW / 2, y0 + cellW / 2)
      })
      // 指针
      const drawPointer = (frac, label, color, idxLbl) => {
        if (frac < 0) return
        const xx = x0 + frac * (cellW + gap) + cellW / 2
        const py = y0 + cellW + 26
        ctx.fillStyle = color
        ctx.beginPath(); ctx.moveTo(xx - 12, py); ctx.lineTo(xx + 12, py); ctx.lineTo(xx, py + 22); ctx.closePath(); ctx.fill()
        ctx.strokeStyle = 'rgba(0,0,0,0.25)'; ctx.lineWidth = 2
        ctx.beginPath(); ctx.moveTo(xx, py - 8); ctx.lineTo(xx, py); ctx.stroke()
        ctx.font = `800 ${Math.min(20, W * 0.018)}px sans-serif`
        ctx.fillText(label, xx, py + 44)
      }
      drawPointer(lp, '左指针', '#7ee0ff')
      drawPointer(rp, '右指针', '#ffc372')
      // 计算气泡 + 批注
      const lv = values[curMove.l ?? -1], rv = values[curMove.r ?? -1]
      const sum = ((lv | 0) + (rv | 0))
      if (ff < 0.35 && curMove.l !== undefined && target !== undefined && isFinite(target)) {
        const rolled = Math.floor(sum * Math.max(0, Math.min(1, ff / 0.35)))
        const hit = sum === target
        ctx.fillStyle = 'rgba(12,16,28,.88)'
        roundRect(ctx, W * 0.5 - 250, H * 0.16, 500, 84, 16)
        ctx.fill()
        ctx.strokeStyle = ac.color
        ctx.lineWidth = 2
        roundRect(ctx, W * 0.5 - 250, H * 0.16, 500, 84, 16)
        ctx.stroke()
        ctx.fillStyle = '#fff'
        ctx.font = `900 ${Math.min(30, W * 0.026)}px sans-serif`
        ctx.textAlign = 'center'
        ctx.fillText(`${lv ?? ''} + ${rv ?? ''} = ${rolled}${hit ? ' 中了!' : (sum > target ? ' 太大' : ' 太小')}`, W * 0.5, H * 0.16 + 46)
      }
      if (curMove.note) {
        ctx.fillStyle = /中|成功|找到/.test(String(curMove.note)) ? '#9dffc2' : '#ffd9a1'
        ctx.font = `700 ${Math.min(22, W * 0.02)}px sans-serif`
        ctx.textAlign = 'center'
        ctx.fillText(String(curMove.note), W * 0.5, H * 0.8)
      }
      if (target !== undefined) {
        ctx.fillStyle = pal.dim
        ctx.font = `${Math.min(20, W * 0.018)}px sans-serif`
        ctx.textAlign = 'center'
        ctx.fillText(`目标 ${target}`, W * 0.5, H * 0.87)
      }
      break
    }
    case 'phrase': {
      const prm = sc.params || {}
      const text = String(prm.text || '')
      const chars = text.split('')
      const lh = Math.min(64, W * 0.06)
      const totalW = chars.length * lh * 0.95
      const x0 = (W - totalW) / 2
      ctx.textBaseline = 'middle'
      ctx.textAlign = 'center'
      ctx.font = withFont(pal, Math.min(46, W * 0.042), '900')
      chars.forEach((c, i) => {
        const a = p * 8 > i * 0.35 ? 1 : 0.15
        ctx.globalAlpha = a
        ctx.fillStyle = pal.ink
        ctx.fillText(c, x0 + i * lh * 0.95 + lh * 0.45, H * 0.5)
      })
      ctx.globalAlpha = 1
      break
    }
  }
}

function drawPanel(ctx, x, y, w, h, pal) {
  ctx.fillStyle = pal.panel
  roundRect(ctx, x, y, w, h, 16)
  ctx.fill()
  ctx.strokeStyle = pal.line
  ctx.lineWidth = 1.5
  roundRect(ctx, x, y, w, h, 16)
  ctx.stroke()
}

function drawLegacySections(ctx, sections, video, W, H) {
  const pal = SKIN_PALETTES.glass
  const list = (sections || []).slice(0, 5)
  ctx.textAlign = 'center'
  ctx.fillStyle = pal.ink
  ctx.font = withFont(pal, Math.min(34, W * 0.03), '800')
  ctx.textBaseline = 'middle'
  ctx.fillText(video.title || video.knowledge_name || '知识点讲解', W * 0.5, H * 0.2)
  list.forEach((s, i) => {
    ctx.fillStyle = pal.dim
    ctx.font = withFont(pal, Math.min(26, W * 0.022))
    s.lines.filter(Boolean).slice(0, 2).forEach((l, j) => ctx.fillText(String(l), W * 0.5, H * 0.34 + i * 92 + j * 36))
  })
}

// ==================== 句级字幕（同播放器切句口径）====================
function subtitleAt(video, t) {
  const narration = String((video.script && (video.script.narration || '')) || video.script_text || '').trim()
  if (!narration) return ''
  const pieces = narration.split(/(?<=[，,。！？!?；;：:、])/).map(s => s.trim()).filter(Boolean)
  const subs = []
  let buf = ''
  for (const p of pieces) {
    buf += p
    if (/[。！？!?]$/.test(p) || buf.length >= 14) {
      subs.push(buf)
      buf = ''
    }
  }
  if (buf.trim()) subs.push(buf)
  if (!subs.length) return ''
  const chars = subs.map(s => Math.max(1, s.length))
  const total = chars.reduce((a, b) => a + b, 0)
  const full = duration(video)
  let acc = 0, idx = 0
  for (let i = 0; i < subs.length; i++) {
    const start = (acc / total) * full
    acc += chars[i]
    if (t < (acc / total) * full) { idx = i; break }
    idx = i
  }
  return subs[idx].replace(/[，。！？；：、,.!?;:]+\s*$/, '')
}

function drawSubtitle(ctx, text, pal, W, H) {
  if (!text) return
  const isLight = !pal.bgB.startsWith('#0')
  ctx.textAlign = 'center'
  ctx.textBaseline = 'alphabetic'
  ctx.font = `700 ${Math.min(30, W * 0.026)}px "Microsoft YaHei","PingFang SC",sans-serif`
  const tw = ctx.measureText(text).width
  const bw = Math.min(W * 0.94, tw + 44)
  const bx = (W - bw) / 2
  const by = H * 0.94
  ctx.fillStyle = isLight ? 'rgba(255,255,255,.72)' : 'rgba(0,0,0,.4)'
  roundRect(ctx, bx, by - 34, bw, 44, 12)
  ctx.fill()
  ctx.fillStyle = isLight ? '#1c2433' : '#ffffff'
  ctx.fillText(text, W * 0.5, by - 4)
}

function drawLetterbox(ctx, W, H) {
  ctx.fillStyle = '#000'
  ctx.fillRect(0, 0, W, H * 0.025)
  ctx.fillRect(0, H * 0.975, W, H * 0.025)
}

export { skinOf }