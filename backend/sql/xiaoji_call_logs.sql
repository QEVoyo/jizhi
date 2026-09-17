-- ============================================================
-- 小基语音通话日志表（2026-08-25）
-- 记录每次通话：起止时间 / 时长 / 对话轮数
-- 用途：小基页「使用日志」侧栏 + 智能体中心小基详情（通话次数/时长/时段分布）
-- 执行方式：Supabase SQL Editor 直接粘贴执行（幂等，可重复执行）
-- ============================================================

create table if not exists public.xiaoji_call_logs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null,
  started_at timestamptz not null default now(),
  ended_at timestamptz,
  duration_seconds int default 0,
  turns int default 0
);

create index if not exists idx_xiaoji_call_logs_user on public.xiaoji_call_logs(user_id);
create index if not exists idx_xiaoji_call_logs_started on public.xiaoji_call_logs(started_at);

alter table public.xiaoji_call_logs enable row level security;

-- 与 xiaoji_messages / xiaoji_config 相同的匿名 key 放行策略（xiaoji_rls_policies.sql 惯例）
drop policy if exists "xiaoji_call_logs_all" on public.xiaoji_call_logs;
create policy "xiaoji_call_logs_all" on public.xiaoji_call_logs
  for all using (true) with check (true);

grant all on public.xiaoji_call_logs to anon, authenticated;
grant all on public.xiaoji_call_logs to service_role;
