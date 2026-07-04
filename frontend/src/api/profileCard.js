import request from '@/utils/request'

export function getProfileCard(userId, currentUserId) {
  return request.get(`/profile-card/${userId}`, {
    params: { current_user_id: currentUserId }
  }).then(res => res.data)
}

export function updateProfileCardSettings(userId, data) {
  return request.put('/profile-card/settings', data, {
    params: { user_id: userId }
  }).then(res => res.data)
}