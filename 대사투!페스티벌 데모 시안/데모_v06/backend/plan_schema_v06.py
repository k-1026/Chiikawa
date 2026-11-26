"""Application-owned fixed plan structure; the model supplies values only."""
import base64
import json
import re
from pathlib import Path
TEMPLATE=json.loads((Path(__file__).resolve().parent.parent/'plan_template_v06.json').read_text())
KEYS=tuple(k for s in TEMPLATE['sections'] for k in s['fields'])+('missing',)
TABLES=TEMPLATE['tables']
def text(value):
    if value is None:return ''
    if isinstance(value,(dict,list)):return json.dumps(value,ensure_ascii=False)
    return str(value)
def normalize_plan(fields):
    source=fields if isinstance(fields,dict) else {}
    result={}
    for key in KEYS:
        value=source.get(key)
        if key not in TABLES:result[key]=text(value);continue
        spec=TABLES[key];rows=value if isinstance(value,list) else []
        if spec['kind']=='scalar':result[key]=[text(v) for v in rows if not isinstance(v,(dict,list))]
        elif spec['kind']=='array':result[key]=[[text(row[i]) if i<len(row) else '' for i in range(len(spec['keys']))] for row in rows if isinstance(row,list)]
        else:result[key]=[{col:text(row.get(col)) for col in spec['keys']} for row in rows if isinstance(row,dict)]
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
    fields=apply_fixed(normalize_plan(fields));sections=[]
    if part=='summary':
        model=summary_model(fields,goods)
        if final:
            tail=model['sections'][-1];tail['h']='4. 사업비 · 굿즈'
            tail['blocks']=tail['blocks'][:-1]
            return mark_final(model,final)
        return model
    for section in TEMPLATE['sections']:
        blocks=[]
        for key in section['fields']:
            value=fields[key]
            if key in TABLES:
                spec=TABLES[key];rows=value or ([['']*len(spec['keys'])] if spec['kind']=='array' else [{}])
                rows=[[text(row.get(c)) for c in spec['keys']] if isinstance(row,dict) else row for row in rows]
                blocks.extend([{'t':'h3','text':TEMPLATE['labels'][key]},{'t':'table','hdr':'col','rows':[spec['headers']]+rows}])
            else:blocks.append({'t':'table','hdr':'row','rows':[[TEMPLATE['labels'][key],value]]})
        if section['title'].startswith('3.'):
            blocks.extend(map_blocks())
        if section['title'].startswith('5.'):
            blocks.insert(0,{'t':'table','hdr':'row','rows':[['총 사업비',fields['budget_total']]]})
        if section['title'].startswith('7.') and not final:
            blocks.append({'t':'table','hdr':'col','rows':[['점검 항목','상태'],['예산 편성','초안 있음' if fields['budget_total'] else '미정'],['전담 인력 편성','초안 있음' if fields['safety_staff'] or fields['scale'] else '미정'],['방문객 추산','초안 있음' if fields['visitors'] else '미정'],['안전계획 수립','별도 확인 필요']]})
        if section['title'].startswith('8.'):
            tail=[['서약서 · 개인정보 동의서','공고 서식으로 별도 작성']]
            if not final:tail.append(['추가로 확인할 사항','\n'.join(fields['missing'])])
            blocks.append({'t':'table','hdr':'row','rows':tail})
        title=section['title'].replace('자체 점검','성과지표') if final else section['title']
        sections.append({'h':title,'blocks':blocks})
    import goods_doc_v06 as GD
    sections.append({'h':'9. 굿즈 운영 및 성과품 납품','blocks':GD.goods_part_blocks(goods,fields['concept'],final=bool(final))})
    model={'title':TEMPLATE['title'],'subtitle':'검토용 초안 · 고정 양식 · 본문','warn':['공식 제출 서식이 아닌 검토용 초안입니다. 미정·가정·추정 항목과 해당 공고의 제출 양식을 확인해 주세요.'],'sections':sections,'foot':'대사투! 페스티벌 · v06 · 고정 양식'}
    return mark_final(model,final) if final else model
