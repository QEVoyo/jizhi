-- =============================================
-- 学科计划 (CET-4 备考系统) 所需的全部 Supabase 表
-- 在 Supabase Dashboard → SQL Editor 中执行
-- =============================================

-- 1. CET-4 题库
CREATE TABLE IF NOT EXISTS cet4_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category TEXT NOT NULL,             -- vocabulary / grammar / reading / translation
    sub_category TEXT NOT NULL,         -- 词义辨析 / 时态语态 / 快速阅读 ...
    kp_name TEXT,                       -- 知识点名称
    kp_id TEXT,                         -- 知识点ID
    question_type TEXT NOT NULL,        -- choice / fill / cloze / translation
    difficulty INTEGER DEFAULT 3,       -- 1-10
    content JSONB NOT NULL DEFAULT '{}', -- {"stem": "...", "options": ["A. xxx", ...]}
    answer JSONB NOT NULL DEFAULT '{}',  -- 正确答案 (choice: "A", fill: "answer text")
    explanation TEXT DEFAULT '',
    tags TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. 学科计划主表
CREATE TABLE IF NOT EXISTS subject_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    subject TEXT NOT NULL DEFAULT 'cet4',
    name TEXT NOT NULL DEFAULT 'CET-4 备考计划',
    goal_score INTEGER NOT NULL DEFAULT 425,
    period_days INTEGER NOT NULL DEFAULT 30,
    daily_minutes INTEGER NOT NULL DEFAULT 60,
    daily_question_count INTEGER NOT NULL DEFAULT 30,
    total_days INTEGER NOT NULL DEFAULT 30,
    completed_days INTEGER NOT NULL DEFAULT 0,
    total_questions INTEGER NOT NULL DEFAULT 0,
    completed_questions INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. 每日任务分配表
CREATE TABLE IF NOT EXISTS plan_daily_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID NOT NULL,
    user_id UUID,
    day_number INTEGER NOT NULL DEFAULT 1,
    date DATE NOT NULL,
    question_ids UUID[] DEFAULT '{}',   -- 当天分配的题目ID列表
    completed_ids UUID[] DEFAULT '{}',  -- 已完成的题目ID
    completed BOOLEAN DEFAULT FALSE,
    score INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 4. 诊断记录表
CREATE TABLE IF NOT EXISTS diagnosis_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID NOT NULL,
    user_id UUID NOT NULL,
    dimension_scores JSONB DEFAULT '{}',   -- {"vocabulary": 80, "grammar": 60, ...}
    weak_points TEXT[] DEFAULT '{}',
    strong_points TEXT[] DEFAULT '{}',
    question_records JSONB DEFAULT '[]',   -- 答案记录数组
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 5. 答题记录表
CREATE TABLE IF NOT EXISTS question_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    plan_id UUID NOT NULL,
    question_id UUID NOT NULL,
    task_id UUID,
    source TEXT DEFAULT 'daily',          -- daily / free / diagnosis
    user_answer JSONB DEFAULT '{}',       -- {"raw": "A"} or {"raw": "answer text"}
    is_correct BOOLEAN DEFAULT FALSE,
    score INTEGER DEFAULT 0,
    ai_feedback JSONB DEFAULT '{}',
    time_spent INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 6. 知识点掌握度跟踪表
CREATE TABLE IF NOT EXISTS user_kp_mastery (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    plan_id UUID NOT NULL,
    kp_id TEXT NOT NULL,
    kp_name TEXT DEFAULT '',
    category TEXT DEFAULT '',
    sub_category TEXT DEFAULT '',
    mastery_score NUMERIC(5,1) DEFAULT 0,   -- 0-100
    correct_count INTEGER DEFAULT 0,
    total_count INTEGER DEFAULT 0,
    last_practiced_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ===== 索引 =====
CREATE INDEX IF NOT EXISTS idx_cet4_questions_category ON cet4_questions(category);
CREATE INDEX IF NOT EXISTS idx_cet4_questions_type ON cet4_questions(question_type);
CREATE INDEX IF NOT EXISTS idx_cet4_questions_difficulty ON cet4_questions(difficulty);
CREATE INDEX IF NOT EXISTS idx_subject_plans_user ON subject_plans(user_id);
CREATE INDEX IF NOT EXISTS idx_subject_plans_status ON subject_plans(status);
CREATE INDEX IF NOT EXISTS idx_plan_daily_tasks_plan ON plan_daily_tasks(plan_id);
CREATE INDEX IF NOT EXISTS idx_plan_daily_tasks_date ON plan_daily_tasks(date);
CREATE INDEX IF NOT EXISTS idx_question_records_user ON question_records(user_id);
CREATE INDEX IF NOT EXISTS idx_question_records_plan ON question_records(plan_id);
CREATE INDEX IF NOT EXISTS idx_question_records_correct ON question_records(is_correct);
CREATE INDEX IF NOT EXISTS idx_user_kp_mastery_user ON user_kp_mastery(user_id);
CREATE INDEX IF NOT EXISTS idx_user_kp_mastery_plan ON user_kp_mastery(plan_id);

-- ===== RLS =====
-- 启用 RLS 但使用宽松策略（认证在 API 层通过 auth_middleware 处理）
ALTER TABLE cet4_questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE subject_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE plan_daily_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE diagnosis_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE question_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_kp_mastery ENABLE ROW LEVEL SECURITY;

-- 题库：所有人可读
CREATE POLICY "Anyone can read questions" ON cet4_questions
    FOR SELECT USING (true);
CREATE POLICY "Anyone can insert questions" ON cet4_questions
    FOR INSERT WITH CHECK (true);

-- 计划/任务/记录：允许通过 API key 访问（认证在中间件层完成）
CREATE POLICY "API can manage plans" ON subject_plans FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "API can manage tasks" ON plan_daily_tasks FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "API can manage diagnosis" ON diagnosis_results FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "API can manage records" ON question_records FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "API can manage mastery" ON user_kp_mastery FOR ALL USING (true) WITH CHECK (true);
