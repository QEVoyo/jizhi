import request from '@/utils/request'

// ============================================================
// 1. 动态
// ============================================================

export function getPosts(params) {
  return request.get('/community/posts', { params }).then(res => res.data)
}

export function getPost(postId, userId) {
  return request.get(`/community/post/${postId}`, { params: { user_id: userId } }).then(res => res.data)
}

export function createPost(data) {
  return request.post('/community/post', {
    content: data.content,
    topic: data.topic || null,
    title: data.title || null,
    tags: data.tags || null,
    images: data.images || null
  }, {
    params: { user_id: data.user_id }
  }).then(res => res.data)
}

export function deletePost(postId, userId) {
  return request.delete(`/community/post/${postId}`, { params: { user_id: userId } }).then(res => res.data)
}

// ============================================================
// 2. 点赞 / 收藏
// ============================================================

export function likePost(postId, userId) {
  return request.post(`/community/post/${postId}/like`, null, { params: { user_id: userId } }).then(res => res.data)
}

export function unlikePost(postId, userId) {
  return request.delete(`/community/post/${postId}/like`, { params: { user_id: userId } }).then(res => res.data)
}

export function collectPost(postId, userId) {
  return request.post(`/community/post/${postId}/collect`, null, { params: { user_id: userId } }).then(res => res.data)
}

export function uncollectPost(postId, userId) {
  return request.delete(`/community/post/${postId}/collect`, { params: { user_id: userId } }).then(res => res.data)
}

// ============================================================
// 3. 评论
// ============================================================

export function createComment(data) {
  return request.post(`/community/post/${data.post_id}/comment`, null, {
    params: { user_id: data.user_id },
    data
  }).then(res => res.data)
}

export function getComments(postId) {
  return request.get(`/community/post/${postId}/comments`).then(res => res.data)
}

export function deleteComment(commentId, userId) {
  return request.delete(`/community/comment/${commentId}`, { params: { user_id: userId } }).then(res => res.data)
}

// ============================================================
// 4. 好友
// ============================================================

export function getFriends(userId) {
  return request.get('/community/friends', { params: { user_id: userId } }).then(res => res.data)
}

export function getFriendRequests(userId) {
  return request.get('/community/friends/requests', { params: { user_id: userId } }).then(res => res.data)
}

export function sendFriendRequest(userId, friendId) {
  return request.post('/community/friends/request', null, { params: { user_id: userId, friend_id: friendId } }).then(res => res.data)
}

export function handleFriendRequest(requestId, action, userId) {
  return request.put(`/community/friends/request/${requestId}`, null, { params: { action, user_id: userId } }).then(res => res.data)
}

export function deleteFriend(userId, friendId) {
  return request.delete(`/community/friends/${friendId}`, { params: { user_id: userId } }).then(res => res.data)
}

export function searchUsers(keyword, userId) {
  return request.get('/community/users/search', { params: { keyword, user_id: userId } }).then(res => res.data)
}

// ============================================================
// 5. 私聊
// ============================================================

export function sendMessage(senderId, data) {
  return request.post('/community/message', data, {
    params: { user_id: senderId }
  }).then(res => res.data)
}

export function getMessages(userId, friendId) {
  return request.get(`/community/messages/${friendId}`, { params: { user_id: userId } }).then(res => res.data)
}

export function getUnreadMessageCount(userId) {
  return request.get('/community/messages/unread/count', { params: { user_id: userId } }).then(res => res.data)
}

// ============================================================
// 6. 题集分享
// ============================================================

export function shareQuestionSet(data) {
  return request.post('/community/share/set', null, { params: { user_id: data.sender_id }, data }).then(res => res.data)
}

export function getReceivedShares(userId) {
  return request.get('/community/share/received', { params: { user_id: userId } }).then(res => res.data)
}

export function handleShare(shareId, action, userId) {
  return request.put(`/community/share/set/${shareId}`, null, { params: { action, user_id: userId } }).then(res => res.data)
}

// ============================================================
// 7. 举报
// ============================================================

export function reportContent(data) {
  const payload = {
    target_type: data.target_type,
    target_id: data.target_id,
    reason: data.reason
  }
  return request.post('/community/report', payload, {
    params: { user_id: data.user_id }
  }).then(res => res.data)
}

// ============================================================
// 8. 收藏列表 / 我的发布
// ============================================================

export function getCollections(userId, page = 1, pageSize = 20) {
  return request.get('/community/collections', { params: { user_id: userId, page, page_size: pageSize } }).then(res => res.data)
}

export function getMyPosts(userId, page = 1, pageSize = 20) {
  return request.get('/community/my-posts', { params: { user_id: userId, page, page_size: pageSize } }).then(res => res.data)
}

// ============================================================
// 9. 资料卡
// ============================================================

export function getProfileCard(userId, currentUserId) {
  return request.get(`/community/profile-card/${userId}`, { params: { current_user_id: currentUserId } }).then(res => res.data)
}
// ===== 小基（AI好友） =====
export function getXiaojiMessages(userId) {
  return request.get('/community/xiaoji/messages', { params: { user_id: userId } })
    .then(res => res.data)
}

export function sendXiaojiMessage(data) {
  return request.post('/community/xiaoji/chat', data, {
    params: { user_id: data.user_id }
  }).then(res => res.data)
}

export function getXiaojiConfig(userId) {
  return request.get('/community/xiaoji/config', { params: { user_id: userId } })
    .then(res => res.data)
}

export function updateXiaojiConfig(data) {
  return request.put('/community/xiaoji/config', null, { params: { user_id: data.user_id }, data })
    .then(res => res.data)
}
export function xiaojiVision(data) {
  return request.post('/community/xiaoji/vision', data, {
    params: { user_id: data.user_id }
  }).then(res => res.data)
}
export function saveXiaojiMessage(data) {
  return request.post('/community/xiaoji/save', data, {
    params: { user_id: data.user_id }
  }).then(res => res.data)
}
// ===== 消息中心 =====

export function getUnreadSummary(userId) {
  return request.get('/community/messages/unread/summary', { params: { user_id: userId } })
    .then(res => res.data)
}

export function getUnreadCount(userId) {
  return request.get('/community/messages/unread/count', { params: { user_id: userId } })
    .then(res => res.data)
}

export function markMessagesRead(userId, friendId) {
  return request.put(`/community/messages/read/${friendId}`, null, { params: { user_id: userId } })
    .then(res => res.data)
}

export function getFriendsRank(userId) {
  return request.get('/community/friends/rank', { params: { user_id: userId } }).then(res => res.data)
}

// ===== 消息中心 =====
export function getMessageHistory(params) {
  return request.get('/community/messages/history', { params }).then(res => res.data)
}

export function markAllRead(userId, msgType = 'all') {
  return request.put('/community/messages/read-all', null, { params: { user_id: userId, msg_type: msgType } }).then(res => res.data)
}

export function clearMessages(userId, msgType = 'all') {
  return request.delete('/community/messages/clear', { params: { user_id: userId, msg_type: msgType } }).then(res => res.data)
}

export function deleteMessages(userId, ids) {
  return request.delete('/community/messages', { params: { user_id: userId, ids } }).then(res => res.data)
}

export function getSidebarBadges(userId) {
  return request.get('/community/sidebar-badges', { params: { user_id: userId } }).then(res => res.data)
}

export function getNotificationSettings(userId) {
  return request.get('/community/notification-settings', { params: { user_id: userId } }).then(res => res.data)
}

export function updateNotificationSettings(data) {
  return request.put('/community/notification-settings', data.data, { params: { user_id: data.user_id } }).then(res => res.data)
}