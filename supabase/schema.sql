-- 2027 대구 사투리 축제 안내 페이지 — 스키마
-- 실행 순서: ① 이 파일(schema.sql) → ② seed.sql
-- 여러 번 실행해도 오류가 나지 않아요. 단, 이미 있는 표의 컬럼은 바꾸지 않아요.
--
-- 이 DB에는 공개해도 되는 안내 내용만 담아요.
-- 체크인·투표·숙박 인증처럼 개인이 만드는 데이터는 표를 만들지 않았어요.

-- 축제 ----------------------------------------------------------------------
create table if not exists public.festivals (
  id              text primary key,
  year            integer not null,
  name            text not null,
  theme           text not null,
  tagline         text not null,
  summary         text not null,
  start_date      date not null,
  end_date        date not null,
  venue           text not null,
  hours_note      text not null,
  admission_note  text not null,
  host_name       text,               -- 비어 있으면 '확정 전'
  organizer_name  text,               -- 비어 있으면 '확정 전'
  status          text not null default 'draft' check (status in ('draft', 'published')),
  check (end_date >= start_date)
);

-- 마스코트 --------------------------------------------------------------------
create table if not exists public.mascots (
  id           text primary key,
  festival_id  text not null references public.festivals (id) on delete cascade,
  name         text not null,
  team         text not null check (team in ('local', 'guest')),
  role_label   text not null,
  description  text not null,
  image_path   text not null,
  sort_order   integer not null default 0
);

-- 구역·지도 -------------------------------------------------------------------
create table if not exists public.zones (
  id           text primary key,
  festival_id  text not null references public.festivals (id) on delete cascade,
  name         text not null,
  place_name   text not null,
  icon         text not null,
  open_hours   text not null,
  description  text not null,
  map_x        integer not null,
  map_y        integer not null,
  map_width    integer not null,
  map_height   integer not null,
  sort_order   integer not null default 0
);

create table if not exists public.map_pois (
  id           bigint generated always as identity primary key,
  festival_id  text not null references public.festivals (id) on delete cascade,
  kind         text not null check (kind in ('stage', 'food', 'wc', 'cool', 'med')),
  x            integer not null,
  y            integer not null
);

-- 프로그램·시간표 --------------------------------------------------------------
create table if not exists public.programs (
  id           text primary key,
  festival_id  text not null references public.festivals (id) on delete cascade,
  category     text not null check (category in ('core', 'side')),
  title        text not null,
  description  text not null,
  zone_id      text references public.zones (id) on delete set null,
  sort_order   integer not null default 0
);

create table if not exists public.schedule_items (
  id            bigint generated always as identity primary key,
  festival_id   text not null references public.festivals (id) on delete cascade,
  day           date not null,
  start_time    time not null,
  end_time      time,
  zone_id       text references public.zones (id) on delete set null,   -- 비어 있으면 축제장 전체
  title         text not null,
  kind          text not null check (kind in ('program', 'debate', 'ceremony', 'food', 'market', 'heat', 'close')),
  is_highlight  boolean not null default false,
  sort_order    integer not null default 0,
  check (end_time is null or end_time > start_time)
);
create index if not exists schedule_items_festival_day_idx
  on public.schedule_items (festival_id, day, start_time);

-- 토론 대회 --------------------------------------------------------------------
create table if not exists public.debate_topics (
  id             text primary key,
  festival_id    text not null references public.festivals (id) on delete cascade,
  title          text not null,
  pro_argument   text not null,
  con_argument   text not null,
  difficulty     text not null check (difficulty in ('하', '중', '상')),
  minutes        integer not null check (minutes > 0),
  audience_mode  text not null,
  is_final       boolean not null default false,
  sort_order     integer not null default 0
);

create table if not exists public.debate_teams (
  id            text primary key,
  festival_id   text not null references public.festivals (id) on delete cascade,
  side          text not null check (side in ('local', 'guest')),
  display_name  text not null,
  sort_order    integer not null default 0
);

create table if not exists public.debate_matches (
  id              text primary key,
  festival_id     text not null references public.festivals (id) on delete cascade,
  round           text not null check (round in ('16강', '8강', '4강', '결승')),
  match_no        integer not null check (match_no > 0),
  match_day       date not null,
  team_a_id       text references public.debate_teams (id) on delete set null,   -- 비어 있으면 대진 미정
  team_b_id       text references public.debate_teams (id) on delete set null,
  winner_team_id  text references public.debate_teams (id) on delete set null,
  topic_id        text references public.debate_topics (id) on delete set null,
  unique (festival_id, round, match_no),
  check (team_a_id is null or team_b_id is null or team_a_id <> team_b_id)
);

-- 먹거리·혜택 ------------------------------------------------------------------
create table if not exists public.menu_items (
  id            bigint generated always as identity primary key,
  festival_id   text not null references public.festivals (id) on delete cascade,
  name          text not null,
  order_phrase  text not null,
  sort_order    integer not null default 0,
  unique (festival_id, name)
);

create table if not exists public.benefits (
  id           text primary key,
  festival_id  text not null references public.festivals (id) on delete cascade,
  title        text not null,
  amount_won   integer not null check (amount_won >= 0),
  summary      text not null,
  steps        text[] not null default '{}',
  sort_order   integer not null default 0
);

-- 능력고사·변환기·도우미 --------------------------------------------------------
create table if not exists public.quiz_questions (
  id           text primary key,
  festival_id  text not null references public.festivals (id) on delete cascade,
  prompt_word  text not null,
  question     text not null,
  sort_order   integer not null default 0
);

create table if not exists public.quiz_options (
  id           bigint generated always as identity primary key,
  question_id  text not null references public.quiz_questions (id) on delete cascade,
  label        text not null,
  is_correct   boolean not null default false,
  sort_order   integer not null default 0,
  unique (question_id, sort_order)
);
-- 문제마다 정답은 하나만 허용해요.
create unique index if not exists quiz_options_one_correct_idx
  on public.quiz_options (question_id) where is_correct;

create table if not exists public.quiz_grades (
  id           text primary key,
  festival_id  text not null references public.festivals (id) on delete cascade,
  min_score    integer not null check (min_score >= 0),
  title        text not null,
  message      text not null,
  image_path   text not null,
  unique (festival_id, min_score)
);

create table if not exists public.dialect_rules (
  id              bigint generated always as identity primary key,
  festival_id     text not null references public.festivals (id) on delete cascade,
  standard_terms  text[] not null,
  dialect_text    text not null,
  sort_order      integer not null default 0
);

create table if not exists public.faq_entries (
  id           bigint generated always as identity primary key,
  festival_id  text not null references public.festivals (id) on delete cascade,
  keywords     text[] not null,
  answer       text not null,
  sort_order   integer not null default 0
);

-- 공개 권한 --------------------------------------------------------------------
-- 웹사이트(anon)는 읽기만 할 수 있어요.
-- Supabase는 새 표를 자동으로 공개하지 않으므로 grant가 꼭 필요해요.
-- 표마다 ① 예전 기본 권한 회수 → ② 읽기 권한 → ③ RLS 켜기 → ④ 읽기 정책 순서로 적용해요.
grant usage on schema public to anon, authenticated, service_role;

do $$
declare
  t text;
begin
  foreach t in array array[
    'festivals', 'mascots', 'zones', 'map_pois', 'programs', 'schedule_items',
    'debate_topics', 'debate_teams', 'debate_matches', 'menu_items', 'benefits',
    'quiz_questions', 'quiz_options', 'quiz_grades', 'dialect_rules', 'faq_entries'
  ]
  loop
    execute format('revoke all on public.%I from anon, authenticated', t);
    execute format('grant select on public.%I to anon, authenticated', t);
    execute format('grant select, insert, update, delete on public.%I to service_role', t);
    execute format('alter table public.%I enable row level security', t);
    execute format('drop policy if exists "public read" on public.%I', t);
    execute format('create policy "public read" on public.%I for select to anon, authenticated using (true)', t);
  end loop;
end
$$;
