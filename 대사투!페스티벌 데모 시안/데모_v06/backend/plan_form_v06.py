"""고정 기획안 양식(본문 20~24쪽 목표): 표지 · 목차 · 사업 요약 · 1~12장 · 별첨(굿즈 제작 계획서).
- 목차·표 구성·운영 기준 표는 해마다 같다(plan_fixed_v06.json).
- 값은 기획안 항목에서, 설명 글(narr)은 장별로 AI가 쓰고 담당자가 고친 것을 그대로 쓴다.
- 장마다 새 쪽에서 시작한다. 근거 없는 값은 만들지 않는다."""
import re

from plan_schema_v06 import FIXED, TEMPLATE, NARRATIVE_CHAPTERS, mark_final, map_blocks, table_spec, text

FORM = FIXED['form']
MAX_APPENDIX = 3          # 별첨에 넣는 굿즈 품목 수 상한
CHAPTER_TITLES = dict(NARRATIVE_CHAPTERS)
TOC = [t for _, t in NARRATIVE_CHAPTERS] + ['12. 신청 단체 · 확약']
JOINED = ('effects',)       # 짧은 장은 앞 장에 이어서 시작한다
NO_NARR = '아직 설명 글이 없습니다. 06. 기획안 작성에서 "AI로 설명 글 쓰기"를 누르거나 직접 적어 주세요.'


def narrative_blocks(value, final):
    """'▶ 요약', '□ 제목', '○ 항목', '- 세부' 줄 표시를 문서 블록으로 바꾼다."""
    blocks = []
    for raw in str(value or '').replace('\r', '').split('\n'):
        line = raw.strip()
        if not line:
            continue
        if line.startswith('▶'):
            blocks.append({'t': 'lead', 'text': line[1:].strip()})
        elif line.startswith('□'):
            blocks.append({'t': 'h3', 'text': line})
        elif line.startswith('○'):
            blocks.append({'t': 'li', 'level': 1, 'text': line})
        elif line.startswith('-'):
            blocks.append({'t': 'li', 'level': 2, 'text': line})
        else:
            blocks.append({'t': 'p', 'text': line})
    if not blocks and not final:
        blocks.append({'t': 'note', 'text': NO_NARR})
    return blocks


def _rows(fields, keys):
    return {'t': 'table', 'hdr': 'row', 'rows': [[TEMPLATE['labels'][k], text(fields[k])] for k in keys]}


def _grid(fields, key):
    spec = table_spec(key, fields.get('period', ''))
    rows = fields[key] or ([['']*len(spec['keys'])] if spec['kind'] == 'array' else [{}])
    rows = [[text(r.get(c)) for c in spec['keys']] if isinstance(r, dict) else r for r in rows]
    return {'t': 'table', 'hdr': 'col', 'rows': [spec['headers']] + rows}


def _fixed(key, title):
    return [{'t': 'h3', 'text': title}, {'t': 'table', 'hdr': 'col', 'rows': FORM[key]}]


def _h(t):
    return {'t': 'h3', 'text': t}


def chapter_tables(key, f, goods, final):
    """장마다 설명 글 뒤에 붙는 표·그림."""
    if key == 'overview':
        return [_h('사업 개요'), _rows(f, ['festival_name', 'period', 'place', 'host', 'concept', 'goal', 'visitors', 'budget_total'])]
    if key == 'background':
        return _fixed('evidence', '조사 근거') + [{'t': 'note', 'text': FORM['evidence_note']}]
    if key == 'purpose':
        return [_h('목표 · 컨셉'), _rows(f, ['goal', 'concept', 'differentiation', 'necessity'])]
    if key == 'outline':
        return [_h('축제 개요'), _rows(f, ['festival_name', 'period', 'place', 'host', 'visitors', 'budget_total', 'scope', 'budget_vat', 'prep_period', 'report_due'])]
    if key == 'programs':
        return [_h('프로그램 구성'), _grid(f, 'programs'), _h('일정표'), _grid(f, 'schedule')]
    if key == 'space':
        return [_rows(f, ['layout'])] + map_blocks()
    if key == 'organization':
        return [_h('추진 여건'), _rows(f, ['partners', 'scale', 'stay_link', 'prep', 'report_plan'])] + \
            _fixed('organization', '역할 분담 (운영 기준안)') + _fixed('stages', '추진 단계 (운영 기준안)')
    if key == 'promotion':
        return [_h('홍보 계획'), _rows(f, ['mascot', 'promo_pre', 'promo_off', 'promo_on'])] + _fixed('promo_stages', '시기별 홍보 (운영 기준안)')
    if key == 'safety':
        return [_h('안전관리 개요'), _rows(f, ['safety_staff', 'safety_peak', 'safety_org', 'heat', 'cautions', 'permits', 'opinion'])] + \
            _fixed('risks', '위험별 대응 (운영 기준안)') + _fixed('safety_checklist', '허가·신고 점검 (관계 기관 최신 기준 확인)')
    if key == 'budget':
        return [_h('총 사업비'), _rows(f, ['budget_total', 'budget_vat']), _h('사업비 산출내역'), _grid(f, 'budget_items')] + \
            _fixed('budget_rules', '예산 편성·관리 기준 (운영 기준안)')
    if key == 'effects':
        blocks = [_rows(f, ['effects']), _h('성과지표와 측정 방법'), _grid(f, 'kpi')]
        return blocks
    if key == 'goods':
        import goods_doc_v06 as GD
        return GD.goods_part_blocks(goods, f['concept'], final=final) + _fixed('goods_flow', '굿즈 제작 흐름 (운영 기준안)')
    return []


def _clean_appendix(sections, final):
    """별첨에서는 작성 방법 안내와 외부 사례 이름을 빼고, 제출본의 미정 칸은 '발주 전 확정'으로 적는다."""
    import goods_doc_v06 as GD
    out = []
    for s in sections:
        blocks = []
        skip_next = False
        for b in s['blocks']:
            if b.get('t') == 'pagebreak':
                continue
            if b.get('t') == 'h3' and b.get('text', '').startswith('10-1.'):
                skip_next = True
                continue
            if skip_next:
                skip_next = False
                continue
            b = dict(b)
            if b.get('t') == 'h3' and b.get('text', '').startswith('10-'):
                b['text'] = '10-%d.%s' % (int(b['text'][3]) - 1, b['text'][5:])
            if b.get('t') == 'table':
                rows = [r for r in b['rows'] if not any(w in str(c) for c in r for w in ('점촌', '미소 「'))]
                if final:
                    rows = [[('발주 전 확정' if str(c).strip() in ('', GD.NEED, GD.VENDOR) else str(c).replace('(초안 → ', '(') ) for c in r] for r in rows]
                    rows = [r for r in rows if r[0] not in ('상태', '시트 버전')]
                b['rows'] = rows
            if final and b.get('t') in ('note', 'p') and ('입력 필요' in b.get('text', '') or '초안' in b.get('text', '')):
                continue
            blocks.append(b)
        if blocks:
            out.append({'h': s.get('h', ''), 'blocks': blocks})
    return out


def appendix_sections(f, goods, final, festival=None):
    import goods_doc_v06 as GD
    sections = []
    for n, g in enumerate((goods or [])[:MAX_APPENDIX], 1):
        info = {'item_key': g.get('item', ''), 'item_name': g['item_name'], 'spec': g.get('spec', ''), 'concept': g.get('concept') or f['concept'],
                'did': g['did'], 'image_b64': g['image_b64'], 'who': g.get('who', 'both'), 'who_txt': g.get('who_txt'), 'pose': g.get('pose_txt', ''),
                'qty': g.get('qty'), 'festival_name': f['festival_name'] or '(축제명 미정)', 'host': f['host'], 'budget_total': f['budget_total'],
                'festival': GD.festival_date({'plan': f}), 'selected': True}
        body = _clean_appendix(GD.goods_plan_model(info)['sections'], final)
        sections.append({'h': '별첨 %d. %s 제작 계획서' % (n, g['item_name']), 'break': True, 'appendix': True, 'blocks': []})
        sections.extend(dict(s, appendix=True) for s in body)
    return sections


def build(fields, goods=None, final=None, with_appendix=True):
    narr = fields.get('narr') or {}
    sections = []
    for key, title in NARRATIVE_CHAPTERS:
        blocks = narrative_blocks(narr.get(key), bool(final)) + chapter_tables(key, fields, goods, bool(final))
        sections.append({'h': title, 'break': key not in JOINED, 'blocks': blocks})
    tail = [['서약서 · 개인정보 동의서', '공고 서식으로 별도 작성']]
    if not final:
        tail.append(['추가로 확인할 사항', '\n'.join(fields['missing'])])
    sections.append({'h': '12. 신청 단체 · 확약', 'blocks': [
        _rows(fields, ['org_intro', 'track_record', 'commitment']), {'t': 'table', 'hdr': 'row', 'rows': tail},
        _h('제출 전 확인'), {'t': 'table', 'hdr': 'col', 'rows': [['확인 내용', '확인'],
            ['기간·장소·주최·예산이 모든 장에서 같은지 확인', '□'], ['[가정]·[추정]·[제안] 표시 값의 승인 여부 확인', '□'],
            ['인용한 조사 자료의 원문과 기준 연도 확인', '□'], ['지도 사용 조건과 출처 표시 확인', '□'], ['해당 공고의 제출 양식·쪽수 확인', '□']]}]})
    toc = [['순서', '내용']] + [[str(i + 1), t] for i, t in enumerate(TOC)]
    appendix = appendix_sections(fields, goods, bool(final)) if with_appendix else []
    if goods:
        toc += [['별첨 %d' % (n + 1), '%s 제작 계획서' % g['item_name']] for n, g in enumerate(goods[:MAX_APPENDIX])]
    cover = [{'h': '', 'blocks': [{'t': 'cover', 'rows': [x for x in (fields['festival_name'], fields['period'], fields['place'], fields['host']) if x]}]},
             {'h': '목차', 'break': True, 'blocks': [{'t': 'table', 'hdr': 'col', 'rows': toc}]}]
    model = {'title': TEMPLATE['title'], 'subtitle': '검토용 초안 · 고정 양식 · 본문',
             'warn': ['공식 제출 서식이 아닌 검토용 초안입니다. 미정·가정·추정 항목과 해당 공고의 제출 양식을 확인해 주세요.'],
             'sections': cover + sections + appendix, 'foot': '대사투! 페스티벌 · 고정 양식'}
    model['form'] = True
    return mark_final(model, final) if final else model


def page_count(pdf):
    return len(re.findall(rb'/Type\s*/Page[^s]', pdf))


def fit_density(model, render):
    """본문이 목표 쪽수를 넘으면 줄 간격·표 간격을 한 단계씩, 모자라면 반대로 조정한 값을 고른다.
    render(model) -> PDF bytes. 글을 지우거나 만들지는 않는다. 반환: (조정한 모델, 본문 쪽수)"""
    low, high = FORM['body_pages']
    pages = page_count(render(body_only(model)))
    steps = [-1, -2] if pages > high else [1, 2] if pages < low else []
    for step in steps:
        model = dict(model, density=step)
        pages = page_count(render(body_only(model)))
        if low <= pages <= high:
            break
    return model, pages


def body_only(model):
    """쪽수 확인용: 표지·목차·별첨을 뺀 본문."""
    body = [s for s in model['sections'][2:] if not s.get('appendix')]
    if body:
        body[0] = dict(body[0], **{'break': False})   # 맨 앞 쪽 나눔은 빈 쪽을 만든다
    return dict(model, sections=body, title='', subtitle='', warn=[], meta='', foot='')
