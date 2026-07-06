import request from '@/utils/request'

export function login(loginInput, password) {
  const payload = { login_input: loginInput, password }
  console.log('=== 登录请求体 ===', payload)
  return request.post('/auth/login', payload)
    .then(res => {
      console.log('=== 登录响应 ===', res.data)
      return res.data
    })
}

export function register(email, password, nickname) {
  return request.post('/auth/register', { email, password, nickname })
    .then(res => res.data)
}

export function getProfile(userId) {
  return request.get(`/auth/profile/${userId}`)
    .then(res => res.data)
}

export function updateNickname(userId, nickname) {
  return request.put('/auth/update-nickname', { user_id: userId, nickname })
    .then(res => res.data)
}

export function updateBio(userId, bio) {
  return request.put('/auth/update-bio', { user_id: userId, bio })
    .then(res => res.data)
}

export function uploadAvatar(userId, file) {
  const formData = new FormData()
  formData.append('file', file)
  return request.post(`/auth/upload-avatar/${userId}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }).then(res => res.data)
}
export function updatePassword(accessToken, newPassword) {
  return request({
    url: '/auth/update-password',
    method: 'put',
    data: { new_password: newPassword },
    headers: {
      Authorization: `Bearer ${accessToken}`
    }
  }).then(res => res.data)
}
export function updateStatus(userId, status) {
  return request.put('/auth/status', null, {
    params: { user_id: userId, status }
  }).then(res => res.data)
}
// 临时占位，后端没有 /auth/logout 接口，直接返回成功
export function logout() {
  return Promise.resolve({ success: true })
}
export function getUserInfo() {
  return Promise.resolve({ success: true, user: null })
}