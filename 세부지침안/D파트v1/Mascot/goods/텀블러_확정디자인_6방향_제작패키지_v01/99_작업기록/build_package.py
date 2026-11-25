from pathlib import Path
import json, math, hashlib, shutil, html
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor, Color, white
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import A4
import pypdfium2 as pdfium
from pypdf import PdfReader

BASE=Path(__file__).resolve().parents[1]
FONT='/Library/Fonts/Arial Unicode.ttf'
pdfmetrics.registerFont(TTFont('KR',FONT))
W,H=A4
INK='#273C44'; MUTED='#65737A'; LINE='#D9E3E4'; BLUE='#8DC4E2'; PINK='#EEA2B7'; GREEN='#B4CE6A'; CREAM='#F7E5CE'
VIEWS=[('01_FRONT','정면','0°'),('02_LEFT','왼쪽 측면','-90°'),('03_RIGHT','오른쪽 측면','+90°'),('04_LEFT45','왼쪽 45도','-45°'),('05_RIGHT45','오른쪽 45도','+45°'),('06_BACK','후면','180°')]
SKUS={'DK900':('대키미','900mL','large'),'OM900':('외지몽','900mL','large'),'DK350':('대키미','350mL','small'),'OM350':('외지몽','350mL','small')}
COLORS=[('B01 하늘색',BLUE,'대키미 본체·큰 손잡이·얼굴'),('P01 리본 핑크',PINK,'대키미 밴드·리본·작은 뚜껑/고리'),('G01 연두색',GREEN,'외지몽 얼굴·밴드·작은 뚜껑/고리'),('C01 따뜻한 크림',CREAM,'외지몽 본체·큰 손잡이·주둥이·우주선')]

def write(path,text):
 p=BASE/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf-8')

# Mechanical separation of generated panels, no retouching of product content.
for sku in SKUS:
 folder=BASE/'01_제품사진'/sku
 im=Image.open(folder/f'{sku}_6방향_생성원본.png').convert('RGB')
 iw,ih=im.size
 for i,(code,name,angle) in enumerate(VIEWS):
  col,row=i%3,i//3
  box=(round(col*iw/3)+3,round(row*ih/2)+3,round((col+1)*iw/3)-3,round((row+1)*ih/2)-3)
  im.crop(box).save(folder/f'{sku}_{code}.png')
 # Deterministic contact sheet with Korean captions outside photographs.
 sheet=Image.new('RGB',(1500,1800),'white');d=ImageDraw.Draw(sheet)
 f=ImageFont.truetype(FONT,24);ft=ImageFont.truetype(FONT,34)
 d.text((35,25),f'{sku}  |  {SKUS[sku][0]} {SKUS[sku][1]}  |  6방향 외관 참고',font=ft,fill=INK)
 for i,(code,name,angle) in enumerate(VIEWS):
  col,row=i%3,i//3;x=col*500;y=100+row*820
  pic=Image.open(folder/f'{sku}_{code}.png');pic.thumbnail((450,740))
  sheet.paste(pic,(x+(500-pic.width)//2,y+(740-pic.height)//2))
  d.text((x+35,y+750),f'{i+1:02d}  {name}  {angle}',font=f,fill=INK)
 d.text((35,1750),'AI 외관 시안 / 형상·색상은 승인원본 우선 / 정밀 CAD 아님',font=f,fill=MUTED)
 sheet.save(folder/f'{sku}_6방향_라벨시트.png')

class PDF:
 def __init__(self,path,title):
  self.path=BASE/path;self.c=canvas.Canvas(str(self.path),pagesize=A4);self.title=title;self.n=0;self.pages=[];self.page(title,'기준 패키지 v01 | 실리콘 밴드형 | 4 SKU')
 def page(self,title,sub=''):
  if self.n:self.c.showPage()
  self.n+=1;self.pages.append(title);c=self.c
  c.setFillColor(HexColor('#F7FAFA'));c.rect(0,H-105,W,105,fill=1,stroke=0)
  c.setFillColor(HexColor(INK));c.setFont('KR',19);c.drawString(35,H-42,title)
  c.setFont('KR',9);c.setFillColor(HexColor(MUTED));c.drawString(36,H-64,sub)
  c.setStrokeColor(HexColor(LINE));c.line(35,35,W-35,35)
  c.setFont('KR',8);c.drawString(35,22,'대키미 · 외지몽  |  디자인 승인 / 치수·소재 제안 / 양산 승인 전')
  c.drawRightString(W-35,22,f'{self.n:02d}')
  self.y=H-125
 def wrap(self,text,size,width):
  lines=[]
  for line in str(text).split('\n'):
   acc=''
   for ch in line:
    if pdfmetrics.stringWidth(acc+ch,'KR',size)>width:
     lines.append(acc);acc=ch
    else:acc+=ch
   lines.append(acc)
  return lines
 def p(self,text,size=10,color=INK,gap=10):
  for line in self.wrap(text,size,W-70):
   assert self.y>48,(self.n,'overflow',text)
   self.c.setFillColor(HexColor(color));self.c.setFont('KR',size);self.c.drawString(35,self.y,line);self.y-=size*1.55
  self.y-=gap
 def h(self,t):self.p(t,13,INK,8)
 def image(self,path,x,y,w,h):
  # y is top, preserve image aspect and center within frame.
  im=Image.open(path);r=min(w/im.width,h/im.height);dw,dh=im.width*r,im.height*r
  self.c.drawImage(ImageReader(im),x+(w-dw)/2,y-dh-(h-dh)/2,dw,dh)
 def table(self,rows,widths=None,size=9):
  widths=widths or [130,W-200];x0=35
  for ri,row in enumerate(rows):
   ls=[self.wrap(cell,size,widths[i]-14) for i,cell in enumerate(row)]
   rh=max(len(x) for x in ls)*size*1.5+16
   assert self.y-rh>47,(self.n,'table overflow',row)
   self.c.setFillColor(HexColor('#EEF4F4' if ri==0 else ('#FAFBFB' if ri%2 else '#FFFFFF')))
   self.c.rect(35,self.y-rh,sum(widths),rh,fill=1,stroke=0)
   x=x0
   for i,lines in enumerate(ls):
    self.c.setFont('KR',size);self.c.setFillColor(HexColor(INK))
    for j,line in enumerate(lines):self.c.drawString(x+7,self.y-12-j*size*1.5,line)
    x+=widths[i]
   self.c.setStrokeColor(HexColor(LINE));self.c.line(35,self.y-rh,W-35,self.y-rh)
   self.y-=rh
  self.y-=14
 def save(self):self.c.save()

def gallery(pdf,sku):
 name,vol,size=SKUS[sku];pdf.page(f'{sku} | {name} {vol} 6방향','윗줄: 정면 / 왼쪽 측면 / 오른쪽 측면   ·   아랫줄: 왼쪽 45도 / 오른쪽 45도 / 후면')
 top=H-115;cw=(W-70)/3;ch=300
 for i,(code,label,angle) in enumerate(VIEWS):
  col,row=i%3,i//3;x=35+col*cw;y=top-row*ch
  pdf.image(BASE/'01_제품사진'/sku/f'{sku}_{code}.png',x+4,y,cw-8,260)
  pdf.c.setFont('KR',9);pdf.c.setFillColor(HexColor(INK));pdf.c.drawCentredString(x+cw/2,y-276,f'{label}  {angle}')
 pdf.y=top-2*ch-5
 pdf.p('회전 외관 제안 시안. 정면 원본이 최우선이며, 실제 각도·두께·투영은 3D/CAD 검증 전입니다.',8,MUTED,0)

def dimension_page(pdf,kind):
 large=kind=='large';sku='DK900' if large else 'DK350'
 pdf.page('900mL 외형·배치 제안' if large else '350mL 외형·배치 제안','단위 mm / 명목 용량 확정, 모든 외형 치수는 제조사 확인 전 제안값 / 비례도·비축척')
 top=H-128;pic=BASE/'00_승인기준'/f'{sku}_정면참고.png'
 pdf.image(pic,55,top,190,365)
 # Dimension arrows use overall reference extent only. No implication of calibrated pixels.
 c=pdf.c;c.setStrokeColor(HexColor(MUTED));c.setFillColor(HexColor(INK));c.setFont('KR',9)
 def dim(x1,y1,x2,y2,label):
  c.line(x1,y1,x2,y2)
  if x1==x2:
   c.line(x1-4,y1,x1+4,y1);c.line(x2-4,y2,x2+4,y2);c.saveState();c.translate(x1-7,(y1+y2)/2);c.rotate(90);c.drawCentredString(0,0,label);c.restoreState()
  else:
   c.line(x1,y1-4,x1,y1+4);c.line(x2,y2-4,x2,y2+4);c.drawCentredString((x1+x2)/2,y1+7,label)
 dim(49,top,49,top-365,'전체 315 제안' if large else '전체 200 제안')
 pdf.y=top-10
 # Small right-column descriptions.
 facts=(['본체+뚜껑: 260','빨대 노출: 55 / 전체: 315','상부 지름: 100 / 바닥: 75','손잡이 포함 최대폭: 145','밴드 높이 24 / 두께 1.8','얼굴 중심 Z=190','밴드·리본 중심 Z=125','얼굴 최대 W58 × H55','리본 W30 × H22','우주선 W32 × H22'] if large else ['뚜껑·고리 포함 전체: 200','몸체·숄더: 155 / 캡: 45','본체 지름: 65','캡 지름: 65 / 고리 일체형','밴드 높이 20 / 두께 1.8','얼굴 중심 Z=120','밴드·장식 중심 Z=78','얼굴 최대 W38 × H35','리본 W24 × H18','우주선 W26 × H18'])
 yy=top-10
 for line in facts:c.drawString(285,yy,line);yy-=27
 pdf.y=top-385
 pdf.h('좌표와 적용 규칙')
 pdf.p('Z=0은 제품 바닥 접지면입니다. 얼굴·리본·우주선의 중심은 정면 중심선에 일치합니다. 얼굴 높이는 귀와 더듬이를 포함한 최대 외곽 기준입니다. 같은 크기의 두 캐릭터는 용기 기본 형상을 공유합니다.',10)
 pdf.p('밴드 장식은 밴드 위 낮은 양각으로 제안합니다. 장식 최대 돌출은 밴드 표면에서 1.0~1.5, 얼굴 배지는 용기 표면에서 총 1.5~2.0으로 제안합니다. 6방향 그림의 과장된 측면 두께를 치수로 읽지 마세요.',10)
 pdf.p('900mL/350mL가 외형 치수만으로 검증된 것은 아닙니다. 내통·단열층·뚜껑 침입량·안전 충전선을 반영해 업체가 유효 용량과 치수를 함께 조정해야 합니다.',9,MUTED)

# Machine-readable shared design contract.
spec={'package_version':'v01','approval_scope':'user supplied front appearance, silicone family only','nominal_capacity_ml':[900,350],
 'status':{'visual':'user approved source','six_views':'AI generated reference; not exact CAD projections; user review pending','dimensions':'designer proposal, supplier confirmation required','materials':'proposal only','colors':'digital starting proposals, not Pantone or measured manufacturing colors'},
 'coordinates':{'origin':'bottom center contact plane','axes':{'X':"right in approved front",'Y':'back','Z':'up'},'front_camera':[0,-1,0],'view_order':[{'id':a,'label':b,'azimuth_deg':c} for a,b,c in VIEWS],
 'camera_left':'camera moves to object X negative; front badges appear on image right edge in side view','camera_right':'camera moves to object X positive; large handle near camera, narrow edge-on grip','handle':'large only, X positive, handle plane XZ','front_decoration':'negative Y only','back':'plain, continuous band only'},
 'palette':{n:{'hex':h,'use':use,'status':'proposed sRGB, master image appearance prevails'} for n,h,use in COLORS},
 'dimensions_mm':{'large':{'closed_height_without_straw':260,'exposed_straw':55,'overall_with_straw':315,'upper_diameter':100,'base_diameter':75,'width_with_handle':145,'band_height':24,'band_thickness':1.8,'band_center_z':125,'face_center_z':190,'face_bbox':[58,55],'bow_bbox':[30,22],'ship_bbox':[32,22]},'small':{'overall_height':200,'body_shoulder_height':155,'cap_including_loop':45,'diameter':65,'cap_diameter':65,'band_height':20,'band_thickness':1.8,'band_center_z':78,'face_center_z':120,'face_bbox':[38,35],'bow_bbox':[24,18],'ship_bbox':[26,18]}},
 'skus':{k:{'character':v[0],'capacity_label':v[1],'size':v[2],'master_reference':f'00_승인기준/{k}_정면참고.png','front_only':True} for k,v in SKUS.items()},
 'fixed_rules':['No names or printed portraits','No bottom silicone boots','No cap ears','Clear large lids and straws','Small cat cap and loop pink','Small dog cap and loop leaf green','Dog muzzle cream; dog face green','Cat bow pink; dog ship cream','Spaceship ears join upper dome shoulders, elongated rounded downward; no disconnected blobs'],
 'reproducibility':'Use supplied photos and this spec together; exact pixel identity not guaranteed; use one approved 3D model and calibrated render for exact multi-view projections.'}
write('04_AI재현규칙/design_contract_v01.json',json.dumps(spec,ensure_ascii=False,indent=2))

d=PDF(Path('02_디자인시트/텀블러_4종_디자인시트_v01.pdf'),'대키미 · 외지몽 텀블러 디자인시트')
d.p('승인 디자인을 다른 제작자에게 전달하기 위한 기준서',15)
d.image(BASE/'00_승인기준/승인원본_사용자첨부.png',35,H-170,W-70,335)
d.y=H-525
d.table([['제품 코드','제품 구성','상태'],['DK900 / OM900','대키미 / 외지몽 900mL 손잡이형','명목 용량 확정'],['DK350 / OM350','대키미 / 외지몽 350mL 고리형','명목 용량 확정'],['기준 형태','중간 실리콘 밴드 / 정면 장식만','사용자 승인 원본 우선']],[135,235,W-440],9)
d.p('읽는 순서: 승인 기준 → 배색 → 크기별 배치 → 제품별 6방향 → 장식 확대 → AI 재현 규칙. 이 PDF에는 승인 원본과 4종 6방향이 함께 포함되어 있어 외부 전달 시에도 기준을 확인할 수 있습니다.',9)
d.p('중요: 디자인 승인과 제조 승인은 다릅니다. 이 패키지는 실측 사진·CAD·금형 도면이 아니라 생성형 외관 참고 및 샘플 개발 문서입니다. 새 6방향 시안은 사용자 최종 검토 전입니다.',9,MUTED)

d.page('01 | 승인 범위와 해석 우선순위','과거 머그컵·매달림 피규어·금속 장식 비교안은 이번 확정 기준에 포함하지 않음')
d.table([['구분','적용 규칙'],['1순위','00_승인기준/승인원본_사용자첨부.png와 이후 사용자 지시'],['2순위','본 문서의 고정 규칙. 보이지 않던 후면은 무지 본체와 연속 밴드만'],['3순위','제안 치수·색상·소재. 업체 확인/실물 승인 후 확정값으로 개정'],['4순위','6방향 생성 이미지. 방향·가림 참고이며 1~3순위와 충돌하면 기준 우선']],[90,W-160],10)
d.h('반드시 유지')
for t in ['대키미: 하늘색 본체·얼굴·큰 손잡이, 핑크 밴드와 리본, 작은 뚜껑·고리도 핑크.','외지몽: 크림 본체·큰 손잡이, 연두 얼굴·밴드·작은 뚜껑/고리, 주둥이와 우주선은 크림.','대용량 두 제품: 무색 투명 뚜껑과 빨대. 작은 두 제품: 귀 장식 없는 고리 일체형 나사 뚜껑.','실리콘은 중간 밴드에만. 바닥 커버 없음. 얼굴과 밴드 장식은 정면 한 곳에만.','제품 위 이름·문구·평면 캐릭터 인쇄 없음. 과도한 광택 금속 테두리·매달림 피규어 없음.']:d.p('• '+t,10)
d.h('후면·밴드')
d.p('후면은 몸체 단색 + 장식 없는 밴드입니다. 밴드는 360° 이어지는 탈착 링 구조를 제안하며, 후면 이음선은 넣지 않는 안입니다. 실제 금형 파팅라인·접합 구조는 업체 제안과 샘플 확인 사항입니다.',10)

d.page('02 | 배색·재질의 시각 기준','코드는 재현용 sRGB 시작 제안값 / 조명 없는 소재색 실측치 및 인쇄·도색 확정값 아님')
for name,h,use in COLORS:
 d.c.setFillColor(HexColor(h));d.c.roundRect(35,d.y-45,70,45,5,fill=1,stroke=0)
 d.c.setFillColor(HexColor(INK));d.c.setFont('KR',12);d.c.drawString(121,d.y-12,f'{name}   {h}')
 d.c.setFont('KR',9);d.c.drawString(121,d.y-32,use);d.y-=78
d.h('표면 표현')
d.p('본체: 미세하고 균일한 무광 분체도장 스테인리스 느낌. 밴드·얼굴·장식: 매끈한 무광 실리콘, 낮고 둥근 양각. 뚜껑: 큰 제품은 무색 투명, 작은 제품은 해당 색의 무광 사출 플라스틱. 목 둘레는 헤어라인 스테인리스.',10)
d.p('색 일치 판단은 승인 원본 → 동일 조명 디지털 목업 → 업체 실리콘/도장 색판 → 승인 샘플 순으로 진행합니다. 같은 HEX를 다른 소재에 지정해도 실물색이 같아지지는 않습니다. Pantone·CMYK 값은 임의 확정하지 않습니다.',10)
d.p('밴드·얼굴·작은 캡의 연두색은 같은 색군으로 맞춥니다. 외지몽 크림 주둥이는 본체와 경계가 보이게 얼굴 위 연두 바탕 안에 넣습니다. 대키미 리본색은 밴드·작은 뚜껑과 통일합니다.',10)

dimension_page(d,'large');dimension_page(d,'small')
for sku in SKUS:gallery(d,sku)

d.page('09 | 장식 상세와 부착 위치','형태는 승인 원본, 아래 확대는 원본에서 발췌 / 별도 벡터·금형 원본은 제작 전 작성 필요')
master=Image.open(BASE/'00_승인기준/승인원본_사용자첨부.png')
details=[('대키미 얼굴',(210,275,370,423)),('외지몽 얼굴',(575,275,780,426)),('핑크 리본',(235,485,343,565)),('크림 우주선',(622,483,735,565))]
for i,(label,box) in enumerate(details):
 p=BASE/'00_승인기준'/f'장식상세_{i+1:02d}.png';master.crop(box).save(p)
 x=35+(i%2)*265;y=H-125-(i//2)*180;d.image(p,x,y,245,140)
 d.c.setFont('KR',10);d.c.setFillColor(HexColor(INK));d.c.drawString(x+8,y-158,label)
d.y=H-500
d.p('얼굴: 두 개의 구슬형 더듬이, 네 갈래 별 눈 표현, 짧은 닫힌 입. 대키미 삼각 귀와 외지몽 늘어진 귀를 혼동하지 않습니다. 외지몽 주둥이는 크림 인레이로 구분합니다.',10)
d.p('우주선: 둥근 돔과 한 줄의 창 윤곽, 더듬이 2개. 귀 모양 엔진은 돔 위쪽 양옆에서 끊김 없이 이어져 아래로 내려옵니다. 끝은 길쭉하게 둥글고, 분리된 원형 덩어리로 만들지 않습니다. 사실적 유리창·조명·해치·다리는 넣지 않습니다.',10)
d.p('작은 배지의 6방향 생성본에는 축약과 두께 차이가 있습니다. 금형/벡터 제작은 승인 원본 확대를 따라 다시 그린 뒤 별도 승인을 받아야 합니다. 생성 PNG를 자동 트레이싱한 결과를 곧바로 금형 원본으로 사용하지 않습니다.',9,MUTED)

d.page('10 | 재현·촬영·검수 규칙','AI와 3D 제작자 모두에 적용 / 개별 6방향 프롬프트는 04_AI재현규칙 폴더')
d.table([['항목','기준'],['방향','정면 0°, 카메라 왼쪽 -90° / 오른쪽 +90°, 왼쪽 앞 -45° / 오른쪽 앞 +45°, 후면 180°'],['좌표','정면 화면 오른쪽 +X, 뒤쪽 +Y, 위쪽 +Z. 카메라 정면은 -Y. 좌우는 카메라 이동 기준'],['큰 손잡이','제품 +X에 고정. 정면은 오른쪽, 후면은 왼쪽. 오른쪽 측면에서 손잡이가 가까워져 얇은 세로 그립으로 보임'],['작은 고리','정면·후면에서 구멍 보임. 양측면에서는 고리의 두께가 보이며 넓은 구멍을 정면처럼 그리지 않음'],['정면 장식','전면 -Y에만 1개씩. 회전하면 원근·가림이 변함. 측면/후면에 새 얼굴·배지 추가 금지'],['공통 촬영','흰색 배경, 5500K 상당 중립 확산광, 긴 초점/정투영에 가까운 시선, 같은 크기 제품끼리 스케일·기준선 고정']],[90,W-160],9)
d.h('사진과 이 문서만 전달할 때')
d.p('이 PDF 자체에 승인 원본·배색·치수 제안·6방향이 들어 있습니다. 개별 사진을 더하면 목표 컷을 지정하기 쉽습니다. 지정한 제품만 같은 외형으로 재현하고 각도만 바꾸도록 요청합니다. 색·비율을 사진마다 새로 추정하지 않습니다.',10)
d.h('복사 가능한 공통 지시문')
d.p('첨부 디자인시트의 승인 원본을 최우선으로 [제품코드]를 재현한다. 크기별 치수 제안과 배치좌표를 따른다. 정면 얼굴·배지는 각각 한 곳에 고정하고 후면에는 복제하지 않는다. 큰 손잡이와 작은 고리는 회전 시 같은 물체의 투영으로 보인다. [방향] 외에는 색·형태·재질·장식을 변경하지 않는다. 이름·바닥 밴드·뚜껑 귀·매달림 장식·인쇄 캐릭터를 추가하지 않는다.',10)
d.p('완전히 동일한 픽셀 결과는 보장하지 않습니다. 정확한 각도·두께·부품 일치가 필요하면 단일 승인 3D 모델, 재질 파일, 카메라와 렌더 설정을 함께 고정해야 합니다.',9,MUTED)
d.save()

m=PDF(Path('03_제작사양서/텀블러_4종_샘플제작사양서_v01.pdf'),'대키미 · 외지몽 샘플 제작사양서')
m.p('업체 견적 · 기성 용기 검토 · 1차 샘플 의뢰용',15)
m.image(BASE/'00_승인기준/승인원본_사용자첨부.png',35,H-170,W-70,300)
m.y=H-490
m.table([['상태','의미'],['사용자 확정','실리콘 밴드형 4종 외관, 명목 900mL / 350mL, 정면 장식만'],['제작자 제안','치수, sRGB 색 코드, 소재/조립 공법, 부품 두께, 검수 목표'],['업체 회신 필요','기성 몰드 적합성, 실제 용량, 도장·실리콘 색판, 내구/누수, 단가·금형·MOQ'],['본 문서 아님','양산 승인서 / 공인 시험성적서 / 식품접촉 적합성 확인서 / CAD 금형 도면']],[100,W-170],9)
m.p('제작 시작 전: 디자인시트와 본 사양서를 함께 확인하고, 기존 용기의 실제 도면/샘플을 우선 제출해주세요. 형상 변경이 필요하면 변경 전후 치수와 외관 영향을 제안해 승인받습니다.',10)

m.page('01 | 모델·치수·배치 회신 기준','전 항목 제조사 확인 전 제안값. 단위 mm. 그림은 비축척 외관 참고')
m.table([['항목','900mL 두 모델','350mL 두 모델'],['코드','DK900 / OM900','DK350 / OM350'],['전체 높이','315 (빨대 포함)','200 (고리 포함)'],['닫힌 높이','260 (빨대 제외)','200'],['본체·숄더/캡','본체+목 245 / 뚜껑 15','155 / 캡·고리 45'],['지름·최대폭','상부 100 / 바닥 75 / 손잡이 포함 145','본체·캡 65'],['밴드','높이 24 / 두께 1.8 / 중심 Z125','높이 20 / 두께 1.8 / 중심 Z78'],['얼굴','최대 58×55 / 중심 Z190','최대 38×35 / 중심 Z120'],['리본 / 우주선','30×22 / 32×22','24×18 / 26×18'],['장식 돌출','밴드 표면에서 1.0~1.5 제안','밴드 표면에서 1.0~1.5 제안'],['얼굴 총두께','용기 표면에서 1.5~2.0 제안','용기 표면에서 1.5~2.0 제안']],[110,190,W-370],9)
m.p('용량은 안전 충전선을 기준으로 업체가 측정하고, 가득 채운 용량과 사용 가능 용량을 각각 회신합니다. 목표 용량과 외형이 충돌하면 단열층·뚜껑·내통을 반영한 수정 치수를 제안해주세요. 상기 치수에 대한 수학적 용적 검증은 아직 수행되지 않았습니다.',10)
m.p('치수 검수 제안: 승인된 샘플 기준 전체 높이/외경 ±1.0, 장식 중심 ±1.0, 밴드 수평 편차 ±1.0을 시작 협의값으로 사용합니다. 나사·밀폐·부품 끼움 공차는 업체 설계값과 시험 결과로 별도 확정합니다.',9,MUTED)

m.page('02 | 부품별 소재·공법 제안','소재 등급·배합·두께·성적서는 제조사 확인 후 확정. 재질은 외관 이미지로 인증되지 않음')
m.table([['부품','제안 소재/공법','업체 확인'],['내·외통','내통 SUS304 제안 / 이중 진공 단열 구조','합금 증빙, 판 두께, 용접, 유효 용량, 열성능'],['본체 외관','외통 무광 분체도장, 캐릭터별 단색','도막/부착력, 색판, 세척/마찰 내구'],['큰 손잡이','색상 사출 폴리머 제안, 용기 연결 구조는 업체 설계','내하중, 체결부, 기성품 활용 가능성'],['큰 뚜껑','무색 투명 코폴리에스터 등 적합 소재 제안','투명성, 내열/세척 조건, 패킹, 누수'],['빨대','무색 투명 식품접촉용 수지 제안, 탈착 가능','재질, 끝단 마감, 길이/지름, 세척'],['작은 캡·고리','색상 PP 계열 제안 / 고리 일체형','고리 하중, 나사, 캡 정렬, 밀폐 패킹'],['중간 밴드','탈착형 실리콘 폐곡선 링, 무광, 두께 1.8 제안','경도 Shore A 45~55 협의, 신축·복원·미끄럼'],['리본/우주선','밴드 일체 낮은 양각. 우주선은 크림 2색 성형 제안','2색 성형/결합, 얇은 더듬이/귀 연결부 내구'],['얼굴 배지','별도 얇은 실리콘 성형. 외지몽 주둥이 크림 2색','부착·밀봉·박리, 작은 코/눈 표현 한계'],['패킹','탈착 세척 가능한 실리콘 패킹 제안','식품접촉 자료, 조립방향, 교체성']],[80,220,W-370],8.5)
m.p('표의 소재와 경도는 견적 비교를 위한 제안이며 확정 발주 사양이 아닙니다. 공급사는 판매 지역·용도에 필요한 적합성 자료와 시험 범위를 회신해주세요.',9,MUTED)

m.page('03 | 장식·조립·세척 구조','정면 장식과 기능부의 간섭 방지 / 착탈 부품과 고정 부품을 구분')
for head,body in [
 ('중간 밴드','본체 중간에 한 개만 적용합니다. 아래쪽으로 늘려 탈착하는 폐곡선 링을 제안합니다. 큰 텀블러의 손잡이 하단 체결부와 밴드 상단이 간섭하지 않도록 기성 용기 치수로 확인합니다. 후면 장식·파팅 돌출·바닥 부츠는 넣지 않습니다.'),
 ('밴드 장식','대키미 리본은 밴드와 같은 핑크. 외지몽 우주선은 연두 밴드 위 크림 낮은 양각으로 제안합니다. 우주선 귀는 돔 상부에서 아래로 이어지는 일체 연결 형태입니다. 매달리는 부품·분리된 원형 귀·실제 창문 부품은 사용하지 않습니다.'),
 ('얼굴 배지','용기 정면에 고정하는 별도 실리콘 배지를 제안합니다. 도장면과 실리콘을 접합할 수 있는 접착/프라이머 및 가장자리 밀봉 구조를 업체가 제시해주세요. 양면테이프나 일반 접착제가 충분하다고 가정하지 않습니다. 박리·세척·물 고임 검증 전 양산하지 않습니다.'),
 ('작은 뚜껑 방향','닫힌 상태에서 고리 평면이 정면 배지 평면과 평행하도록 맞추는 것을 시각 목표로 합니다. 나사 시작점·패킹 압축에 따른 종단 각도 구현은 미확정입니다. 달성이 어려우면 회전 고리 또는 별도 캡 구조를 변경안으로 제시하고 승인받습니다.'),
 ('세척과 사용','밴드·패킹·빨대가 분리되는 구조를 우선 제안합니다. 배지 접합 틈, 리본 뒤, 우주선 더듬이 아래 등에 오염이 고이지 않도록 곡면과 모서리 처리를 제안해주세요. 허용 세척 온도와 식기세척기 사용 가능 여부는 시험 후 지정합니다.')]:
 m.h(head);m.p(body,10)

m.page('04 | 1차 샘플 확인표','시험 조건·표본수·판정값은 발주 전 합의. 아래는 공급사 검증 요청 목록이며 검증 결과 아님')
m.table([['항목','확인·회신 요청'],['외형·배치','기성 용기 치수 도면과 실측. 얼굴/밴드 중심, 밴드 수평, 손잡이 간섭, 뚜껑 정렬'],['용량·중량','사용 가능/만수 용량 구분. 완제품 건조중량, 물을 채웠을 때 총중량'],['밀폐','작은 나사형은 휴대 시 역전·흔들림 누수 시험조건 제안 및 결과. 큰 빨대형은 완전 밀폐로 표시하지 않음'],['열 성능','시험 전후 물 온도, 실내온도, 뚜껑 상태, 시간과 반복수 제안. 검증 전 보온/보냉 시간 광고 금지'],['밴드 고정','건조/젖은 손의 그립감, 회전/밀림, 탈착과 복원, 손잡이와 간섭'],['장식 접합','얼굴 박리, 크림 인레이 분리, 리본 꼬리·우주선 귀/더듬이 파손·인장'],['기능 내구','고리·손잡이의 하중, 캡 개폐, 패킹 반복 조립, 넘어짐/낙하 조건 협의'],['세척·위생','오염 잔류, 패킹 접근성, 배지 가장자리 물 고임, 이염·냄새·마찰·도장 손상'],['색상','도장·실리콘·캡의 실물 색판. 밝은 곳과 실내에서 색군 일치, 투명 뚜껑 착색 여부'],['공급 자료','접촉 부품의 소재·판매 지역별 적합성 자료, 조립도, 세척 안내, 추적/품질 문서']],[100,W-170],9)
m.p('식품접촉 적합성, 내열·누수·보온보냉 성능은 생성 이미지나 본 문서로 보증하지 않습니다. 공급사 자료와 실물 샘플 검증을 완료한 후 제품 표시·판매 사양을 확정합니다.',9,MUTED)

m.page('05 | 견적·샘플 회신 요청서','아래 빈칸은 미작성 상태가 맞습니다. 업체 회신으로 채우고 개정 이력을 남깁니다.')
m.table([['회신 항목','업체 작성'],['업체/담당/회신일','________________________________________'],['적용 가능한 기성 용기','900mL: ______________  350mL: ______________'],['실측 H / D / 손잡이폭','900mL: ______________  350mL: ______________'],['사용가능/만수 용량·중량','________________________________________'],['소재·도장·실리콘·투명수지','________________________________________'],['얼굴 부착/밴드 성형 공법','________________________________________'],['캡 정렬·밀폐 구현','________________________________________'],['단가(수량별) / MOQ','________________________________________'],['금형·색상별 추가비','________________________________________'],['샘플비·일정 / 양산 납기','________________________________________'],['시험 계획·비용·자료','________________________________________'],['불가 항목·변경 제안','________________________________________'],['승인 샘플 코드 / 버전','________________________________________']],[160,W-230],9)
m.p('진행 순서: 기성 용기/도면 회신 → 치수·색판·접합안 승인 → 배지/밴드 벡터·CAD 승인 → 1차 샘플 → 시험/수정 → 승인 실물 봉인 → 양산 조건 확정. 본 문서를 받은 것만으로 금형·양산 발주가 승인되는 것은 아닙니다.',10)
m.save()

# Editable plain-text companion and standalone HTML mirror of the spec contract.
intro='''대키미·외지몽 텀블러 제작 패키지 v01

1. 확정 기준: 00_승인기준/승인원본_사용자첨부.png. 이번 패키지는 실리콘 밴드형이며 금속 비교안은 제외.
2. 사용자 확정: 대키미/외지몽 각 900mL와 350mL, 정면 장식만, 큰 손잡이 정면 오른쪽, 후면 무지.
3. 새 6방향 PNG는 AI 외관 시안이며 실사 촬영본 또는 검증된 CAD 회전도가 아님. 정면 원본 외형 우선.
4. 01_제품사진: 4종 x 6컷=24개별 PNG, 4개 생성원본, 4개 라벨시트. 방향은 카메라 이동 기준.
5. 02_디자인시트 PDF: 원본·배색·배치좌표·치수 제안·6방향·장식 확대·재현 규칙 포함.
6. 03_제작사양서 PDF: BOM·공법·접합·세척·검증 요청·견적 회신표. 양산/법규 적합성/성능 승인서 아님.
7. 04_AI재현규칙: 공통 디자인 계약 JSON과 제품별 실제 생성 프롬프트. 모두 함께 전달할 것을 권장.
8. 파일마다 생성 이미지의 두께·비율·색상에 소차가 있음. 정면원본과 디자인 계약이 우선. 정확한 다각도에는 단일 3D모델 필요.
9. 개별 PNG는 원본 셀을 그대로 분리한 네이티브 해상도이며 인쇄용 고해상도로 업스케일하지 않음.
10. 모든 치수·HEX·소재·경도·허용차·접합공법은 제안값. 제조사 도면·색판·시험·실물 승인 후 확정.
11. 도면 없는 부분: 내통/단열층/나사산/패킹/손잡이 체결/금형 파팅라인/캡 정렬 구조. 업체 설계 후 승인 필요.

재현 요청문:
첨부 승인원본과 디자인시트/디자인계약의 제품코드를 따른다. [제품코드]를 [정면/카메라왼쪽/카메라오른쪽/왼쪽45/오른쪽45/후면]에서 보여준다.
각도 이외의 색상·형태·재질·장식 위치를 변경하지 않는다. 장식은 앞면 한 곳에 고정하고 후면 복제를 금지한다.
대키미는 하늘색+핑크, 외지몽은 크림+연두·크림 주둥이. 우주선 귀는 돔 위에서 길게 내려와 연결된다.
큰 뚜껑은 투명, 작은 대키미 캡은 핑크, 외지몽 캡은 연두. 밴드는 중간에만, 바닥커버·뚜껑귀·이름·문구 없음.

검토 기록:
정면 전용 장식/무지 후면: 4종 확인.
큰 손잡이의 정면/후면 좌우 반전, 측면 가림: 시각 확인.
작은 고리의 측면 edge-on, 후면 무지: 시각 확인.
회전 각도 정확도/절대 치수/캡 나사 종단/색 측정/허용차/성능: 미검증.
우주선·별눈 등 작은 형상의 벡터 원본: 미작성, 업체 도안 작성 후 별도 승인 필요.
'''
write('패키지_사용안내.txt',intro)
write('04_AI재현규칙/재현기준_편집원본.txt',intro+'\n\n기계판독 디자인 계약\n'+json.dumps(spec,ensure_ascii=False,indent=2))

# Preserve full PDF prose in editable HTML, extracted from delivered PDFs.
for folder,file in [('02_디자인시트','텀블러_4종_디자인시트_v01'),('03_제작사양서','텀블러_4종_샘플제작사양서_v01')]:
 reader=PdfReader(BASE/folder/f'{file}.pdf')
 chunks=[]
 for i,page in enumerate(reader.pages):
  txt=page.extract_text() or '';chunks.append(f'<section><h2>Page {i+1}</h2><pre>{html.escape(txt)}</pre></section>')
 write(f'{folder}/{file}_편집용.html','<!doctype html><html lang="ko"><meta charset="utf-8"><title>'+file+'</title><style>body{max-width:900px;margin:40px auto;font-family:sans-serif;color:#273c44}pre{font-family:inherit;white-space:pre-wrap;line-height:1.7}section{margin:40px 0;padding:24px;border:1px solid #ddd}img{max-width:100%}</style><h1>'+file+'</h1><p>문구 편집용 소스. 이미지·레이아웃의 기준은 같은 이름의 PDF를 따릅니다.</p>'+''.join(chunks)+'</html>')

# Render every PDF page for visual QA using bundled PDFium (Poppler unavailable).
qa=BASE/'99_작업기록'/'PDF_QA';qa.mkdir(exist_ok=True)
for f in [d.path,m.path]:
 doc=pdfium.PdfDocument(str(f));thumbs=[]
 for i,page in enumerate(doc):
  pic=page.render(scale=1.15).to_pil().convert('RGB');pic.save(qa/f'{f.stem}_{i+1:02d}.png')
  small=pic.copy();small.thumbnail((300,425));thumbs.append(small)
 cols=4;rows=math.ceil(len(thumbs)/cols);board=Image.new('RGB',(cols*320,rows*455),'#E4EAEB');draw=ImageDraw.Draw(board);ff=ImageFont.truetype(FONT,16)
 for i,pic in enumerate(thumbs):
  x=(i%cols)*320;y=(i//cols)*455;board.paste(pic,(x,y));draw.text((x+8,y+427),f'{i+1:02d}',font=ff,fill=INK)
 board.save(qa/f'{f.stem}_全ページ.png')
 print(f.name,'pages=',len(doc))

print('24 views, 4 label sheets, PDFs, editable sources and JSON created.')
