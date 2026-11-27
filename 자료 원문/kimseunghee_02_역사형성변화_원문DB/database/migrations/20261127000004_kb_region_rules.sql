-- kb 규칙·지역·최신성 보강(001~003 다음). 여러 번 실행해도 됨. 데이터 행은 지우지 않는다.
-- 1) 청크에 region(원문이 다루는 지역) 컬럼 추가
-- 2) 운영 규칙이 대상을 '조건'(컬럼·연산자·값) 또는 대상 청크 목록으로 고르게 함
-- 3) chunk_usability·search_chunks 가 규칙 ID를 코드에 두지 않고 규칙 표를 읽어 적용
-- 4) 주장에 stale(기준 MD가 바뀌어 다시 판정해야 함) 표시

alter table kb.knowledge_chunks add column if not exists region text;
alter table kb.md_claims add column if not exists stale boolean not null default false;

alter table kb.operating_rules add column if not exists match_column text;
alter table kb.operating_rules add column if not exists match_operator text;
alter table kb.operating_rules add column if not exists match_value text;
alter table kb.operating_rules add column if not exists warning_text text;
do $$ begin
  if not exists (select 1 from pg_constraint where conname = 'operating_rules_match_chk') then
    alter table kb.operating_rules add constraint operating_rules_match_chk check (
      (match_column is null and match_operator is null and match_value is null)
      or (match_column in ('region','source_grade','approval_status','info_type','text_check','source_id')
          and match_operator in ('=','<>') and match_value is not null));
  end if;
end $$;

-- 규칙이 청크에 걸리는지(조건 또는 대상 목록). 규칙 ID 는 코드에 없다.
create or replace function kb.rule_matches(r kb.operating_rules, c kb.knowledge_chunks)
returns boolean language sql immutable as $$
  select
    (r.target_chunk_ids is not null and c.chunk_id = any (string_to_array(r.target_chunk_ids, ';')))
    or (r.match_column is not null and (
         case r.match_column
           when 'region'          then coalesce(c.region, '')
           when 'source_grade'    then c.source_grade
           when 'approval_status' then c.approval_status
           when 'info_type'       then c.info_type
           when 'text_check'      then c.text_check
           when 'source_id'       then c.source_id
         end
         is not null
         and case r.match_operator
               when '=' then (case r.match_column
                                when 'region' then coalesce(c.region, '') when 'source_grade' then c.source_grade
                                when 'approval_status' then c.approval_status when 'info_type' then c.info_type
                                when 'text_check' then c.text_check when 'source_id' then c.source_id end) = r.match_value
               when '<>' then (case r.match_column
                                when 'region' then coalesce(c.region, '') when 'source_grade' then c.source_grade
                                when 'approval_status' then c.approval_status when 'info_type' then c.info_type
                                when 'text_check' then c.text_check when 'source_id' then c.source_id end) <> r.match_value
             end));
$$;

-- 사용 가능 여부: 승인 상태 + 규칙 표(차단·경고)를 그대로 적용
create or replace function kb.chunk_usability(p_chunk_id text)
returns table (chunk_id text, usable_as_fact boolean, usable_as_reference boolean, blocking_rules text[], warnings text[])
language sql stable security definer set search_path = kb, pg_temp as $$
  with c as (select * from kb.knowledge_chunks k where k.chunk_id = p_chunk_id),
  hit as (
    select r.rule_id, r.enforcement, coalesce(r.warning_text, r.rule_text) as msg
    from kb.operating_rules r, c where kb.rule_matches(r, c)
  )
  select c.chunk_id,
         c.approval_status = 'approved' and not exists (select 1 from hit where enforcement in ('block','block_as_fact')),
         c.approval_status in ('approved','reference_only','internal') and not exists (select 1 from hit where enforcement = 'block'),
         coalesce((select array_agg(rule_id order by rule_id) from hit where enforcement in ('block','block_as_fact')), '{}'),
         coalesce((select array_agg(rule_id || ': ' || msg order by rule_id) from hit where enforcement = 'warn'), '{}')
  from c;
$$;

-- 검색: 승인 상태 필터 + 'block' 규칙에 걸린 청크 제외 + 경고 규칙은 결과에 함께 표시. 같은 청크는 한 번만.
drop function if exists kb.search_chunks(text, boolean, integer);
create function kb.search_chunks(p_query text, p_include_reference boolean default false, p_limit integer default 20)
returns table (
  chunk_id text, source_id text, source_title text, version_label text, locator text, official_url text,
  parent_section_id text, section_title text, related_chunk_ids text, info_type text, short_title text,
  text_original text, search_context text, region text, approval_status text, usable_as_fact boolean,
  source_grade text, warnings text[], score real
)
language sql stable security definer set search_path = kb, extensions, pg_temp as $$
  select a.chunk_id, a.source_id, a.source_title, a.version_label, a.locator, a.official_url,
         a.parent_section_id, a.section_title, a.related_chunk_ids, a.info_type, a.short_title,
         a.text_original, a.search_context, c.region, a.approval_status,
         a.approval_status = 'approved' and not exists (select 1 from kb.operating_rules r
             where r.enforcement = 'block_as_fact' and kb.rule_matches(r, c)),
         a.source_grade,
         coalesce((select array_agg(r.rule_id || ': ' || coalesce(r.warning_text, r.rule_text) order by r.rule_id)
                   from kb.operating_rules r where r.enforcement in ('warn','block_as_fact') and kb.rule_matches(r, c)), '{}'),
         greatest(similarity(c.search_text, p_query), word_similarity(p_query, c.search_text)) as score
  from kb.agent_chunks a
  join kb.knowledge_chunks c using (chunk_id)
  where (a.approval_status = 'approved' or (p_include_reference and a.approval_status in ('reference_only','internal')))
    and not exists (select 1 from kb.operating_rules r where r.enforcement = 'block' and kb.rule_matches(r, c))
    and (c.search_text ilike '%' || p_query || '%' or word_similarity(p_query, c.search_text) > 0.2)
  order by score desc, a.chunk_id
  limit greatest(1, least(p_limit, 100));
$$;

revoke execute on function kb.search_chunks(text, boolean, integer) from public, anon;
revoke execute on function kb.chunk_usability(text) from public, anon;
grant execute on function kb.search_chunks(text, boolean, integer) to authenticated, service_role;
grant execute on function kb.chunk_usability(text) to authenticated, service_role;

-- 에이전트 표(daesatu.knowledge_chunks)로 옮길 때 쓰는 내보내기 뷰(임베딩 없음 — 적재 후 앱의 임베딩 단계 필요)
create or replace view kb.v_daesatu_export with (security_invoker = true) as
select 'kb:' || c.chunk_id as id,
       'kb/' || coalesce(c.region, '지역 미상') || '/' || s.source_id as source,
       s.title as file,
       c.short_title as heading,
       c.order_no as seq,
       c.text_original || E'\n[출처] ' || s.title || ' / ' || s.publisher
         || coalesce(' / ' || s.official_url, '') || ' / ' || c.locator as text
from kb.knowledge_chunks c join kb.source_documents s using (source_id)
where c.approval_status = 'approved';
revoke all on kb.v_daesatu_export from public, anon, authenticated;
grant select on kb.v_daesatu_export to service_role;
