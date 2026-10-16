-- ============================================================
-- 基智学习助手 - 数据库迁移（一次性执行）
-- Supabase Dashboard -> SQL Editor
-- ============================================================

-- 1. 用户偏好字段
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS learning_goal TEXT DEFAULT '';
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS difficulty_preference TEXT DEFAULT '';
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS learning_style TEXT DEFAULT '';
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS daily_study_time TEXT DEFAULT '';

-- 2. 通知扩展字段
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS summary TEXT DEFAULT '';
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS image_url TEXT DEFAULT '';
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS action_label TEXT DEFAULT '';
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS action_link TEXT DEFAULT '';
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS msg_count INTEGER DEFAULT 1;

-- 3. 通知设置表
CREATE TABLE IF NOT EXISTS notification_settings (
    user_id UUID PRIMARY KEY REFERENCES profiles(id) ON DELETE CASCADE,
    chat_enabled BOOLEAN DEFAULT true,
    social_enabled BOOLEAN DEFAULT true,
    learning_enabled BOOLEAN DEFAULT true,
    plan_reminder_enabled BOOLEAN DEFAULT true,
    evaluation_enabled BOOLEAN DEFAULT true,
    daily_rec_enabled BOOLEAN DEFAULT true,
    daily_summary_enabled BOOLEAN DEFAULT true,
    system_enabled BOOLEAN DEFAULT true,
    daily_rec_time TIME DEFAULT '08:00',
    daily_summary_time TIME DEFAULT '07:00',
    retention_days INTEGER DEFAULT 30,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. 清空旧通知数据（旧逻辑每条消息一行，会产生大量重复）
DELETE FROM notifications;
