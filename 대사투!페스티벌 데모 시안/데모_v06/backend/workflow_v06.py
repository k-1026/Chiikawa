"""Deterministic review of the user's current draft, not a claim of external validation."""
import hashlib
import json
import re
from plan_schema_v06 import TEMPLATE,normalize_plan,apply_fixed,has_gap
CHECKS=('missing','evidence','budget','responsibility')
def signature(w):
    return hashlib.sha256(json.dumps({k:w.get(k) for k in ('conditions','plan','goods','messages')},sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def review_report(w,goods_ids=None):
    """goods_ids: 지금 기획안에 들어가는 굿즈 시안 번호. 검토한 뒤 시안을 바꾸면 다시 검토해야 한다."""
    plan=w.get('plan');fields=apply_fixed(normalize_plan(plan)) if plan else {};blank=[k for s in TEMPLATE['sections'] for k in s['fields'] if has_gap(fields.get(k))] if plan else [];missing=[TEMPLATE['labels'][k] for k in blank]
    evidence=[];seen=set()
    for m in w.get('messages',[]):
        for a in m.get('attachments',[]):
            key='file:'+a.get('id','')
            if key not in seen:seen.add(key);evidence.append({'label':'첨부 · '+a.get('name','자료'),'kind':'file'})
        for url in re.findall(r'https?://[^\s<>\]\)"\u3002]+',m.get('content','')):
            url=url.rstrip('.,;')
            if url not in seen:seen.add(url);evidence.append({'label':url,'url':url,'kind':'url'})
    r=w.get('review') or {};fresh=r.get('signature')==signature(w)
    checks={k:bool(r.get('checks',{}).get(k)) if fresh else False for k in CHECKS}
    goods_changed=goods_ids is not None and fresh and sorted(goods_ids)!=sorted(r.get('goods_ids',[]))
    if goods_changed:fresh=False;checks={k:False for k in CHECKS}
    complete=bool(plan) and fresh and all(checks.values()) and bool(r.get('responsible','').strip())
    blockers=[]
    if not plan:blockers.append('기획안 초안이 없습니다.')
    if missing:blockers.append('미입력 %d개를 채워 주세요: %s'%(len(missing),', '.join(missing)))
    if plan and not complete:blockers.append('07 최종 검토에서 확인 항목 4개와 검토 담당자를 저장해 주세요.'+(' (검토 뒤에 내용이 바뀌었습니다.)' if r and not fresh else ''))
    return {'blank_keys':blank,'blockers':blockers,'submittable':not blockers,'has_plan':bool(plan),'missing':missing,'open_questions':[q for q in fields.get('missing',[]) if not any(q==TEMPLATE['labels'].get(k) and not has_gap(v) for k,v in fields.items() if k!='missing')],'evidence':evidence[:60], 'checks':checks,'responsible':r.get('responsible',''),'note':r.get('note',''),'at':r.get('at') if fresh else None,'stale':bool(r) and not fresh,'complete':complete,'signature':signature(w)}
