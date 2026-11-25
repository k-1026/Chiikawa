-- 굿즈 시안 이미지와 시안별 제작 계획의 근거 정보를 저장한다.
CREATE TABLE IF NOT EXISTS daesatu."goods_designs" (
  "id" TEXT PRIMARY KEY,
  "user_id" BIGINT NOT NULL,
  "item" TEXT NOT NULL,
  "concept" TEXT NOT NULL,
  "prompt" TEXT NOT NULL,
  "image" TEXT NOT NULL,
  "created_at" BIGINT NOT NULL
);
ALTER TABLE daesatu."goods_designs" ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON daesatu."goods_designs" FROM PUBLIC, anon, authenticated;
CREATE INDEX IF NOT EXISTS goods_designs_user ON daesatu.goods_designs(user_id, created_at);
