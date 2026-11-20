from pathlib import Path
import json, hashlib, shutil, csv, zipfile, base64
from PIL import Image
import numpy as np
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import HexColor
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
import pypdfium2 as pdfium
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT.parent.parent
SOURCE=BASE/'goods/사투리라벨_캐릭터_18종_v03/사투리라벨_대키미_외지몽_상품시안_v03.png'
for d in ['01_상품이미지','02_디자인시트','03_제작사양서','04_원본조각_18종','05_실물크기_출력확인','99_작업기록/QA']:
    (ROOT/d).mkdir(parents=True,exist_ok=True)
shutil.copy2(SOURCE,ROOT/'01_상품이미지/상품기준원본_v03.png')
im=Image.open(SOURCE).convert('RGB')
sha=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
pdfmetrics.registerFont(TTFont('KR','/System/Library/Fonts/Supplemental/AppleGothic.ttf'))
pdfmetrics.registerFont(TTFont('Latin','/System/Library/Fonts/Supplemental/Arial.ttf'))
NAVY='#10264A'; GREEN='#286448'; GRAY='#637083'
W,H=297*mm,210*mm
PS=ParagraphStyle('body',fontName='KR',fontSize=9.2,leading=14,textColor=HexColor('#26323E'),wordWrap='CJK')
SM=ParagraphStyle('small',parent=PS,fontSize=8,leading=12)
items=[]
texts=['어서 오이소!','밥 묵었나?','단디 챙기라!','와 이래 좋노!','쪼매 쉬었다 가자.','고맙데이!']
xs=[(8,280),(282,516),(519,762),(765,1015),(1017,1276),(1278,1534)]
ys=[(32,278),(308,613),(640,954)]
names=[texts,['별빛 냥인사','궁금 갸우뚱','냥당당','활짝 웃음','졸려 식빵','애교 부비부비'],['반가워 꼬리붕붕','기본 미소','손 칭찬해','신나서 발라당','졸려 꾸벅','감사 갸우뚱']]
for row in range(3):
    for col in range(6):
        row_xs=[(8,280),(282,516),(517,756),(750,1026),(1026,1258),(1259,1534)] if row==2 else xs
        x0,x1=row_xs[col]; y0,y1=ys[row]
        ident=f'{["T","D","O"][row]}{col+1:02}'
        crop=im.crop((x0,y0,x1,y1))
        out=ROOT/f'04_원본조각_18종/{ident}.png'
        crop.save(out,dpi=(300,300))
        items.append(dict(id=ident,name=names[row][col],group=['사투리 라벨','대키미','외지몽'][row],file=out.name,
                          crop=[x0,y0,x1,y1],pixels=list(crop.size),width_mm=round(crop.width*25.4/300,3),height_mm=round(crop.height*25.4/300,3),
                          sha256=hashlib.sha256(out.read_bytes()).hexdigest(),row=row,col=col))

def p(c,txt,x,y,w,small=False):
    obj=Paragraph(txt,SM if small else PS)
    _,h=obj.wrap(w,1000)
    obj.drawOn(c,x,y-h)
    return y-h-7

def txt(c,s,x,y,size=10,color='#111111'):
    c.setFillColor(HexColor(color));c.setFont('KR',size);c.drawString(x,y,s)

def header(c,title,sub,page,total):
    txt(c,title,15*mm,H-20*mm,23)
    txt(c,sub,15*mm,H-29*mm,9,GRAY)
    txt(c,'대키미 × 외지몽  |  18종 분리형 스티커  |  제작기준 v01  |  2026.11.18',15*mm,11*mm,8,GRAY)
    txt(c,f'{page} / {total}',W-30*mm,11*mm,8,GRAY)

def imagefit(c,path,x,y,w,h):
    pic=Image.open(path); s=min(w/pic.width,h/pic.height)
    rw,rh=pic.width*s,pic.height*s
    c.drawImage(ImageReader(pic),x+(w-rw)/2,y+(h-rh)/2,rw,rh,mask='auto')

def table(c,headers,rows,x,y,widths,rowh=10*mm):
    for r,vals in enumerate([headers]+rows):
        xx=x
        for j,val in enumerate(vals):
            c.setFillColor(HexColor('#EAF0F5' if r==0 else ('#FAFBFC' if r%2 else '#FFFFFF')))
            c.setStrokeColor(HexColor('#D9D9D9'));c.rect(xx,y-rowh,widths[j],rowh,fill=1,stroke=1)
            p(c,str(val),xx+3*mm,y-2.2*mm,widths[j]-6*mm,True)
            xx+=widths[j]
        y-=rowh
    return y

def newpdf(path,title):
    c=canvas.Canvas(str(path),pagesize=(W,H),pageCompression=1)
    c.setTitle(title);c.setAuthor('대키미 외지몽 디자인')
    return c

design=ROOT/'02_디자인시트/스티커18종_디자인시트_v01.pdf'
c=newpdf(design,'대키미 외지몽 스티커 18종 디자인시트')
header(c,'스티커 18종 디자인시트','확정 상품 이미지의 외형과 글자를 보존하는 업체 전달용 시각 기준',1,4)
imagefit(c,SOURCE,14*mm,37*mm,184*mm,131*mm)
y=H-45*mm
for title,body in [
    ('구성','사투리 라벨 6종 T01-T06<br/>대키미 6종 D01-D06<br/>외지몽 6종 O01-O06'),
    ('원본 사용 원칙','글자와 캐릭터는 서로 분리한다. 이 PDF에 실린 이미지는 기준 원본을 그대로 잘라 넣었다. 문구 재입력, 유사 폰트 대체, AI 재생성, 캐릭터 재작화를 하지 않는다.'),
    ('규격 기준','본 패키지는 원본을 300dpi로 사용하는 미니 스티커 기준이다. 개별 프레임은 약 20-27mm이며 정확한 크기는 다음 페이지 표를 따른다. 프레임은 재단선이 아니다.'),
    ('우선순위','시각 디자인은 본 PDF와 기준 원본을 따른다. 제작 규격과 재단 조건은 제작사양서에 따른다. 변경이 필요하면 변경 전후 교정본을 제출한다.')]:
    txt(c,title,207*mm,y,12);y=p(c,body,207*mm,y-5*mm,74*mm)-5*mm
c.showPage()

details=[
 ['하늘색 타원 말풍선과 짙은 청색 궁서풍 글자. 말풍선 꼬리까지 보존한다.',
  '크림색 둥근 사각형. 파란 밥그릇과 검은 김 장식의 위치를 보존한다.',
  '연초록 메모 라벨. 상단 노트 구멍 모양과 체크 표시를 보존한다.',
  '연노랑 둥근 햇살형. 짧은 햇살과 경쾌한 글자 배치를 보존한다.',
  '연하늘색 구름형. 두 줄 문구와 마침표를 보존한다.',
  '연분홍 말풍선. 상단 하트 하나와 느낌표를 보존한다.'],
 ['윙크와 손 인사. 뜬 눈의 별빛, 꼬리 리본과 작은 별을 유지한다.',
  '고개 기울임과 모은 손. 원본의 두 별빛 눈과 표정을 그대로 유지한다.',
  '양손을 허리에 둔 자신만만한 자세. 눈 모양과 별 장식을 유지한다.',
  '양팔을 들고 감은 눈으로 웃는 자세. 감은 눈 위에 별빛을 추가하지 않는다.',
  '편안한 식빵 자세. 원본의 바닥 가까운 발 모양, 감은 눈, 리본을 유지한다.',
  '볼 가까이 모은 손, 감은 눈, 홍조, 하트와 분홍 꼬리 리본을 유지한다.'],
 ['한 손을 든 인사. 늘어진 귀와 크림색 꼬리 끝, 흔들림 표시를 유지한다.',
  '기본 서 있는 미소. 검정 별빛 눈, 작은 크림색 주둥이와 배를 유지한다.',
  '앉아서 한 손을 내민 자세. 보이는 손발의 크림색 패드를 유지한다.',
  '옆으로 누워 배를 보이는 자세. 감은 눈과 보이는 발바닥을 유지한다.',
  '앉아 고개를 기울이고 조는 자세. 감은 눈과 짧은 팔다리를 유지한다.',
  '고개를 기울이고 손을 모은 부드러운 감사 표정. 물음표를 넣지 않는다.']]
for row in range(3):
    header(c,['사투리 라벨 6종','대키미 캐릭터 6종','외지몽 캐릭터 6종'][row],
           '이미지는 확대 참조용  |  표기 치수는 원본 조각 프레임의 실제 출력 크기  |  단위 mm',row+2,4)
    for col,item in enumerate(items[row*6:(row+1)*6]):
        cx=15*mm+(col%3)*91*mm; top=H-41*mm-(col//3)*74*mm
        txt(c,f'{item["id"]}  {item["name"]}',cx,top,12)
        imagefit(c,ROOT/'04_원본조각_18종'/item['file'],cx,top-53*mm,39*mm,48*mm)
        y=top-7*mm
        y=p(c,f'프레임 {item["width_mm"]:.2f} × {item["height_mm"]:.2f} mm<br/>{item["pixels"][0]} × {item["pixels"][1]} px / 300dpi',cx+42*mm,y,44*mm,True)
        y=p(c,details[row][col],cx+42*mm,y-2*mm,44*mm,True)
        cr=', '.join(map(str,item['crop']))
        p(c,f'원본 좌표 [{cr}]<br/>좌상단 원점 / 우측·하단 제외',cx,top-55*mm,85*mm,True)
    c.showPage()
c.save()

spec=ROOT/'03_제작사양서/스티커18종_제작사양서_v01.pdf'
c=newpdf(spec,'대키미 외지몽 스티커 18종 제작사양서')
header(c,'스티커 18종 제작사양서','샘플 발주 기준  |  그림을 다시 만드는 문서가 아니라 확정 원본을 그대로 인쇄하기 위한 사양',1,5)
y=H-42*mm
y=p(c,'이 패키지의 기준은 상품원본 v03이다. 디자인시트 PDF에는 18종 이미지가 각각 내장되어 있어 상품이미지와 디자인시트만으로도 외형을 확인할 수 있다. 제작 시에는 동봉한 무손실 PNG 원본 조각을 우선 사용한다. 글자·그림을 다시 만들지 않는다.',15*mm,y,267*mm)
rows=[('제품 구성','사투리 라벨 6종 + 대키미 6종 + 외지몽 6종 / 세트당 18개'),
      ('샘플 형태','A5 가로 대지 210 × 148mm에 18종 반칼 스티커 / 별도 낱장 포장 제외'),
      ('출력 규격','각 원본 조각을 300dpi로 100% 출력 / 약 20-27mm 미니 규격'),
      ('제안 원단','백색 불투명 PP 점착지 약 80μm + 무광 보호 라미네이팅 약 20μm'),
      ('제안 접착','상온의 매끈한 평면용 아크릴계 영구 점착 / 박리지 포함'),
      ('인쇄','디지털 컬러 단면 인쇄 / 흰 원단 사용 / 투명 원단·홀로그램·별색 제외'),
      ('재단','단일 연결 외곽 반칼 / 박리지 유지 / 작은 장식은 본체와 한 조각'),
      ('제작 수량','견적·발주 시 정함 / 본 문서는 수량이나 단가를 확정하지 않음')]
y=table(c,['항목','본 패키지 기준'],rows,15*mm,y-5*mm,[45*mm,222*mm],10.5*mm)
y=p(c,'원단·접착·라미네이팅은 제작용 제안값이다. 제조사는 실제 제품명, 각 층 두께와 적합 공정을 교정본에 기재한다. 원단 변경이나 확대 제작은 발주자 확인 후 진행한다.',15*mm,y-8*mm,267*mm)
p(c,'중요: 현재 파일은 RGB 래스터 기준이며 확정 벡터 칼선·CMYK 교정 데이터는 포함하지 않는다. 이 자료를 그대로 양산용 완성 파일이라고 간주하지 말고, 업체의 분판·칼선 교정을 거친 뒤 초도 실물 샘플을 제작한다.',15*mm,y,267*mm)
c.showPage()

header(c,'원본과 재현 기준','원본 보존  |  글자 재조판 금지  |  임의 보정과 AI 재생성 금지',2,5)
y=H-42*mm
for title,body in [
 ('파일 기준','상품기준원본_v03.png는 1536 × 1024px RGB 이미지다. 18종 조각은 이 원본의 직사각 영역을 무손실로 잘라 저장했다. 알파 투명화, 배경 제거, 확대 보간, 리터칭은 하지 않았다. 프레임 안의 흰 배경과 미세한 회색 그림자도 원본 픽셀에 포함된다.'),
 ('궁서체와 문구','T01 어서 오이소! / T02 밥 묵었나? / T03 단디 챙기라! / T04 와 이래 좋노! / T05 쪼매 쉬었다 가자. / T06 고맙데이!<br/>글자는 생성 이미지에 고정된 궁서풍 래스터 형태다. 특정 설치형 궁서 폰트 파일과 동일하다는 의미가 아니다. 동일한 결과를 위해 원본 이미지 글자를 그대로 사용하고 글꼴 대체·윤곽 재추적·자동 벡터화를 하지 않는다. 줄바꿈·기울기·획 모양·문장부호도 보존한다.'),
 ('캐릭터 보존','대키미는 하늘색 얼굴과 배, 분홍 안쪽 삼각 귀, 분홍 꼬리 리본을 유지한다. 외지몽은 초록 몸, 길고 둥근 늘어진 귀, 작은 크림색 주둥이와 배, 작은 크림색 꼬리 끝을 유지한다. 각 안테나는 줄기 2개와 끝 구슬 2개다. 뜬 눈의 별빛, 감은 눈의 눈꺼풀과 피부 명암을 바꾸지 않는다.'),
 ('패드와 원본 충돌 처리','외형 원칙은 대키미 패드 1+4개, 외지몽 1+3개이며 손바닥·발바닥에만 적용한다. 다만 이미지에 가려져 보이지 않거나 개수를 판독하기 어려운 부분을 업체가 임의로 추가·수정하지 않는다. 오류가 의심되면 해당 부위를 확대 표시해 발주자 확인을 받는다.'),
 ('표면과 색','부드러운 저광택 3D 명암은 평면 인쇄 이미지다. 캐릭터를 실제 입체 엠보싱하거나 눈·리본만 부분 유광으로 처리하지 않는다. 피부의 무늬, 강한 광택, 새 하이라이트를 추가하지 않는다. 백색 PP와 무광 코팅으로 톤을 통일한다.')]:
    txt(c,title,15*mm,y,12); y=p(c,body,15*mm,y-5*mm,267*mm)-6*mm
c.showPage()

header(c,'개별 규격과 해상도','300dpi 원본 크기  |  아래 치수는 재단 크기가 아닌 직사각 이미지 프레임',3,5)
rows=[]
for i in items:
    rows.append([i['id'],i['name'],f'{i["pixels"][0]} × {i["pixels"][1]}',f'{i["width_mm"]:.2f} × {i["height_mm"]:.2f}',i['file']])
table(c,['ID','내용','원본 px','프레임 mm','원본 조각'],rows,15*mm,H-42*mm,[19*mm,69*mm,48*mm,62*mm,69*mm],6.6*mm)
p(c,'계산식: mm = px ÷ 300 × 25.4. 원본 조각의 직사각 흰 여백도 프레임에 포함된다. 실제 재단 외곽 크기는 업체가 작성한 벡터 칼선의 외접 치수로 교정본에 별도 표기한다. 직사각 프레임대로 사각 재단하지 않는다.',15*mm,37*mm,267*mm,True)
p(c,'2배 확대하면 유효 해상도는 150dpi가 된다. 4-5cm급 확대 제작은 이 원본만으로 300dpi를 확보할 수 없다. 단순 업스케일을 고해상도 원본으로 표기하지 않으며, 확대가 필요하면 별도의 고해상도 원화 작업과 재승인이 필요하다.',15*mm,24*mm,267*mm,True)
c.showPage()

header(c,'재단과 인쇄 데이터 작성','재단은 제조사 교정 대상  |  제시값은 본 샘플의 발주 기준이며 일반 공정 보증값이 아님',4,5)
y=H-42*mm
for title,body in [
 ('외곽 칼선','각 조각의 보이는 흰 스티커 테두리를 따라 단일 폐곡선으로 작성한다. 별·하트·동작선·햇살·수면 표시는 본체와 하나로 이어 붙이며 별개 소형 스티커로 분할하지 않는다. T03 상단 노트 구멍은 인쇄 장식이며 내부 타공하지 않는다. 캐릭터의 눈, 귀, 팔다리, 꼬리, 리본과 문자 획을 자르지 않는다.'),
 ('칼선 파일과 여유','제조사는 별도 CutContour 벡터 레이어 또는 별색 경로를 작성하고, 0.25pt 표시선으로 검토 PDF를 제출한다. 칼선은 인쇄되지 않는다. 칼선 주변 흰 여백을 목표 0.8mm 이상 확보한다. 색 면과 핵심 그림이 칼선에 닿으면 원화를 줄이거나 흰 외곽을 넓히는 수정안을 먼저 제출한다. 문자 획 주변 안전 여유는 최소 1mm를 목표로 한다.'),
 ('작은 연결부','안테나·리본·별 장식의 가는 틈은 흰색 외곽으로 연결해 한 번에 떼어지게 한다. 흰색 연결부 폭은 최소 1mm를 목표로 한다. 복잡한 오목부는 제조사 공정에 맞춰 단순화하되 컬러 원화를 침범하지 않는다. 원본과 달라지는 흰 외곽은 확대 교정에서 확인한다.'),
 ('도련과 배치','원본 조각은 도련 완료 데이터가 아니다. 흰 원단을 이용하므로 컬러 원화를 늘려 도련하지 않는다. 업체는 칼선 밖 2mm까지 흰 여유 영역을 마련하고, 서로의 도련 영역이 겹치지 않도록 칼선 간 4mm 이상을 확보한다. 동봉 A5 확인판은 배치와 크기 확인용이며 최종 인쇄판·칼선 파일이 아니다.'),
 ('색 관리와 그림자','RGB 원본을 기준으로 제조사의 인쇄기·원단·코팅에 맞춰 변환한다. 임의의 CMYK 수치나 팬톤 일치를 확정하지 않는다. 모니터와 실물 색은 다를 수 있어 코팅한 실물 샘플로 비교한다. 원본에 있는 미세한 회색 그림자는 현 단계에서는 그림의 일부로 보존한다. 제거·흰색화가 필요하면 비교 교정본으로 승인받는다.'),
 ('허용차와 승인','재단 위치 목표 허용차 ±0.5mm, 크기 목표 허용차 ±0.5mm를 샘플 발주 기준으로 제안한다. 제조사는 이 작은 규격에서 달성 가능한지 먼저 확인한다. 불가능하면 대안 칼선·최소 크기를 제안한다. 승인 전 임의 확대·재작화·재질 변경·양산을 하지 않는다.')]:
    txt(c,title,15*mm,y,12);y=p(c,body,15*mm,y-5*mm,267*mm)-4*mm
c.showPage()

header(c,'교정과 납품 확인','데이터 교정 후 실물 샘플 승인  |  제조사와 발주자가 함께 확인',5,5)
y=H-42*mm
rows=[
 ['01 데이터','18개 ID 모두 존재 / 6개 문구 철자·띄어쓰기·문장부호 일치'],
 ['02 외형','원본 대비 임의 수정 없음 / 글자·캐릭터 분리 / 귀·꼬리·리본·안테나 손실 없음'],
 ['03 규격','300dpi 프레임 100% / 50mm 확인 눈금 정상 / 칼선 외접 치수 기재'],
 ['04 칼선','18개 단일 외곽 / 작은 장식 분리 없음 / 내부 타공 없음 / 칼선 인쇄 없음'],
 ['05 색과 인쇄','화이트 원단 / 무광 코팅 / 원본 대비 색조·명암·검정 눈 가독성 확인'],
 ['06 재단 실물','박리지 손상 없음 / 외곽 들뜸·찢김 없음 / 미세 연결부 박리 가능'],
 ['07 점착','매끈한 대상 면에서 점착·기포·들뜸 확인 / 실제 사용면 적합성 별도 확인'],
 ['08 출고','세트당 18종 각 1개 / 오염·누락·중복 없음 / 발주 수량과 포장 수량 일치']]
y=table(c,['확인 단계','합격 확인 항목'],rows,15*mm,y,[40*mm,227*mm],10*mm)
y=p(c,'제조사 제출물: 18종이 보이는 칼선 중첩 교정 PDF, 칼선 없는 인쇄 교정 PDF, 각 칼선의 외접 크기 목록, 실제 원단·코팅·접착 제품명, 색 변환 프로파일 정보, 코팅한 실물 1세트. 발주자는 데이터와 실물 샘플을 확인한 후 양산을 승인한다.',15*mm,y-8*mm,267*mm)
y=p(c,'보관과 표시: 직사광선·고온다습을 피한다. 본 샘플 기준만으로 실외 내후성, 식품 접촉, 식기세척기 사용, 무잔사 재부착을 표시하지 않는다. 그러한 용도는 원단과 접착제 시험 근거를 별도로 확보한다.',15*mm,y-3*mm,267*mm)
y=p(c,'파일 식별: 상품기준원본_v03.png / 1536 × 1024px<br/>SHA-256: '+sha,15*mm,y-3*mm,267*mm,True)
p(c,'제조사 ____________________  담당자 ____________________  교정일 ____________________<br/>발주자 ____________________  샘플 확인일 ____________________  승인 버전 ____________________',15*mm,y-3*mm,267*mm)
c.showPage();c.save()

# One-to-one sample layout: keep original raster pixels, no resampling or edits.
proof=ROOT/'05_실물크기_출력확인/A5_18종_300dpi_실물크기확인_v01.pdf'
pw,ph=210*mm,148*mm
c=canvas.Canvas(str(proof),pagesize=(pw,ph));c.setTitle('18종 300dpi 실물크기 확인판')
txt(c,'18종 실물크기 확인판',9*mm,ph-9*mm,11)
txt(c,'A5 가로 210 × 148mm  |  실제 크기 100% 출력  |  페이지 맞춤 해제  |  최종 칼선 없음',9*mm,ph-15*mm,7)
for item in items:
    framew=item['width_mm']*mm;frameh=item['height_mm']*mm
    x=(9+item['col']*32)*mm+(32*mm-framew)/2
    center_y=(115-item['row']*38)*mm
    c.drawImage(str(ROOT/'04_원본조각_18종'/item['file']),x,center_y-frameh/2,framew,frameh)
    txt(c,item['id'],(9+item['col']*32)*mm+12*mm,center_y-frameh/2-3*mm,6,GRAY)
c.setStrokeColor(HexColor('#111111'));c.setLineWidth(.7)
c.line(9*mm,9*mm,59*mm,9*mm)
for x in [9,59]:c.line(x*mm,7*mm,x*mm,11*mm)
txt(c,'50mm  확인 눈금',63*mm,8*mm,7)
txt(c,'ID와 눈금은 확인용이며 상품에는 인쇄하지 않음',117*mm,8*mm,6,GRAY)
c.showPage();c.save()

manifest={'version':'v01','date':'2026-11-18','source_file':'01_상품이미지/상품기준원본_v03.png',
          'source_pixels':list(im.size),'source_sha256':sha,'crop_coordinates':'left, top, right exclusive, bottom exclusive; origin top-left',
          'print_dpi':300,'production_status':'sample specification; vendor vector cut paths and physical proof approval required',
          'items':items}
(ROOT/'03_제작사양서/원본좌표_규격_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
with (ROOT/'03_제작사양서/18종_규격목록.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f);w.writerow(['ID','구분','내용','폭px','높이px','프레임폭mm','프레임높이mm','dpi','원본좌표'])
    for i in items:w.writerow([i['id'],i['group'],i['name'],*i['pixels'],i['width_mm'],i['height_mm'],300,','.join(map(str,i['crop']))])
(ROOT/'00_업체전달_읽어주세요.txt').write_text('''대키미 외지몽 분리형 스티커 18종 제작 패키지 v01

1. 먼저 디자인시트 PDF로 상품 외형과 18종을 확인하십시오.
2. 제작사양서 PDF로 인쇄 규격과 재단·교정 기준을 확인하십시오.
3. 상품원본과 개별 PNG를 원본 300dpi 크기로 사용하십시오.
4. 글자 재입력, 폰트 대체, 캐릭터 재작화 또는 AI 재생성을 하지 마십시오.
5. A5 확인판은 100% 실제 크기로 출력하십시오. 50mm 눈금을 자로 확인하십시오.
6. PNG의 직사각 프레임은 재단선이 아닙니다. 최종 벡터 칼선은 업체가 작성하여 승인받으십시오.
7. 현재는 20-27mm급 미니 스티커 사양입니다. 확대하면 해상도가 낮아집니다.
8. 원단과 접착·허용차는 샘플 제안값이며 제조사 적합성 확인 및 실물 승인 후 양산합니다.

본 패키지는 원본 픽셀을 보존하므로 이미지 재생성보다 재현성이 높습니다.
다만 인쇄기·원단·코팅에 따른 색차와 재단 오차가 있어 실물의 완전한 동일성을 보증하지 않습니다.
승인된 실물 샘플을 이후 양산의 색상과 재단 기준으로 보관하십시오.
''',encoding='utf-8')

# Structural and pixel verification.
for i in items:
    out=Image.open(ROOT/'04_원본조각_18종'/i['file']).convert('RGB')
    assert np.array_equal(np.array(out),np.array(im.crop(i['crop']))),i['id']
assert len(items)==18 and len(set(i['id'] for i in items))==18
assert len(PdfReader(design).pages)==4 and len(PdfReader(spec).pages)==5
combined=''.join(p.extract_text() or '' for p in PdfReader(design).pages)
assert all(t in combined for t in texts)
qa=ROOT/'99_작업기록/QA'
for path in [design,spec,proof]:
    doc=pdfium.PdfDocument(str(path))
    for n in range(len(doc)):
        page=doc[n]; bitmap=page.render(scale=1.25).to_pil()
        bitmap.save(qa/f'{path.stem}_{n+1:02}.png')
(ROOT/'99_작업기록/검증결과.txt').write_text('PASS: 원본 SHA-256 기록\nPASS: 18종 PNG 전체 픽셀이 원본 좌표 영역과 일치\nPASS: 디자인시트 4쪽 / 제작사양서 5쪽 / 실물크기 확인판 1쪽\nPASS: 6개 한국어 문구 PDF 내장 확인\n시각 검수용 모든 페이지 렌더 완료\n',encoding='utf-8')
archive=ROOT.parent/(ROOT.name+'.zip')
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for path in ROOT.rglob('*'):
        if path.is_file() and '99_작업기록' not in path.parts:z.write(path,Path(ROOT.name)/path.relative_to(ROOT))
print(json.dumps({'design':str(design),'spec':str(spec),'proof':str(proof),'zip':str(archive),'items':len(items),'sha256':sha},ensure_ascii=False,indent=2))
