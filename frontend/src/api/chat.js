import { getToken } from '@/utils/storage'
import { BACKEND_URL } from '@/utils/constants'

export async function sendChatMessage(messages, userId, temperature = 0.7, intent = 'chat') {
  const token = getToken()

  const response = await fetch(`${BACKEND_URL}/chat/send`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': token ? `Bearer ${token}` : ''
    },
    body: JSON.stringify({
      messages,
      user_id: userId,
      temperature,
      intent
    })
  })

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }

  return response
}

export function saveLog(userId, keyword) {
  return fetch(`${BACKEND_URL}/chat/log`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getToken()}`
    },
    body: JSON.stringify({ user_id: userId, keyword })
  }).then(res => res.json())
}
export async function extractSummary(content, userId) {
  const token = getToken()
  const response = await fetch(`${BACKEND_URL}/chat/summary`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': token ? `Bearer ${token}` : ''
    },
    body: JSON.stringify({ content, user_id: userId })
  })
  return response.json()
}