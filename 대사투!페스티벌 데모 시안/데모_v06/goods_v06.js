'use strict';
// 06-2. 굿즈 시안: 컨셉으로 시안 이미지를 만들고, 마음에 드는 시안에 맞춘 제작 계획서(md)를 받는다.
const GOODS={items:{},designs:[],enabled:false,loaded:false,busy:false,concept:'',item:'keyring',recs:null,recBusy:false,shown:[],who:'both'};
async function goodsLoad(){try{const d=await api('/api/goods/list');GOODS.items=d.items;GOODS.designs=d.designs;GOODS.enabled=d.enabled;GOODS.loaded=true}catch(e){feedback(e.message,true)}if(S.page==='goodsdesign')render()}
async function goodsMake(){if(GOODS.busy)return;const concept=(GOODS.concept||S.w.plan?.concept||S.w.conditions?.concept||'').trim();if(concept.length<2){feedback('컨셉을 입력해 주세요.',true);return}GOODS.busy=true;render();try{await api('/api/goods/design',{item:GOODS.item,concept,count:2,who:GOODS.who},120000);feedback('시안을 만들었습니다.');await goodsLoad()}catch(e){feedback(e.message,true)}finally{GOODS.busy=false;render()}}
async function goodsRecommend(more=false){const concept=(GOODS.concept||S.w.plan?.concept||S.w.conditions?.concept||'').trim();if(concept.length<2){feedback('컨셉을 먼저 입력해 주세요.',true);return}GOODS.recBusy=true;render();try{const d=await api('/api/goods/recommend',{concept,exclude:more?GOODS.shown:[]},40000);GOODS.shown=d.reset||!more?d.recommendations.map(r=>r.item):[...GOODS.shown,...d.recommendations.map(r=>r.item)];if(d.reset)feedback('모든 종류를 한 번씩 보여드렸어요. 처음부터 다시 추천합니다.');GOODS.recs=d;if(d.recommendations[0])GOODS.item=d.recommendations[0].item}catch(e){feedback(e.message,true)}finally{GOODS.recBusy=false;render()}}
function goodsDownload(r){const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([r.markdown],{type:'text/markdown;charset=utf-8'}));a.download=r.filename;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),2000)}
async function goodsPlan(d){const dialog=$('#guide');const qty=el('input',{type:'number',min:1,max:100000,value:500,id:'g-qty'});const out=el('div',{});const load=async()=>{out.replaceChildren(p('계획서를 만들고 있어요…'));try{const r=await api('/api/goods/plan',{id:d.id,quantity:qty.value},40000);out.replaceChildren(el('pre',{class:'goods-plan'},r.markdown),button('md 파일로 내려받기',()=>goodsDownload(r),'button'))}catch(e){out.replaceChildren(el('div',{class:'form-error'},e.message))}};dialog.replaceChildren(el('div',{class:'guide-head'},el('h2',{id:'guide-title'},d.item_name+' 제작 계획서'),button('닫기',()=>dialog.close(),'button secondary')),el('div',{class:'field'},el('label',{for:'g-qty'},'제작 수량'),qty,button('이 수량으로 만들기',load,'button secondary small')),out);dialog.showModal();load()}
function goodsDesign(){
  if(!GOODS.loaded)goodsLoad();
  const concept=GOODS.concept||S.w.plan?.concept||S.w.conditions?.concept||'';
  const top=heading('굿즈 시안','축제 컨셉에 맞춘 굿즈 시안 이미지를 만들고, 마음에 드는 시안의 제작 계획서를 받아요.');
  const form=el('form',{class:'card'},
    el('div',{class:'field'},el('label',{for:'g-item'},'굿즈 종류'),el('select',{id:'g-item',onchange:e=>GOODS.item=e.target.value},...Object.entries(GOODS.items).map(([k,v])=>el('option',{value:k,selected:k===GOODS.item},v)))),
    el('div',{class:'field'},el('label',{for:'g-who'},'캐릭터'),el('select',{id:'g-who',onchange:e=>GOODS.who=e.target.value},...[['both','대키미 + 외지몽'],['daekimi','대키미'],['oejimong','외지몽']].map(([k,v])=>el('option',{value:k,selected:k===GOODS.who},v)))),
    el('div',{class:'field'},el('label',{for:'g-concept'},'컨셉'),el('textarea',{id:'g-concept',maxlength:300,rows:3,placeholder:'예) 우주 정거장에서 만나는 대구 사투리 파티',value:concept,oninput:e=>GOODS.concept=e.target.value})),
    el('div',{class:'field'},el('div',{class:'row'},button(GOODS.recBusy?'추천을 고르는 중…':'굿즈 종류 추천받기',()=>goodsRecommend(false),'button secondary',{disabled:GOODS.recBusy}),GOODS.recs?button('🔄',()=>goodsRecommend(true),'button secondary goods-refresh',{disabled:GOODS.recBusy,title:'다른 굿즈로 다시 추천','aria-label':'다른 굿즈로 다시 추천'}):null),GOODS.recs?el('div',{class:'goods-recs'},...GOODS.recs.recommendations.map((r,i)=>el('button',{type:'button',class:'goods-rec'+(r.item===GOODS.item?' on':''),onclick:()=>{GOODS.item=r.item;render()}},el('strong',{},(i+1)+'. '+r.name),el('small',{},r.reason)))):null,GOODS.recs?p(GOODS.recs.by==='ai'?'AI가 컨셉과 조건을 보고 고른 추천이에요. 눌러서 선택하세요.':'컨셉 키워드로 고른 추천이에요(AI 연결 시 더 정교해져요). 눌러서 선택하세요.','hint'):null),
    el('button',{type:'submit',class:'button',disabled:GOODS.busy||!GOODS.enabled},GOODS.busy?'시안을 만드는 중… (약 30초)':'시안 2장 만들기'),
    GOODS.enabled?null:p('시안 이미지 서비스가 아직 연결되지 않았습니다. 운영자의 서비스 설정 후 이용할 수 있습니다.','hint'),
    p('시안은 공식 캐릭터 원본 이미지를 그대로 사용하고, 배경·제품 사진만 AI가 만듭니다. 인쇄용 고해상도 파일은 디자이너가 원본으로 다시 정리해야 해요.','hint'));
  form.addEventListener('submit',e=>{e.preventDefault();goodsMake()});
  const grid=el('div',{class:'goods-grid'});
  if(!GOODS.designs.length)grid.append(p(GOODS.loaded?'아직 만든 시안이 없습니다.':'불러오는 중…','hint'));
  for(const d of GOODS.designs)grid.append(el('figure',{class:'card goods-card'},el('img',{src:'/api/goods/image?id='+d.id,alt:d.item_name+' 시안 · '+d.concept,loading:'lazy'}),el('figcaption',{},el('strong',{},d.item_name),el('small',{},d.concept)),button('제작 계획서 보기',()=>goodsPlan(d),'button small')));
  return el('div',{},top,el('div',{class:'stack'},form,grid));
}
