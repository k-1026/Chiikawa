import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {PresentationFile,FileBlob} from '@oai/artifact-tool';
const dir=path.dirname(fileURLToPath(import.meta.url));
const layout=JSON.parse(await fs.readFile(path.join(dir,'layout_v03.json'),'utf8'));
const p=await PresentationFile.importPptx(await FileBlob.load(path.join(dir,'source_v03.pptx')));
p.theme.defaultFont='Apple SD Gothic Neo';
const C={ink:'#25463F',mint:'#55C5A6',mintLight:'#E8F6EF',mintMid:'#BDE8D7',coral:'#FF9691',coralLight:'#FBE5DF',sky:'#94D2EE',skyLight:'#EAF6FC',green:'#B1D77F',greenLight:'#F0F7E8',paper:'#FFFFFF'};
function decor(s,name,pos,fill,geometry='ellipse',radius){const v=s.shapes.add({name,geometry,position:pos,fill,line:{fill:'none',width:0},...(radius?{borderRadius:radius}:{})});v.sendToBack();return v;}
function rect(s,name,x,y,w,h,fill,r=40){return decor(s,name,{left:x,top:y,width:w,height:h},fill,'roundRect',r);}
function circle(s,name,x,y,size,fill){return decor(s,name,{left:x,top:y,width:size,height:size},fill);}
function text(s,txt,x,y,w,h,size=28,bold=false,color=C.ink){const sh=s.shapes.add({name:'milestone-text',geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});sh.text=txt;sh.text.style={fontSize:size,typeface:'Apple SD Gothic Neo',bold,color,insets:0,autoFit:'none',wrap:'none'};return sh;}
function milestone(s){
 for(const sh of [...s.shapes.items])sh.delete();s.background.fill='#FAFDFB';
 const spec=layout[3];
 for(const t of spec.items.filter(x=>x.type==='text'&&x.y<240))text(s,t.text,t.x,t.y,t.w,t.h,t.size,t.bold,C.ink);
 const left=445,right=1840,top=330,rh=78,bottom=top+rh*7,cw=(right-left)/11;
 for(let i=0;i<=11;i++)rect(s,'timeline-grid-v',left+i*cw,top,1,bottom-top,'#E0EAE5',0);
 for(let i=0;i<=7;i++)rect(s,'timeline-grid-h',left,top+i*rh,right-left,1,'#E0EAE5',0);
 const rows=[['제작 조건·견적 협의',0,4,true],['샘플 개발',1,5,false],['샘플 비교·수정',4,7,false],['상품 구성·가격 검토',5,8,false],['텀블벅 준비',4,11,false],['촬영·상세페이지 제작',6,10,false],['심사·보완·공개 준비',8,11,false]];
 for(const [i,[label,start,end,active]]of rows.entries()){
  text(s,label,80,top+i*rh+21,350,45,28,true);
  s.shapes.add({name:'milestone-editable-bar',geometry:'roundRect',position:{left:left+start*cw+5,top:top+i*rh+17,width:(end-start)*cw-10,height:44},fill:active?C.mint:(i===4?C.coral:'#FFC9C4'),line:{fill:'none',width:0},borderRadius:22});
 }
 for(const t of spec.items.filter(x=>x.type==='text'&&x.y>=917))text(s,t.text,t.x,t.y,t.w,t.h,t.size,t.bold,t.y>=1000?'#60746B':C.ink);
 circle(s,'legend-current',1190,260,24,C.mint);text(s,'진행 중',1225,254,160,45,25);
 circle(s,'legend-planned',1435,260,24,'#FFC9C4');text(s,'예정',1470,254,160,45,25);
 rect(s,'header-soft-mint',0,0,1920,240,C.mintLight,0);
 s.speakerNotes.text=String(s.speakerNotes.text)+'\n추가: 텀블벅 준비 D-6주~오픈. 리워드·가격·프로젝트 정보·상세페이지·심사 자료를 준비하는 제안 기간.';
}
for(let si=0;si<p.slides.items.length;si++){
 const n=si+1,s=p.slides.getItem(si),spec=layout[si];if(n===4){milestone(s);continue;}
 s.background.fill=C.paper;
 const mapping=new Map(spec.items.map((v,i)=>[`p${n}-text-${i}`,v]));
 for(const sh of s.shapes.items){
  const old=mapping.get(sh.name);if(!old||old.type!=='text')continue;
  let color=C.ink,size=old.size;if(old.y<70)color='#47816C';if(old.y>=1000)color='#60746B';if(old.bold&&old.size===30)color='#337E68';
  if(n>=11&&n<=16&&old.size===46){size=54;sh.position={...sh.position,height:90};}
  if(n===1&&old.size===78){size=126;sh.position={left:90,top:140,width:1000,height:205};}
  if(n===1&&old.size===38)sh.position={left:90,top:385,width:810,height:90};
  if(n===1&&old.y===435)sh.position={left:90,top:565,width:750,height:110};
  if(n===1&&old.y===559)sh.position={left:90,top:805,width:750,height:110};
  if(n===17&&old.size===78){size=130;sh.position={left:90,top:140,width:1000,height:200};}
  if(n===17&&old.size===38)sh.position={left:90,top:390,width:810,height:135};
  if(n===17)color=old.y<70?'#A4DCC7':(old.size>=70?C.coral:'#FFFFFF');
  sh.text.style={fontSize:size,typeface:'Apple SD Gothic Neo',bold:old.bold,color,insets:0,autoFit:'none',wrap:'none',verticalAlignment:'top'};
 }
 for(const im of s.images.items){im.geometry='roundRect';im.borderRadius=26;im.lockAspectRatio=true;}
 if(n===1){
  s.background.fill='#D9F2E7';circle(s,'cover-orbit-large',1060,310,740,'#B4E6D3');circle(s,'cover-coral-dot',935,150,125,C.coral);circle(s,'cover-sky-dot',1650,965,65,C.sky);rect(s,'cover-photo-ground',820,350,1070,620,'#EFFAF4',64);
 }else if(n===17){
  s.background.fill=C.ink;rect(s,'future-photo-ground',820,340,1070,625,'#7CD2B8',64);circle(s,'future-coral-dot',900,140,110,C.coral);circle(s,'future-sky-dot',1660,970,60,C.sky);
 }else if(n===26){
  s.background.fill=C.coralLight;rect(s,'closing-photo-ground',820,350,1070,620,'#D2EEDF',64);circle(s,'closing-mint-dot',1000,130,90,C.mint);
 }else if(n===10){
  s.background.fill='#FBFEFC';rect(s,'lineup-keyring',65,40,570,990,'#E3F2FA',48);rect(s,'lineup-seated',675,40,570,990,'#E1F0E6',48);rect(s,'lineup-lamp',1285,40,570,990,'#FBE6DE',48);
 }else if(n===5){
  s.background.fill=C.mintLight;circle(s,'brand-coral-orbit',1290,315,570,C.coralLight);rect(s,'brand-photos',1050,350,820,625,'#C6EAD9',56);
 }else if(n>=11&&n<=16){
  const blue=[11,13].includes(n),green=[12,14].includes(n);s.background.fill=blue?'#F3FAFD':green?'#F5FAEF':'#FFF8F4';rect(s,'product-visual-ground',1060,270,815,695,blue?'#DCEFF8':green?'#E2EFCF':'#F7DED3',48);circle(s,'product-point-orbit',1720,120,110,blue?C.sky:green?C.green:C.coral);
 }else if(n===2||n===21){
  s.background.fill='#FAFDFB';rect(s,'left-text-field',55,255,865,685,'#EAF6EF',8);rect(s,'right-text-field',965,255,900,685,'#FFF0E9',8);
 }else if(n===9){
  rect(s,'logo-backdrop',1110,265,760,680,'#DDF1E7',52);circle(s,'logo-coral-dot',1700,140,100,C.coral);
 }else if(n===8){
  s.background.fill='#FCFEFC';rect(s,'development-collage',1070,260,800,695,'#E0F3E9',48);circle(s,'development-sky-dot',980,145,82,C.sky);
 }else if(n===3||n===18){
  rect(s,'friends-photo-field',1070,300,800,640,'#E8F6ED',48);circle(s,'friends-coral-orbit',1660,175,120,C.coralLight);
 }else if(n===6||n===7||n===25){
  rect(s,'expression-sheet-field',1070,255,800,705,'#EBF6F1',8);circle(s,'expression-sheet-coral-dot',1715,125,90,C.coral);
 }else{
  rect(s,'evidence-field',1070,255,800,705,n===19?'#EDF6E7':'#ECF6F1',8);circle(s,'evidence-point',1750,135,70,n%2?C.sky:C.coral);
 }
}
await fs.mkdir(path.join(dir,'renders'),{recursive:true});await(await PresentationFile.exportPptx(p)).save(path.join(dir,'candidate.pptx'));console.log('exported v04');
for(const[i,s]of p.slides.items.entries()){const png=await p.export({slide:s,format:'png',scale:.67});await fs.writeFile(path.join(dir,'renders',`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await png.arrayBuffer()));console.log('rendered',i+1);}
