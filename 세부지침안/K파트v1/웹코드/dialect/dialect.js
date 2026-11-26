/* K11 사투리 사전·번역기·능력고사·챗봇. 챗봇은 규칙 기반 모의 — 실제 AI는 K11.md */
(() => {
  const { S, esc, st, src, seg, store, toast, go, render } = window.H;
  const K = window.K;
  const D = window.DICT;
  const { auth } = K;

  const dictCard = (e) => `<div class="dentry"><b>${esc(e.w)}</b> <span class="muted">${esc(e.pos)} · ${esc(e.region)}</span>
    <div>${esc(e.mean)}</div>${e.ex ? `<div class="muted">예) ${esc(e.ex)}</div>` : ''}<div class="muted">${esc(e.ctx)}</div></div>`;
  function dialectView(sub) {
    sub = sub || 'dict';
    let body = '';
    if (sub === 'dict') {
      body = `<input type="search" id="dq" placeholder="사투리·표준어 검색 (예: 부추, 억수로)"><div class="dwrap" id="dlist" style="margin-top:10px">${D.map(dictCard).join('')}</div>
        <p class="foot-note">출처: J-1 사투리 사전 본문 ${D.length}개 (대구·경북 기준). 뜻은 출처 확인이 끝난 값만 보여요.</p>`;
    } else if (sub === 'trans') {
      body = `<div class="card"><b>표준어 ↔ 사투리 번역기</b><p class="muted">사전에 있는 단어만 바꿔요. 표기는 “표준어(사투리)” 순서예요.</p>
        <textarea id="tin" rows="3" placeholder="예: 부추전이 모두 흔하다"></textarea>
        <div class="row" style="gap:8px;margin-top:8px"><button class="btn pri" data-act="tr" data-d="s2d">표준어 → 사투리</button><button class="btn ghost" data-act="tr" data-d="d2s">사투리 → 표준어</button></div>
        <div class="outbox" id="tout">결과가 여기에 나와요.</div></div>`;
    } else if (sub === 'quiz') {
      body = quizView();
    } else {
      const log = (store.get('chat', null) || [{ b: '안녕! 대키미예요 🐱 일정·위치·주문·사투리 뜻을 물어보세요.' }]);
      body = `<div class="card"><div class="chat" id="chat">${log.map((m) => m.u ? `<div class="u">${esc(m.u)}</div>` : `<div class="b">${esc(m.b)}</div>`).join('')}</div>
        <div class="chips">${['개장 시간', '토론 언제 해요?', '주문 어떻게 해요?', '숙박 혜택', '억수로 뜻'].map((x) => `<button class="food-chip" data-act="ask" data-q="${x}">${x}</button>`).join('')}</div>
        <div class="row" style="gap:8px;margin-top:8px"><input class="txt" id="cin" placeholder="질문을 입력하세요"><button class="btn pri" data-act="ask-send">보내기</button></div></div>
        <p class="foot-note">시험판 챗봇은 규칙 기반 응답이에요(실제는 AI 챗봇이 사전 DB를 참조). 모르는 건 운영·안전 부스에 물어봐 주세요.</p>`;
    }
    return `<div class="page-title">사투리</div>${seg('dialect', [['dict', '사전'], ['trans', '번역기'], ['quiz', '능력고사'], ['bot', 'AI 챗봇']], sub)}<div class="fade-in">${body}</div>`;
  }
  /* 온라인 사투리 능력고사: 5문항 4지선다, 문항은 8개 중 무작위. 계정·스탬프와 무관하고 점수는 저장하지 않아요 */
  let QZ = null;
  const quizView = () => {
    const QS = window.QUIZ;
    if (!QZ) return `<div class="card" style="text-align:center"><div style="font-size:42px">📝</div><h3>대구 사투리 능력고사</h3>
      <p>사투리 뜻을 맞히는 <b>5문제</b>예요. 몰라도 괜찮아요. 틀려도 해설이 알려 줘요!</p>
      <button class="btn pri" data-act="quiz-start">시작하기</button></div>`;
    if (QZ.i >= QZ.qs.length) {
      const n = QZ.score, msg = n === 5 ? '대구 토박이급이에요! 🐱' : n >= 3 ? '꽤 잘 알아요! 외지몽도 놀랄 실력 🐶' : '괜찮아요, 오늘 하나 배웠으면 된 거예요 🌱';
      return `<div class="card" style="text-align:center"><div style="font-size:38px">🎉</div><h3>${n} / ${QZ.qs.length}</h3><p>${msg}</p>
        <div class="row" style="gap:8px;justify-content:center"><button class="btn pri" data-act="quiz-start">다시 풀기</button><button class="btn ghost" data-seg="dialect" data-k="dict">사전 보러 가기</button></div></div>`;
    }
    const q = QZ.qs[QZ.i], done = QZ.pick !== null;
    return `<div class="card"><span class="badge">${QZ.i + 1} / ${QZ.qs.length}</span> <b style="display:block;margin-top:8px">${esc(q.q)}</b>
      <div class="opts">${q.o.map((o, k) => `<button class="btn ghost" style="text-align:left;${done && k === q.a ? 'border-color:#16a34a;background:#e3f7ea;' : ''}${done && k === QZ.pick && k !== q.a ? 'border-color:var(--red);background:#fdeaea;' : ''}" data-act="quiz-pick" data-k="${k}" ${done ? 'disabled' : ''}>${'①②③④'[k]} ${esc(o)}</button>`).join('')}</div>
      ${done ? `<div class="callout ${QZ.pick === q.a ? 'blue' : 'red'}">${QZ.pick === q.a ? '정답! ' : '아쉬워요. 정답은 ' + '①②③④'[q.a] + '번. '}${esc(q.why)}</div>
        <button class="btn pri" data-act="quiz-next" style="width:100%;margin-top:8px">${QZ.i + 1 === QZ.qs.length ? '결과 보기' : '다음 문제'}</button>` : ''}</div>`;
  };
  const translate = (text, dir) => {
    const pairs = D.filter((e) => e.std && e.std.length <= 7 && !/[~]/.test(e.std)).map((e) => dir === 's2d' ? [e.std, e.dia] : [e.dia, e.std]).sort((a, b) => b[0].length - a[0].length);
    let out = text, hit = 0;
    pairs.forEach(([from, to]) => { if (out.includes(from)) { out = out.split(from).join(`\u0001${from}\u0002${to}\u0003`); hit++; } });
    out = out.replace(/\u0001([^\u0002]*)\u0002([^\u0003]*)\u0003/g, dir === 's2d' ? '$1($2)' : '$2($1)');
    return hit ? out : '바꿀 단어를 찾지 못했어요. 사전에 있는 단어로 써 보세요.';
  };
  const bot = (q) => {
    const s = q.replace(/\s/g, ''); const f = S.festival;
    const hit = D.find((e) => s.includes(e.w) || (e.std.length > 1 && s.includes(e.std.replace(/\s/g, ''))));
    if (/개장|시간|몇시|폐막|운영/.test(s)) return `매일 12:00에 열어요. ${f.hours}`;
    if (/토론|결승|투표/.test(s)) return '토론 대회 본선·결승은 일요일(8/22)에만 해요. 결승은 16:00~17:00. 투표는 로그인 후 경기마다 1표예요.';
    if (/주문|결제|대기|웨이팅/.test(s)) return '10미·7구 부스는 주문 탭에서 카카오페이로 결제하고 대기번호를 받아요. 현장에서 구두로 주문·결제해도 같은 줄이에요. 구글 계정은 현장 구매를 이용해 주세요.';
    if (/스탬프|쿠폰/.test(s)) return '스탬프·쿠폰은 웹에서 안내하지 않아요. 현장 운영·안전 부스에 문의해 주세요.';
    if (/숙박|호텔|대구로페이/.test(s)) return '대구 밖에 사는 분은 사전 신청 → 1박 → 인증 후 대구로페이를 받아요. 금액은 미확정이에요.';
    if (/위치|어디|지도|화장실|출입/.test(s)) return `${f.placeDetail}에서 열려요. 지도 탭에서 구역을 눌러 보세요. 출입로는 두류공원로·공원순환로 교차점이에요.`;
    if (hit) return `“${hit.w}” = ${hit.mean}${hit.ex ? `\n예) ${hit.ex}` : ''}`;
    return '잘 모르겠어요 🙏 행사 정보만 답할 수 있어요. 운영·안전 부스에서 안내받을 수 있어요.';
  };
  Object.assign(window.VIEWS, { dialect: dialectView });

  document.addEventListener('input', (e) => {
    if (e.target.id !== 'dq') return;
    const v = e.target.value.trim().replace(/\s/g, '');
    document.getElementById('dlist').innerHTML = D.filter((x) => !v || x.w.includes(v) || x.std.replace(/\s/g, '').includes(v) || x.mean.replace(/\s/g, '').includes(v)).map(dictCard).join('') || '<div class="card">검색 결과가 없어요.</div>';
  });
  const say = (q) => {
    const log = (store.get('chat', null) || [{ b: '안녕! 대키미예요 🐱 일정·위치·주문·사투리 뜻을 물어보세요.' }]);
    log.push({ u: q }, { b: bot(q) }); store.set('chat', log); render();
  };
  document.addEventListener('click', (e) => {
    const el = e.target.closest('[data-act]'); if (!el) return; const a = el.dataset.act;
    if (a === 'quiz-start') {
      QZ = { qs: window.QUIZ.slice().sort(() => Math.random() - 0.5).slice(0, 5), i: 0, score: 0, pick: null }; render();
    } else if (a === 'quiz-pick') {
      QZ.pick = Number(el.dataset.k); if (QZ.pick === QZ.qs[QZ.i].a) QZ.score++; render();
    } else if (a === 'quiz-next') {
      QZ.i++; QZ.pick = null; render();
    } else if (a === 'tr') {
      const t = document.getElementById('tin').value.trim(); if (!t) return toast('문장을 입력해 주세요');
      document.getElementById('tout').textContent = translate(t, el.dataset.d);
    } else if (a === 'ask') say(el.dataset.q);
    else if (a === 'ask-send') { const i = document.getElementById('cin'); if (i.value.trim()) say(i.value.trim()); }
  });
  document.addEventListener('keydown', (e) => { if (e.key === 'Enter' && e.target.id === 'cin') document.querySelector('[data-act="ask-send"]').click(); });
})();
