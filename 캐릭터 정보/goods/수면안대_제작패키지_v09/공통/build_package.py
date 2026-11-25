from pathlib import Path
import json, base64, html, hashlib

ROOT=Path(__file__).resolve().parent.parent
COMMON=ROOT/'공통'
BODY='M100 0 C40 0 0 10 0 48 C0 80 15 95 48 95 C73 95 84 80 100 80 C116 80 127 95 152 95 C185 95 200 80 200 48 C200 10 160 0 100 0 Z'
PINK='#F3A2B8'; CREAM='#F6EBD8'
CHARS=[dict(key='DK',name='대키미',word='잠와',color='#6DCFF5',text=PINK,photo='대키미_잠와_정면후면_상품이미지_v09.png',ears='삼각 고양이 귀 2개 · 안쪽 분홍',earSize='폭 34 × 노출높이 25 mm',earPositions='왼쪽 x=18~52, 오른쪽 x=148~182; 귀 끝 y=-25',outer='200 × 135 mm (귀·더듬이 포함, 밴드 제외)'),dict(key='OE',name='외지몽',word='졸려',color='#008C3A',text=CREAM,photo='외지몽_졸려_정면후면_상품이미지_v09.png',ears='길고 둥근 강아지 처진 귀 2개',earSize='폭 30 × 길이 82 mm',earPositions='상단 고정점 (15,5), (185,5); 귀가 앞쪽 양옆에 내려옴',outer='210 × 135 mm (처진 귀 돌출 포함, 밴드 제외)')]

def glyphs(c):
    # Font-independent, editable round-stroke construction masters.
    if c['key']=='DK':
        paths=['M10 10 H72 M42 10 L10 44 M42 10 L72 44','M94 8 V46 M94 28 H111','M22 66 H98 V89 H22 Z','M142 32 C142 9 178 9 178 32 C178 55 142 55 142 32 Z','M160 56 V77 M131 77 H181','M203 8 V91 M203 49 H220']
    else:
        paths=['M12 8 H77 M44.5 8 L14 29 M44.5 8 L77 29','M44.5 38 V47 M7 47 H87','M17 62 H78 V76 H17 V92 H81','M120 12 H157 V34 H120 V68 H161','M204 8 V92 M176 32 H204 M176 63 H204']
    return '<g fill="none" stroke="'+c['text']+'" stroke-width="13" stroke-linecap="round" stroke-linejoin="round">'+''.join('<path d="'+p+'"/>' for p in paths)+'</g>'

def lettering(c):
    # Bounds incl. rounded caps: x=0.5..226.5, y=1.5..98.5 (DK), OE x=.5..210.5 y=1.5..98.5.
    return '<g transform="translate(58 28.5) scale('+('0.371681 0.412371' if c['key']=='DK' else '0.4 0.412371')+') translate(-0.5 -1.5)">'+glyphs(c)+'</g>'

def mask(c,back=False):
    col=c['color']; parts=[]
    if back:
        parts += ['<path d="M0 48 C-20 -65 220 -65 200 48" fill="none" stroke="'+col+'" stroke-width="15"/>','<rect x="90" y="-42" width="20" height="17" rx="3" fill="'+col+'" stroke="#304b52" stroke-width="1"/><rect x="95" y="-38" width="10" height="9" rx="1" fill="#e9edef"/>']
    for x in [76,124]:
        parts+=['<path d="M'+str(x)+' 4 L'+str(x)+' -24" stroke="'+col+'" stroke-width="8"/>','<circle cx="'+str(x)+'" cy="-28" r="12" fill="'+col+'"/>']
    if c['key']=='DK':
        parts += ['<path d="M18 12 L22 -25 Q36 -22 52 7 Z" fill="'+col+'"/>','<path d="M148 7 Q164 -22 178 -25 L182 12 Z" fill="'+col+'"/>']
        if not back:
            parts+=['<path d="M26 4 L28 -16 L44 3 Z" fill="'+PINK+'"/>','<path d="M156 3 L172 -16 L174 4 Z" fill="'+PINK+'"/>']
    parts+=['<path d="'+BODY+'" fill="'+col+'" stroke="#36545a" stroke-width="0.6"/>','<path d="'+BODY+'" transform="translate(2 2) scale(.98 .96)" fill="none" stroke="#ffffff" stroke-opacity=".65" stroke-width="0.65" stroke-dasharray="1.5 1.5"/>']
    if c['key']=='OE':
        for trans in ['', 'translate(200 0) scale(-1 1)']:
            parts+=['<g transform="'+trans+'"><path d="M15 5 C3 9 -10 48 -4 72 Q0 90 17 85 C32 78 29 58 27 39 L27 10 Z" fill="'+col+'" stroke="#36545a" stroke-width=".6"/></g>']
    if not back: parts += [lettering(c)]
    else:
        for x in [0,193]: parts+=['<rect x="'+str(x)+'" y="40" width="7" height="15" fill="'+col+'" stroke="#fff" stroke-width=".6"/>']
    return ''.join(parts)

def svg(content,w=1600,h=2200):
    return f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><style>text{{font-family:"Apple SD Gothic Neo","Arial Unicode MS",sans-serif;fill:#23323e}} .small{{font-size:23px}} .label{{font-size:27px;font-weight:600}} .muted{{fill:#657582}}</style><rect width="100%" height="100%" fill="#f8fafb"/>{content}</svg>'

def text(x,y,s,size=25,cls=''):
    return f'<text x="{x}" y="{y}" font-size="{size}" class="{cls}">{html.escape(s)}</text>'

def dim(x1,y1,x2,y2,label,tx=None,ty=None):
    return f'<path d="M{x1} {y1} L{x2} {y2}" stroke="#526674" stroke-width="1.7"/><path d="M{x1-5} {y1-7} L{x1+5} {y1+7} M{x2-5} {y2-7} L{x2+5} {y2+7}" stroke="#526674" stroke-width="1.7"/>'+text(tx if tx is not None else (x1+x2)/2-45,ty if ty is not None else (y1+y2)/2-12,label,22)

def make_sheet(c):
    folder=ROOT/c['name']; photo=folder/c['photo']
    b64=base64.b64encode(photo.read_bytes()).decode()
    s=text(70,72,c['name']+' '+c['word']+' 수면안대 디자인 시트',44)+text(70,112,'V09 · 재현 기준 / 1차 샘플 설계 제안 · 단위 mm · 축척 없음',24,'muted')
    s+='<rect x="60" y="145" width="1480" height="740" rx="18" fill="#fff"/>'
    s+=f'<image x="75" y="160" width="1450" height="675" preserveAspectRatio="xMidYMid meet" xlink:href="data:image/png;base64,{b64}"/>'
    s+=text(345,860,'정면 · 레터링만 적용',24)+text(1070,860,'후면 · 매끈한 동색 안감',24)
    s+=text(70,945,'01  치수와 위치를 고정하는 선도안',32)
    s+='<g transform="translate(140 1130) scale(2.8)">'+mask(c)+'</g>'
    s+=dim(140,1435,700,1435,'본체 200',365,1467)+dim(105,1130,105,1396,'95',60,1270)
    s+=text(175,1500,'앞면 원점 (0,0) = 본체 좌상단 바운딩박스',21)
    s+=text(175,1532,'글자 외곽 84 × 40 / 중심 (100,48.5)',23)
    s+='<g transform="translate(920 1130) scale(2.8)">'+mask(c,True)+'</g>'
    s+=text(950,1467,'밴드 폭 15 / 조절구 20 × 17',23)+text(950,1500,'후면 무지 · 자수 뒷실 완전 차폐',23)
    s+=text(70,1602,'02  색상과 소재',32)
    swatches=[('본체·귀·더듬이',c['color']),('텍스트',c['text']),('안감·밴드',c['color']),('차광 심지','#15171A')]
    for i,(label,color) in enumerate(swatches):
        x=70+i*380
        s+=f'<rect x="{x}" y="1630" width="68" height="68" rx="12" fill="{color}" stroke="#bcc5cb"/>'+text(x+84,1657,label,23)+text(x+84,1688,color,22)
    rows=['겉감: 폴리에스터 마이크로플러시 / 파일 2~3 / 250~320 g/m² 제안',
          '안감: 동색 매끈한 폴리에스터 트리코트 / 120~160 g/m² 제안',
          '구조: 겉감 → 자수 안정지 → 얇은 패딩 → 차광 심지 → 안감',
          '장식: '+c['ears']+' / '+c['earSize'],
          '더듬이: 2개 / 중심 x=76,124 / 끝 원형 지름 24 / 전체 높이 135',
          '자수: 둥근 통통한 형태 / 사진의 부피감 / 별도 SVG 글자 기준',
          '금지: 이목구비, 문장부호, 추가 로고, 후면 글자, 귀·더듬이 수 변경']
    for i,row in enumerate(rows): s+=text(70,1750+i*43,row,24)
    s+=text(70,2102,'브랜드 몸색 HEX 외 보조색·물성·치수는 샘플 제안값. 사진 조명색을 원단 기준색으로 읽지 않음.',22,'muted')
    s+=text(70,2140,'치수·글자 획은 선도안 우선 / 질감·입체감은 상품 사진 우선 / 양산용 패턴·자수 펀칭 검증 전',22,'muted')
    out=folder/(c['name']+'_디자인시트_v09.svg');out.write_text(svg(s),encoding='utf-8')
    master='<svg xmlns="http://www.w3.org/2000/svg" width="200mm" height="135mm" viewBox="0 -40 200 135">'+mask(c)+'</svg>'
    (folder/(c['name']+'_정면_배치기준_1대1_v09.svg')).write_text(master,encoding='utf-8')
    # Text-only vector file includes no installed font dependency; new tracing guide, not licensed original font data.
    art='<svg xmlns="http://www.w3.org/2000/svg" width="84mm" height="40mm" viewBox="0 0 84 40"><g transform="translate(-58 -28.5)">'+lettering(c)+'</g></svg>'
    (folder/(c['word']+'_레터링_84x40mm_선도안_v09.svg')).write_text(art,encoding='utf-8')

COMMON_SPEC='''## 사양의 상태와 적용 순서

2026-11-18 기준. 디자인 고정사항은 대키미 하늘색·분홍색 「잠와」, 외지몽 초록색·크림색 「졸려」, 이목구비 없음, 각 더듬이 2개이다. 기존 「잠온다」「졸리다」 및 졸린 표정 시안은 재현 참조에서 제외한다.

본 패키지는 제작 견적·1차 샘플 개발·AI 재현을 위한 설계 제안이다. 실제 제품 측정치나 사용자 승인된 양산 규격이 아니다. 미확정 치수·소재·후면 구조를 구체적인 제안값으로 설정했다. 제조사는 원단 실물과 1차 봉제 샘플로 치수·착용·차광·자수 품질을 검증한 뒤 패턴과 펀칭 데이터를 확정한다.

재현 우선순위는 최신 사용자 지시 → 사양서의 문구·장식 개수·배치 수치 → 디자인 시트와 SVG 선도안 → 상품 사진의 질감·입체감 순이다. 상품 사진은 AI 생성 시각화이며 자·색차계로 측정할 수 있는 원본이 아니다. 같은 조건이라도 생성 모델은 미세하게 다른 결과를 낼 수 있다. 글자와 실루엣을 정확하게 반복하려면 첨부 도안을 합성·편집 기준으로 사용하고, 사진을 전체 재생성하지 않는다.

## 공통 치수 제안

완성 본체 바운딩박스 200(W) × 95(H) mm. 본체 상단 최상점 y=0, 좌측 끝 x=0, 우측 끝 x=200. x는 오른쪽, y는 아래쪽으로 증가한다. 중심선 x=100. 코 회피 곡선 최상점 (100,80): 바닥 y=95보다 15 mm 올라간다. SVG 베지어 윤곽을 기준으로 한다. 눈구멍은 없다.

귀·더듬이 포함 전체 높이 135 mm, 밴드 제외. 본체 두께 무압축 목표 7±2 mm, 파일 포함이며 자수 돌출 제외. 이 치수는 접촉 압력을 검증한 값이 아니다. 본체 폭·높이 허용차 ±3 mm, 장식 위치 ±2 mm, 자수 중심 ±1.5 mm, 자수 전체 폭·높이 ±1.5 mm를 1차 샘플 목표로 제안한다.

텍스트는 두 제품 모두 완성 외곽 84(W) × 40(H) mm, 중심 (100,48.5). 바운딩박스 x=58~142, y=28.5~68.5. 두 음절을 한 줄로 놓고, 문자별 폭을 강제로 동일하게 만들지 않는다. 둥글고 통통한 버블 스타일과 모서리 라운딩을 유지한다. 별도 SVG는 폰트명이 아닌 획 기반 재현 도안이다. 원래 첨부 이미지의 상용 폰트 파일이나 라이선스를 추정하지 않는다. 사진과 획 도안의 미세 차이는 1차 샘플 검토 시 대조한다. 자수 펀칭 완료 파일(DST/PES/EMB)은 포함하지 않는다.

더듬이 2개: 중심 x=76,124; 원형 끝 중심 y=-28, 완성 지름 24 mm; 줄기 폭 8 mm, 본체와 겹치는 고정 여유를 포함해 y=4까지 연장. 줄기에 철사·단단한 코어를 넣지 않고, 끝 구는 솜을 소량 넣은 부드러운 봉제 구조. 귀·더듬이는 외곽 봉제선에 삽입 고정하며 분리형 접착 장식으로 만들지 않는다.

## 색상 관리

본체 브랜드 기준은 대키미 #6DCFF5, 외지몽 #008C3A. 대키미 귀 안쪽과 글씨의 작업용 보조색 제안은 #F3A2B8, 외지몽 글씨의 크림 보조색 제안은 #F6EBD8. 차광 심지 제안 #15171A이며 완제품 외부에서 보이지 않는다. HEX는 화면 표현용 sRGB 기준이며 원단·실의 염색 지시나 Pantone/실번호와 동치가 아니다. 보조색은 사진을 바탕으로 수치화한 작업 기준이고 공식 IP 승인 색번호가 아니다.

전·후면·귀 뒷면·더듬이·밴드는 해당 캐릭터 몸색 계열로 통일한다. 조절구 역시 동색. 색상은 중립광 아래 실물 원단·자수실 스와치로 맞춘다. 모니터 하이라이트로 생긴 옅은 하늘색/연두색을 새로운 본체 염색색으로 고정하지 않는다.

## 자재와 구조 제안

| 부위 | 1차 샘플 제안 | 보이는 조건 |
|---|---|---|
| 앞판 | 폴리에스터 마이크로플러시, 파일 2~3 mm, 250~320 g/m² | 보송하고 촘촘한 짧은 결, 뻣뻣한 플라스틱 광택 금지 |
| 뒤판 | 동색 매끈한 폴리에스터 트리코트, 120~160 g/m² | 피부 접촉면에 앞판의 긴 털 없음 |
| 완충층 | 얇은 폴리에스터 패딩, 무압축 2~3 mm | 과충전 쿠션처럼 부풀지 않음 |
| 차광층 | 유연한 불투명 검정 폴리에스터 직물, 0.2~0.4 mm 제안 | 외부 노출·밝은 안감 비침 없음 |
| 자수 | 유광이 과하지 않은 폴리에스터 자수실 + 얇은 입체 심 | 원형 풍선 글자처럼 둥글되 봉제물의 실결 유지 |
| 귀·더듬이 | 본체와 동색 겉감, 최소 충전 | 부드럽게 휘고 바늘자국·봉제 경계 자연스러움 |
| 밴드 | 폭 15±1 mm 탄성 밴드, 동색 원단 커버 | 주름 분포 균일, 뒤틀림 없음 |
| 조절구 | 동색 플라스틱 1개, 외곽 약 20×17 mm, 슬롯은 밴드 폭에 맞춤 | 정면 중앙 장식으로 배치하지 않음 |

레이어는 바깥에서 앞판/자수 안정지 → 완충층 → 차광층 → 매끈한 안감 순이다. 자수는 앞판에 먼저 작업하고 뒤판을 마지막에 결합해 뒷실·안정지가 피부에 닿지 않게 한다. 자수 높이 목표는 앞판 바탕에서 1.5~2.5 mm. 획이 서로 붙거나 속공간이 막히지 않도록 펀칭 밀도와 심 두께를 샘플에서 조절한다. 원단의 복슬한 결 때문에 글씨가 묻히지 않도록 수용성 상지 사용 여부를 샘플 업체가 검토한다.

## 후면과 밴드

후면은 동색 무지 안감만 보인다. 글씨, 로고, 얼굴, 앞판 자수 뒷실을 추가하지 않는다. 양옆 밴드 고정 중심은 (0,47.5), (200,47.5), 고정되는 밴드 폭은 y=40~55이다. 시접 안 삽입 길이 15 mm 제안. 끝단 바텍 또는 박스 보강을 겉면 미관과 양립하게 적용한다.

밴드 유효 길이(본체 양옆 고정점 사이, 장착상태, 비신장) 300~420 mm 조절 범위를 제안한다. 본체 폭과 단순 합한 폐곡선 길이는 500~620 mm이나 실제 착용 둘레·압박감은 재질과 곡률의 영향을 받아 동일하지 않다. 성인용 1차 샘플에서 실측 착용 확인 후 확정한다. 재단 길이는 커버 주름·조절구 경로·겹침 길이에 따라 업체가 산출한다. 300~420 mm를 고무밴드 재단 길이로 사용하지 않는다.

후면 촬영에서는 밴드를 위로 아치 모양으로 놓아 안감 전체를 가리지 않는다. 이는 촬영 배치이고 착용 때의 고정 형상이 아니다. 뒷면을 볼 때 좌우 장식은 실제 뒤집힌 방향에 맞는다. 고양이 귀 뒤쪽은 하늘색이며 분홍 안귀가 후면에 반복되지 않는다.

## 봉제 순서와 패턴 전달

1. 앞판 원단 수축·파일 방향을 확인한다. 두 제품 모두 파일은 정면 위에서 아래로 정리한다.
2. 앞판에 텍스트 자수를 먼저 놓고 글자 획·크기·중심을 대조한다.
3. 귀와 더듬이를 봉제·뒤집기·최소 충전하고 좌우 중심 좌표에 맞춘다.
4. 앞판·완충층·차광층·뒤판을 구성한다. 귀·더듬이·밴드 삽입부를 외곽 시접에 고정한다.
5. 외곽 마감, 뒤집기와 창구멍 마감 후 바인딩/눌러박기 형태를 사진처럼 좁고 부드럽게 정리한다.
6. 최종 스팀·털결 정리 후 자수·봉제·조절 기능을 확인한다.

시접 기본 제안 6 mm. 디자인 시트와 1:1 SVG는 완성선이며 재단선이 아니다. 시접·두께 먹힘·원단 늘어남·뒤집기 보정은 패턴사가 추가한다. 외곽 눌러박기 위치는 완성 가장자리에서 약 2.5~3 mm 안쪽, 땀길이 2.5 mm 제안. 사진에 보이는 좁은 외곽 마감의 최종 방식은 1차 샘플로 결정한다. 귀·더듬이·자수의 구조를 확인하지 않은 상태에서 바로 양산 패턴으로 전달하지 않는다.

## 재현에 고정할 항목과 금지사항

항상 고정: 몸색과 텍스트색, 정확한 두 음절, 문장부호 없음, 귀 2개·더듬이 2개, 이목구비 없음, 정면 중앙 자수, 무지 동색 후면, 밴드 1개와 조절구 1개. 사진은 정면을 왼쪽, 후면을 오른쪽에 같은 크기로 놓는다.

금지: 「잠온다」「졸리다」로 되돌리기, 「잠와」의 ㅈ에 덧획을 넣어 ㅊ처럼 만들기, 「졸려」를 「졸리」「졸러」로 바꾸기, 분홍/크림 색상 서로 바꾸기, 눈·코·입·수염 추가, 크림 주둥이 패치 추가, 더듬이 1개/3개, 앞면 글씨를 뒷면에도 반복, 뒤집힌 글씨, 리본·행성·로고 추가, 원단 전체를 새틴으로 바꾸기, 털을 장모로 과장, 부피 큰 인형/베개로 만들기.

## 이미지 촬영과 AI 재현

고정 촬영 레시피: 정면은 좌측, 후면은 우측. 두 본체 바닥선을 맞추고 동일 배율로 배치. 한 캐릭터만 한 이미지에 포함. 가로 2:1 구도, 권장 2400×1200 이상. 따뜻한 무지 아이보리 배경, 부드러운 좌상단 확산광, 얕은 자연 접지 그림자. 모든 귀·더듬이·밴드를 프레임 안에 담고 글씨와 봉제선이 선명해야 한다. 과도한 광각·피사계심도 흐림·광택·CG 윤곽광 금지. 앞·뒤가 같은 제품임을 유지한다.

AI 입력 세트는 캐릭터별 상품 사진 + 디자인 시트 PNG + 해당 제작사양서이다. 도안 입력이 가능한 모델에는 레터링 SVG와 정면 배치 SVG도 함께 넣는다. 사진은 소재·입체감 기준, 시트는 구조·좌표 기준으로 역할을 분리한다. 수정 때는 전체 재생성보다 이미지 편집을 사용하고 변경 부위 외 나머지를 보존하도록 명시한다. 모델 버전·비율·시드 옵션이 제공되면 함께 기록한다. 시드 고정만으로 서로 다른 모델 간 동일 이미지를 보장하지 않는다.

서체 이름만 지시하지 말고 이 패키지의 두 음절 외곽을 유지한다. SVG는 폰트 설치 없이 열리는 획 선도안이며 사진의 자수 폼을 모사한 새 재현 보조자료다. 실제 자수 외곽과 밀리미터 단위로 일치하는 자동 트레이싱·자수 펀칭 데이터는 아니다. 인쇄나 양산처럼 정확한 글자 고정이 필요한 경우 패턴·펀칭 담당자가 이 선도안과 사진을 대조해 승인용 자수 원본으로 정리한다.

## 검수 기준

화면 검수: 글자 유니코드 대조(잠와 U+C7A0 U+C640 / 졸려 U+C878 U+B824), ㅈ의 덧획·교차·잘림 없음, 둥근 글자 속공간 확보, 정면/후면 장식 개수 동일, 후면 무지, 밴드 연결 좌우 대칭, 색상 역할 정확, 제품 잘림 없음. 글자가 틀리면 시각적 분위기가 좋아도 불합격이다.

봉제 샘플 검수: 완성 치수와 자수 위치를 평평하게 놓고 측정, 좌우 균형과 코 회피 곡선 확인, 실뭉침·뜯김·비뚤어진 박음질·겉으로 나온 차광 심지 없음, 더듬이/귀/밴드 고정부 확인, 조절구 작동과 착용 압박 확인. 차광성·세탁 후 수축·이염·보풀은 실제 원단과 완제품으로 검증하며 현재 통과했다고 표시하지 않는다. 세탁라벨 문구는 검증 결과에 맞춰 제조사가 확정한다.

## 패키지 파일과 재사용

캐릭터별 상품이미지 PNG, 디자인시트 SVG/PNG, 1:1 정면 배치 SVG, 84×40 mm 레터링 선도안 SVG, 제작사양서 HTML, AI 재현 프롬프트 TXT를 묶었다. 공통 사양 JSON과 이 문서는 같은 제안값을 사용한다. SVG를 100%로 인쇄할 때만 1:1이며 프린터 페이지 맞춤 기능은 끈다. 별도 재단패턴/DST/PES/실물 컬러칩은 포함하지 않는다.
'''

def char_details(c):
    return f'''## {c['name']} {c['word']} 전용 기준

모델 식별자 {c['key']}-SM-V09. 정면에는 오직 「{c['word']}」 두 음절을 한 줄로 자수 처리한다. 문장부호·이목구비 없음. 본체와 후면 안감·밴드·더듬이 색은 {c['color']}, 글씨는 {c['text']}. {c['ears']}. 귀 완성 치수 제안 {c['earSize']}. 귀 위치: {c['earPositions']}. 전체 외곽 제안 {c['outer']}. 나머지 수치는 공통 치수표를 적용한다.

정면 사진의 질감과 글자 입체감은 시각 기준이다. 후면은 사진처럼 매끈한 무지 동색 안감이며 앞판 자수가 비치지 않는다. 귀 뒤쪽·더듬이 뒤쪽도 몸색으로 연속된다. 더듬이·귀·밴드가 모델마다 생략되거나 추가되지 않도록 한다.
'''

def md_html(md):
    # Small deterministic renderer for local portable spec; tables supported.
    lines=md.splitlines(); out=[]; inlist=False; table=[]
    def flush():
        if table:
            rows=[r for r in table if not set(r.replace('|','').replace(' ','').replace(':',''))<=set('-')]
            out.append('<table>'+''.join('<tr>'+''.join('<'+('th' if i==0 else 'td')+'>'+html.escape(cell.strip())+'</'+('th' if i==0 else 'td')+'>' for cell in row.strip('|').split('|'))+'</tr>' for i,row in enumerate(rows))+'</table>');table.clear()
    for line in lines:
        if line.startswith('|'):table.append(line);continue
        flush()
        if line.startswith('## '):out.append('<h2>'+html.escape(line[3:])+'</h2>')
        elif line.strip():out.append('<p>'+html.escape(line)+'</p>')
    flush();return '\n'.join(out)

CSS='''body{font-family:"Apple SD Gothic Neo","Malgun Gothic",sans-serif;max-width:1060px;margin:48px auto;color:#26343e;line-height:1.8;padding:0 30px}h1{font-size:36px;line-height:1.3}h2{margin-top:42px;border-top:1px solid #dce3e7;padding-top:25px;font-size:25px}p{white-space:pre-line}table{width:100%;border-collapse:collapse;font-size:14px}th,td{border:1px solid #dce3e7;padding:10px;text-align:left}th{background:#f2f5f7}img{max-width:100%;height:auto}.tag{color:#627584}nav a{margin-right:20px}@media print{body{margin:15mm;font-size:10pt}h2{break-after:avoid}img{max-height:230mm;object-fit:contain}table{break-inside:avoid}nav{display:none}}'''

def prompt(c):
    return f'''Reference hierarchy: latest user instructions > specification and design-sheet dimensions > front/back silhouette and lettering SVG > product photo for material, lighting and relief. Generate only {c['name']} ({c['key']}-SM-V09), not both characters. Product front LEFT and same product skin-facing back RIGHT, equal scale and baseline, 2:1 warm ivory studio photograph. Front body 200x95 mm with 15 mm nose recess; total height 135 mm including two round-tip antennae. Body, back lining and strap {c['color']}. {c['ears']}. Front ONLY exact Korean text "{c['word']}" in {c['text']}, no punctuation. Preserve supplied rounded bubble lettering contours, no extra strokes. Text outer bounds 84x40 mm, center x=100,y=48.5 measured from body top-left. Fluffy short-pile 2–3 mm polyester microplush front; smooth same-color tricot back; lightly padded flexible 7 mm panel, no visible embroidery backing. Two antennae centers x=76,124, tip diameter24 mm. Single 15 mm fabric-covered elastic strap fixed to side centers, one same-color adjuster; display loop above back without covering lining. Soft diffuse upper-left light, realistic tiny fur fibers, fine satin embroidery thread relief, subtle contact shadows. NO eyes, mouth, nose, whiskers, blush, muzzle patch, logos, ribbon, punctuation, repeated rear text, extra antennae, inflated cushion appearance. Use image editing to preserve supplied identity and lettering rather than redraw. Photograph is an appearance reference; technical sheet dimensions control geometry. Exact pixel identity is not guaranteed by generative models. For exact typography reuse SVG contours/compositing instead of generating text.\n'''

for c in CHARS:
    make_sheet(c)
    folder=ROOT/c['name']; full=char_details(c)+'\n'+COMMON_SPEC
    page='<!doctype html><html lang="ko"><meta charset="utf-8"><title>'+c['name']+' 수면안대 제작사양서 V09</title><style>'+CSS+'</style><body><h1>'+c['name']+' '+c['word']+' 수면안대 제작사양서</h1><p class="tag">V09 · 2026-11-18 · 1차 샘플 제작 제안 / 양산 검증 전</p><img src="'+c['photo']+'" alt="정면과 후면 상품 이미지">'+md_html(full)+'<h2>디자인 시트</h2><img src="'+c['name']+'_디자인시트_v09.png" alt="디자인 시트"></body></html>'
    (folder/(c['name']+'_제작사양서_v09.html')).write_text(page,encoding='utf-8')
    (folder/(c['name']+'_AI재현프롬프트_v09.txt')).write_text(prompt(c),encoding='utf-8')

data={'version':'V09','status':'first_sample_design_proposal_not_production_verified','date':'2026-11-18','units':'mm','body':{'width':200,'height':95,'thickness_target':7,'thickness_tolerance':2,'nose_recess':15,'finished_contour_svg_path':BODY},'text':{'width':84,'height':40,'center':[100,48.5],'bbox':[58,28.5,142,68.5],'font':'custom_round_stroke_vector_guide_not_identified_commercial_font','embroidery_relief':[1.5,2.5]},'antennae':{'count':2,'center_x':[76,124],'tip_center_y':-28,'tip_diameter':24,'stem_width':8},'strap':{'width':15,'adjustable_effective_length_unstretched':[300,420],'anchors':[[0,47.5],[200,47.5]],'adjuster_count':1,'adjuster_size':[20,17]},'constraints':{'facial_features':False,'punctuation':False,'rear_text':False,'rear_lining':'smooth_same_body_color'},'tolerances':{'body':3,'appendage_position':2,'text_position':1.5,'text_dimensions':1.5},'characters':CHARS,'color_status':{'body':'existing_brand_srgb_reference','pink_and_cream':'proposed_working_srgb_not_official_approved_dye_code'},'limits':['generated_photos_not_scale_measurements','SVG_guide_not_cutting_pattern','lettering_guide_not_embroidery_digitization','model_outputs_not_pixel_identical']}
(COMMON/'공통_제작사양_v09.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
(COMMON/'page_sections.json').write_text(json.dumps({'common':COMMON_SPEC,'characters':[char_details(c) for c in CHARS]},ensure_ascii=False),encoding='utf-8')
links=''.join('<h2>'+c['name']+'</h2><p><a href="'+c['name']+'/'+c['name']+'_제작사양서_v09.html">제작사양서 열기</a> · <a href="'+c['name']+'/'+c['name']+'_디자인시트_v09.png">디자인 시트 PNG</a> · <a href="'+c['name']+'/'+c['photo']+'">정면·후면 상품 이미지</a></p>' for c in CHARS)
(ROOT/'패키지_시작.html').write_text('<!doctype html><html lang="ko"><meta charset="utf-8"><title>대키미 외지몽 수면안대 V09</title><style>'+CSS+'</style><body><h1>대키미 외지몽 수면안대 V09</h1><p>이목구비 없는 대키미 분홍 「잠와」 / 외지몽 크림 「졸려」. 제품별 제작사양서와 디자인 시트를 함께 사용하세요.</p><p>치수와 봉제 구조는 1차 샘플 제안값입니다. AI 사진·선도안은 양산 검증 패턴이나 자수 펀칭 파일이 아닙니다.</p>'+links+'</body></html>',encoding='utf-8')
print('Built specifications, SVG masters and HTML package at',ROOT)
