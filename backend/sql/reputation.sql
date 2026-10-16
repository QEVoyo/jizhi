-- ============================================================================
-- 信誉值 · 数据层
-- 2026-10-15
--
-- 信誉值是什么：一个**可增可减的风控分**（默认 100，范围 0-100），
--   与 user_stats.points 那个「只增不减的成长分/段位」是两回事 ——
--   学习分不该因为一次骂人被清零，段位也不该变得有惩罚性。
--   个人中心里两个并排展示，都参与权益。
--
-- 四张表（原计划三张，写的时候拆出第四张，理由见第 4 节）：
--   1. user_reputation       当前分（懒创建，没行 = 100 分）
--   2. user_reputation_logs  加减分流水（**申诉全靠它**）
--   3. reputation_rules      加减分规则
--   4. reputation_tiers      档位阈值 + 每档权益
--
-- 「规则不许散在代码里」是刻意的：本项目 2026-10-08 的教训是
--   「阈值这种东西不该由我发明」—— 当时 JUMP_DELTA=20 是拍脑袋定的，
--   收敛到常量并点名之后才算数。信誉值的阈值只多不少，所以全部进表。
--
-- 幂等：可重复执行。种子数据用 ON CONFLICT DO NOTHING ——
--   重跑**不会**把管理员调过的数值冲回默认（这点很重要，否则调完一次白调）。
-- ============================================================================


-- ============================================================================
-- 1. user_reputation —— 当前分
--
-- 懒创建：读的时候查不到就当 100 分，**不做全量回填**。
--   理由同 user_stats（career.py:445）：全站用户一次性插一批默认行，
--   绝大多数人这辈子不会产生一条流水，表里全是死行。
--
-- ⚠️ 外键用 profiles(id) ON DELETE CASCADE —— 与 supabase_migration.sql:21 同一套。
--   信誉**是依附于用户**的数据，人没了分就该没。
--   （对比 security_events：那张表刻意**不加**外键，因为安全事件必须能在
--     用户被删之后依然存在 —— 那正是最需要留痕的时候。两个需求不同，别统一。）
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.user_reputation (
    user_id     UUID PRIMARY KEY REFERENCES public.profiles(id) ON DELETE CASCADE,
    score       INT NOT NULL DEFAULT 100,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT user_reputation_score_range CHECK (score >= 0 AND score <= 100)
);

-- 后台要能「按档位筛选用户」，也要能拉低分榜
CREATE INDEX IF NOT EXISTS idx_reputation_score ON public.user_reputation (score);


-- ============================================================================
-- 2. user_reputation_logs —— 加减分流水
--
-- ⚠️ 这张表是**申诉的唯一依据**。用户来问「我为什么是 60 分」，
--   能答上来的前提就是每一次变动都有行、且写清了是哪条规则、因为什么事。
--   所以任何改分路径都**必须**写这里 —— 后台手动改分也不例外，
--   且要记下 operator_id 和理由。
--
-- score_after 冗余存当时的分数：只存 delta 的话，事后要靠累加才能还原，
--   而累加一旦漏了一条（比如某次写入失败）就永远对不上。
--
-- 主键用 BIGSERIAL（同 security_events）：只增不改不删的流水，
--   UUID v4 的随机性会让 B-tree 索引持续碎片化，而这里的 id 不对外暴露。
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.user_reputation_logs (
    id           BIGSERIAL PRIMARY KEY,
    user_id      UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    -- 扣分为负、加分为正。**允许 0** —— 见下方说明，这是必须保留的一种记录。
    delta        INT NOT NULL,
    score_after  INT NOT NULL,               -- 这次变动之后的分数
    reason_code  TEXT NOT NULL,              -- 规则 code；后台手动改分用 "admin.manual"
    reason_text  TEXT,                       -- 给人看的一句话
    source_type  TEXT,                       -- report / sanction / content / ai / system / admin
    source_id    TEXT,                       -- 关联的业务 id（举报 id、视频 id…）
    operator_id  UUID,                       -- 管理员手动改分时记；系统自动为空
    detail       JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ⚠️ delta = 0 是**合法且必要**的一种记录，不要加 CHECK (delta <> 0)。
--
--   场景：用户已经是 0 分，又违规一次。分数没得可扣，但"今天又违规了"这件事
--   必须留下 —— 因为自然恢复的判定是「连续 N 天没有扣分记录」。
--   不记这一条的话，一个在 0 分持续违规的人，恢复计时器会照常往前走，
--   明明还在违规却开始攒恢复天数。这条 0 分流水就是用来重置那个计时器的。
--   （恢复判定因此按「非恢复类的、delta <= 0 的记录」来查，见 utils/reputation.py。）

CREATE INDEX IF NOT EXISTS idx_rep_logs_user ON public.user_reputation_logs (user_id, created_at DESC);
-- 看「哪条规则最常触发」——调阈值时的主要依据
CREATE INDEX IF NOT EXISTS idx_rep_logs_code ON public.user_reputation_logs (reason_code, created_at DESC);
-- 幂等判重（once_per_day / daily_cap）要按天扫某个用户的某条规则
CREATE INDEX IF NOT EXISTS idx_rep_logs_user_code_time
    ON public.user_reputation_logs (user_id, reason_code, created_at DESC);


-- ============================================================================
-- 3. reputation_rules —— 加减分规则
--
-- daily_cap 的语义：**该规则每天累计变动上限（取绝对值）**，NULL = 不限。
--   · 加分类要它 —— 否则刷一个动作就能刷满（用户的原始担忧）
--   · 扣分类多数不要它 —— 扣分被 cap 住就失去了威慑
--   · 例外：rate_limit.abuse 给了 -20/天。扫描器一晚上能触发几千次限流，
--     不 cap 的话一次扫描直接把人打到 0 分，此后所有正常功能全废 ——
--     那不是风控，那是误伤。
--
-- once_per_day：这条规则每个用户每天最多生效一次（按自然日）。
--   语义上幂等的规则（每日登录）用它，比设 daily_cap=1 更直白。
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.reputation_rules (
    code         TEXT PRIMARY KEY,
    kind         TEXT NOT NULL,              -- deduct / award / recovery
    delta        INT NOT NULL,               -- 扣分为负、加分为正
    once_per_day BOOLEAN NOT NULL DEFAULT FALSE,
    daily_cap    INT,                        -- 见上方说明；NULL = 不限
    enabled      BOOLEAN NOT NULL DEFAULT TRUE,
    label        TEXT NOT NULL,              -- 后台/个人中心展示用
    description  TEXT,
    sort_order   INT NOT NULL DEFAULT 100,
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT reputation_rules_kind CHECK (kind IN ('deduct', 'award', 'recovery')),
    CONSTRAINT reputation_rules_sign CHECK (
        (kind = 'deduct' AND delta < 0) OR (kind <> 'deduct' AND delta > 0)
    )
);

-- ── 自然恢复专用的列（2026-10-15 追加）──
-- 只对 kind='recovery' 的规则有意义：要求「连续清白至少这么多天」才发这一档。
-- 用单独的 ALTER 是为了让已经执行过本文件的人也能补上（幂等，可重复跑）。
ALTER TABLE public.reputation_rules ADD COLUMN IF NOT EXISTS min_streak_days INT;


-- ============================================================================
-- 4. reputation_tiers —— 档位阈值 + 每档权益
--
-- 为什么从 reputation_rules 里拆出来（原计划是「一张配置表」）：
--   规则是一条条**事件**（命中违禁词 -3），档位是一段段**区间**
--   （90-100 是什么待遇）。字段几乎不重叠 —— 硬塞一张表会得到
--   半列永远 NULL 的表，读的时候还得先判 kind 才知道哪些列有意义。
--   拆开后两张表各自列齐、各自可校验（档位区间不重叠能查、规则符号能查）。
--
-- ⚠️ 下面这些数字（90/70/40、配额、先审后发）**是初稿，需要拍板**。
--   定它们的时候参照的是「别误伤正常用户」，不是算出来的。
--   改只需要 UPDATE 这张表，代码里没有任何硬编码的阈值。
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.reputation_tiers (
    code                 TEXT PRIMARY KEY,
    min_score            INT NOT NULL,           -- 含
    max_score            INT NOT NULL,           -- 含
    ai_daily_quota       INT NOT NULL DEFAULT -1,  -- AI 生成每日次数；-1 = 不限，0 = 禁止
    content_needs_review BOOLEAN NOT NULL DEFAULT FALSE,  -- 发帖/评论是否先审后发
    can_publish          BOOLEAN NOT NULL DEFAULT TRUE,   -- 能否发布内容
    badge                TEXT,                   -- 正反馈徽章文案；NULL = 无
    perks_text           TEXT,                   -- 给用户看的权益说明（个人中心展示）
    sort_order           INT NOT NULL DEFAULT 100,
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT reputation_tiers_range CHECK (min_score <= max_score)
);


-- ============================================================================
-- 5. 权限：只给 service_role
--
-- 同 security_center.sql 第 1 节：Supabase 建表时的默认权限会把
-- anon / authenticated 一起授上，所以**必须先 REVOKE 再 GRANT**，成对出现。
--
-- 这张表被滥用的后果：anon key 打包在前端产物里（谁都能扒），
-- 若放开 anon，任何人可以直接 PATCH 自己的 score=100 —— 信誉值当场作废。
-- ============================================================================
REVOKE ALL ON public.user_reputation      FROM anon, authenticated;
REVOKE ALL ON public.user_reputation_logs FROM anon, authenticated;
REVOKE ALL ON public.reputation_rules     FROM anon, authenticated;
REVOKE ALL ON public.reputation_tiers     FROM anon, authenticated;

GRANT SELECT, INSERT, UPDATE, DELETE ON public.user_reputation      TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.user_reputation_logs TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.reputation_rules     TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.reputation_tiers     TO service_role;

-- BIGSERIAL 的序列要单独授权 —— GRANT ON TABLE 不覆盖序列。
-- 漏了这条的表现：能读能写，但 INSERT 报 42501 permission denied for sequence。
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class
               WHERE relkind = 'S' AND relname = 'user_reputation_logs_id_seq') THEN
        EXECUTE 'REVOKE ALL ON SEQUENCE public.user_reputation_logs_id_seq FROM anon, authenticated';
        EXECUTE 'GRANT USAGE, SELECT ON SEQUENCE public.user_reputation_logs_id_seq TO service_role';
    END IF;
END $$;


-- ============================================================================
-- 6. 种子：规则
--
-- ON CONFLICT DO NOTHING —— 重跑不覆盖管理员改过的值。
-- 想恢复默认得手动 UPDATE 或先 DELETE 再跑。
-- ============================================================================
INSERT INTO public.reputation_rules
    (code, kind, delta, once_per_day, daily_cap, label, description, sort_order)
VALUES
    -- ── 扣分 ──
    ('content.banned_word', 'deduct',  -3, FALSE, NULL,
     '内容命中违禁词', '用户提交的文本（提问、评论、AI 生成提示词等）被违禁词闸拦下', 10),
    ('rate_limit.abuse',    'deduct',  -2, FALSE, 20,
     '异常高频触发限流', '触发限流本身多半只是误触或手滑；这条针对的是被自动化刷。'
     '每天最多累计扣 20 —— 不 cap 的话一次扫描就能把正常用户打到 0 分', 20),
    ('sanction.warn',       'deduct',  -5, FALSE, NULL,
     '收到警告', '管理员处置举报时给出的警告', 30),
    ('report.upheld',       'deduct', -10, FALSE, NULL,
     '举报被判定成立', '内容被判定违规（与「收到警告」可叠加，因为性质更重）', 40),
    ('sanction.mute',       'deduct', -15, FALSE, NULL,
     '被禁言', '管理员禁言', 50),
    ('access.impersonation','deduct', -20, FALSE, NULL,
     '冒充他人身份', '请求里自报的 user_id 与凭证不符 —— 这几乎没有误报的可能', 60),
    ('sanction.ban',        'deduct', -40, FALSE, NULL,
     '被封禁', '管理员封禁。单独一条就足以跌进最高危档', 70),

    -- ── 加分 ──
    ('login.daily',              'award', 1, TRUE,  1,
     '每日首次登录', '按自然日去重', 110),
    ('learning.daily_rec_done',  'award', 1, TRUE,  1,
     '完成每日学习推荐', '按自然日去重', 120),
    ('content.approved',         'award', 2, FALSE, 4,
     '内容通过审核发布', '发帖/评论/视频过审。封顶 4/天 —— 否则刷量就能刷分', 130),
    ('report.accepted',          'award', 5, FALSE, 10,
     '举报被采纳', '管理员处置举报且判定成立', 140),

    -- ── 自然恢复 ──
    --
    -- 【为什么是一条曲线，而不是一个固定值】
    --
    -- 第一版设计是「连续 7 天无违规 → +2」。算一下就知道不能这么干：
    -- 从 0 分爬回 100 需要 50 次恢复 = **350 天**。那不叫恢复，叫永久留疤 ——
    -- 而且一次误判就够把人废掉，误判是一定会有的。
    --
    -- 现在这条曲线的性质：
    --   · 前 3 天冷却（刚被扣分不该马上回血，否则扣分形同虚设）
    --   · 之后**越清白恢复越快**（+1 → +2 → +3 → +5），有正向牵引
    --   · 从 0 分回到满分约 38 天：轻度过失（扣 3 分）约 6 天就回来了，
    --     严重违规（封禁扣 40 分）要一个多月 —— 威慑和容错都在
    --   · 每一步都在界面上可预期（"连续清白 N 天，还差 M 天到下一档"）
    --
    -- 引擎每次只发**当前清白天数够得着的最高一档**（见 utils/reputation.py）。
    ('recovery.streak_3',  'recovery', 1, TRUE, 1, '连续 3 天无违规',  '冷却结束，开始缓慢回血', 200),
    ('recovery.streak_7',  'recovery', 2, TRUE, 2, '连续 7 天无违规',  '一周没出事', 210),
    ('recovery.streak_14', 'recovery', 3, TRUE, 3, '连续 14 天无违规', '两周清白', 220),
    ('recovery.streak_30', 'recovery', 5, TRUE, 5, '连续 30 天无违规', '一个月清白，恢复加速', 230)
ON CONFLICT (code) DO NOTHING;

-- 把第一版那个固定 +2/7 天的规则停用（它太慢了，见上面的说明）。
-- 用 UPDATE 而不是 DELETE：留着能看到它曾经存在过，历史流水也指向它。
UPDATE public.reputation_rules SET enabled = FALSE, updated_at = now()
WHERE code = 'recovery.clean_7d';

-- 补 min_streak_days（ON CONFLICT DO NOTHING 在"行已存在"时不会更新这一列，
-- 所以单独 UPDATE 一次，保证重跑本文件能把新列填上）
UPDATE public.reputation_rules SET min_streak_days = 3  WHERE code = 'recovery.streak_3'  AND min_streak_days IS DISTINCT FROM 3;
UPDATE public.reputation_rules SET min_streak_days = 7  WHERE code = 'recovery.streak_7'  AND min_streak_days IS DISTINCT FROM 7;
UPDATE public.reputation_rules SET min_streak_days = 14 WHERE code = 'recovery.streak_14' AND min_streak_days IS DISTINCT FROM 14;
UPDATE public.reputation_rules SET min_streak_days = 30 WHERE code = 'recovery.streak_30' AND min_streak_days IS DISTINCT FROM 30;


-- ============================================================================
-- 7. 种子：档位
--
-- ⚠️ 区间必须无缝无重叠地覆盖 0-100（自检 8.5 会查）。
-- ============================================================================
INSERT INTO public.reputation_tiers
    (code, min_score, max_score, ai_daily_quota, content_needs_review, can_publish,
     badge, perks_text, sort_order)
VALUES
    ('excellent', 90, 100, -1, FALSE, TRUE,
     '守信',
     'AI 生成不限次 · 内容免审直发 · 个人中心显示守信徽章', 10),
    ('normal',    70,  89, 100, FALSE, TRUE,
     NULL,
     '各项功能正常使用（AI 生成每天上限 100 次）', 20),
    ('restricted',40,  69,  10, TRUE,  TRUE,
     NULL,
     'AI 生成每天限 10 次 · 新发内容需先经过审核', 30),
    ('high_risk',  0,  39,   0, TRUE,  FALSE,
     NULL,
     '暂停 AI 生成与内容发布；可联系管理员申诉', 40)
ON CONFLICT (code) DO NOTHING;


-- ============================================================================
-- 8. 自检 —— 执行完请跑这一段
-- ============================================================================

-- 8.1 四张表都建好了吗（应 4 行）
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('user_reputation','user_reputation_logs','reputation_rules','reputation_tiers')
ORDER BY table_name;

-- 8.2 规则条数（应 12 行：7 扣分 + 4 加分 + 1 恢复）
SELECT kind, count(*) AS 条数, sum(delta) AS 合计
FROM public.reputation_rules GROUP BY kind ORDER BY kind;

-- 8.3 档位是否覆盖 0-100 且不重叠（应 4 行，且缺口/重叠查询为空）
SELECT code, min_score, max_score, ai_daily_quota, content_needs_review, can_publish
FROM public.reputation_tiers ORDER BY min_score DESC;

-- 8.3b 重叠检测（期望 0 行）
SELECT '重叠' AS 问题, a.code AS 档A, b.code AS 档B, a.min_score, a.max_score
FROM public.reputation_tiers a
JOIN public.reputation_tiers b
  ON a.code < b.code                       -- 每对只查一次
 AND a.min_score <= b.max_score
 AND a.max_score >= b.min_score;

-- 8.3c 缺口检测：区间按起点排序后，每一档的「终点+1」必须正好等于下一档的「起点」
--      （期望 0 行）
SELECT '缺口' AS 问题, code AS 本档, max_score AS 本档终点, next_min AS 下一档起点
FROM (
    SELECT code, max_score,
           LEAD(min_score) OVER (ORDER BY min_score) AS next_min
    FROM public.reputation_tiers
) x
WHERE next_min IS NOT NULL AND next_min <> max_score + 1;

-- 8.3d 覆盖范围（期望 0 / 100）
SELECT min(min_score) AS 最低档起点, max(max_score) AS 最高档终点
FROM public.reputation_tiers;

-- 8.4 权限：anon / authenticated 不该有任何一行（应空）
SELECT grantee, table_name, privilege_type
FROM   information_schema.role_table_grants
WHERE  table_schema = 'public'
  AND  table_name IN ('user_reputation','user_reputation_logs','reputation_rules','reputation_tiers')
  AND  grantee IN ('anon','authenticated');

-- 8.5 序列授权（应只有 service_role）
SELECT grantee, privilege_type FROM information_schema.role_usage_grants
WHERE object_schema = 'public' AND object_name = 'user_reputation_logs_id_seq';
