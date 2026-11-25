# v06 배포 구조와 수정 방법

```text
사용자 → Vercel(화면, daesatu-festival-web) → Render(서버, daesatu-festival-api) → Supabase(DB·지침 문서)
                                                       └→ Gemini(AI)
```
내 컴퓨터는 이 경로에 없다. 컴퓨터를 꺼도 동작한다(Render 무료 서버는 접속이 없으면 잠들어 첫 접속이 30~60초 늦을 수 있음).

## 연결 상태
| 연결 | 내용 |
|---|---|
| GitHub | `k-1026/Chiikawa`, 브랜치 `main` (공개 저장소: 비밀값은 코드에 넣지 않는다) |
| Vercel | 프로젝트 `daesatu-festival-web`, 폴더 `대사투!페스티벌 데모 시안/데모_v06`, 운영 브랜치 `main`, `vercel.json` 이 `/api` 를 Render 로 연결 |
| Render | 서비스 `daesatu-festival-api`, 저장소 루트의 `Dockerfile.v06`, `render.yaml`(Blueprint), 자동 배포 |
| Supabase | 프로젝트 `aqtsgaeqnqppezxkidhe`, 스키마 `daesatu`(계정·기획·감사), 표 `knowledge_chunks`(지침 문서 1,031조각, pgvector) |

## 고치는 방법
- 화면(HTML/CSS/JS) 또는 서버(Python) 수정 → GitHub `main` 에 푸시 → Vercel·Render 가 자동 배포 (1~3분).
- 서버 환경변수(`DATABASE_URL`, `GEMINI_API_KEY`, `GEMINI_MODEL`, `EMBEDDING_MODEL`, `EMBEDDING_DIM`) 는 Render 화면 Environment 에서만 바꾼다.
- DB 구조 변경 → `supabase/` 에 SQL 파일을 추가해 Supabase 에서 실행.
- 지침 문서 변경 → 임베딩을 다시 만든 뒤 `tools/load_knowledge_v06.py --replace`.
- 서버 주소를 바꾸면 `python3 tools/package_vercel.py --destination public --root-config --backend <새 주소>` 로 `vercel.json` 을 다시 만든다.

## 주의
- 사이트 주소를 추가하면 Render 의 `PUBLIC_WEB_ORIGINS`(루트 `render.yaml`)에도 넣어야 로그인이 막히지 않는다.
- Render 폴더 이름에 한글·`!` 가 있으면 Root Directory 를 못 쓰므로 `Dockerfile.v06` 방식을 쓴다.
- 테스트는 실제 DB 와 분리된 스키마(`daesatu_test`)에서 한다.
