import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const STORAGE_KEY = 'jizhi-sessions'

export const useSessionStore = defineStore('session', () => {
  const sessions = ref([])
  const currentSessionId = ref(null)

  const currentSession = computed(() => {
    return sessions.value.find(s => s.id === currentSessionId.value) || null
  })

  function loadSessions() {
    try {
      const data = localStorage.getItem(STORAGE_KEY)
      if (data) {
        const parsed = JSON.parse(data)
        sessions.value = parsed.sessions || []
        currentSessionId.value = parsed.currentSessionId || null
      }
    } catch (e) {
      console.error('加载会话失败', e)
    }
  }

  function saveSessions() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({
        sessions: sessions.value,
        currentSessionId: currentSessionId.value
      }))
    } catch (e) {
      console.error('保存会话失败', e)
    }
  }

  function createSession(title = '新对话') {
    const id = 'session_' + Date.now()
    sessions.value.unshift({
      id,
      title,
      messages: [],
      createdAt: new Date().toISOString()
    })
    currentSessionId.value = id
    saveSessions()
    return id
  }

  function switchSession(id) {
    const session = sessions.value.find(s => s.id === id)
    if (session) {
      currentSessionId.value = id
      saveSessions()
    }
  }

  function deleteSession(id) {
    sessions.value = sessions.value.filter(s => s.id !== id)
    if (currentSessionId.value === id) {
      currentSessionId.value = sessions.value.length > 0 ? sessions.value[0].id : null
    }
    saveSessions()
  }

  function updateSessionTitle(id, title) {
    const session = sessions.value.find(s => s.id === id)
    if (session) {
      session.title = title
      saveSessions()
    }
  }

  function addMessage(sessionId, role, content) {
    const session = sessions.value.find(s => s.id === sessionId)
    if (session) {
      session.messages.push({ role, content, timestamp: new Date().toISOString() })
      saveSessions()
    }
  }

  function getMessages(sessionId) {
    const session = sessions.value.find(s => s.id === sessionId)
    return session ? session.messages : []
  }

  function clearMessages(sessionId) {
    const session = sessions.value.find(s => s.id === sessionId)
    if (session) {
      session.messages = []
      saveSessions()
    }
  }

  return {
    sessions,
    currentSessionId,
    currentSession,
    loadSessions,
    saveSessions,
    createSession,
    switchSession,
    deleteSession,
    updateSessionTitle,
    addMessage,
    getMessages,
    clearMessages
  }
})