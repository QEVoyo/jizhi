-- ============================================================
-- 设置页修复：xiaoji_config 补列 + notification_settings 授权
-- 2026-08-24 实测发现：
--   1. 小基设置保存报 400「Could not find the 'voice_speed' column ...」
--      → xiaoji_config 缺 voice_speed / voice_volume / voice_name 三列
--      → 设置页任何一项保存都失败（前端提示「保存失败，但本地已生效」）
--   2. 通知设置读写 401「permission denied for table notification_settings」
--      → 表建好后未授权给 API 角色（anon / service_role 都没有权限）
--      → 通知开关保存静默失败、刷新回默认值
-- 全部幂等，可重复执行。
-- ============================================================

-- 1. 小基配置表：补语音参数列
alter table public.xiaoji_config add column if not exists voice_speed int default 5;
alter table public.xiaoji_config add column if not exists voice_volume int default 5;
alter table public.xiaoji_config add column if not exists voice_name text default 'xiaoyan';

-- 2. 通知设置表：补齐列（若表是旧结构，避免缺列报错）
alter table public.notification_settings add column if not exists chat_enabled boolean default true;
alter table public.notification_settings add column if not exists social_enabled boolean default true;
alter table public.notification_settings add column if not exists learning_enabled boolean default true;
alter table public.notification_settings add column if not exists plan_reminder_enabled boolean default true;
alter table public.notification_settings add column if not exists evaluation_enabled boolean default true;
alter table public.notification_settings add column if not exists daily_rec_enabled boolean default true;
alter table public.notification_settings add column if not exists daily_summary_enabled boolean default true;
alter table public.notification_settings add column if not exists system_enabled boolean default true;
alter table public.notification_settings add column if not exists daily_rec_time text default '08:00';
alter table public.notification_settings add column if not exists daily_summary_time text default '07:00';
alter table public.notification_settings add column if not exists updated_at timestamptz default now();

-- 3. 通知设置表：授权 + RLS 放行（与 xiaoji 表惯例一致，应用层校验 user_id）
grant all on public.notification_settings to anon, service_role;
alter table public.notification_settings enable row level security;
drop policy if exists "notification_settings_all_access" on public.notification_settings;
create policy "notification_settings_all_access"
  on public.notification_settings
  for all
  using (true)
  with check (true);

-- 验证：
--   select * from public.xiaoji_config limit 1;
--   → 应能看到 voice_speed / voice_volume / voice_name 三列
--   前端：小基设置保存应提示「设置已保存」；通知开关保存后刷新页面应保持
