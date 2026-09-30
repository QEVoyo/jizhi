-- 用户自定义快捷键（跟随账号，换设备也在）
--
-- 表结构照 user_theme_settings 的先例（见 fix_user_theme.sql）：
-- user_id 主键、一行一个用户、updated_at 记录时间。
--
-- 唯一不同：快捷键是**变长映射**（动作 id → 组合键），
-- 没法像主题那样「一个设置一列」——那些轴是固定的四轴，而动作会随时增删。
-- 所以用 JSONB 存整个映射：
--   {"nav.home": "Ctrl+Shift+H", "action.search": "Ctrl+K", ...}
-- 空串表示用户主动解绑了某个动作（与「没有这个键」区分开：
-- 前者是「我不想要」，后者是「还没配过、用默认」）。
--
-- 增删动作时**不需要动这张表**，也不需要迁移 —— 注册表里没有的 id 会被忽略。

CREATE TABLE IF NOT EXISTS public.user_shortcuts (
    user_id     UUID PRIMARY KEY,
    bindings    JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  public.user_shortcuts IS '用户自定义快捷键绑定（动作 id → 组合键）';
COMMENT ON COLUMN public.user_shortcuts.bindings IS 'JSONB 映射；值为空串表示主动解绑';

-- ⚠️ Supabase 手工建表不会自动 GRANT，必须显式授权，
--    否则 REST 访问会「静默返回空」而不是报错（这个坑项目里记过多次，
--    见 subject_plan_tables.sql 与 create_xiaoji_memory.sql 的注释）。
GRANT SELECT, INSERT, UPDATE, DELETE ON public.user_shortcuts TO anon, authenticated, service_role;

-- RLS 段：和先例 fix_user_theme.sql 保持一致。
-- 老实说，**开不开在安全上是等价的** —— 策略是 USING(true) 全放行，
-- 和「不开 RLS、只靠 GRANT」效果一样，身份校验都在 FastAPI 层做。
-- 补它是为了两点：① 和 user_theme_settings 逐句对齐，将来改策略不会漏这张表；
-- ② Supabase 后台对 public 下「没有 RLS」的表会报警告。
ALTER TABLE public.user_shortcuts ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "user_shortcuts_all_access" ON public.user_shortcuts;
CREATE POLICY "user_shortcuts_all_access"
  ON public.user_shortcuts
  FOR ALL
  USING (true)
  WITH CHECK (true);
