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
click('04. 기획 결과',win.document.querySelector('#navigation'));await tick();
click('빈 양식으로 직접 작성');await tick();
assert.equal(win.document.querySelectorAll('.plan-section').length,9);
assert.ok(!calls.some(([u])=>['/api/chat','/api/plan'].includes(u)));
win.document.querySelector('[name=festival_name]').value='API 없이 작성한 축제';
win.document.querySelector('.plan-form').requestSubmit();await tick();
assert.ok(calls.some(([u,b])=>u==='/api/workspace'&&b?.plan?.festival_name==='API 없이 작성한 축제'));
console.log('PASS: mandatory conditions, blank fixed template, manual save without AI API');
await win.happyDOM.abort();
