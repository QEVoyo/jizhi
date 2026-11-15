/**
 * 页面事件 → 小基反应（2026-11-11）
 *
 * 规则只描述「什么事件、什么表情、说哪句」，不含 DOM / Vue。
 * 文案按既定口径：界面专业，小基对白口语化，一句不超过 20 字左右。
 */

import { XIAOJI_EVENT as E } from './bus'

const L = {
  correct: [
    '稳，这题拿下了。',
    '漂亮，思路是对的。',
    '对了，记住这一步。',
  ],
  wrong: [
    '没关系，看看错因。',
    '这题值一个复盘。',
    '先别急，错因比答案重要。',
  ],
  genStart: [
    '开始搞了，你先去忙别的。',
    '生成中，我盯着进度。',
  ],
  genDone: [
    '弄好了，去看看结果？',
    '出炉了，检查一下？',
  ],
  genError: [
    '我这边卡了一下，再试一次？',
    '这次没成，别急，再试一次。',
  ],
  planStart: [
    '计划开始排了，稍等一会儿。',
    '我在排计划，你先歇会儿。',
  ],
  planDone: [
    '计划排好了，去看看？',
    '路线出来了，检查一下？',
  ],
  planError: [
    '计划没排成，我再看一眼。',
    '这次没排出来，再试一次？',
  ],
  taskDone: [
    '这一步完成啦。',
    '搞定一件，继续。',
  ],
  taskFail: [
    '这次没跑完，看看原因？',
    '任务卡住了，我记下了。',
  ],
  saved: [
    '保存好了。',
    '记下了。',
  ],
  network: [
    '网络抖了一下，稍后再试。',
    '我这边没连上，等会儿再试。',
  ],
  achievement: [
    '又解锁一个，厉害。',
    '这个成就拿下了。',
  ],
}

/**
 * 事件 → 反应规则。
 * look: idle / happy / thinking / speaking / sleeping
 * duration: 表情保持毫秒；0 表示不自动回 idle
 * cooldown: 同一事件的节流毫秒
 * lines: 随机挑一句；不填则只做表情
 * bubbleMs: 这句话在头像旁停留多久
 * quietOnExam: 考试页只做表情、不弹字
 */
export const REACTIONS = {
  [E.ANSWER_SUBMIT]: {
    look: 'thinking', duration: 1800, cooldown: 2500, quietOnExam: true,
  },
  [E.ANSWER_CORRECT]: {
    look: 'happy', duration: 2600, cooldown: 1200,
    lines: L.correct, bubbleMs: 3200, quietOnExam: true,
  },
  [E.ANSWER_WRONG]: {
    look: 'thinking', duration: 3200, cooldown: 1200,
    lines: L.wrong, bubbleMs: 3800, quietOnExam: true,
  },
  [E.GENERATION_START]: {
    look: 'thinking', duration: 4200, cooldown: 6000,
    lines: L.genStart, bubbleMs: 3200,
  },
  [E.GENERATION_DONE]: {
    look: 'happy', duration: 3000, cooldown: 4000,
    lines: L.genDone, bubbleMs: 3600,
  },
  [E.GENERATION_ERROR]: {
    look: 'thinking', duration: 3600, cooldown: 6000,
    lines: L.genError, bubbleMs: 4200,
  },
  [E.PLAN_GENERATE_START]: {
    look: 'thinking', duration: 4200, cooldown: 6000,
    lines: L.planStart, bubbleMs: 3200,
  },
  [E.PLAN_GENERATE_DONE]: {
    look: 'happy', duration: 3000, cooldown: 4000,
    lines: L.planDone, bubbleMs: 3600,
  },
  [E.PLAN_GENERATE_ERROR]: {
    look: 'thinking', duration: 3600, cooldown: 6000,
    lines: L.planError, bubbleMs: 4200,
  },
  [E.TASK_COMPLETE]: {
    look: 'happy', duration: 2600, cooldown: 4000,
    lines: L.taskDone, bubbleMs: 3200,
  },
  [E.TASK_FAIL]: {
    look: 'thinking', duration: 3200, cooldown: 5000,
    lines: L.taskFail, bubbleMs: 3800,
  },
  [E.SAVE_SUCCESS]: {
    look: 'happy', duration: 2000, cooldown: 3000,
    lines: L.saved, bubbleMs: 2600,
  },
  [E.NETWORK_ERROR]: {
    look: 'thinking', duration: 3000, cooldown: 8000,
    lines: L.network, bubbleMs: 3600,
  },
  [E.ACHIEVEMENT_UNLOCK]: {
    look: 'happy', duration: 3200, cooldown: 5000,
    lines: L.achievement, bubbleMs: 3600,
  },
}

function pickLine(lines) {
  if (!Array.isArray(lines) || !lines.length) return ''
  return lines[Math.floor(Math.random() * lines.length)]
}

/** 把一条事件整理成组件能直接用的反应；不认识的事件返回 null。 */
export function resolveReaction(detail) {
  if (!detail || !detail.type) return null

  // 直接控制：任何页面都能让小基说一句 / 做个表情
  if (detail.type === E.SAY) {
    const text = String(detail.text || '').trim()
    if (!text) return null
    return {
      look: detail.look || 'speaking',
      duration: detail.ms || 3600,
      cooldown: 0,
      text: text.slice(0, 40),
      bubbleMs: detail.ms || 3800,
      quietOnExam: false,
      force: true,
    }
  }
  if (detail.type === E.REACT) {
    return {
      look: detail.look || 'happy',
      duration: detail.ms || 1800,
      cooldown: 0,
      text: '',
      bubbleMs: 0,
      quietOnExam: false,
      force: true,
    }
  }

  const rule = REACTIONS[detail.type]
  if (!rule) return null
  return {
    look: rule.look || 'happy',
    duration: rule.duration || 2200,
    cooldown: rule.cooldown || 0,
    text: pickLine(rule.lines),
    bubbleMs: rule.bubbleMs || 3200,
    // 只有答题类事件默认在考试页闭嘴；生成/计划/网络是用户主动触发的，
    // 即使人在考试页也应该有文字反馈。
    quietOnExam: rule.quietOnExam === true,
    force: false,
  }
}
