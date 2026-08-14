-- =============================================
-- 管理员系统 — 全部建表 SQL
-- 在 Supabase Dashboard → SQL Editor 中执行
-- =============================================

-- ===== 1. profiles 表加字段 =====
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;

-- ===== 2. 用户反馈记录 =====
CREATE TABLE IF NOT EXISTS user_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    nickname TEXT,
    email TEXT,
    feedback_type TEXT,                  -- bug / suggestion / other
    content TEXT NOT NULL,
    status TEXT DEFAULT 'pending',       -- pending / resolved
    admin_note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

-- ===== 3. 用户 Q&A 记录 =====
CREATE TABLE IF NOT EXISTS user_qa (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    nickname TEXT,
    email TEXT,
    question TEXT NOT NULL,
    image_url TEXT,
    status TEXT DEFAULT 'pending',       -- pending / resolved
    admin_note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

-- ===== 4. 内容举报记录 =====
CREATE TABLE IF NOT EXISTS content_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reporter_id UUID,
    reporter_nickname TEXT,
    target_type TEXT NOT NULL,           -- post / comment
    target_id UUID,
    reason TEXT,
    status TEXT DEFAULT 'pending',       -- pending / resolved / dismissed
    admin_id UUID,
    admin_note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

-- ===== 5. 系统公告 =====
CREATE TABLE IF NOT EXISTS system_announcements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    content TEXT,
    image_url TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ===== 6. 管理员操作日志 =====
CREATE TABLE IF NOT EXISTS admin_audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_id UUID NOT NULL,
    admin_nickname TEXT,
    action TEXT NOT NULL,                -- ban_user / unban_user / delete_post / edit_question / ...
    target_type TEXT,                    -- user / post / question / syllabus / feedback / ...
    target_id TEXT,
    detail JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ===== 索引 =====
CREATE INDEX IF NOT EXISTS idx_user_feedback_status ON user_feedback(status);
CREATE INDEX IF NOT EXISTS idx_user_feedback_created ON user_feedback(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_user_qa_status ON user_qa(status);
CREATE INDEX IF NOT EXISTS idx_content_reports_status ON content_reports(status);
CREATE INDEX IF NOT EXISTS idx_content_reports_target ON content_reports(target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_announcements_active ON system_announcements(is_active);
CREATE INDEX IF NOT EXISTS idx_admin_logs_admin ON admin_audit_logs(admin_id);
CREATE INDEX IF NOT EXISTS idx_admin_logs_action ON admin_audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_admin_logs_created ON admin_audit_logs(created_at DESC);

-- ===== RLS 策略（可重复执行）=====
ALTER TABLE user_feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_qa ENABLE ROW LEVEL SECURITY;
ALTER TABLE content_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_announcements ENABLE ROW LEVEL SECURITY;
ALTER TABLE admin_audit_logs ENABLE ROW LEVEL SECURITY;

-- 反馈
DROP POLICY IF EXISTS "Anyone can insert feedback" ON user_feedback;
DROP POLICY IF EXISTS "API can manage feedback" ON user_feedback;
CREATE POLICY "Anyone can insert feedback" ON user_feedback FOR INSERT WITH CHECK (true);
CREATE POLICY "API can manage feedback" ON user_feedback FOR ALL USING (true) WITH CHECK (true);

-- Q&A
DROP POLICY IF EXISTS "Anyone can insert qa" ON user_qa;
DROP POLICY IF EXISTS "API can manage qa" ON user_qa;
CREATE POLICY "Anyone can insert qa" ON user_qa FOR INSERT WITH CHECK (true);
CREATE POLICY "API can manage qa" ON user_qa FOR ALL USING (true) WITH CHECK (true);

-- 举报
DROP POLICY IF EXISTS "Anyone can insert reports" ON content_reports;
DROP POLICY IF EXISTS "API can manage reports" ON content_reports;
CREATE POLICY "Anyone can insert reports" ON content_reports FOR INSERT WITH CHECK (true);
CREATE POLICY "API can manage reports" ON content_reports FOR ALL USING (true) WITH CHECK (true);

-- 公告
DROP POLICY IF EXISTS "Anyone can read announcements" ON system_announcements;
DROP POLICY IF EXISTS "API can manage announcements" ON system_announcements;
CREATE POLICY "Anyone can read announcements" ON system_announcements FOR SELECT USING (true);
CREATE POLICY "API can manage announcements" ON system_announcements FOR ALL USING (true) WITH CHECK (true);

-- 日志
DROP POLICY IF EXISTS "Anyone can read audit logs" ON admin_audit_logs;
DROP POLICY IF EXISTS "API can insert audit logs" ON admin_audit_logs;
CREATE POLICY "Anyone can read audit logs" ON admin_audit_logs FOR SELECT USING (true);
CREATE POLICY "API can insert audit logs" ON admin_audit_logs FOR INSERT WITH CHECK (true);
