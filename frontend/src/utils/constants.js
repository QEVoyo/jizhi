// ===== 后端地址 =====
export const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'https://api.jizhi-learn.com'
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