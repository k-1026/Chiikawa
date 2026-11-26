-- 에이전트 조회용 뷰·함수와 원문 보관 Storage 버킷.
-- 임베딩·벡터 검색은 이번에 만들지 않는다(가짜 벡터 금지). 검색은 pg_trgm 문자열 유사도로만 한다.
-- 데이터 삭제·초기화 문장 없음.

-- 1. 청크 + 출처 메타데이터 뷰 -------------------------------------------------
create or replace view kb.agent_chunks with (security_invoker = true) as
select
  c.chunk_id, c.source_id, s.title as source_title, s.publisher, s.doc_type, s.source_grade,
  s.version_label, s.published_date, s.accessed_at, s.official_url, s.direct_attachment_url,
  s.original_file_path, s.storage_object_path,
  c.parent_section_id, sec.title as section_title, c.source_block_id, blk.title as block_title,
  c.order_no, c.info_type, c.short_title, c.text_original, c.text_is_excerpt, c.text_format,
  c.search_context, c.applies_to, c.condition_text, c.period_text, c.locator, c.related_chunk_ids,
  c.text_check, c.verification_status, c.approval_status, c.version,
  (c.approval_status = 'approved') as usable_as_fact
from kb.knowledge_chunks c
join kb.source_documents s on s.source_id = c.source_id
join kb.source_sections sec on sec.section_id = c.parent_section_id
join kb.source_sections blk on blk.section_id = c.source_block_id;

grant select on kb.agent_chunks to authenticated;

-- 2. 규칙 기반 사용 가능 여부(벡터 검색 성공 여부와 무관하게 서버에서 판정) -------
create or replace function kb.chunk_usability(p_chunk_id text)
returns table (chunk_id text, usable_as_fact boolean, usable_as_reference boolean, blocking_rules text[], warnings text[])
language sql stable security invoker set search_path = kb, pg_temp as $$
  with c as (select * from kb.knowledge_chunks where knowledge_chunks.chunk_id = p_chunk_id),
  banned as (
    select array_agg(r.rule_id) as ids from kb.operating_rules r, c
    where r.enforcement = 'block' and r.target_chunk_ids is not null
      and c.chunk_id = any (string_to_array(r.target_chunk_ids, ';'))
  )
  select
    c.chunk_id,
    c.approval_status = 'approved' and coalesce(cardinality(banned.ids), 0) = 0,
    c.approval_status in ('approved','reference_only','internal') and coalesce(cardinality(banned.ids), 0) = 0,
    array_remove(
      coalesce(banned.ids, '{}')
      || case when c.approval_status = 'pending' then array['RULE-002'] else '{}' end
      || case when c.text_check = 'reported_by_aside_not_stored' then array['RULE-013'] else '{}' end, null),
    array_remove(
      case when c.source_grade = 'B' then array['RULE-001: 언론 보도 기준 — 확정 사실로 답하지 말 것'] else '{}' end
      || case when exists (select 1 from kb.chunk_links l where l.from_chunk_id = c.chunk_id and l.relation = 'conflicts_with')
              then array['RULE-009: 값이 다른 공식 자료가 있음 — 두 값을 함께 제시'] else '{}' end
      || case when c.info_type in ('figure','condition') and c.source_grade in ('S','A')
              then array['RULE-008: 요금·운영시간 등은 확인일(accessed_at) 기준 — 사용 전 재확인'] else '{}' end, null)
  from c left join banned on true;
$$;

-- 3. 검색: 원문 ID·제목·버전·위치·URL과 계층·관계 정보를 함께 반환 ---------------
create or replace function kb.search_chunks(p_query text, p_include_reference boolean default false, p_limit integer default 20)
returns table (
  chunk_id text, source_id text, source_title text, version_label text, locator text, official_url text,
  parent_section_id text, section_title text, related_chunk_ids text, info_type text, short_title text,
  text_original text, search_context text, approval_status text, usable_as_fact boolean, source_grade text,
  score real
)
language sql stable security invoker set search_path = kb, extensions, pg_temp as $$
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

-- 4. 상위 문맥·연결 청크 함께 조회 -------------------------------------------
create or replace function kb.chunk_context(p_chunk_id text)
returns table (relation text, chunk_id text, short_title text, text_original text, locator text, approval_status text)
language sql stable security invoker set search_path = kb, pg_temp as $$
  select 'self', c.chunk_id, c.short_title, c.text_original, c.locator, c.approval_status
    from kb.knowledge_chunks c where c.chunk_id = p_chunk_id
  union all
  select l.relation, c.chunk_id, c.short_title, c.text_original, c.locator, c.approval_status
    from kb.chunk_links l join kb.knowledge_chunks c on c.chunk_id = l.to_chunk_id
   where l.from_chunk_id = p_chunk_id
  union all
  select 'same_block', c.chunk_id, c.short_title, c.text_original, c.locator, c.approval_status
    from kb.knowledge_chunks c
   where c.source_block_id = (select source_block_id from kb.knowledge_chunks where chunk_id = p_chunk_id)
     and c.chunk_id <> p_chunk_id;
$$;

-- search_chunks 는 security invoker 라 호출자가 pg_trgm 함수(extensions 스키마)를 볼 수 있어야 한다.
-- Supabase 기본 설정에도 있지만, 기본값에 기대지 않도록 명시한다(이미 있으면 아무 변화 없음).
grant usage on schema extensions to authenticated;

grant execute on function kb.chunk_usability(text) to authenticated;
grant execute on function kb.search_chunks(text, boolean, integer) to authenticated;
grant execute on function kb.chunk_context(text) to authenticated;

-- 5. 원문 보관 버킷(비공개). 이미 있으면 그대로 둔다 ---------------------------
insert into storage.buckets (id, name, public)
values ('research-originals', 'research-originals', false)
on conflict (id) do nothing;
