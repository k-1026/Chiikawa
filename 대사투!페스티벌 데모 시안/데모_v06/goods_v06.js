'use strict';
// 06-2. 굿즈 시안: 컨셉으로 시안 이미지를 만들고, 마음에 드는 시안에 맞춘 제작 계획서(md)를 받는다.
const GOODS={items:{},groups:{},designs:[],enabled:false,loaded:false,busy:false,concept:'',item:'keyring',recs:null,recBusy:false,poseMode:'auto',shown:[],who:'both'};
async function goodsLoad(){try{const d=await api('/api/goods/list');GOODS.items=d.items;GOODS.groups=d.groups||{};GOODS.designs=d.designs;GOODS.enabled=d.enabled;GOODS.loaded=true}catch(e){feedback(e.message,true)}if(S.page==='goodsdesign')render()}
async function goodsMake(){if(GOODS.busy)return;const concept=(GOODS.concept||S.w.plan?.concept||S.w.conditions?.concept||'').trim();if(concept.length<2){feedback('컨셉을 입력해 주세요.',true);return}GOODS.busy=true;render();try{const made=await api('/api/goods/design',{item:GOODS.item,concept,count:2,who:GOODS.who,pose_mode:GOODS.poseMode},120000);feedback((made.designs||[]).some(x=>x.bg_failed)?'시안을 만들었습니다. 배경 이미지는 이용 한도 때문에 만들지 못해 기본 배경을 썼어요(내일 오전 9시 이후 다시 만들면 달라집니다).':'시안을 만들었습니다.');await goodsLoad()}catch(e){feedback(e.message,true)}finally{GOODS.busy=false;render()}}
async function goodsSelect(d){try{const r=await api('/api/goods/select',{id:d.id,selected:!d.selected},20000);d.selected=r.selected;feedback(r.selected?'이 시안을 선택했습니다. 기획안의 굿즈 파트에 들어갑니다.':'선택을 해제했습니다.')}catch(e){feedback(e.message,true)}render()}
async function goodsRecommend(more=false){const concept=(GOODS.concept||S.w.plan?.concept||S.w.conditions?.concept||'').trim();if(concept.length<2){feedback('컨셉을 먼저 입력해 주세요.',true);return}GOODS.recBusy=true;render();try{const d=await api('/api/goods/recommend',{concept,exclude:more?GOODS.shown:[]},40000);GOODS.shown=d.reset||!more?d.recommendations.map(r=>r.item):[...GOODS.shown,...d.recommendations.map(r=>r.item)];if(d.reset)feedback('모든 종류를 한 번씩 보여드렸어요. 처음부터 다시 추천합니다.');GOODS.recs=d;if(d.recommendations[0])GOODS.item=d.recommendations[0].item}catch(e){feedback(e.message,true)}finally{GOODS.recBusy=false;render()}}
function goodsDownload(r){const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([r.markdown],{type:'text/markdown;charset=utf-8'}));a.download=r.filename;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),2000)}
async function goodsFile(d,qty,fmt){const r=await fetch('/api/goods/export?fmt='+fmt,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-CSRF-Token':S.csrf},body:JSON.stringify({id:d.id,quantity:qty})});if(!r.ok){let m='문서를 만들지 못했습니다.';try{m=(await r.json()).error||m}catch{}throw new Error(m)}return r.blob()}
function goodsSave(blob,name){const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(a.href),3000)}
async function goodsPlan(d){const dialog=$('#guide');let pdfUrl='';const qty=el('input',{type:'number',min:1,max:100000,value:500,id:'g-qty'});
  const frame=el('iframe',{class:'goods-pdf',title:'제작 계획서 PDF 미리보기'});const status=p('PDF 미리보기를 만들고 있어요…','hint');
  const preview=async()=>{status.textContent='PDF 미리보기를 만들고 있어요…';status.className='hint';try{const blob=await goodsFile(d,qty.value,'pdf');if(pdfUrl)URL.revokeObjectURL(pdfUrl);pdfUrl=URL.createObjectURL(blob);frame.src=pdfUrl+'#view=FitH';status.textContent='아래 버튼으로 파일을 내려받을 수 있어요.'}catch(e){status.textContent=e.message;status.className='form-error'}};
  const dl=(fmt,label,ext)=>button(label,async()=>{try{goodsSave(await goodsFile(d,qty.value,fmt),'제작계획서_'+d.item_name+'.'+ext);feedback(label+' 파일을 내려받았습니다.')}catch(e){feedback(e.message,true)}},'button');
  const md=button('md 파일',async()=>{try{const r=await api('/api/goods/plan',{id:d.id,quantity:qty.value},40000);goodsDownload(r)}catch(e){feedback(e.message,true)}},'button secondary');
  dialog.classList.add('goods-dialog');dialog.addEventListener('close',()=>{if(pdfUrl)URL.revokeObjectURL(pdfUrl);dialog.classList.remove('goods-dialog')},{once:true});
  dialog.replaceChildren(el('div',{class:'guide-head'},el('h2',{id:'guide-title'},d.item_name+' 제작 계획서'),button('닫기',()=>dialog.close(),'button secondary')),
    el('div',{class:'field'},el('label',{for:'g-qty'},'제작 수량'),qty,button('이 수량으로 다시 만들기',preview,'button secondary small')),
    status,frame,
    el('div',{class:'goods-downloads'},el('strong',{},'파일로 내려받기'),el('div',{class:'row'},dl('pdf','PDF','pdf'),dl('docx','Word','docx'),dl('hwpx','한글(.hwpx)','hwpx'),md),p('한글 파일은 .hwpx 형식입니다(그림은 PDF·Word에만 들어갑니다). 한글에서 열었을 때 서식이 어긋나면 PDF를 기준으로 확인해 주세요.','hint')));
  dialog.showModal();preview()}
function goodsDesign(){
  if(!GOODS.loaded)goodsLoad();
  const concept=GOODS.concept||S.w.plan?.concept||S.w.conditions?.concept||'';
  const top=heading('굿즈 시안','축제 컨셉에 맞춘 굿즈 시안 이미지를 만들고, 마음에 드는 시안의 제작 계획서를 받아요.');
  const form=el('form',{class:'card'},
    el('div',{class:'field'},el('label',{for:'g-item'},'굿즈 종류'),el('select',{id:'g-item',onchange:e=>GOODS.item=e.target.value},...[['신규 후보 (추천 대상)',(GOODS.groups||{}).new||[]],['기본 품목',(GOODS.groups||{}).basic||Object.keys(GOODS.items)]].map(([label,keys])=>el('optgroup',{label},...keys.filter(k=>GOODS.items[k]).map(k=>el('option',{value:k,selected:k===GOODS.item},GOODS.items[k])))))),
    el('div',{class:'field'},el('label',{for:'g-who'},'캐릭터'),el('select',{id:'g-who',onchange:e=>GOODS.who=e.target.value},...[['both','대키미 + 외지몽'],['daekimi','대키미'],['oejimong','외지몽']].map(([k,v])=>el('option',{value:k,selected:k===GOODS.who},v)))),
    el('div',{class:'field'},el('label',{for:'g-pose'},'포즈·표정'),el('select',{id:'g-pose',onchange:e=>GOODS.poseMode=e.target.value},...[['auto','올해 추천 포즈 (공식 표정·자세에서 매년 다르게)'],['default','기본 포즈 (공식 대표 이미지)']].map(([k,v])=>el('option',{value:k,selected:k===GOODS.poseMode},v))),p('생김새와 색은 공식 원본 그대로이고, 포즈·표정만 공식 표정·자세 시트의 승인된 그림에서 골라 올해 다르게 씁니다. 이미 쓴 포즈는 피합니다.','hint')),
    el('div',{class:'field'},el('label',{for:'g-concept'},'컨셉'),el('textarea',{id:'g-concept',maxlength:300,rows:3,placeholder:'예) 우주 정거장에서 만나는 대구 사투리 파티',value:concept,oninput:e=>GOODS.concept=e.target.value})),
    el('div',{class:'field'},el('div',{class:'row'},button(GOODS.recBusy?'추천을 고르는 중…':'굿즈 종류 추천받기',()=>goodsRecommend(false),'button secondary',{disabled:GOODS.recBusy}),GOODS.recs?button('🔄',()=>goodsRecommend(true),'button secondary goods-refresh',{disabled:GOODS.recBusy,title:'다른 굿즈로 다시 추천','aria-label':'다른 굿즈로 다시 추천'}):null),GOODS.recs?el('div',{class:'goods-recs'},...GOODS.recs.recommendations.map((r,i)=>el('button',{type:'button',class:'goods-rec'+(r.item===GOODS.item?' on':''),onclick:()=>{GOODS.item=r.item;render()}},el('strong',{},(i+1)+'. '+r.name+' · '+(r.yoy||'신규')),el('small',{},'컨셉 연결: '+(r.conn||r.reason)),el('small',{},'제작 전 확인: '+(r.check||'업체 확인 필요'))))):null,GOODS.recs?p((GOODS.recs.by==='ai'?'AI가 컨셉과 조건을 보고 고른 후보예요. ':'컨셉 키워드로 고른 후보예요(AI 연결 시 더 정교해져요). ')+'팀 규칙: 고정 8종과 다른 새 품목 후보 5종 중 사람이 2종을 골라요. 눌러서 선택하세요.','hint'):null),
    el('button',{type:'submit',class:'button',disabled:GOODS.busy||!GOODS.enabled},GOODS.busy?'시안을 만드는 중… (약 30초)':'시안 2장 만들기'),
    GOODS.enabled?null:p('시안 이미지 서비스가 아직 연결되지 않았습니다. 운영자의 서비스 설정 후 이용할 수 있습니다.','hint'),
    p('시안은 공식 캐릭터 원본 이미지를 그대로 사용하고, 배경·제품 사진만 AI가 만듭니다. 인쇄용 고해상도 파일은 디자이너가 원본으로 다시 정리해야 해요.','hint'));
  form.addEventListener('submit',e=>{e.preventDefault();goodsMake()});
  const grid=el('div',{class:'goods-grid'});
  if(!GOODS.designs.length)grid.append(p(GOODS.loaded?'아직 만든 시안이 없습니다.':'불러오는 중…','hint'));
  for(const d of GOODS.designs)grid.append(el('figure',{class:'card goods-card'+(d.selected?' selected':'')},el('img',{src:'/api/goods/image?id='+d.id,alt:d.item_name+' 시안 · '+d.concept,loading:'lazy'}),el('figcaption',{},el('strong',{},d.item_name),el('small',{},d.concept),el('small',{},'포즈: '+((d.pose_names&&d.pose_names.length)?d.pose_names.join(' + '):'기본 포즈'))),el('div',{class:'row'},button(d.selected?'✓ 선택됨 (해제)':'이 시안 선택',()=>goodsSelect(d),d.selected?'button small':'button secondary small'),button('제작 계획서 보기',()=>goodsPlan(d),'button secondary small'))));
  return el('div',{},top,el('div',{class:'stack'},form,grid));
}

// 축제 기획안: 요약본(A4 1~2쪽)과 본문을 따로 PDF로 미리 보고, PDF·Word·한글로 내려받는다.
async function planDoc(part){
  const dialog=$('#guide');let pdfUrl='';const label=part==='summary'?'요약본 (A4 1~2쪽)':'본문';
  const fields=S.planDraft||S.w.plan;if(!fields){feedback('먼저 기획안을 작성해 주세요.',true);return}
  const get=async fmt=>{const r=await fetch('/api/export?fmt='+fmt,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-CSRF-Token':S.csrf},body:JSON.stringify({fields,part})});if(!r.ok){let m='문서를 만들지 못했습니다.';try{m=(await r.json()).error||m}catch{}throw new Error(m)}return r.blob()};
  const frame=el('iframe',{class:'goods-pdf',title:'기획안 PDF 미리보기'});const status=p('PDF 미리보기를 만들고 있어요…','hint');
  const preview=async()=>{try{const blob=await get('pdf');if(pdfUrl)URL.revokeObjectURL(pdfUrl);pdfUrl=URL.createObjectURL(blob);frame.src=pdfUrl+'#view=FitH';status.textContent=S.planDraft?'저장하지 않은 편집 내용을 기준으로 보여줍니다. 아래 버튼으로 내려받을 수 있어요.':'아래 버튼으로 파일을 내려받을 수 있어요.';status.className='hint'}catch(e){status.textContent=e.message;status.className='form-error'}};
  const dl=(fmt,text,ext)=>button(text,async()=>{try{goodsSave(await get(fmt),'대사투_기획안_'+(part==='summary'?'요약본':'본문')+'.'+ext);feedback(text+' 파일을 내려받았습니다.')}catch(e){feedback(e.message,true)}},'button');
  dialog.classList.add('goods-dialog');dialog.addEventListener('close',()=>{if(pdfUrl)URL.revokeObjectURL(pdfUrl);dialog.classList.remove('goods-dialog')},{once:true});
  dialog.replaceChildren(el('div',{class:'guide-head'},el('h2',{id:'guide-title'},'축제 기획안 · '+label),button('닫기',()=>dialog.close(),'button secondary')),
    el('div',{class:'row'},button(part==='summary'?'본문 보기':'요약본 보기',()=>{dialog.close();planDoc(part==='summary'?'full':'summary')},'button secondary small')),
    status,frame,
    el('div',{class:'goods-downloads'},el('strong',{},'파일로 내려받기'),el('div',{class:'row'},dl('pdf','PDF','pdf'),dl('docx','Word','docx'),dl('hwpx','한글(.hwpx)','hwpx')),p('한글 파일은 .hwpx 형식입니다. 한글에서 열었을 때 서식이 어긋나면 PDF를 기준으로 확인해 주세요.','hint')));
  dialog.showModal();preview()}
