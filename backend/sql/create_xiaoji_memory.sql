-- 小基长期记忆表（2026-09-10）
--
-- 背景：小基此前只有「最近 10 条消息」的短期上下文——聊得越久，早期信息越读不到；
--   而要「按聊天记录生成个性化计划」就得往回读，一读全文就一次比一次耗 API。
--
-- 解法：三层上下文，读取成本与聊天长度**无关**
--   ① facts   事实档案（结构化：学习目标/当前状态/薄弱点/时间安排/偏好）——增量更新
--   ② summary 滚动摘要（更早的对话压成要点时间线）——每累积若干条增量压缩
--   ③ 最近若干轮原文（保持对话连贯）
--   读取 = ①+②+③（几百字恒定），不随历史增长。
--
-- 执行方式：Supabase SQL Editor 直接粘贴执行（幂等，可重复执行）。
-- 未执行前：全链路优雅降级——照旧只读最近 10 条原文，压缩跳过，聊天不受影响。

-- 1. 建表
create table if not exists public.xiaoji_memory (
  user_id          text primary key,
  facts            jsonb default '{}'::jsonb,   -- 结构化事实档案
  summary          text  default '',            -- 滚动摘要（要点时间线）
  summarized_upto  timestamptz,                 -- 摘要已覆盖到哪条消息（增量压缩游标）
  updated_at       timestamptz default now()
);

comment on table  public.xiaoji_memory is '小基长期记忆：事实档案 + 滚动摘要（三层上下文，读取成本恒定）';
comment on column public.xiaoji_memory.summarized_upto is '已压缩到的消息时间；下次只读这之后的新消息，避免重复读全文';

-- 2. RLS 全放行（与 xiaoji_messages / xiaoji_config 同惯例：后端统一匿名 key 访问，
--    身份校验在 FastAPI 层完成，数据库层依赖策略放行）
alter table public.xiaoji_memory enable row level security;
drop policy if exists "xiaoji_memory_all_access" on public.xiaoji_memory;
create policy "xiaoji_memory_all_access"
  on public.xiaoji_memory
  for all
  using (true)
  with check (true);

-- 3. 三角色 GRANT（缺 GRANT 会静默失败——历史上的老坑，见 grant_exam_paper_records.sql）
grant all on public.xiaoji_memory to anon;
grant all on public.xiaoji_memory to authenticated;
grant all on public.xiaoji_memory to service_role;

-- 验证：执行后进小基聊几句（≥12 条），后端日志出现
--   === [memory] 压缩完成 user=xxxxxxxx ===
-- 且该用户 xiaoji_memory 行的 summary 非空即成功。
