"""고정 양식의 장별 '설명 글'을 AI(Gemini)가 쓴다.
- 근거: 담당자가 저장한 조건, 기획안 항목, 고정 배치 정보, 팀 조사 근거, 선택한 굿즈 시안. 그 밖의 사실·수치·기관명은 만들지 않는다.
- 무료 한도를 아끼려고 장을 몇 개씩 묶어 부른다. 한 장만 다시 쓰면 1번 부른다."""
import json
import os
import re
import time

from plan_schema_v06 import FIXED, TEMPLATE, NARRATIVE_CHAPTERS, NARR_MAX, apply_fixed, normalize_plan, condition_values

# 장 키: (묶음 번호, 목표 글자 수, 써야 할 내용)
GUIDE = {
    'overview': (1, 800, '어떤 축제를 왜, 누구를 위해, 어떻게 여는지 한 쪽으로 요약. □ 추진 개요 / □ 핵심 운영 방향 / □ 담당자 확인 요청'),
    'background': (1, 1200, '□ 현황(조사 근거를 자료 종류와 함께 인용) / □ 문제 / □ 이 축제가 필요한 이유'),
    'purpose': (1, 1300, '□ 올해 컨셉의 의미와 적용 방식 / □ 목표와 우선순위 / □ 대상별 기대 경험 / □ 차별화 전략'),
    'outline': (1, 700, '□ 기간 / □ 장소(왜 이 장소를 이 구성으로 쓰는지) / □ 규모와 운영 시간 원칙'),
    'programs': (2, 3600, '프로그램마다 □ 이름을 만들고 ○ 추진 취지, ○ 진행 순서, ○ 시간·장소, ○ 참여 방법, ○ 운영 인력·준비물, ○ 우천·폭염 대안을 모두 쓴다. 마지막에 □ 일자별 운영 흐름'),
    'space': (3, 1300, '□ 공간 구성 원칙 / □ 방문객 동선(출입로부터 순서대로) / □ 구역별 운영 방식(구역마다 ○) / □ 편의·안전 시설 이용 안내'),
    'organization': (3, 1200, '□ 추진 체계와 의사 결정 / □ 협력 방식 / □ 단계별 준비 / □ 보고와 기록'),
    'promotion': (3, 1300, '□ 홍보 방향과 핵심 메시지 / □ 대상별 접근 / □ 시기별 전략 / □ 마스코트·사투리 표현 활용 원칙 / □ 확인 방법'),
    'safety': (4, 2200, '□ 안전 운영 원칙 / □ 인파 관리 / □ 폭염(공공데이터에 날씨 관측값이 있으면 첫 ○ 에서 "기상청 관측 기준"이라고 밝히고 연도별 가장 높은 기온과 33℃ 이상인 날 수를 값 그대로 인용한 뒤 대책의 근거로 삼는다) / □ 우천·강풍 / □ 응급·화재 / □ 비상 연락과 중단 결정'),
    'budget': (4, 1000, '□ 예산 편성 방향 / □ 주요 항목의 편성 이유 / □ 근거 확보와 변경 관리. 금액은 주어진 값만 쓴다'),
    'effects': (4, 900, '□ 기대하는 변화(방문객·지역 상권·사투리 인식) / □ 측정과 활용. 달성했다고 단정하지 않는다'),
    'goods': (4, 900, '□ 컨셉과 굿즈의 연결 / □ 선택 품목과 선정 이유 / □ 제작·검수 방식 / □ 현장 운영과 결과 기록. 선택한 시안이 없으면 선정 기준만 쓴다'),
}

SYSTEM = """너는 대구 사투리 축제 '대사투! 페스티벌' 기획안의 설명 글을 쓰는 공공 축제 기획 담당자다.
'자료'에 있는 내용만 사실로 사용한다.

작성 규칙
1. 장마다 첫 줄은 '▶ '로 시작하는 핵심 요약 1~2문장이다.
2. 이어서 줄 표시를 지켜 쓴다: '□ 제목', '○ 항목: 내용', '- 세부 내용'. 한 줄에 하나씩, 표시 없는 긴 문단은 장마다 2개 이하.
3. ○ 항목은 이유와 운영 방법이 드러나는 1~3문장으로 구체적으로 쓴다. 공공기관 기획서의 간결한 평서문(~한다, ~함)을 쓴다.
4. 자료에 없는 숫자(인원·금액·시각·횟수·기간), 기관·업체·사람 이름, 실적, 협약, 법령 조항을 만들지 않는다.
   자료에 없지만 운영에 필요한 제안은 문장 끝에 [제안]을, 정해지지 않은 것은 '협의 예정'이라고 쓴다.
5. 자료의 [가정]·[추정] 표시는 그대로 유지한다.
6. 저장한 조건(conditions)이 다른 어떤 값보다 우선한다. 기간·장소·주최·컨셉·프로그램을 바꾸지 않는다.
7. 표에 있는 값을 문장으로 그대로 되풀이하지 않는다. 같은 문장을 반복해 분량을 늘리지 않는다.
8. 12~16시에는 야외 핵심 프로그램을 두지 않는 원칙을 지킨다. 할매 말투·지역 비하 표현을 쓰지 않는다.
9. 분량이 중요하다. 각 장은 지정한 글자 수 이상(최대 120%)으로 쓴다. □ 마다 ○ 를 2개 이상 두고, ○ 마다 '무엇을 · 왜 · 어떻게 · 누가 확인하는지'를 2~3문장으로 설명한다. 필요한 ○ 아래에는 '- ' 세부 실행 내용을 1~3개 붙인다.
10. 운영 방법·진행 순서·인력 구성·준비물·접수 방식·대안처럼 자료에 없는 실행 내용은 모두 문장 끝에 [제안]을 붙인다.
11. 그늘막·그늘 텐트는 햇빛을 피하는 시설이므로 비를 피하는 대안으로 쓰지 않는다. 우천·강풍 대안은 기상 확인 뒤 축소·연기·중단을 판단하는 것을 먼저 쓰고, 실내 장소는 확정 자료가 없으면 '협의 예정'으로 쓴다.
12. 공공데이터를 인용할 때는 기관 이름과 '몇 년 관측값/언제 기준'을 함께 쓴다. 과거 날씨를 개최 연도의 예보처럼 쓰지 않고, 상가 수를 참여 업체 수로 쓰지 않는다. 8장 폭염에는 날씨 관측값을, 6장 협력에는 상권 자료를 근거로 쓴다.
출력은 JSON 객체 하나다. 키는 요청한 장 키, 값은 그 장의 글(줄바꿈 포함 문자열)이다."""


def facts(plan, conditions, goods):
    f = apply_fixed(normalize_plan(plan))
    values = {TEMPLATE['labels'].get(k, k): f[k] for s in TEMPLATE['sections'] for k in s['fields'] if f.get(k)}
    import public_data_v06 as PD
    return {
        '공공데이터': PD.summary_for_ai(f.get('public')),
        'conditions(저장한 조건)': conditions or {},
        '조건에서 확정된 값': condition_values(conditions),
        '기획안 항목': values,
        '배치 구역': FIXED['map']['zones'][1:],
        '편의시설': [r[1] for r in FIXED['map']['facilities'][1:]],
        '팀 조사 근거': FIXED['form']['evidence'][1:],
        '위험 대응 기준': FIXED['form']['risks'][1:],
        '선택한 굿즈 시안': [{'품목': g['item_name'], '시안 컨셉': g.get('concept'), '캐릭터': g.get('who_txt'), '포즈': g.get('pose_txt'), '규격(제안)': g.get('spec')} for g in (goods or [])[:3]],
    }


def _call(prompt, system):
    from google import genai
    from google.genai import types
    key, model = os.getenv('GEMINI_API_KEY'), os.getenv('GEMINI_MODEL')
    if not key or not model:
        raise RuntimeError('AI 설정이 없습니다.')
    client = genai.Client(api_key=key)
    config = types.GenerateContentConfig(system_instruction=system, temperature=0.4, response_mime_type='application/json', max_output_tokens=16000)
    for attempt in range(4):   # 혼잡(503)·일시 오류는 잠시 쉬었다가 다시 시도한다
        try:
            return client.models.generate_content(model=model, contents=prompt, config=config).text or ''
        except Exception as e:
            if getattr(e, 'code', None) not in (500, 503) or attempt == 3:
                raise
            time.sleep(4 * (attempt + 1))


def _parse(raw):
    t = re.sub(r'^```(?:json)?|```$', '', raw.strip(), flags=re.M).strip()
    a, b = t.find('{'), t.rfind('}')
    if a < 0 or b < 0:
        raise ValueError('AI 응답에서 글을 찾지 못했습니다.')
    return json.loads(t[a:b + 1], strict=False)


def _as_text(value):
    if isinstance(value, list):
        value = '\n'.join(str(v) for v in value)
    return str(value or '').replace('**', '').strip()[:NARR_MAX]


def groups(keys):
    out = {}
    for key, _ in NARRATIVE_CHAPTERS:
        if key in keys:
            out.setdefault(GUIDE[key][0], []).append(key)
    return [out[g] for g in sorted(out)]


SHORT = 0.75   # 목표의 이 비율보다 짧으면 한 번 더 보강한다


def _expand(data, keys, drafts, call):
    titles = dict(NARRATIVE_CHAPTERS)
    ask = '\n\n'.join('- %s (%s): 지금 %d자 → %d자 이상으로 보강. 써야 할 내용: %s\n[지금 글]\n%s' % (k, titles[k], len(drafts[k]), GUIDE[k][1], GUIDE[k][2], drafts[k]) for k in keys)
    return _parse(call('## 자료\n%s\n\n## 보강할 장\n아래 글의 구조와 사실을 유지하면서, 각 ○ 의 이유·실행 방법·확인 방법을 구체적으로 늘리고 빠진 항목을 더한다. 같은 말을 반복하지 않고 새 사실·수치·기관명을 만들지 않는다. 각 장의 전체 글을 다시 준다.\n%s' % (data, ask), SYSTEM))


def write(plan, conditions, goods, keys, call=_call):
    """keys 에 있는 장의 설명 글을 {키: 글}로 돌려준다."""
    titles = dict(NARRATIVE_CHAPTERS)
    data = json.dumps(facts(plan, conditions, goods), ensure_ascii=False)
    out = {}
    for group in groups(set(keys)):
        ask = '\n'.join('- %s (%s, 약 %d자): %s' % (k, titles[k], GUIDE[k][1], GUIDE[k][2]) for k in group)
        result = _parse(call('## 자료\n%s\n\n## 이번에 쓸 장\n%s' % (data, ask), SYSTEM))
        drafts = {k: _as_text(result.get(k)) for k in group if _as_text(result.get(k))}
        short = [k for k, v in drafts.items() if len(v) < GUIDE[k][1] * SHORT]
        if short:
            try:
                longer = _expand(data, short, drafts, call)
                drafts.update({k: _as_text(longer.get(k)) for k in short if len(_as_text(longer.get(k))) > len(drafts[k])})
            except Exception:
                pass   # 보강에 실패해도 먼저 쓴 글은 남긴다
        out.update(drafts)
    return out
