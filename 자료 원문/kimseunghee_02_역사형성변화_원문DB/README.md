# kimseunghee_02_역사형성변화 원문 DB 패키지

`local 리서치/kimseunghee_02_역사형성변화.md`(main 기준 `a7043e7`, blob `caea051`)의 주장을 공식 원문과 대조해 Supabase `kb` 스키마에 넣고 에이전트가 검색할 수 있게 만든 패키지입니다. 확인일 2026-11-27. 마무리 직전 main(`3e96ab7`)에서 MD가 바뀌지 않은 것을 다시 확인했습니다.

## 완료 단계

| 단계 | 상태 |
|---|---|
| ① 패키지 생성 | 완료 |
| ② 오프라인 검증 | 완료(오류 0, 경고 1 — 청크 없는 연혁 원문) |
| ③ 테스트 DB 적재 | **미실행**(DB 없음) |
| ④ 검색 적중률 | **미실행**(오프라인 점검만: 기대 청크 17/17 존재) |
| ⑤ 에이전트 연결 | **미실행** — 앱 코드 변경 제안만 작성(docs 8절) |

## 폴더 구조

| 위치 | 내용 |
|---|---|
| `docs/데이터사전.md` | **상세 문서** — 결과·지표, 시리즈 대상 목록, 불일치·미확인, 규칙, 에이전트 연결 제안, 데이터 사전 |
| `data/` | 적재 CSV 11개 + `rule_tests.csv`, `search_tests.csv` |
| `json/` | MD 고정 양식, 코드값 |
| `originals/` | 보관 원문 10개(국어기본법 전문, 제주어 조례 현행·제정본·연혁, UNESCO 2건, RISS 2건, 새국어생활, 원본 MD) |
| `database/migrations/` | 001~003(공통), **004 지역·규칙·최신성(신규)** |
| `database/` | `load_kb.py`, `validate_package.py`, `verify_after_load.sql`, `run_search_tests.py` |
| `tools/build_dataset.py` | 생성기(ID·판정 고정, stale 자동 판정) |
| `.gitattributes`, `.gitignore` | 원문 SHA-256 보호. **최상위에 둘 것** |

## 실행 순서

```powershell
python -I database/validate_package.py
```

```powershell
python -I database/load_kb.py
```

```powershell
python -I database/run_search_tests.py --offline
```

1. 위 세 명령으로 오프라인 검증·사전 점검
2. 테스트용 Supabase에 `database/migrations/` 001 → 002 → 003 → 004 적용
3. `SUPABASE_DB_URL` 설정 후 `python -I database/load_kb.py --check-db` → `--apply`
4. `database/verify_after_load.sql`, `python -I database/run_search_tests.py`
