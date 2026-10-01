-- 「推送视频」：谁、因为什么、被推送到哪条视频（2026-10-01）
--
-- ============ 为什么是一张新表，而不是给 video_library 加列 ============
--
-- video_gen.py 开头写死了一条设计：
--     「视频单元 = 知识点，与题目无关：一个新知识点只生成一次，其下所有题复用」
--     唯一格 = (subject, knowledge_key, angle)
--
-- 也就是说 **视频是全站共享的，一个知识点只有一条**。
-- 那么「推送到自己的视频库」就**不能**理解成「这条视频归我了」——
-- 猜「A 触发生成的所以归 A」在别人复用时必然错乱：
-- 用户 B 需要同一个知识点时，ensure 直接复用 A 那条，B 的推送列表里就什么都不会有。
--
-- 所以：视频池不动，另记一张「谁被推送过什么」的关联表。
--
-- ============ 这张表还解决什么 ============
--
--   · 视频库新增的「推送」分类读它（原来的「我的视频」= 自己点的，两者要分得开）
--   · 出问题能倒查「这条视频是谁的什么操作带出来的」（source + source_ref）
--
-- 幂等，可重复执行。

CREATE TABLE IF NOT EXISTS public.user_video_pushes (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL,
    video_id    UUID NOT NULL,
    -- 触发场景：resource=资源库生成题目 / plan=自定义计划 / practice=做题页
    source      TEXT NOT NULL DEFAULT 'practice',
    -- 触发的题目或任务 id —— 只用于倒查，不做外键（题目可能来自内存题库或 questions 表）
    source_ref  TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    -- 同一个人同一条视频只推一次：重复触发生时直接忽略，不刷屏
    CONSTRAINT user_video_pushes_uniq UNIQUE (user_id, video_id)
);

CREATE INDEX IF NOT EXISTS idx_uvp_user  ON public.user_video_pushes(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_uvp_video ON public.user_video_pushes(video_id);

-- 授权：anon 要能读写（后端统一用 anon key，见 services/supabase.py 的 get_supabase_headers）。
-- ⚠️ 这个项目里 service_role 和 anon 的权限是**错开的**（09-30 那轮踩过：
--    社区那批表 anon 能读、service_role 403，generation_history 也是），
--    所以两个都授，别只授一个。
GRANT SELECT, INSERT, UPDATE, DELETE ON public.user_video_pushes TO anon, authenticated, service_role;

-- RLS 全放行 —— 和视频库其它表一致（写入路径由后端把关，不靠 RLS）
ALTER TABLE public.user_video_pushes ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "uvp_all" ON public.user_video_pushes;
CREATE POLICY "uvp_all" ON public.user_video_pushes
  FOR ALL USING (true) WITH CHECK (true);

-- 自检
SELECT count(*) AS uvp_rows FROM public.user_video_pushes;
