-- 视频库·社交与广场（2026-09-04 用户拍板「视频库要很完善」）
-- 幂等可重复执行；依赖已建的 video_library（缺作者列的环境先跑 fix_video_library_author.sql）

-- ============ 1. video_library 扩展：归属 + 发布状态 + 冗余计数 ============
alter table video_library add column if not exists owner_user_id text;               -- null = 官方
alter table video_library add column if not exists publish_status text not null default 'public';  -- private/pending/public/rejected
alter table video_library add column if not exists views_count bigint not null default 0;
alter table video_library add column if not exists likes_count int not null default 0;
alter table video_library add column if not exists favorites_count int not null default 0;
alter table video_library add column if not exists comments_count int not null default 0;

create index if not exists idx_video_lib_square on video_library(publish_status, status, views_count desc);

-- ============ 2. 点赞 / 收藏（toggle，主键幂等）============
create table if not exists video_likes (
  video_id uuid references video_library(id) on delete cascade,
  user_id text not null,
  created_at timestamptz default now(),
  primary key (video_id, user_id)
);

create table if not exists video_favorites (
  video_id uuid references video_library(id) on delete cascade,
  user_id text not null,
  created_at timestamptz default now(),
  primary key (video_id, user_id)
);

-- ============ 3. 评论（1 级，软删除）============
create table if not exists video_comments (
  id uuid primary key default gen_random_uuid(),
  video_id uuid references video_library(id) on delete cascade,
  user_id text not null,
  user_name text not null default '',
  user_avatar text not null default '',
  content text not null,
  deleted boolean not null default false,
  created_at timestamptz default now()
);
create index if not exists idx_video_comments_video on video_comments(video_id, created_at desc);

-- ============ 4. 举报 ============
create table if not exists video_reports (
  id uuid primary key default gen_random_uuid(),
  video_id uuid references video_library(id) on delete cascade,
  user_id text not null,
  reason text not null default '',
  detail text not null default '',
  status text not null default 'pending',   -- pending / dismissed / removed
  handled_by text not null default '',
  handled_at timestamptz,
  created_at timestamptz default now()
);
create index if not exists idx_video_reports_status on video_reports(status);

-- ============ 5. 播放记录（浏览量，人·日去重）+ 热点词库 ============
create table if not exists video_views (
  video_id uuid references video_library(id) on delete cascade,
  user_id text not null,
  view_date date not null default current_date,
  created_at timestamptz default now(),
  primary key (video_id, user_id, view_date)
);

-- 热点词库（2026-09-04 用户方案：进入该视频的题目知识点累积 → 推送词库匹配）
create table if not exists video_keyword_hits (
  video_id uuid references video_library(id) on delete cascade,
  knowledge_key text not null,
  subject text not null default '',
  hits int not null default 1,
  last_hit_at timestamptz default now(),
  primary key (video_id, knowledge_key)
);

-- ============ 6. RLS 全放行 + 授权（沿用全站惯例）============
do $$
declare t text;
begin
  foreach t in array array['video_likes','video_favorites','video_comments','video_reports','video_views','video_keyword_hits']
  loop
    execute format('alter table %I enable row level security', t);
    execute format('drop policy if exists %I_all on %I', t, t);
    execute format('create policy %I_all on %I for all using (true) with check (true)', t, t);
    execute format('grant select, insert, update, delete on %I to anon, authenticated, service_role', t);
  end loop;
end $$;