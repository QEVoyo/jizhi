-- ============================================================================
-- 消息中心改造 · 数据层
-- 2026-10-07
--
-- 背景（实测线上的现状）：
--   · notifications 全表只有 5 行（system 3 / chat 2，最近 08-24），前端却挂着 10 个 Tab
--   · 聚合 upsert 每次 PATCH 都写 updated_at 列 —— 而这张表根本没有这一列：
--         PATCH → 400 {"code":"42703","message":"column notifications.updated_at does not exist"}
--     调用方不检查返回值（messages.py:180）→ 静默失败两个月
--     铁证：接收者 540b599b… 的 chat 通知冻结在 08-24、msg_count=1，
--           而同一发送者后来还发过 3 条（最后 10-02）
--   · 未读口径有三套算法（unread/summary、sidebar-badges、前端公告 fetch），数字必然对不上
--
-- 本文件做七件事：
--   1. notifications 补列（分组 / 触发者 / 首次-最近时间 / 待办 / 软删 / 三合一 payload）
--   2. 回填线上 5 行旧数据的 group_key 与 last_at
--   3. 未读聚合的部分唯一索引（同 (user,type,source) 只留一行未读）
--   4. 查询索引
--   5. notification_settings 补列（career/todo/admin 开关 + 免打扰时段）
--   6. 补 service_role 的 GRANT（这张表此前 service_role 是 403 —— 见 admin_rework 的同款问题）
--   7. ⚠️ 收回 anon 权限（**必须与新后端同一批上线**，见文末）
--
-- 幂等：可重复执行。末尾带自检。
-- ============================================================================


-- ============================================================================
-- 1. notifications 补列
--
-- ⚠️ 列名用 group_key 不用 group —— group 是 SQL 保留字，裸写要处处加引号。
-- ============================================================================

ALTER TABLE notifications ADD COLUMN IF NOT EXISTS group_key   text;
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS actor_id    uuid;
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS last_at     timestamptz;
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS read_at     timestamptz;
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS is_todo     boolean NOT NULL DEFAULT false;
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS handled_at  timestamptz;
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS deleted_at  timestamptz;
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS payload     jsonb;

COMMENT ON COLUMN notifications.group_key  IS '大类：chat/social/learning/plan/evaluation/career/system/todo/admin';
COMMENT ON COLUMN notifications.actor_id   IS '触发者（点赞的人、发消息的好友）；系统消息为 NULL';
COMMENT ON COLUMN notifications.last_at    IS '最近一条的时间（聚合时更新）。取代此前误用的 updated_at —— 那一列不存在';
COMMENT ON COLUMN notifications.is_todo    IS '待办型：已读必须由「处理动作」驱动，看见不算';
COMMENT ON COLUMN notifications.payload    IS '结构化内容，目前用于每日学习推荐的三合一（内容/题目/视频）';


-- ============================================================================
-- 2. 回填旧数据（线上 5 行）
-- ============================================================================

UPDATE notifications SET group_key = CASE
    WHEN type = 'chat'                                  THEN 'chat'
    WHEN type = 'social'                                THEN 'social'
    WHEN type IN ('learning','daily_rec',
                  'daily_summary','task_done','task_failed') THEN 'learning'
    WHEN type = 'plan_reminder'                         THEN 'plan'
    WHEN type = 'evaluation'                            THEN 'evaluation'
    ELSE 'system'
END
WHERE group_key IS NULL;

UPDATE notifications SET last_at = created_at WHERE last_at IS NULL;


-- ============================================================================
-- 3. 未读聚合的部分唯一索引
--
-- 语义：同一个 (user, type, source_id) 在「未读且未删除」状态下只允许一行。
-- 新入口 notify() 的做法是「先 INSERT，撞索引(409) 再改走 UPDATE」——
-- 不用 ON CONFLICT：部分索引的谓词没法在 ON CONFLICT 里表达，
-- PostgreSQL 会报 "no unique or exclusion constraint matching the ON CONFLICT specification"。
--
-- ⚠️ 执行前先看一眼有没有重复行（下面的自检 6.2 会报）；有就把旧的删掉再建索引。
-- ============================================================================

CREATE UNIQUE INDEX IF NOT EXISTS uq_notifications_unread_agg
    ON notifications (user_id, type, source_id)
    WHERE is_read = false AND deleted_at IS NULL AND source_id IS NOT NULL;


-- ============================================================================
-- 4. 查询索引
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_notifications_user_unread
    ON notifications (user_id, is_read)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_notifications_user_last
    ON notifications (user_id, last_at DESC NULLS LAST)
    WHERE deleted_at IS NULL;


-- ============================================================================
-- 5. notification_settings 补列
--
-- 现有 8 个开关（chat/social/learning/plan_reminder/evaluation/daily_rec/
-- daily_summary/system）+ 2 个时间，缺三类开关与免打扰时段。
-- ============================================================================

ALTER TABLE notification_settings ADD COLUMN IF NOT EXISTS career_enabled boolean DEFAULT true;
ALTER TABLE notification_settings ADD COLUMN IF NOT EXISTS todo_enabled   boolean DEFAULT true;
ALTER TABLE notification_settings ADD COLUMN IF NOT EXISTS admin_enabled  boolean DEFAULT true;
ALTER TABLE notification_settings ADD COLUMN IF NOT EXISTS dnd_start      text;   -- 'HH:MM'
ALTER TABLE notification_settings ADD COLUMN IF NOT EXISTS dnd_end        text;   -- 'HH:MM'

-- 5.1 每日学习推荐的**依据**（2026-10-07 追加，重跑本文件即可）
--     profile = 按个人信息（学习阶段/年级/专业/目标/难度偏好）
--     history = 按以往做题记录（错题、薄弱知识点、掌握度）
--     mix     = 两者结合（默认）：有做题记录就优先它，没有就退回资料
--
-- ⚠️ 两条回落规则是必须的，否则新用户选了 history 会**永远收不到推荐**：
--     选 history 但一条记录都没有 → 退回 profile
--     选 profile 但资料没填全     → 退回 history
ALTER TABLE notification_settings ADD COLUMN IF NOT EXISTS daily_rec_source text DEFAULT 'mix';

COMMENT ON COLUMN notification_settings.daily_rec_source IS
    '每日推荐的依据：profile / history / mix（默认）。为空按 mix 处理';


-- ============================================================================
-- 6. 补 GRANT（本文件里的改动都不授 anon）
--
-- admin_rework_20260930.sql 记过同一类病：表建了却没有 GRANT，
-- 表现是 403 42501，再被「非 200 降级成空」的代码伪装成「暂无数据」。
-- ============================================================================

GRANT SELECT, INSERT, UPDATE, DELETE ON notifications         TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON notification_settings TO service_role;


-- ============================================================================
-- 7. ⚠️ 收回 anon 权限 —— **必须与新后端同一批上线**
--
-- 为什么必须收：这几张表的 RLS 是放行的，GRANT 才是防线，
--   而 anon key 打包在前端产物里（谁都能扒）。
--   留着 anon = 任何人拿公开的 anon key 就能查别人的私信通知和处置记录。
--
-- 为什么不能现在收：**后端此刻正是用 anon 访问 notifications 的**
--   （utils/notification.py / community/messages.py 走 get_supabase_headers()）。
--   先收权限、后部署后端 = 消息中心当场 403。
--
-- 顺序：① 部署切换 service_role 的新后端 → ② 再取消下面两行的注释执行。
-- 已确认安全：Web 前端只用 Supabase 做 Storage 上传（api/upload.js），
--             小程序 src/ 里 supabase 出现 0 次 —— 没有任何客户端直连这张表。
-- ============================================================================

-- REVOKE ALL ON notifications         FROM anon;
-- REVOKE ALL ON notification_settings FROM anon;


-- ============================================================================
-- 自检
-- ============================================================================

-- 6.1 新列（应 8 行）
SELECT column_name, data_type
FROM   information_schema.columns
WHERE  table_schema = 'public' AND table_name = 'notifications'
  AND  column_name IN ('group_key','actor_id','last_at','read_at',
                       'is_todo','handled_at','deleted_at','payload')
ORDER  BY column_name;

-- 6.2 有没有重复的未读聚合行（有的话唯一索引建不上）
SELECT user_id, type, source_id, count(*) AS 重复数
FROM   notifications
WHERE  is_read = false AND deleted_at IS NULL AND source_id IS NOT NULL
GROUP  BY user_id, type, source_id
HAVING count(*) > 1;

-- 6.3 旧数据回填结果
SELECT group_key, type, count(*) AS 行数, min(last_at) AS 最早, max(last_at) AS 最近
FROM   notifications
GROUP  BY group_key, type
ORDER  BY group_key, type;

-- 6.4 索引是否就位（应 3 行）
SELECT indexname FROM pg_indexes
WHERE  tablename = 'notifications'
  AND  indexname IN ('uq_notifications_unread_agg',
                     'idx_notifications_user_unread',
                     'idx_notifications_user_last')
ORDER  BY indexname;

-- 6.5 notification_settings 新列（应 5 行）
SELECT column_name FROM information_schema.columns
WHERE  table_schema = 'public' AND table_name = 'notification_settings'
  AND  column_name IN ('career_enabled','todo_enabled','admin_enabled','dnd_start','dnd_end')
ORDER  BY column_name;

-- 6.6 ⚠️ 权限现状：anon 还在不在？
--     第 7 步执行前 anon 会有 4 行（这是已知的洞）；
--     执行后应为 0 行，service_role 应为 4 行。
SELECT grantee, string_agg(privilege_type, ',' ORDER BY privilege_type) AS privs
FROM   information_schema.role_table_grants
WHERE  table_name IN ('notifications','notification_settings')
  AND  grantee IN ('anon','service_role','authenticated')
GROUP  BY grantee, table_name
ORDER  BY table_name, grantee;
