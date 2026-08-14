-- =============================================
-- 授予学科计划各表的读写权限
-- 在 Supabase SQL Editor 中执行
-- =============================================

-- service_role (API key 后端使用)
GRANT ALL ON public.subject_plans TO service_role;
GRANT ALL ON public.plan_daily_tasks TO service_role;
GRANT ALL ON public.diagnosis_results TO service_role;
GRANT ALL ON public.question_records TO service_role;
GRANT ALL ON public.user_kp_mastery TO service_role;
GRANT ALL ON public.cet4_questions TO service_role;

-- anon / authenticated (前端可直接调用的最低权限)
GRANT SELECT, INSERT, UPDATE, DELETE ON public.subject_plans TO anon, authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.plan_daily_tasks TO anon, authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.diagnosis_results TO anon, authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.question_records TO anon, authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.user_kp_mastery TO anon, authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.cet4_questions TO anon, authenticated;
