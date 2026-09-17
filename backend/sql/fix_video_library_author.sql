-- 视频库补丁（2026-09-04 追加定稿「生成主」）：
-- 建表在先、作者定稿在后 → 已执行 create_video_library.sql 的环境直接跑这个，幂等
alter table video_library add column if not exists author_name text not null default '官方基智';
alter table video_library add column if not exists author_avatar text not null default '/logo.png';