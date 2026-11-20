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
SRC=ROOT/'01_외지몽_마그넷_상품이미지_v02.png'
QA=ROOT/'_qa'
pdfmetrics.registerFont(TTFont('KR','/System/Library/Fonts/Supplemental/AppleGothic.ttf'))
NAVY=colors.HexColor('#13334C'); BLUE=colors.HexColor('#008C3A'); LIGHT=colors.HexColor('#EDF6FA')
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
def title(num,name,sub): return [tag('DAEGU EOLL ADEUL  /  OJ-MAG-01  /  v01  /  2026-11-18'),p(name,'h'),p(sub)]
def image_file(path,width=CW):
    im=Image.open(path); return RLImage(str(path),width=width,height=width*im.height/im.width)
im=Image.open(SRC)
im.crop((84,76,731,851)).save(QA/'front_detail.png')
im.crop((151,497,272,601)).resize((588,450)).save(QA/'paw_detail.png')
SHA=hashlib.sha256(SRC.read_bytes()).hexdigest()

class DimDiagram(Flowable):
    def __init__(self): super().__init__(); self.width=CW; self.height=263
    def draw(self):
        c=self.canv; k=3.05; x=55; y=23; ww=58.5*k; hh=70*k
        # reference crop for positioning only, no manufacturing cut contour inferred
        c.drawImage(str(QA/'front_detail.png'),x,y,width=ww,height=hh)
        c.setStrokeColor(NAVY); c.setLineWidth(.65)
        c.line(x-13,y,x-13,y+hh);c.line(x-17,y,x-9,y);c.line(x-17,y+hh,x-9,y+hh)
        c.setFont('KR',9);c.drawString(0,y+hh/2,'70 mm')
        c.line(x,y+hh+12,x+ww,y+hh+12);c.line(x,y+hh+8,x,y+hh+16);c.line(x+ww,y+hh+8,x+ww,y+hh+16)
        c.drawCentredString(x+ww/2,y+hh+18,'58.5 mm')
        bx=290; by=y; c.setFillColor(LIGHT);c.rect(bx,by,ww,hh,fill=1,stroke=1)
        mx=bx+29.25*k;my=by+(70-31.5)*k
        c.setFillColor(colors.HexColor('#3E4143'));c.circle(mx,my,8*k,fill=1,stroke=0)
        c.setStrokeColor(GRAY);c.setDash(2,2);c.line(bx,my,bx+ww,my);c.line(mx,by,mx,by+hh);c.setDash()
        c.setFillColor(INK);c.setFont('KR',8)
        c.drawString(bx+5,by+hh-14,'후면 배치 좌표 상자')
        c.drawString(bx+5,by+13,'사각형은 칼선이 아님')
        c.drawString(bx+5,my+33,'자석 중심 (29.25, 31.5) mm')
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
    c.drawString(40,27,'OJ-MAG-01  |  상품 이미지 v02  |  제작 수치 v01 제안  |  양산 승인 전')
    c.drawRightString(W-40,27,str(d.page))
def write(name,story):
    doc=SimpleDocTemplate(str(ROOT/name),pagesize=(W,H),leftMargin=40,rightMargin=40,topMargin=37,bottomMargin=45,title=name,author='대구 얼라들 디자인 제작 패키지')
    doc.build(story,onFirstPage=footer,onLaterPages=footer)

