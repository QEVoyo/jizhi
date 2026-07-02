import request from '@/utils/request'

export function login(loginInput, password) {
  return request.post('/auth/login', { login_input: loginInput, password })
    .then(res => res.data)
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