-- 自定义计划（learning_plans / learning_tasks）改造 · 数据层（2026-10-01）
--
-- 配套设计：
--   · 题目不再以「正文」形式塞在 learning_tasks 里，改成引用 questions 表的 id
--     （两池模型：题库真题 → 学科计划；AI 生成题 → 资源库 + 自定义计划）
--   · 做过的题记「做对过没有 / 最近一次 / 做了几次」，用于算**当日最佳正确率**
--     （最佳率：重做做错不回退，只从 false 变 true）
--   · 学习内容改成**按需生成 + 缓存**（照学科计划 generate-learning 的先例），
--     列表只显示摘要前两行，点进去才生成详细正文 —— 否则一次生成 N 天正文会
--     撑爆响应（前端 90 秒超时）
--
-- 全部是 ADD COLUMN IF NOT EXISTS，纯增量，不动现有列、不动现有数据。可重复执行。

ALTER TABLE public.learning_tasks ADD COLUMN IF NOT EXISTS question_id      UUID;
ALTER TABLE public.learning_tasks ADD COLUMN IF NOT EXISTS best_correct     BOOLEAN DEFAULT FALSE;
ALTER TABLE public.learning_tasks ADD COLUMN IF NOT EXISTS last_correct     BOOLEAN;
ALTER TABLE public.learning_tasks ADD COLUMN IF NOT EXISTS user_answer      TEXT;
ALTER TABLE public.learning_tasks ADD COLUMN IF NOT EXISTS attempts         INTEGER DEFAULT 0;
ALTER TABLE public.learning_tasks ADD COLUMN IF NOT EXISTS estimated_minutes INTEGER;
-- 按需生成的详细教学正文（JSON：{summary, sections[], key_points[], common_mistakes[]}）
ALTER TABLE public.learning_tasks ADD COLUMN IF NOT EXISTS lesson_content   JSONB;

-- 计划侧：难度真正参与生成后，把它和「每日时长」一起留着做校验依据
ALTER TABLE public.learning_plans ADD COLUMN IF NOT EXISTS difficulty       INTEGER DEFAULT 5;
ALTER TABLE public.learning_plans ADD COLUMN IF NOT EXISTS total_days       INTEGER;
ALTER TABLE public.learning_plans ADD COLUMN IF NOT EXISTS daily_minutes    INTEGER;
ALTER TABLE public.learning_plans ADD COLUMN IF NOT EXISTS accuracy         INTEGER DEFAULT 0;

-- 自检
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public' AND table_name = 'learning_tasks'
ORDER BY ordinal_position;
