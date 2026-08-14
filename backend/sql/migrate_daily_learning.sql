-- 每日学习内容迁移 — 在 Supabase SQL Editor 执行

-- 1. plan_daily_tasks 加阶段字段
ALTER TABLE plan_daily_tasks ADD COLUMN IF NOT EXISTS phase TEXT DEFAULT '基础期';

-- 2. plan_daily_tasks 加学习讲解缓存（AI 生成后缓存，避免重复生成）
ALTER TABLE plan_daily_tasks ADD COLUMN IF NOT EXISTS learning_content JSONB;

-- 3. plan_daily_tasks 加难度字段（从易到难排序用）
ALTER TABLE plan_daily_tasks ADD COLUMN IF NOT EXISTS difficulty_level INTEGER DEFAULT 1;

-- 4. subject_plans 加每日预计时长说明
ALTER TABLE subject_plans ADD COLUMN IF NOT EXISTS daily_time_hint TEXT;
