-- ============================================================
-- 小基视频消息留存（2026-10-17）
--
-- 视频用户消息的存储约定：
--   image_url  = 首帧缩略图（WebP data URL，体积很小）
--   video_url  = 原视频在 Supabase Storage 的公共 URL（chat-images 桶）
--   kind       = 'video'
--   content    = 用户当时的问题（没有问题时为空字符串，不再显示占位符）
--
-- 幂等，可直接在 Supabase SQL Editor 执行。
-- ============================================================

ALTER TABLE public.xiaoji_messages
  ADD COLUMN IF NOT EXISTS video_url TEXT;

COMMENT ON COLUMN public.xiaoji_messages.video_url IS
  '视频消息的原视频 URL；image_url 存首帧缩略图。非视频消息为 NULL。';
