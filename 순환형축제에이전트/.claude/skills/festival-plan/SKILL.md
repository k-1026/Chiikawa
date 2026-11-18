---
name: festival-plan
description: 연도 주제부터 기획안 통합까지(S4~S10). 연도 주제·아이디어 평가·파트 기획·운영(동선·예산·인력·안전·스탬프 운영·웹)·KPI·전체 검증을 거쳐 03_기획안을 만든다. 항목을 붙이면("토론 대회만", "예산만") 부분 요청 모드로 돈다.
argument-hint: <개최 연도> [부분 항목]
---

# 이어 하기 입구 3 — S4 ~ S10

인자: `$ARGUMENTS` — 첫 단어는 연도, 나머지는 부분 항목.

## 부분 항목이 있으면
`지침/라우팅표.md` 의 "부분 요청 처리 순서"대로 한다. 03_기획안의 해당 장과 `03_파트/` 해당 파일만 고친다.

## 전체면
1. `00_진행상태.md` 를 읽고 멈춘 단계부터 이어 간다. S3까지 통과하지 않았으면 `/festival-research <연도>` 를 안내하고 멈춘다.
2. `지침/호출순서.md` 를 따른다.
   - 3단 뒷부분 S4: `strategist (연도 주제)` → `ethics-reviewer` → **게이트 S4**
   - 4단 S5~S6: `part-agent A · E (후보)` → `ethics-reviewer` → `idea-scorer` → 재계산 비교 → **게이트 S6**
   - 5단 S7: `part-agent` A~G 병렬 → J 검수 · G 이어받기 → `duplicate-finder` · `format-checker` · `ethics-reviewer`
   - 6단 S8: `flow-designer` → `part-agent H` · `part-agent K` → `conflict-checker`
   - 7단 S9: `part-agent I` → `conflict-checker`
   - 8단 S10 전체 검증: 검증 5개 병렬 → `reviewer`
   - 9단: 오케스트레이터가 `양식/03_기획안.md` 로 통합 → **게이트 S10**
3. 게이트마다 멈추고 승인을 받는다. 단계마다 재작업 최대 2회.
4. 담당자가 결정할 항목(채택 아이디어, 예산안 선택)을 따로 목록으로 보여 준다.
5. 축제가 끝나면 `/festival-review <연도>` 를 쓰라고 안내한다.
