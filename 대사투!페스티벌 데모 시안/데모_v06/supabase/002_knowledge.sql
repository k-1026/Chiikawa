-- 에이전트가 참고하는 지침 문서(RAG)를 DB로 옮긴다. 컴퓨터의 rag_index 파일 대신 이 표를 검색한다.
CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA extensions;

CREATE TABLE IF NOT EXISTS daesatu."knowledge_chunks" (
  "id" TEXT PRIMARY KEY,
  "source" TEXT NOT NULL,
  "file" TEXT NOT NULL,
  "heading" TEXT NOT NULL DEFAULT '',
  "seq" INTEGER NOT NULL DEFAULT 0,
  "text" TEXT NOT NULL,
  "embedding" extensions.vector(768) NOT NULL
);
ALTER TABLE daesatu."knowledge_chunks" ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON daesatu."knowledge_chunks" FROM PUBLIC, anon, authenticated;
CREATE INDEX IF NOT EXISTS knowledge_chunks_file ON daesatu.knowledge_chunks(file);
