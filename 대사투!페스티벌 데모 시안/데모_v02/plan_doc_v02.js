/* ============ 기획안 문서 (미리보기 + 다운로드) ============
   내 기획 틀(선택 결과)을 8개 항목의 '대사투! 페스티벌 기획안(초안)'으로 만든다.
   대구시 보조사업 신청 서식(사업계획서 12개 항) · 행안부 지역축제 안전관리계획서 표준안 ·
   대구문화예술진흥원 인증제 서식의 항목 구성을 참고했다. 공식 제출 서식이 아니다. */
(function(){
  const plain=h=>String(h).replace(/<i class="lb[^"]*">([^<]*)<\/i>/g,'[$1]').replace(/<br\s*\/?>/g,' ').replace(/<[^>]+>/g,'');
  const BLANK='<span class="dc-blank">미입력 · 직접 작성</span>';
  const KDAY=['일','월','화','수','목','금','토'];

  function docBody(){
    const c=CBY[SEL.concept],f=FOCUS[SEL.focus],sc=SCALE[SEL.scale],st=STAY[SEL.stay];
    const today=new Date(), ds=today.getFullYear()+'. '+(today.getMonth()+1)+'. '+today.getDate()+'.';
    const money=c.id==='malson'?plain(sc.amt)+' 원 [추정]':'2027 기본안 대비 '+sc.ratio+'배 (금액 산정 전)';
    const tl=document.createElement('table');tl.innerHTML=timelineRows();
    const tlRows=[...tl.querySelectorAll('tr')].map(r=>'<tr>'+[...r.children].map((td,i)=>`<td${i===0?' class="dc-k"':''}>${esc(plain(td.innerHTML))}</td>`).join('')+'</tr>').join('');
    const T=(rows)=>'<table class="dc-t">'+rows.map(r=>'<tr>'+r.map((x,i)=>`<${i===0?'th':'td'}>${x}</${i===0?'th':'td'}>`).join('')+'</tr>').join('')+'</table>';
    return `
<h1 class="dc-title">「${esc(c.name)}」<br>대사투! 페스티벌 기획안 <small>(초안)</small></h1>
<p class="dc-warn">※ 시연용 기획 초안입니다. 대구광역시의 공식 제출 서식이 아니며, 실제 공모·협의 때는 해당 공고의 서식으로 옮겨 적어야 합니다.<br>※ <b>[추정]</b> <b>[가정]</b> 표시는 근거가 확정되지 않은 값이고, <span class="dc-blank">미입력</span> 칸은 담당자가 직접 채워야 합니다.</p>
<p class="dc-meta">작성일 ${ds} · 작성: 대키미 기획 에이전트(시연)</p>

<h2>1. 축제 개요</h2>
${T([
 ['축제명','대사투! 페스티벌 · '+esc(c.name)],
 ['개최 기간','2027. 8. 20.(금) ~ 8. 22.(일), 3일 [2027 일정표 기준]'],
 ['개최 장소','두류공원 일원 (대구 달서구) [main 자료 기준, 확정 전]'],
 ['주최 · 주관',BLANK],
 ['예상 관람객 / 순간 최대 인원',BLANK],
 ['총 사업비',money],
 ['선택한 구성',esc(f.label)+' · '+esc(sc.label)+' · '+esc(st.label)]
])}

<h2>2. 목적 · 필요성 · 차별화 전략</h2>
<p><b>핵심 목표.</b> ${esc(c.pros)}.</p>
<p><b>컨셉.</b> ${esc(c.line)}</p>
<p><b>차별화.</b> ${esc(plain(f.txt))}</p>
<p><b>필요성.</b> ${BLANK}</p>

<h2>3. 프로그램 구성</h2>
${T([['구분','프로그램','내용'],...c.programs.map((p,i)=>['프로그램 '+(i+1)+(i===f.idx?' (메인)':''),esc(p[0]),esc(p[1])])])}
<h3>3일 일정표 <small>(2027 일정표 기준 · 제안)</small></h3>
<table class="dc-t"><tr><th></th><th>8/20(금)</th><th>8/21(토)</th><th>8/22(일)</th></tr>${tlRows}</table>
<p><b>배치도.</b> ${BLANK}</p>

<h2>4. 추진 계획</h2>
${T([
 ['체류 · 상권 연결',esc(st.label)+' — '+esc(plain(st.txt))+'<br>'+esc(c.link)],
 ['마스코트 활용',esc(c.mascot)],
 ['운영 규모',esc(sc.txt)+' [가정]'],
 ['협력 기관 · 네트워크',BLANK],
 ['추진 일정(준비 단계)',BLANK]
])}

<h2>5. 사업비 계획</h2>
<p>총 사업비: <b>${money}</b></p>
${T([['비목','산출 근거 (단가 × 수량 × 횟수)','금액(원)'],['보조금 (시비 · 구군비)',BLANK,BLANK],['자부담',BLANK,BLANK],['수입금(입장·판매 등)',BLANK,BLANK],['비목별 집행 계획',BLANK,BLANK]])}
<p class="dc-note">세부 산출내역은 대구시 보조사업 신청 서식의 ‘사업비 집행계획(산출내역)’ 형식(단가 × 횟수 = 금액)에 맞춰 작성합니다.</p>

<h2>6. 안전관리 요약</h2>
${T([
 ['안전 인력',esc(sc.txt.split('·').find(x=>x.includes('안전'))||'')+' [가정]'],
 ['순간 최대 · 동시 수용 인원',BLANK],
 ['안전관리 조직 · 인파 · 교통 대책',BLANK],
 ['폭염 대응','12~16시 야외 핵심 프로그램 금지, 실내 사랑방(냉방 쉼터) 운영'],
 ['유의 사항',esc(c.caution)]
])}
<p class="dc-note"><b>법정 제출 서류.</b> 지역축제 안전관리계획서는 이 문서와 별도로 지정된 서식으로 작성해, 개최 3주 전까지 관할 구청장에게 제출해야 합니다(재난 및 안전관리 기본법 시행령 제73조의9 · 시행규칙 별지 제20호의3, 조사 자료 기준 — 담당 부서 확인 필요).</p>

<h2>7. 기대효과 · 자체 점검</h2>
<p>${esc(c.pros)}. 측정 가능한 장치: ${esc(plain(st.txt))}</p>
<table class="dc-t"><tr><th>점검 항목</th><th>상태</th></tr>
<tr><td>예산 편성</td><td>${c.id==='malson'?'초안 있음 [추정]':'산정 전'}</td></tr>
<tr><td>전담 인력 편성</td><td>규모만 가정 [가정]</td></tr>
<tr><td>방문객 추산</td><td>미입력</td></tr>
<tr><td>안전계획 수립</td><td>미수립 (별도 서식 필요)</td></tr></table>

<h2>8. 신청 단체 · 실적 · 확약</h2>
${T([['단체 소개',BLANK],['최근 3~5년 동종 행사 실적',BLANK],['자기부담 확약',BLANK],['서약서 · 개인정보 동의서','☐ 공고 서식으로 별도 작성']])}
<p class="dc-foot">대사투! 페스티벌 · 축제 기획 AI 에이전트 데모 · 시연용 초안</p>`;
  }

  const CSS=`.dc-title{font-size:24px;text-align:center;margin:0 0 14px;line-height:1.35}.dc-title small{font-size:15px;color:#667}
.dc-warn{background:#FFF6D6;border:1px solid #E8C65A;padding:9px 12px;font-size:12.5px;line-height:1.55;border-radius:6px}
.dc-meta{text-align:right;color:#667;font-size:12.5px;margin:6px 0 4px}
.dc h2{font-size:16px;margin:20px 0 8px;padding:4px 0 4px 10px;border-left:5px solid #3DA9DB;background:#F1F8FD}
.dc h3{font-size:14px;margin:14px 0 6px}.dc h3 small{font-weight:400;color:#667}
.dc p{margin:6px 0;line-height:1.65;font-size:13.5px}
.dc-t{width:100%;border-collapse:collapse;margin:6px 0;font-size:13px}.dc-t th,.dc-t td{border:1px solid #9AA7B5;padding:6px 9px;vertical-align:top;line-height:1.55;text-align:left}
.dc-t th{background:#EEF3F8;width:24%;font-weight:700}.dc-t tr:first-child th:only-child{width:auto}.dc-k{background:#F6F8FA;font-weight:700}
.dc-blank{color:#B0481F;background:#FFF0E6;padding:0 5px;border-radius:3px;font-size:12px}
.dc-note{font-size:12px!important;color:#445}.dc-foot{text-align:center;color:#889;font-size:11.5px!important;margin-top:22px!important;border-top:1px solid #CCD;padding-top:8px}`;

  function open(){
    if(!SEL.concept||!SEL.stay){return}
    let m=document.getElementById('docModal');
    if(!m){m=document.createElement('div');m.id='docModal';m.className='doc-modal';m.hidden=true;document.body.appendChild(m);}
    m.innerHTML=`<div class="doc-bar"><b>기획안 미리보기</b><span class="doc-hint">시연용 초안 · 공식 제출 서식 아님</span>
      <button type="button" class="doc-btn" data-d="print">PDF로 저장</button>
      <button type="button" class="doc-btn pri" data-d="doc">Word·한글용 파일 받기 (.doc)</button>
      <button type="button" class="doc-btn" data-d="close" aria-label="닫기">닫기 ✕</button></div>
      <div class="doc-scroll"><article class="doc-paper dc"><style>${CSS}</style>${docBody()}</article></div>`;
    m.hidden=false;document.body.classList.add('doc-open');
    m.querySelector('.doc-scroll').scrollTop=0;
  }
  function close(){const m=document.getElementById('docModal');if(m)m.hidden=true;document.body.classList.remove('doc-open')}
  function download(){
    const html='<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:w="urn:schemas-microsoft-com:office:word" xmlns="http://www.w3.org/TR/REC-html40"><head><meta charset="utf-8"><title>대사투 페스티벌 기획안(초안)</title><style>body{font-family:"맑은 고딕","Malgun Gothic",sans-serif}'+CSS+'</style></head><body class="dc">'+docBody()+'</body></html>';
    const b=new Blob(['﻿',html],{type:'application/msword'}),a=document.createElement('a');
    a.href=URL.createObjectURL(b);a.download='대사투페스티벌_기획안_초안_'+CBY[SEL.concept].name.replace(/\s+/g,'')+'.doc';
    document.body.appendChild(a);a.click();setTimeout(()=>{URL.revokeObjectURL(a.href);a.remove()},500);
  }
  document.addEventListener('click',e=>{
    const t=e.target.closest('[data-d]');if(!t)return;
    const d=t.dataset.d;
    if(d==='open')open();else if(d==='close')close();else if(d==='print')window.print();else if(d==='doc')download();
  });
  document.addEventListener('keydown',e=>{if(e.key==='Escape')close()});

  /* 내 기획 틀이 채워질 때 상단에 '기획안 미리보기' 줄을 붙인다 */
  const _render=renderPlan;
  renderPlan=function(){
    _render();
    const host=document.getElementById('myplan');
    const bar=document.createElement('div');bar.className='doc-cta';
    bar.innerHTML=`<div><b>이 기획 틀로 기획안 만들기</b><span>공공기관 서식의 항목 구성을 참고한 8개 항목 초안이에요. 미리보기로 읽고 파일로 받을 수 있어요.</span></div>
      <button type="button" class="btn btn-sky" data-d="open">기획안 미리보기</button>`;
    host.insertBefore(bar,host.firstChild);
  };
})();
