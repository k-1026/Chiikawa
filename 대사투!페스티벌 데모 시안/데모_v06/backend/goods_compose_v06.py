"""굿즈 시안 합성: 공식 캐릭터 원본 이미지(투명 PNG)를 그대로 굿즈 모양에 올린다.
AI(FLUX)는 배경·제품 사진만 만들고, 캐릭터는 AI가 다시 그리지 않으므로 원본과 같다."""
import base64,io,math,threading
from pathlib import Path
from PIL import Image,ImageChops,ImageDraw,ImageFilter,ImageOps

ASSETS=Path(__file__).resolve().parents[1]/'assets_v06'
CHARS={'daekimi':'hero_daekimi.png','oejimong':'hero_oejimong.png'}
SIZE=1024

_ctx=threading.local()   # 요청마다 다른 포즈를 쓰므로 스레드별로 보관한다
POSE_DIR=ASSETS/'poses'

def load(name):
    """공식 캐릭터 이미지. 포즈 ID가 지정되면 공식 표정·자세 시트에서 오린 포즈를, 아니면 기본 포즈(hero)를 쓴다."""
    used=getattr(_ctx,'used',None)
    if used is not None:used.add(name)
    pid=(getattr(_ctx,'poses',None) or {}).get(name)
    f=POSE_DIR/(pid+'.png') if pid else None
    if f and f.exists():
        im=Image.open(f).convert('RGBA')
        if im.height<420:   # 시트에서 오린 포즈는 작아서 2배로 키우고 살짝 선명하게 한다
            im=im.resize((im.width*2,im.height*2),Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1.4,percent=55,threshold=2))
        return im
    return Image.open(ASSETS/CHARS[name]).convert('RGBA')

def fit_h(img,h):
    if img.width>img.height:   # 누운 포즈처럼 가로로 긴 그림은 가로를 기준으로 맞춘다
        w=int(h*0.95);return img.resize((w,max(1,round(img.height*w/img.width))),Image.LANCZOS)
    w=round(img.width*h/img.height);return img.resize((w,h),Image.LANCZOS)

def outline(img,px,color=(255,255,255,255)):
    """캐릭터 가장자리에 흰 테두리(다이컷)를 붙인다."""
    pad=px+4;big=Image.new('RGBA',(img.width+pad*2,img.height+pad*2),(0,0,0,0));big.paste(img,(pad,pad),img)
    a=big.getchannel('A').point(lambda v:255 if v>20 else 0)
    k=px*2+1 if px*2+1%2 else px*2+1
    grown=a.filter(ImageFilter.MaxFilter(min(k,255 if k%2 else k+1)))
    grown=grown.filter(ImageFilter.GaussianBlur(1.2))
    base=Image.new('RGBA',big.size,color);base.putalpha(grown)
    base.alpha_composite(big);return base

def shadow(img,offset=(10,16),blur=14,opacity=110):
    sh=Image.new('RGBA',(img.width+80,img.height+80),(0,0,0,0))
    a=Image.new('L',img.size,0);a.paste(img.getchannel('A'),(0,0))
    blk=Image.new('RGBA',img.size,(30,20,50,opacity));blk.putalpha(a.point(lambda v:v*opacity//255))
    sh.paste(blk,(40+offset[0],40+offset[1]));return sh.filter(ImageFilter.GaussianBlur(blur))

def paste_center(canvas,img,cx,cy,shadowed=True,angle=0):
    if angle:img=img.rotate(angle,resample=Image.BICUBIC,expand=True)
    if shadowed:
        s=shadow(img);canvas.alpha_composite(s,(int(cx-s.width/2),int(cy-s.height/2)))
    canvas.alpha_composite(img,(int(cx-img.width/2),int(cy-img.height/2)))

def pair(who,h,gap=-30):
    names=['daekimi','oejimong'] if who=='both' else [who]
    imgs=[fit_h(load(n),int(h*(1.0 if n=='daekimi' else 0.96))) for n in names]
    w=sum(i.width for i in imgs)+gap*(len(imgs)-1);hh=max(i.height for i in imgs)
    out=Image.new('RGBA',(w,hh),(0,0,0,0));x=0
    for i in imgs:out.alpha_composite(i,(x,hh-i.height));x+=i.width+gap
    return out

def backdrop(raw,blur=0,tint=None):
    if raw:
        bg=Image.open(io.BytesIO(raw)).convert('RGB').resize((SIZE,SIZE),Image.LANCZOS)
        if blur:bg=bg.filter(ImageFilter.GaussianBlur(blur))
    else:
        bg=Image.new('RGB',(SIZE,SIZE),(236,230,250))
    return bg.convert('RGBA')

def keyring(who,bg_raw,variant=0):
    c=backdrop(bg_raw,blur=6)
    art=outline(pair(who,540 if who=='both' else 600),22)
    cx,cy=SIZE//2,SIZE//2+110
    paste_center(c,art,cx,cy)
    # 실루엣의 맨 위 지점(가운데 근처)에 고리 구멍 탭을 붙인다
    a=art.getchannel('A');ox,oy=cx-art.width//2,cy-art.height//2
    best=None
    for dx in range(-art.width//4,art.width//4+1,6):
        x=art.width//2+dx
        col=a.crop((x,0,x+1,art.height)).getbbox()
        if col and (best is None or col[1]<best[1]):best=(x,col[1])
    tx,ty=ox+best[0],oy+best[1]+14
    d=ImageDraw.Draw(c)
    d.ellipse((tx-46,ty-46,tx+46,ty+46),fill=(255,255,255,255))
    d.ellipse((tx-17,ty-17,tx+17,ty+17),fill=(120,110,140,255))
    d.ellipse((tx-26,ty-150,tx+26,ty-6),outline=(140,140,156,255),width=8)   # 고리
    d.ellipse((tx-22,ty-146,tx+22,ty-10),outline=(222,222,232,255),width=3)
    d.line((tx,ty-8,tx,ty+4),fill=(140,140,156,255),width=8)
    return c

def sticker(who,bg_raw,variant=0):
    c=Image.new('RGBA',(SIZE,SIZE),(244,241,250,255))
    d=ImageDraw.Draw(c);d.rounded_rectangle((70,70,SIZE-70,SIZE-70),radius=44,fill=(255,255,255,255),outline=(222,214,240,255),width=4)
    names=['daekimi','oejimong'] if who=='both' else [who]
    spots=[(0.30,0.34,0.42,-6),(0.70,0.34,0.42,5),(0.20,0.72,0.20,-10),(0.42,0.74,0.22,8),(0.64,0.72,0.20,-4),(0.84,0.74,0.22,10)] if variant==0 else \
          [(0.30,0.36,0.40,6),(0.70,0.36,0.40,-5),(0.22,0.74,0.22,9),(0.46,0.73,0.20,-8),(0.68,0.74,0.22,5),(0.86,0.72,0.20,-10)]
    for i,(sx,sy,sc,ang) in enumerate(spots):
        n=names[i%len(names)];h=int(SIZE*sc)
        im=fit_h(load(n),h)
        if i>=2 and i%2==1:im=ImageOps.mirror(im)
        paste_center(c,outline(im,9),SIZE*sx,SIZE*sy,shadowed=False,angle=ang)
    return c

def poster(who,bg_raw,variant=0):
    c=backdrop(bg_raw,blur=4)
    veil=Image.new('RGBA',c.size,(255,255,255,60));c.alpha_composite(veil)
    art=pair(who,500 if who=='both' else 620,gap=-6)
    paste_center(c,art,SIZE//2,SIZE-art.height//2-40,shadowed=True)
    d=ImageDraw.Draw(c);d.rectangle((24,24,SIZE-24,SIZE-24),outline=(255,255,255,235),width=10)
    return c

def worn(who,bg_raw,variant=0,scale=0.40,cy=0.50):
    """에코백·티셔츠: 제품 사진 중앙(인쇄 영역)에 원본 캐릭터를 인쇄한 것처럼 올린다."""
    c=backdrop(bg_raw)
    art=pair(who,int(SIZE*scale*(1.25 if who=='both' else 1.5)),gap=-14)
    flat=Image.new('RGBA',art.size,(0,0,0,0));flat.alpha_composite(art)
    # 천에 인쇄된 느낌: 약간 투명하게
    a=flat.getchannel('A').point(lambda v:int(v*0.93));flat.putalpha(a)
    c.alpha_composite(flat,(int(SIZE/2-flat.width/2),int(SIZE*cy-flat.height/2)))
    return c

def magnet(who,bg_raw,variant=0):
    c=backdrop(bg_raw,blur=10)
    names=['daekimi','oejimong'] if who=='both' else [who]
    n=names[variant%len(names)]
    art=outline(fit_h(load(n),520),34)
    paste_center(c,art,SIZE//2,SIZE//2,shadowed=True,angle=-4 if variant%2==0 else 4)
    return c

RENDER={'keyring':keyring,'sticker':sticker,'poster':poster,'ecobag':lambda w,b,v=0:worn(w,b,v,0.27,0.60),
        'tshirt':lambda w,b,v=0:worn(w,b,v,0.27,0.46),'magnet':magnet}

def last_used():
    """방금 compose 한 시안에 실제로 그린 캐릭터."""
    return getattr(_ctx,'last',())

def compose(item,who,bg_raw,variant=0,poses=None):
    _ctx.poses=poses or {};_ctx.used=set()
    try:
        img=RENDER[item](who,bg_raw,variant).convert('RGB')
    finally:
        _ctx.last=tuple(sorted(_ctx.used));_ctx.poses={};_ctx.used=None
    buf=io.BytesIO();img.save(buf,'JPEG',quality=90);return base64.b64encode(buf.getvalue()).decode()


# ───────── 신규 후보 품목 (공식 캐릭터 원본을 그대로 올린다)
PALETTE=[(255,226,236),(226,240,255),(255,244,214),(230,246,226),(238,230,255)]

def _one(who,variant):
    return who if who!='both' else ('daekimi' if variant%2==0 else 'oejimong')

def _circle_mask(d):
    m=Image.new('L',(d*4,d*4),0);ImageDraw.Draw(m).ellipse((0,0,d*4-1,d*4-1),fill=255);return m.resize((d,d),Image.LANCZOS)

def _badge(who,d,variant,rim=14):
    """원형 배지: 파스텔 바탕 + 캐릭터(원 안에서 잘림) + 흰 테두리·금속 가장자리."""
    base=Image.new('RGBA',(d,d),PALETTE[variant%len(PALETTE)]+(255,))
    one=who if who!='both' else ('daekimi' if variant%2==0 else 'oejimong')   # 배지는 작아서 캐릭터 한 명을 크게 쓴다
    art=fit_h(load(one),int(d*0.86))
    if art.width>d*0.9:art=art.resize((int(d*0.9),int(art.height*d*0.9/art.width)),Image.LANCZOS)
    base.alpha_composite(art,(int((d-art.width)/2),int(d*0.16)))
    out=Image.new('RGBA',(d+rim*2,d+rim*2),(0,0,0,0))
    ring=Image.new('RGBA',out.size,(205,208,218,255));ring.putalpha(_circle_mask(d+rim*2));out.alpha_composite(ring)
    inner=Image.new('RGBA',(d,d),(0,0,0,0));inner.paste(base,(0,0),_circle_mask(d));out.alpha_composite(inner,(rim,rim))
    return out

def pinbutton(who,bg_raw,variant=0):
    c=backdrop(bg_raw,blur=10);b=_badge(who,520,variant);paste_center(c,b,SIZE//2,SIZE//2,shadowed=True,angle=-3)
    return c

def griptok(who,bg_raw,variant=0):
    c=backdrop(bg_raw,blur=10)
    phone=Image.new('RGBA',(430,820),(0,0,0,0));d=ImageDraw.Draw(phone);d.rounded_rectangle((0,0,429,819),radius=70,fill=(244,244,250,255),outline=(205,205,220,255),width=6)
    paste_center(c,phone,SIZE//2,SIZE//2,shadowed=True,angle=-6)
    b=_badge(who,300,variant,rim=10);paste_center(c,b,SIZE//2,SIZE//2+60,shadowed=True,angle=-6)
    return c

def acrylic_stand(who,bg_raw,variant=0):
    c=backdrop(bg_raw,blur=10)
    art=outline(pair(who,440 if who=='both' else 600),16,(255,255,255,235))
    cx,cy=SIZE//2,SIZE//2-30
    base=Image.new('RGBA',(art.width+80,70),(0,0,0,0));ImageDraw.Draw(base).rounded_rectangle((0,0,base.width-1,69),radius=30,fill=(238,242,250,215),outline=(200,208,225,255),width=4)
    paste_center(c,base,cx,cy+art.height//2-6,shadowed=True)
    paste_center(c,art,cx,cy,shadowed=True)
    return c

def postcard(who,bg_raw,variant=0):
    c=backdrop(bg_raw,blur=10)
    card=Image.new('RGBA',(760,540),(255,255,255,255));d=ImageDraw.Draw(card)
    d.rectangle((26,26,733,513),fill=PALETTE[variant%len(PALETTE)]+(255,))
    art=pair(who,430 if who=='both' else 470,gap=-8);card.alpha_composite(art,(int((760-art.width)/2),540-26-art.height))
    d.rectangle((26,26,733,513),outline=(255,255,255,255),width=2)
    paste_center(c,card,SIZE//2,SIZE//2,shadowed=True,angle=-5 if variant%2==0 else 5)
    return c

def maskingtape(who,bg_raw,variant=0):
    c=Image.new('RGBA',(SIZE,SIZE),(247,244,252,255))
    n=['daekimi','oejimong'] if who=='both' else [who]
    strip=Image.new('RGBA',(900,250),PALETTE[variant%len(PALETTE)]+(255,));x=20;i=0
    while x<880:
        im=fit_h(load(n[i%len(n)]),190);
        if i%2:im=ImageOps.mirror(im)
        strip.alpha_composite(im,(x,30));x+=im.width+22;i+=1
    mask=Image.new('L',strip.size,255);ImageDraw.Draw(mask).polygon([(0,0),(14,40),(0,80),(14,125),(0,170),(14,210),(0,249)],fill=0)
    strip.putalpha(Image.eval(mask,lambda v:230 if v else 0))
    paste_center(c,strip,SIZE//2,SIZE//2-120,shadowed=True,angle=-4)
    roll=Image.new('RGBA',(360,360),(0,0,0,0));d=ImageDraw.Draw(roll)
    d.ellipse((0,0,359,359),fill=PALETTE[(variant+1)%len(PALETTE)]+(255,));art=fit_h(load(n[0]),150);roll.alpha_composite(art,(int((360-art.width)/2),12))
    d.ellipse((120,120,239,239),fill=(247,244,252,255),outline=(200,196,215,255),width=6);d.ellipse((0,0,359,359),outline=(200,196,215,255),width=6)
    paste_center(c,roll,SIZE//2,SIZE//2+250,shadowed=True)
    return c

RENDER.update({'pinbutton':pinbutton,'griptok':griptok,'acrylic_stand':acrylic_stand,'postcard':postcard,'maskingtape':maskingtape,
    'pouch':lambda w,b,v=0:worn(w,b,v,0.17,0.57),'handkerchief':lambda w,b,v=0:worn(w,b,v,0.20,0.48),'notebook':lambda w,b,v=0:worn(_one(w,v),b,v,0.34,0.52),
    'phonecase':lambda w,b,v=0:worn(_one(w,v),b,v,0.26,0.50),'blanket':lambda w,b,v=0:worn(w,b,v,0.26,0.50)})
