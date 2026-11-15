// ===== 后端地址 =====
const envBackend = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'
// 本地联调：手机/另一台电脑用局域网 IP 打开 Vite 时，页面里的 localhost
// 指的是那台手机自己，API 必须回到开发机。开发模式下自动把 API 指到
// 「当前页面 host 的 8000 端口」；生产构建（DEV=false）不受影响。
const pageHost = typeof window !== 'undefined' ? window.location.hostname : ''
const isPrivateLan = /^(10\.|192\.168\.|172\.(?:1[6-9]|2\d|3[01])\.)/.test(pageHost)
export const BACKEND_URL = import.meta.env.DEV && isPrivateLan
  ? `http://${pageHost}:8000`
  : envBackend
console.log('=== constants.js BACKEND_URL:', BACKEND_URL)
// ===== 题型映射 =====
export const TYPE_MAP = {
  '选择题': 'choice',
  '填空题': 'fill',
  '判断题': 'judge',
  '简答题': 'essay',
  '计算题': 'calculation',
  '论述题': 'essay',
  '编程题': 'coding'
}

export const TYPE_DISPLAY_MAP = {
  choice: '选择题',
  fill: '填空题',
  judge: '判断题',
  essay: '简答题/论述题',
  calculation: '计算题',
  coding: '编程题'
}

// ===== 段位配置 =====
export const RANK_ICONS = {
  '启程': '◈',
  '求索': '❖',
  '明理': '✧',
  '致知': '✦',
  '笃行': '✹',
  '臻境': '❋',
  '传说': '★'
}

export const RANK_COLORS = {
  '启程': '#8B8B8B',
  '求索': '#4FC3F7',
  '明理': '#4CAF50',
  '致知': '#FFB300',
  '笃行': '#FF6F00',
  '臻境': '#9C27B0',
  '传说': '#FF6B6B'
}

export const RANK_ORDER = ['启程', '求索', '明理', '致知', '笃行', '臻境', '传说']

export const SUB_SYMBOLS = { 1: '○', 2: '◌', 3: '◎', 4: '◍', 5: '●' }

// 背景图映射（BG_MAP）已于 2026-09-03 移除：舍弃背景图，页面底色/氛围由背景色 + 品牌色派生
// （见 stores/theme.js 与 styles/theme.css `.app-container`）