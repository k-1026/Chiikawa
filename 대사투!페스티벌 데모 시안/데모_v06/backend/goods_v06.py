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

# ───────── 굿즈 종류
# 팀 고정 8종(D02 2-1)과 스탬프 교환용·시상용, 그리고 예전 시안 목록의 6종은 "원래 있는 종류"라서 추천하지 않는다.
FIXED=('keyring','sticker','headband','magnet','ecobag','tshirt','eyemask','tumbler','poster')
NEW_ITEMS={
 'acrylic_stand':('아크릴 스탠드','','캐릭터 컷 + 받침대 · 투명 아크릴 · 높이 약 10~12cm (제안값)','받침대 안정성(쓰러짐)·얇은 돌출부 파손 확인','캐릭터 컷을 그대로 세워 책상·전시에 두기 좋음'),
 'pinbutton':('핀버튼(뱃지)','','지름 약 44mm 원형 · 틴 소재 · 핀 뒷면 (제안값)','핀 안전(어린이 대상은 KC 확인)·가장자리 마감 확인','작고 저렴해 수집·교환·스탬프 보상에 좋음'),
 'postcard':('엽서·포토카드 세트','','엽서 A6 · 포토카드 55×85mm 안팎 · 스노우지 (제안값)','인쇄 색감 차이·용지 두께 확인','여러 포즈를 한 세트로 묶어 수집욕을 살림'),
 'pouch':('파우치','','캔버스 또는 폴리 소재 · 지퍼 · 가로 약 20cm (제안값)','지퍼·박음질 품질, 인쇄 공법(전사·실크) 확인','일상에서 매일 쓰여 캐릭터가 오래 노출됨'),
 'handkerchief':('손수건','','면 · 약 40×40cm · 전사 인쇄 (제안값)','세탁 시 색 빠짐·원단 확인','여름 행사에 실용적이고 가벼워 부담 없는 기념품'),
 'notebook':('노트','','A5 · 스프링 또는 무선 · 표지 코팅 (제안값)','제본 방식·표지 마감 확인','사투리 메모·여행 기록용으로 활용도가 높음'),
 'phonecase':('폰케이스','','기종별 제작 · TPU 또는 하드 케이스 (제안값)','기종 범위(SKU 급증)·인쇄 내구성 확인','매일 손에 쥐는 물건이라 팬덤 굿즈로 인기'),
 'griptok':('그립톡','','지름 약 40mm · 접착면 · 에폭시 마감 (제안값)','접착력·에폭시 마감 확인','작은 면적에 캐릭터 얼굴을 살리기 좋음'),
 'maskingtape':('마스킹테이프','','폭 15~30mm · 길이 약 5m · 롤 (제안값)','패턴 반복 길이·재단 확인','캐릭터를 반복 패턴으로 쓰기 좋아 꾸미기 수요에 맞음'),
 'blanket':('담요','','플리스 또는 극세사 · 약 100×140cm · 전사 (제안값)','대형 인쇄 가능 업체·번짐 확인','야간·가을 행사에서 실용적인 소장 굿즈'),
}
for _k,_v in NEW_ITEMS.items():ITEMS[_k]=_v[:4]
NEW_KEYS=tuple(NEW_ITEMS)
NEW_NOTE={k:v[4] for k,v in NEW_ITEMS.items()}
GROUPS={'new':list(NEW_KEYS),'basic':[k for k in ('keyring','sticker','magnet','ecobag','tshirt','poster')]}

RULES=[
 (('어린이','아이','가족','초등','유아'),{'postcard':3,'maskingtape':2,'pinbutton':2,'notebook':1},'가족·어린이 대상'),
 (('청년','mz','sns','인스타','사진','포토','인증'),{'postcard':3,'griptok':3,'phonecase':2,'pinbutton':2},'SNS 인증·수집 성향'),
 (('기념','소장','한정','공식','굿즈샵','판매'),{'acrylic_stand':3,'postcard':2,'blanket':1,'pinbutton':1},'소장·판매 목적'),
 (('실용','일상','친환경','제로웨이스트'),{'pouch':3,'notebook':2,'handkerchief':2,'maskingtape':1},'실용·친환경 방향'),
 (('우주','사투리','캐릭터','마스코트','대키미','외지몽'),{'acrylic_stand':2,'pinbutton':2,'griptok':2,'postcard':1},'캐릭터 중심 컨셉'),
 (('관광','외지인','여행','기념품','방문'),{'postcard':3,'handkerchief':2,'pinbutton':1,'acrylic_stand':1},'관광·기념품 수요'),
 (('행사장','현장','무료','증정','참여','스탬프'),{'pinbutton':3,'maskingtape':2,'postcard':1},'현장 증정·스탬프 보상'),
 (('밤','야간','겨울','가을','추위','캠핑'),{'blanket':4,'pouch':1},'야간·쌀쌀한 시기 행사'),
]
BASE_ORDER={'pinbutton':3,'postcard':3,'acrylic_stand':2,'griptok':2,'maskingtape':2,'pouch':1,'notebook':1,'handkerchief':1,'phonecase':1,'blanket':0}

def _card(k,conn,check=None):
    return {'item':k,'name':ITEMS[k][0],'conn':conn,'check':check or ITEMS[k][3],'yoy':'실험 (신규 품목)','reason':conn}

def recommend_rules(text,budget_text='',exclude=(),n=5):
    t=(text or '').lower();score={k:0 for k in NEW_KEYS};tag={k:'' for k in NEW_KEYS}
    for keys,pts,label in RULES:
        if any(w in t for w in keys):
            for it,v in pts.items():
                score[it]+=v
                if not tag[it]:tag[it]=label
    if any(w in (budget_text or '') for w in ('적','소액','저예산','천만')):
        for it in ('pinbutton','maskingtape','postcard'):score[it]+=1
    ranked=sorted((k for k in NEW_KEYS if k not in exclude),key=lambda k:(-(score[k]+BASE_ORDER[k]),k))[:n]
    return [_card(k,('%s에 맞고, ' % tag[k] if tag[k] else '')+NEW_NOTE[k]) for k in ranked]

def recommend_ai(concept,context,exclude=(),n=5):
    """Gemini 가 컨셉·조건을 읽고 신규 후보 n종과 이유(연도 주제 연결 1줄·제작 확인 항목)를 고른다. 실패하면 None."""
    key,model=os.getenv('GEMINI_API_KEY'),os.getenv('GEMINI_MODEL')
    if not key or not model:return None
    pool=[k for k in NEW_KEYS if k not in exclude]
    if len(pool)<2:return None
    names=', '.join('%s(%s)'%(k,ITEMS[k][0]) for k in pool)
    prompt=('대구 지역 축제 굿즈 기획자입니다. 팀 규칙: 고정 품목과 다른 새 품목 후보를 골라, 후보마다 연도 주제(컨셉)와 연결되는 이유 한 줄과 제작 가능성 확인 항목 한 줄을 적습니다. '
            '근거 없이 "인기 상품"이라고 쓰지 않습니다. 아래 컨셉과 조건에 맞는 후보 %d개를 JSON 배열로만 답하세요. '
            '형식: [{"item":"pinbutton","conn":"컨셉과 연결되는 이유 한 문장(한국어, 60자 이내)","check":"제작 전 확인할 것 한 문장(한국어, 40자 이내)"}]. '
            'item 은 반드시 다음 중에서만: %s\n컨셉: %s\n조건: %s')%(n,names,concept,context)
    try:
        url='https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent'%model
        body={'contents':[{'parts':[{'text':prompt}]}],'generationConfig':{'responseMimeType':'application/json'}}
        with _post(url,body,{'Content-Type':'application/json','x-goog-api-key':key},25) as r:
            arr=json.loads(json.load(r)['candidates'][0]['content']['parts'][0]['text'])
        out=[]
        for a in arr:
            k=a.get('item')
            if k in NEW_KEYS and k not in exclude and k not in [o['item'] for o in out]:
                out.append(_card(k,str(a.get('conn',''))[:120] or NEW_NOTE[k],str(a.get('check',''))[:80] or None))
        return out[:n] if len(out)>=3 else None
    except Exception:return None

def recommend(concept,workspace,exclude=(),history=()):
    concept=str(concept or '').strip()[:300]
    if len(concept)<2:raise GoodsError('컨셉을 먼저 입력해 주세요.')
    c=(workspace.get('conditions') or {});plan=workspace.get('plan') or {}
    ctx=' / '.join('%s: %s'%(k,v) for k,v in (('대상',c.get('target') or plan.get('target')),('예산',c.get('budget_total') or plan.get('budget_total')),('규모',c.get('scale') or plan.get('scale')),('테마',c.get('theme'))) if v)
    shown=[x for x in (exclude or []) if x in NEW_KEYS]
    base=[x for x in (history or []) if x in NEW_KEYS]   # 지난번에 이미 고른 품목은 새 후보에서 뺀다
    reset=len(set(shown)|set(base))>=len(NEW_KEYS)-1
    if reset:shown=[];base=[]
    skip=tuple(set(shown)|set(base))
    ai=recommend_ai(concept,ctx,skip)
    recs=ai or recommend_rules(concept+' '+ctx,str(c.get('budget_total') or ''),skip)
    return {'recommendations':recs,'by':'ai' if ai else 'rules','reset':reset,'excluded_history':base,'rule':'고정 8종·기존 품목 제외, 후보 5종 중 사람이 2종 선택 (D02 2-3)'}

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
 'acrylic_stand':'A dreamy festival backdrop scene, soft focus, empty center, {c}.',
 'pinbutton':'A soft pastel festival backdrop with bokeh lights, empty center, {c}.',
 'postcard':'A soft pastel festival backdrop with bokeh lights, empty center, {c}.',
 'griptok':'A soft pastel backdrop with bokeh lights, empty center, {c}.',
 'pouch':'A plain blank cream canvas zipper pouch, front view, flat lay product photo on a soft background, no print, no logo.',
 'handkerchief':'A plain blank white square cotton handkerchief laid flat, top view product photo on a soft background, no print.',
 'notebook':'A plain blank pastel notebook with an elastic band, front cover, flat lay product photo on a soft background, no print, no logo.',
 'phonecase':'A plain blank white smartphone case, back view, flat lay product photo on a soft background, no print, no logo.',
 'blanket':'A plain blank cream fleece blanket laid flat, top view product photo on a soft background, no print.',
}
NEEDS_BG=('ecobag','tshirt','pouch','handkerchief','notebook','phonecase','blanket')  # 제품 사진이 없으면 만들 수 없는 종류
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

def history_items(store,uid):
    """지금까지 담당자가 선택한 품목(새 후보 추천에서 뺀다)."""
    ensure_table(store)
    with store.db() as db:
        rows=db.execute('SELECT DISTINCT item FROM goods_designs WHERE user_id=? AND selected=1',(uid,)).fetchall()
    return [r['item'] for r in rows]

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
