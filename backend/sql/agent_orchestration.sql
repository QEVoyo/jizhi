-- ============================================================
-- 多智能体编排 / 自我循环 / 上传抽象 — 数据层 DDL
--
-- 设计见 project1/AGENT_ORCHESTRATION_DESIGN.md
-- 在 Supabase Dashboard → SQL Editor 执行；全部可重复执行。
--
-- 新增 11 张表：
--   agent_defs           Agent 定义与版本
--   agent_runs           一次编排运行
--   agent_run_steps      节点级轨迹/检查点
--   agent_messages       A2A 会议记录
--   agent_memory         M3/M4 分层记忆
--   agent_decisions      调参日记 / LLM 仲裁结果
--   patrol_rules         巡检规则定义
--   patrol_user_state    每用户规则状态（接受度/抑制）
--   patrol_events        巡检事件与行为回流
--   upload_jobs          上传任务状态机 + 文档画像
--   upload_seeds         可出题点（抽象结果）
--
-- 补列：
--   agent_tuning_log     日记/证据/置信/复盘
--   questions            origin / 来源文件 / 来源种子 / 源文引用 / 校验
--   question_sets        source / 来源文件 / 上传任务
--   generation_history   source / set_id / file_name / upload_job_id
-- ============================================================

-- ============================================================
-- 1. Agent 定义与版本
-- ============================================================
CREATE TABLE IF NOT EXISTS agent_defs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_key TEXT NOT NULL,
    version INT NOT NULL DEFAULT 1,
    name TEXT NOT NULL DEFAULT '',
    role TEXT NOT NULL DEFAULT '',
    system_prompt TEXT NOT NULL DEFAULT '',
    tools JSONB NOT NULL DEFAULT '[]'::jsonb,
    model TEXT NOT NULL DEFAULT '',
    config JSONB NOT NULL DEFAULT '{}'::jsonb,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    user_id UUID,                          -- NULL = 全局定义；非空 = 用户覆盖
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 全局定义与用户覆盖分别唯一（Postgres 的 UNIQUE 对 NULL 不去重，所以用部分索引）
CREATE UNIQUE INDEX IF NOT EXISTS uq_agent_defs_global
    ON agent_defs(agent_key, version) WHERE user_id IS NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_agent_defs_user
    ON agent_defs(agent_key, version, user_id) WHERE user_id IS NOT NULL;

-- ============================================================
-- 2. 一次编排运行
-- ============================================================
CREATE TABLE IF NOT EXISTS agent_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    workflow_key TEXT NOT NULL,            -- question_gen / evaluate / file_to_questions / tuning_debate
    mode TEXT NOT NULL DEFAULT 'auto',     -- auto / quick / team / background
    status TEXT NOT NULL DEFAULT 'queued', -- queued / running / paused / awaiting_confirm / confirmed / completed / failed / cancelled
    title TEXT NOT NULL DEFAULT '',        -- 任务中心展示名（如「生成：高数讲义.pdf」）
    link TEXT NOT NULL DEFAULT '',         -- 完成后跳转（如 /set-detail?id=...）
    progress INT NOT NULL DEFAULT 0,       -- 0-100，任务中心/小基进度环用
    stage TEXT NOT NULL DEFAULT '',        -- queued / extracting / profiling / seeding / awaiting_confirm / generating / crosschecking / saving / ready ...
    input JSONB NOT NULL DEFAULT '{}'::jsonb,
    state JSONB NOT NULL DEFAULT '{}'::jsonb,
    output JSONB,
    confidence NUMERIC(4,3),
    llm_calls INT NOT NULL DEFAULT 0,
    tokens INT NOT NULL DEFAULT 0,
    cost NUMERIC(12,6) NOT NULL DEFAULT 0,
    latency_ms INT,
    error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ
);

-- 老库补列（2026-10-31：任务中心与智能体中心合并，run 即任务）
ALTER TABLE agent_runs ADD COLUMN IF NOT EXISTS title TEXT NOT NULL DEFAULT '';
ALTER TABLE agent_runs ADD COLUMN IF NOT EXISTS link TEXT NOT NULL DEFAULT '';
ALTER TABLE agent_runs ADD COLUMN IF NOT EXISTS progress INT NOT NULL DEFAULT 0;
ALTER TABLE agent_runs ADD COLUMN IF NOT EXISTS stage TEXT NOT NULL DEFAULT '';

-- 老库补列（2026-11-02：任务控制层 —— 排序/暂停/删除/重试/心跳）
ALTER TABLE agent_runs ADD COLUMN IF NOT EXISTS kind TEXT NOT NULL DEFAULT '';
ALTER TABLE agent_runs ADD COLUMN IF NOT EXISTS queue_pos INT NOT NULL DEFAULT 0;
ALTER TABLE agent_runs ADD COLUMN IF NOT EXISTS pause_requested BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE agent_runs ADD COLUMN IF NOT EXISTS paused_at TIMESTAMPTZ;
ALTER TABLE agent_runs ADD COLUMN IF NOT EXISTS checkpoint JSONB NOT NULL DEFAULT '{}'::jsonb;
ALTER TABLE agent_runs ADD COLUMN IF NOT EXISTS heartbeat_at TIMESTAMPTZ;
ALTER TABLE agent_runs ADD COLUMN IF NOT EXISTS lease_owner TEXT NOT NULL DEFAULT '';
ALTER TABLE agent_runs ADD COLUMN IF NOT EXISTS attempt INT NOT NULL DEFAULT 1;
ALTER TABLE agent_runs ADD COLUMN IF NOT EXISTS retry_of UUID;
ALTER TABLE agent_runs ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
ALTER TABLE agent_runs ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

-- ============================================================
-- 3. 节点级轨迹 / 检查点
-- ============================================================
CREATE TABLE IF NOT EXISTS agent_run_steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES agent_runs(id) ON DELETE CASCADE,
    node_key TEXT NOT NULL,
    agent_key TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'pending', -- pending / running / completed / failed / skipped
    input JSONB,
    output JSONB,
    tool_calls JSONB NOT NULL DEFAULT '[]'::jsonb,
    verification JSONB,
    degraded BOOLEAN NOT NULL DEFAULT FALSE,
    retry_count INT NOT NULL DEFAULT 0,
    started_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 4. A2A 会议记录
-- ============================================================
CREATE TABLE IF NOT EXISTS agent_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES agent_runs(id) ON DELETE CASCADE,
    seq INT NOT NULL,
    from_agent TEXT NOT NULL,
    to_agent TEXT NOT NULL DEFAULT '',
    kind TEXT NOT NULL,                    -- task / proposal / critique / verdict / result / escalation
    content TEXT NOT NULL DEFAULT '',
    data JSONB NOT NULL DEFAULT '{}'::jsonb,
    confidence NUMERIC(4,3),
    refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (run_id, seq)
);

-- ============================================================
-- 5. 分层记忆（M3 语义 / M4 程序）
-- ============================================================
CREATE TABLE IF NOT EXISTS agent_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    scope TEXT NOT NULL DEFAULT 'user',    -- user / agent:{key} / workflow:{key}
    kind TEXT NOT NULL,                    -- fact / weakness / misconception / preference / strategy / event
    key TEXT NOT NULL,                     -- kp:函数单调性 / pref:format ...
    value JSONB NOT NULL DEFAULT '{}'::jsonb,
    confidence NUMERIC(4,3) NOT NULL DEFAULT 0.5,
    evidence JSONB NOT NULL DEFAULT '[]'::jsonb,
    hit_count INT NOT NULL DEFAULT 0,
    last_used_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, scope, kind, key)
);

-- ============================================================
-- 6. 调参日记 / LLM 仲裁结果
-- ============================================================
CREATE TABLE IF NOT EXISTS agent_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    run_id UUID,                           -- tuning_debate 的 run（可空）
    signal TEXT NOT NULL DEFAULT '',       -- 触发信号（如 plan_completion_drop）
    evidence JSONB NOT NULL DEFAULT '{}'::jsonb,
    diagnosis TEXT NOT NULL DEFAULT '',
    confidence NUMERIC(4,3),
    changes JSONB NOT NULL DEFAULT '[]'::jsonb,
    actions JSONB NOT NULL DEFAULT '[]'::jsonb,
    rejected JSONB NOT NULL DEFAULT '[]'::jsonb,
    diary TEXT NOT NULL DEFAULT '',
    model TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'applied', -- proposed / applied / reverted / rejected
    agrees BOOLEAN,                         -- LLM 是否认同规则这次的调整
    suggestion TEXT NOT NULL DEFAULT '',    -- LLM 认为更好的做法（P0 只展示，不自动执行）
    feedback JSONB NOT NULL DEFAULT '[]'::jsonb, -- 用户: agree / disagree / lock
    outcome JSONB,                          -- 7 天后复盘
    review_at TIMESTAMPTZ,
    fallback BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 7. 巡检规则定义
-- ============================================================
CREATE TABLE IF NOT EXISTS patrol_rules (
    rule_key TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    config JSONB NOT NULL DEFAULT '{}'::jsonb,
    priority INT NOT NULL DEFAULT 5,
    cooldown_hours INT NOT NULL DEFAULT 24,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 8. 每用户规则状态（接受度 / 抑制）
-- ============================================================
CREATE TABLE IF NOT EXISTS patrol_user_state (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    rule_key TEXT NOT NULL,
    last_fired_at TIMESTAMPTZ,
    last_acted_at TIMESTAMPTZ,
    delivered INT NOT NULL DEFAULT 0,
    acted INT NOT NULL DEFAULT 0,
    dismissed INT NOT NULL DEFAULT 0,
    receptivity NUMERIC(4,3) NOT NULL DEFAULT 0.5,
    suppress_until TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, rule_key)
);

-- ============================================================
-- 9. 巡检事件与行为回流
-- ============================================================
CREATE TABLE IF NOT EXISTS patrol_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    rule_key TEXT NOT NULL,
    dedupe_key TEXT NOT NULL DEFAULT '',
    score NUMERIC(6,3) NOT NULL DEFAULT 0,
    title TEXT NOT NULL DEFAULT '',
    content TEXT NOT NULL DEFAULT '',
    evidence JSONB NOT NULL DEFAULT '{}'::jsonb,
    status TEXT NOT NULL DEFAULT 'pending', -- pending / delivered / acted / dismissed / snoozed / expired
    mode_hint TEXT NOT NULL DEFAULT 'bubble', -- bubble / popup / pet / inbox
    delivered_at TIMESTAMPTZ,
    acted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 同一用户 + 规则 + 去重键只留一行（按天/对象去重）
CREATE UNIQUE INDEX IF NOT EXISTS uq_patrol_events_dedupe
    ON patrol_events(user_id, rule_key, dedupe_key);

-- ============================================================
-- 10. 上传任务状态机 + 文档画像
-- ============================================================
CREATE TABLE IF NOT EXISTS upload_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    run_id UUID,                            -- 关联 agent_runs（任务中心与智能体中心共用一条记录）
    batch_id UUID,                          -- 多文件批量出题时同组
    filename TEXT NOT NULL DEFAULT '',
    mime TEXT NOT NULL DEFAULT '',
    size BIGINT NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'queued',  -- queued / parsing / paused / awaiting_confirm / confirmed / generating / ready / failed / cancelled
    progress INT NOT NULL DEFAULT 0,
    stage TEXT NOT NULL DEFAULT '',         -- queued / extracting / profiling / seeding / awaiting_confirm / generating / crosschecking / saving / ready ...
    cancel_requested BOOLEAN NOT NULL DEFAULT FALSE,
    source_type TEXT NOT NULL DEFAULT '',   -- pdf / pptx / docx / xlsx / image / text
    profile JSONB NOT NULL DEFAULT '{}'::jsonb,
    seed_count INT NOT NULL DEFAULT 0,
    selected_count INT NOT NULL DEFAULT 0,
    generated_count INT NOT NULL DEFAULT 0,
    passed_count INT NOT NULL DEFAULT 0,
    error TEXT,
    result_set_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    queued_at TIMESTAMPTZ,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ
);

-- 老库补列（2026-10-31：上传任务接入 agent_runs + 跨页进度/取消）
ALTER TABLE upload_jobs ADD COLUMN IF NOT EXISTS run_id UUID;
ALTER TABLE upload_jobs ADD COLUMN IF NOT EXISTS batch_id UUID;
ALTER TABLE upload_jobs ADD COLUMN IF NOT EXISTS stage TEXT NOT NULL DEFAULT '';
ALTER TABLE upload_jobs ADD COLUMN IF NOT EXISTS cancel_requested BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE upload_jobs ADD COLUMN IF NOT EXISTS queued_at TIMESTAMPTZ;
ALTER TABLE upload_jobs ADD COLUMN IF NOT EXISTS started_at TIMESTAMPTZ;
ALTER TABLE upload_jobs ADD COLUMN IF NOT EXISTS finished_at TIMESTAMPTZ;

-- 老库补列（2026-11-02：暂停/继续 + 可恢复生成）
ALTER TABLE upload_jobs ADD COLUMN IF NOT EXISTS pause_requested BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE upload_jobs ADD COLUMN IF NOT EXISTS paused_at TIMESTAMPTZ;
ALTER TABLE upload_jobs ADD COLUMN IF NOT EXISTS pause_stage TEXT NOT NULL DEFAULT '';
ALTER TABLE upload_jobs ADD COLUMN IF NOT EXISTS arq_job_id TEXT NOT NULL DEFAULT '';

-- ============================================================
-- 11. 可出题点（抽象结果）
-- ============================================================
CREATE TABLE IF NOT EXISTS upload_seeds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES upload_jobs(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    seed_key TEXT NOT NULL DEFAULT '',
    kind TEXT NOT NULL DEFAULT 'fact',       -- definition/fact/relation/process/comparison/formula/calculation/argument/data_trend/method/limitation ...
    concept TEXT NOT NULL DEFAULT '',
    proposition TEXT NOT NULL DEFAULT '',
    evidence JSONB NOT NULL DEFAULT '{}'::jsonb,   -- {chunk_id, quote, page}
    source_ref JSONB NOT NULL DEFAULT '{}'::jsonb,
    question_forms JSONB NOT NULL DEFAULT '[]'::jsonb,
    distractor_angles JSONB NOT NULL DEFAULT '[]'::jsonb,
    difficulty TEXT NOT NULL DEFAULT '中等',
    questionability NUMERIC(4,3) NOT NULL DEFAULT 0,
    self_contained BOOLEAN NOT NULL DEFAULT TRUE,
    requires_external_context BOOLEAN NOT NULL DEFAULT FALSE,
    reason TEXT NOT NULL DEFAULT '',
    selected BOOLEAN NOT NULL DEFAULT FALSE,
    generated_question_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (job_id, seed_key)
);

-- ============================================================
-- 11.1 生成单元（可暂停/继续的检查点）
-- ============================================================
-- 上传生成以前只在内存里 gather；暂停/worker 崩溃后无法续跑。
-- 每个「种子 × 题型」落一行，题目生成完就写回，恢复时跳过已完成单元。
CREATE TABLE IF NOT EXISTS upload_job_units (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES upload_jobs(id) ON DELETE CASCADE,
    run_id UUID,
    idx INT NOT NULL,
    seed_id UUID,
    qtype TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'pending', -- pending / generating / done / failed / skipped
    question JSONB,
    error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (job_id, idx)
);

-- ============================================================
-- 12. 补列：磨合记录 → 调参日记
-- ============================================================
ALTER TABLE agent_tuning_log ADD COLUMN IF NOT EXISTS decision_id UUID;
ALTER TABLE agent_tuning_log ADD COLUMN IF NOT EXISTS trigger_signal TEXT;
ALTER TABLE agent_tuning_log ADD COLUMN IF NOT EXISTS evidence JSONB;
ALTER TABLE agent_tuning_log ADD COLUMN IF NOT EXISTS diagnosis TEXT;
ALTER TABLE agent_tuning_log ADD COLUMN IF NOT EXISTS confidence NUMERIC(4,3);
ALTER TABLE agent_tuning_log ADD COLUMN IF NOT EXISTS rationale TEXT;
ALTER TABLE agent_tuning_log ADD COLUMN IF NOT EXISTS alternatives JSONB;
ALTER TABLE agent_tuning_log ADD COLUMN IF NOT EXISTS diary TEXT;
ALTER TABLE agent_tuning_log ADD COLUMN IF NOT EXISTS model TEXT;
ALTER TABLE agent_tuning_log ADD COLUMN IF NOT EXISTS review_at TIMESTAMPTZ;
ALTER TABLE agent_tuning_log ADD COLUMN IF NOT EXISTS outcome JSONB;
ALTER TABLE agent_tuning_log ADD COLUMN IF NOT EXISTS fallback BOOLEAN DEFAULT FALSE;

-- ============================================================
-- 13. 补列：题目来源与校验
-- ============================================================
-- 已有题目绝大多数是生成/题库来的，默认 'generated' 比 'chat' 更贴近事实；
-- 上传生成的题会显式写 origin='upload'。
ALTER TABLE questions ADD COLUMN IF NOT EXISTS origin TEXT DEFAULT 'generated';
UPDATE questions SET origin = 'generated' WHERE origin IS NULL;
ALTER TABLE questions ADD COLUMN IF NOT EXISTS source_file_id UUID;
ALTER TABLE questions ADD COLUMN IF NOT EXISTS source_seed_id UUID;
ALTER TABLE questions ADD COLUMN IF NOT EXISTS source_ref JSONB;
ALTER TABLE questions ADD COLUMN IF NOT EXISTS verification JSONB;

-- ============================================================
-- 14. 补列：题集来源
-- ============================================================
ALTER TABLE question_sets ADD COLUMN IF NOT EXISTS source TEXT DEFAULT 'manual';
ALTER TABLE question_sets ADD COLUMN IF NOT EXISTS source_file_id UUID;
ALTER TABLE question_sets ADD COLUMN IF NOT EXISTS upload_job_id UUID;

-- ============================================================
-- 15. 补列：生成历史来源/题集/文件
-- ============================================================
ALTER TABLE generation_history ADD COLUMN IF NOT EXISTS source TEXT DEFAULT 'generate';
ALTER TABLE generation_history ADD COLUMN IF NOT EXISTS set_id UUID;
ALTER TABLE generation_history ADD COLUMN IF NOT EXISTS file_name TEXT;
ALTER TABLE generation_history ADD COLUMN IF NOT EXISTS upload_job_id UUID;

-- ============================================================
-- 索引
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_agent_runs_user ON agent_runs(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_runs_workflow ON agent_runs(workflow_key, status);
CREATE INDEX IF NOT EXISTS idx_agent_runs_active ON agent_runs(user_id, status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_run_steps_run ON agent_run_steps(run_id, node_key);
CREATE INDEX IF NOT EXISTS idx_agent_messages_run ON agent_messages(run_id, seq);
CREATE INDEX IF NOT EXISTS idx_agent_memory_user ON agent_memory(user_id, scope, kind);
CREATE INDEX IF NOT EXISTS idx_agent_decisions_user ON agent_decisions(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_patrol_events_user ON patrol_events(user_id, status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_patrol_user_state_user ON patrol_user_state(user_id, rule_key);
CREATE INDEX IF NOT EXISTS idx_upload_jobs_user ON upload_jobs(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_upload_jobs_active ON upload_jobs(user_id, status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_upload_jobs_run ON upload_jobs(run_id);
CREATE INDEX IF NOT EXISTS idx_upload_seeds_job ON upload_seeds(job_id, questionability DESC);
CREATE INDEX IF NOT EXISTS idx_upload_job_units_job ON upload_job_units(job_id, status, idx);
CREATE INDEX IF NOT EXISTS idx_agent_runs_user_queue
    ON agent_runs(user_id, status, queue_pos, created_at) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_agent_runs_user_active
    ON agent_runs(user_id, updated_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_questions_source_file ON questions(source_file_id);
CREATE INDEX IF NOT EXISTS idx_generation_history_source ON generation_history(user_id, source, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_question_sets_source ON question_sets(user_id, source, created_at DESC);

-- ============================================================
-- RLS（认证在 API 层；与 subject_plan_tables.sql 惯例一致）
-- ============================================================
ALTER TABLE agent_defs ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_run_steps ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_memory ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE patrol_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE patrol_user_state ENABLE ROW LEVEL SECURITY;
ALTER TABLE patrol_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE upload_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE upload_seeds ENABLE ROW LEVEL SECURITY;
ALTER TABLE upload_job_units ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "API can manage agent defs" ON agent_defs;
DROP POLICY IF EXISTS "API can manage agent runs" ON agent_runs;
DROP POLICY IF EXISTS "API can manage agent run steps" ON agent_run_steps;
DROP POLICY IF EXISTS "API can manage agent messages" ON agent_messages;
DROP POLICY IF EXISTS "API can manage agent memory" ON agent_memory;
DROP POLICY IF EXISTS "API can manage agent decisions" ON agent_decisions;
DROP POLICY IF EXISTS "API can manage patrol rules" ON patrol_rules;
DROP POLICY IF EXISTS "API can manage patrol user state" ON patrol_user_state;
DROP POLICY IF EXISTS "API can manage patrol events" ON patrol_events;
DROP POLICY IF EXISTS "API can manage upload jobs" ON upload_jobs;
DROP POLICY IF EXISTS "API can manage upload seeds" ON upload_seeds;
DROP POLICY IF EXISTS "API can manage upload job units" ON upload_job_units;

CREATE POLICY "API can manage agent defs" ON agent_defs FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "API can manage agent runs" ON agent_runs FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "API can manage agent run steps" ON agent_run_steps FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "API can manage agent messages" ON agent_messages FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "API can manage agent memory" ON agent_memory FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "API can manage agent decisions" ON agent_decisions FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "API can manage patrol rules" ON patrol_rules FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "API can manage patrol user state" ON patrol_user_state FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "API can manage patrol events" ON patrol_events FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "API can manage upload jobs" ON upload_jobs FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "API can manage upload seeds" ON upload_seeds FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "API can manage upload job units" ON upload_job_units FOR ALL USING (true) WITH CHECK (true);

-- ============================================================
-- 授权（Supabase 手工建表不会自动 GRANT）
-- ============================================================
GRANT SELECT, INSERT, UPDATE, DELETE ON public.agent_defs TO anon, authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.agent_runs TO anon, authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.agent_run_steps TO anon, authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.agent_messages TO anon, authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.agent_memory TO anon, authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.agent_decisions TO anon, authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.patrol_rules TO anon, authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.patrol_user_state TO anon, authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.patrol_events TO anon, authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.upload_jobs TO anon, authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.upload_seeds TO anon, authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.upload_job_units TO anon, authenticated, service_role;

-- ============================================================
-- 原子重排（拖拽排序）
-- ============================================================
-- 只允许排自己的 queued / paused 任务；返回真正更新的行数。
-- 后端必须校验返回值 == len(p_ids)，少一行就说明有任务不属于本人或状态不允许。
CREATE OR REPLACE FUNCTION reorder_agent_runs(p_user_id UUID, p_ids UUID[])
RETURNS INT
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    n INT;
BEGIN
    -- 服务端调用（service_role）时 auth.uid() 为 NULL；浏览器直连时只允许排自己
    IF auth.uid() IS NOT NULL AND auth.uid() <> p_user_id THEN
        RETURN 0;
    END IF;

    WITH ord AS (
        SELECT id, (ord - 1)::int AS pos
        FROM unnest(p_ids) WITH ORDINALITY AS t(id, ord)
    ), upd AS (
        UPDATE agent_runs r
        SET queue_pos = ord.pos, updated_at = NOW()
        FROM ord
        WHERE r.id = ord.id
          AND r.user_id = p_user_id
          AND r.deleted_at IS NULL
          AND r.status IN ('queued', 'paused')
        RETURNING 1
    )
    SELECT count(*) INTO n FROM upd;
    RETURN n;
END;
$$;

GRANT EXECUTE ON FUNCTION reorder_agent_runs(UUID, UUID[]) TO anon, authenticated, service_role;

-- ============================================================
-- 巡检规则种子（可在后台/前端覆盖 config）
-- ============================================================
INSERT INTO patrol_rules (rule_key, name, enabled, config, priority, cooldown_hours) VALUES
    ('review_gap',           '错题复习提醒', TRUE, '{"min_wrong": 5, "days": 3}'::jsonb,           7, 48),
    ('inactive',             '连续未学习关心', TRUE, '{"days": 3}'::jsonb,                         6, 72),
    ('plan_behind',          '计划落后提醒', TRUE, '{"threshold": 50, "days": 3}'::jsonb,           6, 72),
    ('streak_risk',          '连击风险提醒', TRUE, '{"min_streak": 3, "after_hour": 20}'::jsonb,    5, 24),
    ('mastery_stuck',        '知识点卡住', TRUE, '{"wrong_times": 3, "days": 7}'::jsonb,            7, 72),
    ('upload_pending',       '题集待做提醒', TRUE, '{"hours": 24}'::jsonb,                          4, 24),
    ('exam_countdown',       '考试倒计时', TRUE, '{"days": 3}'::jsonb,                              8, 24),
    ('verification_warning', '质检异常提醒', TRUE, '{"pass_rate": 60}'::jsonb,                      5, 168)
ON CONFLICT (rule_key) DO NOTHING;
