-- 真题套卷记录表（exam_paper_records）权限补授
-- 背景（2026-08-30 排查）：该表建表时只有 RLS 策略、没有任何 GRANT，
--   导致 anon/service_role 都 401（42501）——交卷落库静默失败、
--   真题列表「完成状态/历史成绩」、解析模式做题记录、学情报告真题卷板块全部拿不到数据。
-- 在 Supabase SQL Editor 执行一次即可（幂等）。

GRANT SELECT, INSERT, UPDATE, DELETE ON public.exam_paper_records TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.exam_paper_records TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.exam_paper_records TO service_role;