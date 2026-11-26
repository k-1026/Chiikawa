-- 굿즈 시안 선택 여부, 사용한 캐릭터, 포즈 출처를 저장한다.
ALTER TABLE daesatu."goods_designs" ADD COLUMN IF NOT EXISTS "selected" INTEGER NOT NULL DEFAULT 0;
ALTER TABLE daesatu."goods_designs" ADD COLUMN IF NOT EXISTS "who" TEXT NOT NULL DEFAULT 'both';
ALTER TABLE daesatu."goods_designs" ADD COLUMN IF NOT EXISTS "pose" TEXT NOT NULL DEFAULT '';
