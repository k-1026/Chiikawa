'use strict';
// 06-2. 굿즈 시안: 컨셉으로 시안 이미지를 만들고, 마음에 드는 시안에 맞춘 제작 계획서(md)를 받는다.
const GOODS={items:{},designs:[],enabled:false,loaded:false,busy:false,concept:'',item:'keyring'};
async function goodsLoad(){try{const d=await api('/api/goods/list');GOODS.items=d.items;GOODS.designs=d.designs;GOODS.enabled=d.enabled;GOODS.loaded=true}catch(e){feedback(e.message,true)}if(S.page==='goodsdesign')render()}
async function goodsMake(){if(GOODS.busy)return;const concept=(GOODS.concept||S.w.plan?.concept||S.w.conditions?.concept||'').trim();if(concept.length<2){feedback('컨셉을 입력해 주세요.',true);return}GOODS.busy=true;render();try{await api('/api/goods/design',{item:GOODS.item,concept,count:2});feedback('시안을 만들었습니다.');await goodsLoad()}catch(e){feedback(e.message,true)}finally{GOODS.busy=false;render()}}
async function goodsPlan(d){const q=prompt('제작할 수량을 입력해 주세요 (숫자)','500');if(q===null)return;try{const r=await api('/api/goods/plan',{id:d.id,quantity:q});const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([r.markdown],{type:'text/markdown;charset=utf-8'}));a.download=r.filename;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),2000);feedback('제작 계획서를 내려받았습니다.')}catch(e){feedback(e.message,true)}}
function goodsDesign(){
  if(!GOODS.loaded)goodsLoad();
  const concept=GOODS.concept||S.w.plan?.concept||S.w.conditions?.concept||'';
  const top=heading('굿즈 시안','축제 컨셉에 맞춘 굿즈 시안 이미지를 만들고, 마음에 드는 시안의 제작 계획서를 받아요.');
  const form=el('form',{class:'card'},
    el('div',{class:'field'},el('label',{for:'g-item'},'굿즈 종류'),el('select',{id:'g-item',onchange:e=>GOODS.item=e.target.value},...Object.entries(GOODS.items).map(([k,v])=>el('option',{value:k,selected:k===GOODS.item},v)))),
    el('div',{class:'field'},el('label',{for:'g-concept'},'컨셉'),el('textarea',{id:'g-concept',maxlength:300,rows:3,placeholder:'예) 우주 정거장에서 만나는 대구 사투리 파티',value:concept,oninput:e=>GOODS.concept=e.target.value})),
    el('button',{type:'submit',class:'button',disabled:GOODS.busy||!GOODS.enabled},GOODS.busy?'시안을 만드는 중… (약 20초)':'시안 2장 만들기'),
    GOODS.enabled?null:p('시안 이미지 서비스가 아직 연결되지 않았습니다. 운영자의 서비스 설정 후 이용할 수 있습니다.','hint'),
    p('AI가 만든 시안은 참고용입니다. 인쇄 전에는 디자이너의 정리와 마스코트 사용 확인이 필요해요.','hint'));
  form.addEventListener('submit',e=>{e.preventDefault();goodsMake()});
  const grid=el('div',{class:'goods-grid'});
  if(!GOODS.designs.length)grid.append(p(GOODS.loaded?'아직 만든 시안이 없습니다.':'불러오는 중…','hint'));
  for(const d of GOODS.designs)grid.append(el('figure',{class:'card goods-card'},el('img',{src:'/api/goods/image?id='+d.id,alt:d.item_name+' 시안 · '+d.concept,loading:'lazy'}),el('figcaption',{},el('strong',{},d.item_name),el('small',{},d.concept)),button('제작 계획서(md) 받기',()=>goodsPlan(d),'button secondary small')));
  return el('div',{},top,el('div',{class:'stack'},form,grid));
}
