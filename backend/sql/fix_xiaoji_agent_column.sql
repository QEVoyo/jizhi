-- xiaoji_messages 补 agent 列：队员署名持久化（2026-09-02）
-- 背景：小基世界「队友真实分流」——规划/评估 Agent 的回复以 assistant 消息落库，
--   agent 字段记录是哪位队员的产出，历史消息/刷新后重进页面徽章不丢。
-- 执行方式：Supabase SQL Editor 直接粘贴执行（幂等，可重复执行）。
-- 未执行前：队员回复降级为普通小基消息保存（聊天不受影响，只是栏目署名不落库）。

ALTER TABLE public.xiaoji_messages ADD COLUMN IF NOT EXISTS agent TEXT;