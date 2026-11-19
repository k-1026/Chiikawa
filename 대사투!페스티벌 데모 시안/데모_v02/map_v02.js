/* =====================================================================
   축제 지도 (두류공원 축제 안내도 위에 구역 버튼을 올린 인터랙티브 지도)
   - 정보 출처: main Y.지도(Y_축제전체_지도·Y_메인구역_지도), P0-3_장소 v14,
     B파트 B-1·B-4, C파트 C-1, D파트 D-05, 대사투/2027 기획안
   - 안내도는 계속 업그레이드 중이라 바뀔 수 있어요.
   ===================================================================== */

const MAP_W=1448,MAP_H=1086;
const ZONES=[
 {id:'z0',no:'0',name:'메인 출입로',grp:0,color:'#E5282B',
  shapes:[{t:'c',cx:1275,cy:183,r:36}],pill:[1290,132,'공식 출입로 1곳'],
  kw:['출입로','입구','정문','출입구','메인출입로','어디로들어','들어오는길'],
  what:'축제의 공식 출입로예요. 정상 출입은 이 한 곳뿐이에요.',
  items:['두류공원로와 공원순환로가 만나는 곳, 두류도서관 아래예요','공원순환로는 원래 차도지만 축제 기간에는 차량을 통제하고 축제거리로 써요','방문객 동선의 시작이에요: 출입로 → 운영·안전 부스 → 플리마켓 → 7구 맛집거리 → 메인구역','가까운 기존 화장실: 두류도서관(상시), 도서관 건물 안(07~22시, 첫째·셋째 월요일 휴관)'],
  need:['공원순환로 차량 통제는 경찰서·구청 등 허가가 필요할 수 있어요','야외음악당 북서쪽으로 들어오는 방문객을 통제할지는 팀회의 안건이에요'],
  src:'Y.지도/Y_축제전체_지도 2·3·4장·5장 · P0-3_장소 2-3'},
 {id:'z11',no:'1-1',name:'운영·관리 본부',grp:0,color:'#2F6BFF',
  shapes:[{t:'p',pts:'1140,262 1270,196 1340,258 1322,356 1206,385'}],pill:[1236,332,'운영진·안내데스크'],
  kw:['운영관리본부','운영본부','본부'],
  what:'안내도에 "운영·관리 본부"로 표시된 큰 구역이에요. 2.28자유광장 앞 광장 일부를 써요.',
  items:['운영진 부스와 안전 부스(안내데스크, 의료실 등)가 들어가요','스탬프북 배부, 완성 보상 교환, 정보 안내를 해요(스탬프 운영은 H-10 담당)','2.28자유광장 안쪽 타원형 경기장은 사용하지 않고, 앞 광장 일부만 운영·안전 부스로 써요'],
  need:['2.28자유광장 앞 광장 사용 허가·공문이 필요해요','안내도의 "본부" 표시와 자료의 "운영·안전 부스" 표현이 달라서, 본부 규모는 자료에서 찾지 못했어요'],
  src:'Y.지도/Y_축제전체_지도 3·3-1장 · P0-3_장소 2-3, 2-3-2'},
 {id:'z12',no:'1-2',name:'운영·관리 부스 (출입로 옆)',grp:0,color:'#2F6BFF',
  shapes:[{t:'l',pts:'1088,264 1172,222'}],pill:[1010,176,'안내·스탬프북'],
  kw:['출입로옆부스','운영안전부스','안내데스크','스탬프북배부'],
  what:'출입로 바로 옆 공원순환로 초입에 두는 운영·안전 부스예요.',
  items:['운영진 부스와 안내데스크 같은 안전 관련 부스가 들어가요','스탬프북·축제 팔찌 같은 참여 물품과 정보를 나눠 주고 안내해요(스탬프북 제도는 M-6, 팔찌는 담당 파트에서 정해요)'],
  need:['안전 부스 종류는 다른 파트에서 정리한 목록을 따라요'],
  src:'Y.지도/Y_축제전체_지도 3·3-1장'},
 {id:'z134',no:'1-3 · 1-4',name:'운영·관리 부스 (메인구역)',grp:0,color:'#2F6BFF',
  shapes:[{t:'l',pts:'96,688 132,604'},{t:'l',pts:'170,553 288,517'}],pill:[120,512,'운영·안전 부스'],
  kw:['메인구역운영부스','X구역','엑스구역','x1','분수대앞'],
  what:'메인구역 X구역에 두는 운영·안전 부스예요(2027 기준).',
  items:['X구역에는 운영·안전 부스와 굿즈샵·이벤트 부스가 함께 들어가요','X-1은 분수대 앞 평지예요. 토론대회 리허설 때 신분증 확인도 여기서 해요','X·Y·Z 구역은 해마다 용도가 바뀔 수 있어요'],
  need:['안내도는 계속 업그레이드 중이라 부스 위치가 바뀔 수 있어요'],
  src:'Y.지도/Y_메인구역_지도 2장 · P0-3_장소 2-3-1'},
 {id:'z2',no:'2',name:'플리마켓',grp:1,color:'#F2B705',
  shapes:[{t:'l',pts:'1020,503 1018,440 1035,370 1060,310 1078,272'}],pill:[1135,445,'플리마켓 50~60부스'],
  kw:['플리마켓위치','플리마켓어디','플리마켓자리','장터위치','장터어디','플리마켓구역'],
  what:'소상공인 플리마켓이 공원순환로를 따라 길게 들어서요.',
  items:['운영·안전 부스가 있는 길부터 두류공원2공영주차장 앞 공원순환로까지예요','부스는 최소 50 ~ 최대 60개(3m × 3m)이고, 셀러가 적어 낸 요청 부스 수의 합계로 정해져요','판매와 체험·협업 비율은 고정이 아니라 참고 목표예요','매일 12:00 개장, 금·토 22:00 / 일 20:00 폐장이에요'],
  need:['2027 기획안 초안은 플리마켓을 잔디광장 쪽으로 적었어요. 최신 안내도(공원순환로변)를 기준으로 봐요','공원순환로 차량 통제 허가가 필요해요'],
  src:'P0-3_장소 2-3 · C파트 C-1 · Y.지도/Y_축제전체_지도 3장'},
 {id:'z3',no:'3-1 · 3-2',name:'7구 맛집거리',grp:1,color:'#E5484D',
  shapes:[{t:'l',pts:'612,604 810,550 1012,512'},{t:'l',pts:'862,410 890,528'},{t:'l',pts:'180,926 300,820 400,740 490,658'}],pill:[800,688,'7구 맛집거리 60~70부스'],
  kw:['7구위치','7구어디','맛집거리위치','맛집거리어디','맛집거리자리','7구맛집거리위치'],
  what:'대구 7개 구의 맛집과 제과점이 공원순환로를 따라 이어지는 먹거리 거리예요.',
  items:['플리마켓 끝부터 임시 바리게이트 ①(자료의 ⑴)까지 이어지는 공원순환로예요','중·동·서·남·북·수성·달서구의 대표 맛집과 제과점, 프랜차이즈 후원사 부스가 들어가요','부스는 60 ~ 70개(5m × 5m)이고, 구별 최소 7동(달서구는 8동)이에요','프랜차이즈 후원사는 별도 구역 없이 7구 맛집거리 안에 함께 둬요'],
  need:['7구 안에서 일반 업소 구간과 프랜차이즈 구간을 어떻게 나눌지는 미정이에요','7구 맛집거리 중간~바리게이트 ① 구간에는 기존 화장실이 없어서 이동식 화장실 후보 구간이에요'],
  src:'B파트 B-1·B-4 · P0-3_장소 2-3 · Y.지도/Y_축제전체_지도 3·4-2장'},
 {id:'z4',no:'4',name:'굿즈샵·이벤트 부스',grp:2,color:'#F28C28',
  shapes:[{t:'l',pts:'432,614 505,578'}],pill:[615,652,'굿즈샵·이벤트 부스'],
  kw:['굿즈샵위치','굿즈샵어디','굿즈샵은어디','굿즈샵자리','굿즈상점위치','굿즈부스','이벤트부스','굿즈어디서'],
  what:'공식 굿즈 상점과 이벤트 부스가 들어가는 메인구역 가장자리예요.',
  items:['굿즈 상점 1곳과 이벤트 부스가 메인구역 X구역에 들어가요','굿즈 8종: 아크릴 키링, 스티커, 머리띠, 마그넷, 에코백, 티셔츠, 수면안대, 텀블러','매일 12:00 개장, 금·토 22:00 / 일 20:00 폐장이고, 상점 운영 시간은 이에 맞추는 안이에요(제안)','스탬프 교환용 굿즈는 팔지 않고, 교환 지급으로 따로 기록해요'],
  need:['상점 위치는 지도 확정을 따르고, 운영진 부스와 같이 쓸지는 미정이에요','결제·정산 방식과 인력은 미정이에요. 가격과 수량도 아직 정해지지 않았어요'],
  link:{label:'굿즈샵 구경하기',sel:'#shop'},
  src:'D파트 D-05 2-1~2-3 · D-02 · P0-3_장소 2-3-1'},
 {id:'z5',no:'5',name:'메인무대 (코오롱 야외음악당)',grp:2,color:'#B3141C',
  shapes:[{t:'e',cx:388,cy:548,rx:88,ry:80}],pill:[388,548,'토론 대회 무대'],
  kw:['메인무대','야외음악당','코오롱','야당','말판','무대위치','무대어디'],
  what:'코오롱 야외음악당(야당)이 메인무대예요.',
  items:['주소: 대구 달서구 야외음악당로 180','메인 프로그램과 부대 프로그램이 열려요. 2027 기획안에서는 사투리 토론 대회 \'말판\' 무대로 써요(토요일 20:30 결승)','고정 객석이 있어서 관람과 투표에 알맞아요','음악당 건물은 메인무대 스태프, 방송 장비, 섭외자(연예인·뮤지컬 배우 등)가 들어오는 곳이에요','메인무대와 앞 잔디광장을 합쳐서 "메인구역"이라고 불러요'],
  need:['"광장"과 "잔디광장" 중 공식 표현은 팀회의 안건이에요','코오롱 야외음악당·잔디광장 대관 허가가 필요해요'],
  src:'Y.지도/Y_메인구역_지도 · Y_축제전체_지도 3-2장 · 03_기획안 6-2, 12-3'},
 {id:'z6',no:'6',name:'10미 포장마차',grp:2,color:'#A66CE8',
  shapes:[{t:'l',pts:'105,712 130,760 200,795 285,790 355,745 405,690 425,640'}],pill:[240,842,'10미 포장마차'],
  kw:['포장마차위치','포장마차어디','포장마차자리','10미위치','10미어디','n-2'],
  what:'대구 10미 포장마차 부스가 메인구역 바깥쪽 가장자리를 따라 들어가요.',
  items:['메인구역 Z구역과 E·F·G 뒤쪽 외곽(n-2)에 10미 부스가 들어가요','부스는 최소 40동(5m × 5m)이 기준이에요','대구말로 주문하면 스탬프 1개를 주는 사투리 주문 미션이 있어요(선택, 표준어 주문도 똑같이 받아요)','부스마다 시내 원조가게 QR 카드를 달아 일요일 스탬프투어로 이어져요','돗자리 촌(바닥 좌석)과 테이블 촌(테이블 좌석)에서 먹어요'],
  need:['E·F·G의 n-1 / n-2 구분선은 지도 담당이 정할 예정이에요','10미 부스 수가 문서마다 달라요. 2027 기획안 초안은 15동, 최신 P0-3는 최소 40동이에요'],
  src:'Y.지도/Y_메인구역_지도 2장 · P0-3_장소 2-3 · 03_기획안 6-3'},
 {id:'z7',no:'7',name:'돗자리존',grp:2,color:'#4FB0EE',
  shapes:[{t:'p',pts:'150,560 285,520 318,560 330,625 410,625 425,640 405,700 350,750 270,785 190,780 125,740 98,690 125,620'}],pill:[215,660,'돗자리 존'],
  kw:['돗자리','돗자리존','돗자리촌','테이블존','테이블촌','잔디밭','a구역','b구역','c구역','d구역'],
  what:'메인구역 A·B·C·D 구역이 돗자리 존이에요.',
  items:['바닥에 돗자리를 깔고 앉아 먹고 쉬는 좌석 구역이에요(돗자리 촌)','C구역이 구심점이에요. 메인무대와 가까우면 앞쪽, 멀면 뒤쪽이라고 불러요','E·F·G 앞쪽(n-1)은 테이블 존으로, 10미 손님과 선착순으로 자유롭게 써요','A구역은 골든벨 예선 장소였지만, 최신 문서는 무대 앞 의자석을 써요'],
  need:['의자석 위치는 메인구역 구획 지도에 아직 없어요'],
  src:'Y.지도/Y_메인구역_지도 2·3장 · P0-3_장소 2-3-1 · B파트 B-1'},
 {id:'zmain',no:'메인 스테이지',name:'메인구역 전체',grp:2,color:'#7B2FBF',
  shapes:[{t:'p',pts:'22,610 60,520 150,455 300,430 430,440 480,480 470,640 400,760 250,815 130,790 60,690',dash:true}],
  kw:['메인구역','메인스테이지','메인존','메인구역구성'],
  what:'메인무대, 돗자리존, 포장마차를 한 덩어리로 묶은 구역이에요(점선 영역).',
  items:['메인구역 = 메인무대 + A~G + X·Y·Z (지도 담당 결정, 2026-11-18)','A·B·C·D는 돗자리 존, E·F·G는 테이블 존(뒤쪽 n-2는 10미 포장마차), X·Y·Z는 부스 구역이에요','X·Y·Z는 해마다 용도가 바뀔 수 있어요(2027: X는 운영·굿즈, Z는 10미 포장마차)','X·Y·Z는 구심점인 C구역과 가까운 쪽을 내부, 먼 쪽을 외곽이라고 불러요'],
  need:['안내도는 계속 업그레이드 중이라 메인구역 배치가 바뀔 수 있어요'],
  src:'Y.지도/Y_메인구역_지도 · P0-3_장소 2-3-1'},
 {id:'z8',no:'8',name:'식사존',grp:3,color:'#F07FB0',
  shapes:[{t:'p',pts:'888,430 985,410 1010,445 1005,490 990,512 900,518'}],pill:[948,392,'테이블·의자·중계화면'],
  kw:['식사존','광장휴게소','2공영주차장','쉴곳','어디서먹'],
  what:'7구 맛집거리 음식을 먹고 쉬는 곳이에요. 메인구역 혼잡을 나누는 역할도 해요.',
  items:['두류공원2공영주차장(광장휴게소 옆)을 차량 통제 후 써요','테이블과 의자를 놓고, 앞쪽에 메인무대 중계 대형 디스플레이를 둬요','플리마켓과 7구 맛집거리가 만나는 곳 북쪽이에요','광장휴게소 화장실이 바로 옆이에요(축제 기간 개방 시간은 미확인)'],
  need:['2공영주차장 사용 허가가 필요해요','식사존을 맡는 파트는 아직 정해지지 않았어요','광장휴게소·관광정보센터를 화장실 말고 쉼터로 쓸지는 검토 중이에요'],
  src:'Y.지도/Y_축제전체_지도 3·4-1·4-2장 · P0-3_장소 2-3'},
 {id:'zmed',no:'의료실',name:'의료실',grp:3,color:'#2E9E4F',
  shapes:[{t:'c',cx:272,cy:460,r:26},{t:'c',cx:1055,cy:228,r:26},{t:'c',cx:1330,cy:205,r:26}],
  kw:['의료실','의료','응급','구급','온열','더위쉼터','쉼터','화장실','편의시설'],
  what:'안내도에 의료실이 세 곳 표시돼 있어요. 출입로 쪽 두 곳, 메인구역 한 곳이에요.',
  items:['의료실은 안전 부스(안내데스크, 의료실 등)에 포함돼요','2027 기획안: 구급차 1대와 의료 인력이 3일 동안 상주해요(온열질환 대응, 추정)','낮 12~16시에는 야외 핵심 프로그램을 두지 않고 냉방 쉼터를 둬요','기존 화장실은 출입로~운영·안전 부스 쪽에 많고, 7구 맛집거리 중간 구간에는 없어서 이동식 화장실을 검토해요'],
  need:['더위 쉼터, 물품보관소, 이동식 화장실 위치는 지도 담당이 작성 중이에요','2.28자유광장 화장실은 등록 개방시간이 18시까지라 저녁 개방 연장 공문이 필요해요'],
  src:'Y.지도/Y_축제전체_지도 3-1·4·4-2장 · 03_기획안 11·12장'},
 {id:'zbar',no:'①~④',name:'임시 바리게이트',grp:3,color:'#555B66',
  shapes:[{t:'c',cx:185,cy:966,r:26},{t:'c',cx:874,cy:315,r:26},{t:'c',cx:1128,cy:527,r:26},{t:'c',cx:408,cy:337,r:26}],
  kw:['바리게이트','바리케이드','통제','차량통제','막는','비상차량','비상차'],
  what:'축제 운영을 위해 임시로 길을 막는 곳이에요. 안내도에 네 곳이 표시돼 있어요.',
  items:['① (자료의 ⑴) 7구 맛집거리 끝, 오르막길 시작 부근을 막아요','② (자료의 ⑵) 야외음악당로와 공원순환로가 만나는 길, 3공영주차장 입구 근처예요. 비상차량이 필요할 때와 폐장 때 열어요','③ (자료의 ⑶) 2.28자유광장 서남쪽 갈림길에서 남동쪽으로 이어지는 공원순환로를 막기로 했어요','④ 안내도 북서쪽(두류3동 쪽)에 있어요. 자료에는 이쪽 통제 여부를 논의 중이라고만 있어요'],
  need:['③을 막아도 되는지 팀 확인이 필요해요','④는 번호가 자료와 맞는지 확인이 필요해요(제 해석이에요)','공원순환로 차량 통제 허가가 필요할 수 있어요'],
  src:'Y.지도/Y_축제전체_지도 6-1장·5장 미확정 1·7번'},
 {id:'zsign',no:'표지판',name:'표지판',grp:3,color:'#F5A300',
  shapes:[{t:'c',cx:423,cy:257,r:28}],
  kw:['표지판','안내판','사인물'],
  what:'안내도 범례에 표지판 표시가 있어요.',
  items:['안내도 북쪽(두류3동 쪽)에 한 곳 표시돼 있어요'],
  need:['설치 내용, 문구, 개수는 자료에서 찾지 못했어요. 지도 담당에게 확인이 필요해요'],
  src:'두류공원 축제 안내도(범례)'}
];
const ZBY=Object.fromEntries(ZONES.map(z=>[z.id,z]));
const ZGRP=['입구·운영','거리','메인구역','편의·안전'];
const hex2rgba=(h,a)=>{const n=parseInt(h.slice(1),16);return `rgba(${n>>16},${(n>>8)&255},${n&255},${a})`};

/* ---------- 챗봇 연동: 구역별 질문 답변 ---------- */
function zoneAnswer(z){
  const rel=ZONES.filter(x=>x.id!==z.id&&x.grp===z.grp).slice(0,2);
  const chs=[{label:'지도에서 보기',act:'zonemap',id:z.id},...rel.map(r=>({label:r.name,act:'zone',id:r.id}))];
  if(z.link)chs.push({label:z.link.label,act:'goto',sel:z.link.sel});
  return {html:`<p><b>${esc(z.no.length<=4&&/^\d/.test(z.no)?'('+z.no+') ':'')}${esc(z.name)}</b> · ${esc(z.what)}</p><ul>${z.items.map(i=>`<li>${i}</li>`).join('')}</ul><p>${L('hyp','확인 필요')} ${z.need.map(esc).join(' / ')}</p>${SRC(z.src)}`,ch:chs};
}
async function answerZone(z){const a=zoneAnswer(z);await botSay(a.html,a.ch)}
KB.push({id:'map',kw:['지도','맵','안내도','배치도','구역안내','구역별','축제장지도','축제맵','동선','구역','위치'],a:()=>({html:`<p>축제장 지도를 같이 볼까요? 어느 구역이 궁금하세요? 버튼을 누르면 그 구역에서 무엇을 설치하고 운영하는지 알려 드려요. 지도에서도 바로 찾아 줄게요!</p>`,ch:[
  {label:'출입로·운영 부스',act:'zone',id:'z0'},{label:'플리마켓',act:'zone',id:'z2'},{label:'7구 맛집거리',act:'zone',id:'z3'},{label:'메인무대',act:'zone',id:'z5'},{label:'10미 포장마차',act:'zone',id:'z6'},{label:'식사존',act:'zone',id:'z8'},{label:'굿즈샵·이벤트',act:'zone',id:'z4'},{label:'지도 전체 보기',act:'goto',sel:'#map'}]})});
ZONES.forEach(z=>{KB.push({id:'zone_'+z.id,bonus:1.8,exact:['z2','z3','z4','z6'].includes(z.id),kw:z.kw,a:()=>{selectZone(z.id,{scroll:false});return zoneAnswer(z)}});TN['zone_'+z.id]=z.name});
TN.map='축제 지도';

/* ---------- 지도 렌더 ---------- */
let SELZ=null,PILLS=false;
function shapeSVG(s,z){
  if(s.t==='c')return `<circle class="shp" cx="${s.cx}" cy="${s.cy}" r="${s.r}"/>`;
  if(s.t==='e')return `<ellipse class="shp" cx="${s.cx}" cy="${s.cy}" rx="${s.rx}" ry="${s.ry}"/>`;
  if(s.t==='p')return `<polygon class="shp ${s.dash?'dash':''}" points="${s.pts}"/>`;
  return `<polyline class="shp ln" points="${s.pts}"/>`;
}
function renderMap(){
  const gs=ZONES.map(z=>`<g class="hot" id="hz_${z.id}" data-zone="${z.id}" role="button" tabindex="0" aria-label="${esc(z.name)} 자세히 보기" style="--zc:${z.color};--zf:${hex2rgba(z.color,.28)}">${z.shapes.map(s=>shapeSVG(s,z)).join('')}</g>`).join('');
  const pills=ZONES.filter(z=>z.pill).map(z=>{const [x,y,t]=z.pill;const w=t.length*25+30;return `<g class="pill" style="--zc:${z.color}" transform="translate(${x},${y})"><rect x="${-w/2}" y="-22" width="${w}" height="44" rx="22"/><text text-anchor="middle" y="9">${esc(t)}</text></g>`}).join('');
  $('#mapSvg').insertAdjacentHTML('beforeend',`<g id="hots">${gs}</g><g id="pills">${pills}</g>`);
  $('#zoneBtns').innerHTML=ZGRP.map((g,gi)=>`<div class="zgrp"><span class="zg">${g}</span><div class="zrow">${ZONES.filter(z=>z.grp===gi).map(z=>`<button type="button" class="zbtn" data-zone="${z.id}" aria-pressed="false" style="--zc:${z.color}"><i class="zdot"></i><span><em>${esc(z.no)}</em>${esc(z.name)}</span></button>`).join('')}</div></div>`).join('');
  $('#map').addEventListener('click',e=>{const t=e.target.closest('[data-zone]');if(t)selectZone(t.dataset.zone,{scroll:false})});
  $('#map').addEventListener('keydown',e=>{if((e.key==='Enter'||e.key===' ')&&e.target.closest('[data-zone]')){e.preventDefault();selectZone(e.target.closest('[data-zone]').dataset.zone,{scroll:false})}});
  $('#pillBtn').addEventListener('click',()=>{PILLS=!PILLS;$('#mapSvg').classList.toggle('showpills',PILLS);$('#pillBtn').setAttribute('aria-pressed',PILLS);$('#pillBtn').textContent=PILLS?'설치·운영 표시 끄기':'설치·운영 표시 켜기'});
  $('#zoneDetail').addEventListener('click',e=>{
    const g=e.target.closest('[data-goto]');if(g){const t=document.querySelector(g.dataset.goto);if(t)t.scrollIntoView({behavior:'smooth',block:'start'})}
    const a=e.target.closest('[data-ask]');if(a){document.querySelector('#demo').scrollIntoView({behavior:'smooth',block:'start'});handleUser(a.dataset.ask)}
  });
  selectZone(null);
}
function selectZone(id,{scroll=false}={}){
  SELZ=id;
  document.querySelectorAll('.hot').forEach(g=>g.classList.toggle('on',g.dataset.zone===id));
  document.querySelectorAll('.zbtn').forEach(b=>b.setAttribute('aria-pressed',b.dataset.zone===id));
  const box=$('#zoneDetail');
  if(!id){
    box.innerHTML=`<div class="zempty"><i class="spr" data-pose="k.peek" style="--dw:130px"></i><h3>구역을 눌러 보세요</h3><p>지도 위 구역이나 위쪽 버튼을 누르면, 그 구역에 무엇을 설치하고 어떻게 운영하는지 알려 드려요.</p><p class="zhint">지도 위 <b>설치·운영 표시 켜기</b>를 누르면 구역마다 들어갈 내용이 한눈에 보여요.</p></div>`;
    initSprIn(box);return;
  }
  const z=ZBY[id];
  box.innerHTML=`<div class="zhead" style="--zc:${z.color}"><span class="zno">${esc(z.no)}</span><h3>${esc(z.name)}</h3></div>
    <p class="zwhat">${esc(z.what)}</p>
    <h4>설치·운영 내용</h4><ul class="zlist">${z.items.map(i=>`<li>${i}</li>`).join('')}</ul>
    <h4>확인이 필요한 것 ${L('hyp','미정')}</h4><ul class="zlist need">${z.need.map(i=>`<li>${esc(i)}</li>`).join('')}</ul>
    <div class="zact">${z.link?`<button type="button" class="link-btn" data-goto="${z.link.sel}">${esc(z.link.label)}</button>`:''}<button type="button" class="link-btn" data-ask="${esc(z.name)} 알려줘">대키미에게 물어보기</button></div>
    <small class="src">출처: ${esc(z.src)} · 안내도는 계속 업그레이드 중이라 바뀔 수 있어요.</small>`;
  if(scroll){const m=document.querySelector('#map');if(m)m.scrollIntoView({behavior:'smooth',block:'start'})}
}
renderMap();
