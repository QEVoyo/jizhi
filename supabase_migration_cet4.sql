-- ============================================================
-- CET-4 学科计划模块 — 数据库迁移
-- ============================================================

-- 1. 学科计划主表
CREATE TABLE IF NOT EXISTS subject_plans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  subject TEXT NOT NULL DEFAULT 'cet4',           -- 科目：cet4/cet6/考研等
  name TEXT NOT NULL DEFAULT 'CET-4 备考计划',
  goal_score INT NOT NULL DEFAULT 425,            -- 目标分数：425/500/550+
  period_days INT NOT NULL DEFAULT 30,            -- 备考周期：30/60/90
  daily_minutes INT NOT NULL DEFAULT 60,          -- 每日学习时间（分钟）
  daily_question_count INT NOT NULL DEFAULT 0,    -- 每日题量（由系统计算）
  total_days INT NOT NULL DEFAULT 0,
  completed_days INT NOT NULL DEFAULT 0,
  total_questions INT NOT NULL DEFAULT 0,
  completed_questions INT NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'active',          -- active/paused/completed
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- 2. 诊断测试结果
CREATE TABLE IF NOT EXISTS diagnosis_results (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  plan_id UUID NOT NULL REFERENCES subject_plans(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  dimension_scores JSONB NOT NULL DEFAULT '{}',     -- {"vocabulary":65,"grammar":40,"reading":55,"translation":30,"writing":20}
  weak_points JSONB NOT NULL DEFAULT '[]',          -- ["虚拟语气","高频词辨析"]
  strong_points JSONB NOT NULL DEFAULT '[]',
  question_records JSONB NOT NULL DEFAULT '[]',     -- 诊断题目作答记录
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 3. CET-4 题库
CREATE TABLE IF NOT EXISTS cet4_questions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  category TEXT NOT NULL,                           -- vocabulary/grammar/reading/translation/writing
  sub_category TEXT NOT NULL,                       -- 高频词/近义词辨析/时态语态/虚拟语气等
  kp_id TEXT,                                       -- 知识点唯一标识
  kp_name TEXT NOT NULL,                            -- 知识点名称
  question_type TEXT NOT NULL,                      -- choice/fill/cloze/translation
  difficulty INT NOT NULL DEFAULT 1,                -- 1-4★
  content JSONB NOT NULL,                           -- {"stem":"...","options":["A..","B..","C..","D.."]} 或 {"stem":"...","blank_context":"..."}
  answer JSONB NOT NULL,                            -- 正确答案（适配多种题型）
  explanation TEXT NOT NULL,                        -- 解析
  distractor_analysis JSONB,                        -- {"A":"为什么错","B":"为什么错"}
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 4. 每日任务分配
CREATE TABLE IF NOT EXISTS plan_daily_tasks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  plan_id UUID NOT NULL REFERENCES subject_plans(id) ON DELETE CASCADE,
  day_number INT NOT NULL,                          -- 第几天 (1-90)
  date DATE,                                        -- 对应日期
  question_ids UUID[] NOT NULL DEFAULT '{}',        -- 当天分配的题目ID列表
  completed_ids UUID[] NOT NULL DEFAULT '{}',       -- 已完成的题目ID
  completed BOOLEAN NOT NULL DEFAULT false,
  score DECIMAL DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(plan_id, day_number)
);

-- 5. 做题记录
CREATE TABLE IF NOT EXISTS question_records (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  plan_id UUID NOT NULL REFERENCES subject_plans(id) ON DELETE CASCADE,
  question_id UUID NOT NULL REFERENCES cet4_questions(id) ON DELETE CASCADE,
  task_id UUID REFERENCES plan_daily_tasks(id) ON DELETE SET NULL,
  source TEXT NOT NULL DEFAULT 'daily',             -- daily/free/diagnosis
  user_answer JSONB,                                 -- 用户答案
  is_correct BOOLEAN,
  score DECIMAL DEFAULT 0,                          -- 精确评分 0-100
  ai_feedback JSONB,                                -- AI批改反馈
  time_spent INT DEFAULT 0,                         -- 用时（秒）
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_question_records_user ON question_records(user_id);
CREATE INDEX IF NOT EXISTS idx_question_records_plan ON question_records(plan_id);
CREATE INDEX IF NOT EXISTS idx_question_records_question ON question_records(question_id);

-- 6. 知识点掌握度
CREATE TABLE IF NOT EXISTS user_kp_mastery (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  plan_id UUID NOT NULL REFERENCES subject_plans(id) ON DELETE CASCADE,
  kp_id TEXT NOT NULL,
  kp_name TEXT NOT NULL,
  category TEXT NOT NULL,
  sub_category TEXT NOT NULL,
  mastery_score DECIMAL NOT NULL DEFAULT 0,         -- 0-100
  correct_count INT NOT NULL DEFAULT 0,
  total_count INT NOT NULL DEFAULT 0,
  last_practiced_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(user_id, plan_id, kp_id)
);
CREATE INDEX IF NOT EXISTS idx_kp_mastery_user ON user_kp_mastery(user_id, plan_id);

-- ============================================================
-- RLS 策略
-- ============================================================
ALTER TABLE subject_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE diagnosis_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE plan_daily_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE question_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_kp_mastery ENABLE ROW LEVEL SECURITY;

-- cet4_questions：公开可读，服务端可写
ALTER TABLE cet4_questions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "题库公开可读" ON cet4_questions FOR SELECT USING (true);
CREATE POLICY "服务端可写入" ON cet4_questions FOR INSERT WITH CHECK (true);
CREATE POLICY "服务端可更新" ON cet4_questions FOR UPDATE USING (true);
CREATE POLICY "服务端可删除" ON cet4_questions FOR DELETE USING (true);

-- 用户只能操作自己的计划数据
CREATE POLICY "用户管理自己的计划" ON subject_plans FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "用户管理自己的诊断" ON diagnosis_results FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "用户管理自己的任务" ON plan_daily_tasks FOR ALL
  USING (EXISTS (SELECT 1 FROM subject_plans WHERE id = plan_daily_tasks.plan_id AND user_id = auth.uid()));
CREATE POLICY "用户管理自己的记录" ON question_records FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "用户管理自己的掌握度" ON user_kp_mastery FOR ALL USING (auth.uid() = user_id);
