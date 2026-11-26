"""Application-owned fixed plan structure; the model supplies values only."""
import base64
import datetime
import json
import re
from pathlib import Path
TEMPLATE=json.loads((Path(__file__).resolve().parent.parent/'plan_template_v06.json').read_text())
KEYS=tuple(k for s in TEMPLATE['sections'] for k in s['fields'])+('missing',)
TABLES=TEMPLATE['tables']
# 설명 글을 쓰는 장 (저장 키, 장 제목). 고정 양식의 순서와 같다.
NARRATIVE_CHAPTERS=(('overview','사업 요약'),('background','1. 추진 배경 · 필요성'),('purpose','2. 목적 · 컨셉 · 차별화'),('outline','3. 축제 개요'),
    ('programs','4. 프로그램 운영 계획'),('space','5. 공간 구성 · 동선'),('organization','6. 추진 체계 · 일정'),('promotion','7. 홍보 계획'),
    ('safety','8. 안전관리 계획'),('budget','9. 사업비 계획'),('effects','10. 기대효과 · 성과 측정'),('goods','11. 굿즈 운영 계획'))
NARR_MAX=7000
def text(value):
    if value is None:return ''
    if isinstance(value,(dict,list)):return json.dumps(value,ensure_ascii=False)
    return str(value)
MAX_DAYS=10
def schedule_headers(period):
    """개최 기간에서 일정표의 날짜 칸 이름을 만든다. 날짜를 알 수 없으면 '1일차' 식으로 3칸(또는 'N일'에 적힌 수)."""
    v=str(period or '');dates=[]
    full=re.findall(r'(20\d{2})\s*[-./년]\s*(\d{1,2})\s*[-./월]\s*(\d{1,2})',v)
    try:
        if len(full)>=2:
            a,b=(datetime.date(*map(int,x)) for x in (full[0],full[-1]))
        else:
            m=re.search(r'(\d{1,2})\s*월\s*(\d{1,2})\s*일?\s*(?:\([^)]*\))?\s*[~∼\-–—]\s*(?:(\d{1,2})\s*월\s*)?(\d{1,2})\s*일',v)
            year=re.search(r'20\d{2}',v)
            if not m:raise ValueError
            y=int(year.group(0)) if year else None
            a=datetime.date(y or 2001,int(m[1]),int(m[2]));b=datetime.date(y or 2001,int(m[3] or m[1]),int(m[4]))
            if not y:
                n=(b-a).days+1
                if not 1<=n<=MAX_DAYS:raise ValueError
                return ['%d/%d'%((a+datetime.timedelta(i)).month,(a+datetime.timedelta(i)).day) for i in range(n)]
        n=(b-a).days+1
        if not 1<=n<=MAX_DAYS:raise ValueError
        dates=[a+datetime.timedelta(i) for i in range(n)]
    except ValueError:
        m=re.search(r'(?<![\d월])(\d)\s*일\s*(?:간|\(|동안)',v)
        n=int(m[1]) if m and 1<=int(m[1])<=MAX_DAYS else 3
        return ['%d일차'%(i+1) for i in range(n)]
    return ['%d/%d(%s)'%(d.month,d.day,'월화수목금토일'[d.weekday()]) for d in dates]
def table_spec(key,period=''):
    spec=TABLES[key]
    if key!='schedule':return spec
    days=schedule_headers(period)
    return {'kind':'array','keys':[str(i) for i in range(len(days)+1)],'headers':[spec['headers'][0]]+days}
def clean_public(value):
    """저장된 공공데이터 시점 값의 모양을 확인한다(글자 길이·행 수 제한). 모양이 다르면 버린다."""
    if not isinstance(value,dict):return None
    s=lambda v,n=200:str(v if v is not None else '')[:n]
    table=lambda rows,width:[[s(c,80) for c in r[:width]] for r in rows[:20] if isinstance(r,list) and len(r)>=width] if isinstance(rows,list) else []
    shapes={'weather':(('station',),{'rows':6}),'stores':(('center','radius','total','counted','asof'),{'rows':2,'food':2}),'events':(('range','total'),{'rows':2})}
    out={'fetched':s(value.get('fetched'),20),'period_key':s(value.get('period_key'),200)}
    for name,(texts,tables) in shapes.items():
        part=value.get(name)
        if isinstance(part,dict):
            out[name]={**{k:s(part.get(k)) for k in texts},**{k:table(part.get(k),w) for k,w in tables.items()}}
    return out if any(k in out for k in shapes) else None
def normalize_plan(fields):
    source=fields if isinstance(fields,dict) else {}
    result={}
    for key in KEYS:
        value=source.get(key)
        if key not in TABLES:result[key]=text(value);continue
        spec=table_spec(key,text(source.get('period')));rows=value if isinstance(value,list) else []
        if spec['kind']=='scalar':result[key]=[text(v) for v in rows if not isinstance(v,(dict,list))]
        elif spec['kind']=='array':result[key]=[[text(row[i]) if i<len(row) else '' for i in range(len(spec['keys']))] for row in rows if isinstance(row,list)]
        else:result[key]=[{col:text(row.get(col)) for col in spec['keys']} for row in rows if isinstance(row,dict)]
    narr=source.get('narr') if isinstance(source.get('narr'),dict) else {}
    written={k:str(narr[k])[:NARR_MAX] for k,_ in NARRATIVE_CHAPTERS if isinstance(narr.get(k),str) and narr[k].strip()}
    if written:result['narr']=written
    public=clean_public(source.get('public'))
    if public:result['public']=public
    if isinstance(source.get('_searches'),list):result['_searches']=[v for v in source['_searches'] if isinstance(v,str)]
    return result

ROOT=Path(__file__).resolve().parent.parent
FIXED=json.loads((ROOT/'plan_fixed_v06.json').read_text(encoding='utf-8'))
EMPTY=re.compile(r'(미정|미입력|추가 확인 필요|확인 필요|미확정|TBD)[ .·\-]*',re.I)
def is_blank(value):
    if isinstance(value,list):return not value or all(is_blank(v) for v in value)
    if isinstance(value,dict):return not value or all(is_blank(v) for v in value.values())
    v=str(value or '').strip()
    return not v or bool(EMPTY.fullmatch(v))
def has_gap(value):
    """제출본 기준: 값이 없거나, 표의 칸이 하나라도 비어 있으면 True."""
    if isinstance(value,list):return not value or any(has_gap(v) for v in value)
    if isinstance(value,dict):return not value or any(has_gap(v) for v in value.values())
    return is_blank(value)
def apply_fixed(fields,generated=False):
    """해마다 같은 내용을 채운다. generated=True(AI가 막 작성)면 배치도·구역은 고정 문구로 덮고,
    그 밖에는 빈칸만 채워 담당자가 고친 내용을 지키지 않는 일이 없게 한다."""
    out=dict(fields)
    for key,val in FIXED['always'].items():
        if generated or is_blank(out.get(key)):out[key]=val
    for key,val in FIXED['when_blank'].items():
        if is_blank(out.get(key)):out[key]=val
    if isinstance(out.get('missing'),list):
        done={TEMPLATE['labels'].get(k) for k in list(FIXED['always'])+list(FIXED['when_blank'])}
        out['missing']=[v for v in out['missing'] if v not in done]
    return out
CONDITION_KEYS=('period','place','host','concept','goal','visitors','budget_total')
def condition_values(conditions):
    """담당자가 02 조건 선택에 저장한 값 중 기획안에 그대로 써야 하는 것. '산정 요청'처럼 값이 아닌 것은 뺀다."""
    c=conditions if isinstance(conditions,dict) else {}
    get=lambda k:str(c.get(k) or '').strip()
    out={k:get(k) for k in ('place','host','concept','goal') if not is_blank(get(k))}
    year=re.sub(r'\D','',get('year'));period=get('period')
    if period and not is_blank(period):
        out['period']=period if not year or year in period else year+'년 '+period
    m=re.search(r'[\d,]+\s*(?:천|만)?\s*명[^·]*',get('scale'))
    if m:out['visitors']=m.group(0).strip()
    budget=get('budget_total')
    if budget and not is_blank(budget) and '산정' not in budget:out['budget_total']=budget
    return out
def apply_conditions(fields,conditions):
    """AI가 새로 쓴 초안에 조건 값을 덮어쓴다. 조건에 적은 프로그램이 빠졌으면 이름을 넣는다."""
    out=dict(fields);out.update(condition_values(conditions))
    wanted=[v.strip() for v in re.split(r'\s*(?:·|,|/|\n)\s*',str((conditions or {}).get('programs') or '')) if v.strip() and not is_blank(v.strip())]
    rows=[dict(r) for r in (out.get('programs') or []) if isinstance(r,dict)]
    have=[''.join(str(r.get('name','')).split()) for r in rows]
    missing=[{'name':w,'desc':''} for w in wanted if not any(''.join(w.split()) in n or (n and n in ''.join(w.split())) for n in have)]
    if wanted:out['programs']=missing+rows
    if isinstance(out.get('missing'),list):
        done={TEMPLATE['labels'].get(k) for k in condition_values(conditions)}
        out['missing']=[v for v in out['missing'] if v not in done]
    return out
def previous_for_ai(plan):
    """이전 초안을 AI에게 줄 때, 조건에서 오는 값과 긴 설명 글은 뺀다(예전 값이 새 조건을 이기지 않게)."""
    if not isinstance(plan,dict):return plan
    return {k:v for k,v in plan.items() if k not in CONDITION_KEYS+('narr','public')}

def map_blocks():
    m=FIXED['map'];path=ROOT/m['image']
    blocks=[{'t':'h3','text':m['title']}]
    if path.is_file():
        blocks.append({'t':'img','wide':True,'src':'data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode(),'caption':m['caption']})
    blocks+=[{'t':'h3','text':'구역 안내'},{'t':'table','hdr':'col','rows':m['zones']},
             {'t':'h3','text':'편의시설 안내'},{'t':'table','hdr':'col','rows':m['facilities']}]
    return blocks

def clip(value,n=150):
    v=' '.join(text(value).split())
    return v if len(v)<=n else v[:n-1]+'…'

def mark_final(model,final):
    """검토를 마친 제출본: 초안 안내를 빼고 검토 담당자·확인일을 적는다."""
    model['warn']=[]
    model['subtitle']=('요약본' if model.get('compact') else '본문')+' · 제출본'
    model['meta']='검토 담당: %s · 검토 확인일: %s'%(final['responsible'],final['date'])
    model['foot']='대사투! 페스티벌'+(' · 요약본' if model.get('compact') else '')
    return model

def summary_model(fields,goods):
    rows=lambda keys:[[TEMPLATE['labels'][k],clip(fields[k],110)] for k in keys]
    progs=[[clip(r.get('name'),24),clip(r.get('desc'),60)] for r in (fields['programs'] or [])[:5]] or [['','']]
    items=[[clip(r.get('item'),30),clip(r.get('amount'),20)] for r in (fields['budget_items'] or [])[:5]]
    goods_rows=[['굿즈','시안','캐릭터']]+[[g['item_name'],g['did'][:8],g['who_txt']] for g in (goods or [])[:4]] if goods else [['굿즈','시안','캐릭터'],['선택한 시안 없음','','']]
    return {'compact':True,'title':TEMPLATE['title']+' · 요약본','subtitle':'요약본 (A4 1~2쪽) · 상세 내용은 본문 참고',
        'warn':['공식 제출 서식이 아닌 검토용 초안입니다. 미정·가정·추정 항목과 해당 공고의 제출 양식을 확인해 주세요.'],
        'sections':[
         {'h':'1. 개요','blocks':[{'t':'table','hdr':'row','rows':rows(['festival_name','period','place','host','visitors','budget_total'])}]},
         {'h':'2. 컨셉 · 목표 · 차별화','blocks':[{'t':'table','hdr':'row','rows':[[TEMPLATE['labels'][k],clip(fields[k],170)] for k in ('concept','goal','differentiation')]}]},
         {'h':'3. 주요 프로그램','blocks':[{'t':'table','hdr':'col','rows':[['프로그램','내용']]+progs}]},
         {'h':'4. 사업비 · 굿즈 · 확인 사항','blocks':[
            {'t':'table','hdr':'col','rows':[['비목','금액(원)']]+(items or [['미입력 · 직접 작성','']])},
            {'t':'table','hdr':'col','rows':goods_rows},
            {'t':'table','hdr':'row','rows':[['추가로 확인할 사항',clip('; '.join(fields['missing']),160)]]}]}],
        'foot':'대사투! 페스티벌 · 요약본'}

def plan_model(fields,goods=None,part='full',final=None):
    fields=apply_fixed(normalize_plan(fields))
    if part=='summary':
        model=summary_model(fields,goods)
        if final:
            tail=model['sections'][-1];tail['h']='4. 사업비 · 굿즈'
            tail['blocks']=tail['blocks'][:-1]
            return mark_final(model,final)
        return model
    import plan_form_v06 as FORM
    return FORM.build(fields,goods=goods,final=final)
