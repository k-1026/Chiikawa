# kimseunghee_01_방언특성변이 원문 DB 패키지

`local 리서치/kimseunghee_01_방언특성변이.md`(main, 마지막 수정 커밋 `5f61dc4`)의 주장을 공식·학술 원문과 대조해 Supabase `kb` 스키마에 적재할 수 있게 만든 패키지입니다. 확인일 2026-11-26.

**하지 않은 것:** Supabase 적재·스키마 변경, Storage 업로드, 임베딩·AI API 호출, 에이전트 연결, 한글 검색 테스트 실행(**미실행** — 실제 DB 없음). 마이그레이션 003은 아직 어떤 DB에서도 실행하지 않았습니다.

## 폴더 구조

| 위치 | 내용 |
|---|---|
| `README.md` | 이 안내 |
| `docs/데이터사전.md` | **상세 문서** — 결과, 불일치·미확인 목록, 파일·테이블, 규칙, 도구 기록 |
| `data/` | 적재용 CSV 11개 + `search_tests.csv` |
| `json/` | MD 고정 양식(하위 키워드 문서 01~09 공통), 코드값 사전 |
| `originals/` | 보관 원문 7개(국립국어원 2, 학술 서지 4, 원본 MD 1). 칼럼 1건은 URL·발췌·SHA-256만 |
| `database/` | 마이그레이션 001~003, `load_kb.py`, `validate_package.py`, `verify_after_load.sql`, `run_search_tests.py` |
| `tools/build_dataset.py` | CSV·JSON 생성기(ID·판정 고정) |
| `.gitattributes`, `.gitignore` | 원문 SHA-256 보호. **최상위에 둘 것** |

## 실행 순서

```powershell
python -I database/validate_package.py
```

```powershell
python -I database/load_kb.py
```

1. 위 두 명령으로 오프라인 검증·사전 점검
2. Supabase(테스트 프로젝트 권장)에 `database/migrations/` 001 → 002 → 003 적용(다른 kimseunghee·hyunhee 패키지와 같은 파일이라 이미 적용했으면 다시 해도 무해)
3. 환경변수 `SUPABASE_DB_URL` 설정 후 `--check-db` → `--apply`, 필요 시 `--upload-originals --verify-storage`
4. `database/verify_after_load.sql`, `python -I database/run_search_tests.py`

자세한 내용은 [docs/데이터사전.md](docs/데이터사전.md).
