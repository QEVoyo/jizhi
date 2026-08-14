-- 计划表列迁移 — 在 Supabase SQL Editor 执行
-- 修复: subject_plans 缺 syllabus_id；plan_daily_tasks 缺任务查询字段

-- 1. subject_plans 添加 syllabus_id（考纲ID，多考纲支持）
ALTER TABLE subject_plans ADD COLUMN IF NOT EXISTS syllabus_id TEXT;
-- 回填：旧数据的 subject 字段值作为 syllabus_id
UPDATE subject_plans SET syllabus_id = subject WHERE syllabus_id IS NULL;

-- 2. subject_plans 添加其他新字段
ALTER TABLE subject_plans ADD COLUMN IF NOT EXISTS start_date TIMESTAMPTZ;
ALTER TABLE subject_plans ADD COLUMN IF NOT EXISTS end_date DATE;
ALTER TABLE subject_plans ADD COLUMN IF NOT EXISTS source TEXT DEFAULT 'diagnosis';  -- diagnosis / exam_paper
ALTER TABLE subject_plans ADD COLUMN IF NOT EXISTS source_paper_id TEXT;              -- 真题卷ID（答卷生成时）
ALTER TABLE subject_plans ADD COLUMN IF NOT EXISTS accuracy_at_create NUMERIC(5,1);   -- 生成时的正确率

-- 3. plan_daily_tasks 添加任务查询字段（对接题库查询）
ALTER TABLE plan_daily_tasks ADD COLUMN IF NOT EXISTS title TEXT;
ALTER TABLE plan_daily_tasks ADD COLUMN IF NOT EXISTS category TEXT;
ALTER TABLE plan_daily_tasks ADD COLUMN IF NOT EXISTS question_type TEXT DEFAULT 'choice';
ALTER TABLE plan_daily_tasks ADD COLUMN IF NOT EXISTS question_count INTEGER DEFAULT 5;
ALTER TABLE plan_daily_tasks ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'pending';
ALTER TABLE plan_daily_tasks ADD COLUMN IF NOT EXISTS estimated_minutes INTEGER DEFAULT 15;

-- 4. plan_daily_tasks 的 date 列改可空（新代码用 day_number 定位）
ALTER TABLE plan_daily_tasks ALTER COLUMN date DROP NOT NULL;

-- 5. 新表：真题答卷记录（如果还没建）
CREATE TABLE IF NOT EXISTS exam_paper_records (
  id          TEXT PRIMARY KEY,
  user_id     TEXT NOT NULL,
  paper_id    TEXT NOT NULL,
  total_score NUMERIC(6,1) NOT NULL,
  max_score   NUMERIC(6,1) NOT NULL,
  score_pct   NUMERIC(5,1) NOT NULL,
  section_scores    JSONB DEFAULT '[]',
  question_results  JSONB DEFAULT '[]',
  elapsed_seconds   INTEGER DEFAULT 0,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_epr_user  ON exam_paper_records(user_id);
CREATE INDEX IF NOT EXISTS idx_epr_paper ON exam_paper_records(paper_id);
ALTER TABLE exam_paper_records ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "service_all" ON exam_paper_records;
CREATE POLICY "service_all" ON exam_paper_records FOR ALL USING (true);
