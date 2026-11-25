from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
import pypdfium2 as pdfium

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent.parent
pdfmetrics.registerFont(UnicodeCIDFont('HYSMyeongJo-Medium'))
FONT = 'HYSMyeongJo-Medium'
GREEN = '#174D3A'

def text(c,x,y,s,size=10,color='#263B35'):
    c.setFillColor(HexColor(color)); c.setFont(FONT,size); c.drawString(x,y,s)
def header(c,title,sub):
    c.setFillColor(HexColor(GREEN)); c.rect(0,748,595,94,fill=1,stroke=0)
    text(c,36,794,title,22,'#FFFFFF'); text(c,36,767,sub,10,'#FFFFFF')
def footer(c,n):
    text(c,36,25,'2026-11-18 | ECO-01 v01 | 검토용 초안 · 디자인/문구 미승인',9)
    text(c,545,25,str(n),9)
def section(c,y,title,lines):
    text(c,36,y,title,14,GREEN)
    for i,line in enumerate(lines): text(c,42,y-24-i*19,line,10)
    return y-24-len(lines)*19-19
def save(c,name):
    c.save(); pdf=pdfium.PdfDocument(str(OUT/name))
    for i,p in enumerate(pdf):
        p.render(scale=1.4).to_pil().save(OUT/(name.replace('.pdf',f'_검수_{i+1}.png')))

c=canvas.Canvas(str(OUT/'에코백_제작사양서_검토초안_v01.pdf'),pagesize=(595,842))
header(c,'대화형 에코백 · 제작사양서','대사투 페스티벌 / 대구 얼라들 / 샘플 견적 협의용')
y=section(c,715,'01  제품 제안',["구성: 성체 대키미·외지몽 듀오 1종 / 내추럴 아이보리 + 초록 손잡이",'목적: 축제 기념성과 일상 사용을 함께 고려한 어깨형 캔버스 가방','아래 수치는 모두 작성자 제안값이며, 업체 확정 사양이 아닙니다.'])
y=section(c,y,'02  규격 · 원부자재',["본체 완성치: 가로 360 × 세로 400 × 바닥 폭 80mm",'손잡이: 2개 / 각 전체 길이 600 × 폭 30mm / 노출 길이는 봉제 후 확인','원단: 면 100% 캔버스 12oz/yd²(약 407g/m²) 제안','본체색: 내추럴 아이보리 / 손잡이색: 짙은 초록, 실물 원단칩 선정 필요','구조: 오픈형 입구, 바닥 거싯 / 손잡이 연결부 보강 봉제','안감·지퍼·내부 포켓: 이번 기본안에는 미적용 / 봉제실은 본체 동계열'])
y=section(c,y,'03  인쇄 · 납품 파일',["앞면 컬러 인쇄 1곳 / 뒷면 무지 / 목표 인쇄 범위 230 × 220mm 이내",'위치 제안: 앞면 중심, 본체 상단에서 그래픽 상단까지 약 85mm','샘플 공법: DTF 전사 우선 비교 / 면적감·발색·세탁 후 상태 확인','대키미 #6DCFF5 / 외지몽 #008C3A: 디지털 참고색, 인쇄색 확정 아님','생산 원고: 실제 인쇄 크기 300ppi 이상, 투명 배경 또는 업체 지정 형식','목업은 생성 대기 / 분리 인쇄 원고·벡터·칼선·실측 패턴은 미포함'])
y=section(c,y,'04  샘플 승인 전 확인',["완성치 허용오차 ±10mm, 인쇄 위치 ±5mm를 협의 목표로 제안",'원단 수축·물빠짐·전사 들뜸·마찰 이염·손잡이 봉제는 실물로 확인','세탁 방법·사용하중·인증 및 표시사항은 업체 확인 후 결정','제작 수량·단가·납기·포장·행택·최종 로고 원고: 미정','문구와 지역 어감 확인 → 배치 선택 → 업체 시안 → 실물 샘플 검토'])
footer(c,1); save(c,'에코백_제작사양서_검토초안_v01.pdf')

c=canvas.Canvas(str(OUT/'에코백_디자인시트_검토초안_v01.pdf'),pagesize=(595,842))
header(c,'마이 담아라! · 마음을?','디자인 시트 / 성체 듀오 / 배치 설명용 도식 · 상품 목업 생성 대기')
text(c,44,715,'앞면 · 배치 설명',13); text(c,337,715,'뒷면 · 무지',13)
for x in (55,340):
    c.setStrokeColor(HexColor(GREEN)); c.setLineWidth(16)
    c.roundRect(x+43,608,94,80,30,fill=0,stroke=1)
    c.setFillColor(HexColor('#F4EDDF')); c.setLineWidth(1)
    c.roundRect(x,437,180,200,3,fill=1,stroke=1)
    text(c,x+31,417,'360 × 400 × 80mm',10)
c.setStrokeColor(HexColor('#9DAEA6')); c.setDash(3,3)
c.rect(87,484,115,110,fill=0,stroke=1); c.setDash()
text(c,90,577,'마이 담아라!',12,GREEN); text(c,145,558,'마음을?',11,GREEN)
text(c,93,526,'대키미 + 외지몽',11)
text(c,96,505,'그래픽 생성 대기',9)
text(c,360,532,'인쇄 없음',12)
y=section(c,380,'01  디자인 의도',["캐릭터 대화가 먼저 읽히고, 넉넉한 원단 여백이 남는 일상용 구성.",'대키미는 왼쪽에서 반갑게 인사, 외지몽은 오른쪽에서 고개를 갸웃.','캐릭터 위에 둥근 초록 글씨, 주변에 작은 별만 제한적으로 사용.'])
y=section(c,y,'02  문구 · 브랜드',["대키미: ‘마이 담아라!’ / 제안 의도: 물건과 추억을 많이 담아 가라는 인사",'외지몽: ‘마음을?’ / 사투리를 배우는 친구의 다정한 되물음','두 문구는 신규 제안이며, 지역 담당자 어감 확인과 사용자 선택 필요.','승인 브랜드 로고는 별도 행택에 적용 제안. 이 도식에는 미적용.'])
y=section(c,y,'03  고정할 요소',["성체 기준 유지 / 고양이와 강아지 귀 구분 / 각각 더듬이 2개",'대키미 하늘색 주둥이·분홍 꼬리 리본 / 외지몽 크림 주둥이·배·꼬리 끝','도식의 박스·치수·설명은 인쇄 요소가 아닙니다. 그래픽 크기는 제안값.'])
footer(c,1); c.showPage()
header(c,'캐릭터 기준 · 검수 항목','원본 레퍼런스 / 새 상품 디자인 승인을 의미하지 않음')
refs=[ROOT/'output/design-sheets/daekimi-signature-v01/대키미_표정자세_레퍼런스_v08.png',ROOT/'character/외지몽_성체_표정자세_확정본_v01/외지몽_성체_표정자세_확정레퍼런스_v01.png']
for y,p,label in zip([451,159],refs,['대키미 · 시그니처 표정 SAMPLE 08','외지몽 · 확정 표정·자세 SAMPLE 05']):
    text(c,36,y+265,label,12)
    c.drawImage(ImageReader(str(p)),36,y,width=523,height=250,preserveAspectRatio=True,anchor='c')
text(c,36,127,'검수: 귀·더듬이 수 / 얼굴·꼬리·리본 / 한글 원문 / 원단·인쇄 위치',10)
text(c,36,106,'상품 이미지: 도구 사용 한도로 생성 실패. 재개 시 위 두 원본을 참조할 것.',10)
text(c,36,85,'이 문서는 배치 초안이며 실제 상품 목업·최종 분리 인쇄 원고가 아닙니다.',10)
footer(c,2); save(c,'에코백_디자인시트_검토초안_v01.pdf')
(OUT/'생성상태.txt').write_text('내장 image_gen 사용 시도: usage_limit_reached (429)\n이미지 생성 안 됨. 재사용 안내: 2026-11-19 17:19:17 KST\n컨셉: 아이보리 12oz 면 캔버스, 초록 손잡이, 앞면 성체 대키미와 외지몽 대화형 프린트, 뒷면 무지. 대키미 문구 마이 담아라! / 외지몽 문구 마음을?\n이미지 프롬프트는 본 채팅 도구 호출에 기록됨. 문구와 규격은 미승인 제안.\n',encoding='utf-8')
print(OUT)
