from pathlib import Path
import json, math, html
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, white
import pypdfium2 as pdfium
from pypdf import PdfReader

BASE=Path(__file__).resolve().parents[1]
FONT='/Library/Fonts/Arial Unicode.ttf'
pdfmetrics.registerFont(TTFont('KR',FONT))
W,H=A4
INK='#203A44'; MUTED='#61747B'; LINE='#D7E3E5'
BLUE='#6DCFF5'; GREEN='#008C3A'; CREAM='#F8F0E4'; PINK='#F4B3C6'
SKUS={'DK-HB01':('대키미',BLUE),'OM-HB01':('외지몽',GREEN)}

def write(name,text):
    p=BASE/name; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(text,encoding='utf-8')

class Doc:
    def __init__(self,path):
        self.path=BASE/path; self.c=canvas.Canvas(str(self.path),pagesize=A4); self.n=0; self.y=0
        self.c.setTitle(self.path.stem); self.c.setAuthor('대구 얼라들 / 디자인 개발')
    def page(self,title,sub):
        if self.n:self.c.showPage()
        self.n+=1; c=self.c
        c.setFillColor(HexColor('#F1F7F8')); c.rect(0,H-108,W,108,fill=1,stroke=0)
        c.setFillColor(HexColor(INK)); c.setFont('KR',20); c.drawString(36,H-43,title)
        c.setFont('KR',9); c.setFillColor(HexColor(MUTED)); c.drawString(37,H-66,sub)
        c.setFont('KR',8); c.drawString(37,H-88,'2026.11.18  /  v01  /  디자인 방향 승인 · 세부 도식 검토용 · 양산 승인 전')
        c.setStrokeColor(HexColor(LINE)); c.line(36,37,W-36,37)
        c.setFont('KR',8); c.drawString(36,23,'대키미 · 외지몽  |  모든 치수·공차·내부 구조는 샘플 개발 제안')
        c.drawRightString(W-36,23,f'{self.n:02d}'); self.y=H-130
    def lines(self,text,size,width):
        out=[]
        for s in str(text).split('\n'):
            a=''
            for ch in s:
                if pdfmetrics.stringWidth(a+ch,'KR',size)>width:out.append(a);a=ch
                else:a+=ch
            out.append(a)
        return out
    def p(self,text,size=10,color=INK,gap=10):
        c=self.c;c.setFillColor(HexColor(color));c.setFont('KR',size)
        for s in self.lines(text,size,W-72):c.drawString(36,self.y,s);self.y-=size*1.6
        self.y-=gap
        assert self.y>46,(self.path,self.n,self.y)
    def h(self,text):self.y-=5;self.p(text,13,gap=7)
    def table(self,rows,widths,size=9):
        c=self.c
        for r,row in enumerate(rows):
            ls=[self.lines(t,size,widths[i]-16) for i,t in enumerate(row)]
            rh=max(map(len,ls))*size*1.6+17
            assert self.y-rh>49,(self.path,self.n,'table overflow',self.y,rh)
            c.setFillColor(HexColor('#EAF2F4' if r==0 else ('#F8FAFA' if r%2 else '#FFFFFF')))
            c.rect(36,self.y-rh,W-72,rh,fill=1,stroke=0)
            x=36
            c.setFont('KR',size);c.setFillColor(HexColor(INK))
            for i,lines in enumerate(ls):
                for j,t in enumerate(lines):c.drawString(x+8,self.y-15-j*size*1.6,t)
                x+=widths[i]
            c.setStrokeColor(HexColor(LINE));c.line(36,self.y-rh,W-36,self.y-rh);self.y-=rh
        self.y-=13
    def save(self):self.c.save()

# Explanatory native vector drawings. No generated product photograph is substituted.
def drawing(c,sku,cx,by,s=1,view='front'):
    cat=sku.startswith('DK'); color=BLUE if cat else GREEN
    c.saveState();c.translate(cx,by);c.scale(s,s)
    def path(seq,fill,stroke=INK,lw=0.8):
        p=c.beginPath()
        for op,args in seq:
            getattr(p,op)(*args)
        c.setLineWidth(lw);c.setFillColor(HexColor(fill));c.setStrokeColor(HexColor(stroke));c.drawPath(p,fill=1,stroke=1)
    def band():
        p=c.beginPath();p.moveTo(-47,0);p.curveTo(-72,35,-82,115,-48,140);p.curveTo(-25,159,25,159,48,140);p.curveTo(82,115,72,35,47,0)
        c.setLineCap(1);c.setStrokeColor(HexColor(INK));c.setLineWidth(10);c.drawPath(p)
        c.setStrokeColor(HexColor(color));c.setLineWidth(8);c.drawPath(p)
    if view=='side':
        # Side is intentionally schematic; paired parts overlap in this view.
        p=c.beginPath();p.moveTo(-9,0);p.curveTo(-15,50,-10,122,0,150);p.curveTo(12,120,13,55,9,0)
        c.setStrokeColor(HexColor(color));c.setLineWidth(8);c.setLineCap(1);c.drawPath(p)
        if cat:
            path([('moveTo',(-7,144)),('curveTo',(-10,163,-8,185,-1,199)),('curveTo',(9,181,11,158,6,144)),('close',())],color)
        else:
            path([('moveTo',(-5,140)),('curveTo',(22,136,28,108,20,74)),('curveTo',(14,52,-3,53,-9,70)),('curveTo',(-14,91,-11,121,-5,140)),('close',())],color)
        c.setLineWidth(10);c.setStrokeColor(HexColor(INK));c.line(0,150,2,199)
        c.setLineWidth(8);c.setStrokeColor(HexColor(color));c.line(0,150,2,199)
        c.setFillColor(HexColor(color));c.setStrokeColor(HexColor(INK));c.setLineWidth(.8);c.circle(2,203,12,fill=1,stroke=1)
    else:
        # Ears behind band. Front inner panels are invisible from the rear.
        for sign in [-1,1]:
            c.saveState();c.scale(sign,1)
            if cat:
                path([('moveTo',(34,144)),('curveTo',(39,159,47,185,66,199)),('curveTo',(76,181,80,157,75,132)),('close',())],color)
                if view=='front':path([('moveTo',(45,148)),('lineTo',(65,183)),('curveTo',(70,170,72,156,69,144)),('close',())],PINK,stroke=color,lw=.7)
            else:
                path([('moveTo',(51,143)),('curveTo',(79,145,95,118,98,86)),('curveTo',(104,54,78,44,65,65)),('curveTo',(55,82,55,112,51,143)),('close',())],color)
                if view=='front':path([('moveTo',(59,133)),('curveTo',(68,116,66,89,76,68)),('curveTo',(79,62,84,61,87,65)),('curveTo',(71,87,75,113,59,133)),('close',())],CREAM,stroke=color,lw=.6)
            c.restoreState()
        band()
        for sign in [-1,1]:
            c.setLineCap(1);c.setStrokeColor(HexColor(INK));c.setLineWidth(11);c.line(sign*23,150,sign*27,200)
            c.setStrokeColor(HexColor(color));c.setLineWidth(9);c.line(sign*23,150,sign*27,200)
            c.setFillColor(HexColor(color));c.setStrokeColor(HexColor(INK));c.setLineWidth(.8);c.circle(sign*27,203,12,fill=1,stroke=1)
        if view=='back':
            c.setDash(2,3);c.setStrokeColor(HexColor('#668080'));c.setLineWidth(.7)
            for sign in [-1,1]:c.line(sign*27,150,sign*27,192)
            c.setDash()
    c.restoreState()

def label(c,x,y,t,size=10):
    c.setFont('KR',size);c.setFillColor(HexColor(INK));c.drawCentredString(x,y,t)

def dim(c,x1,y1,x2,y2,text):
    c.saveState();c.setLineWidth(.6);c.setStrokeColor(HexColor(MUTED));c.line(x1,y1,x2,y2)
    c.setFillColor(HexColor(MUTED));c.setFont('KR',8)
    if y1==y2:
        for x in [x1,x2]:c.line(x,y1-4,x,y1+4)
        c.drawCentredString((x1+x2)/2,y1+6,text)
    else:
        for y in [y1,y2]:c.line(x1-4,y,x1+4,y)
        c.translate(x1-6,(y1+y2)/2);c.rotate(90);c.drawCentredString(0,0,text)
    c.restoreState()

D=Doc('02_디자인시트/머리띠_2종_디자인시트_v01.pdf')
D.page('귀와 안테나로 완성하는 머리띠','대키미 / 외지몽 2종 · 단모 봉제 · 설명용 도식')
drawing(D.c,'DK-HB01',165,405,1.12);drawing(D.c,'OM-HB01',425,405,1.12)
label(D.c,165,379,'DK-HB01  대키미');label(D.c,425,379,'OM-HB01  외지몽')
D.y=345
D.p('두 캐릭터의 귀와 구슬 안테나만 남긴 착용형 굿즈. 밴드까지 같은 계열 원단으로 감싸 두 제품이 한 시리즈로 보이도록 구성합니다.',11)
D.table([['항목','대키미','외지몽'],['정체성','삼각 고양이 귀 2개','둥글게 처진 강아지 귀 2개'],['공통 구성','줄기 2개 + 구슬 2개','줄기 2개 + 구슬 2개'],['배색','하늘색 / 분홍 귀 안쪽','초록 / 크림 귀 안쪽'],['장식 범위','얼굴·문구·추가 소품 없음','얼굴·문구·추가 소품 없음']],[85,219,219],9)
D.p('현재 상태: 디자인 방향 승인. 이 도식의 세부 비율·치수는 신규 제안이며 검토 전입니다. 실사 상품 이미지는 생성 한도 오류로 미생성입니다.',9,MUTED)

for sku,(name,color) in SKUS.items():
    cat=sku.startswith('DK')
    D.page(f'{name} | 3방향 디자인',f'{sku} · 정면 / 오른쪽 측면 / 후면 · 비축척 개념도')
    for x,view,title in [(132,'front','정면'),(301,'side','측면'),(464,'back','후면')]:
        drawing(D.c,sku,x,432,.77,view);label(D.c,x,407,title)
    D.y=374
    D.p('측면은 두 안테나와 두 귀가 겹쳐 보이는 설명도입니다. 측면에 하나만 보여도 실제 부품은 각각 2개이며, 새 구조나 정밀 투영을 뜻하지 않습니다.',9,MUTED)
    D.table([['부위','형태와 배치'],['귀',('귀 끝을 부드럽게 둥글린 삼각형. 밴드 양쪽 어깨에 세우고, 분홍 안쪽을 정면으로 노출.' if cat else '양쪽 어깨에서 바깥쪽 아래로 늘어뜨림. 끝이 둥글고 자연스럽게 굽으며, 크림 안쪽은 안으로 말린 가장자리에만 조금 노출.')],['안테나','귀 사이에 짧은 줄기 2개. 구슬은 각각 1개씩. 좌우 간격을 확보하고 귀와 부딪히지 않게 배치.'],['후면','귀 뒷면·줄기·구슬·밴드는 캐릭터 기본색. 안쪽 배색이 뒷면을 덮지 않음. 점선은 후면 봉제선 후보.'],['표면','짧고 고른 털의 저광택 봉제 원단. 귀·구슬은 부드러운 볼륨, 밴드는 얇고 매끈하게 감쌈.']],[78,445],9)
    D.h('비율 제안 | 완성 외형 기준, mm')
    D.p(('귀 1개 W45 × H55 / 최대 두께 10~14. 안테나 1개 총높이 65 / 줄기 폭 10~12 / 구슬 Ø24.' if cat else '귀 1개 펼친 외형 W42 × L85 / 최대 두께 10~14. 안테나 1개 총높이 65 / 줄기 폭 10~12 / 구슬 Ø24.'),10)
    D.p('밴드 정면 외곽 W140 × H150, 원단 포함 밴드 폭 15, 두께 5를 출발점으로 제안합니다. 총높이는 약 215이며, 뿌리 기울기와 봉제 수축에 따라 달라집니다.',9,MUTED)

D.page('배색 · 소재 · 원본 연결','디지털 기준색과 실물 원단색 구분 / 모든 배색은 원단 샘플로 재확인')
for y,col,title,desc in [(H-145,BLUE,'하늘색  #6DCFF5','대키미 밴드·귀 겉면·줄기·구슬'),(H-215,PINK,'분홍  #F4B3C6  |  임시 표현값','대키미 귀 안쪽. 공식 수치 확정값이 아니며 원본 분홍과 대조'),(H-285,GREEN,'초록  #008C3A','외지몽 밴드·귀 겉면·줄기·구슬'),(H-355,CREAM,'크림  #F8F0E4','외지몽 귀 안쪽. 기존 성체 디자인 시트의 기준색')]:
    D.c.setFillColor(HexColor(col));D.c.roundRect(36,y-40,57,40,5,fill=1,stroke=0)
    D.c.setFillColor(HexColor(INK));D.c.setFont('KR',11);D.c.drawString(108,y-10,title)
    D.c.setFont('KR',9);D.c.drawString(108,y-30,desc)
D.y=H-430
D.h('봉제 소재로 옮기는 방식')
D.p('캐릭터 원본의 매끈한 3D 피부는 정체성 참고입니다. 이번 상품은 사용자가 승인한 단모 봉제 질감으로 변환합니다. 원본의 종·귀 윤곽·색·두 안테나를 유지합니다.')
D.p('1~2mm 단모 폴리에스터 원단, 귀 내부의 얇은 솜과 보강재, 가벼운 구슬 충전재를 제안합니다. 털 방향은 좌우 대칭으로 정렬하고 바늘땀·접합부는 눈에 덜 띄게 배치합니다.')
D.h('기준 자료')
D.p('사용자 첨부 머리띠 사진 2장: 밴드 구조·봉제 질감 참고. 토끼/여우 귀의 길이·색·당근 장식은 적용하지 않습니다.',9)
D.p('character/대키미 캐릭터 설정보드.png 및 외지몽 캐릭터 설정보드.png: 귀와 안테나 정체성. 외지몽 성체 표정자세 확정본 v01의 귀·크림색 설명도 참고했습니다.',9)
D.p('참고 문서의 제작 지시는 사용자 요청과 구분했습니다. 이번 산출물 범위는 사용자가 승인한 머리띠 2종이며, 기존 다른 굿즈의 문구·장식·제작 순서는 적용하지 않습니다.',9,MUTED)
D.save()

S=Doc('03_제작사양서/머리띠_2종_샘플제작사양서_v01.pdf')
S.page('01 | 샘플 개발 치수','제작사 견적·첫 샘플 협의용 / 모든 수치는 디자이너 제안 / 단위 mm')
drawing(S.c,'DK-HB01',155,451,.94)
dim(S.c,65,451,65,653,'전체 높이 약 215')
dim(S.c,90,431,220,431,'밴드 외곽 폭 140 제안')
S.c.setFont('KR',9);S.c.setFillColor(HexColor(INK))
for i,t in enumerate(['좌표 원점: 정면 밴드 상단 중앙','좌우 X축 / 위쪽 Z축','안테나 뿌리: X = ±23, Z ≈ 0','구슬 중심: X = ±27, Z ≈ 53','귀 부착 중심: X ≈ ±58','귀 뿌리는 밴드 곡면을 따라 위치','도식의 픽셀에서 치수 역산 금지']):S.c.drawString(290,650-i*24,t)
S.y=397
S.table([['항목','공통 / 대키미','외지몽'],['밴드 외곽 정면','W140 × H150','동일 기본 밴드'],['밴드 단면 / 끝 간격','폭15 × 두께5 / 자유상태 90~95','동일, 착용 샘플로 조정'],['귀 1개 외형','W45 × H55 × T10~14','W42 × L85 × T10~14'],['안테나 1개','총높이65, 줄기 폭10~12','동일'],['구슬 / 수량','Ø24 / 귀2·줄기2·구슬2','동일'],['총 외형 목표','약 W165 × H215','약 W200 × H215']],[115,204,204],9)
S.p('치수 정의: 밴드 폭은 정면 외곽 최대폭. 단면 폭은 앞뒤 방향 원단 폭. 귀는 부착 여유를 제외한 완성 외형, 안테나 높이는 부착부에서 구슬 꼭대기까지입니다. 총 외형은 배치·처짐에 따른 목표 범위이며 확정 CAD 치수가 아닙니다.',9,MUTED)
S.p('첫 샘플 비교용 잠정 허용편차: 밴드·장식 치수 ±3, 구슬 지름 ±2, 좌우 부착 위치 차이 3 이내. 업체 공정능력 확인 후 재합의하며 현재 양산 합격 기준으로 사용하지 않습니다.',9,MUTED)

S.page('02 | 자재 · 봉제 · 고정 구조','BOM 및 조립 제안 / 구매 자재 확정 및 생산 패턴은 제작사 개발 범위')
S.table([['부품','수량/개','소재·구조 제안'],['밴드 심재','1','복원성 있는 PP 또는 동등 수지. 단면·곡률·압박감은 기존 밴드 샘플 비교 후 선정.'],['밴드 커버','1식','캐릭터색 단모 폴리에스터 원단. 끝단까지 완전 피복, 끝부분 얇은 완충재 추가.'],['귀 겉감 / 안감','좌우 1쌍','본체색 겉감 + 배색 안쪽. 대키미는 얇은 폼 등으로 삼각 윤곽 유지, 외지몽은 부드럽게 처지도록 보강 최소화.'],['귀 충전재','1식','얇은 폴리에스터 솜. 귀 끝에 뭉침 없이 좌우 볼륨 맞춤.'],['안테나 줄기','2','원단 튜브 안에 유연한 수지 보강재를 완전히 감쌈. 노출 철사·스프링은 사용하지 않는 제안.'],['안테나 구슬','2','Ø24 완성 목표의 봉제 구. 가벼운 솜 충전, 단단한 외부 비즈 대신 봉제 부품.'],['봉제실 / 보강테이프','1식','각 원단과 같은 색 실, 뿌리 하중을 분산하는 내부 봉제 탭 및 테이프.']],[84,52,387],9)
S.h('고정 방식')
S.p('귀 뿌리와 안테나 뿌리를 커버 표면에만 붙이지 말고, 내부 봉제 탭을 밴드 둘레를 감싸는 보강 슬리브에 연결하는 방식을 제안합니다. 접착은 위치 고정 보조로만 검토하고, 뿌리 봉제와 슬리브가 지지하도록 업체가 구조를 제시합니다.',10)
S.p('구슬과 줄기 연결부는 봉제 여유를 안으로 넣고 보강 봉제합니다. 구슬과 줄기가 따로 빠지지 않는 연결을 목표로 하되, 인장 수치와 시험 방법은 사용 대상·자재를 정한 뒤 업체가 제안해야 합니다.',10)
S.p('안테나가 자립하면서 머리를 움직일 때 과하게 흔들리지 않는지 확인합니다. 심재 강성·길이·구슬 중량을 함께 조정하며, 이 문서의 구조는 검증된 설계가 아닙니다.',9,MUTED)

S.page('03 | 샘플 검수 · 전달 조건','성인·청소년용 출발 제안 / 최종 대상 연령·사이즈는 사용자 및 제작사 확인 전')
S.table([['점검','첫 샘플에서 확인할 내용'],['외형','대키미 삼각 귀 / 외지몽 처진 귀. 각 제품 귀2·줄기2·구슬2. 안테나와 귀 간섭, 좌우 비대칭 확인.'],['색상','자연광과 같은 실내조명에서 원단 색판·원본·샘플 비교. 디지털 HEX를 실물색 승인으로 취급하지 않음.'],['착용','머리 크기가 다른 착용자에게 압박·흘러내림·끝단 불편을 기록. 20분 착용 비교를 제안하며 적합성 검증을 뜻하지 않음.'],['구조','반복 착탈 후 커버 밀림·귀 처짐·줄기 꺾임·구슬 이탈·심재 노출 확인. 반복 횟수와 인장 합격값은 업체 제안 후 승인.'],['봉제','벌어진 봉제선·털 끼임·솜 뭉침·끝단 단차 확인. 구슬 접합부와 귀 뿌리의 빠짐 여부 확인.'],['표시·취급','확정 혼용률·제조 정보·사용 대상·원단별 관리법을 업체 자료로 작성. 어린이용 전환 여부는 발주 전에 결정.']],[70,453],9)
S.h('제작사에 요청할 회신')
S.p('① 기존 밴드 실물 치수·곡률과 소재 ② 원단 색판 및 혼용률 ③ 귀·안테나 내부 단면안 ④ 구슬 중량과 자립 샘플 ⑤ 생산 가능한 치수 편차 ⑥ 샘플 비용·수량별 견적·제작 기간 ⑦ 생산용 패턴 및 최종 자재표.',10)
S.h('파일과 승인 상태')
S.p('디자인 시트: 형태·색·배치의 검토용 기준. 본 사양서: 제안 치수와 첫 샘플 요구사항. 생산 패턴·재단 파일·심재 설계·실사 상품 사진은 포함되지 않습니다.',10)
S.p('진행 순서: 세부 도식 검토 → 업체 구조·견적 회신 → 실물 첫 샘플 → 착용·봉제 수정 → 색상·자재·치수 확정 → 양산 승인. 이번 사용자의 승인은 앞선 디자인 방향에 한정해 기록했습니다.',10)
S.p('상품 이미지 생성은 usage_limit_reached 오류로 미완료입니다. 문서의 평면 도식은 실물 사진이나 생성형 상품 사진으로 표시하지 않았습니다.',9,MUTED)
S.save()

contract={
 'version':'v01','date':'2026-11-18','status':{'concept':'user approved','detailed_drawings':'proposal, review pending','dimensions':'proposed, supplier confirmation required','product_photo':'not generated: image_gen usage_limit_reached','production':'not approved'},
 'skus':{sku:{'character':name,'base_hex':color,'ears':2,'antenna_stems':2,'antenna_balls':2} for sku,(name,color) in SKUS.items()},
 'dimensions_mm':{'band_front':[140,150],'band_cross_section':[15,5],'antenna_overall_height':65,'ball_diameter':24,'cat_ear':[45,55],'dog_ear':[42,85]},
 'palette':{'blue':BLUE,'green':GREEN,'cream':CREAM,'pink':{'hex':PINK,'status':'temporary illustration value, not official numerical color'}},
 'invariants':['cat triangular pink-inner ears','dog green drooping rounded ears with narrow cream inner edge','no face, lettering, carrot, bow or other decoration'],
 'not_included':['photorealistic product image','production pattern','validated material or tolerance','approved sample']}
write('99_작업기록/design_contract_v01.json',json.dumps(contract,ensure_ascii=False,indent=2))

md='''# 대키미·외지몽 머리띠 2종 | 수정용 사양 원문 v01

작성 2026-11-18. 앞선 사용자의 디자인 방향 승인을 반영. 세부 도식·치수·소재는 제안이며 실물 샘플 및 양산 승인 전.

## 디자인
- DK-HB01 대키미: 하늘색 밴드, 분홍 안쪽의 삼각 귀 2개, 하늘색 줄기 2개와 구슬 2개.
- OM-HB01 외지몽: 초록 밴드, 양옆 아래로 처지는 둥근 귀 2개, 안으로 말린 가장자리에만 크림 안쪽 노출, 초록 줄기 2개와 구슬 2개.
- 얼굴·문구·리본·당근·추가 장식 없음. 짧은 털 봉제 원단으로 소재 변환.
- 정면·측면·후면은 비축척 개념도. 측면에서는 쌍을 이룬 부품이 겹쳐 보임.

## 디지털 색
하늘색 #6DCFF5, 초록 #008C3A, 크림 #F8F0E4. 분홍 #F4B3C6은 도식용 임시 표현값이며 공식 수치 아님. 실제 원단색은 색판으로 별도 승인.

## 샘플 치수 제안 (mm)
|항목|대키미|외지몽|
|---|---|---|
|밴드 정면 외곽|W140 × H150|동일|
|밴드 단면|폭15 × 두께5|동일|
|자유상태 끝 간격|90~95|동일|
|귀 1개 완성 외형|W45 × H55 × T10~14|W42 × L85 × T10~14|
|안테나 1개 총높이|65|65|
|줄기 폭 / 구슬 지름|10~12 / Ø24|동일|
|총 외형 목표|약 W165 × H215|약 W200 × H215|

밴드 상단 중앙을 X=0, Z=0으로 두고, 안테나 뿌리 X=±23, 구슬 중심 X=±27·Z≈53, 귀 부착 중심 X≈±58로 제안. 뿌리는 밴드 곡면을 따라 조정. 치수는 봉제 여유 제외한 완성 외형 기준이며 픽셀에서 역산 금지.

첫 샘플 비교용 허용편차: 주요 치수 ±3, 구슬 지름 ±2, 좌우 부착 위치 차이 3 이내. 업체 확인 전 양산 합격 기준이 아님.

## 자재 및 구조 제안
1~2mm 단모 폴리에스터 원단, 밴드 PP 또는 동등 수지 심재, 폴리에스터 솜. 대키미 귀는 얇은 폼 보강, 외지몽 귀는 처짐을 유지. 안테나는 유연 수지 보강재를 원단 안에 완전 피복하고 구슬은 가벼운 봉제 충전구로 제작. 노출 철사·스프링 제외 제안.

귀·줄기 뿌리는 내부 봉제 탭으로 밴드 둘레 보강 슬리브에 연결. 접착만으로 고정하지 않는 안. 구슬 연결은 봉제 여유를 안쪽으로 넣고 보강 봉제. 강성·중량·인장값은 업체 설계 및 샘플로 확인.

## 실물 확인 및 업체 회신
성인·청소년용을 출발 제안으로 두되 최종 대상 연령과 사이즈는 미확정. 외형·부품 개수·원단색·압박감·흘러내림·끝단 불편·커버 밀림·심재 노출·구슬 이탈·봉제 벌어짐 확인. 20분 착용 비교는 개발 제안이며 성능 검증이 아님.

업체 회신: 기존 밴드 치수/곡률/소재, 원단 색판과 혼용률, 귀/안테나 단면, 구슬 중량 및 자립 여부, 치수 편차, 샘플비 및 수량별 견적/기간, 생산 패턴. 합격 인장값과 반복 횟수는 업체 제안 후 별도 승인. 확정 자재·관리법에 맞춰 표시사항 작성.

진행: 도식 검토 → 구조·견적 회신 → 첫 샘플 → 착용·봉제 수정 → 색·자재·치수 확정 → 양산 승인.

## 산출물과 제한
디자인 시트 PDF 4쪽, 샘플 제작사양서 PDF 3쪽, 도식 미리보기 PNG, JSON 기준 및 재생성 소스 포함. 상품 이미지 생성은 내장 image_gen의 사용 한도 오류로 실패했으며 프롬프트만 저장. 도식은 실물 사진을 대체하거나 검증하지 않음. 생산 패턴·재단 파일·검증된 구조는 포함되지 않음.
'''
write('03_제작사양서/머리띠_2종_수정용사양원문_v01.md',md)
write('README.md','''# 머리띠 2종 제작 패키지 v01

- 02_디자인시트: 4쪽 PDF, 정면·측면·후면 설명도 및 배색.
- 03_제작사양서: 3쪽 PDF와 수정용 Markdown. 치수·구조·소재는 샘플 개발 제안.
- 01_상품이미지: 실사 상품 이미지는 생성 한도 오류로 미생성. 상품 이미지 없음.
- 99_작업기록: 생성 프롬프트, JSON 기준, PDF 제작 소스, 페이지 검수 이미지.

사용자 승인 범위는 앞선 디자인 방향입니다. 새 세부 도식·치수·소재와 실물 샘플은 미승인입니다. 문서의 도식은 상품 사진이 아닙니다.
''')
write('01_상품이미지/생성상태.txt','내장 image_gen 상품 이미지 생성 시도: HTTP 429 / usage_limit_reached. 상품 이미지는 미생성. 99_작업기록/상품이미지_생성프롬프트.txt에 프롬프트 보관.\n')

# Render every page for visual inspection and supply useful design previews.
qa=BASE/'99_작업기록/PDF_QA';qa.mkdir(exist_ok=True)
results=[]
for file in [D.path,S.path]:
    pdf=pdfium.PdfDocument(str(file));reader=PdfReader(str(file));results.append((file.name,len(pdf)))
    assert len(reader.pages)==len(pdf)
    for i,page in enumerate(pdf):
        image=page.render(scale=1.5).to_pil();image.save(qa/f'{file.stem}_{i+1:02d}.png')
        txt=reader.pages[i].extract_text();assert len(txt)>200,(file,i,'missing text')
        if file==D.path and i==0:image.save(BASE/'02_디자인시트/머리띠_2종_디자인도식_미리보기_v01.png')
print(json.dumps({'pdfs':results,'qa_pages':len(list(qa.glob('*.png')))},ensure_ascii=False))
