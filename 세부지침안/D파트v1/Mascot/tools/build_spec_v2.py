"""Package current approved working specs as matching v2 Markdown and PDF."""
from pathlib import Path
import re,json,html,unicodedata
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,Table,TableStyle,Image,KeepTogether,Flowable
from PIL import Image as PILImage
ROOT=Path(__file__).resolve().parents[1];SRC=ROOT/'specs';OUT=ROOT/'output/design_spec_v2';OUT.mkdir(parents=True,exist_ok=True)
MD=OUT/'mascot_design_spec_v2.md';PDF=OUT/'mascot_design_spec_v2.pdf'
NAVY=colors.HexColor('#16304B');BLUE=colors.HexColor('#6DCFF5');GREEN=colors.HexColor('#008C3A');INK=colors.HexColor('#263746');MUTED=colors.HexColor('#63788A');PALE=colors.HexColor('#F0F5F9')
chapters=[]
intro='''## 문서 개요와 적용 기준

버전: **2.0** · 작성일: **2026-11-03**

대구 사투리 축제 기획 AI 에이전트, 일러스트, 홍보물, 굿즈 제작에 사용하는 대키미·외지몽 통합 디자인 가이드다. 기존 v1.1의 디자인·비율·색상을 유지하고, 최신 전체 키와 환산 치수를 한 문서로 정리한 배포 버전이다.

| 핵심 항목 | 대키미 | 외지몽 |
|---|---|---|
| 종족 | 고양이형 외계인 | 강아지형 외계인 |
| 출신 | 대구 | 우주 |
| 전체 키 | 103cm | 105cm |
| 키의 측정 구간 | 안테나 구슬 최고점~발바닥 | 안테나 구슬 최고점~발바닥 |
| 1u의 실제 길이 | 1.03cm | 1.05cm |
| 안테나 구슬 지름 | 11.845cm (표시 11.8cm) | 13.65cm (표시 13.7cm) |
| 대표색 | #6DCFF5 | #008C3A |

### 우선 적용하는 사용자 확정 사항

- 눈을 완전히 뜬 기본 표정에서 한쪽 눈당 하이라이트 총 3개. 큰 별 1개와 작은 반짝임 2개이며 별 모양 사용은 확정이다.
- 기본 얼굴에 홍조는 없다. 감정 표현에 따라 홍조를 허용한다.
- 대키미 얼굴은 코·입 주변까지 하늘색으로 유지하며 흰색 주둥이 영역을 만들지 않는다.
- 외지몽의 입 주변과 감정·귀 움직임으로 드러나는 귀 안쪽은 같은 크림빛 흰색이다.
- 두 캐릭터의 코와 입은 각각의 원본 형태를 유지한다.
- 대키미 전체 키 103cm, 외지몽 전체 키 105cm를 적용하며, 기존 부위별 상대 비율은 유지한다.

### 정보의 근거

| 구분 | 의미 |
|---|---|
| 사용자 확정 | 이번 대화에서 직접 확정한 외형·표현·키 규칙 |
| 보드 명시값 | 설정 보드에 적힌 대표색 등의 값 |
| 원본 근사 판독값 | 원본 PNG의 부위 경계·픽셀·색상 견본을 읽은 값 |
| 제작 지정값 | 깊이·가림 부위·세부 도형·허용 오차 등 반복 제작을 위해 지정한 작업 규격 |

제작 지정값을 원본 3D 모델의 실측값으로 해석하지 않는다. 전체 키를 제외한 부위 치수는 원본 근사 판독 또는 기존 작업 기준의 환산 결과다. 제조용 금형이나 물리 구조를 검증한 도면은 아니다.

### 캐릭터 관계와 메시지

대키미는 자신만만하지만 허당스럽고 친구를 진심으로 챙기는 대구 토박이다. 외지몽은 호기심이 많고 솔직하며 실수 후에도 다시 도전하는 여행자다. 둘은 표현을 오해하면서 티격태격하지만 서로 배우고 영향을 주는 친구다.

기본 보드 문구는 **“말이 달라도, 친구가 된다.”**다. 이전 기록의 “표현이 달라도, 친구가 된다.”는 같은 관계의 의미를 설명하는 문구로 남긴다.
'''
chapters.append(intro)
modules=[('physical_dimensions.md','실제 키·지름·cm 치수표'),('design_spec_common.md','공통 디자인 규칙'),('design_spec_daekimi.md','대키미 개별 스펙'),('design_spec_oejimong.md','외지몽 개별 스펙'),('proportion_guide.md','정규화 비율·배치 기준'),('face_detail_guide.md','얼굴·하이라이트 세부 기준'),('color_palette.md','색상 팔레트와 추출 근거'),('expression_guide.md','표정·동작 가이드'),('ai_prompt_guide.md','AI 이미지 생성 프롬프트'),('negative_prompt.md','금지 사항과 결과 확인')]
for file,title in modules:
 s=(SRC/file).read_text();s=s.split('\n',1)[1].lstrip()
 s=re.sub(r'^## 실제 키 기준 v1\.1\n.*?\n\n','',s,count=1,flags=re.S)
 # Cross-references become self-contained chapter references in the delivered file.
 s=re.sub(r'\[([^\]]+)\]\([^)]+\)',r'\1',s)
 s=s.replace('proportion_guide.md','「정규화 비율·배치 기준」').replace('face_detail_guide.md','「얼굴·하이라이트 세부 기준」').replace('color_palette.md','「색상 팔레트와 추출 근거」')
 s=s.replace('아래 v1 추가 기준','아래 추가 기준').replace('## v1 추가 팔레트','## 추가 팔레트').replace('## v1 제작 기준의 적용','## 제작 기준의 적용').replace('## v1 수치 보조 지시','## 수치 보조 지시').replace('## 실제 키와 상대 크기 v1.1','## 실제 키와 상대 크기')
 s=s.replace('이번 버전의 제작 지정값','기존 작업 기준에서 유지한 제작 지정값')
 s=re.sub(r'^(#+) ',r'#\1 ',s,flags=re.M)
 chapters.append('## '+title+'\n\n'+s.strip()+'\n')
# Self-contained provenance appendix, including original geometry coordinates.
g=json.loads((SRC/'geometry_reference.json').read_text())
appendix='''## 측정 원장·원본 자료

### 원본과 측정 기준

설정 보드 두 장의 원본 해상도는 각각 793 × 1983px다. 좌표는 좌상단 (0,0) 기준이며, 경계 사각형은 [왼쪽 x, 위 y, 오른쪽 x, 아래 y]로 적는다. 좌표 차이로 너비·높이를 계산한다. 정확한 원본 파일명은 프로젝트의 character 폴더에 저장되어 있다.

대키미 정면 기준 키는 y=638~852의 214px, 외지몽은 y=705~915의 210px다. 아래 사각형에는 가려진 접합부의 수동 근사도 포함된다. 실제 키 103cm·105cm는 이 픽셀 크기에서 알아낸 것이 아니라 사용자가 지정한 기준이다.

| 항목 | 대키미 원본 경계 | 외지몽 원본 경계 |
|---|---|---|
'''
for role,(box,label,basis) in g['characters']['daekimi']['boxes'].items():
 other=g['characters']['oejimong']['boxes'].get(role)
 appendix+=f'| {label} | {", ".join(map(str,box))} | {", ".join(map(str,other[0])) if other else "해당 없음"} |\n'
appendix+='| 외지몽 주둥이 | 해당 없음 | 97, 800, 142, 840 |\n'
appendix+='''
### 코·입·혀 색상 샘플 위치

상단 큰 캐릭터 렌더링에서 3 × 3px의 채널별 중앙값을 읽었다. 독립 색상 견본이 아니라 렌더링 표면의 관찰값이다.

| 부위 | 대키미 중심 (x,y) | 외지몽 중심 (x,y) |
|---|---|---|
| 코 | 562, 224 | 568, 231 |
| 입 안쪽 | 559, 236 | 565, 249 |
| 혀 | 559, 245 | 568, 263 |

### 버전 2 변경 기록

- 최신 실제 키: 대키미 103cm, 외지몽 105cm.
- 기존 비율에 따른 구슬·꼬리 지름과 부위별 cm 환산값을 통합했다.
- 디자인·색상·얼굴·표정·하이라이트 규칙은 기존 기준을 유지했다.
- 문서 중복을 줄이고 원본 근거와 제작 지정값을 구분했다.
- PDF와 Markdown은 동일한 본문에서 생성한다. PDF에는 원본 보드를 참고 이미지로 함께 수록한다.

### 기존 규격 파일

프로젝트의 specs 폴더에는 geometry_reference.json, physical_dimensions.json, color_samples.json, detail_color_samples.json이 남아 있다. 이 문서는 해당 자료의 주요 치수·근거를 본문과 측정 원장에 수록했으므로 위 파일 없이도 읽을 수 있다.
'''
appendix=appendix.split("### 버전 2 변경 기록")[0].rstrip()+"\n"
chapters.append(appendix)
boards=[]
for p in (ROOT/'character').glob('*.png'):
 name=unicodedata.normalize('NFC',p.name)
 boards.append(('대키미' if '대키미' in name else '외지몽',p))
boards.sort(key=lambda a:a[0])
for name,p in boards:
 chapters.append('## '+name+' 원본 설정 보드\n\n참고 이미지다. 보드의 일부 표현과 최신 확정 규칙이 다를 때는 이 문서의 본문을 우선 적용한다. 특히 기본 홍조, 대키미 주둥이 영역, 눈 하이라이트 규칙은 본문을 따른다.\n\n!['+name+' 원본 설정 보드](../../'+p.relative_to(ROOT).as_posix()+')\n')
# Number chapters for navigation and clear table of contents.
for i,ch in enumerate(chapters,1):chapters[i-1]=re.sub(r'^## ',f'## {i:02d}. ',ch,count=1)
contents='## 목차\n\n'+'\n'.join(f'- {re.sub(r"^## ","",c.splitlines()[0])}' for c in chapters)+'\n'
header='# 대키미·외지몽 캐릭터 디자인 스펙 시트\n\n**VERSION 2.0** · 2026-11-03\n\n대구 사투리 축제 기획 AI 에이전트\n\n**대키미 103cm / 외지몽 105cm**\n\n전체 키 기준: 안테나 구슬의 가장 높은 지점부터 발바닥까지.\n\n'
MD.write_text(header+'---\n\n'+contents+'\n---\n\n'+'\n---\n\n'.join(chapters),encoding='utf-8')
# PDF rendering from the same Markdown string.
pdfmetrics.registerFont(TTFont('KR','/System/Library/Fonts/Supplemental/Arial Unicode.ttf'))
pdfmetrics.registerFont(TTFont('KRHead','/System/Library/Fonts/Supplemental/AppleGothic.ttf'))
pdfmetrics.registerFontFamily('KR',normal='KR',bold='KRHead',italic='KR',boldItalic='KRHead')
styles={
 'p':ParagraphStyle('p',fontName='KR',fontSize=9.1,leading=14.1,textColor=INK,spaceAfter=5,wordWrap='CJK'),
 'small':ParagraphStyle('small',fontName='KR',fontSize=8,leading=11.6,textColor=MUTED,spaceAfter=5,wordWrap='CJK'),
 'h1':ParagraphStyle('h1',fontName='KRHead',fontSize=20,leading=27,textColor=NAVY,spaceAfter=16,keepWithNext=True,wordWrap='CJK'),
 'h2':ParagraphStyle('h2',fontName='KRHead',fontSize=12.1,leading=18,textColor=NAVY,spaceBefore=9,spaceAfter=6,keepWithNext=True,wordWrap='CJK'),
 'h3':ParagraphStyle('h3',fontName='KRHead',fontSize=10.5,leading=16,textColor=GREEN,spaceBefore=8,spaceAfter=5,keepWithNext=True,wordWrap='CJK'),
 'cell':ParagraphStyle('cell',fontName='KR',fontSize=8.1,leading=11.8,wordWrap='CJK',textColor=INK),
 'th':ParagraphStyle('th',fontName='KRHead',fontSize=8.2,leading=12.2,wordWrap='CJK',textColor=colors.white)
}
def inline(s):
 s=re.sub(r'\[([^\]]+)\]\([^)]+\)',r'\1',s)
 s=html.escape(s)
 s=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',s)
 s=re.sub(r'`([^`]+)`',r'<font color="#176284">\1</font>',s)
 return s
WIDTH=A4[0]-88

def table(rows):
 n=len(rows[0]);charmax=[max(len(re.sub(r'[*`]','',row[i])) if i<len(row) else 0 for row in rows) for i in range(n)]
 if n==3:weights=[.32,.34,.34]
 elif n==2:weights=[.29,.71]
 elif n==4:weights=[.20,.23,.23,.34]
 elif n==5:weights=[.13,.29,.17,.21,.20]
 else:weights=[1/n]*n
 cells=[[Paragraph(inline(c),styles['th' if y==0 else 'cell']) for c in row] for y,row in enumerate(rows)]
 t=Table(cells,colWidths=[WIDTH*w for w in weights],repeatRows=1,hAlign='LEFT')
 commands=[('BACKGROUND',(0,0),(-1,0),NAVY),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),('LINEBELOW',(0,0),(-1,0),.5,NAVY),('LINEBELOW',(0,1),(-1,-1),.35,colors.HexColor('#DAE4EC'))]
 for y in range(1,len(rows)):
  if y%2:commands.append(('BACKGROUND',(0,y),(-1,y),PALE))
 t.setStyle(TableStyle(commands));return t
story=[]
# Cover mirrors the MD header. Images remain unchanged source assets.
story += [Spacer(1,25),Paragraph('CHARACTER DESIGN SPECIFICATION',ParagraphStyle('eyebrow',fontName='KR',fontSize=9,leading=14,textColor=MUTED,spaceAfter=16)),Paragraph('대키미 · 외지몽',ParagraphStyle('cover',fontName='KRHead',fontSize=32,leading=43,textColor=NAVY,spaceAfter=4)),Paragraph('캐릭터 디자인 스펙 시트',ParagraphStyle('cover2',fontName='KRHead',fontSize=22,leading=32,textColor=NAVY,spaceAfter=17)),Paragraph('VERSION 2.0  /  2026-11-03',styles['small']),Spacer(1,12)]
summary=Table([[Paragraph('대키미 103cm',styles['h2']),Paragraph('외지몽 105cm',styles['h2'])]],colWidths=[WIDTH/2]*2)
summary.setStyle(TableStyle([('BACKGROUND',(0,0),(0,0),colors.HexColor('#E9F7FF')),('BACKGROUND',(1,0),(1,0),colors.HexColor('#E9F7ED')),('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10),('LEFTPADDING',(0,0),(-1,-1),14)]));story += [summary,Spacer(1,13),Paragraph('대구 사투리 축제 기획 AI 에이전트',styles['p']),Paragraph('전체 키 기준: 안테나 구슬의 가장 높은 지점부터 발바닥까지.',styles['p']),Spacer(1,13)]
# Original boards on the cover as references; full versions also appear in appendix.
ims=[]
for name,p in boards:
 im=PILImage.open(p);w=155;ims.append(Image(str(p),width=w,height=w*im.height/im.width))
coverimgs=Table([ims],colWidths=[WIDTH/2]*2);coverimgs.setStyle(TableStyle([('ALIGN',(0,0),(-1,-1),'CENTER'),('VALIGN',(0,0),(-1,-1),'TOP')]))
story += [coverimgs,Spacer(1,10),Paragraph('기존 디자인과 비율을 유지한 통합 배포본 · 원본 근사 판독값과 제작 지정값 구분',styles['small']),PageBreak()]

def parse(md):
 lines=md.strip().splitlines();i=0;flow=[]
 while i<len(lines):
  line=lines[i].strip()
  if not line:i+=1;continue
  if line.startswith('|'):
   rows=[]
   while i<len(lines) and lines[i].strip().startswith('|'):
    row=[c.strip() for c in lines[i].strip().strip('|').split('|')]
    if not all(re.fullmatch(r':?-+:?',c.replace(' ','')) for c in row):rows.append(row)
    i+=1
   if rows:flow +=[table(rows),Spacer(1,9)]
   continue
  if line.startswith('!['):
   m=re.match(r'!\[([^]]*)\]\((.*)\)',line)
   p=(OUT/m.group(2)).resolve();im=PILImage.open(p);maxh=620;maxw=WIDTH;scale=min(maxw/im.width,maxh/im.height)
   flow.append(Image(str(p),width=im.width*scale,height=im.height*scale));i+=1;continue
  if line.startswith('#'):
   level=len(line)-len(line.lstrip('#'));style='h1' if level==2 else 'h2' if level==3 else 'h3'
   flow.append(Paragraph(inline(line.lstrip('#').strip()),styles[style]));i+=1;continue
  if line=='---':i+=1;continue
  if line.startswith('- ') or re.match(r'^\d+\. ',line):
   text=line[2:] if line.startswith('- ') else line
   flow.append(Paragraph('• '+inline(text),styles['p']));i+=1;continue
  paras=[line];i+=1
  while i<len(lines) and lines[i].strip() and not lines[i].lstrip().startswith(('#','|','- ','![')):
   paras.append(lines[i].strip());i+=1
  flow.append(Paragraph(inline(' '.join(paras)),styles['p']))
 return flow
story+=parse(contents);story.append(PageBreak())
for i,ch in enumerate(chapters):
 story+=parse(ch)
 if i<len(chapters)-1:story.append(PageBreak())

def decor(c,doc):
 w,h=A4;c.saveState();c.setStrokeColor(colors.HexColor('#D9E6EE'));c.setLineWidth(.6);c.line(44,h-34,w-44,h-34)
 c.setFont('KR',7.5);c.setFillColor(MUTED);c.drawString(44,h-27,'대키미 · 외지몽  |  캐릭터 디자인 스펙 시트 v2.0');c.drawRightString(w-44,h-27,'2026-11-03')
 c.line(44,35,w-44,35);c.drawString(44,22,'DAEKIMI 103cm  /  OEJIMONG 105cm');c.drawRightString(w-44,22,str(doc.page));c.restoreState()
doc=SimpleDocTemplate(str(PDF),pagesize=A4,rightMargin=44,leftMargin=44,topMargin=52,bottomMargin=49,title='대키미·외지몽 캐릭터 디자인 스펙 시트 v2.0',author='대구 사투리 축제 마스코트 프로젝트',pageCompression=1)
doc.build(story,onFirstPage=decor,onLaterPages=decor)
print(MD);print(PDF)
