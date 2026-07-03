import request from '@/utils/request'

/**
 * 搜索B站视频
 * @param {string} keyword - 搜索关键词
 * @param {number} page - 页码
 * @param {number} pageSize - 每页数量
 */
export function searchBilibili(keyword, page = 1, pageSize = 4) {
  return request.get('/video/search', {
    params: { keyword, page, page_size: pageSize }
  }).then(res => res.data)
}