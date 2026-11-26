"""굿즈 시안 이미지(Cloudflare Workers AI · FLUX)와 시안에 맞춘 제작 계획서(md)."""
import base64,json,os,secrets,ssl,sys,time,urllib.error,urllib.request
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'vendor'))

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
def recommend_rules(text,budget_text='',exclude=()):
    t=(text or '').lower();score={k:0 for k in ITEMS};why={k:[] for k in ITEMS}
    for keys,pts,reason in RULES:
        if any(k in t for k in keys):
            for it,v in pts.items():score[it]+=v;why[it].append(reason)
    if any(k in (budget_text or '') for k in ('적','소액','저예산','천만')):
        for it in ('sticker','magnet'):score[it]+=1;why[it].append('예산이 작은 조건')
    base={'keyring':2,'sticker':2,'poster':1,'magnet':1,'ecobag':1,'tshirt':0}  # 아무 단서가 없을 때의 기본 순서
    ranked=sorted((k for k in ITEMS if k not in exclude),key=lambda k:(-(score[k]+base[k]),k))[:3]
    return [{'item':k,'name':ITEMS[k][0],'reason':((why[k][0]+'에 맞고, ' if why[k] else '')+NOTE[k])} for k in ranked]

def recommend_ai(concept,context,exclude=()):
    """Gemini 가 컨셉을 읽고 굿즈 3종과 이유를 고른다. 실패하면 None."""
    key,model=os.getenv('GEMINI_API_KEY'),os.getenv('GEMINI_MODEL')
    if not key or not model:return None
    names=', '.join('%s(%s)'%(k,v[0]) for k,v in ITEMS.items() if k not in exclude)
    prompt=('대구 지역 축제 굿즈 기획자입니다. 아래 컨셉과 조건에 가장 잘 맞는 굿즈 종류 3개를 골라 JSON 배열로만 답하세요. '
            '형식: [{"item":"keyring","reason":"한 문장(한국어, 50자 이내)"}]. item 은 반드시 다음 중에서만: '+names+'\n컨셉: '+concept+'\n조건: '+context)
    try:
        url='https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent'%model
        body={'contents':[{'parts':[{'text':prompt}]}],'generationConfig':{'responseMimeType':'application/json'}}
        with _post(url,body,{'Content-Type':'application/json','x-goog-api-key':key},20) as r:
            arr=json.loads(json.load(r)['candidates'][0]['content']['parts'][0]['text'])
        out=[]
        for a in arr:
            if a.get('item') in ITEMS and a['item'] not in exclude and a['item'] not in [o['item'] for o in out]:
                out.append({'item':a['item'],'name':ITEMS[a['item']][0],'reason':str(a.get('reason',''))[:120]})
        return out[:3] or None
    except Exception:return None

def recommend(concept,workspace,exclude=()):
    concept=str(concept or '').strip()[:300]
    if len(concept)<2:raise GoodsError('컨셉을 먼저 입력해 주세요.')
    c=(workspace.get('conditions') or {});plan=workspace.get('plan') or {}
    ctx=' / '.join('%s: %s'%(k,v) for k,v in (('대상',c.get('target') or plan.get('target')),('예산',c.get('budget_total') or plan.get('budget_total')),('규모',c.get('scale') or plan.get('scale')),('테마',c.get('theme'))) if v)
    exclude=[x for x in (exclude or []) if x in ITEMS]
    reset=len(exclude)>=len(ITEMS)  # 6종을 모두 보여 줬으면 처음부터 다시
    if reset:exclude=[]
    ai=recommend_ai(concept,ctx,exclude)
    recs=ai or recommend_rules(concept+' '+ctx,str(c.get('budget_total') or ''),exclude)
    return {'recommendations':recs,'by':'ai' if ai else 'rules','reset':reset,'remaining':len([k for k in ITEMS if k not in exclude and k not in [r['item'] for r in recs]])}

def ensure_table(store):
    if store.pg:return  # Supabase 는 supabase/003·004_goods*.sql 로 미리 만든다
    with store.db() as db:
        db.execute("CREATE TABLE IF NOT EXISTS goods_designs(id TEXT PRIMARY KEY,user_id INTEGER NOT NULL,item TEXT NOT NULL,concept TEXT NOT NULL,prompt TEXT NOT NULL,image TEXT NOT NULL,created_at INTEGER NOT NULL,selected INTEGER NOT NULL DEFAULT 0,who TEXT NOT NULL DEFAULT 'both',pose TEXT NOT NULL DEFAULT '')")
        cols={r[1] for r in db.execute('PRAGMA table_info(goods_designs)').fetchall()}
        for c,d in (('selected','INTEGER NOT NULL DEFAULT 0'),('who',"TEXT NOT NULL DEFAULT 'both'"),('pose',"TEXT NOT NULL DEFAULT ''")):
            if c not in cols:db.execute('ALTER TABLE goods_designs ADD COLUMN %s %s'%(c,d))

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

BG={  # 캐릭터는 넣지 않는다(원본 이미지를 따로 합성). 배경·제품 사진만 만든다.
 'keyring':'A dreamy festival backdrop scene, soft focus, empty center, {c}.',
 'poster':'A vivid festival poster background illustration, large empty area in the lower center, {c}.',
 'magnet':'A soft pastel festival backdrop with bokeh lights, empty center, {c}.',
 'ecobag':'A plain blank cream canvas tote bag, front view, flat lay product photo on a soft background, no print, no logo.',
 'tshirt':'A plain blank white t-shirt, front view, flat lay product photo on a soft background, no print, no logo.',
}
NEEDS_BG=('ecobag','tshirt')  # 제품 사진이 없으면 만들 수 없는 종류
def make_prompt(item,concept):
    if item not in BG:return ''
    return BG[item].format(c=english_concept(concept))+' No characters, no animals, no people, no text, no letters, no writing.'

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

def create(store,uid,item,concept,count,who='both'):
    import goods_compose_v06 as C
    if item not in ITEMS:raise GoodsError('지원하지 않는 굿즈 종류입니다.')
    if who not in ('both','daekimi','oejimong'):who='both'
    concept=str(concept or '').strip()[:300]
    if len(concept)<2:raise GoodsError('컨셉을 입력해 주세요.')
    count=max(1,min(3,int(count or 2)))
    ensure_table(store)
    prompt=make_prompt(item,concept);out=[]
    for i in range(count):
        raw=None
        if prompt:
            try:raw=base64.b64decode(generate_image(prompt))
            except GoodsError:
                if item in NEEDS_BG:raise
        img=C.compose(item,who,raw,i)
        did=secrets.token_hex(8)
        with store.db() as db:
            db.execute('INSERT INTO goods_designs(id,user_id,item,concept,prompt,image,created_at,who,pose) VALUES(?,?,?,?,?,?,?,?,?)',(did,uid,item,concept,(prompt or '(배경 없음: 캐릭터 원본 합성)'),img,int(time.time()),who,''))
        out.append({'id':did,'item':item,'concept':concept})
    return out

def list_designs(store,uid):
    ensure_table(store)
    with store.db() as db:
        rows=db.execute('SELECT id,item,concept,created_at,selected,who,pose FROM goods_designs WHERE user_id=? ORDER BY created_at DESC LIMIT 60',(uid,)).fetchall()
    return [{'id':r['id'],'item':r['item'],'concept':r['concept'],'created_at':r['created_at'],'selected':bool(r['selected']),'who':r['who'],'pose':r['pose'],'item_name':ITEMS.get(r['item'],('굿즈',))[0]} for r in rows]

def select_design(store,uid,did,selected):
    ensure_table(store)
    with store.db() as db:
        r=db.execute('SELECT id FROM goods_designs WHERE id=? AND user_id=?',(str(did)[:40],uid)).fetchone()
        if not r:raise GoodsError('시안을 찾을 수 없습니다.')
        db.execute('UPDATE goods_designs SET selected=? WHERE id=? AND user_id=?',(1 if selected else 0,str(did)[:40],uid))
    return {'id':str(did)[:40],'selected':bool(selected)}

def image_bytes(store,uid,did):
    ensure_table(store)
    with store.db() as db:
        r=db.execute('SELECT image FROM goods_designs WHERE id=? AND user_id=?',(str(did)[:40],uid)).fetchone()
    if not r:raise GoodsError('시안을 찾을 수 없습니다.')
    return base64.b64decode(r['image'])

WHO_TXT={'both':'대키미 + 외지몽','daekimi':'대키미','oejimong':'외지몽'}

def selected_designs(store,uid,workspace=None):
    """담당자가 선택한 시안(기획안의 굿즈 파트에 쓴다)."""
    ensure_table(store)
    with store.db() as db:
        rows=db.execute('SELECT id,item,concept,image,who,pose FROM goods_designs WHERE user_id=? AND selected=1 ORDER BY created_at DESC LIMIT 8',(uid,)).fetchall()
    out=[]
    for r in rows:
        name,_,spec,_=ITEMS.get(r['item'],('굿즈','','',''))
        out.append({'did':r['id'],'item':r['item'],'item_name':name,'concept':r['concept'],'image_b64':r['image'],'who':r['who'],'who_txt':WHO_TXT.get(r['who'],'대키미 + 외지몽'),'spec':spec,'pose':r['pose']})
    return out

def _plan_info(store,uid,did,quantity,workspace):
    import goods_doc_v06 as D
    ensure_table(store)
    with store.db() as db:
        r=db.execute('SELECT item,concept,image,selected,who,pose FROM goods_designs WHERE id=? AND user_id=?',(str(did)[:40],uid)).fetchone()
    if not r:raise GoodsError('시안을 찾을 수 없습니다.')
    try:qty=max(1,min(100000,int(quantity)))
    except (TypeError,ValueError):raise GoodsError('수량을 숫자로 입력해 주세요.')
    plan=workspace.get('plan') or {};cond=workspace.get('conditions') or {}
    name,_,spec,_=ITEMS[r['item']]
    return {'item_key':r['item'],'item_name':name,'spec':spec,'concept':r['concept'],'did':str(did)[:40],'image_b64':r['image'],'who':r['who'],'pose':r['pose'],
            'qty':qty,'festival_name':plan.get('festival_name') or '(축제명 미정)','host':plan.get('host') or cond.get('host') or '','budget_total':plan.get('budget_total') or cond.get('budget_total') or '',
            'festival':D.festival_date(workspace),'selected':bool(r['selected'])}

MIN_PAGES=5
def _pdf_pages(data):
    import re
    return len(re.findall(rb'/Type\s*/Page[^s]',data))

def export_plan(store,uid,did,quantity,workspace,fmt):
    import goods_doc_v06 as D,plan_export_v06 as X
    if fmt not in ('pdf','docx','hwpx'):raise GoodsError('지원하지 않는 형식입니다.')
    info=_plan_info(store,uid,did,quantity,workspace)
    model=D.goods_plan_model(info)
    data=getattr(X,'to_'+fmt)(model)
    if fmt=='pdf' and _pdf_pages(data)<MIN_PAGES:
        raise GoodsError('계획서가 A4 %d쪽 미만으로 만들어졌습니다. 운영자에게 알려 주세요.'%MIN_PAGES)
    return data,'제작계획서_%s_%s.%s'%(info['item_name'],str(did)[:6],fmt)

def production_plan(store,uid,did,quantity,workspace):
    import goods_doc_v06 as D
    info=_plan_info(store,uid,did,quantity,workspace)
    return {'markdown':D.model_to_md(D.goods_plan_model(info)),'filename':'제작계획서_%s_%s.md'%(info['item_name'],str(did)[:6])}
