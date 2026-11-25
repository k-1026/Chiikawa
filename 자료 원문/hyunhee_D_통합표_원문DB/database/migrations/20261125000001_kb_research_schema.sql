-- 대구 관광 리서치 원문 DB (hyunhee_D_통합표_조사결과_v2.md) — 스키마
-- 대상: Supabase Postgres. 별도 스키마 kb 를 쓰고 기존 public 표(축제 안내 페이지)는 건드리지 않는다.
-- 여러 번 실행해도 오류가 나지 않는다(create ... if not exists). 기존 표의 컬럼·데이터는 바꾸거나 지우지 않는다.
-- 이 파일은 데이터 삭제·초기화(drop/truncate/delete) 문장을 포함하지 않는다.

create schema if not exists kb;
create extension if not exists pg_trgm with schema extensions;

-- 1. 원문 문서 -------------------------------------------------------------
create table if not exists kb.source_documents (
  source_id             text primary key,
  title                 text not null,
  publisher             text not null,
  doc_type              text not null check (doc_type in ('user_authored','official_web','official_attachment','open_data',
                                                          'statistics','law','press_release','news')),
  source_grade          text not null check (source_grade in ('S','A','B','D','E','U')),
  official_url          text,
  direct_attachment_url text,
  published_date        date,
  published_date_basis  text,
  effective_period      text,
  version_label         text,
  accessed_at           date,
  retrieval_method      text not null,
  original_status       text not null check (original_status in ('stored','url_only_copyright','not_retrieved')),
  original_file_path    text,
  original_sha256       text check (original_sha256 is null or original_sha256 ~ '^[0-9a-f]{64}$'),
  storage_object_path   text,
  approval_status       text not null check (approval_status in ('approved','reference_only','internal','pending')),
  rights_note           text,
  revision_check        text,
  notes                 text,
  loaded_at             timestamptz not null default now(),
  check (original_status <> 'stored' or (original_file_path is not null and original_sha256 is not null))
);

-- 2. MD 문서 ---------------------------------------------------------------
create table if not exists kb.md_documents (
  md_id            text primary key,
  repo_path        text not null,
  git_branch       text not null,
  last_commit_sha  text not null check (last_commit_sha ~ '^[0-9a-f]{40}$'),
  branch_head_sha  text check (branch_head_sha ~ '^[0-9a-f]{40}$'),
  git_blob_sha     text check (git_blob_sha ~ '^[0-9a-f]{40}$'),
  file_sha256      text check (file_sha256 ~ '^[0-9a-f]{64}$'),
  title            text not null,
  written_date     date,
  md_version       text,
  source_id        text references kb.source_documents(source_id),
  notes            text,
  loaded_at        timestamptz not null default now()
);

-- 3. 원문 계층: 문서(document) → 절(section) → 블록(block) ------------------
create table if not exists kb.source_sections (
  section_id         text primary key,
  source_id          text not null references kb.source_documents(source_id),
  parent_section_id  text references kb.source_sections(section_id),
  level              text not null check (level in ('document','section','block')),
  order_no           integer not null,
  title              text not null,
  block_type         text,
  locator            text,
  check ((level = 'document') = (parent_section_id is null))
);
create index if not exists source_sections_source_idx on kb.source_sections(source_id);

-- 4. 최소 의미 청크 ----------------------------------------------------------
create table if not exists kb.knowledge_chunks (
  chunk_id              text primary key,
  source_id             text not null references kb.source_documents(source_id),
  md_id                 text references kb.md_documents(md_id),
  parent_section_id     text not null references kb.source_sections(section_id),
  source_block_id       text not null references kb.source_sections(section_id),
  order_no              integer not null,
  info_type             text not null check (info_type in ('fact','rule','condition','exception','figure','procedure','example')),
  short_title           text not null,
  text_original         text not null check (length(btrim(text_original)) > 0),   -- 원문 그대로(공백만 정리)
  text_is_excerpt       boolean not null,                                         -- 언론 기사 등 짧은 발췌
  text_format           text not null check (text_format in ('text','lines')),   -- lines: 목록형(줄마다 원문 항목)
  search_context        text,     -- 검색 보조 설명(원문 아님)
  summary               text,     -- 요약(원문 아님)
  author_interpretation text,     -- 작성자 해석(원문 아님)
  applies_to            text,
  condition_text        text,
  period_text           text,
  locator               text not null,
  related_chunk_ids     text,     -- 세미콜론 구분. 정규형은 kb.chunk_links
  source_grade          text not null,
  text_check            text not null check (text_check in ('verified_in_stored_original','verified_in_snapshot_not_stored',
                                                            'reported_by_aside_not_stored','not_found_in_original','not_checked')),
  verification_status   text not null check (verification_status in ('verified','aside_reported','unverified')),
  approval_status       text not null check (approval_status in ('approved','reference_only','internal','pending')),
  version               text not null,
  char_count            integer not null,
  search_text           text generated always as (coalesce(short_title,'') || ' ' || text_original || ' ' || coalesce(search_context,'')) stored,
  loaded_at             timestamptz not null default now()
);
create index if not exists knowledge_chunks_source_idx on kb.knowledge_chunks(source_id);
create index if not exists knowledge_chunks_parent_idx on kb.knowledge_chunks(parent_section_id);
create index if not exists knowledge_chunks_trgm_idx on kb.knowledge_chunks using gin (search_text extensions.gin_trgm_ops);

create table if not exists kb.chunk_links (
  link_id        text primary key,
  from_chunk_id  text not null references kb.knowledge_chunks(chunk_id),
  to_chunk_id    text not null references kb.knowledge_chunks(chunk_id),
  relation       text not null check (relation in ('must_read_with','conflicts_with','exception_of','rule_about')),
  unique (from_chunk_id, to_chunk_id, relation)
);

-- 5. MD 주장과 근거 ---------------------------------------------------------
create table if not exists kb.md_claims (
  claim_id            text primary key,
  md_id               text not null references kb.md_documents(md_id),
  md_section          text not null,
  row_key             text not null,
  claim_type          text not null check (claim_type in ('fact','figure','rule','quote','proposal','status')),
  is_external         boolean not null,
  claim_text          text not null,
  md_stated_grade     text,
  md_stated_source    text,
  overall_verdict     text not null,
  overall_verdict_ko  text not null,
  evidence_count      integer not null
);

create table if not exists kb.evidence_links (
  link_id                text primary key,
  claim_id               text not null references kb.md_claims(claim_id),
  md_id                  text not null references kb.md_documents(md_id),
  md_path                text not null,
  md_commit_sha          text not null,
  md_section             text,
  md_row_key             text,
  claim_text             text,
  source_id              text not null references kb.source_documents(source_id),
  chunk_id               text references kb.knowledge_chunks(chunk_id),
  source_title           text,
  publisher              text,
  official_url           text,
  direct_attachment_url  text,
  published_date         date,
  effective_period       text,
  accessed_at            date,
  original_file_path     text,
  original_sha256        text,
  locator                text,
  excerpt                text,
  source_relation        text not null check (source_relation in ('original_confirmed','alternative_official','user_authored','unverifiable')),
  source_relation_ko     text not null,
  verdict                text not null check (verdict in ('match','faithful_summary','interpretation','overgeneralization',
                                                          'scope_mismatch','mismatch','unverifiable')),
  verdict_ko             text not null,
  review_note            text
);
create index if not exists evidence_links_claim_idx on kb.evidence_links(claim_id);

-- 6. 업무용 정형 데이터 ------------------------------------------------------
create table if not exists kb.domain_figures (
  record_id       text primary key,
  domain          text not null check (domain in ('statistic','budget','program','operation','price','spec')),
  subject         text not null,
  metric          text not null,
  value_numeric   numeric,              -- 어림값('약', '여')·원문 미확인은 NULL
  value_text      text,                 -- 원문 표기 그대로
  unit            text,
  currency        text,
  vat_basis       text,                 -- not_stated: 원문에 부가세 표기 없음
  quantity_basis  text,
  base_year       integer,
  period_start    date,
  period_end      date,
  value_status    text not null check (value_status in ('reported','not_available','unconfirmed','not_applicable','actual_zero')),
  source_id       text references kb.source_documents(source_id),
  chunk_id        text references kb.knowledge_chunks(chunk_id),
  claim_id        text references kb.md_claims(claim_id),
  approval_status text not null check (approval_status in ('approved','reference_only','internal','pending')),
  note            text,
  check (value_status <> 'actual_zero' or value_numeric = 0),
  check (value_status not in ('unconfirmed','not_available') or value_numeric is null)
);

create table if not exists kb.domain_places (
  place_id        text primary key,
  list_name       text not null,
  list_order      integer not null,
  name            text not null,
  place_kind      text not null,
  district        text,
  source_id       text not null references kb.source_documents(source_id),
  chunk_id        text not null references kb.knowledge_chunks(chunk_id),
  approval_status text not null,
  note            text
);

-- 7. 운영 규칙(벡터 검색과 별개로 서버에서 강제) ------------------------------
create table if not exists kb.operating_rules (
  rule_id          text primary key,
  rule_scope       text not null,
  rule_text        text not null,
  enforcement      text not null check (enforcement in ('block','block_as_fact','warn')),
  condition_text   text,
  rule_source_id   text references kb.source_documents(source_id),
  rule_chunk_id    text references kb.knowledge_chunks(chunk_id),
  target_chunk_ids text,
  approval_status  text not null
);

create table if not exists kb.review_issues (
  issue_id     text primary key,
  issue_type   text not null,
  claim_ids    text,
  source_ids   text,
  description  text not null,
  next_action  text
);

-- 8. 적재 기록 -------------------------------------------------------------
create table if not exists kb.load_runs (
  run_id        uuid primary key default gen_random_uuid(),
  started_at    timestamptz not null default now(),
  finished_at   timestamptz,
  package_name  text not null,
  mode          text not null,
  counts_before jsonb,
  counts_after  jsonb,
  error_rows    integer,
  note          text
);

-- 9. 권한: 로그인 사용자 읽기 전용. 쓰기는 service_role(적재 스크립트)만 ----------
do $$
declare t text;
begin
  foreach t in array array['source_documents','md_documents','source_sections','knowledge_chunks','chunk_links','md_claims',
                           'evidence_links','domain_figures','domain_places','operating_rules','review_issues','load_runs']
  loop
    execute format('alter table kb.%I enable row level security', t);
    if not exists (select 1 from pg_policies where schemaname = 'kb' and tablename = t and policyname = t || '_read_authenticated') then
      execute format('create policy %I on kb.%I for select to authenticated using (true)', t || '_read_authenticated', t);
    end if;
  end loop;
end $$;

grant usage on schema kb to authenticated, service_role;
grant select on all tables in schema kb to authenticated;
grant all on all tables in schema kb to service_role;
