-- kb 접근 강화(001·002 다음에 실행). 여러 번 실행해도 됨. 데이터 행은 지우지 않는다.
-- 1) 로그인 사용자·에이전트는 표를 직접 읽지 못하고, 아래 함수로만 조회한다.
-- 2) 함수가 승인 상태로 거른다: 기본은 approved 만, 요청하면 reference_only·internal 까지. pending 은 service_role 만.
-- 3) chunk_context 는 같은 청크를 한 번만 돌려주고 관계를 한 칸에 모은다.
-- kb 스키마를 쓰는 모든 패키지(hyunhee_D, kimseunghee 등)에 함께 적용된다.

-- 1. 표 직접 조회 차단 --------------------------------------------------------
revoke select on all tables in schema kb from authenticated, anon;
do $$
declare t text;
begin
  foreach t in array array['source_documents','md_documents','source_sections','knowledge_chunks','chunk_links','md_claims',
                           'evidence_links','domain_figures','domain_places','operating_rules','review_issues','load_runs']
  loop
    execute format('drop policy if exists %I on kb.%I', t || '_read_authenticated', t);
  end loop;
end $$;
-- RLS 는 켜 둔 채(001) 정책이 없으므로 authenticated·anon 은 행이 보이지 않는다. service_role 은 RLS 를 우회한다.

-- 2. 검색 함수: security definer + 승인 필터 ------------------------------------
create or replace function kb.search_chunks(p_query text, p_include_reference boolean default false, p_limit integer default 20)
returns table (
  chunk_id text, source_id text, source_title text, version_label text, locator text, official_url text,
  parent_section_id text, section_title text, related_chunk_ids text, info_type text, short_title text,
  text_original text, search_context text, approval_status text, usable_as_fact boolean, source_grade text,
  score real
)
language sql stable security definer set search_path = kb, extensions, pg_temp as $$
  select a.chunk_id, a.source_id, a.source_title, a.version_label, a.locator, a.official_url,
         a.parent_section_id, a.section_title, a.related_chunk_ids, a.info_type, a.short_title,
         a.text_original, a.search_context, a.approval_status, a.usable_as_fact, a.source_grade,
         greatest(similarity(c.search_text, p_query), word_similarity(p_query, c.search_text)) as score
  from kb.agent_chunks a
  join kb.knowledge_chunks c using (chunk_id)
  where (a.approval_status = 'approved' or (p_include_reference and a.approval_status in ('reference_only','internal')))
    and not exists (select 1 from kb.operating_rules r
                    where r.enforcement = 'block' and a.chunk_id = any (string_to_array(coalesce(r.target_chunk_ids,''), ';')))
    and (c.search_text ilike '%' || p_query || '%' or word_similarity(p_query, c.search_text) > 0.2)
  order by score desc, a.chunk_id
  limit greatest(1, least(p_limit, 100));
$$;

-- 3. 문맥 조회: 중복 제거, pending 제외 ----------------------------------------
drop function if exists kb.chunk_context(text);
create function kb.chunk_context(p_chunk_id text)
returns table (relations text, chunk_id text, parent_section_id text, short_title text, text_original text,
               locator text, approval_status text)
language sql stable security definer set search_path = kb, pg_temp as $$
  with rel as (
    select c.chunk_id, 'self'::text as relation, 0 as ord from kb.knowledge_chunks c where c.chunk_id = p_chunk_id
    union all
    select l.to_chunk_id, l.relation, 1 from kb.chunk_links l where l.from_chunk_id = p_chunk_id
    union all
    select c.chunk_id, 'same_block', 2 from kb.knowledge_chunks c
     where c.source_block_id = (select k.source_block_id from kb.knowledge_chunks k where k.chunk_id = p_chunk_id)
       and c.chunk_id <> p_chunk_id
  )
  select string_agg(distinct r.relation, ',' order by r.relation), c.chunk_id, c.parent_section_id, c.short_title,
         c.text_original, c.locator, c.approval_status
  from rel r join kb.knowledge_chunks c on c.chunk_id = r.chunk_id
  where c.approval_status <> 'pending'
  group by c.chunk_id, c.parent_section_id, c.short_title, c.text_original, c.locator, c.approval_status
  order by min(r.ord), c.chunk_id;
$$;

-- 4. 사용 가능 여부: 본문은 돌려주지 않으므로 pending 청크도 판정만 알려 준다 ----------
alter function kb.chunk_usability(text) security definer;
alter function kb.chunk_usability(text) set search_path = kb, pg_temp;

-- 5. 실행 권한: 로그인 사용자만 --------------------------------------------------
revoke execute on function kb.search_chunks(text, boolean, integer) from public, anon;
revoke execute on function kb.chunk_context(text) from public, anon;
revoke execute on function kb.chunk_usability(text) from public, anon;
grant execute on function kb.search_chunks(text, boolean, integer) to authenticated, service_role;
grant execute on function kb.chunk_context(text) to authenticated, service_role;
grant execute on function kb.chunk_usability(text) to authenticated, service_role;
