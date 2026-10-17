// src/api/upload.js
import { useAuthStore } from '@/stores/auth'

/**
 * Supabase Storage 的 object key 必须是 ASCII 安全字符：
 * 中文文件名（如「屏幕录制_….mp4」）会直接报 InvalidKey。
 * 这里只保留字母/数字/下划线/短横线，其余压成下划线，并保留原扩展名。
 */
function safeStorageName(name, fallback = 'file', defaultExt = '') {
  const raw = String(name || '')
  const extMatch = raw.match(/\.([a-zA-Z0-9]{1,10})$/)
  const ext = extMatch ? extMatch[1].toLowerCase() : ''
  const base = raw.replace(/\.[^/.]+$/, '')
  const safeBase = base
    .replace(/[^a-zA-Z0-9_-]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .slice(0, 60) || fallback
  const finalExt = ext || defaultExt
  return finalExt ? `${safeBase}.${finalExt}` : safeBase
}

export async function uploadImage(file) {
  const authStore = useAuthStore()
  const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
  const supabaseKey = import.meta.env.VITE_SUPABASE_KEY

  if (!supabaseUrl || !supabaseKey) {
    throw new Error('Supabase 配置缺失，请检查 .env 文件')
  }

  const timestamp = Date.now()
  const random = Math.random().toString(36).substring(2, 8)
  const filename = `${timestamp}_${random}_${safeStorageName(file.name, 'image', 'jpg')}`

  console.log('📤 上传文件名:', filename)

  const url = `${supabaseUrl}/storage/v1/object/chat-images/${filename}`

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${supabaseKey}`,
      'Content-Type': file.type
    },
    body: file
  })

  if (!response.ok) {
    const errorText = await response.text()
    console.error('上传失败:', errorText)
    throw new Error(`图片上传失败: ${response.status}`)
  }

  const publicUrl = `${supabaseUrl}/storage/v1/object/public/chat-images/${filename}`
  console.log('✅ 上传成功:', publicUrl)
  return publicUrl
}

/**
 * 视频留存上传（2026-10-17）。
 * 复用 chat-images 桶；成功后返回公共 URL，写进 xiaoji_messages.video_url。
 * ⚠️ 视频文件大小受 Supabase 桶配置限制（默认 50MB），调用方先做前端提示。
 */
export async function uploadVideo(file) {
  const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
  const supabaseKey = import.meta.env.VITE_SUPABASE_KEY
  if (!supabaseUrl || !supabaseKey) {
    throw new Error('Supabase 配置缺失，请检查 .env 文件')
  }

  const filename = `${Date.now()}_${Math.random().toString(36).substring(2, 8)}_${safeStorageName(file.name, 'video', 'mp4')}`
  const url = `${supabaseUrl}/storage/v1/object/chat-images/${filename}`

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${supabaseKey}`,
      'Content-Type': file.type || 'video/mp4',
    },
    body: file,
  })

  if (!response.ok) {
    const errorText = await response.text()
    console.error('视频上传失败:', errorText)
    throw new Error(`视频上传失败: ${response.status} ${errorText.slice(0, 120)}`)
  }

  const publicUrl = `${supabaseUrl}/storage/v1/object/public/chat-images/${filename}`
  console.log('✅ 视频留存成功:', publicUrl)
  return publicUrl
}