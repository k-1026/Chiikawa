-- 적재 후 확인용(읽기 전용). service_role/postgres 로 Supabase SQL Editor 나 psql 에서 실행.
-- kb 스키마를 여러 패키지가 함께 쓰므로 건수는 이 패키지(K01) 행만 센다. 기대값은 README 표와 같아야 한다.

-- 1. 표별 건수
select 'source_documents' t, count(*) from kb.source_documents where source_id like 'SRC-K01-%' union all
select 'md_documents', count(*) from kb.md_documents where md_id = 'MD-K01' union all
select 'source_sections', count(*) from kb.source_sections where section_id like 'SEC-K01-%' or section_id like 'BLK-K01-%' union all
select 'knowledge_chunks', count(*) from kb.knowledge_chunks where chunk_id like 'CHK-K01-%' union all
select 'chunk_links', count(*) from kb.chunk_links where from_chunk_id like 'CHK-K01-%' union all
select 'md_claims', count(*) from kb.md_claims where md_id = 'MD-K01' union all
select 'evidence_links', count(*) from kb.evidence_links where md_id = 'MD-K01' union all
select 'domain_figures', count(*) from kb.domain_figures where record_id like 'FIG-K01-%' union all
select 'operating_rules', count(*) from kb.operating_rules where rule_id like 'RULE-K01-%' union all
select 'review_issues', count(*) from kb.review_issues where issue_id like 'ISS-K01-%';

-- 2. 참조 끊김(모두 0이어야 함)
select 'chunk→source' chk, count(*) from kb.knowledge_chunks c left join kb.source_documents s using (source_id) where s.source_id is null
union all select 'chunk→block', count(*) from kb.knowledge_chunks c left join kb.source_sections b on b.section_id = c.source_block_id where b.section_id is null
union all select 'evidence→claim', count(*) from kb.evidence_links e left join kb.md_claims m using (claim_id) where m.claim_id is null
union all select 'evidence→chunk', count(*) from kb.evidence_links e left join kb.knowledge_chunks c using (chunk_id) where e.chunk_id is not null and c.chunk_id is null
union all select 'figure→chunk', count(*) from kb.domain_figures f left join kb.knowledge_chunks c using (chunk_id) where f.chunk_id is not null and c.chunk_id is null
union all select 'claim without evidence', count(*) from kb.md_claims m where not exists (select 1 from kb.evidence_links e where e.claim_id = m.claim_id);

-- 3. 승인 규칙 위반(0이어야 함): 승인 청크는 S/A 원문 보관 + 글자 대조 완료
select count(*) as approved_rule_violations
from kb.knowledge_chunks
where approval_status = 'approved'
  and (source_grade not in ('S','A') or text_check <> 'verified_in_stored_original');

-- 4. 상태별 분포
select approval_status, text_check, count(*) from kb.knowledge_chunks group by 1, 2 order by 1, 2;
select overall_verdict_ko, count(*) from kb.md_claims group by 1 order by 2 desc;

-- 5. 원문 보관 경로(Storage 대조는 load_kb.py --verify-storage)
select source_id, original_file_path, storage_object_path, original_sha256
from kb.source_documents where original_status = 'stored' and source_id like 'SRC-K01-%' order by 1;

-- 6. 에이전트 함수 동작 예시
select chunk_id, source_title, locator, usable_as_fact, score from kb.search_chunks('낙동강', false, 5);
select * from kb.chunk_usability('CHK-K01-KB0715-002');  -- 기사(B) → RULE-001 경고
select * from kb.chunk_context('CHK-K01-NK98-003');        -- 낙동강 경계·서재극 각주 청크가 관계 한 칸(relations)으로 한 번씩 나와야 함

-- 7. 권한(마이그레이션 003): authenticated 는 표 직접 조회가 거부되고 함수만 실행돼야 함
--   Supabase SQL Editor: set role authenticated; select count(*) from kb.knowledge_chunks;  → permission denied 기대
--                        set role authenticated; select count(*) from kb.search_chunks('하소체', false, 5); → 결과 기대
--   확인 뒤 reset role;
