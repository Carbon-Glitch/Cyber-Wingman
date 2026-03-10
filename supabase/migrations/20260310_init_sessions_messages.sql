-- ───────────────────────────────────────────────────────────────
-- 赛博僚机 Supabase Schema（在 Supabase SQL Editor 中执行）
-- 执行前提：参考项目中的 init.sql 已执行（创建了 users 表 + auth trigger）
-- ───────────────────────────────────────────────────────────────

-- ── 会话表 (Chat Sessions) ────────────────────────────────────
-- 每个用户可以拥有多个独立对话会话
create table if not exists sessions (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references auth.users on delete cascade not null,
  -- 会话标题（首条消息的前30字符，由后端生成）
  title text not null default 'New Chat',
  -- 使用的四象限身份
  quadrant text not null default 'tactical'
    check (quadrant in ('tactical', 'strategist', 'bestie', 'advisor')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- RLS: 仅用户本人能操作自己的会话
alter table sessions enable row level security;
create policy "user_owns_session_select" on sessions for select using (auth.uid() = user_id);
create policy "user_owns_session_insert" on sessions for insert with check (auth.uid() = user_id);
create policy "user_owns_session_update" on sessions for update using (auth.uid() = user_id);
create policy "user_owns_session_delete" on sessions for delete using (auth.uid() = user_id);

-- 自动更新 updated_at
create or replace function update_updated_at_column()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger sessions_updated_at
  before update on sessions
  for each row execute function update_updated_at_column();


-- ── 消息表 (Chat Messages) ────────────────────────────────────
-- 每条消息挂在一个 session 下，session 删除时消息级联删除
create table if not exists messages (
  id uuid default gen_random_uuid() primary key,
  session_id uuid references sessions on delete cascade not null,
  user_id uuid references auth.users on delete cascade not null,
  role text not null check (role in ('user', 'assistant')),
  content text not null,
  -- 前端展示用的额外元数据（如 mode, skill 等）
  metadata jsonb default '{}'::jsonb,
  created_at timestamptz not null default now()
);

-- RLS: 仅用户本人能操作自己的消息
alter table messages enable row level security;
create policy "user_owns_messages_select" on messages for select using (auth.uid() = user_id);
create policy "user_owns_messages_insert" on messages for insert with check (auth.uid() = user_id);
create policy "user_owns_messages_delete" on messages for delete using (auth.uid() = user_id);

-- ── 索引优化 ─────────────────────────────────────────────────
create index if not exists sessions_user_id_idx on sessions(user_id, updated_at desc);
create index if not exists messages_session_id_idx on messages(session_id, created_at asc);
