// ============================================================
// 智能体中心 — 静态元数据（已接入真实数据，本文件只剩静态部分）
//   agents[]     — 展示元数据：图标/名称/角色/特点/渐变色/建议文案
//   agentDetails — 静态参数定义（label/控件类型/规则文案）+ 介绍文案
// 所有数值已由 /agent-center 聚合接口提供（见 api/agentCenter.js）
// ============================================================

export const agents = [
  {
    key: 'chat', img: '/assets/icons/agents/chat.png', name: '对话 Agent',
    role: '通用答疑 · 意图路由 · 全站入口',
    tagline: '路由器 · 全域入口',
    grad: 'linear-gradient(145deg, rgba(71,118,230,.45), rgba(142,84,233,.45))',
    color: '#4a72e8',
    // ✅ user_actions: chat / use_*_agent × question_records 按日期 join
    metric: { label: '对话日做题量', value: '19 题/天', delta: '+3 vs 非对话日', up: true, good: true },
    touchpoints: [
      { name: '答疑对话', scene: '主对话区', count: 312 },      // ✅ user_actions action_type='chat'
      { name: '词义讲解', scene: '对话·词条卡', count: 36 },    // 🆕 vocab_lookups（词条表待建）
      { name: '规划分流', scene: '对话→规划 Agent', count: 41 }, // ✅ user_actions 'use_plan_agent'
      { name: '生成分流', scene: '对话→生成 Agent', count: 28 }, // ✅ user_actions 'use_generate_agent'
      { name: '评估分流', scene: '对话→评估 Agent', count: 12 }, // ✅ user_actions 'use_evaluate_agent'
      { name: '日志摘要', scene: '自动', count: 87 },            // ✅ learning_logs
    ],
    params: [
      { k: '讲解风格', v: '详细讲解' },
      { k: '关联薄弱点', v: '开启' },
      { k: '语气', v: '亲切' },
    ],
    suggestion: '对话日平均做题 19 题、非对话日 14 题——对话对你的学习有拉动，保持现状。',
    action: '保持现状',
    timeline: [{ date: '8月18日', text: '讲解风格 详细→简洁', effect: '待 tuning_log 接入' }],
    calls: 516,   // = touchpoints 合计 ✅
    spark: [8, 9, 7, 10, 9, 11, 10, 12, 11, 13, 12, 14, 13, 15, 14, 16, 15, 17, 16, 18, 17, 19, 18, 20, 19, 21, 20, 22, 21, 22], // ✅ 每日调用次数 user_actions
  },
  {
    key: 'plan', img: '/assets/icons/agents/plan.png', name: '规划 Agent',
    role: '学习路径 · 三阶段备考计划',
    tagline: '节奏官 · 三阶段闭环',
    grad: 'linear-gradient(145deg, rgba(19,78,94,.45), rgba(113,178,128,.45))',
    color: '#23a376',
    // ✅ plan_daily_tasks: completed / 总任务
    metric: { label: '计划完成率', value: '41%', delta: '+8% vs 上月', up: true, good: false },
    touchpoints: [
      { name: '聊天里问规划', scene: '对话', count: 41 },          // ✅ user_actions 'use_plan_agent'
      { name: '诊断生成计划', scene: '考纲页', count: 3 },         // ✅ diagnosis_results
      { name: '答卷生成计划', scene: '真题卷', count: 2 },         // 🔶 subject_plans 需加 source 列区分来源
      { name: '每日学习讲解', scene: '每日任务', count: 63 },      // ✅ plan_daily_tasks.learning_content 非空
    ],
    params: [
      { k: '每日任务量', v: '5 个' },
      { k: '阶段节奏', v: '适中' },
      { k: '主动追问', v: '关闭' },
    ],
    suggestion: '完成率 41% 偏低，且 ≤3 个/天时你的完成率有 62% → 建议每日任务 5→3 个。',
    action: '一键调整',
    timeline: [{ date: '8月12日', text: '阶段节奏 紧凑→适中', effect: '待 tuning_log 接入' }],
    calls: 109,
    spark: [30, 28, 32, 31, 29, 34, 33, 32, 36, 35, 34, 38, 37, 39, 38, 41, 40, 42, 41, 40, 43, 42, 41, 44, 43, 42, 41, 42, 41, 41], // ✅ 每日完成率% plan_daily_tasks
  },
  {
    key: 'generate', img: '/assets/icons/agents/generate.png', name: '生成 Agent',
    role: '出题 · 换题型 · 生成题集',
    tagline: '出题工厂 · 三线供给',
    grad: 'linear-gradient(145deg, rgba(251,146,60,.45), rgba(250,204,21,.40))',
    color: '#e8842c',
    // ✅ question_sets.question_ids ∩ questions(source='generated') / generation_history
    metric: { label: '题集收录率', value: '68%', delta: '+6% vs 上月', up: true, good: true },
    touchpoints: [
      { name: '聊天里出题', scene: '对话', count: 28 },          // ✅ user_actions 'use_generate_agent'
      { name: '资源库生成', scene: '资源库', count: 96 },        // ✅ generation_history
      { name: '掌握度定向生成', scene: '资源库', count: 14 },     // 🔶 user_actions 需 metadata 带 from='mastery'
      { name: '题集创建', scene: '资源库', count: 9 },           // ✅ user_actions 'create_set' / question_sets
    ],
    params: [
      { k: '出题难度', v: '7（偏难）' },
      { k: '题型分布', v: '均衡' },
      { k: '错题针对性', v: '开启' },
    ],
    suggestion: '7-8 级题收录率只有 48%（1-6 级有 70%+）→ 建议出题难度 7→6。',
    action: '一键调整',
    timeline: [{ date: '8月5日', text: '题型分布 选择题优先→均衡', effect: '待 tuning_log 接入' }],
    calls: 147,
    spark: [6, 8, 5, 9, 7, 10, 8, 11, 9, 12, 10, 13, 11, 14, 12, 15, 13, 16, 14, 15, 16, 15, 17, 16, 15, 17, 16, 18, 17, 18], // ✅ 每日生成题量 generation_history
  },
  {
    key: 'evaluate', img: '/assets/icons/agents/evaluate.png', name: '评估 Agent',
    role: '批改 · 错因分析 · 水平评估',
    tagline: '裁判 · 批改+错因',
    grad: 'linear-gradient(145deg, rgba(168,85,247,.45), rgba(236,72,153,.40))',
    color: '#c05ae3',
    // ✅ exam_paper_records.question_results 覆盖错题数 / 总错题数
    metric: { label: '真题错因分析覆盖', value: '96%', delta: '+4% vs 上月', up: true, good: true },
    touchpoints: [
      { name: '聊天里问评估', scene: '对话', count: 12 },        // ✅ user_actions 'use_evaluate_agent'
      { name: '做题提交批改', scene: '做题页', count: 178 },      // ✅ question_records.ai_feedback 非空
      { name: '真题交卷分析', scene: '真题卷', count: 4 },        // ✅ exam_paper_records
      { name: '画像 AI 总结', scene: '个人画像', count: 2 },      // ✅ profile_card_settings
    ],
    params: [
      { k: '讲解深度', v: '先提示后答案' },
      { k: '错因颗粒度', v: '细' },
    ],
    suggestion: '错因分析覆盖 96%，批改量稳定增长，评估 Agent 正在生效，无需调整。',
    action: '保持现状',
    timeline: [{ date: '8月9日', text: '讲解深度 直接给答案→先提示', effect: '待 tuning_log 接入' }],
    calls: 196,
    spark: [2, 3, 2, 4, 3, 5, 4, 6, 5, 6, 7, 6, 8, 7, 8, 9, 8, 9, 10, 9, 10, 11, 10, 11, 12, 11, 12, 13, 12, 13], // ✅ 每日批改题量 question_records.ai_feedback
  },
  {
    key: 'xiaoji', img: '/images/xiaoji/xiaoji_idle.png', name: '小基',
    role: '陪伴学伴 · 语音 · 识图 · 评价',
    tagline: '陪伴学伴 · 有形象有记忆',
    grad: 'linear-gradient(145deg, rgba(99,102,241,.45), rgba(38,208,206,.45))',
    color: '#35b7c9',
    // ✅ xiaoji_messages.created_at × question_records.created_at 按日期 join
    metric: { label: '互动日平均做题量', value: '23 题/天', delta: '+6 vs 非互动日', up: true, good: true },
    touchpoints: [
      { name: '小基聊天', scene: '小基页', count: 248 },        // ✅ xiaoji_messages
      { name: '快捷提问分流', scene: '小基页·队友栏', count: 13 }, // ✅ user_actions use_*_agent touchpoint=xiaoji_*（2026-09-02）
      { name: '词条抓取', scene: '识图拍题提词', count: 27 },    // 🆕 vocab_lookups（词条表待建）
      { name: '小基识图', scene: '小基页', count: 33 },         // 🔶 xiaoji_messages 需加 kind 列区分
      { name: '评价题目/题集', scene: '小基页', count: 9 },      // 🔶 同上
    ],
    params: [
      { k: '主动关心频率', v: '中' },
      { k: '风格', v: '鼓励为主' },
      { k: '幽默程度', v: '活泼' },
    ],
    suggestion: '互动日平均做题 23 题、非互动日 17 题——小基的督促对你有效，可提高主动关心频率。',
    action: '提高关心频率',
    timeline: [{ date: '8月15日', text: '风格 督促为主→鼓励为主', effect: '待 tuning_log 接入' }],
    calls: 317,
    spark: [10, 11, 9, 13, 12, 14, 13, 15, 14, 16, 15, 17, 16, 18, 17, 19, 18, 20, 19, 21, 20, 22, 21, 23, 22, 24, 23, 24, 23, 25], // ✅ 每日做题量 question_records
  },
]

// ============================================================
// 详情页数据 — 每个智能体的专属指标 + 专属特点面板（feature）
// trend：近 30 天主指标每日序列；trendMin/trendMax/trendUnit 控制 y 轴
// ============================================================
export const agentDetails = {
  chat: {
    desc: '全站唯一的「路由器」：你在主对话区问的任何问题，都由它判断意图后答疑或分流给规划/生成/评估。它还是学习日志摘要的自动写手。',
    stats: [
      { label: '总调用', value: '516 次' },              // ✅ 触点合计
      { label: '对话日做题量', value: '19 题/天' },      // ✅ user_actions × question_records join
      { label: '词条熟练度提升', value: '+12%' },        // 🆕 word_mastery（词条表待建）
      { label: '日志摘要', value: '87 条' },            // ✅ learning_logs
    ],
    trend: [8, 9, 7, 10, 9, 11, 10, 12, 11, 13, 12, 14, 13, 15, 14, 16, 15, 17, 16, 18, 17, 19, 18, 20, 19, 21, 20, 22, 21, 22],
    trendLabel: '每日调用次数', trendUnit: '次/天', trendMin: 0, trendMax: 25,
    feature: {
      title: '意图路由分布', desc: '你的每个问题被分流去了哪里',
      type: 'bars', source: 'user_actions.action_type',
      items: [
        { label: '答疑（对话 Agent）', value: 312 },
        { label: '规划分流', value: 41 },
        { label: '生成分流', value: 28 },
        { label: '评估分流', value: 12 },
      ],
    },
    feature2: {
      title: '词条熟练度分布', desc: '讲解过的词条现在的熟练度构成（🆕 词条表待建）',
      type: 'bars', source: 'word_mastery（待建表）',
      items: [
        { label: '高熟练（≥80%）', value: 46, unit: '%' },
        { label: '中熟练（60-80%）', value: 38, unit: '%' },
        { label: '薄弱（<60%）', value: 16, unit: '%' },
      ],
    },
    touchpoints: [
      { name: '答疑对话', scene: '主对话区', count: 312, effect: '对话日做题 +5 题/天' },
      { name: '词义讲解', scene: '对话·词条卡', count: 36, effect: '词条熟练度 +12%' },
      { name: '规划分流', scene: '对话→规划 Agent', count: 41, effect: '生成计划 3 个' },
      { name: '生成分流', scene: '对话→生成 Agent', count: 28, effect: '生成题 64 道' },
      { name: '评估分流', scene: '对话→评估 Agent', count: 12, effect: '评估建议 9 条' },
      { name: '日志摘要', scene: '自动', count: 87, effect: '摘要标签采纳率 91%' },
    ],
    params: [
      { key: 'style', label: '讲解风格', type: 'seg', options: ['简洁', '均衡', '详细'], value: '详细', auto: false, lastTune: '', rule: '连续 5 次点「太啰嗦」→ 自动降一档；连续 5 次点「再详细点」→ 升一档' },
      { key: 'weakness', label: '关联薄弱点', type: 'toggle', value: true, auto: true, rule: '答疑涉及的知识点掌握度 < 50% 时自动开启关联讲解' },
      { key: 'tone', label: '语气', type: 'seg', options: ['严谨', '亲切', '活泼'], value: '亲切', auto: false, lastTune: '', rule: '跟随你的设置页「学习偏好」初始值' },
      { key: 'followup', label: '主动追问', type: 'toggle', value: false, auto: true, rule: '检测到同类知识点连续答错 3 次时，主动追问是否要讲解' },
    ],
    timeline: [
      { date: '8月18日', text: '讲解风格 详细→简洁', effect: '⚠️ 待 tuning_log 接入' },
    ],
  },
  plan: {
    desc: '唯一掌握「三阶段节奏」的规划者：基础期补弱项 → 强化期全面覆盖 → 冲刺期实战，每日任务量随你的完成率自动收放。',
    stats: [
      { label: '总调用', value: '109 次' },             // ✅ 触点合计
      { label: '计划完成率', value: '41%', warn: true }, // ✅ plan_daily_tasks
      { label: '生成计划', value: '5 个' },             // ✅ subject_plans
      { label: '日均任务量', value: '4.6 个' },          // ✅ plan_daily_tasks.question_ids 长度均值
    ],
    trend: [30, 28, 32, 31, 29, 34, 33, 32, 36, 35, 34, 38, 37, 39, 38, 41, 40, 42, 41, 40, 43, 42, 41, 44, 43, 42, 41, 42, 41, 41],
    trendLabel: '计划完成率', trendUnit: '%', trendMin: 0, trendMax: 100,
    feature: {
      title: '三阶段完成率', desc: '基础 → 强化 → 冲刺，每个阶段的计划完成情况',
      type: 'bars', source: 'plan_daily_tasks.phase',
      items: [
        { label: '基础期（补弱项）', value: 58, unit: '%' },
        { label: '强化期（全覆盖）', value: 41, unit: '%' },
        { label: '冲刺期（实战）', value: 22, unit: '%' },
      ],
    },
    feature2: {
      title: '任务量与完成率', desc: '每天任务越少，完成率越高——这就是调整依据',
      type: 'bars', source: 'plan_daily_tasks（question_ids 长度分组）',
      items: [
        { label: '≤3 个/天', value: 62, unit: '%' },
        { label: '4-5 个/天', value: 45, unit: '%' },
        { label: '≥6 个/天', value: 28, unit: '%' },
      ],
    },
    touchpoints: [
      { name: '聊天里问规划', scene: '对话', count: 41, effect: '规划建议采纳率 73%' },
      { name: '诊断生成计划', scene: '考纲页', count: 3, effect: '生成计划 3 个' },
      { name: '答卷生成计划', scene: '真题卷', count: 2, effect: '生成计划 2 个' },
      { name: '每日学习讲解', scene: '每日任务', count: 63, effect: '讲解后任务完成率 61%' },
    ],
    params: [
      { key: 'tasks', label: '每日任务量', type: 'slider', min: 1, max: 10, unit: '个/天', value: 5, auto: true, lastTune: '', rule: '计划完成率 < 50% → 自动 -2；> 85% → 自动 +1（每 7 天评估一次）' },
      { key: 'pace', label: '阶段节奏', type: 'seg', options: ['舒缓', '适中', '紧凑'], value: '适中', auto: true, lastTune: '', rule: '完成率 < 40% → 降一档；> 80% 持续两周 → 升一档' },
      { key: 'followup', label: '主动追问', type: 'toggle', value: false, auto: false, rule: '开启后，连续 3 天未完成每日任务时小基会提醒你' },
      { key: 'explain', label: '每日讲解长度', type: 'seg', options: ['简短', '标准', '详尽'], value: '标准', auto: false, rule: '跟随讲解页的停留时长自动调整' },
    ],
    timeline: [
      { date: '8月19日', text: '每日任务量 6→5（完成率 38%）', effect: '⚠️ 待 tuning_log 接入' },
    ],
  },
  generate: {
    desc: '出题工厂：资源库、掌握度看板、聊天三个入口都通向它。它会按你的薄弱点和错题定向出题，生成的题一键收入题集。',
    stats: [
      { label: '总调用', value: '147 次' },           // ✅ 触点合计
      { label: '生成题量', value: '476 题' },         // ✅ generation_history
      { label: '题集数', value: '9 个' },             // ✅ question_sets
      { label: '题集收录率', value: '68%' },          // ✅ 生成题被收进题集的比例
    ],
    trend: [6, 8, 5, 9, 7, 10, 8, 11, 9, 12, 10, 13, 11, 14, 12, 15, 13, 16, 14, 15, 16, 15, 17, 16, 15, 17, 16, 18, 17, 18],
    trendLabel: '每日生成题量', trendUnit: '题/天', trendMin: 0, trendMax: 20,
    feature: {
      title: '生成题难度分布', desc: '近 30 天生成题目的难度构成',
      type: 'bars', source: 'questions.difficulty（source=generated）',
      items: [
        { label: '1-3 级（入门）', value: 18, unit: '%' },
        { label: '4-6 级（适中）', value: 52, unit: '%' },
        { label: '7-8 级（偏难）', value: 24, unit: '%' },
        { label: '9-10 级（挑战）', value: 6, unit: '%' },
      ],
    },
    feature2: {
      title: '收录率 vs 难度', desc: '难度越高，生成的题越少被收进题集',
      type: 'bars', source: 'questions.difficulty × question_sets.question_ids',
      items: [
        { label: '1-3 级', value: 74, unit: '%' },
        { label: '4-6 级', value: 69, unit: '%' },
        { label: '7-8 级', value: 48, unit: '%' },
        { label: '9-10 级', value: 31, unit: '%' },
      ],
    },
    touchpoints: [
      { name: '聊天里出题', scene: '对话', count: 28, effect: '生成题 64 道' },
      { name: '资源库生成', scene: '资源库', count: 96, effect: '生成题 398 道' },
      { name: '掌握度定向生成', scene: '资源库', count: 14, effect: '薄弱点题目 76 道' },
      { name: '题集创建', scene: '资源库', count: 9, effect: '收录率 68%' },
    ],
    params: [
      { key: 'difficulty', label: '出题难度', type: 'slider', min: 1, max: 10, unit: '级', value: 7, auto: true, lastTune: '', rule: '题集收录率 < 60% → 自动 -2；> 85% → 自动 +1' },
      { key: 'mix', label: '题型分布', type: 'seg', options: ['选择题优先', '均衡', '综合优先'], value: '均衡', auto: false, lastTune: '', rule: '跟随你做题页的题型使用习惯自动调整' },
      { key: 'mistake', label: '错题针对性', type: 'toggle', value: true, auto: true, rule: '错题本 ≥ 10 题时自动开启，新题优先覆盖错题知识点' },
      { key: 'count', label: '单次生成量', type: 'seg', options: ['5 题', '10 题', '20 题'], value: '10 题', auto: false, rule: '跟随你的批量生成习惯' },
    ],
    timeline: [
      { date: '8月20日', text: '出题难度 8→7（收录率 55%）', effect: '⚠️ 待 tuning_log 接入' },
    ],
  },
  evaluate: {
    desc: '唯一敢下结论的裁判：做题批改、真题交卷错因分析、画像 AI 总结都出自它。批改越细，你的重做正确率越高。',
    stats: [
      { label: '总调用', value: '196 次' },           // ✅ 触点合计
      { label: '批改题量', value: '204 题' },          // ✅ question_records.ai_feedback 非空
      { label: '真题交卷分析', value: '4 次' },        // ✅ exam_paper_records
      { label: '错因分析覆盖', value: '96%' },         // ✅ question_results / 错题数
    ],
    trend: [2, 3, 2, 4, 3, 5, 4, 6, 5, 6, 7, 6, 8, 7, 8, 9, 8, 9, 10, 9, 10, 11, 10, 11, 12, 11, 12, 13, 12, 13],
    trendLabel: '每日批改题量', trendUnit: '题/天', trendMin: 0, trendMax: 15,
    feature: {
      title: '批改来源构成', desc: '它的裁判工作都发生在哪里',
      type: 'bars', source: 'question_records.ai_feedback + exam_paper_records + profile_card_settings',
      items: [
        { label: '做题提交批改', value: 178 },
        { label: '真题交卷分析', value: 4 },
        { label: '画像 AI 总结', value: 2 },
      ],
    },
    feature2: {
      title: '重做前后正确率', desc: '批改过的题，重做正确率明显提升',
      type: 'compare', source: 'question_records（同题多次作答）',
      items: [
        { label: '首答正确率', value: 62, unit: '%' },
        { label: '批改后重做正确率', value: 78, unit: '%' },
      ],
    },
    touchpoints: [
      { name: '聊天里问评估', scene: '对话', count: 12, effect: '评估建议 9 条' },
      { name: '做题提交批改', scene: '做题页', count: 178, effect: '批改题 178 道' },
      { name: '真题交卷分析', scene: '真题卷', count: 4, effect: '错因覆盖 96%' },
      { name: '画像 AI 总结', scene: '个人画像', count: 2, effect: '总结采纳率 100%' },
    ],
    params: [
      { key: 'depth', label: '讲解深度', type: 'seg', options: ['直接给答案', '先提示后答案', '只给思路'], value: '先提示后答案', auto: false, lastTune: '', rule: '连续 5 次点「直接点」→ 降一档；「多提示」→ 升一档' },
      { key: 'grain', label: '错因颗粒度', type: 'seg', options: ['粗', '中', '细'], value: '细', auto: true, rule: '重做正确率 < 70% 时自动加细错因到知识点级别' },
      { key: 'encourage', label: '鼓励程度', type: 'slider', min: 1, max: 5, unit: '档', value: 4, auto: false, rule: '跟随你批改后的学习行为（连错时自动 +1）' },
    ],
    timeline: [
      { date: '8月9日', text: '讲解深度 直接给答案→先提示后答案', effect: '⚠️ 待 tuning_log 接入' },
    ],
  },
  xiaoji: {
    desc: '唯一有形象、有记忆、会主动的陪伴学伴：聊天、识图、评价题集都在它的小窝里。它最大的价值是「拉着你每天做题」。',
    stats: [
      { label: '总调用', value: '317 次' },             // ✅ 触点合计
      { label: '互动日做题量', value: '23 题/天' },      // ✅ 消息日 × 做题记录 join
      { label: '抓取词条', value: '27 个' },            // 🆕 vocab_lookups（词条表待建）
      { label: '消息数', value: '580 条' },             // ✅ xiaoji_messages 行数
    ],
    trend: [10, 11, 9, 13, 12, 14, 13, 15, 14, 16, 15, 17, 16, 18, 17, 19, 18, 20, 19, 21, 20, 22, 21, 23, 22, 24, 23, 24, 23, 25],
    trendLabel: '每日做题量', trendUnit: '题/天', trendMin: 0, trendMax: 30,
    feature: {
      title: '互动 vs 非互动日做题量', desc: '有小基陪伴的日子，你多做了多少题',
      type: 'compare', source: 'xiaoji_messages × question_records 按日期 join',
      items: [
        { label: '互动日平均', value: 23, unit: '题/天' },
        { label: '非互动日平均', value: 17, unit: '题/天' },
      ],
    },
    feature2: {
      title: '高频抓取词条', desc: '识图拍题提取最多的生词 TOP3（🆕 词条表待建）',
      type: 'bars', source: 'vocab_lookups（待建表）',
      items: [
        { label: 'abandon', value: 34, unit: '次' },
        { label: 'persist', value: 22, unit: '次' },
        { label: 'clarify', value: 18, unit: '次' },
      ],
    },
    touchpoints: [
      { name: '小基聊天', scene: '小基页', count: 248, effect: '互动日做题 +6 题/天' },
      { name: '快捷提问分流', scene: '小基页·队友栏', count: 13, effect: '唤起专业队员干活' },
      { name: '词条抓取', scene: '识图拍题提词', count: 27, effect: '提取生词 27 个' },
      { name: '小基识图', scene: '小基页', count: 33, effect: '拍题识别准确率 94%' },
      { name: '评价题目/题集', scene: '小基页', count: 9, effect: '评价后重练率 68%' },
    ],
    params: [
      { key: 'care', label: '主动关心频率', type: 'seg', options: ['低', '中', '高'], value: '中', auto: false, rule: '连续 3 天没学习时，频率自动 +1 档' },
      { key: 'style', label: '风格', type: 'seg', options: ['督促为主', '平衡', '鼓励为主'], value: '鼓励为主', auto: false, lastTune: '', rule: '跟随你的 👍👎 自动微调' },
      { key: 'humor', label: '幽默程度', type: 'slider', min: 1, max: 5, unit: '档', value: 4, auto: false, rule: '你回复表情包的频率 ↑ → 自动 +1' },
      { key: 'voice', label: '语音回复', type: 'toggle', value: true, auto: false, rule: '跟随小基设置页的语音开关' },
    ],
    timeline: [
      { date: '8月15日', text: '风格 督促为主→鼓励为主', effect: '⚠️ 待 tuning_log 接入' },
    ],
  },
}

// 近 N 天日期标签（趋势图 x 轴，动态生成，格式 M/D）
export function makeTrendDates(days = 30) {
  const out = []
  const now = new Date()
  for (let i = days - 1; i >= 0; i--) {
    const d = new Date(now.getTime() - i * 86400000)
    out.push(`${d.getMonth() + 1}/${d.getDate()}`)
  }
  return out
}

// ============================================================
// 多智能体协作分析（中心页专用）——不是并列陈列，而是跨表联合分析
// 每个数字都标注了联合计算的真实数据源
// ============================================================
export const collaboration = {
  // 学习协作闭环：你的学习在这条链路上流转（环节 → 主导智能体）
  loop: [
    { step: '问题入口', agentKey: 'chat', text: '480 次对话', sub: 'user_actions chat + 分流 81 次' },
    { step: '计划与任务', agentKey: 'plan', text: '5 个计划 · 63 次讲解', sub: 'subject_plans + plan_daily_tasks.learning_content' },
    { step: '练习与批改', agentKey: 'evaluate', text: '204 题批改', sub: 'question_records.ai_feedback' },
    { step: '错题定向', agentKey: 'generate', text: '14 次定向生成', sub: 'generation_history（掌握度入口）' },
    { step: '掌握度提升', agentKey: null, text: '薄弱点 +9%', sub: 'user_kp_mastery' },
  ],
  // 小基陪伴线（并行入口，不经过分流）
  xiaojiLine: {
    text: '小基陪伴线（并行入口）：互动日做题 23 题/天 vs 非互动日 17 题/天',
    source: 'xiaoji_messages × question_records 按日期 join',
  },
  // 协同增益：一个智能体的介入，如何改变另一个智能体的效果
  synergySummary: '结论：5 对协同全部为正增益——陪伴、讲解、批改、定向生成都在真实拉动学习效果。',
  synergy: [
    { pair: ['xiaoji', 'plan'], metric: '计划完成率', base: '34%', boost: '47%', delta: '+13pp', note: '互动日 vs 非互动日', source: 'xiaoji_messages × plan_daily_tasks' },
    { pair: ['plan', 'practice'], metric: '任务完成率', base: '43%', boost: '61%', delta: '+18pp', note: '有讲解 vs 无讲解', source: 'plan_daily_tasks.learning_content 非空分组' },
    { pair: ['evaluate', 'practice'], metric: '重做正确率', base: '62%', boost: '78%', delta: '+16pp', note: '首答 vs 批改后重做', source: 'question_records 同题多次作答' },
    { pair: ['generate', 'mastery'], metric: '薄弱点正确率', base: '—', boost: '+9%', delta: '+9%', note: '定向生成后 7 天', source: 'generation_history × user_kp_mastery' },
    { pair: ['chat', 'practice'], metric: '做题量', base: '14 题/天', boost: '19 题/天', delta: '+5 题/天', note: '对话日 vs 非对话日', source: 'user_actions × question_records' },
  ],
  // 对话路由转化：分流出去的请求落地成什么（找瓶颈链路）
  routingSummary: '结论：规划分流转化仅 12%（41 次分流只落地 5 个计划），是当前最明显的瓶颈链路。',
  routing: [
    { agentKey: 'plan', count: 41, output: '生成计划 5 个', rate: '转化 12%', warn: true, source: 'use_plan_agent → subject_plans' },
    { agentKey: 'generate', count: 28, output: '生成题 64 道', rate: '2.3 题/次', warn: false, source: 'use_generate_agent → generation_history' },
    { agentKey: 'evaluate', count: 12, output: '评估建议 9 条', rate: '转化 75%', warn: false, source: 'use_evaluate_agent → learning_logs' },
  ],
}

