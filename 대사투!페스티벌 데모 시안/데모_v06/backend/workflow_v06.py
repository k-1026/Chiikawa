"""Deterministic review of the user's current draft, not a claim of external validation."""
import hashlib
import json
import re
from plan_schema_v06 import TEMPLATE,normalize_plan
CHECKS=('missing','evidence','budget','responsibility')
def signature(w):
    return hashlib.sha256(json.dumps({k:w.get(k) for k in ('conditions','plan','goods','messages')},sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def unresolved(value):
    if isinstance(value,list):return not value or all(unresolved(v) for v in value)
    if isinstance(value,dict):return not value or all(unresolved(v) for v in value.values())
    return not str(value or '').strip() or bool(re.fullmatch(r'(미정|미입력|추가 확인 필요|확인 필요|미확정|TBD)[ .·\-]*',str(value).strip(),re.I))
def review_report(w):
    plan=w.get('plan');fields=normalize_plan(plan) if plan else {};missing=[TEMPLATE['labels'][k] for s in TEMPLATE['sections'] for k in s['fields'] if unresolved(fields.get(k))]
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
    return {'has_plan':bool(plan),'missing':missing,'open_questions':fields.get('missing',[]),'evidence':evidence[:60], 'checks':checks,'responsible':r.get('responsible',''),'note':r.get('note',''),'at':r.get('at') if fresh else None,'stale':bool(r) and not fresh,'complete':bool(plan) and fresh and all(checks.values()) and bool(r.get('responsible','').strip()),'signature':signature(w)}
