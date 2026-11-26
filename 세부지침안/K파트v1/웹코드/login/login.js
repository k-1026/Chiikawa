/* K08 로그인·시작 전 질문. 로그인은 모의(데모) — 실제 연동은 K08.md */
(() => {
  const { S, esc, st, src, seg, store, toast, go, render } = window.H;
  const K = window.K;
  const Q = window.SURVEY;
  const { $view, $app, auth } = K;

  /* ---------- 게이트: 로그인 → 설문 ---------- */
  window.GATE = () => {
    const a = auth();
    $app.classList.toggle('gate', !a);
    if (!a) { $view.innerHTML = gateLogin(); return true; }
    return false;
  };
  const gateLogin = () => {
    const [dk, om] = S.mascots;
    return `<section class="card gate-card">
      <div class="duo"><figure><img src="${dk.img}" alt="${esc(dk.alt)}"></figure><span class="and">&</span><figure><img src="${om.img}" alt="${esc(om.alt)}"></figure></div>
      <h1>대사투</h1><p class="muted">${esc(S.festival.fullName)} · ${esc(S.festival.dates)}</p>
      <div class="message"><div class="q">“${esc(S.festival.message)}”</div></div>
      <label class="fld" for="nick">닉네임 (모의 로그인 — 실제 카카오·구글 연동 없음)</label>
      <input class="txt" id="nick" maxlength="12" placeholder="예: 대구초보">
      <button class="btn-kakao" data-act="auth" data-p="kakao">💬 카카오로 시작하기</button>
      <button class="btn-google" data-act="auth" data-p="google">G 구글로 시작하기</button>
      <button class="btn ghost" data-act="browse" style="width:100%;margin-top:8px">로그인 없이 둘러보기</button>
      <p class="muted" style="margin-top:12px">주문·투표는 로그인 후에 해요. 구매(카카오페이)는 카카오 계정만 가능해요. 구글 계정은 열람·설문·투표가 가능하고, 구매는 현장에서 해 주세요.</p>
      <p class="muted">웹을 쓰지 않아도 축제에는 똑같이 참여할 수 있어요.</p>
    </section>`;
  };
  const qHtml = (q, hide) => `<div class="card" data-q="${q.id}" ${hide ? 'hidden' : ''}><b>${q.n ? q.n + '. ' : ''}${esc(q.q)}</b>${q.note ? `<div class="muted">※ ${esc(q.note)}</div>` : ''}
    ${q.type === 'select' ? `<select name="sv_${q.id}"><option value="">선택</option>${q.opts.map((o) => `<option>${esc(o)}</option>`).join('')}</select>`
      : `<div class="opts" ${q.type === 'likert' ? 'style="grid-template-columns:repeat(5,1fr)"' : ''}>${q.opts.map((o) => `<label><input type="${q.type === 'check' ? 'checkbox' : 'radio'}" name="sv_${q.id}" value="${esc(o)}">${esc(o)}</label>`).join('')}</div>`}</div>`;
  const gateSurvey = () => `<div class="page-title">시작 전에 1분만요 🙌</div>
    <div class="card"><p class="muted">응답은 통계로만 쓰고 계정 정보와 따로 보관해요. 모두 선택이라 건너뛰어도 돼요.</p></div>
    ${Q.map((q) => qHtml(q) + (q.sub ? qHtml({ ...q.sub, type: 'radio' }, true) : '')).join('')}
    <button class="btn pri" data-act="survey-go" style="width:100%">제출하고 시작하기</button>
    <button class="btn ghost" data-act="survey-skip" style="width:100%;margin-top:8px">건너뛰기</button>`;
  window.surveyCard = () => store.get('survey', null) ? '' : `<button class="card shortcut" style="text-align:left;width:100%" data-go="survey"><b>시작 전에 1분만요 🙌</b> <span class="muted">방문자 설문 (모두 선택·건너뛰기 가능)</span></button>`;
  Object.assign(window.VIEWS, { survey: () => gateSurvey() });
  document.addEventListener('change', (e) => {   // 조건부 문항: 가족 → 자녀 나이대, 1박 이상 → 숙박 지역
    const n = e.target.name || ''; if (!n.startsWith('sv_')) return;
    const q = Q.find((x) => 'sv_' + x.id === n && x.sub); if (!q) return;
    const on = [].concat(q.sub.when).includes(e.target.value);
    const box = document.querySelector(`[data-q="${q.sub.id}"]`); if (box) box.hidden = !on;
  });
  document.addEventListener('click', (e) => {
    const el = e.target.closest('[data-act]'); if (!el) return; const a = el.dataset.act;
    if (a === 'auth') {
      const nick = (document.getElementById('nick').value.trim()) || '방문객';
      store.set('auth', { provider: el.dataset.p, name: nick }); toast(`${el.dataset.p === 'kakao' ? '카카오' : '구글'} 로그인(모의) 완료`); render();
    } else if (a === 'survey-go' || a === 'survey-skip') {
      const ans = {}; if (a === 'survey-go') [...Q, ...Q.filter((q) => q.sub).map((q) => q.sub)].forEach((q) => { const box = document.querySelector(`[data-q="${q.id}"]`); if (box && box.hidden) return; const els = [...document.querySelectorAll(`[name="sv_${q.id}"]`)]; const v = els[0] && els[0].tagName === 'SELECT' ? els[0].value : els.filter((x) => x.checked).map((x) => x.value).join(','); if (v) ans[q.id] = v; });
      store.set('survey', { done: true, skipped: a === 'survey-skip', ans }); go('home');
    } else if (a === 'browse') {
      store.set('auth', { provider: 'guest', name: '둘러보기' }); render();
    } else if (a === 'relogin') {
      store.set('auth', null); render();
    } else if (a === 'logout2') {
      ['auth', 'survey', 'cart', 'orders', 'votes', 'chat', 'stayStep'].forEach((k) => store.set(k, null)); history.replaceState(null, '', '#home'); render();
    }
  });
})();
