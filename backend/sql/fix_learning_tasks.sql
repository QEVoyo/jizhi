-- learning_tasks 表缺 video_query 列修复
-- 背景（2026-08-30 排查「生成不出来」）：
--   POST /learning-plan/create 保存任务时报 400
--   "Could not find the 'video_query' column of 'learning_tasks' in the schema cache"（PGRST204）
--   → 自定义计划（学习规划）的保存整链失败。
-- 在 Supabase SQL Editor 执行一次即可（幂等）。

ALTER TABLE public.learning_tasks ADD COLUMN IF NOT EXISTS video_query TEXT DEFAULT '';