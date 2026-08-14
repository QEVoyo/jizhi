-- 真题套卷答题记录表
-- 在 Supabase SQL Editor 中执行

CREATE TABLE IF NOT EXISTS exam_paper_records (
  id          TEXT PRIMARY KEY,
  user_id     TEXT NOT NULL,
  paper_id    TEXT NOT NULL,           -- 对应 JSON 文件的 paper_id
  total_score NUMERIC(6,1) NOT NULL,   -- 用户得分
  max_score   NUMERIC(6,1) NOT NULL,   -- 可练部分满分
  score_pct   NUMERIC(5,1) NOT NULL,   -- 百分制得分
  section_scores    JSONB DEFAULT '[]',    -- [{order, name, score, max_score}]
  question_results  JSONB DEFAULT '[]',    -- 逐题结果
  elapsed_seconds   INTEGER DEFAULT 0,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_epr_user    ON exam_paper_records(user_id);
CREATE INDEX IF NOT EXISTS idx_epr_paper   ON exam_paper_records(paper_id);
CREATE INDEX IF NOT EXISTS idx_epr_created ON exam_paper_records(created_at DESC);

-- RLS 策略
ALTER TABLE exam_paper_records ENABLE ROW LEVEL SECURITY;

-- 允许 service_role 全操作（后端使用）
DROP POLICY IF EXISTS "service_all" ON exam_paper_records;
CREATE POLICY "service_all" ON exam_paper_records
  FOR ALL USING (true);

-- 允许用户读自己的记录
DROP POLICY IF EXISTS "user_read_own" ON exam_paper_records;
CREATE POLICY "user_read_own" ON exam_paper_records
  FOR SELECT USING (auth.uid() = user_id);

-- 允许用户插入自己的记录
DROP POLICY IF EXISTS "user_insert_own" ON exam_paper_records;
CREATE POLICY "user_insert_own" ON exam_paper_records
  FOR INSERT WITH CHECK (auth.uid() = user_id);
