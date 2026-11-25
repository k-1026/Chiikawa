"""굿즈 시안 합성: 공식 캐릭터 원본 이미지(투명 PNG)를 그대로 굿즈 모양에 올린다.
AI(FLUX)는 배경·제품 사진만 만들고, 캐릭터는 AI가 다시 그리지 않으므로 원본과 같다."""
import base64,io,math
from pathlib import Path
from PIL import Image,ImageChops,ImageDraw,ImageFilter,ImageOps

ASSETS=Path(__file__).resolve().parents[1]/'assets_v06'
CHARS={'daekimi':'hero_daekimi.png','oejimong':'hero_oejimong.png'}
SIZE=1024

def load(name):
    return Image.open(ASSETS/CHARS[name]).convert('RGBA')

def fit_h(img,h):
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

def compose(item,who,bg_raw,variant=0):
    img=RENDER[item](who,bg_raw,variant).convert('RGB')
    buf=io.BytesIO();img.save(buf,'JPEG',quality=90);return base64.b64encode(buf.getvalue()).decode()
