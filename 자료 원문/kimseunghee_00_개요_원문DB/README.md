# kimseunghee_00_개요 원문 DB 패키지

`local 리서치/kimseunghee_00_개요.md`(main, 마지막 수정 커밋 `5f61dc4`)의 주장을 공식 원문과 대조해 Supabase `kb` 스키마에 적재할 수 있게 만든 패키지입니다. 확인일 2026-11-26.

**하지 않은 것:** Supabase 적재·스키마 변경, Storage 업로드, 임베딩·AI API 호출, 에이전트 연결, 한글 검색 테스트 실행(**미실행** — 실제 DB가 없음). SQL은 실행해 보지 않았습니다(001·002는 hyunhee_D 패키지에서 로컬 Postgres로 실행 확인, **003은 새로 만들어 미실행**).

## 폴더 구조

| 위치 | 내용 |
|---|---|
| `README.md` | 이 안내 |
| `docs/데이터사전.md` | **상세 문서** — 결과 요약, 불일치·미확인 목록, 파일별 대상 테이블, 필수값·타입·상태 규칙, 도구 사용 기록 |
| `data/` | 적재용 CSV 12개(`search_tests.csv` 포함) |
| `json/` | MD 고정 양식, 코드값 사전 |
| `originals/` | 보관 원문 11개(공식 10 + 원본 MD 1). 기사 6건은 URL·발췌·SHA-256만 |
| `database/migrations/` | 001 스키마, 002 에이전트 함수·버킷, **003 접근 강화(신규)** |
| `database/load_kb.py` | 적재 스크립트(기본은 사전 점검) |
| `database/validate_package.py` | 오프라인 검증 |
| `database/verify_after_load.sql` | 적재 후 확인 쿼리 |
| `database/run_search_tests.py` | 적재 후 한글 검색 적중률 점검 |
| `tools/build_dataset.py` | CSV·JSON 생성기(ID·판정 고정) |
| `.gitattributes`, `.gitignore` | 원문 SHA-256 보호(줄바꿈 변환 끔). **최상위에 둘 것** |

## 실행 순서

```powershell
python -I database/validate_package.py
```

```powershell
python -I database/load_kb.py
```

1. 위 두 명령으로 오프라인 검증·사전 점검
2. Supabase(테스트 프로젝트 권장)에 `database/migrations/` 001 → 002 → 003 순서로 적용
3. 환경변수 `SUPABASE_DB_URL`(필요 시 `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`) 설정 후 `--check-db` → `--apply`
4. `--upload-originals --verify-storage`로 원문 업로드·SHA 대조
5. `database/verify_after_load.sql` 실행, `python -I database/run_search_tests.py`로 한글 검색 적중률 확인

자세한 내용은 [docs/데이터사전.md](docs/데이터사전.md).
