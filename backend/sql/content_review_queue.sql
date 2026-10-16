-- ============================================================================
-- 内容待审队列 · 数据层
-- 2026-10-15
--
-- 给什么用的：信誉值「内容先审后发」这个后果需要一套落地的机制。
--   低信誉用户发的帖子/评论不再直接公开，而是
--     status='pending'  →  仅自己可见 + 进后台待审队列  →  通过 / 驳回
--
-- 为什么复用 posts / comments 加一列，而不是建一张待审表：
--   待审的内容**就是内容本身**，它只是还没公开。搬去另一张表意味着
--   通过时要搬回来、驳回时要留个副本、评论的父子关系还要重建 ——
--   而 `status` 一列把这些全部消掉，查询侧只是多一个 where。
--   （视频那条链路早就是 private→pending→public 的状态机，这里是同一套思路。）
--
-- 顺带修一个既有 bug：动态流的查询**从来没有过滤 is_deleted** ——
--   被举报删掉的帖子仍然在社区里显示。本文件不动代码，但下面的索引
--   和注释里标了这件事，代码侧在同一批里改（routers/community/posts.py）。
--
-- 幂等：可重复执行。
-- ============================================================================


-- ============================================================================
-- 1. posts / comments 加 status
--
-- ⚠️ 用 `NOT NULL DEFAULT 'published'` 一次写完，而不是「先加可空列 → UPDATE
--    回填 → 再 SET NOT NULL」三步。PostgreSQL 11 起，带默认值的 ADD COLUMN
--    不会重写整张表（fast default），所以这一句对线上大表也是安全的。
--
-- 存量数据自动成为 'published' —— 这是对的：本功能上线**之前**发的内容
-- 都是直接公开的，不该被追溯塞进待审队列。
-- ============================================================================
ALTER TABLE public.posts
    ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'published';
ALTER TABLE public.comments
    ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'published';


-- ============================================================================
-- 2. 审核元信息
--
-- 为什么要有 reviewed_by / review_note：
--   「这条为什么被驳回」是作者申诉时唯一能拿出来的东西。
--   只存一个 rejected 而不说原因，等于让管理员和作者都失忆。
-- ============================================================================
ALTER TABLE public.posts    ADD COLUMN IF NOT EXISTS reviewed_by UUID;
ALTER TABLE public.posts    ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMPTZ;
ALTER TABLE public.posts    ADD COLUMN IF NOT EXISTS review_note TEXT;
ALTER TABLE public.comments ADD COLUMN IF NOT EXISTS reviewed_by UUID;
ALTER TABLE public.comments ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMPTZ;
ALTER TABLE public.comments ADD COLUMN IF NOT EXISTS review_note TEXT;


-- ============================================================================
-- 3. 取值约束
--
-- 用 DO 块包起来是因为 ALTER TABLE ADD CONSTRAINT 没有 IF NOT EXISTS，
-- 直接写的话第二次执行会报 42710（约束已存在），整份脚本就断在那里。
-- ============================================================================
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'posts_status_check') THEN
        ALTER TABLE public.posts ADD CONSTRAINT posts_status_check
            CHECK (status IN ('published', 'pending', 'rejected'));
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'comments_status_check') THEN
        ALTER TABLE public.comments ADD CONSTRAINT comments_status_check
            CHECK (status IN ('published', 'pending', 'rejected'));
    END IF;
END $$;


-- ============================================================================
-- 4. 索引
--
-- ⚠️ 部分索引（WHERE status='pending'）而不是全表 status 索引：
--   待审的永远是极少数，而全表索引会跟着每一次发帖长大。
--   后台那个「待审队列」查询只关心 pending，正好走这个部分索引。
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_posts_pending
    ON public.posts (created_at DESC) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_comments_pending
    ON public.comments (created_at DESC) WHERE status = 'pending';

-- 动态流的常规查询：公开 + 未删除 + 按时间倒序。
-- 带上 is_deleted 是因为这个组合索引正好也是那个既有 bug 的修复所依赖的路径。
CREATE INDEX IF NOT EXISTS idx_posts_feed
    ON public.posts (created_at DESC) WHERE status = 'published' AND is_deleted = false;

-- 作者要看自己那些还没公开的内容，走这条
CREATE INDEX IF NOT EXISTS idx_posts_author_status
    ON public.posts (user_id, status, created_at DESC);


-- ============================================================================
-- 5. 自检 —— 执行完请跑这一段
-- ============================================================================

-- 5.1 新列是否就位（应 8 行：posts/comments 各 4 列）
SELECT table_name, column_name, data_type, is_nullable, column_default
FROM   information_schema.columns
WHERE  table_schema = 'public'
  AND  table_name IN ('posts', 'comments')
  AND  column_name IN ('status', 'reviewed_by', 'reviewed_at', 'review_note')
ORDER  BY table_name, column_name;

-- 5.2 约束是否挂上（应 2 行）
SELECT conname, pg_get_constraintdef(oid) AS 定义
FROM   pg_constraint
WHERE  conname IN ('posts_status_check', 'comments_status_check');

-- 5.3 存量数据都该是 published（应 0 行 pending —— 除非你跑过一次带待审的流程）
SELECT 'posts' AS 表, status, count(*) FROM public.posts GROUP BY status
UNION ALL
SELECT 'comments', status, count(*) FROM public.comments GROUP BY status
ORDER BY 1, 2;

-- 5.4 索引（应 4 行）
SELECT indexname FROM pg_indexes
WHERE schemaname = 'public' AND tablename IN ('posts', 'comments')
  AND indexname IN ('idx_posts_pending','idx_comments_pending',
                    'idx_posts_feed','idx_posts_author_status')
ORDER BY indexname;
