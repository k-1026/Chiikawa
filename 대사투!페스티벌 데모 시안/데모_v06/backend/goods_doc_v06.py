"""굿즈 제작 계획서(문서 모델)와 기획안의 굿즈 파트를 만든다.
뼈대: 팀 D03 품목 시트(상품 정보·기준 자료·고정/변경/금지·면 배치·치수/소재/공법) + D04 일정 규칙(D-60 역산, 소요 기간은 입력 필요)
      + 점촌점빵길 과업지시서 「Ⅳ 성과품 작성 및 납품」 방식(작성기준·납품 목록·원본자료·정량평가).
규칙: 근거 없는 숫자는 넣지 않는다. 모르는 값은 '입력 필요' 또는 '업체 확인 필요'로 둔다."""
import datetime, json, re
from pathlib import Path

CATALOG_PATH = Path(__file__).resolve().parent.parent / 'goods_catalog_v06.json'
try:
    CATALOG = json.loads(CATALOG_PATH.read_text(encoding='utf-8'))
except Exception:
    CATALOG = {}

NEED = '입력 필요'
VENDOR = '업체 확인 필요'
PB = {'t': 'pagebreak'}


def festival_date(workspace):
    """기획안·조건의 개최 기간에서 첫 날짜를 찾는다. 없으면 None."""
    plan = workspace.get('plan') or {}
    cond = workspace.get('conditions') or {}
    for src in (plan.get('period'), cond.get('period')):
        m = re.search(r'(20\d{2})\D{1,3}(\d{1,2})\D{1,3}(\d{1,2})', str(src or ''))
        if m:
            try:
                return datetime.date(int(m[1]), int(m[2]), int(m[3]))
            except ValueError:
                pass
    return None


def _tbl(rows, hdr='col'):
    return {'t': 'table', 'hdr': hdr, 'rows': rows}


def _p(text):
    return {'t': 'p', 'text': text}


def _note(text):
    return {'t': 'note', 'text': text}


def _h3(text):
    return {'t': 'h3', 'text': text}


GENERIC_CHECKS = [
    ['캐릭터 승인본 사용', '공식 승인 이미지만 사용하고 생김새·색상을 바꾸지 않는다 (D01)', '□ 미확인'],
    ['포즈·표정', '공식 표정·자세 시트의 승인된 포즈인지 확인한다', '□ 미확인'],
    ['로고 규칙', '승인 로고만 쓰고, 이 품목에서 로고를 노출할 면을 정한다', '□ 미확인'],
    ['문구', '승인 문구의 표기와 줄바꿈을 지키고 표준어 뜻풀이는 넣지 않는다 (D01 2-4)', '□ 미확인'],
    ['제3자 권리', '타인의 캐릭터·로고·사진·글꼴을 허락 없이 쓰지 않는다', '□ 미확인'],
    ['안전·인증', '만 13세 이하 대상 여부를 확인하고 KC 해당 여부는 국가기술표준원 안내로 판단한다', '□ 미확인'],
    ['샘플 검수', '색감·재질·부자재·크기를 실물 샘플로 확인한다 (화면색과 인쇄색은 다르다)', '□ 미확인'],
]


def _spec_rows(item_key, info):
    cat = CATALOG.get(item_key)
    if cat and len(cat.get('spec', [])) > 1:
        return cat['spec'], True
    spec = info.get('spec') or VENDOR
    return [['항목', '값 (단위 포함)', '상태', '근거·확인자'],
            ['규격·재질·공법', spec, '디자인 제안값', '작성자 제안. 업체 확인 필요'],
            ['색 재현', '캐릭터 대표색 유지', VENDOR, '샘플 색 확인 필요'],
            ['체결·부자재', VENDOR, VENDOR, '업체 템플릿 필요']], False


def _schedule_rows(festival):
    d60 = (festival - datetime.timedelta(days=60)) if festival else None
    first = ('D-60 = %s [추정] (개최일 %s − 60일)' % (d60.isoformat(), festival.isoformat())) if d60 else ('D-60 (개최일이 정해지면 계산)')
    return [['순서', '마감', '계산', '필요한 입력', '상태'],
            ['①', '홍보 시작일 = 굿즈 사진 첫 공개일', first, '개최일 (기획안)', '기준 확정(담당자 결정 2026-11-20)'],
            ['②', '검수 완료 목표일', '① − 담당자가 정한 여유 기간', '여유 기간', NEED],
            ['③', '입고 목표일', '② − 검수·불량 대응 소요', '담당자 확인', NEED],
            ['④', '발주 완료 마감', '③ − 생산·배송 소요', '업체 확인', NEED],
            ['⑤', '샘플 승인', '④ − 샘플 제작·수정 소요', '업체 확인', NEED],
            ['⑥', '디자인(시안) 확정', '⑤ − 파일 정리·확정 소요', '디자이너 확인', NEED],
            ['⑦', '시안 선택', '현재 단계', '담당자', '진행 중']]


# 시안 합성 코드(goods_compose_v06)가 품목마다 하는 일을 그대로 적은 기록. (구성, 인쇄·제작 대상, 화면 연출용)
LAYOUT = {
    'keyring': ('캐릭터 윤곽을 따라 흰 테두리를 두른 다이컷. 윤곽의 가장 높은 지점에 고리 구멍 탭과 금속 고리를 배치', '흰 테두리를 포함한 캐릭터 다이컷, 고리 구멍 위치', '흐리게 처리한 배경, 그림자'),
    'sticker': ('흰 시트 위에 큰 캐릭터 2개와 작은 캐릭터 4개를 각각 흰 테두리로 배치(일부는 좌우 반전, 조금씩 기울임)', '낱개 스티커 6개와 칼선, 시트', '시트 바깥 바탕색'),
    'poster': ('배경 위에 옅은 흰 막을 덮고 아래쪽에 캐릭터를 배치, 흰 외곽 테두리', '배경·캐릭터·테두리 전체 (배경은 인쇄용으로 다시 제작)', '없음'),
    'ecobag': ('무지 에코백 사진의 가운데 아래 인쇄 영역에 캐릭터를 배치', '캐릭터 그래픽과 인쇄 위치', '에코백 제품 사진, 천 질감 표현'),
    'tshirt': ('무지 티셔츠 사진의 가슴 인쇄 영역에 캐릭터를 배치', '캐릭터 그래픽과 인쇄 위치', '티셔츠 제품 사진, 천 질감 표현'),
    'magnet': ('캐릭터 한 명을 두꺼운 흰 테두리로 두른 다이컷, 약간 기울여 표시', '흰 테두리를 포함한 캐릭터 다이컷', '흐린 배경, 그림자, 기울기'),
    'pinbutton': ('원형 파스텔 바탕에 캐릭터 한 명을 크게 넣고 흰·금속 가장자리를 두름', '원형 앞면(바탕색과 캐릭터), 재단 원', '흐린 배경, 그림자, 금속 가장자리 표현'),
    'griptok': ('원형 배지 형태의 그립 윗면에 캐릭터 한 명을 배치', '원형 윗면 그래픽', '휴대전화 모형, 배경, 그림자'),
    'acrylic_stand': ('흰 테두리를 두른 캐릭터 아크릴 몸체와 아래 받침', '캐릭터 인쇄면, 흰 여백, 받침 형태', '배경, 그림자'),
    'postcard': ('흰 테두리의 가로형 카드 안에 파스텔 바탕과 캐릭터를 아래쪽에 배치', '카드 앞면 전체', '카드 바깥 배경, 그림자, 기울기'),
    'maskingtape': ('파스텔 띠에 캐릭터를 번갈아(좌우 반전 포함) 반복 배치', '반복 패턴 띠', '테이프 롤 연출, 바탕'),
    'blanket': ('무지 담요 사진 위에 캐릭터를 배치', '캐릭터 그래픽과 위치', '담요 제품 사진'),
}
WORN = ('무지 제품 사진 위에 캐릭터를 배치', '캐릭터 그래픽과 인쇄 위치', '제품 사진')


def design_application(info):
    comp, print_part, staging = LAYOUT.get(info['item_key'], WORN)
    return [_tbl([['구분', '내용'],
                  ['시안 구성', comp],
                  ['캐릭터', info.get('who_txt') or '시안 그림 기준'],
                  ['포즈·표정', info.get('pose') or '공식 이미지의 기본 포즈'],
                  ['인쇄·제작 대상', print_part],
                  ['화면 연출용 (제작하지 않음)', staging],
                  ['바꾸지 않는 요소', '캐릭터의 생김새·색상·비례. 공식 원본 이미지를 사용한다']]),
            _note('위 구성은 시안을 만든 합성 방식의 기록입니다. 시안은 화면용(1024px)이라 그대로 인쇄하지 않고, 공식 고해상도 원본으로 인쇄용 파일을 새로 만듭니다.')]


def goods_plan_model(info):
    """info: item_key, item_name, concept, did, image_b64, who, qty, festival_name, host, budget_total, festival(date|None), selected(bool)"""
    key, name = info['item_key'], info['item_name']
    cat = CATALOG.get(key) or {}
    fest, did, qty = info['festival_name'], info['did'], info['qty']
    today = datetime.date.today().isoformat()
    qty_txt = '%s개' % format(qty, ',') if qty else '발주 전 확정'
    who_txt = info.get('who_txt') or {'both': '대키미 + 외지몽', 'daekimi': '대키미', 'oejimong': '외지몽'}.get(info.get('who', 'both'), '대키미 + 외지몽')
    spec_rows, official = _spec_rows(key, info)
    fixed = cat.get('fixed_change_ban') or [['구분', '내용'],
                                            ['고정', '성체 대키미·외지몽의 생김새와 대표색(대키미 하늘색, 외지몽 초록), 승인 문구의 표기, 승인 로고의 구조'],
                                            ['변경 가능', '표정·동작(공식 포즈 안에서), 배치와 크기, 배경색, 소재, 연도별 문구 세트'],
                                            ['금지', '캐릭터 생김새·색상 변경, 승인되지 않은 포즈, 표준어 뜻풀이 삽입, 할매 말투·지역 비하 콘셉트']]
    faces = cat.get('faces') or [['면', '들어가는 그래픽', '로고 노출', '비고'],
                                 ['앞면', '%s (공식 원본 이미지)' % who_txt, '아니오', '시안 번호 %s' % did],
                                 ['뒷면', VENDOR, '아니오', '업체 공법에 따라 결정']]
    purpose = cat.get('purpose') or '%s: 선택한 컨셉에 맞춰 캐릭터를 일상 소품에 적용하는 굿즈 [가설] (검증: 첫 회차 판매·후기)' % name
    code = cat.get('code', '신규 품목 (D03 시트 없음)')
    blocks = []

    # ── 1쪽: 표지·발주 정보·상품 정보
    blocks.append({'h': '발주 정보', 'blocks': [
        _tbl([['항목', '내용'],
              ['발주처(주최·주관)', info.get('host') or NEED],
              ['발주 담당자', NEED],
              ['납품 희망일', NEED],
              ['제작 업체', '견적·선정 전 (업체 3곳 이상 견적 비교)'],
              ['사업 예산(총 사업비)', info.get('budget_total') or NEED]])]})
    blocks.append({'h': '1. 상품 정보', 'blocks': [
        _tbl([['항목', '내용'],
              ['상품 ID', code],
              ['시트 버전', 'v01 (자동 생성 초안)'],
              ['작업일', today],
              ['상태', '초안 → ' + ('선택안 (담당자가 시안 선택)' if info.get('selected') else '검토 중 (시안 선택 전)')],
              ['이번 변경점', '연도 컨셉을 반영한 시안 (캐릭터: %s)' % who_txt],
              ['컨셉', info['concept']],
              ['상품 목적', purpose],
              ['판매 단위', '확인 필요 (낱개 / 세트)']], hdr='row'),
]})
    blocks.append({'h': '', 'blocks': [PB]})

    # ── 2쪽: 기준 자료 + 고정/변경/금지
    blocks.append({'h': '품목군 · SKU · 사이즈 · 제작 수량', 'blocks': [
        _tbl([['구분', '값', '상태'],
              ['품목군 수', '1 (%s)' % name, '확정'],
              ['디자인 옵션(캐릭터)', who_txt, '제안'],
              ['SKU 수', '품목군 × 옵션 × 사이즈 (사이즈·옵션 확정 후 계산)', NEED],
              ['제작 수량', qty_txt, '담당자 입력값' if qty else '미정']])]})
    blocks.append({'h': '2. 기준 자료', 'blocks': [
        _tbl([['항목', '값'],
              ['캐릭터 버전', '성체 (굿즈는 성체 기준 — 담당자 결정 2026-11-17)'],
              ['캐릭터 기준 이미지', '공식 투명 PNG (assets_v06/hero_daekimi.png, hero_oejimong.png). 원본 설정보드는 저장소 「캐릭터 정보/character」 참고'],
              ['포즈 출처', info.get('pose') or '공식 이미지의 기본 포즈'],
              ['로고 기준 파일', '이번 시안에는 노출하지 않음 (포장 카드에서만 노출하는 품목이 많음)'],
              ['문구', '문구 없음 (문구가 필요하면 승인 문구 ID와 원문·줄바꿈을 그대로 적는다)'],
              ['승인 상태', '확인 필요 — 「캐릭터 정보/00_팀원용_현재자료안내」의 승인 상태를 기준으로 한다 ("최종"이라는 이름만으로 승인본으로 쓰지 않는다)']], hdr='row'),
        _note('생김새와 색상은 공식 원본과 같고, 포즈만 해마다 달라질 수 있습니다.')]})
    blocks.append({'h': '3. 고정할 요소 · 변경 가능한 요소 · 금지 사항', 'blocks': [_tbl(fixed)]})

    # ── 3쪽: 시안
    blocks.append({'h': '4. 시안 및 면·그래픽 배치', 'blocks': [
        {'t': 'img', 'src': 'data:image/jpeg;base64,' + info['image_b64'], 'caption': '시안 번호 %s · %s' % (did, name)},
        _p('공식 캐릭터 원본 이미지를 굿즈 모양에 올린 시안입니다. 캐릭터는 AI가 다시 그리지 않았고, 배경·제품 사진만 AI가 만들었습니다.'),
        _note('이 시안은 보기용 이미지(1024px)입니다. 인쇄용 고해상도·벡터 파일은 디자이너가 원본으로 다시 정리해야 합니다 [확인 필요].')]})
    blocks.append({'h': '', 'blocks': [_h3('디자인 적용 방법 (선택한 시안 기준)')] + design_application(info)})
    blocks.append({'h': '', 'blocks': [_h3('면 · 그래픽 배치'), _tbl(faces),
                                        _note('필요한 면은 별도 컷으로 확인합니다. 한 시점으로 모든 면을 검증하지 않습니다.')]})
    blocks.append({'h': '', 'blocks': [PB]})

    # ── 치수·소재·공법, 수량·예산
    blocks.append({'h': '5. 치수 · 소재 · 공법', 'blocks': [
        _tbl(spec_rows),
        _note(('팀 품목 시트(%s)의 값입니다. ' % cat.get('sheet', '')) if official else '품목 시트가 없어 일반 값으로 작성했습니다. 모든 값은 업체 확인 전까지 제안값입니다.'),
        _note('근거 없이 "생산 가능"이라고 쓰지 않습니다. 재단선·도련·최소 획·색상 수는 업체 템플릿을 받은 뒤 확정합니다.')]})
    blocks.append({'h': '6. 수량 · 예산', 'blocks': [
        _tbl([['항목', '내용', '상태'],
              ['제작 수량', qty_txt, '담당자 입력값' if qty else '미정'],
              ['단가', NEED, '업체 3곳 이상 견적 비교'],
              ['제작비 합계', '단가 × 수량', '견적 후 계산'],
              ['예비 수량', NEED, '담당자 결정 (임의 비율을 넣지 않음)'],
              ['다음 해 수량', '이번 회차 판매 기록(KPI)을 근거로 예측', '다음 회차']]),
        _note('첫 해에는 판매 자료가 없어 "미수집"이며, 수량은 팀이 정한 값만 씁니다 (D04).')]})

    # ── 일정·보고
    blocks.append({'h': '7. 제작 · 발주 일정 (홍보 시작일에서 거꾸로 계산)', 'blocks': [
        _tbl(_schedule_rows(info.get('festival'))),
        _note('소요 기간은 업체·담당자가 확인한 값만 씁니다. 임의 날짜를 넣지 않습니다 (D04).')]})
    blocks.append({'h': '8. 보고 · 승인 단계', 'blocks': [
        _tbl([['단계', '시점', '내용', '기록'],
              ['착수', '발주 결정 후', '품목·수량·예산·업체 선정 방향 확인', '착수 메모'],
              ['시안 확정', '⑥ 마감 전', '선택한 시안과 포즈 확정, 인쇄용 파일 정리', '시안 승인 기록'],
              ['샘플 승인', '⑤ 마감 전', '실물 샘플의 색감·재질·부자재 확인', '시안과 샘플 승인본을 한 파일로 보관'],
              ['입고·검수', '③ 마감 전', '수량·인쇄 상태·불량 확인', '검수 기록'],
              ['결과 기록', '행사 후', '판매·재고·반응을 기록해 다음 회차 근거로 사용', '정량평가 자료']]),
        _note('메신저 승인만 믿지 않고, 최종 시안과 샘플 승인본을 한 파일로 모아 보관합니다.')]})
    blocks.append({'h': '', 'blocks': [PB]})

    # ── 검수·납품·성과품
    checks = [['점검 항목', '기준', '확인 여부']] + GENERIC_CHECKS
    blocks.append({'h': '9. 검수 · IP · 안전 점검', 'blocks': [_tbl(checks)]})
    blocks.append({'h': '10. 납품 및 성과품', 'blocks': [
        _h3('10-1. 작성 기준'),
        _p('개조식으로 간결하게 쓰고 표와 사진 위주로 구성한다. 값마다 근거와 상태([확인]·[추정]·[가정])를 적는다. 모든 표기는 한글과 아라비아 숫자, 길이 단위는 mm로 한다.'),
        _h3('10-2. 납품 목록'),
        _tbl([['구분', '내용', '규격', '수량', '비고'],
              ['완제품', name, '위 5장 사양', qty_txt, '개별 포장·포장 방식은 업체와 협의'],
              ['샘플', '본 제작 전 1차 샘플', '동일 사양', NEED, '샘플 승인 후 본 제작'],
              ['인쇄용 원본 파일', '벡터 또는 충분한 해상도 파일 (글꼴은 윤곽선 처리)', 'AI·PDF', '1식', '업체 템플릿 기준'],
              ['시안·승인 기록', '최종 시안과 샘플 승인본을 한 파일로 묶음', 'PDF', '1식', '분쟁 예방'],
              ['검수 기록', '입고 수량, 인쇄 상태, 불량 처리 내역', '표', '1식', '입고 때 작성'],
              ['정량평가 자료', '판매량, 재고, 반응(후기) 기록', '표·그래프', '1식', '다음 회차 근거']]),
        _h3('10-3. 원본 자료 폴더 구성 (편집·활용이 쉽도록 폴더별 저장)'),
        _tbl([['폴더', '들어가는 자료'],
              ['01_시안', '선택 시안, 비교 시안, 캐릭터 기준 이미지 경로'],
              ['02_인쇄용파일', 'AI·PDF 원본, 색상 번호, 글꼴 처리본'],
              ['03_승인기록', '시안·샘플 승인본, 협의 내용, 회의록'],
              ['04_검수·입고', '검수 기록, 사진'],
              ['05_정량평가', '판매·재고·반응 자료, 다음 해 수량 예측 근거']]),
        _h3('10-4. 책임 · 권리'),
        _p('캐릭터·로고·문구의 권리는 팀(발주처)에 있으며, 제3자 권리를 침해하지 않도록 승인된 자료만 사용한다. 납품 후 하자가 발견되면 업체가 재제작 또는 보완한다 (계약서에 명시 필요).')]})
    blocks.append({'h': '', 'blocks': [PB]})

    # ── 미정·출처
    pending = [['번호', '미정 사항', '확인할 곳']]
    n = 1
    for r in spec_rows[1:]:
        if len(r) >= 3 and ('업체 확인' in r[2] or '확인 필요' in r[2]):
            pending.append([str(n), '%s — %s' % (r[0], r[1][:60]), '제작 업체']); n += 1
            if n > 12: break
    for extra in ['제작 업체 선정과 견적 3건', '납품 희망일과 소요 기간', '캐릭터·포즈의 승인 상태', '판매 단위와 SKU 구성', '예비 수량']:
        pending.append([str(n), extra, '담당자']); n += 1
    blocks.append({'h': '11. 미정 사항 · 확인 필요', 'blocks': [_tbl(pending)]})
    blocks.append({'h': '12. 근거 · 참고 자료', 'blocks': [
        _tbl([['구분', '자료', '쓴 곳'],
              ['팀 자료', 'D03 품목 시트 (%s)' % (cat.get('sheet') or '해당 품목 시트 없음'), '1·3·4·5장'],
              ['팀 자료', 'D04 제작·발주 일정 (홍보 시작 = 굿즈 사진 첫 공개 D-60)', '7장'],
              ['팀 자료', 'D01 IP 규칙 검수, D02 굿즈 라인 구성', '9장'],
              ['외부 사례', '점촌점빵길 축제이벤트 기획 및 운영 용역 과업지시서 「Ⅳ 성과품 작성 및 납품」 (구성 방식만 참고)', '10장'],
              ['외부 사례', '미소 「굿즈 시안 만들기 순서」 (6단계·색상 차이·KC 확인 항목만 참고)', '8·9장']]),
        _note('[확인] 시스템에 저장된 시안·컨셉 / [가정] 담당자가 입력한 수량 / [추정] 일반적인 제작 관행·계산한 날짜. 업체와 확정이 필요합니다.')]})

    # blocks → 문서 모델 sections (빈 제목은 이어붙이기)
    sections = []
    for b in blocks:
        if not b['h'] and sections is not None and b['blocks'] and b['blocks'][0].get('t') == 'pagebreak':
            sections.append({'h': '', 'blocks': b['blocks']})
        else:
            sections.append(b)
    return {'title': '%s · %s 제작 계획서' % (fest, name), 'subtitle': '굿즈 제작 계획서 (초안) · A4 기준 6쪽 이상',
            'warn': ['이 문서는 공식 캐릭터 시안에 맞춘 초안입니다. [추정]·[확인 필요]·입력 필요 표시는 업체 견적과 담당자 확인 뒤 확정해 주세요.'],
            'meta': '작성일 %s · 시안 번호 %s' % (today, did), 'sections': sections,
            'foot': '대사투! 페스티벌 · 굿즈 제작 계획서 (초안)'}


def goods_part_blocks(designs, concept, final=False):
    """기획안 본문의 '굿즈 운영 및 성과품 납품' 블록. designs: 선택한 시안 목록 [{item_name, did, who, image_b64, qty?}]"""
    if not designs:
        return [_p('선택한 굿즈 시안이 아직 없습니다. 「05. 굿즈 시안」에서 시안을 만들고 "이 시안 선택"을 눌러 주세요.'),
                _tbl([['구분', '내용'], ['컨셉', concept or NEED], ['굿즈', '선택한 시안 없음']], hdr='row')]
    rows = [['구분', '내용', '규격', '수량', '비고']]
    for d in designs:
        rows.append([d['item_name'], '컨셉 「%s」 · 캐릭터 %s · 시안 %s' % ((concept or NEED)[:40], d['who_txt'], d['did'][:8]),
                     d.get('spec') or VENDOR, d.get('qty') or NEED, '별첨 참고'])
    blocks = [
        _h3('가. 담당자가 선택한 컨셉과 시안'),
        _tbl([['항목', '내용'], ['컨셉', concept or NEED], ['선택 시안 수', '%d종' % len(designs)]], hdr='row')]
    for d in designs[:3]:
        blocks.append({'t': 'img', 'src': 'data:image/jpeg;base64,' + d['image_b64'], 'caption': '%s · 시안 %s' % (d['item_name'], d['did'][:8])})
    blocks += [
        _h3('나. 납품 목록'), _tbl(rows),
        _h3('다. 원본 자료 (폴더별 저장)'),
        _p('시안, 인쇄용 파일(AI·PDF), 시안·샘플 승인 기록, 검수 기록, 정량평가 자료를 폴더로 나눠 함께 제출한다.'),
        _h3('라. 정량평가 항목'),
        _tbl([['지표', '측정 방법', '목표값'], ['굿즈 판매량', '품목·SKU별 판매 수량 기록', NEED], ['재고·소진율', '입고 수량 대비 잔여 수량', NEED], ['방문객 반응', '현장 후기·SNS 반응 수집', NEED]]),
        _note('품목별 상세는 이 문서의 별첨(굿즈 제작 계획서)에 있습니다.')]
    if final:
        for b in blocks:
            if b.get('t') == 'table':
                b['rows'] = [[('발주 전 확정' if str(c).strip() in ('', NEED, VENDOR) else c) for c in r] for r in b['rows']]
    return blocks


def model_to_md(m):
    """문서 모델 → 마크다운 (그림은 제외)."""
    out=['# '+m.get('title',''),'',m.get('subtitle',''),'']
    for w in m.get('warn',[]):out+=['> '+w,'']
    if m.get('meta'):out+=[m['meta'],'']
    for s in m.get('sections',[]):
        if s.get('h'):out+=['## '+s['h'],'']
        for b in s.get('blocks',[]):
            t=b.get('t')
            if t=='table':
                rows=b.get('rows',[])
                if not rows:continue
                cells=lambda r:'| '+' | '.join(str(c).replace('\n','<br>').replace('|','/') for c in r)+' |'
                if b.get('hdr')=='row':
                    out+=['| 항목 | 내용 |','|---|---|']+[cells(r) for r in rows]
                else:
                    out+=[cells(rows[0]),'|'+'---|'*len(rows[0])]+[cells(r) for r in rows[1:]]
                out.append('')
            elif t=='h3':out+=['### '+b.get('text',''),'']
            elif t=='note':out+=['> '+b.get('text',''),'']
            elif t=='p':out+=[b.get('text',''),'']
    if m.get('foot'):out.append('---');out.append(m['foot'])
    return '\n'.join(out)
