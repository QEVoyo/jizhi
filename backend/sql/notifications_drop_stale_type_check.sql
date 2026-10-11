-- ============================================================================
-- notifications：去掉建表时留下的 type 白名单 CHECK
-- 2026-10-08
--
-- ## 症状
--
-- 真跑每日推荐时，六条通知**全部**写入失败：
--
--     POST /rest/v1/notifications → 400
--     {"code":"23514","message":"..."}      ← 23514 = check_violation
--
-- 23514 是 CHECK 违约（外键是 23503、非空是 23502），所以不是权限也不是外键。
--
-- ## 根因（只读排查得出）
--
-- `notifications` 全表 5 行，`type` 只有两个值：`chat` / `system` ——
-- **都是无点号的老式类型**。而 2026-10-07 的消息中心改造引入了 66 个新类型，
-- 全是 `组.动作` 形式（`learning.daily_rec`、`chat.message`、`admin.new_report`…）。
--
-- 结论：这张表**建表时**（早于本仓库所有迁移文件）按当时的类型加过一个白名单
-- CHECK。改造后的所有新类型**一条都插不进去** ——
-- 也就是说 10-07 的 66 个消息点、10-08 和 10-08 续接的所有线，
-- 在真实库上**从来没有成功发出过一条通知**。
--
-- 一直没被发现，是因为这套东西**从来没在真库上跑过**（只编译过、只跑过假 HTTP 的
-- 单测）。这是这个项目反复栽的同一类病：**「写进去了」和「以为写进去了」长得一样**。
--
-- ## 做法
--
-- 1. **先把现有 CHECK 全打出来**（RAISE NOTICE），让执行的人看见原本是什么 ——
--    这样「根因」就是观察到的，而不是推断的。
-- 2. 删掉**定义里提到 type 或 group_key** 的那种白名单约束。
--    ⚠️ 不无差别删光所有 CHECK：`msg_count >= 0` 之类是有意义的，别误伤。
-- 3. **不再补一个新的类型白名单。** 类型合法性由
--    `notification_registry.spec()` 把关 —— 未注册的类型直接抛 KeyError，
--    这是 10-07 定的契约（见 notification_registry.py 文件头）。
--    在数据库里再维护一份白名单 = 同一个概念两个副本，加一个消息点要改两处，
--    迟早对不上（正是这次踩的坑：注册表加了 66 个，DB 白名单没跟着动）。
--
-- 幂等：可重复执行。第二次跑时第 1 步会打不出任何东西。
-- ============================================================================


-- ============================================================================
-- 1. 先看清楚这张表上到底有哪些 CHECK
-- ============================================================================
DO $$
DECLARE
    c RECORD;
    n INT := 0;
BEGIN
    RAISE NOTICE '---- notifications 上的 CHECK 约束 ----';
    FOR c IN
        SELECT conname, pg_get_constraintdef(oid) AS def
        FROM pg_constraint
        WHERE conrelid = 'public.notifications'::regclass
          AND contype = 'c'
        ORDER BY conname
    LOOP
        n := n + 1;
        RAISE NOTICE '  [%] %', n, c.conname;
        RAISE NOTICE '      %', c.def;
    END LOOP;
    IF n = 0 THEN
        RAISE NOTICE '  （没有 CHECK 约束 —— 那 23514 就不是它造成的，往下看第 3 步）';
    END IF;
END $$;


-- ============================================================================
-- 2. 删掉「按 type / group_key 列白名单」的那类约束
--
-- ⚠️ 第一版这里要求定义里出现 `IN (`，**那是错的、会让人白跑一趟**：
--    PostgreSQL 会把 `type IN ('chat','system')` 规范化成
--        CHECK ((type = ANY (ARRAY['chat'::text, 'system'::text])))
--    定义里根本没有 `IN (` —— 于是第 1 步看得见它、这一步却一个都不删，
--    跑完还是同样报 23514。改用**列名词边界**匹配。
--
-- ⚠️ 用 `\y`（词边界）而不是裸的 `ILIKE '%type%'`：后者会误伤
--    `jsonb_typeof(payload)` 这类。而 `jsonb_typeof` 里 `type` 前面是 `_`
--    （词字符），不构成词边界，正好被排除。`notif_type` 同理。
--
-- 其余 CHECK（如 `msg_count >= 0`）原样保留，并逐个打出来，看得见。
-- ============================================================================
DO $$
DECLARE
    c RECORD;
    dropped INT := 0;
BEGIN
    FOR c IN
        SELECT conname, pg_get_constraintdef(oid) AS def
        FROM pg_constraint
        WHERE conrelid = 'public.notifications'::regclass
          AND contype = 'c'
    LOOP
        IF c.def ~* '\y(type|group_key)\y' THEN
            EXECUTE format('ALTER TABLE public.notifications DROP CONSTRAINT %I', c.conname);
            RAISE NOTICE '已删除约束 %：%', c.conname, c.def;
            dropped := dropped + 1;
        ELSE
            RAISE NOTICE '保留约束 %（与 type/group_key 无关）：%', c.conname, c.def;
        END IF;
    END LOOP;
    IF dropped = 0 THEN
        RAISE NOTICE '';
        RAISE NOTICE '⚠️ 一个都没删。如果第 1 步确实列出了 CHECK 约束，';
        RAISE NOTICE '   把它的定义贴给我 —— 说明白名单不是建在 type/group_key 上，';
        RAISE NOTICE '   我的推断就是错的，得换个方向查。';
    END IF;
    RAISE NOTICE '共删除 % 个约束', dropped;
END $$;


-- ============================================================================
-- 3. 自检
--
-- ⚠️ 这一段**不会再写任何行**（之前那版探针想插测试行被拦下了 —— 拦得对，
--    不该为了验 schema 往生产表写东西）。它只报告「现在还剩下哪些 CHECK」，
--    由执行的人对照第 1 步的输出确认白名单那条确实没了。
-- ============================================================================
DO $$
DECLARE
    c RECORD;
    n INT := 0;
BEGIN
    RAISE NOTICE '---- 删除后剩余的 CHECK ----';
    FOR c IN
        SELECT conname, pg_get_constraintdef(oid) AS def
        FROM pg_constraint
        WHERE conrelid = 'public.notifications'::regclass
          AND contype = 'c'
    LOOP
        n := n + 1;
        RAISE NOTICE '  % -> %', c.conname, c.def;
    END LOOP;
    IF n = 0 THEN
        RAISE NOTICE '  （已无 CHECK —— 通知类型改由 notification_registry 把关）';
    END IF;
    RAISE NOTICE '';
    RAISE NOTICE '✅ 执行完毕后，重跑一次每日推荐即可验证：';
    RAISE NOTICE '   POST /community/generate-daily?user_id=<你>&gen_type=rec';
    RAISE NOTICE '   或直接点首页小基推荐卡片上的「生成今日推荐」';
END $$;
