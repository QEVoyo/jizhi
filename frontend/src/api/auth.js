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

// ✅ 修改：注册增加 code 参数
export function register(email, password, code, nickname) {
  return request.post('/auth/register', { email, password, code, nickname })
    .then(res => res.data)
}

// ✅ 新增：发送验证码
export function sendVerificationCode(email) {
  return request.post('/auth/send-code', null, {
    params: { email }
  }).then(res => res.data)
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

export function updatePassword(userId, oldPassword, newPassword) {
  return request({
    url: '/auth/update-password',
    method: 'put',
    params: { user_id: userId },
    data: { old_password: oldPassword, new_password: newPassword }
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

export function updateLearningInfo(data) {
  return request.put('/auth/update-learning-info', {
    user_id: data.user_id,
    learning_stage: data.learning_stage || '',
    grade: data.grade || '',
    major: data.major || '',
    learning_goal: data.learning_goal || '',
    difficulty_preference: data.difficulty_preference || '',
    learning_style: data.learning_style || '',
    daily_study_time: data.daily_study_time || ''
  }).then(res => res.data)
}

export function getUserInfo() {
  return Promise.resolve({ success: true, user: null })
}

// ===== 微信扫码登录（公众号测试号）=====

// 获取登录二维码 + 轮询 token
export function getWechatQrcode(redirect = '/home') {
  return request.get('/auth/wechat/qrcode', { params: { redirect } })
    .then(res => res.data)
}

// 轮询：检查用户是否已扫码授权
export function wechatPoll(pollToken) {
  return request.get(`/auth/wechat/poll/${pollToken}`)
    .then(res => res.data)
}

// ===== 微信绑定（已登录用户在个人中心绑微信）=====

// 获取绑定微信的二维码
export function getWechatBindQrcode() {
  return request.get('/auth/wechat/bind-qrcode')
    .then(res => res.data)
}

// 获取微信用户资料
export function getWechatUser(userId) {
  return request.get(`/auth/wechat/user/${userId}`)
    .then(res => res.data)
}