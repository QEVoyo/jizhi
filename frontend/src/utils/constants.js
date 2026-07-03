// ===== 后端地址 =====
export const BACKEND_URL = 'https://api.jizhi-learn.com'
console.log('=== constants.js 加载了, BACKEND_URL:', 'https://api.jizhi-learn.com')  // 👈 加这行
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

// ===== 背景图映射 =====
export const BG_MAP = {
  light: {
    landing: '/assets/bg/main_bg.jpg',
    login: '/assets/bg/main_bg.jpg',
    main: '/assets/bg/main_bg.jpg',
    career: '/assets/bg/career_bg.png',
    rank: '/assets/bg/career_rank_bg.png',
    tasks: '/assets/bg/career_tasks_bg.jpg',
    achievements: '/assets/bg/career_achievements_bg.jpg',
    resource_lib: '/assets/bg/resource_lib_bg.png',
    do_question: '/assets/bg/do_question_bg.png',
    mastery_board: '/assets/bg/mastery_board_bg.jpg',
    set_detail: '/assets/bg/set_detail_bg.jpg',
    generate: '/assets/bg/generate_from_mastery_bg.jpg',
    profile: '/assets/bg/profile_bg.jpg'
  },
  dark: {
    landing: '/assets/bg/main_bl.jpg',
    login: '/assets/bg/main_bl.jpg',
    main: '/assets/bg/main_bl.jpg',
    career: '/assets/bg/career_bl.jpg',
    rank: '/assets/bg/career_rank_bl.jpg',
    tasks: '/assets/bg/career_tasks_bl.jpg',
    achievements: '/assets/bg/career_achievements_bl.jpg',
    resource_lib: '/assets/bg/resource_lib_bl.jpg',
    do_question: '/assets/bg/do_question_bl.jpg',
    mastery_board: '/assets/bg/mastery_board_bl.jpg',
    set_detail: '/assets/bg/set_detail_bl.jpg',
    generate: '/assets/bg/generate_from_mastery_bl.jpg',
    profile: '/assets/bg/profile_bl.jpg'
  }
}