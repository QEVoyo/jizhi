-- 视频库（2026-09-04 定稿）：知识点级模板生成视频
-- 设计要点：
--   video_library 与题目无关，主键轴 = (subject, knowledge_key, angle)；
--   一个知识点可按热度铺多个角度（低1/中3/高6+），use_count 驱动扩产
--   question_video_links 为题↔视频绑定 + 匹配分快照（检索排行免实时算）
-- RLS 全放行 + 三角色 GRANT（沿用 xiaoji 系表惯例），幂等可重复执行

-- ============ 1. 视频本体 ============
create table if not exists video_library (
  id uuid primary key default gen_random_uuid(),
  subject text not null default '',            -- 学科/考纲（cet4 / 高中数学 / …）
  knowledge_key text not null,                 -- 知识点键（稳定、url-safe，如 cet4:<kp_hash>）
  knowledge_name text not null,                -- 展示用知识点名（如「动词时态」）
  stage text not null default '',              -- 学段（过滤维度，可选）
  angle text not null default 'method',        -- 讲解角度（concept/method/pitfall/…）
  author_name text not null default '官方基智', -- 生成主（学科计划 = 官方基智；未来可用户自建知识视频）
  author_avatar text not null default '/logo.png',  -- 生成主头像（官方用 logo）
  style text not null default 'tutor',         -- 叙事风格
  template_key text not null default 'chalkboard',  -- 画面模板
  voice_key text not null default 'xiaoyan',   -- TTS 音色
  title text not null default '',
  script jsonb not null default '[]'::jsonb,   -- 结构化脚本段（播放器渲染用）
  script_text text not null default '',        -- 纯文本口播稿（重生成/TTS 复用用）
  audio_url text,                              -- 音轨地址（storage 公共读 URL）
  audio_duration real,                         -- 秒（估算）
  status text not null default 'generating',   -- generating / ready / failed
  error text,
  attempts int not null default 0,             -- 失败重试次数
  use_count int not null default 0,            -- 播放次数（热度/扩产决策）
  avg_rating real,                             -- 预留：用户评分
  goal int not null default 1,                 -- 生成时的目标条数（扩产依据）
  model text not null default '',              -- 生成元数据（脚本模型）
  prompt_version int not null default 1,
  tts_engine text not null default 'xunfei',
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  unique (subject, knowledge_key, angle)       -- 幂等格：同一知识点同角度只此一条
);

create index if not exists idx_video_lib_knowledge on video_library(subject, knowledge_key);
create index if not exists idx_video_lib_status on video_library(status);
create index if not exists idx_video_lib_use_count on video_library(use_count desc);

-- ============ 2. 题 ↔ 视频绑定（匹配分快照）============
create table if not exists question_video_links (
  question_fingerprint text not null,          -- 题干归一化指纹
  video_id uuid references video_library(id) on delete cascade,
  match_score int not null default 100,        -- 100 主知识点 / 70 同科目 / 55 泛相关
  created_at timestamptz default now(),
  primary key (question_fingerprint, video_id)
);

create index if not exists idx_question_video_links_fp on question_video_links(question_fingerprint);

-- ============ 3. RLS 全放行 + 三角色授权（幂等）============
alter table video_library enable row level security;
drop policy if exists video_library_all on video_library;
create policy video_library_all on video_library for all using (true) with check (true);

alter table question_video_links enable row level security;
drop policy if exists question_video_links_all on question_video_links;
create policy question_video_links_all on question_video_links for all using (true) with check (true);

grant select, insert, update, delete on video_library to anon, authenticated, service_role;
grant select, insert, update, delete on question_video_links to anon, authenticated, service_role;

-- ============ 4. Storage 公共读桶（音频直接可播）============
insert into storage.buckets (id, name, public)
values ('video-lib', 'video-lib', true)
on conflict (id) do nothing;