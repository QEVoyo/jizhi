-- ============================================================================
-- 管理后台整改 · 数据层
-- 2026-09-30
--
-- 背景：后台 8 个页面里，反馈 / Q&A / 举报 三个页面永远是空的。
--   根因不是代码，是 admin_tables.sql 建了表却一条 GRANT 都没写 ——
--   而这几张表的 RLS 策略是「全放行」(USING true)，所以 RLS 不是防线，GRANT 才是。
--   实测（service_role 探测线上）：
--     user_feedback / user_qa / content_reports / reports  → 403 42501
--     admin_audit_logs / system_announcements              → 200（有 GRANT）
--
-- 本文件做四件事：
--   1. 补 GRANT —— 让后台读得到数据
--   2. content_reports 补「被举报人 + 内容快照」—— 让举报可处置
--   3. 统一举报表到 content_reports 并迁移 reports 的历史数据
--   4. 新建 user_sanctions + profiles 快路径列 —— 警告 / 禁言 / 封禁
--
-- 幂等：可重复执行。
-- ============================================================================


-- ============================================================================
-- 1. 补 GRANT
--
-- ⚠️ 只授 service_role，不授 anon / authenticated。
--    理由：这几张表的 RLS 是 WITH CHECK (true) USING (true)，GRANT 就是唯一防线；
--    而 anon key 打包在前端产物里（任何人可提取）。
--    授给 anon 等于把用户反馈的邮箱正文和全部管理员审计日志对全网公开。
--
--    用户侧的写入（提交反馈 / 举报 / 提问）本来就经过 FastAPI 后端，
--    后端已做 get_current_user 鉴权，再把写入换成 service_role 即可，
--    不需要也不会给 anon 任何直接访问权。
-- ============================================================================
GRANT SELECT, INSERT, UPDATE, DELETE ON public.user_feedback        TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.user_qa              TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.content_reports      TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.reports              TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.admin_audit_logs     TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.system_announcements TO service_role;

-- ⚠️⚠️ profiles 只有 SELECT 权限 —— 这是**禁言 / 封禁 / 改角色三件事的总阻塞点**。
--     实测（2026-09-30，四权限逐一探测）：profiles 的 INSERT/UPDATE/DELETE 全部 403，
--     而其余 13 张相关表都正常。表现是：
--       · 禁言 → PATCH profiles.muted_until  → 42501
--       · 封禁 → PATCH profiles.is_active    → 42501
--       · 改角色 → PATCH profiles.role       → 42501
--     也就是说，即使处置记录写得进去、UI 显示"已禁言"，**行为限制那一半根本没落库**。
--     （这个坑第一轮探测漏了，因为当时只测了 SELECT。）
GRANT SELECT, INSERT, UPDATE, DELETE ON public.profiles TO service_role;


-- ============================================================================
-- 2. content_reports：补「被举报人」与「内容快照」
--
-- 现状：content_reports 只有 target_id（帖子/评论的 id），
--   没有任何字段指向「被举报人」，也没有被举报内容的留存。
--   后果：管理员审核时既看不到被举报了什么，也无从知道该处罚谁 ——
--   处置闭环在数据层就是断的。
--
-- 注：写入方 routers/community/messages.py 其实**已经抓到了**这两样东西
--   （target_content / target_author），只是只发进了邮件、没落库。
-- ============================================================================
ALTER TABLE public.content_reports ADD COLUMN IF NOT EXISTS target_author_id       UUID;
ALTER TABLE public.content_reports ADD COLUMN IF NOT EXISTS target_author_nickname TEXT;
ALTER TABLE public.content_reports ADD COLUMN IF NOT EXISTS target_snapshot        TEXT;   -- 被举报内容前 200 字
ALTER TABLE public.content_reports ADD COLUMN IF NOT EXISTS action_taken           TEXT;   -- dismiss/warn/delete/mute/ban

CREATE INDEX IF NOT EXISTS idx_content_reports_status  ON public.content_reports (status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_content_reports_author  ON public.content_reports (target_author_id);
CREATE INDEX IF NOT EXISTS idx_content_reports_target  ON public.content_reports (target_type, target_id);


-- ============================================================================
-- 3. 统一举报表：reports → content_reports
--
-- reports（7 列）的字段是 content_reports（11 列）的真子集：
--     reports:         id, reporter_id, target_type, target_id, reason, status, created_at
--     content_reports: 上述全部 + reporter_nickname, admin_id, admin_note, resolved_at
-- 所以迁移不用做任何字段映射，直接把行搬过去。
--
-- 迁移完成后由代码统一切到 content_reports（写入方 messages.py:359）。
-- reports 表保留不删，作为历史留档。
-- ============================================================================
INSERT INTO public.content_reports
    (id, reporter_id, target_type, target_id, reason, status, created_at)
SELECT r.id, r.reporter_id, r.target_type, r.target_id, r.reason,
       COALESCE(NULLIF(r.status, ''), 'pending'), r.created_at
FROM   public.reports r
WHERE  NOT EXISTS (SELECT 1 FROM public.content_reports c WHERE c.id = r.id);


-- ============================================================================
-- 4. 处置能力：user_sanctions（警告 / 禁言 / 封禁）
--
-- 设计取舍：
--   · 历史上没有禁言概念，全仓库零命中；封禁也只有一个 profiles.is_active 布尔。
--   · user_sanctions 存**处置历史**（谁、因为什么、多久、谁操作的、是否已解除），
--     这是审计和「这个用户被处置过几次」的依据。
--   · 热路径（每次请求都要判）不查这张表，改查 profiles 上的两个冗余列
--     （见第 5 节）—— 认证中间件本来就已经在查 profiles 了，零额外开销。
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.user_sanctions (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id          UUID NOT NULL,
    kind             TEXT NOT NULL,        -- warn / mute / ban
    scope            TEXT,                 -- post / comment / all（mute 用；ban 恒为 all）
    reason           TEXT,
    report_id        UUID,                 -- 来源举报，可空（也可手动处罚）
    admin_id         UUID,
    admin_nickname   TEXT,
    starts_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at       TIMESTAMPTZ,          -- NULL = 永久；到期自然失效，不需要定时任务
    lifted_at        TIMESTAMPTZ,          -- 管理员提前解除
    lifted_by        UUID,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sanctions_user   ON public.user_sanctions (user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_sanctions_active ON public.user_sanctions (user_id)
    WHERE lifted_at IS NULL;

ALTER TABLE public.user_sanctions ENABLE ROW LEVEL SECURITY;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.user_sanctions TO service_role;


-- ============================================================================
-- 5. profiles：处置状态的快路径列
--
--   is_active    已存在 —— 封禁（布尔，账号级）
--   muted_until  新增   —— 禁言到期时间；NULL 或已过期 = 未禁言
--   mute_scope   新增   —— 禁言范围 post / comment / all
--
-- 判定式（后端代码用）：
--   封禁：is_active IS NOT TRUE                        → 拒绝一切操作
--   禁言：muted_until > NOW() AND mute_scope 命中当前动作 → 拒绝该动作
-- ============================================================================
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS muted_until TIMESTAMPTZ;
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS mute_scope  TEXT;

CREATE INDEX IF NOT EXISTS idx_profiles_muted ON public.profiles (muted_until)
    WHERE muted_until IS NOT NULL;


-- ============================================================================
-- 6. 修 video_reports 的外键：CASCADE → SET NULL
--
-- 问题：video_reports.video_id 是 ON DELETE CASCADE（见 fix_video_social.sql:45）。
--   后台「处理举报 → 下架视频」会先删 video_library 那一行，
--   于是**这条举报记录自己被级联删掉了**，紧接着的状态回写命中 0 行，
--   而代码不回读返回值 → 管理员看到"已处理"，实际举报记录已经没了，
--   用 ?status=removed 也永远查不到。
--
-- 为什么选 SET NULL 而不是软删视频：
--   video_library 没有 is_deleted 列（不像 posts/comments 那样天生支持软删），
--   加一列要动的地方更多。SET NULL 保留举报记录这一诉求，代价最小。
--   （将来若要视频保留可追溯，再给 video_library 加 is_deleted 列即可。）
--
-- video_reports.video_id 本身可空，所以 SET NULL 合法。
-- ============================================================================
DO $$
DECLARE cname text;
BEGIN
    SELECT conname INTO cname
    FROM   pg_constraint
    WHERE  conrelid  = 'public.video_reports'::regclass
      AND  confrelid = 'public.video_library'::regclass
      AND  contype   = 'f';
    IF cname IS NOT NULL THEN
        EXECUTE format('ALTER TABLE public.video_reports DROP CONSTRAINT %I', cname);
        RAISE NOTICE '已删除旧外键约束 %', cname;
    END IF;
END $$;

ALTER TABLE public.video_reports
    ADD CONSTRAINT video_reports_video_id_fkey
    FOREIGN KEY (video_id) REFERENCES public.video_library(id) ON DELETE SET NULL;


-- ============================================================================
-- 7. 社区表的反向缺口：service_role 没授权
--
-- 第 1 节修的是「管理员表只有 RLS 全放行、缺 GRANT，谁都读不了」。
-- 这一节是**镜像问题**：社区这批表当年授权给了 anon，却**从没给 service_role**。
-- 实测（2026-09-30，service_role 探测线上）：
--     posts / comments / post_likes / post_collects / friendships /
--     private_messages / messages / notifications / user_actions / user_stats
--     → 全部 403，而其中多数对 anon 反而是 200。
--
-- 后果举例：`GET /admin/users/{id}` 的用户详情是用 service_role 查 posts 数的 ——
--   即便把列名从 author_id 改成 user_id，查询本身仍会被 403 挡掉，
--   post_count 依旧是 0。整条"后台看不到社区数据"的链路都卡在这。
--
-- 为什么现在必须补：后端正在往 service_role 迁移（2026-09-27 的安全整改方向：
--   写操作换 service_role + 查状态码 + 回读校验），但这批老表的授权没跟上。
-- 安全性：service_role key 只存在于服务端（.env），不打包进前端产物，
--   授权给它是安全且必要的；本次也**不**扩大 anon 的权限。
-- ============================================================================
GRANT SELECT, INSERT, UPDATE, DELETE ON public.posts            TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.comments         TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.post_likes       TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.post_collects    TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.friendships      TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.private_messages TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.messages         TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.notifications    TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.user_actions     TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.user_stats       TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.user_achievements TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.user_task_claims  TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.user_tasks        TO service_role;


-- ============================================================================
-- 8. 自检 —— 执行完请跑这一段
-- ============================================================================

-- 6.1 GRANT 是否补齐（应为 7 行，每行 4 个权限；profiles 那行最关键）
SELECT table_name, string_agg(privilege_type, ',' ORDER BY privilege_type) AS privs,
       count(*) AS 权限数
FROM   information_schema.role_table_grants
WHERE  grantee = 'service_role'
  AND  table_name IN ('user_feedback','user_qa','content_reports','reports',
                      'admin_audit_logs','system_announcements','user_sanctions','profiles')
GROUP  BY table_name
ORDER  BY table_name;

-- 6.2 content_reports 新列是否就位（应为 4 行）
SELECT column_name, data_type
FROM   information_schema.columns
WHERE  table_name = 'content_reports'
  AND  column_name IN ('target_author_id','target_author_nickname','target_snapshot','action_taken')
ORDER  BY column_name;

-- 6.3 迁移结果：两边条数应相等（reports 为 0 时 content_reports 不应减少）
SELECT (SELECT count(*) FROM public.reports)         AS reports_rows,
       (SELECT count(*) FROM public.content_reports) AS content_reports_rows;

-- 6.4 user_sanctions 是否建好（应为 1 行）
SELECT count(*) AS sanctions_table_exists
FROM   information_schema.tables
WHERE  table_schema = 'public' AND table_name = 'user_sanctions';

-- 6.5 video_reports 外键应为 SET NULL（confdeltype = 'n'）
SELECT conname, confdeltype,
       CASE confdeltype WHEN 'c' THEN 'CASCADE（仍是旧的，未生效）'
                        WHEN 'n' THEN 'SET NULL ✓'
                        ELSE confdeltype::text END AS 删除行为
FROM   pg_constraint
WHERE  conrelid = 'public.video_reports'::regclass AND contype = 'f';

-- 6.6 profiles 的处置快路径列（应为 2 行）
SELECT column_name, data_type
FROM   information_schema.columns
WHERE  table_name = 'profiles' AND column_name IN ('muted_until', 'mute_scope')
ORDER  BY column_name;

-- 6.7 社区表的 service_role 授权（应为 13 行，每行 4 个权限）
SELECT table_name, string_agg(privilege_type, ',' ORDER BY privilege_type) AS privs
FROM   information_schema.role_table_grants
WHERE  grantee = 'service_role'
  AND  table_name IN ('posts','comments','post_likes','post_collects','friendships',
                      'private_messages','messages','notifications','user_actions',
                      'user_stats','user_achievements','user_task_claims','user_tasks')
GROUP  BY table_name
ORDER  BY table_name;
