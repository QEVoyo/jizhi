-- ============================================================================
-- AI 生成审计 · 数据层
-- 2026-10-15
--
-- 为什么需要一张**专门的**表：
--
--   安全中心的「生成审计」那一格一直是空的。原因是全仓 40 处 AI 调用各写各的，
--   没有任何一处能回答「我们的 AI 生成到底跑成什么样」。
--
--   而安全事件表**不能兼职** —— 这条是刻意的：security_events 的队列有上限，
--   满了会**丢最旧的**（见 utils/security_log.py）。一次生成写一条事件的话，
--   正常使用几小时就能把队列刷满，等于**让 AI 用量把真正的攻击记录挤掉**。
--   所以那边只记失败和拦截（低频、高价值），全量生成审计落在这里。
--
-- 与 security_events 的三个区别（决定了它们的结构不同）：
--   1. 这里记**成功也记**；那边只记失败/拦截
--   2. 这里的量级大得多（每次生成一行），所以字段要窄、索引要有针对性
--   3. 这里回答的是「用了多少、跑得怎么样」；那边回答的是「谁在攻击」
--
-- 谁写：utils/gen_audit.py（由 utils/safety_gateway.py 每次生成后调用）
-- 谁读：routers/admin_security.py 的 /admin/security/gen-audit*
--
-- 幂等：可重复执行。
-- ============================================================================


CREATE TABLE IF NOT EXISTS public.ai_generation_audit (
    id           BIGSERIAL PRIMARY KEY,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- 用途标识。形如 question_gen / daily_rec / video_script / xiaoji_chat，
    -- 与 utils/safety_gateway.py 里 generate(purpose=...) 传的一致。
    -- 后台按它分组看「哪一类生成最贵、最容易失败」。
    purpose      TEXT NOT NULL,

    -- 可空：有些生成是系统触发的（每日推荐、视频暖库），背后没有具体用户。
    user_id      UUID,

    provider     TEXT NOT NULL,        -- deepseek / qwen
    model        TEXT,                 -- 实际用的模型名（便于对比换模型前后的表现）

    -- 结局。取值见 utils/gen_audit.py 的 STATUS_* 常量，**代码与库两边必须一致**。
    --   ok                  正常返回
    --   blocked_input       入闸拦下（用户可控文本命中违禁词）
    --   quota_denied        信誉配额用尽
    --   provider_error      模型调用失败（超时/网络/4xx/5xx）
    --   empty_output        模型返回空白
    --   too_short           出闸长度不足
    --   json_parse_failed   要求 JSON 但抠不出来
    --
    -- ⚠️ **刻意不加 CHECK 约束**，理由同 notifications 那次教训
    --    （见 notifications_drop_stale_type_check.sql）：调用点还在陆续往网关迁，
    --    新的失败类型随时会出现。加了 CHECK 的话，一个新类型会让**整条审计写入
    --    失败** —— 而审计写失败恰恰是最不该发生的事。合法性在 Python 侧校验并告警。
    status       TEXT NOT NULL,

    -- 耗时（毫秒）。只对真的调了模型的 status 有意义，其余为 NULL。
    -- 这是回答「换模型值不值」的主要依据。
    latency_ms   INT,

    -- 只记**长度**不记**内容**。审计要的是规模和成功率，
    -- 内容属于用户隐私（而且可能是很长的 prompt），入库既没必要也有风险。
    input_chars  INT,
    output_chars INT,

    -- 自由详情：失败原因、命中的词、重试次数等。
    -- 同样要注意别把用户原文整段塞进来。
    detail       JSONB NOT NULL DEFAULT '{}'::jsonb
);


-- 列表页默认排序（后台一进来就是这个查询）
CREATE INDEX IF NOT EXISTS idx_gen_audit_time
    ON public.ai_generation_audit (created_at DESC);

-- 「哪类生成最多/最慢/最容易失败」—— 调用途级策略时的主要依据
CREATE INDEX IF NOT EXISTS idx_gen_audit_purpose_time
    ON public.ai_generation_audit (purpose, created_at DESC);

-- 「这个用户用了多少」——排查刷量、核对配额
CREATE INDEX IF NOT EXISTS idx_gen_audit_user_time
    ON public.ai_generation_audit (user_id, created_at DESC)
    WHERE user_id IS NOT NULL;

-- 只看失败的。**部分索引**：绝大多数行是 ok，把它们排除掉索引能小一个量级。
-- 同 security_events 的 severity 部分索引。
CREATE INDEX IF NOT EXISTS idx_gen_audit_failed_time
    ON public.ai_generation_audit (status, created_at DESC)
    WHERE status <> 'ok';


ALTER TABLE public.ai_generation_audit ENABLE ROW LEVEL SECURITY;

-- ⚠️⚠️ Supabase 建表时的默认权限会把 anon / authenticated 一起授上
--     （ALTER DEFAULT PRIVILEGES ... GRANT ALL ON TABLES TO anon, authenticated, service_role）。
--     这张表里是**全站 AI 用量明细 + 用户 id**，敞开等于把用量画像公开。
--     先 REVOKE 再 GRANT，顺序不能反，且必须成对出现 —— 同 security_center.sql。
REVOKE ALL ON public.ai_generation_audit FROM anon, authenticated;
GRANT  SELECT, INSERT, UPDATE, DELETE ON public.ai_generation_audit TO service_role;

-- BIGSERIAL 的序列要单独授权 —— GRANT ON TABLE 不覆盖序列。
-- 漏了这条的表现是：service_role 能读能写，但 INSERT 报
-- 42501 permission denied for sequence ai_generation_audit_id_seq。
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class
               WHERE relkind = 'S' AND relname = 'ai_generation_audit_id_seq') THEN
        EXECUTE 'REVOKE ALL ON SEQUENCE public.ai_generation_audit_id_seq FROM anon, authenticated';
        EXECUTE 'GRANT USAGE, SELECT ON SEQUENCE public.ai_generation_audit_id_seq TO service_role';
    END IF;
END $$;


-- ============================================================================
-- ⚠️ 容量：这张表是**只增**的，而且是全站每次生成一行。
--
--    按现在的调用点（已迁 2/40）量很小；等 38 处都迁完、用户量上来之后，
--    它会成为库里增长最快的表。到那时需要**保留策略**（比如只留 90 天），
--    形式可以是：
--      · 定时任务 DELETE ... WHERE created_at < now() - interval '90 days'
--      · 或按月分区（PARTITION BY RANGE (created_at)）后直接 DROP 老分区
--
--    现在**故意不做**：还没有真实量级数据，拍一个保留天数就是瞎猜
--    （这个项目在 JUMP_DELTA=20 上吃过一次「阈值拍脑袋定」的亏）。
--    先让它长，等有数了再定。
-- ============================================================================


-- ============================================================================
-- 自检（跑完看一眼）
-- ============================================================================
-- 表在不在、权限对不对、索引齐不齐：
--
--   SELECT count(*) FROM public.ai_generation_audit;          -- 应为 0
--
--   -- 确认 anon 读不到（应报 401 或空）
--   -- 用 anon key 打 GET /rest/v1/ai_generation_audit?select=id
--
--   SELECT indexname FROM pg_indexes
--    WHERE tablename = 'ai_generation_audit' ORDER BY indexname;
--   -- 应看到 idx_gen_audit_time / _purpose_time / _user_time / _failed_time
