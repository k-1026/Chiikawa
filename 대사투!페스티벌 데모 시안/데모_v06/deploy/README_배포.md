# v06 서버 배포 메모

## 이미 된 것 (검증함)
- 계정·기관·세션·작업공간·감사·첨부·호출 기록이 Supabase `daesatu` 스키마로 이전됨 (건수 일치).
- 서버가 `DATABASE_URL` 이 있으면 Supabase 를 쓴다 (시작 시 "저장소: Supabase(PostgreSQL)" 출력).
- 지침 문서 1,031조각이 `daesatu.knowledge_chunks`(pgvector)에 있고, 검색이 DB를 본다.
- 기존 테스트가 실제 PostgreSQL(테스트용 `daesatu_test` 스키마)에서 통과: 인증 16/17(1건은 SQLite 파일 권한 검사), 첨부 5/5, HTTP 18/18.

## 아직 안 된 것
1. ~~외부 경로 의존~~ → 해결: AI 모듈·지침·문서 파일을 `ai_v06/` 안으로 옮겼고, v05·docs 폴더 없이 AI 모듈 로드와 DB 검색이 동작함(검증함).
2. Dockerfile·render.yaml 은 작성만 했고 빌드/배포는 해 보지 않았다 (이 컴퓨터에 docker 없음, Render 계정 필요).
3. Vercel 화면이 새 서버 주소를 보게 바꾸고, 임시 터널(cloudflared) 의존을 없애야 한다.
4. 서버 환경변수: DATABASE_URL, GEMINI_API_KEY, GEMINI_MODEL, EMBEDDING_MODEL, EMBEDDING_DIM (Render 화면에 직접 입력).
5. Render 가 코드를 가져가려면 `데모_v06`이 GitHub 에 올라가 있어야 한다 (.env, .runtime, backend/vendor 는 제외됨).
