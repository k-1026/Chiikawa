"""굿즈 시안 이미지(Cloudflare Workers AI · FLUX)와 시안에 맞춘 제작 계획서(md)."""
import base64,json,os,secrets,ssl,time,urllib.error,urllib.request

MODEL='@cf/black-forest-labs/flux-1-schnell'
MASCOT=('Two original alien mascots: Daekimi, a sky-blue cat alien with big round eyes and a small antenna, '
        'and Oejimong, a green dog alien with floppy ears. Cute, friendly, rounded shapes.')
# 굿즈 종류 → (한글 이름, 영어 디자인 설명, 규격·재질 초안, 제작 주의)
ITEMS={
 'keyring':('아크릴 키링','an acrylic keyring design, die-cut silhouette with white border, front view, centered on plain background','5~6cm · 투명 아크릴 3T · 양면 인쇄 · 볼체인 포함(추정)','어린이 대상 판매 시 KC 인증·유해물질 시험 확인 필요'),
 'sticker':('스티커 시트','a sticker sheet design, several die-cut stickers with white borders, flat colors, plain background','A6 시트 · 반광 스티커 · 코팅(추정)','잉크 번짐·재단 오차 샘플 확인 필요'),
 'poster':('포스터','a festival poster illustration, vertical layout with large empty area for title text, bold colors','A2~A3 · 아트지 · 무광 코팅(추정)','게시 장소별 허가·현수막 규격 확인 필요'),
 'ecobag':('에코백','a tote bag print design, bold simple artwork centered, flat vector style, plain background','캔버스 · 실크스크린 1~2도(추정)','색상 수에 따라 제작 단가 변동'),
 'tshirt':('티셔츠','a t-shirt chest print design, bold simple artwork, flat vector, plain background','면 · 사이즈 3종 이상(추정)','사이즈 비율 사전 조사 필요'),
 'magnet':('마그넷','a fridge magnet design, die-cut silhouette, glossy flat colors, plain background','6~7cm · 아크릴 또는 PVC(추정)','자석 부착력·모서리 안전 확인'),
}
class GoodsError(Exception):pass

# 컨셉·대상·예산 글에서 키워드를 찾아 굿즈 종류에 점수를 준다(AI가 안 될 때도 추천은 나온다).
RULES=[
 (('어린이','아이','가족','초등','유아'),{'sticker':3,'keyring':2,'magnet':1},'가족·어린이 대상'),
 (('청년','mz','sns','인스타','사진','포토','인증'),{'keyring':3,'sticker':3,'magnet':1},'SNS 인증·수집 성향'),
 (('기념','소장','한정','공식','굿즈샵','판매'),{'tshirt':3,'poster':2,'keyring':1},'소장·판매 목적'),
 (('실용','일상','친환경','제로웨이스트','장바구니'),{'ecobag':3,'tshirt':1},'실용·친환경 방향'),
 (('우주','사투리','캐릭터','마스코트','대키미','외지몽'),{'keyring':2,'sticker':2,'poster':1},'캐릭터 중심 컨셉'),
 (('관광','외지인','여행','기념품','방문'),{'magnet':3,'poster':1,'keyring':1},'관광·기념품 수요'),
 (('행사장','현장','무료','증정','참여','스탬프'),{'sticker':2,'keyring':1},'현장 증정·스탬프 보상'),
]
NOTE={'keyring':'휴대·수집이 쉬운 대표 굿즈예요','sticker':'단가가 낮고 많이 나눠 주기 좋아요','poster':'소장·전시용으로 컨셉을 크게 보여줘요','ecobag':'일상에서 계속 쓰여 홍보 효과가 오래가요','tshirt':'스태프·참가자 단체복으로도 쓸 수 있어요','magnet':'부피가 작아 관광 기념품으로 좋아요'}
def recommend_rules(text,budget_text=''):
    t=(text or '').lower();score={k:0 for k in ITEMS};why={k:[] for k in ITEMS}
    for keys,pts,reason in RULES:
        if any(k in t for k in keys):
            for it,v in pts.items():score[it]+=v;why[it].append(reason)
    if any(k in (budget_text or '') for k in ('적','소액','저예산','천만')):
        for it in ('sticker','magnet'):score[it]+=1;why[it].append('예산이 작은 조건')
    base={'keyring':2,'sticker':2,'poster':1,'magnet':1,'ecobag':1,'tshirt':0}  # 아무 단서가 없을 때의 기본 순서
    ranked=sorted(ITEMS,key=lambda k:(-(score[k]+base[k]),k))[:3]
    return [{'item':k,'name':ITEMS[k][0],'reason':((why[k][0]+'에 맞고, ' if why[k] else '')+NOTE[k])} for k in ranked]

def recommend_ai(concept,context):
    """Gemini 가 컨셉을 읽고 굿즈 3종과 이유를 고른다. 실패하면 None."""
    key,model=os.getenv('GEMINI_API_KEY'),os.getenv('GEMINI_MODEL')
    if not key or not model:return None
    names=', '.join('%s(%s)'%(k,v[0]) for k,v in ITEMS.items())
    prompt=('대구 지역 축제 굿즈 기획자입니다. 아래 컨셉과 조건에 가장 잘 맞는 굿즈 종류 3개를 골라 JSON 배열로만 답하세요. '
            '형식: [{"item":"keyring","reason":"한 문장(한국어, 50자 이내)"}]. item 은 반드시 다음 중에서만: '+names+'\n컨셉: '+concept+'\n조건: '+context)
    try:
        url='https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent'%model
        body={'contents':[{'parts':[{'text':prompt}]}],'generationConfig':{'responseMimeType':'application/json'}}
        with _post(url,body,{'Content-Type':'application/json','x-goog-api-key':key},20) as r:
            arr=json.loads(json.load(r)['candidates'][0]['content']['parts'][0]['text'])
        out=[]
        for a in arr:
            if a.get('item') in ITEMS and a['item'] not in [o['item'] for o in out]:
                out.append({'item':a['item'],'name':ITEMS[a['item']][0],'reason':str(a.get('reason',''))[:120]})
        return out[:3] or None
    except Exception:return None

def recommend(concept,workspace):
    concept=str(concept or '').strip()[:300]
    if len(concept)<2:raise GoodsError('컨셉을 먼저 입력해 주세요.')
    c=(workspace.get('conditions') or {});plan=workspace.get('plan') or {}
    ctx=' / '.join('%s: %s'%(k,v) for k,v in (('대상',c.get('target') or plan.get('target')),('예산',c.get('budget_total') or plan.get('budget_total')),('규모',c.get('scale') or plan.get('scale')),('테마',c.get('theme'))) if v)
    ai=recommend_ai(concept,ctx)
    return {'recommendations':ai or recommend_rules(concept+' '+ctx,str(c.get('budget_total') or '')),'by':'ai' if ai else 'rules'}

def ensure_table(store):
    if store.pg:return  # Supabase 는 supabase/003_goods.sql 로 미리 만든다
    with store.db() as db:
        db.execute('CREATE TABLE IF NOT EXISTS goods_designs(id TEXT PRIMARY KEY,user_id INTEGER NOT NULL,item TEXT NOT NULL,concept TEXT NOT NULL,prompt TEXT NOT NULL,image TEXT NOT NULL,created_at INTEGER NOT NULL)')

def configured():
    return bool(os.getenv('CF_ACCOUNT_ID') and os.getenv('CF_API_TOKEN'))

def _ctx():
    try:return ssl.create_default_context()
    except Exception:return None

def _post(url,body,headers,timeout):
    req=urllib.request.Request(url,data=json.dumps(body).encode(),headers=headers)
    try:
        return urllib.request.urlopen(req,timeout=timeout)
    except urllib.error.URLError as e:
        if isinstance(getattr(e,'reason',None),ssl.SSLCertVerificationError) and os.path.exists('/etc/ssl/cert.pem'):
            return urllib.request.urlopen(req,timeout=timeout,context=ssl.create_default_context(cafile='/etc/ssl/cert.pem'))
        raise

def english_concept(concept):
    """컨셉(한글)을 이미지 모델이 알아듣는 짧은 영어로 옮긴다. 실패하면 원문을 그대로 쓴다."""
    key,model=os.getenv('GEMINI_API_KEY'),os.getenv('GEMINI_MODEL')
    if not key or not model:return concept
    try:
        url='https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent'%model
        body={'contents':[{'parts':[{'text':'Translate this Korean festival concept into one short English phrase of visual keywords (max 25 words), output only the phrase:\n'+concept}]}]}
        with _post(url,body,{'Content-Type':'application/json','x-goog-api-key':key},15) as r:
            t=json.load(r)['candidates'][0]['content']['parts'][0]['text'].strip()
        return t[:300] or concept
    except Exception:return concept

def make_prompt(item,concept):
    name,desc,_,_=ITEMS[item]
    return '%s %s Festival concept: %s. Absolutely no text, letters, numbers or writing anywhere in the image.'%(desc[0].upper()+desc[1:]+'.',MASCOT,english_concept(concept))

def generate_image(prompt):
    a,t=os.getenv('CF_ACCOUNT_ID'),os.getenv('CF_API_TOKEN')
    if not a or not t:raise GoodsError('굿즈 시안 이미지 서비스가 아직 연결되지 않았습니다.')
    body={'prompt':prompt,'steps':6}
    try:
        with _post('https://api.cloudflare.com/client/v4/accounts/%s/ai/run/%s'%(a,MODEL),body,{'Authorization':'Bearer '+t,'Content-Type':'application/json'},90) as r:
            d=json.load(r)
    except urllib.error.HTTPError as e:
        raise GoodsError('시안 이미지를 만들지 못했습니다(이용 한도 초과일 수 있어요). 잠시 후 다시 시도해 주세요.' if e.code in (429,403) else '시안 이미지를 만들지 못했습니다.')
    except Exception:raise GoodsError('시안 이미지 서비스에 연결하지 못했습니다.')
    img=(d.get('result') or {}).get('image')
    if not img:raise GoodsError('시안 이미지를 받지 못했습니다.')
    return img  # base64 JPEG

def create(store,uid,item,concept,count):
    if item not in ITEMS:raise GoodsError('지원하지 않는 굿즈 종류입니다.')
    concept=str(concept or '').strip()[:300]
    if len(concept)<2:raise GoodsError('컨셉을 입력해 주세요.')
    count=max(1,min(3,int(count or 2)))
    ensure_table(store)
    prompt=make_prompt(item,concept);out=[]
    poses=['','Different pose and composition.','Alternative layout, mascots in a new arrangement.']
    for i in range(count):
        img=generate_image((prompt+' '+poses[i]).strip())
        did=secrets.token_hex(8)
        with store.db() as db:
            db.execute('INSERT INTO goods_designs(id,user_id,item,concept,prompt,image,created_at) VALUES(?,?,?,?,?,?,?)',(did,uid,item,concept,prompt,img,int(time.time())))
        out.append({'id':did,'item':item,'concept':concept})
    return out

def list_designs(store,uid):
    ensure_table(store)
    with store.db() as db:
        rows=db.execute('SELECT id,item,concept,created_at FROM goods_designs WHERE user_id=? ORDER BY created_at DESC LIMIT 60',(uid,)).fetchall()
    return [{'id':r['id'],'item':r['item'],'concept':r['concept'],'created_at':r['created_at'],'item_name':ITEMS.get(r['item'],('굿즈',))[0]} for r in rows]

def image_bytes(store,uid,did):
    ensure_table(store)
    with store.db() as db:
        r=db.execute('SELECT image FROM goods_designs WHERE id=? AND user_id=?',(str(did)[:40],uid)).fetchone()
    if not r:raise GoodsError('시안을 찾을 수 없습니다.')
    return base64.b64decode(r['image'])

def production_plan(store,uid,did,quantity,workspace):
    ensure_table(store)
    with store.db() as db:
        r=db.execute('SELECT item,concept,prompt,created_at FROM goods_designs WHERE id=? AND user_id=?',(str(did)[:40],uid)).fetchone()
    if not r:raise GoodsError('시안을 찾을 수 없습니다.')
    name,_,spec,caution=ITEMS[r['item']]
    try:qty=max(1,min(100000,int(quantity)))
    except (TypeError,ValueError):raise GoodsError('수량을 숫자로 입력해 주세요.')
    plan=workspace.get('plan') or {}
    fest=plan.get('festival_name') or '(축제명 미정)'
    md=f"""# {fest} · {name} 제작 계획서 (초안)

> 이 문서는 AI가 만든 시안에 맞춘 **초안**입니다. 표시한 [추정]·[확인 필요] 항목은 실제 업체 견적과 담당자 확인 뒤 확정해 주세요.

## 1. 개요
- 축제: {fest}
- 굿즈: {name}
- 컨셉: {r['concept']}
- 시안 번호: {did}
- 계획 수량: {qty:,}개 [가정: 담당자 입력값]

## 2. 시안 설명
- 마스코트(대키미·외지몽)를 컨셉에 맞게 표현한 AI 생성 시안입니다.
- 시안 그대로 인쇄하기 어렵습니다. 최종 제작용 벡터 파일(AI/PDF)은 디자이너가 다시 정리해야 합니다 [확인 필요].
- 생성 지시문(영문): {r['prompt']}

## 3. 사양
- 규격·재질: {spec}
- 주의: {caution}

## 4. 수량·예산
| 항목 | 내용 |
|---|---|
| 수량 | {qty:,}개 |
| 단가 | [확인 필요] 업체 3곳 이상 견적 비교 |
| 제작비 합계 | 단가 × 수량 (견적 후 기입) |
| 예비분 | 약 5~10% 추가 제작 [추정] |

## 5. 제작 일정 (축제 개막일 기준 역산) [추정]
| 시점 | 할 일 |
|---|---|
| D-60 | 디자인 확정, 업체 견적 요청 |
| D-45 | 업체 선정·계약, 시안 파일 전달 |
| D-35 | 샘플(1차) 수령·검수 |
| D-25 | 수정 반영·본 제작 시작 |
| D-10 | 납품·수량 검수 |
| D-3 | 현장 반입·판매·배포 위치 확정 |

## 6. 점검 목록
- [ ] 마스코트·로고 사용 승인 여부
- [ ] 제작 업체 견적 3건 이상
- [ ] 안전·인증(어린이 대상이면 KC 등) 확인
- [ ] 샘플 검수(색상·재단·내구성)
- [ ] 판매·배포 방식(무료 증정/판매) 및 재고 관리 계획

## 7. 근거 표시
- [확인] 시안·컨셉: 시스템에 저장된 값
- [가정] 수량: 담당자 입력
- [추정] 규격·일정: 일반적인 제작 관행. 업체와 확정 필요
"""
    return {'markdown':md,'filename':'제작계획서_%s_%s.md'%(name,did[:6])}
