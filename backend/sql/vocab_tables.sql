-- ============================================================
-- 词条系统三张表（词条 / 抓取记录 / 熟练度）
-- 词条本体全局共享（word 唯一，AI 生成一次全员复用）；记录与熟练度按用户隔离
-- 在 Supabase Dashboard → SQL Editor 中执行（可重复执行）
-- ============================================================

-- 1. 全局词条库
CREATE TABLE IF NOT EXISTS vocab_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    word TEXT NOT NULL UNIQUE,             -- 词条（小写）
    phonetic TEXT DEFAULT '',              -- 音标
    meaning TEXT DEFAULT '',               -- 中文释义
    example TEXT DEFAULT '',               -- 例句
    tags TEXT[] DEFAULT '{}',              -- cet4 / cet6 / kaoyan ...
    source TEXT DEFAULT 'ai',              -- ai / builtin
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. 抓取/讲解记录（触点计数来源）
CREATE TABLE IF NOT EXISTS vocab_lookups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    word TEXT NOT NULL,
    touchpoint TEXT NOT NULL,              -- xiaoji_vision（识图提词）/ chat_ask（对话问词义）
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. 词条熟练度（每人一份，EWMA 平滑）
CREATE TABLE IF NOT EXISTS word_mastery (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    word TEXT NOT NULL,
    mastery_score NUMERIC(5,1) DEFAULT 0,  -- 0-100
    correct_count INTEGER DEFAULT 0,
    total_count INTEGER DEFAULT 0,
    last_practiced_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, word)
);

-- ===== 授权（Supabase 手工建表不会自动 GRANT） =====
GRANT SELECT, INSERT, UPDATE, DELETE ON public.vocab_entries TO anon, authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.vocab_lookups TO anon, authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.word_mastery TO anon, authenticated, service_role;

-- ===== RLS（认证在 API 层，宽松策略） =====
ALTER TABLE vocab_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE vocab_lookups ENABLE ROW LEVEL SECURITY;
ALTER TABLE word_mastery ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Anyone can read entries" ON vocab_entries FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "API can manage lookups" ON vocab_lookups FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "API can manage mastery" ON word_mastery FOR ALL USING (true) WITH CHECK (true);

-- ===== 索引 =====
CREATE INDEX IF NOT EXISTS idx_vocab_entries_word ON vocab_entries(word);
CREATE INDEX IF NOT EXISTS idx_vocab_lookups_user ON vocab_lookups(user_id, touchpoint, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_word_mastery_user ON word_mastery(user_id, mastery_score);
