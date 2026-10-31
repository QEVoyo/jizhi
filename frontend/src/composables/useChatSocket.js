import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { BACKEND_URL } from '@/utils/constants'

// ============================================================
// 社区私聊 WebSocket（2026-10-30）
//
// 一个聊天框一条连接，只订阅当前好友（peer）；服务端也按 peer 过滤。
// 心跳 25s 一次：浏览器发不了协议层 ping，只能应用层 {"type":"ping"}。
// 断线后指数退避重连，重连成功回调 onReconnect，让页面补拉离线消息。
//
// 发消息仍然走 POST /community/message；本连接只负责收。
// ============================================================

const HEARTBEAT_MS = 25000
const PONG_TIMEOUT_MS = 10000
const MAX_BACKOFF_MS = 15000

export function useChatSocket({ peerId, onMessage, onReconnect, enabled = true } = {}) {
  const authStore = useAuthStore()
  const connected = ref(false)

  let ws = null
  let retry = 0
  let everConnected = false
  let closedByUs = false
  let reconnectTimer = null
  let heartbeatTimer = null
  let pongTimer = null

  function wsUrl() {
    const base = (BACKEND_URL || 'http://localhost:8000').replace(/^http/, 'ws')
    const params = new URLSearchParams()
    if (authStore.token) params.set('token', authStore.token)
    if (peerId) params.set('peer', peerId)
    return `${base}/community/ws?${params.toString()}`
  }

  function clearTimers() {
    if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null }
    if (heartbeatTimer) { clearInterval(heartbeatTimer); heartbeatTimer = null }
    if (pongTimer) { clearTimeout(pongTimer); pongTimer = null }
  }

  function startHeartbeat() {
    if (heartbeatTimer) clearInterval(heartbeatTimer)
    heartbeatTimer = setInterval(() => {
      if (!ws || ws.readyState !== WebSocket.OPEN) return
      if (pongTimer) return              // 上一拍还没回，说明连接已经假死
      try { ws.send(JSON.stringify({ type: 'ping' })) } catch { return }
      pongTimer = setTimeout(() => {
        pongTimer = null
        try { ws.close() } catch {}
      }, PONG_TIMEOUT_MS)
    }, HEARTBEAT_MS)
  }

  function scheduleReconnect() {
    if (closedByUs) return
    clearTimeout(reconnectTimer)
    const base = Math.min(MAX_BACKOFF_MS, 1000 * 2 ** retry)
    retry += 1
    // 加一点抖动，避免多个标签页同时重连
    const delay = base + Math.random() * 400
    reconnectTimer = setTimeout(connect, delay)
  }

  function connect() {
    if (!enabled || closedByUs) return
    if (!authStore.token || !authStore.user?.id) return
    if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) return

    try {
      ws = new WebSocket(wsUrl())
    } catch {
      scheduleReconnect()
      return
    }

    ws.onopen = () => {
      connected.value = true
      retry = 0
      startHeartbeat()
      if (everConnected) onReconnect?.()
      everConnected = true
    }

    ws.onmessage = (e) => {
      let data
      try { data = JSON.parse(e.data) } catch { return }
      if (data.type === 'pong') {
        if (pongTimer) { clearTimeout(pongTimer); pongTimer = null }
        return
      }
      if (data.type === 'chat.message' && data.message) onMessage?.(data.message)
    }

    ws.onerror = () => {
      try { ws.close() } catch {}
    }

    ws.onclose = () => {
      connected.value = false
      if (pongTimer) { clearTimeout(pongTimer); pongTimer = null }
      if (heartbeatTimer) { clearInterval(heartbeatTimer); heartbeatTimer = null }
      if (!closedByUs) scheduleReconnect()
    }
  }

  function close() {
    closedByUs = true
    clearTimers()
    if (ws && ws.readyState !== WebSocket.CLOSED) {
      try { ws.close() } catch {}
    }
    ws = null
    connected.value = false
  }

  onMounted(connect)
  onBeforeUnmount(close)

  return { connected, connect, close }
}
