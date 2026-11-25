"""All selected conditions are a prerequisite to any v06 AI planning call."""
import re
LABELS={'year':'개최 연도','host':'주최·주관','concept':'컨셉','programs':'프로그램','scale':'운영 규모 · 예상 관람객','theme':'테마','period':'개최 기간','place':'개최 장소','budget_total':'예산 범위','target':'대상 관람객','goal':'핵심 목표'}
UNKNOWN={'미입력','미정','미확정','모름','모르겠어요','선택','선택해 주세요','미선택','tbd','n/a','-'}
def missing_conditions(values):
    values=values if isinstance(values,dict) else {}
    missing=[k for k in LABELS if not isinstance(values.get(k),str) or not values[k].strip() or values[k].strip().lower() in UNKNOWN]
    if 'year' not in missing and not re.fullmatch(r'(?:19|20|21)\d{2}년?',values['year'].strip()):missing.append('year')
    return missing

def require_conditions(values):
    from auth_v06 import Error
    missing=missing_conditions(values)
    if missing:raise Error('02. 조건 선택에서 모든 필수 조건을 입력·저장한 뒤 기획을 시작해 주세요. 확인할 항목: '+', '.join(LABELS[k] for k in missing),409)
