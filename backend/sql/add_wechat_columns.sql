-- 为 profiles 表添加微信登录字段
-- 执行方式：Supabase SQL Editor 或 psql

-- 1. 添加微信 openid 和 unionid 列（如果不存在）
ALTER TABLE public.profiles
ADD COLUMN IF NOT EXISTS wechat_openid TEXT,
ADD COLUMN IF NOT EXISTS wechat_unionid TEXT;

-- 2. 创建索引加速 openid/unionid 查询
CREATE INDEX IF NOT EXISTS idx_profiles_wechat_openid ON public.profiles(wechat_openid);
CREATE INDEX IF NOT EXISTS idx_profiles_wechat_unionid ON public.profiles(wechat_unionid);

-- 3. 注释
COMMENT ON COLUMN public.profiles.wechat_openid IS '微信 OpenID（单应用唯一）';
COMMENT ON COLUMN public.profiles.wechat_unionid IS '微信 UnionID（同开放平台下所有应用唯一）';
