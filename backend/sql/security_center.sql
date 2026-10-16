-- ============================================================================
-- 安全中心 · 数据层
-- 2026-10-15
--
-- 背景：需要一套「入口记录被攻击 + 用户信誉值」的落地载体。
--   盘点线上现状时发现三件事：
--     1. 没有任何攻击/风控事件记录 —— 限流命中了、越权尝试了、账号被封了还来敲门，
--        全都只有一行 stdout 日志，重启即失。后台看不到、也追溯不了。
--     2. 没有任何信誉值概念 —— 只有 admin 手动点的禁言/封禁，没有可增可减、能分级的风控分。
--     3. 两张表对 anon 完全敞开（见第 2 节）。
--
-- 本文件做四件事：
--   1. 建 security_events —— 攻击/风控事件流水
--   2. 立刻收掉两个已经没人用 anon 访问的口子
--   3. 把「还收不了」的口子列清楚并给出探测语句（不盲收，盲收会把后端打死）
--   4. 自检
--
-- 幂等：可重复执行。
-- ============================================================================


-- ============================================================================
-- 1. security_events —— 安全事件流水
--
-- 谁写：
--   · 中间件自动写 —— 限流命中(429)、鉴权失败(401)、越权(403)、参数异常(422)
--   · 业务主动写 —— 违禁词命中、冒充他人 user_id、信誉扣分、管理员敏感操作
--   （入口在 utils/security_log.py；记日志失败绝不能影响主流程，那里全程 try/except）
--
-- 谁读：后台 /admin/security（只读列表 + 总览聚合），Depends(get_current_admin)
--
-- ⚠️ 主键用 BIGSERIAL 而不是本项目惯用的 UUID：
--     这是**只增不改不删的流水表**，写入频率远高于实体表。
--     UUID v4 是随机的，做主键会让 B-tree 索引持续碎片化、页分裂；
--     而流水表的 id 没有任何对外暴露的语义（不像帖子 id 那样出现在 URL 里），
--     自增整数没有枚举风险。这是一处**有意偏离惯例**，不是疏忽。
--
-- ⚠️ 没有外键指向 profiles：
--     安全事件必须能在**用户已被删除之后**依然存在（那正是最需要留痕的时候）。
--     user_id 是裸 UUID，不做约束。
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.security_events (
    id           BIGSERIAL PRIMARY KEY,
    occurred_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- 事件类型。取值见 utils/security_log.py 的 EVENT_* 常量，代码与库两边必须一致。
    -- 形如 auth.login_failed / rate_limit.hit / content.banned_word（沿用消息中心那套「组.动作」）
    event_type   TEXT NOT NULL,

    -- info / warn / high / critical
    --   info     正常登记（生成审计、管理员操作）
    --   warn     可疑但未必恶意（限流命中、违禁词命中）
    --   high     明确的攻击行为（冒充他人 user_id、探测他人资料）
    --   critical 需要立刻看的（批量扫描、撞库、越权改数据）
    severity     TEXT NOT NULL DEFAULT 'info',

    user_id      UUID,                    -- 可空：未登录就没有
    ip           TEXT,                    -- 真实 IP，来源见 utils/client_ip.py
    method       TEXT,
    endpoint     TEXT,
    status_code  INT,
    user_agent   TEXT,

    -- 自由详情：命中的词、被冒充的 id、限流的键与阈值、原始请求摘要……
    detail       JSONB NOT NULL DEFAULT '{}'::jsonb
);

-- 列表默认排序（后台一进来就是这个查询）
CREATE INDEX IF NOT EXISTS idx_sec_events_time
    ON public.security_events (occurred_at DESC);

-- 按类型筛 + 看趋势
CREATE INDEX IF NOT EXISTS idx_sec_events_type_time
    ON public.security_events (event_type, occurred_at DESC);

-- 「这个用户干了什么」/「这个 IP 干了什么」—— 两个 Top 榜都走它
CREATE INDEX IF NOT EXISTS idx_sec_events_user
    ON public.security_events (user_id, occurred_at DESC) WHERE user_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_sec_events_ip
    ON public.security_events (ip, occurred_at DESC) WHERE ip IS NOT NULL;

-- 严重级筛选（后台要能只看 high 以上）
CREATE INDEX IF NOT EXISTS idx_sec_events_severity
    ON public.security_events (severity, occurred_at DESC)
    WHERE severity IN ('high', 'critical');

ALTER TABLE public.security_events ENABLE ROW LEVEL SECURITY;

-- ⚠️⚠️ 关键：Supabase 建表时的默认权限会把 anon / authenticated 一起授上
--     （ALTER DEFAULT PRIVILEGES ... GRANT ALL ON TABLES TO anon, authenticated, service_role），
--     所以**光建表不加这一段，安全事件表就是对全网公开的攻击日志**——
--     等于给攻击者一份「我们发现了什么、没发现什么」的清单。
--     这是本项目反复踩过的同一个坑（admin_tables.sql 建了表却只有 RLS 全放行策略，
--     最后 GRANT 才是唯一防线，见 admin_rework_20260930.sql 文件头）。
--
--     先 REVOKE 再 GRANT，顺序不能反，且必须成对出现。
REVOKE ALL ON public.security_events FROM anon, authenticated;
GRANT  SELECT, INSERT, UPDATE, DELETE ON public.security_events TO service_role;

-- BIGSERIAL 的序列要单独授权 —— GRANT ON TABLE 不覆盖序列。
-- 漏了这条的表现是：service_role 能读能写，但 INSERT 报 42501 permission denied for sequence。
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class
               WHERE relkind = 'S' AND relname = 'security_events_id_seq') THEN
        EXECUTE 'REVOKE ALL ON SEQUENCE public.security_events_id_seq FROM anon, authenticated';
        EXECUTE 'GRANT USAGE, SELECT ON SEQUENCE public.security_events_id_seq TO service_role';
    END IF;
END $$;


-- ============================================================================
-- 2. 立刻收掉：这两张表已经 100% 走 service_role，anon 一个访问点都没有
--
-- 已经逐个核过代码（2026-10-15）：
--
--   admin_audit_logs
--     写 utils/admin_middleware.py:83   → get_admin_headers()  = service_role
--     读 routers/admin.py:1409-1410     → get_admin_headers()  = service_role
--     全仓仅此两处访问，**无任何 anon 路径**。
--
--   content_reports
--     写 routers/community/messages.py:420 → get_supabase_service_headers()（代码里还专门写了注释说明为什么）
--     读/改 routers/admin.py:322/601/767/850/855/865 → get_admin_headers() = service_role
--     **无任何 anon 路径**。
--
-- 为什么不收就出事：
--   anon key 打包在前端产物里（frontend/.env 的 VITE_SUPABASE_KEY，Vite 构建时会**内联进 JS**，
--   任何人从浏览器里就能扒出来）。而这两张表的 RLS 策略是 USING (true) / WITH CHECK (true)
--   —— RLS 不是防线，**GRANT 才是唯一门槛**。现状等于：
--     · 全网都能读走全部管理员审计日志（谁封了谁、什么时候、什么理由）
--     · 全网都能改任意一条举报记录的状态和被举报人
--
-- ⚠️ 前提是 get_admin_headers() 真的以 service_role 身份执行。
--    它拼的是 apikey=SUPABASE_KEY(anon) + Authorization=Bearer SERVICE_ROLE_KEY
--     —— PostgREST 的角色取自 Authorization 里的 JWT，apikey 只用于网关识别项目，
--     所以这是成立的（admin_rework_20260930.sql 的整改实测也印证了这一点）。
--     执行完请跑下面的自检 4.4 复验。
-- ============================================================================
REVOKE ALL ON public.admin_audit_logs FROM anon, authenticated;
REVOKE ALL ON public.content_reports  FROM anon, authenticated;

-- 注：**故意不去改这两张表的 RLS 策略**（它们仍是 `USING (true)` / `WITH CHECK (true)`）。
--   理由：service_role 本来就绕过 RLS，而 anon 已经没有 GRANT 了 —— 策略改成
--   `TO service_role` 在功能上零变化，却会和 admin_tables.sql（那里是
--   `DROP POLICY ... ; CREATE POLICY ... USING (true)`）**互相打架**：
--   谁后跑谁说了算，将来有人重跑一次那个文件就又敞开了，且没有任何提示。
--   收口只留一处（GRANT），比两处各写一半可靠。
--   本项目的既定口径也是这条：RLS 不是防线，GRANT 才是（见 admin_rework_20260930.sql 文件头）。


-- ============================================================================
-- 3. ⚠️ 暂缓收的口子 —— 先看清，别盲收
--
-- 后端**当前仍有 122 处**在用 anon 访问 Supabase
-- （grep get_supabase_headers 的调用点，分布在 routers/ 和 services/ 下 17 个文件）。
-- 这些表**现在收 = 后端当场大面积 403**，表现会像「功能莫名其妙全坏了」。
--
-- 正确顺序（与 message_center_rework.sql 第 7 节同一条规矩）：
--     ① 把后端逐文件迁到 get_supabase_service_headers()
--     ② 验证功能正常
--     ③ 才执行 REVOKE
--
-- 已知高危（`grant_permissions.sql` 当年**主动**授给了 anon, authenticated 全套增删改）：
--     subject_plans · plan_daily_tasks · diagnosis_results ·
--     question_records · user_kp_mastery · cet4_questions
--   其中 cet4_questions 是**题库**，question_records 是**答题记录**——
--   拿公开的 anon key 就能读改任意用户的学习数据。这是比「题库被爬」更重的问题。
--
-- 先跑这段看全貌再决定（只读，不改任何东西）：
-- ---------------------------------------------------------------------------
-- SELECT table_name,
--        string_agg(privilege_type, ',' ORDER BY privilege_type) AS privs
-- FROM   information_schema.role_table_grants
-- WHERE  grantee = 'anon' AND table_schema = 'public'
-- GROUP  BY table_name
-- ORDER  BY table_name;
-- ---------------------------------------------------------------------------
--
-- 收的时候照这个写法（逐表注释，一次一张，收一张验一张）：
-- ---------------------------------------------------------------------------
-- REVOKE ALL ON public.cet4_questions   FROM anon, authenticated;
-- REVOKE ALL ON public.question_records FROM anon, authenticated;
-- ---------------------------------------------------------------------------


-- ============================================================================
-- 4. 自检 —— 执行完请跑这一段
-- ============================================================================

-- 4.1 security_events 建好了吗（应为 1 行）
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public' AND table_name = 'security_events';

-- 4.2 security_events 的授权（应只有 service_role 一行，且权限 4 个）
SELECT grantee, string_agg(privilege_type, ',' ORDER BY privilege_type) AS privs
FROM   information_schema.role_table_grants
WHERE  table_schema = 'public' AND table_name = 'security_events'
GROUP  BY grantee
ORDER  BY grantee;

-- 4.3 序列授权（应为空 —— anon/authenticated 不该有任何一行）
SELECT grantee, privilege_type
FROM   information_schema.role_usage_grants
WHERE  object_schema = 'public' AND object_name = 'security_events_id_seq';

-- 4.4 第 2 节收口的结果（应为空；有行说明还没生效，anon 仍能读审计日志）
SELECT grantee, privilege_type
FROM   information_schema.role_table_grants
WHERE  table_schema = 'public'
  AND  table_name IN ('admin_audit_logs', 'content_reports')
  AND  grantee IN ('anon', 'authenticated');

-- 4.5 RLS 是否为 security_events 开着（应为 true）
SELECT relname, relrowsecurity
FROM   pg_class WHERE relname = 'security_events';

-- 4.6 索引是否齐全（应为 5 行）
SELECT indexname FROM pg_indexes
WHERE schemaname = 'public' AND tablename = 'security_events'
ORDER BY indexname;
