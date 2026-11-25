import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {PresentationFile,FileBlob} from '@oai/artifact-tool';
const dir=path.dirname(fileURLToPath(import.meta.url));
const source=path.join(dir,'../../portfolio_design_v04/deliverables/대구_얼라들_포트폴리오_디자인반영_v04.pptx');
const p=await PresentationFile.importPptx(await FileBlob.load(source));
const paper=new Uint8Array(await fs.readFile(path.join(dir,'../assets/graph-paper-landscape.png')));
const ink='#172C25',muted='#485A53',mint='#EAF8F1',coral='#F68081';
function backShape(s,name,x,y,w,h,fill='#FFFFFF',line='none',shadow){const sh=s.shapes.add({name,geometry:'rect',position:{left:x,top:y,width:w,height:h},fill,line:{fill:line,width:line==='none'?0:1},...(shadow?{shadow}:{})});sh.sendToBack();return sh;}
function star(s,x,y,size,fill=coral){const sh=s.shapes.add({name:'design-star',geometry:'star4',position:{left:x,top:y,width:size,height:size},fill,line:{fill:'none',width:0}});return sh;}
let preserved=[];
for(let i=0;i<26;i++){
 const n=i+1,s=p.slides.getItem(i);const pictures=[...s.images.items];
 preserved.push({n,texts:s.shapes.items.filter(x=>String(x.text).trim()).map(x=>String(x.text)),pictures:pictures.length});
 // Remove only the previous decorative shapes. Keep all text, images, and milestone data.
 for(const sh of [...s.shapes.items]){
  if(String(sh.text).trim())continue;
  if(n===4&&(/timeline-grid|milestone-editable-bar|legend-current|legend-planned/.test(sh.name)))continue;
  sh.delete();
 }
 for(const sh of s.shapes.items){
  if(!String(sh.text).trim())continue;
  const pos=sh.position,oldStyle=sh.text.style;
  sh.text.color=pos.top<70||pos.top>=1000?muted:ink;
  sh.text.outline={fill:'none',width:0};
  // Typeface and wording are retained so the user can choose fonts later.
 }
 for(const im of pictures){
  im.geometry='rect';im.borderRadius=0;im.lockAspectRatio=true;
  const f=im.frame;
  const margin=6;
  backShape(s,'photo-paper',Math.max(0,f.left-margin),Math.max(0,f.top-margin),Math.min(1920-Math.max(0,f.left-margin),f.width+2*margin),Math.min(1080-Math.max(0,f.top-margin),f.height+2*margin),'#FFFFFF','none');
 }
 const accent=[5,17].includes(n);
 s.background.fill=accent?mint:'#FFFFFF';
 if(n===1){
  backShape(s,'cover-reading-paper',65,515,745,320,'#FFFFFF/96');
  for(const sh of s.shapes.items){if(sh.name==='p1-text-3')sh.position={...sh.position,top:540};if(sh.name==='p1-text-4')sh.position={...sh.position,top:710};}
  star(s,888,190,60);star(s,1780,980,32,'#54CFA0');
 }else if(n===17){
  star(s,900,220,66);star(s,1780,980,30,'#54CFA0');
 }else if(n===5){
  for(const sh of s.shapes.items){if(sh.name==='p5-text-2'){sh.text.fontSize=36;sh.position={...sh.position,height:190};}}
  star(s,1080,195,46);star(s,1715,245,28,'#54CFA0');
 }else if(n===26){
  backShape(s,'closing-reading-paper',60,250,760,410,'#FFFFFF/96');star(s,950,185,40);star(s,1750,985,30,'#54CFA0');
 }else if(n===4){
  backShape(s,'milestone-reading-paper',55,280,1815,680,'#FFFFFF/96');
 }else if(n===2||n===21){
  backShape(s,'contents-left-paper',55,260,865,685,'#FFFFFF/96');backShape(s,'contents-right-paper',965,260,900,685,'#FFFFFF/96');
 }else if(n===10){
  // The image-only lineup stays image-only, with one uniform photographic grid.
 }else{
  const width=n===9?1035:990;
  backShape(s,'body-reading-paper',60,260,width,700,'#FFFFFF/96');
 }
 // This one 16:9 texture is embedded, never stretched from the portrait reference.
 if(!accent){backShape(s,'paper-quiet-overlay',0,0,1920,1080,'#FFFFFF/38');const bg=s.images.add({blob:paper,contentType:'image/png',alt:'모눈 종이 배경',position:{left:0,top:0,width:1920,height:1080},fit:'cover'});bg.sendToBack();}
 console.log('styled',n);
}
await fs.writeFile(path.join(dir,'preservation_manifest.json'),JSON.stringify(preserved,null,2));
await fs.mkdir(path.join(dir,'renders'),{recursive:true});
await(await PresentationFile.exportPptx(p)).save(path.join(dir,'candidate.pptx'));console.log('exported');
for(const[i,s]of p.slides.items.entries()){
 const png=await p.export({slide:s,format:'png',scale:.67});await fs.writeFile(path.join(dir,'renders',`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await png.arrayBuffer()));console.log('rendered',i+1);
}
