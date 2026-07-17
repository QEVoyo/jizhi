// src/api/upload.js
import { useAuthStore } from '@/stores/auth'

export async function uploadImage(file) {
  const authStore = useAuthStore()
  const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
  const supabaseKey = import.meta.env.VITE_SUPABASE_KEY

  if (!supabaseUrl || !supabaseKey) {
    throw new Error('Supabase 配置缺失，请检查 .env 文件')
  }

  // ✅ 清理文件名：只保留字母、数字、下划线、点
  const originalName = file.name
  const ext = originalName.split('.').pop() || 'jpg'
  const nameWithoutExt = originalName.replace(/\.[^/.]+$/, '')
  const cleanName = nameWithoutExt.replace(/[^a-zA-Z0-9\u4e00-\u9fa5]/g, '_')

  const timestamp = Date.now()
  const random = Math.random().toString(36).substring(2, 8)
  const filename = `${timestamp}_${random}_${cleanName}.${ext}`

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