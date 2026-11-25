from pathlib import Path
import hashlib, json, shutil
from xml.sax.saxutils import escape
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle, PageBreak, Flowable
from reportlab.lib.utils import ImageReader

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'01_대키미_마그넷_상품이미지_v04.png'
QA=ROOT/'_qa'
pdfmetrics.registerFont(TTFont('KR','/System/Library/Fonts/Supplemental/AppleGothic.ttf'))
NAVY=colors.HexColor('#13334C'); BLUE=colors.HexColor('#6DCFF5'); LIGHT=colors.HexColor('#EDF6FA')
GRAY=colors.HexColor('#536574'); INK=colors.HexColor('#182A38')
W,H=595.276,841.89; CW=W-80
styles={
 'h':ParagraphStyle('h',fontName='KR',fontSize=23,leading=31,textColor=INK,spaceAfter=12),
 'sub':ParagraphStyle('sub',fontName='KR',fontSize=14,leading=21,textColor=NAVY,spaceBefore=10,spaceAfter=7),
 'p':ParagraphStyle('p',fontName='KR',fontSize=9.2,leading=15,textColor=INK,spaceAfter=7,wordWrap='CJK'),
 'sm':ParagraphStyle('sm',fontName='KR',fontSize=8,leading=12,textColor=GRAY,spaceAfter=5,wordWrap='CJK'),
 'cell':ParagraphStyle('cell',fontName='KR',fontSize=8.6,leading=13,textColor=INK,wordWrap='CJK'),
 'th':ParagraphStyle('th',fontName='KR',fontSize=8.6,leading=13,textColor=colors.white,wordWrap='CJK'),
 'prompt':ParagraphStyle('prompt',fontName='KR',fontSize=8.4,leading=13,textColor=INK,spaceAfter=6,wordWrap='CJK'),
}
def p(s,kind='p'): return Paragraph(escape(s).replace('\n','<br/>'),styles[kind])
def table(rows,widths=None):
    data=[[p(str(c),'th' if i==0 else 'cell') for c in r] for i,r in enumerate(rows)]
    t=Table(data,colWidths=widths or [CW*.25,CW*.75],hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),NAVY),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,LIGHT]),('LINEBELOW',(0,0),(-1,0),.3,NAVY)]))
    return t
def tag(s): return p(s,'sm')
def title(num,name,sub): return [tag('DAEGU EOLL ADEUL  /  DK-MAG-01  /  v01  /  2026-11-18'),p(name,'h'),p(sub)]
def image_file(path,width=CW):
    im=Image.open(path); return RLImage(str(path),width=width,height=width*im.height/im.width)
im=Image.open(SRC)
im.crop((107,72,718,853)).save(QA/'front_detail.png')
im.crop((111,487,307,637)).resize((588,450)).save(QA/'paw_detail.png')
SHA=hashlib.sha256(SRC.read_bytes()).hexdigest()

PROMPT='''Use the attached 01_대키미_마그넷_상품이미지_v04.png as the controlling visual reference. Use the design sheet and manufacturing specification as constraints. Preserve the exact adult Daekimi blue alien CAT identity, face, proportions and pose. One full-body front view on the left and the blank back of the SAME flat die-cut product on the right, equal scale. Blue body #6DCFF5, two triangular ears with pink interiors, exactly TWO blue ball-tipped antennae, black eyes with white STAR highlights, small smiling mouth with pink tongue, all-blue muzzle and belly. The raised paw at image-left is a single smooth rounded mitten, no separate human fingers or thumb. Its visible palm has exactly ONE large pink central pad plus exactly FOUR small pink oval pads in an arc above it, FIVE pink shapes total. No pads on hand backs or foot tops. Blue curled tail at image-right with a pink ribbon. One front-only color print on a thin white-backed flat acrylic plate, narrow white border. Shading is printed illustration, never sculpted relief. Back is a plain opaque white REVERSED silhouette of the same front cut-line, tail at image-left, raised paw at image-right. One centered dark charcoal round ferrite magnet visible on the back at the broad head area. No rear character illustration. No dialect, no speech bubble, no logo, no keychain hole, no stand. Off-white neutral backdrop, soft contact shadows, same framing and near-perpendicular camera as reference. Only external labels 정면 and 후면. Retain all unrequested details. Dimensions 55 x 70 mm and rear magnet diameter 16 mm are proposed physical specifications, not measured image facts. For exact artwork reuse the supplied master image; do not invent new illustration details.'''

class DimDiagram(Flowable):
    def __init__(self): super().__init__(); self.width=CW; self.height=263
    def draw(self):
        c=self.canv; k=3.05; x=55; y=23; ww=55*k; hh=70*k
        # reference crop for positioning only, no manufacturing cut contour inferred
        c.drawImage(str(QA/'front_detail.png'),x,y,width=ww,height=hh)
        c.setStrokeColor(NAVY); c.setLineWidth(.65)
        c.line(x-13,y,x-13,y+hh);c.line(x-17,y,x-9,y);c.line(x-17,y+hh,x-9,y+hh)
        c.setFont('KR',9);c.drawString(0,y+hh/2,'70 mm')
        c.line(x,y+hh+12,x+ww,y+hh+12);c.line(x,y+hh+8,x,y+hh+16);c.line(x+ww,y+hh+8,x+ww,y+hh+16)
        c.drawCentredString(x+ww/2,y+hh+18,'55 mm')
        bx=290; by=y; c.setFillColor(LIGHT);c.rect(bx,by,ww,hh,fill=1,stroke=1)
        mx=bx+27.5*k;my=by+(70-31.5)*k
        c.setFillColor(colors.HexColor('#3E4143'));c.circle(mx,my,8*k,fill=1,stroke=0)
        c.setStrokeColor(GRAY);c.setDash(2,2);c.line(bx,my,bx+ww,my);c.line(mx,by,mx,by+hh);c.setDash()
        c.setFillColor(INK);c.setFont('KR',8)
        c.drawString(bx+5,by+hh-14,'후면 배치 좌표 상자')
        c.drawString(bx+5,by+13,'사각형은 칼선이 아님')
        c.drawString(bx+5,my+33,'자석 중심 (27.5, 31.5) mm')
        c.drawString(bx+5,my-39,'원형 자석 지름 16 mm')
        c.setFont('KR',8);c.drawString(55,5,'정면 비례 참고');c.drawString(290,5,'원점은 후면 외접상자 좌상단')

class Section(Flowable):
    def __init__(self): super().__init__();self.width=CW;self.height=165
    def draw(self):
        c=self.canv;x=24;w=250;y=133
        layers=[(4,BLUE,'정면 컬러 인쇄 + 백색 차폐층 / 두께 공정값'),(28,colors.HexColor('#DDEBF0'),'백색 차폐된 아크릴 바디 / 2.0 mm 제안'),(4,colors.HexColor('#A4ADB0'),'접착층 / 0.1 mm 계산용 가정'),(28,colors.HexColor('#414447'),'후면 페라이트 자석 / 2.0 mm 제안')]
        c.setFont('KR',8)
        for i,(h,col,txt) in enumerate(layers):
            yy=y-h; xx=x if i<2 else x+90; lw=w if i<2 else 80
            c.setFillColor(col);c.rect(xx,yy,lw,h,fill=1,stroke=0)
            c.setStrokeColor(GRAY);c.line(xx+lw,yy+h/2,300,yy+h/2)
            c.setFillColor(INK);c.drawString(306,yy+h/2-3,txt)
            y=yy-5
        c.drawString(24,18,'단면 개념도 / 층 두께를 보기 위해 과장 / 축척 없음')

def footer(c,d):
    c.setFont('KR',7.5);c.setFillColor(GRAY)
    c.drawString(40,27,'DK-MAG-01  |  디자인 기준 v04  |  제작 수치 v01 제안  |  양산 승인 전')
    c.drawRightString(W-40,27,str(d.page))
def write(name,story):
    doc=SimpleDocTemplate(str(ROOT/name),pagesize=(W,H),leftMargin=40,rightMargin=40,topMargin=37,bottomMargin=45,title=name,author='대구 얼라들 디자인 제작 패키지')
    doc.build(story,onFirstPage=footer,onLaterPages=footer)

D=[]
D+=title(1,'대키미 마그넷 디자인 시트','대상은 사투리와 말풍선이 없는 대키미 단독 마그넷이다. 상품 이미지 v04의 정면 디자인과 흰색 무지 후면을 기준으로 AI 재현과 제작 검수를 통일한다.')
D+=[image_file(SRC),tag('기준 원본 전체 / 이미지 1536 × 1024 px / 정면 왼쪽, 후면 오른쪽. 아래 정면·후면 글자는 상품 인쇄 대상이 아니다.'),p('사용 범위와 기준 우선순위','sub'),table([['구분','적용 기준'],['디자인 기준','동봉한 상품 이미지 v04. 얼굴, 표정, 포즈, 리본, 질감과 색 관계를 유지한다. 사용자는 이 이미지를 문서 작성 기준으로 지정했다.'],['변경 금지','종·몸색·얼굴 비례·더듬이 2개·별 눈·꼬리 리본·둥근 앞발·젤리패드 1+4.'],['실물 제작 기준','치수와 구조는 제작사양서 v01의 제안값이다. 그림에서 실측한 값이나 제조 검증 결과가 아니다.'],['충돌 처리','기준 이미지의 디자인 + 문서의 명시적 구조 지시를 함께 따른다. 다른 캐릭터 설정 보드나 초기 시안으로 되돌리지 않는다.']]),p('동일 결과를 얻는 방법','sub'),p('정확히 같은 상품 이미지는 원본 PNG를 그대로 재사용한다. AI로 새로 생성하면 미세 차이가 생길 수 있으므로 결과를 이 시트의 항목과 대조한다. 실물은 목업을 인쇄하는 것이 아니라 정면 아트와 칼선 원본을 제작한 뒤 샘플로 확인한다.')]
D+=[PageBreak()]
D+=title(2,'캐릭터와 앞발 고정 규칙','성체 대키미 한 캐릭터만 사용한다. 아기 버전이나 외지몽의 귀·크림 주둥이·패드를 혼합하지 않는다.')
D+=[table([['요소','정면 고정 디자인'],['실루엣과 포즈','큰 둥근 머리, 짧고 통통한 몸·팔다리. 화면 왼쪽 앞발을 들어 인사하고 오른쪽 앞발은 내린다.'],['머리와 더듬이','삼각 고양이 귀 2개와 분홍 귀 안쪽. 파란 구슬형 더듬이 정확히 2개.'],['눈과 표정','큰 검정 눈, 흰 별 모양 주 하이라이트와 작은 보조 반사. 작은 코, 미소 입, 분홍 혀.'],['몸과 꼬리','몸·주둥이·배는 파랑. 흰 주둥이·배 패치 금지. 화면 오른쪽의 말린 파란 꼬리에 분홍 리본.'],['들어 올린 앞발','한 덩어리의 매끈한 둥근 손바닥. 개별 손가락 돌출, 엄지, 손가락 골, 사람 손 모양을 만들지 않는다.'],['젤리패드','큰 중앙 분홍 패드 1개 + 위쪽 호 모양의 작은 분홍 패드 4개. 총 5개. 손등·발등에 패드를 추가하지 않는다.']]),Spacer(1,10)]
pad=Table([[image_file(QA/'paw_detail.png',190),p('앞발 확대 기준\n작은 패드는 4개다. 큰 패드를 포함한 전체 분홍 도형 수는 5개다.\n\n젤리패드와 명암은 표면 인쇄다. 별도 돌출 부품이나 입체 몰드로 만들지 않는다.')]],colWidths=[210,CW-210]);pad.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE')]));D+=[pad]
D+=[p('색상과 인쇄 표현','sub'),table([['부위','색 기준과 처리'],['기본 몸색','IP 기준색 sRGB #6DCFF5. 목업의 하이라이트·그림자를 전부 이 단색으로 덮지 않는다.'],['귀·패드·리본','기준 이미지의 분홍 계열 관계 유지. 공식 별색 수치 미지정. 출력 색은 실물 교정쇄로 맞춘다.'],['눈·후면·자석','눈은 검정 계열, 후면은 불투명 백색, 자석은 짙은 차콜. 자석의 어두운 원을 프린트로 대신하지 않는다.'],['표면','균일한 매끈한 인쇄와 은은한 광택. 털·봉제·실제 볼록 조형·과한 글리터를 추가하지 않는다.']])]
D+=[PageBreak()]
D+=title(3,'정면과 후면 배치 기준','아래 수치는 신규 실물 샘플을 위한 제안이다. 정면·후면이 하나의 물체라는 점을 먼저 고정하고, 앞뒤 외곽선을 따로 생성하지 않는다.')
D+=[DimDiagram(),table([['항목','고정 방식'],['외접 크기','폭 55.0 × 높이 70.0 mm 제안. 더듬이·앞발·꼬리·흰 테두리 포함, 촬영 배경·그림자·글자 제외.'],['정면 외곽선','정면 마스터에서 한 개의 닫힌 칼선을 만든다. 백색 여백 목표 1.5 mm. 가는 더듬이 부분은 파손 위험을 샘플로 검토한다.'],['후면 외곽선','정면 칼선을 좌우 반전한다. 후면에서 꼬리는 왼쪽, 들어 올린 앞발은 오른쪽. 목업 양쪽 윤곽의 미세 차이는 복제하지 않는다.'],['후면 인쇄','캐릭터 뒷모습·얼굴·분홍 리본 등 어떠한 그래픽도 넣지 않는다. 흰색 차폐층으로 정면 인쇄 비침을 억제한다.'],['자석 배치','후면 외접상자 좌상단을 (0,0)으로 정의. 자석 중심 X=27.5 mm, Y=31.5 mm. 지름 16 mm 원판 1개. 제안값.'],['촬영 배치','정면 왼쪽, 후면 오른쪽, 비슷한 높이와 동일 축척. 밝은 미색 배경과 부드러운 접지 그림자. 정면/후면 표기는 제품 밖에만 둔다.']]),p('금지 요소','sub'),p('사투리, 말풍선, 축제명, 로고, 키링 고리·구멍, 거치대, 옷, 추가 소품, 후면 캐릭터 일러스트, 제품 자체의 입체 조형을 넣지 않는다. 참고 사진 속 입체 명암을 실제 제품 두께로 해석하지 않는다.')]
D+=[PageBreak()]
D+=title(4,'AI 재현 지침과 판정','AI에는 상품 이미지 PNG와 디자인 시트 PDF, 제작사양서 PDF 3개를 함께 넣는다. 참고 이미지를 직접 읽을 수 있는 모델을 사용한다.')
D+=[p('복사해서 사용하는 프롬프트','sub'),p(PROMPT,'prompt'),p('출력 후 필수 검사','sub'),table([['판정 항목','통과 기준'],['정체성과 포즈','성체 대키미, 고양이 귀, 더듬이 2개, 별 눈, 파란 배, 오른쪽 리본 꼬리 유지.'],['앞발','손가락 구분 없는 둥근 앞발. 큰 1개와 작은 4개가 분리되어 보임.'],['뒷면','불투명 무지 백색. 앞면 칼선의 좌우 반전 형태, 실제 원형 자석 1개가 머리 중앙부에 보임.'],['상품과 장면','단면 인쇄한 평판 구조. 사투리·말풍선 없음. 글자는 상품 밖에만 있음.'],['오류 처리','필수 항목 하나라도 다르면 재생성 전체 변경보다 해당 부위 편집을 우선한다. 잘못된 결과를 생산 마스터로 쓰지 않는다.']]),tag('원본 식별 SHA-256: '+SHA),tag('원본 파일: 01_대키미_마그넷_상품이미지_v04.png / 02 디자인 시트 v01과 03 제작사양서 v01이 한 세트다.')]
write('02_대키미_마그넷_디자인시트_v01.pdf',D)

S=[]
S+=title(1,'대키미 마그넷 제작사양서','DK-MAG-01 / 단면 컬러 인쇄한 백색 차폐 아크릴 마그넷 / 초도 샘플 의뢰용. 외관 기준은 동봉한 v04 상품 이미지이며, 아래 치수·재료·공차는 제작 제안값이다.')
S+=[image_file(SRC,440),p('제작 기본 사양','sub'),table([['항목','샘플 제작 제안'],['판매 구성','대키미 단독 마그넷 1개. 제품 정면과 후면에 문자·로고 없음. 포장 디자인은 본 범위에서 제외.'],['완성 크기','최대 폭 55.0 × 최대 높이 70.0 mm. 제작 허용차 목표 ±0.5 mm. 원본 종횡비를 크게 왜곡하지 않음.'],['본체','아크릴 2.0 mm 목표, 두께 허용차는 공급업체 규격 확인. 정면 컬러와 백색 차폐층을 적용하고 후면은 백색 무지.'],['인쇄와 마감','정면에만 컬러 표현. UV 인쇄 기준으로 교정. 실제 인쇄면·백색 차폐 적층 순서는 업체 제안과 샘플로 결정. 표면 균일, 절단면 버 제거.'],['자석','짙은 차콜색 페라이트 원판 1개, 지름 16 × 두께 2.0 mm 목표. 다른 재질·수량으로 바꿀 때 샘플 비교 필요.'],['후면 접착','아크릴·페라이트에 적합한 접착제 또는 양면 접착재. 흘러나옴·정면 노출 금지. 재질 적합성과 경화조건은 업체 확인.']]),tag('목업에서 실제 재료나 자력을 판별할 수는 없다. 소재 적합성·부착력·두께·절단 품질은 실물 샘플로 확인한다. 가격·수량·납기는 본 사양서에서 정하지 않는다.')]
S+=[PageBreak()]
S+=title(2,'치수와 후면 자석 조립','좌표 단위는 mm다. 위치는 후면을 정면에서 바라본 상태로 표기한다. 정면 칼선을 반전해 후면 도안을 만들고 같은 외곽선을 사용한다.')
S+=[DimDiagram(),table([['항목','목표와 검사 방법'],['좌표 원점','후면 외접상자의 좌상단 (0,0). X는 오른쪽, Y는 아래쪽.'],['자석 중심','(27.5, 31.5) mm / 배치 허용차 목표 X·Y 각각 ±1.0 mm. 머리 넓은 면에 위치.'],['자석 크기','지름 16.0 mm, 두께 2.0 mm 목표. 자석 공급 공차는 제조사 도면으로 확인 후 발주 기준에 반영.'],['전체 두께','자석 부위에서 약 4.1 mm 예상 = 본체 2.0 + 접착층 0.1 가정 + 자석 2.0. 인쇄막 등 공정 두께 별도. 실측값 아님.'],['외곽선 정합','정면 칼선 마스터 1개 사용. 후면은 좌우 반전. 독립 AI 생성 후면의 미세한 외곽 차이는 그대로 제작하지 않는다.'],['접착과 간섭','원판 전체가 평탄한 후면 안에 들어가야 함. 가장자리 돌출·기울어짐·기포성 들뜸·접착제 번짐 없어야 함.']]),p('조립 순서','sub'),p('① 정면 아트와 닫힌 칼선 승인 → ② 소재·인쇄·백색 차폐 샘플 → ③ 재단과 버 제거 → ④ 후면 청소 및 건조 → ⑤ 위치 지그로 자석 접착 → ⑥ 업체 경화조건 준수 → ⑦ 외관·부착·박리 검사. 조립 중 앞면을 긁지 않도록 보호한다.')]
S+=[PageBreak()]
S+=title(3,'인쇄 파일과 단면 구조','동봉 PNG는 외관 기준용 목업이다. 촬영 배경·그림자·후면 사진·라벨이 포함되어 있으므로 이 사진 전체를 잘라 바로 제품에 인쇄하지 않는다.')
S+=[Section(),table([['전달 레이어','생산 아트 제작 지시'],['ART_FRONT','정면 캐릭터만 분리해 정리. 사진 배경·접지 그림자·정면 글자·후면 그림 제거. 털, 손가락, 후면 아트를 새로 만들지 않음.'],['WHITE','정면 컬러가 뒤로 비치지 않는 백색 차폐층. 업체의 실제 인쇄 적층 구조에 맞추어 작성. 핀홀·반투명 비침 검사.'],['CUT','단일 닫힌 벡터 패스. 별도 레이어와 식별 가능한 별색선 사용. 선색·선폭·파일형식은 업체 템플릿으로 확정.'],['MAGNET_POSITION','후면 배치 지그 전용. 중심과 지름 표시. 이 원·좌표·주석은 상품 인쇄물에 출력하지 않음.'],['REAR','완성 후면은 무지 백색. 반전한 칼선과 자석 위치만 검토. 캐릭터 뒷모습을 그리는 레이어는 만들지 않음.']]),p('해상도와 여백','sub'),p('컬러 아트는 최종 55 × 70 mm 기준 600 ppi 목표(외접 영역 약 1299 × 1654 px), 업체 최소 300 ppi 이상 확인. 단순 확대는 디테일 복원이 아니다. 흰 테두리 목표 1.5 mm를 유지하고, 도련·최소 획·더듬이 최소 연결 폭·급한 곡률은 업체 재단 방식으로 검토한다.'),p('출력과 생산 마스터의 구분','sub'),p('PDF 안의 상품 사진은 1:1 재단 도면이 아니다. AI 이미지 재생성을 생산 칼선이나 색 교정의 대체로 쓰지 않는다. 인쇄용 AI/SVG/PDF와 레이어 분리 원본은 샘플 개발 때 제작해야 하며 이 패키지에 완성 생산 원본으로 포함된 것은 아니다. 샘플의 색과 외곽선을 확인한 뒤 생산 마스터 버전을 고정한다.')]
S+=[PageBreak()]
S+=title(4,'실물 샘플 검수와 변경 관리','디자인과 구조를 함께 확인한다. 아래 수치 검사 기준은 샘플 평가 제안이며 업체와 확인 후 발주 사양으로 고정한다.')
S+=[table([['검사','합격 목표'],['기준 디자인','별 눈·더듬이 2개·리본·둥근 앞발 유지. 손바닥은 큰 패드 1개 + 작은 패드 4개. 손등·발등 패드 없음.'],['앞뒤 구조','정면만 컬러, 후면 무지 백색, 자석 1개. 후면이 앞면의 반전 칼선과 일치. 앞면에 자석 윤곽이 볼록하게 드러나지 않음.'],['치수와 위치','외접 55 × 70 mm 목표 ±0.5 mm. 자석 중심 X=27.5, Y=31.5 mm, 각 ±1.0 mm 목표. 실측값 기록.'],['인쇄','색·선명도·광택을 교정 샘플과 비교. 패드 4+1이 분리되어 읽힘. 번짐·백색 핀홀·벗겨짐·후면 비침 없음.'],['절단과 접촉면','날카로운 버·균열·깨짐·눈에 띄는 황변 없음. 더듬이 연결부와 리본 외곽 손상 없음. 자석이 비뚤거나 들뜨지 않음.'],['부착 유지 시험','깨끗한 수직 도장 강판에 제품 자체 무게 + 추가 하중 20 g 조건으로 24 h 관찰 제안. 미끄러짐·탈락 없음. 강판·온도·하중 부착 방법 기록.'],['접착 내구 확인','실사용 모사 탈부착 100회 제안. 자석 분리·흔들림·접착층 들뜸 없음. 자력 수치나 접착강도 인증을 뜻하지 않음.']]),p('샘플 결과 기록','sub'),table([['기록 항목','업체와 담당자가 작성'],['실측과 소재','폭 ____ mm / 높이 ____ mm / 본체 ____ mm / 총두께 ____ mm\n자석 재질·지름·두께 ____ / 접착재와 경화조건 ____'],['검수와 처리','부착시험 조건·결과 ____ / 100회 탈부착 결과 ____\n수정사항 ____ / 샘플 번호 ____ / 확인일 ____ / 확인자 ____']]),p('AI와 업체에 전달하는 지시','sub'),p('3개 파일을 함께 검토하고 상품 이미지의 외관을 유지한다. 디자인 시트 4쪽의 프롬프트와 필수 검사 기준을 따른다. 제품을 바꾸는 소재·치수·자석·인쇄면 변경은 변경 사유와 전후 비교를 기록한다. 실물 샘플 확인 전에는 양산 승인으로 표시하지 않는다.'),tag('원본 상품 이미지 SHA-256: '+SHA),tag('현재 상태: 디자인 문서 작성 완료 / 제작 수치 제안 / 생산 아트·업체 검토·실물 샘플 확인 전. 이 문서는 안전 인증 또는 성능 인증서가 아니다.')]
write('03_대키미_마그넷_제작사양서_v01.pdf',S)

(ROOT/'_source'/'AI_재현프롬프트.txt').write_text(PROMPT,encoding='utf-8')
(ROOT/'_source'/'manifest.json').write_text(json.dumps({'product_id':'DK-MAG-01','visual_master':'v04','document_version':'v01','source_sha256':SHA,'source_size_px':im.size,'status':'visual reference; proposed sample dimensions; not production-approved','proposed_size_mm':[55,70],'proposed_magnet_center_mm':[27.5,31.5],'proposed_magnet_diameter_mm':16,'files':[x.name for x in ROOT.iterdir() if x.is_file()]},ensure_ascii=False,indent=2),encoding='utf-8')
print('Created package:',ROOT)
