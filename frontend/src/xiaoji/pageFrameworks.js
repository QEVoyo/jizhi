/**
 * 页面概览框架（2026-10-30）
 *
 * 用户的要求：总结页面时**先按页面已有的框架**，再填用户自己的内容；
 * 不要每次都把整页 DOM 塞给模型 —— 像个人中心，固定的是「基本信息 / 学习画像 /
 * 成就统计」，变的是昵称、阶段、目标。框架已知，就用本地模板渲染；
 * 只有「让小基细说」才可选调一次模型，且只传框架 + 结构化数据（或 1200 字片段）。
 *
 * 好处：
 *   · 默认总结 0 token、即时返回；
 *   · 输出稳定（不会这次三句、下次八句）；
 *   · 页面改版时只改一处框架，不用重调提示词。
 */

function textOf(sel, root = document) {
  const el = root.querySelector(sel)
  return (el?.textContent || '').trim()
}

function headings(limit = 10) {
  return Array.from(document.querySelectorAll('.app-container h1, .app-container h2, .app-container h3'))
    .map(el => (el.textContent || '').trim())
    .filter(Boolean)
    .slice(0, limit)
}

function visibleTabs() {
  return Array.from(document.querySelectorAll('.el-tabs__item'))
    .map(el => (el.textContent || '').replace(/^[^一-龥A-Za-z0-9]+/, '').trim())
    .filter(Boolean)
}

function bodySnippet(max = 1200) {
  const root = document.querySelector('.app-container')
  if (!root) return ''
  const clone = root.cloneNode(true)
  clone.querySelectorAll('.xj-page-host, .xj-bubble, .gs-overlay, .jz-toast, script, style, svg, img')
    .forEach(el => el.remove())
  return (clone.textContent || '').replace(/\s+/g, ' ').trim().slice(0, max)
}

function pick(...vals) {
  return vals.find(v => v != null && String(v).trim() !== '') || ''
}

const FRAMEWORKS = [
  {
    id: 'profile',
    match: /^\/profile$/,
    title: '个人中心',
    sections: ['基本信息', '学习画像', '成就与统计'],
    extract: ({ auth }) => {
      const u = auth || {}
      return {
        nickname: pick(u.nickname, '未设置'),
        stage: pick(u.learning_stage, '未填写'),
        grade: pick(u.grade, ''),
        major: pick(u.major, ''),
        goal: pick(u.learning_goal, '未填写'),
        style: pick(u.learning_style, ''),
        daily: pick(u.daily_study_time, ''),
      }
    },
    render: (d) => {
      const bits = [`昵称「${d.nickname}」`, `学习阶段：${d.stage}`]
      if (d.grade || d.major) bits.push(`${d.grade}${d.major ? ' · ' + d.major : ''}`)
      bits.push(`学习目标：${d.goal}`)
      if (d.style || d.daily) bits.push(`学习偏好：${[d.style, d.daily].filter(Boolean).join(' / ')}`)
      return `这是你的个人中心，固定展示基本信息、学习画像和成就统计。\n${bits.join('；')}。\n要改偏好或重新填问卷，去设置/引导页；需要我解读画像，点「找小基聊聊」。`
    },
  },
  {
    id: 'settings',
    match: /^\/settings/,
    title: '设置中心',
    sections: ['账号安全', '通知设置', '外观与主题', '桌面端与桌宠', '快捷键'],
    render: () => '这里是设置中心，固定包含账号安全、通知、外观主题、桌面端/桌宠、快捷键五块。\n改完记得保存；账号安全里的密码和邮箱是最需要留意的两项。',
  },
  {
    id: 'home',
    match: /^\/home$/,
    title: '小基主页',
    sections: ['对话与语音', '今日推荐', '小基关心', '使用日志'],
    render: () => '这是小基主页：中间是对话/语音，右侧是今日推荐、小基关心和使用日志。\n想直接开始，可以点推荐里的「去做」，或者在输入框里说出你的目标。',
  },
  {
    id: 'resource-lib',
    match: /^\/resource-lib/,
    title: '资源库',
    sections: ['生成题目', '我的题集', '错题本', '生成历史'],
    extract: () => ({ tabs: visibleTabs() }),
    render: (d) => {
      const tabs = d.tabs?.length ? d.tabs : ['生成题目', '我的题集', '错题本', '生成历史']
      return `这里是资源库，固定分 ${tabs.length} 块：${tabs.join('、')}。\n出题、整理题集、复习错题、看历史记录都在这一页；也可以直接把资料拖给小基，让它按资料出题。`
    },
  },
  {
    id: 'agent-center',
    match: /^\/agent-center/,
    title: '智能体中心',
    sections: ['团队与工作流', '运行轨迹', '调参日记', '分层记忆', '功能地图'],
    render: () => '这里是智能体中心：能看到团队工作流、每次运行的节点轨迹、调参日记和分层记忆。\n它展示的是「系统为什么这么调」，不是学习内容本身；想看学习数据去资源库或掌握度看板。',
  },
  {
    id: 'mastery',
    match: /^\/mastery-board/,
    title: '掌握度看板',
    sections: ['薄弱 / 待巩固 / 优势', '知识点分布', '下一步建议'],
    extract: () => {
      const t = bodySnippet(800)
      const m = t.match(/薄弱\s*(\d+)[\s\S]{0,30}?待巩固\s*(\d+)[\s\S]{0,30}?优势\s*(\d+)/)
      return m ? { weak: m[1], mid: m[2], strong: m[3] } : {}
    },
    render: (d) => {
      const nums = (d.weak != null)
        ? `当前分布：薄弱 ${d.weak}、待巩固 ${d.mid}、优势 ${d.strong}。`
        : '当前看板按薄弱 / 待巩固 / 优势三段显示知识点分布。'
      return `这是掌握度看板。${nums}\n优先补「薄弱」段；如果某一格连续错，我可以帮你定向出题。`
    },
  },
  {
    id: 'learning-plan',
    match: /^\/learning-plan|^\/plan-detail|^\/plan-preview/,
    title: '学习计划',
    sections: ['当前阶段', '每日任务', '完成进度', '调整建议'],
    render: () => '这里是学习计划页：固定看当前阶段、每日任务、完成进度和调整建议。\n完成率连续偏低时，别硬扛，可以让小基把任务量或难度调小一点。',
  },
  {
    id: 'subject-plan',
    match: /^\/subject-plan/,
    title: '学科计划',
    sections: ['考纲诊断', '阶段计划', '练习记录', '掌握度'],
    render: () => '这里是学科计划：从考纲诊断开始，生成阶段计划，再做练习、看掌握度。\n如果还没诊断，先做一次摸底；诊断完的计划会更贴合你的薄弱点。',
  },
  {
    id: 'do-question',
    match: /^\/do-question|practice/,
    title: '做题页',
    sections: ['题干与选项', '提交与反馈', '解析', '错题收录'],
    render: () => '这是做题页：读题干、选答案、提交后看反馈和解析，答错会自动进错题本。\n卡住时可以点页面右下角的小基，让我看错因或给提示。',
  },
  {
    id: 'evaluation',
    match: /^\/evaluation/,
    title: '评估中心',
    sections: ['评估报告', '评估表', '薄弱点', '建议'],
    render: () => '这里是评估中心：报告、评估表、薄弱点和建议都在这一页。\n先看「薄弱点」和「建议」两段，再看总分；总分只说明结果，薄弱点才说明下一步做什么。',
  },
  {
    id: 'community',
    match: /^\/community|^\/post/,
    title: '社区',
    sections: ['好友与消息', '帖子与问答', '排行榜', '收藏'],
    render: () => '这里是社区：好友、消息、帖子问答、排行榜和收藏。\n学习上的问题去问答区；想找同伴互相监督，可以加好友或看排行榜。',
  },
  {
    id: 'message',
    match: /^\/message/,
    title: '消息中心',
    sections: ['学习提醒', '计划提醒', '社区互动', '系统消息'],
    render: () => '这里是消息中心：学习提醒、计划提醒、社区互动和系统消息。\n没读的会聚合计数；不想被某类提醒打扰，去设置里关对应开关。',
  },
  {
    id: 'wordbook',
    match: /^\/wordbook/,
    title: '词条本',
    sections: ['全部词条', '薄弱词', '已掌握', '复习'],
    render: () => '这里是词条本：按全部 / 薄弱 / 已掌握筛选，薄弱词可以复习或定向出题。\n词条熟练度会随作答更新；连续答对会升，答错会降。',
  },
  {
    id: 'profile-card',
    match: /^\/profile-card/,
    title: '个人画像',
    sections: ['学习画像', '优势与薄弱', '成就'],
    render: () => '这里是个人画像：展示学习画像、优势与薄弱、成就。\n画像来自真实行为；如果觉得哪条不准，可以在个人中心重新填偏好问卷。',
  },
  {
    id: 'video',
    match: /^\/video/,
    title: '视频库',
    sections: ['视频列表', '播放', '收藏与评论'],
    render: () => '这里是视频库/视频详情：可以看知识点讲解、收藏和评论。\n视频适合先建立直觉；看完回到练习页做两题，才算真的掌握。',
  },
]

export function getPageFramework(path = '') {
  return FRAMEWORKS.find(f => f.match.test(path)) || null
}

export function localOverview(path, ctx = {}) {
  const fw = getPageFramework(path)
  if (fw) {
    try {
      const data = fw.extract ? fw.extract(ctx) : {}
      return { title: fw.title, sections: fw.sections, text: fw.render(data) }
    } catch {
      return { title: fw.title, sections: fw.sections, text: `${fw.title}：${(fw.sections || []).join('、')}。` }
    }
  }
  // 未知页面：只用标题 + 1200 字片段做本地概述，不调模型
  const hs = headings(8)
  const snippet = bodySnippet(1200)
  const head = hs.length ? `这一页包含：${hs.join('、')}。` : '这一页有一个主内容区。'
  const body = snippet ? `\n页面摘要：${snippet.slice(0, 180)}…` : ''
  return {
    title: document.title || path || '当前页面',
    sections: hs,
    text: `${head}${body}\n需要更细的总结，可以点「让小基细说」。`,
  }
}

export function pageLightContext(path) {
  const fw = getPageFramework(path)
  return {
    page_key: fw?.id || 'generic',
    title: fw?.title || (document.title || path || '当前页面'),
    framework: fw?.sections || headings(8),
    snippet: bodySnippet(1200),
  }
}
