-- 账号主题定制表（2026-09-02 品牌/字体 → 2026-09-03 四轴：背景/组件/主题/字体）
-- 背景：用户拍板「自定义背景色 + 组件色 + 主题色 + 字体色，舍弃现有背景图」——
--   四轴方案存账号（跨设备同步），页面底色氛围由背景色/品牌色前端派生、毛玻璃白描层随组件色联动。
-- 端点：GET /auth/theme/{user_id}、PUT /auth/theme（backend/routers/auth.py，全量保存）
-- 执行方式：Supabase SQL Editor 直接粘贴执行（幂等，可重复执行）。
-- 未执行前：读写接口返回 400/默认值，主题定制界面可用但不同步。

CREATE TABLE IF NOT EXISTS public.user_theme_settings (
  user_id UUID PRIMARY KEY,
  brand_color TEXT DEFAULT '#409EFF',      -- 主题色 hex
  text_scheme TEXT DEFAULT 'default',      -- 字体预设档：default / paper / warmink / cyanink / ink
  text_overrides JSONB DEFAULT NULL,       -- 自定义三档字色 {"primary","secondary","muted"}
  bg_color TEXT DEFAULT NULL,              -- 自定义背景色 hex；NULL = 跟随浅/深模式
  surface_color TEXT DEFAULT NULL,         -- 自定义组件色（毛玻璃）hex；NULL = 白描层默认
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 已建表的旧环境幂等补列
ALTER TABLE public.user_theme_settings ADD COLUMN IF NOT EXISTS bg_color TEXT DEFAULT NULL;
ALTER TABLE public.user_theme_settings ADD COLUMN IF NOT EXISTS surface_color TEXT DEFAULT NULL;

ALTER TABLE public.user_theme_settings ENABLE ROW LEVEL SECURITY;

-- 与 xiaoji 系表相同惯例：后端统一匿名 key 访问，身份校验在 FastAPI 层
DROP POLICY IF EXISTS "user_theme_all_access" ON public.user_theme_settings;
CREATE POLICY "user_theme_all_access"
  ON public.user_theme_settings
  FOR ALL
  USING (true)
  WITH CHECK (true);

GRANT ALL ON public.user_theme_settings TO anon, authenticated;
GRANT ALL ON public.user_theme_settings TO service_role;