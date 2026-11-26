-- 한 번 만든 배경·제품 사진을 다시 쓰기 위한 저장소(Cloudflare 무료 한도 절약).
CREATE TABLE IF NOT EXISTS daesatu."goods_bg_cache" (
  "key" TEXT PRIMARY KEY,
  "image" TEXT NOT NULL,
  "created_at" BIGINT NOT NULL
);
ALTER TABLE daesatu."goods_bg_cache" ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON daesatu."goods_bg_cache" FROM PUBLIC, anon, authenticated;
