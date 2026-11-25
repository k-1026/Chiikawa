"""Application-owned fixed plan structure; the model supplies values only."""
import json
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

def plan_model(fields):
    fields=normalize_plan(fields);sections=[]
    for section in TEMPLATE['sections']:
        blocks=[]
        for key in section['fields']:
            value=fields[key]
            if key in TABLES:
                spec=TABLES[key];rows=value or ([['']*len(spec['keys'])] if spec['kind']=='array' else [{}])
                rows=[[text(row.get(c)) for c in spec['keys']] if isinstance(row,dict) else row for row in rows]
                blocks.extend([{'t':'h3','text':TEMPLATE['labels'][key]},{'t':'table','hdr':'col','rows':[spec['headers']]+rows}])
            else:blocks.append({'t':'table','hdr':'row','rows':[[TEMPLATE['labels'][key],value]]})
        if section['title'].startswith('5.'):
            blocks.insert(0,{'t':'table','hdr':'row','rows':[['총 사업비',fields['budget_total']]]})
        if section['title'].startswith('7.'):
            blocks.append({'t':'table','hdr':'col','rows':[['점검 항목','상태'],['예산 편성','초안 있음' if fields['budget_total'] else '미정'],['전담 인력 편성','초안 있음' if fields['safety_staff'] or fields['scale'] else '미정'],['방문객 추산','초안 있음' if fields['visitors'] else '미정'],['안전계획 수립','별도 확인 필요']]})
        if section['title'].startswith('8.'):
            blocks.append({'t':'table','hdr':'row','rows':[['서약서 · 개인정보 동의서','공고 서식으로 별도 작성'],['추가로 확인할 사항','\n'.join(fields['missing'])]]})
        sections.append({'h':section['title'],'blocks':blocks})
    return {'title':TEMPLATE['title'],'subtitle':'검토용 초안 · 고정 양식','warn':['공식 제출 서식이 아닌 검토용 초안입니다. 미정·가정·추정 항목과 해당 공고의 제출 양식을 확인해 주세요.'],'sections':sections,'foot':'대사투! 페스티벌 · v06 · 고정 양식'}
