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
  return request.post('/community/post', null, { params: { user_id: data.user_id }, data }).then(res => res.data)
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
  return request.delete('/community/friends', { params: { user_id: userId, friend_id: friendId } }).then(res => res.data)
}

export function searchUsers(keyword, userId) {
  return request.get('/community/users/search', { params: { keyword, user_id: userId } }).then(res => res.data)
}

// ============================================================
// 5. 私聊
// ============================================================

export function sendMessage(data) {
  return request.post('/community/message', null, { params: { user_id: data.sender_id }, data }).then(res => res.data)
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
  return request.post('/community/report', null, { params: { user_id: data.user_id }, data }).then(res => res.data)
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