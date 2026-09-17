-- ============================================================
-- 智能体中心数据层 DDL（原则：能用现有表就不建新表）
--
-- 复用现有表：
--   user_actions     — 触点调用计数（action_type + metadata.touchpoint，已支持）
--   plan_daily_tasks — 计划完成率 / 每日讲解（learning_content）
--   subject_plans    — 计划来源（补 source 列）
--   question_records — 答题 / 批改（ai_feedback 非空）/ 重做正确率
--   exam_paper_records — 真题交卷 + 错题分析（question_results）
--   generation_history — 生成题目历史
--   question_sets    — 题集
--   learning_logs    — 对话日志摘要
--   xiaoji_messages  — 小基消息（补 kind 列区分触点）
--   user_kp_mastery  — 知识点掌握度
--   profile_card_settings — 画像 AI 总结
--   diagnosis_results — 诊断记录
--
-- 真正需要新建的只有 2 张表 + 2 个补列迁移
-- 在 Supabase Dashboard → SQL Editor 中执行（可重复执行）
-- ============================================================

-- 1. 智能体共享参数（agent_prefs）：参数持久化，一处调全触点生效
CREATE TABLE IF NOT EXISTS agent_prefs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    agent_key TEXT NOT NULL,             -- chat / plan / generate / evaluate / xiaoji
    param_key TEXT NOT NULL,             -- style / tasks / difficulty ...
    param_value JSONB NOT NULL DEFAULT '{}',
    auto_managed BOOLEAN DEFAULT FALSE,  -- 自动托管开关（磨合规则接管）
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, agent_key, param_key)
);

-- 2. 磨合记录（agent_tuning_log）：参数调整审计，趋势图 markLine 的数据源
CREATE TABLE IF NOT EXISTS agent_tuning_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    agent_key TEXT NOT NULL,
    param_key TEXT NOT NULL,
    old_value JSONB,
    new_value JSONB,
    reason TEXT,                         -- 触发规则描述（如「完成率 38% < 50%」）
    source TEXT DEFAULT 'auto',          -- auto（磨合规则）/ manual（用户手动）
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. 补列：小基消息区分触点（chat / vision / evaluate）
ALTER TABLE xiaoji_messages ADD COLUMN IF NOT EXISTS kind TEXT DEFAULT 'chat';

-- 4. 补列：计划来源区分（diagnosis / exam_paper / chat）
ALTER TABLE subject_plans ADD COLUMN IF NOT EXISTS source TEXT DEFAULT 'diagnosis';

-- ===== RLS（与 subject_plan_tables.sql 惯例一致：认证在 API 层） =====
ALTER TABLE agent_prefs ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_tuning_log ENABLE ROW LEVEL SECURITY;
CREATE POLICY "API can manage agent prefs" ON agent_prefs FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "API can manage tuning log" ON agent_tuning_log FOR ALL USING (true) WITH CHECK (true);

-- ===== 授权（Supabase 手工建表不会自动 GRANT，必须显式授权） =====
GRANT SELECT, INSERT, UPDATE, DELETE ON public.agent_prefs TO anon, authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.agent_tuning_log TO anon, authenticated, service_role;

-- ===== 索引 =====
CREATE INDEX IF NOT EXISTS idx_agent_prefs_user ON agent_prefs(user_id, agent_key);
CREATE INDEX IF NOT EXISTS idx_tuning_log_user ON agent_tuning_log(user_id, agent_key, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_xiaoji_messages_kind ON xiaoji_messages(user_id, kind);
