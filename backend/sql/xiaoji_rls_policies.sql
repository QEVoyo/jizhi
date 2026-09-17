-- 小基聊天记录 + 配置表 RLS 策略
-- 问题：xiaoji_messages / xiaoji_config 表存在但 RLS 开启且无策略
--   → 读取返回空数组（200），写入 401 被拒
--   → 表现：小基没有上下文记忆、设置保存失败
-- 说明：后端统一用匿名 key 访问 Supabase（见 services/supabase.py），
--   身份校验在 FastAPI 层完成（verify_user_match），数据库层依赖策略放行，
--   与 community 其他表（posts/messages/friends）的既有做法一致。

-- 1. 确保两张表开启 RLS（幂等）
alter table public.xiaoji_messages enable row level security;
alter table public.xiaoji_config enable row level security;

-- 2. 聊天记录：全操作放行（应用层已校验 user_id 归属）
drop policy if exists "xiaoji_messages_all_access" on public.xiaoji_messages;
create policy "xiaoji_messages_all_access"
  on public.xiaoji_messages
  for all
  using (true)
  with check (true);

-- 3. 小基配置：全操作放行
drop policy if exists "xiaoji_config_all_access" on public.xiaoji_config;
create policy "xiaoji_config_all_access"
  on public.xiaoji_config
  for all
  using (true)
  with check (true);

-- 验证：策略建立后，后端日志中
--   === 保存用户消息状态: 201 ===
--   === 保存助手消息状态: 201 ===
