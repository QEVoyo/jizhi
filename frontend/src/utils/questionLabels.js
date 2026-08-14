/**
 * 题型标签映射 — 所有考纲共用
 * 用于将 question_type ID 转为中文显示名
 */
export const TYPE_LABEL_MAP = {
  choice: '单选',
  choice_single: '单选',
  choice_multi: '多选',
  choice_indefinite: '不定项',
  fill: '填空',
  cloze: '完形',
  translation: '翻译',
  essay: '写作',
  calculation: '计算',
  programming: '编程',
  short_answer: '简答',
  case_analysis: '案例分析',
  teaching_design: '教学设计',
  analysis: '论述分析',
}

export function typeLabel(t) {
  return TYPE_LABEL_MAP[t] || t
}

/**
 * 根据 syllabus.dimensions 构建 category → display name 映射
 * @param {Array} dimensions — syllabus.dimensions 数组 [{name, category}, ...]
 * @returns {Object} — { category: displayName }
 */
export function buildCategoryMap(dimensions) {
  const map = {}
  if (Array.isArray(dimensions)) {
    dimensions.forEach(d => {
      if (d.category) map[d.category] = d.name
    })
  }
  // 内置回退（常见英文 category ID → 中文名）
  const fallback = {
    vocabulary: '词汇',
    grammar: '语法',
    reading: '阅读',
    translation: '翻译',
    writing: '写作',
    cloze: '完形填空',
    advanced_math: '高等数学',
    linear_algebra: '线性代数',
    probability: '概率论',
    marxism: '马原',
    mao_thought: '毛中特',
    modern_history: '史纲',
    ideology_law: '思修',
    current_affairs: '时政',
    cs_fundamentals: '计算机基础',
    python_syntax: 'Python语法',
    c_syntax: 'C语法',
    pointer_memory: '指针与内存',
    data_structure: '数据结构',
    file_io: '文件与异常',
    word: 'Word',
    excel: 'Excel',
    ppt: 'PPT',
    verbal: '言语理解',
    quantitative: '数量关系',
    reasoning: '判断推理',
    data_analysis: '资料分析',
    general_knowledge: '常识判断',
    comprehensive_quality: '综合素质',
    education_knowledge: '教育知识',
    subject_knowledge: '学科知识',
    teaching_ability: '教学能力',
    accounting: '会计',
    audit: '审计',
    finance_mgmt: '财管',
    economic_law: '经济法',
    tax_law: '税法',
    strategy_risk: '战略',
    civil_law: '民法',
    criminal_law: '刑法',
    admin_law: '行政法',
    procedural_law: '诉讼法',
    theory_law: '理论法',
    business_law: '商经法',
    character_pinyin: '字音',
    word_pronunciation: '词语',
    reading_basics: '朗读',
    speaking_topic: '说话',
  }
  return { ...fallback, ...map }
}

/**
 * 题型判断辅助
 */
export function isSingleChoice(t) {
  return ['choice', 'choice_single'].includes(t)
}

export function isMultiChoice(t) {
  return ['choice_multi', 'choice_indefinite'].includes(t)
}

export function isChoiceType(t) {
  return isSingleChoice(t) || isMultiChoice(t) || t === 'cloze'
}

export function isLongTextType(t) {
  return ['translation', 'essay', 'short_answer', 'case_analysis', 'teaching_design', 'programming', 'analysis'].includes(t)
}

export function longTextPlaceholder(t) {
  return {
    translation: '输入翻译...',
    essay: '输入作文...',
    short_answer: '输入简答...',
    case_analysis: '输入案例分析...',
    teaching_design: '输入教学设计方案...',
    programming: '输入代码...',
    analysis: '输入论述答案...',
  }[t] || '输入答案...'
}
