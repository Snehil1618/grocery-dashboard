-- 001_people.sql
-- Needed by the personal-links version of app.py (branch `personal-links`).
-- Run once in Supabase → SQL Editor. Safe to re-run the CREATE parts.

-- 1. Remember who sent each bill (Make.com fills this from Telegram: Message → From → ID)
alter table receipts add column if not exists telegram_user_id bigint;

-- 2. People who may open the dashboard, each with a personal link code
create table if not exists dashboard_users (
  id               bigint generated always as identity primary key,
  display_name     text        not null,
  access_code      text        not null unique,
  telegram_user_id bigint      unique,
  is_admin         boolean     not null default false,
  created_at       timestamptz not null default now()
);

alter table dashboard_users enable row level security;

-- The app uses the anon key, which only lives in Streamlit's server-side secrets.
-- It lists, adds, edits and removes people from the People tab.
drop policy if exists "app read people"   on dashboard_users;
drop policy if exists "app add people"    on dashboard_users;
drop policy if exists "app edit people"   on dashboard_users;
drop policy if exists "app remove people" on dashboard_users;
create policy "app read people"   on dashboard_users for select to anon using (true);
create policy "app add people"    on dashboard_users for insert to anon with check (true);
create policy "app edit people"   on dashboard_users for update to anon using (true) with check (true);
create policy "app remove people" on dashboard_users for delete to anon using (true);

-- 3. The first admin. Change 'Owner' to your name before running.
--    The result shows your code; your link is
--    https://domestic-gc-analyst.streamlit.app/?u=<access_code>
insert into dashboard_users (display_name, access_code, is_admin)
values ('Owner', md5(random()::text || clock_timestamp()::text), true)
returning display_name, access_code;
