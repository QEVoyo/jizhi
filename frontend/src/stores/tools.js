import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getCheckin, saveCheckin, getCountdown, saveCountdown, getTimer, saveTimer } from '@/api/tools'

export const useToolsStore = defineStore('tools', () => {
  // ===== 打卡 =====
  const checkinProjects = ref([])

  async function loadCheckin(userId) {
    try {
      const data = await getCheckin(userId)
      checkinProjects.value = data.projects || []
    } catch (e) {
      console.error('加载打卡失败', e)
    }
  }

  async function saveCheckinData(userId, projects) {
    try {
      await saveCheckin(userId, projects)
      checkinProjects.value = projects
    } catch (e) {
      console.error('保存打卡失败', e)
    }
  }

  function addCheckinProject(name, targetDays) {
    checkinProjects.value.push({
      name,
      target_days: targetDays,
      completed_days: 0,
      last_checkin: null
    })
  }

  function deleteCheckinProject(name) {
    checkinProjects.value = checkinProjects.value.filter(p => p.name !== name)
  }

  function doCheckin(name) {
    const project = checkinProjects.value.find(p => p.name === name)
    if (!project) return false
    const today = new Date().toISOString().slice(0, 10)
    if (project.last_checkin === today) return false
    project.completed_days += 1
    project.last_checkin = today
    return true
  }

  // ===== 倒计时（时间胶囊，2026-08-26 改版）=====
  // 胶囊对象：{ id, title, target_date, created_at, entries: [{content, created_at}], opened_at }
  // 状态派生：opened_at 非空 = 已开启；到期未开启 = 待开启；否则 = 密封中
  const countdownEvents = ref([])

  async function loadCountdown(userId) {
    try {
      const data = await getCountdown(userId)
      countdownEvents.value = (data.events || []).map(migrateCapsule)
    } catch (e) {
      console.error('加载时间胶囊失败', e)
    }
  }

  async function saveCountdownData(userId, events) {
    try {
      await saveCountdown(userId, events)
      countdownEvents.value = events
    } catch (e) {
      console.error('保存时间胶囊失败', e)
    }
  }

  // 老数据迁移：{id, name, target_date} → 胶囊结构（title=name, entries=[], opened_at=null）
  function migrateCapsule(e) {
    if (e && e.title === undefined && e.name !== undefined) {
      return {
        id: e.id,
        title: e.name,
        target_date: e.target_date,
        created_at: e.created_at || new Date().toISOString(),
        entries: [],
        opened_at: null
      }
    }
    return e
  }

  function addCapsule(title, targetDate, firstMessage) {
    countdownEvents.value.push({
      id: 'cap_' + Date.now(),
      title,
      target_date: targetDate,
      created_at: new Date().toISOString(),
      entries: firstMessage ? [{ content: firstMessage, created_at: new Date().toISOString() }] : [],
      opened_at: null
    })
  }

  function appendCapsuleEntry(id, content) {
    const cap = countdownEvents.value.find(e => e.id === id)
    if (!cap) return
    cap.entries.push({ content, created_at: new Date().toISOString() })
  }

  function openCapsule(id) {
    const cap = countdownEvents.value.find(e => e.id === id)
    if (!cap) return
    cap.opened_at = new Date().toISOString()
  }

  function deleteCountdownEvent(id) {
    countdownEvents.value = countdownEvents.value.filter(e => e.id !== id)
  }

  // ===== 计时器 =====
  const timerTemplates = ref([])

  async function loadTimer(userId) {
    try {
      const data = await getTimer(userId)
      timerTemplates.value = data.timers || []
    } catch (e) {
      console.error('加载计时器失败', e)
    }
  }

  async function saveTimerData(userId, timers) {
    try {
      await saveTimer(userId, timers)
      timerTemplates.value = timers
    } catch (e) {
      console.error('保存计时器失败', e)
    }
  }

  function addTimerTemplate(name, type, durationMinutes = 25) {
    timerTemplates.value.push({
      id: 'tmr_' + Date.now(),
      name,
      type: type, // 'countdown' | 'stopwatch'
      duration_minutes: durationMinutes
    })
  }

  function deleteTimerTemplate(id) {
    timerTemplates.value = timerTemplates.value.filter(t => t.id !== id)
  }

  return {
    // 打卡
    checkinProjects,
    loadCheckin,
    saveCheckinData,
    addCheckinProject,
    deleteCheckinProject,
    doCheckin,
    // 倒计时（时间胶囊）
    countdownEvents,
    loadCountdown,
    saveCountdownData,
    addCapsule,
    appendCapsuleEntry,
    openCapsule,
    deleteCountdownEvent,
    // 计时器
    timerTemplates,
    loadTimer,
    saveTimerData,
    addTimerTemplate,
    deleteTimerTemplate
  }
})