# hyunhee_D_통합표 원문 DB 패키지

`local 리서치/hyunhee_D_통합표_조사결과_v2.md`(main, 마지막 수정 커밋 `5f61dc4`)에 적힌 외부 사실·수치·규칙을 원문과 대조하고,
Supabase에 적재할 수 있는 CSV·JSON·원문 파일·SQL·적재 코드로 만든 패키지입니다.

- 확인일: **2026-11-25**
- **하지 않은 것**: Supabase 실제 적재·스키마 변경, Storage 업로드, 사이트 배포, 임베딩·AI API 호출, 에이전트 검색 연결.
  SQL은 이 컴퓨터에 Postgres가 없어 **실행해 보지 않았습니다.** 적재 스크립트는 사전 점검(dry-run)까지만 실행했습니다.
- 가짜 벡터·가짜 AI 답변은 넣지 않았습니다. 검색 함수는 `pg_trgm` 문자열 유사도만 씁니다.

---

## 1. 결과 요약

| 항목 | 수 |
|---|---|
| 원문(source_documents) | 58건 — 공식·통계·법령·보도자료 승인 31, 언론 참고 22, 원문 미확보 4, 사용자 작성 원본 1 |
| 원문 파일 보관(originals/) | 32개(공식 31 + 원본 MD 1). 언론 기사 22건은 저작권 때문에 URL·짧은 발췌·스냅숏 SHA-256만 기록 |
| MD 주장(md_claims) | 113건(외부 사실 110, 작성자 제안 3) |
| 근거 연결(evidence_links) | 175건 — 원래 출처 확인 142, 원래 출처 불명확·대체 근거 28, 사용자 작성 원본 3, 원문 확인 불가 2 |
| 원문 청크(knowledge_chunks) | 180건 — 보관 원문 글자 대조 103, 기사 스냅숏 대조 73, Aside 보고만 4 |
| 승인 상태(청크) | approved 91 / reference_only 73 / internal 12 / pending 4 |
| 원문 계층(source_sections) | 233행(문서 58 → 절 → 블록) |
| 청크 관계(chunk_links) | 115건 |
| 정형 데이터 | domain_figures 103행, domain_places 97행 |
| 운영 규칙 / 검토 목록 | 13건 / 23건 |

### 주장별 대조 결과(대표 판정)

| 판정 | 건수 |
|---|---|
| 일치 | 92 |
| 의미를 유지한 요약 | 12 |
| 불일치 | 4 |
| 과도한 일반화 | 1 |
| 적용 범위 다름 | 1 |
| 해석·제안 | 2 |
| 확인 불가 | 1 |

대표 판정은 원래 출처 근거가 있으면 그 안에서 가장 나쁜 판정, 없으면 대체 공식 근거, 그다음 사용자 작성 원본 순으로 고릅니다.
근거별 판정은 `evidence_links.csv`에 따로 있습니다.

### 불일치·과도한 일반화·적용 범위 다름(MD 수정 검토 대상)

| 주장 | MD 내용 | 원문 확인 결과 |
|---|---|---|
| CLM-D2-23-06 | 시티투어 야경·체험코스 '준비중' | 확인일에 야경 투어 페이지에 동절기 금·토 운행·코스가 있음(작성 후 바뀌었을 수 있음) |
| CLM-D2-27-01 | 북구 스탬프투어 6곳 이상 방문 시 2만 원 상품권 | 원문은 **매월 50명 추첨** — 조건 누락 |
| CLM-D2-27-03 | 북구 테마여행 코스 7개 | 본문 코스 카드 7개와는 일치, 왼쪽 하위메뉴는 8개 — 어느 기준인지 표시 필요(적용 범위 다름) |
| CLM-D2-28-01 | 2024-07 달성군 관광박람회 수상(파크골프 투어상품) | 2024-07 수상은 워케이션 중심, 파크골프 언급 없음 |
| CLM-D2-31-02 | 수상공연장 일정 2026-06→2027→2028 | 원문은 '2026년 말 완공 계획' → 2027 → 2028년 2월. '2026-06' 없음 |
| CLM-D2-S6-01 | 대표 관광명소 45곳 | 확인일 44곳(메뉴명에는 '30선'도 쓰임) |

### 확인 불가

| 주장 | 이유 |
|---|---|
| CLM-D2-41-01 | 한국관광 데이터랩 원자료 미열람(MD도 별도 진행으로 남김) |

동화사 템플스테이 요금(어른 5만/어린이 3만)은 처음엔 근거를 못 찾았으나, Aside 재실행으로 대구관광안내 팔공산힐링 페이지에 있다는 것을 알아내 보관 원문에서 대조했습니다(일치). 다만 templestay.com 현행 요금(휴식형 성인 80,000원 등, Aside 보고)과 달라 옛 요금일 수 있습니다(ISS-012).

### 원문 미확보·보류(승인 데이터에서 제외)

| 원문 | 상태 |
|---|---|
| SRC-JUNG-GOLMOK 중구 골목투어 | 사이트가 자동 접속 확인을 요구해 curl·내장 브라우저로 못 열었고, **Aside로만 열람**. 거리·시간은 MD와 일치하지만 원문을 보관하지 못해 4개 청크 `pending` |
| SRC-TOUR-GUIDEBOOK 음식점가이드북 | 파일 미열람(링크 존재만 확인). 스캔 PDF라면 OCR 검수 필요 |
| SRC-DATALAB 한국관광 데이터랩 | 미열람 |
| SRC-TEMPLESTAY templestay.com 현행 요금 | Aside 보고만 있고 원문 미보관 |
| 남구 관광명소 CSV 파일 자체 | 포털 소개 페이지(메타데이터)만 보관. 파일은 브라우저 다운로드가 필요해 미확보 |
| KOSIS 입장객 통계 파일 | 파일 존재·갱신일만 확인. 대구 행 값은 미확인 |

**OCR**: 이번 패키지에는 OCR한 스캔 문서가 없습니다(미검수 OCR 데이터 0건).

공식 자료끼리 또는 공식 자료와 기사가 다른 값도 있습니다.
- 시티투어 운행 끝 시각: 시간표 페이지 17:50 / 이용 안내 페이지 17:30(ISS-001)
- 앞산 케이블카 요금: 남구 상세 페이지 10,500원 / 남구 첫 화면 9,500원(ISS-021)
- 수성못 수상공연장 규모: 경북매일 '2000석 규모' / 대구시 보도자료 '메인 객석 1,000석'(ISS-023)
- 골목상권 가을축제: 9월 발표 '10월 12일부터' → 10월 8일 대구시 보도자료 '10월 15일부터 11월 말까지'(ISS-006)
전체 검토 목록은 `review_issues.csv`.

---

## 2. 도구 사용 기록

| 도구 | 한 일 |
|---|---|
| Claude Code (git) | main 브랜치 MD·Git 이력 확인, 원본 MD 보관 |
| Claude Code (curl) | 공식 페이지·기사 HTML을 직접 받아 SHA-256 기록, 청크 본문을 원문에서 글자 대조 |
| 웹 검색 | 기사 후보 URL 찾기(검색 요약은 출처 확정에 쓰지 않음 — 원문을 직접 받아 대조) |
| 앱 내장 브라우저 | 중구청 페이지 열기 시도 → 빈 화면, 실패 |
| Aside | 총 5건 실행(모두 완료). 처음 3건은 'claude-code' 모델 공급자 인증이 끊겨 실패했고, 인증 복구 후 **같은 프롬프트로 3건 재실행**: 기사 A묶음 6건 모두 기존 대조와 일치 / 기사 B묶음 9건 일치, 대구시 보도자료 3건(10미데이·가을축제 일정 변경·수성못 합의서) 추가 발견 / 공식 자료 8건 — 템플스테이 요금 위치, 북구 본문 카드 7개, 케이블카 요금 9,500원 표기 추가 발견. 추가 2건은 법령·중구 골목투어·KOSIS·연간축제일정·야시장 공지·대구시 메뉴 확인과 MD 원 기사 4건(경북매일 2026-09-11, 중도일보 2026-05-28, 매일신문 2026-06-29, 뉴스서울 2024)·보도자료 3건 발견. **Aside가 찾은 페이지는 중구청·templestay.com·관광지식정보시스템을 빼고 모두 curl로 다시 받아 직접 대조** |

---

## 3. 폴더 구조와 대상 테이블

| 파일 | 대상 테이블 | 기본키 | 내용 |
|---|---|---|---|
| `source_documents.csv` | `kb.source_documents` | source_id | 원문 메타데이터·출처·보관 파일·해시·승인 상태 |
| `md_documents.csv` | `kb.md_documents` | md_id | 대상 MD(경로·커밋 SHA·blob SHA·파일 SHA-256) |
| `source_sections.csv` | `kb.source_sections` | section_id | 원문 계층: document → section → block |
| `knowledge_chunks.csv` | `kb.knowledge_chunks` | chunk_id | 최소 의미 청크(원문 그대로·검색 보조 설명·조건·기간·위치·검증 상태) |
| `chunk_links.csv` | `kb.chunk_links` | link_id | 함께 읽을 청크·충돌·예외 관계 |
| `md_claims.csv` | `kb.md_claims` | claim_id | MD에서 뽑은 주장과 대표 판정 |
| `evidence_links.csv` | `kb.evidence_links` | link_id | 주장 ↔ 원문 근거(발췌·위치·출처 관계·판정·메모) |
| `domain_figures.csv` | `kb.domain_figures` | record_id | 예산·통계·요금·규격·프로그램 수치 |
| `domain_places.csv` | `kb.domain_places` | place_id | 10미·12경·대표 관광명소·시티투어 정류장 등 목록 |
| `operating_rules.csv` | `kb.operating_rules` | rule_id | 서버에서 강제할 운영 규칙 |
| `review_issues.csv` | `kb.review_issues` | issue_id | 불일치·미확인·충돌 검토 목록 |
| `json/md_template_hyunhee_D_v2.json` | — | — | MD 고정 양식(절 구성·통합표 열 정의). 값은 넣지 않음 |
| `json/code_lists.json` | — | — | 코드값 사전(등급·판정·승인·값 상태·청크 유형 등) |
| `originals/` | Storage `research-originals/hyunhee_D_v2/` | — | 보관 원문 28개(파일명 = source_id) |
| `database/migrations/*.sql` | — | — | 스키마·권한(001), 에이전트 뷰·함수·Storage 버킷(002) |
| `database/load_kb.py` | — | — | 적재 스크립트 |
| `database/validate_package.py` | — | — | 오프라인 검증 |
| `database/verify_after_load.sql` | — | — | 적재 후 확인 쿼리 |
| `tools/build_dataset.py` | — | — | 이 패키지의 CSV·JSON 생성기(ID·판정은 이 파일에 고정) |

**CSV 11개와 이 README는 `잡다한거/` 폴더에 있습니다**(위 표의 CSV 파일명은 모두 `잡다한거/` 아래). 스크립트는 이 위치를 읽고 씁니다. `.gitattributes`·`.gitignore`는 패키지 최상위에 있어야 합니다(원문 SHA-256 보호).

CSV는 모두 UTF-8(BOM 없음), 영문 소문자 컬럼명, 한 행 한 레코드입니다. 목록형 청크는 `text_original` 안에 줄바꿈이 있습니다(`text_format = lines`, CSV 따옴표 처리됨).

---

## 4. 데이터 규칙

### ID
- 모든 ID는 `tools/build_dataset.py`에 고정 — 다시 생성해도 같은 ID가 나옵니다(재생성 결과 바이트 단위 동일 확인).
- 형식: `SRC-…`(원문), `SEC-…-NN`(절), `BLK-…-NN-NN`(블록), `CHK-…`(청크), `CLM-D2-<행>-<번호>`(주장), `EVL-…`(근거 연결), `FIG-…`, `PLC-…`, `RULE-…`, `ISS-…`.

### 원문 본문과 보조 정보 구분(knowledge_chunks)
- `text_original`: 원문 글자 그대로. 공백·줄바꿈만 정리했습니다. 원문의 오탈자(예: `달성군는`, `관게망`, 야시장 공지의 `2025. 3. 27.`)도 그대로 둡니다.
- `search_context`: 검색을 돕는 설명. **원문 인용이 아닙니다.**
- `summary`, `author_interpretation`: 이번엔 비워 둠(원문·해석 분리용 자리).
- `text_is_excerpt = true`: 언론 기사 짧은 발췌(문장 1개 수준, 200자 이하).
- `text_check`: `verified_in_stored_original`(originals/ 원문에서 대조) / `verified_in_snapshot_not_stored`(기사 스냅숏에서 대조, 스냅숏 미보관) / `reported_by_aside_not_stored`(Aside 인용값, 원문 미보관) / `not_found_in_original` / `not_checked`.

### 승인 상태(approval_status)
| 값 | 뜻 | 에이전트 사용 |
|---|---|---|
| approved | 공식·통계(S/A) 원문을 보관하고 글자 대조 완료 | 확정 근거로 사용 가능 |
| reference_only | 언론 보도(B) | 참고만. 확정 사실로 답하지 않음 |
| internal | 팀 내부 원본 MD | 조사 규칙의 근거 |
| pending | 원문 미보관·미대조 | 사용 금지 |

### 값 상태(domain_figures.value_status)
`reported`(원문 값) / `not_available`(자료에 그 값이 없음, 예: 시티투어 이용객 수) / `unconfirmed`(원문을 못 봐 확인 못 함) / `not_applicable` / `actual_zero`(실제 0, 예: 대구시민의 날 무료).
- '약 130개', '5천여 개' 같은 어림값은 `value_numeric`을 비우고 `value_text`에만 원문 표기를 둡니다.
- 금액은 `currency = KRW`, 원 단위 숫자. 부가세 표기가 없으면 `vat_basis = not_stated`.
- 원문에 없는 시작·종료일은 채우지 않습니다(예: 동성로 사업 기사 문장에 시작 연도 없음 → 비움).

### NULL
CSV의 빈 칸은 적재 시 NULL입니다. 필수 컬럼은 SQL의 `not null`과 같습니다.

### 버전
`knowledge_chunks.version = v1`. 원문이 바뀌면 새 원문 파일·SHA로 행을 갱신하고 버전을 올립니다. 이전 판 보존이 필요하면 source_id에 접미사를 붙여 새 원문으로 추가하세요(기존 행은 지우지 않음).

---

## 5. 실행 방법

비밀값은 환경변수로만 넣습니다. 파일에 적지 마세요.

```powershell
$env:SUPABASE_DB_URL = "<postgres 연결 문자열>"
$env:SUPABASE_URL = "https://<project>.supabase.co"
$env:SUPABASE_SERVICE_ROLE_KEY = "<service role key>"
```

순서:

1. 오프라인 검증

```powershell
python -I database/validate_package.py
```

2. 적재 사전 점검(DB 연결 없음)

```powershell
python -I database/load_kb.py
```

3. 마이그레이션 적용 — Supabase SQL Editor 또는 `supabase db push`로 `database/migrations/` 두 파일을 순서대로 실행

4. DB 건수만 확인(쓰기 없음) — 이후 단계는 `pip install "psycopg[binary]"` 필요

```powershell
python -I database/load_kb.py --check-db
```

5. 적재

```powershell
python -I database/load_kb.py --apply
```

6. 원문 Storage 업로드와 대조

```powershell
python -I database/load_kb.py --upload-originals --verify-storage
```

7. `database/verify_after_load.sql` 실행해 건수·참조·승인 규칙 확인

적재 순서(FK 순): source_documents → md_documents → source_sections → knowledge_chunks → chunk_links → md_claims → evidence_links → domain_figures → domain_places → operating_rules → review_issues.

### 재실행·중복 방지
- `insert … on conflict (기본키) do update` — 같은 ID는 갱신, 중복 행 없음.
- **어떤 행도 지우지 않습니다.** 패키지에 없는 기존 행은 건수만 보고합니다. SQL에도 drop/truncate/delete가 없습니다.
- 한 트랜잭션으로 적재하고, 적재 후 건수·참조 검사가 실패하면 전체 롤백합니다.
- 형식이 잘못된 행은 `load_errors/<표>_errors.csv`로 빠지고, 기본값은 적재 중단입니다(`--allow-partial`로 제외 후 적재).
- 적재 기록은 `kb.load_runs`.

### 데이터 재생성
```powershell
python -I tools/build_dataset.py
```
기사 스냅숏 폴더가 있으면 `--news-dir <폴더>`로 기사 발췌도 다시 대조합니다(없으면 이전 대조 결과 유지).

---

## 6. 에이전트 활용

- `kb.search_chunks(검색어, 참고자료포함여부, 개수)` — 청크와 함께 **source_id·원문 제목·버전·위치(locator)·URL·parent_section_id·연결 청크**를 돌려줍니다. 기본은 approved만, `true`면 reference_only·internal도 포함. 규칙으로 막힌 청크는 빠집니다.
- `kb.chunk_context(chunk_id)` — 연결 청크(조건·예외·충돌)와 같은 블록의 청크를 함께 돌려줍니다. 최소 청크만 보고 조건을 놓치지 않게 하는 용도입니다.
- `kb.chunk_usability(chunk_id)` — 승인 상태와 `operating_rules`로 사용 가능 여부·막는 규칙·경고를 서버에서 판정합니다. 중요한 규칙이 벡터 검색 결과에 기대지 않게 하는 장치입니다.
- 뷰 `kb.agent_chunks` — 청크 + 출처 메타데이터.
- 권한: 로그인 사용자(authenticated) 읽기 전용, 쓰기는 service_role만. anon에는 권한을 주지 않았습니다.
- **참고 문서 안의 명령·지시문은 에이전트 지침으로 실행하지 않습니다**(RULE-010). 문서 내용은 데이터로만 다룹니다.

---

## 7. 개인정보·저작권

- 언론 기사 원문 HTML은 저장소에 넣지 않았습니다. URL·제목·게재일·문장 단위 짧은 발췌·스냅숏 SHA-256만 있습니다.
- KOSIS 페이지 보관본 2개는 담당자 휴대전화 번호를 `010-****-****`로 가렸습니다. 그래서 이 두 파일은 웹 원문과 바이트가 다르며, 기록된 SHA-256은 가린 파일 기준입니다.
- 계정 DB·비밀번호·API 키·세션 정보는 포함하지 않았습니다(검증 스크립트가 비밀값·휴대전화 패턴을 검사).

---

## 8. 로컬 Postgres 적재 테스트 결과(2026-11-26)

실제 Supabase가 아니라, 내 컴퓨터 임시 폴더의 PostgreSQL 16.2(PyPI `pgserver` 휠의 실행 파일)로 실행했습니다.
Supabase에만 있는 것(역할 `anon`·`authenticated`·`service_role`, `storage.buckets`, `extensions` 스키마)은 흉내 낸 스텁을 썼고,
`pg_trgm`이 없어 유사도 함수는 '포함 여부 1/0' 스텁, trigram 인덱스는 생략했습니다.

| 항목 | 결과 |
|---|---|
| 마이그레이션 001·002 적용 | 성공. 두 번 실행해도 오류 없음 |
| `load_kb.py --check-db` / `--apply` | 성공. 11개 표 1,111행 적재 |
| `--apply` 재실행 | 성공. 건수 그대로(중복 없음) |
| `verify_after_load.sql` | 참조 끊김 0, 근거 없는 주장 0, 승인 규칙 위반 0 |
| CSV ↔ DB 값 왕복 비교 | 11개 표 전 칸 불일치 0(한글·줄바꿈·큰 금액 정밀도 포함) |
| 권한 | authenticated 읽기만 가능(쓰기·삭제 거부), anon 거부, service_role 쓰기 가능 |
| DB 제약 | 잘못된 허용값·없는 FK 입력은 DB가 거부 |
| 에이전트 함수 | RULE-003 차단, RULE-009 충돌 경고, 조건 청크 함께 반환 확인 |

테스트 중 고친 것: 로그인 사용자가 `search_chunks`를 부르면 `extensions` 스키마 권한이 없어 실패 → 002에 `grant usage on schema extensions to authenticated` 추가(Supabase 기본값에도 있으나 명시).

**실제 Supabase에서 아직 확인하지 않은 것**: `pg_trgm` 실제 확장·trigram 인덱스·유사도 점수, `storage.buckets` 실제 표, Storage 업로드·대조(`--upload-originals --verify-storage`).

## 9. 남은 단계(별도 완료 보고 필요)

1. Supabase에 마이그레이션 적용 → `--apply` 적재 → Storage 업로드·대조 → `verify_after_load.sql` 확인
2. 임베딩 생성과 벡터 검색 연결(이번엔 하지 않음)
3. 에이전트에서 `search_chunks`·`chunk_usability` 연결
4. `review_issues.csv`의 MD 수정 항목 팀 검토
