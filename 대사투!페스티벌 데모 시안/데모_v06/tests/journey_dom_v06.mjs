// Run with HAPPY_DOM_MODULE=/absolute/path/to/happy-dom/lib/index.js node tests/journey_dom_v06.mjs
// Pure DOM component/integration tests; no browser session or real user workspace.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
const {Window}=await import(pathToFileURL(process.env.HAPPY_DOM_MODULE).href);
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const win=new Window({url:'http://localhost:8002/index_v06.html#home'});
win.document.write(fs.readFileSync(path.join(root,'index_v06.html'),'utf8').replace(/<script[\s\S]*?<\/script>/g,''));
win.HTMLDialogElement.prototype.showModal=function(){this.open=true};
win.HTMLDialogElement.prototype.close=function(){this.open=false;this.dispatchEvent(new win.Event('close'))};
win.HTMLMediaElement.prototype.play=async function(){this.playedByTest=true};
win.HTMLMediaElement.prototype.pause=function(){};
let pageTop=120;Object.defineProperty(win,'scrollY',{get:()=>pageTop});win.scrollTo=({top})=>{pageTop=top};win.confirm=()=>true;
const template=JSON.parse(fs.readFileSync(path.join(root,'plan_template_v06.json'),'utf8'));
const emptyFields=Object.fromEntries([...template.sections.flatMap(s=>s.fields),'missing'].map(k=>[k,template.tables[k]?[]:'']));
let workspace={messages:[],conditions:{},plan:null,goods:[]};let calls=[];
const report=()=>({has_plan:!!workspace.plan,missing:['주최·주관'],evidence:[],open_questions:['우천 장소'],checks:Object.fromEntries(['missing','evidence','budget','responsibility'].map(k=>[k,false])),responsible:'',note:'',signature:'test-signature',complete:false});
win.fetch=async function(url,opts={}){const b=opts.body?JSON.parse(opts.body):null;calls.push([url,b]);let data;
 if(url==='/api/status')data={orgs:[],providers:{},setup_required:false};
 else if((url==='/api/me'||url==='/api/entry'))data={user:{id:1,name:'테스트 담당자',org_name:'일반 관리자',role:'manager',verified:1,status:'approved'},csrf:'test'};
 else if(url==='/plan_template_v06.json')data=template;
 else if(url==='/api/conditions'){workspace.conditions=b.conditions;data=workspace}
 else if(url==='/api/plan'){workspace.plan={...emptyFields,festival_name:'테스트 축제',concept:workspace.conditions.concept};data={workspace,steps:[]}}
 else if(url==='/api/chat/edit'){workspace.archives=[{at:1,messages:structuredClone(workspace.messages),plan:workspace.plan}];workspace.messages=[{role:'user',content:b.question},{role:'assistant',content:'수정 후 자동 작성 완료'}];data={workspace,steps:[]}}
 else if(url==='/api/chat'){workspace.messages.push({role:'user',content:b.question},{role:'assistant',content:'조건을 적용해 기획안을 작성했습니다.'});workspace.plan={...emptyFields,festival_name:'자동 기획'};workspace.agent={stages:[{label:'조건 정리',status:'done'},{label:'초안 작성',status:'done'}],next:{page:'review',label:'다음: 최종 검토',description:'미정 항목을 확인하세요.'}};data={workspace,steps:[],next_action:workspace.agent.next}}
 else if(url==='/api/review'){data=report();if(b){data={workspace,report:{...report(),complete:true}}}}
 else if(url==='/api/workspace'){if(b)workspace={...workspace,...b};data=workspace}
 else throw new Error('Unexpected endpoint '+url);
 return {ok:true,status:200,json:async()=>structuredClone(data)};
};
win.eval(fs.readFileSync(path.join(root,'journey_v06.js'),'utf8')+'\n'+fs.readFileSync(path.join(root,'app_v06.js'),'utf8'));
const tick=()=>new Promise(r=>setTimeout(r,20));await tick();
const text=()=>win.document.querySelector('#main').textContent;
const click=(label,scope=win.document)=>{const buttons=[...scope.querySelectorAll('button')];const b=buttons.find(b=>b.textContent===label)||buttons.find(b=>b.textContent.includes(label));assert.ok(b,'missing button '+label);b.click();return b};
assert.equal(win.document.querySelectorAll('.journey-step').length,0);assert.deepEqual([...win.document.querySelectorAll('#navigation button')].slice(0,3).map(b=>b.textContent),['01. 홈','02. 조건 선택','03. AI 기획']);click('03. AI 기획');await tick();assert.ok(text().includes('조건 선택을 먼저'));assert.equal(win.document.querySelector('#chat-input'),null);click('01. 홈',win.document.querySelector('#navigation'));
click('영상 재생하기 ▶');let v=win.document.querySelector('video');assert.ok(v.controls);assert.ok(v.querySelector('source').src.endsWith('.mp4'));click('0:27 결과 확인');assert.equal(v.currentTime,27);assert.ok(v.playedByTest);win.document.querySelector('#guide').close();
click('사용법 먼저 알아보기');click('청년 참여형',win.document.querySelector('#guide'));click('이 질문으로 기획 시작 →');await tick();assert.ok(text().includes('02. 내 기획 조건'));
const filled={year:'2027',host:'기획팀',concept:'참여형 체험',programs:'사투리 퀴즈',scale:'500명',theme:'지역문화',period:'2027년 8월 27~29일',place:'두류공원',budget_total:'산정 요청',target:'가족',goal:'지역문화 체험 확대'};
const start=click('조건 저장하고 AI 기획 시작 →');assert.ok(start.disabled);assert.ok(!calls.some(([u])=>u==='/api/chat'||u==='/api/plan'));
for(const [k,v] of Object.entries(filled)){if(k==='goal')continue;const f=win.document.querySelector('[name='+k+']');f.value=v;f.dispatchEvent(new win.Event('input',{bubbles:true}))}assert.ok(start.disabled);
const goal=win.document.querySelector('[name=goal]');goal.value=filled.goal;goal.dispatchEvent(new win.Event('input',{bubbles:true}));assert.ok(!start.disabled);click('조건 저장하고 AI 기획 시작 →');await tick();assert.ok(text().includes('03. 대키미와 AI 기획'));assert.ok(!calls.some(([u])=>u==='/api/chat'||u==='/api/plan'));let input=win.document.querySelector('#chat-input');assert.ok(input.value.includes('청년'));
input.value='가족 500명 참여 축제를 기획해줘';input.dispatchEvent(new win.Event('input',{bubbles:true}));win.document.querySelector('.chat-form').requestSubmit();await tick();assert.ok(calls.find(([url,b])=>url==='/api/chat'&&b.agent_mode===true));assert.ok(text().includes('대키미가 이어서 수행한 작업'));assert.ok(text().includes('다음: 최종 검토'));
assert.equal(win.document.querySelectorAll('.message.user .message-actions .message-action').length,2);assert.ok(!win.document.querySelector('.message-actions').textContent.includes('돌아가기'));const oldLog=win.document.querySelector('.messages');oldLog.scrollTop=64;pageTop=180;click('메시지 수정');await tick();assert.equal(win.document.querySelector('.messages').scrollTop,64);assert.equal(win.scrollY,180);win.document.querySelector('.message-edit-input').value='700명으로 기획 변경';win.document.querySelector('.message-edit-form').requestSubmit();await tick();assert.ok(calls.find(([url,b])=>url==='/api/chat/edit'&&b.message_index===0));assert.ok(text().includes('수정 전 대화 보기'));
click('04. 기획 결과',win.document.querySelector('#navigation'));await tick();assert.ok(text().includes('04. 기획 결과'));
click('조사 내용',win.document.querySelector('.result-tabs'));await tick();assert.ok(text().includes('대키미와 정리한 조사 내용'));click('최종 검토',win.document.querySelector('#navigation'));await tick();assert.equal(win.document.querySelectorAll('.review-check').length,4);win.document.querySelector('[name=responsible]').value='검토 담당자';for(const i of win.document.querySelectorAll('.review-check input'))i.checked=true;win.document.querySelector('.review-form').requestSubmit();await tick();assert.ok(calls.find(([url,b])=>url==='/api/review'&&b?.responsible==='검토 담당자'&&b.checks.budget));
click('저장·활용',win.document.querySelector('#navigation'));await tick();assert.equal(win.document.querySelectorAll('.export-option').length,3);
click('기획안 직접 편집');await tick();assert.equal(win.document.querySelectorAll('.plan-section').length,9);assert.ok(text().includes('기획안 직접 편집'));
console.log('PASS: numbered navigation; no duplicate buttons; all-conditions gate; conditions before AI; edit keeps scroll; no back button; results/review/export');
await win.happyDOM.abort();
