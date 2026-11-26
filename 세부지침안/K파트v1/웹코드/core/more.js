/* 신청 링크(구글 폼)·토론 투표·더보기 */
(() => {
  const { S, esc, st, src, seg, store, toast, go, render } = window.H;
  const K = window.K;
  const { auth } = K;

  window.formBtn = (k) => {
    const F = S.forms[k]; if (!F) return '';
    return `<div class="callout blue" style="margin-top:10px"><b>${esc(F.label)}</b><br><span class="muted">${esc(F.period)}</span>
      <ul class="dots">${F.notes.map((n) => `<li>${esc(n)}</li>`).join('')}</ul>
      ${F.url ? `<a class="btn pri" href="${esc(F.url)}" target="_blank" rel="noopener">구글 폼으로 이동</a>` : '<span class="badge">신청 링크 준비 중 (기획자 확인 필요)</span>'}</div>`;
  };
  const SEED = [[132, 118], [97, 141], [120, 120], [88, 103]];
  window.voteView2 = () => {
    const a = auth(); const votes = (store.get('votes', {}) || {});
    if (a.provider === 'guest') return `<div class="card"><b>투표는 로그인 후에 할 수 있어요</b><p class="muted">카카오 또는 구글 계정으로 로그인하면 경기마다 1표예요.</p><button class="btn-kakao" data-act="relogin">로그인하러 가기</button></div>`;
    return `<div class="card"><b>${esc(a.name)}</b>님 (${a.provider === 'kakao' ? '카카오' : '구글'} 계정) <span class="st st-plan">모의</span>
      <p class="muted" style="margin-top:6px">한 계정으로만 투표해 주세요. 경기마다 1표예요. 관객 점수는 최종 점수의 40%예요.</p></div>
      ${S.debate.bracket.map(([x, y], i) => { const v = votes[i];
        const [p, q] = SEED[i].map((n, j) => n + (v === j ? 1 : 0)); const pa = Math.round(p / (p + q) * 100);
        return `<div class="vote-match"><div class="lbl">8강 ${i + 1}경기</div><div class="vote-opts">
          <button class="dk" data-act="vote2" data-m="${i}" data-c="0" aria-pressed="${v === 0}" ${v !== undefined ? 'disabled' : ''}>${esc(x)}</button>
          <button class="om" data-act="vote2" data-m="${i}" data-c="1" aria-pressed="${v === 1}" ${v !== undefined ? 'disabled' : ''}>${esc(y)}</button></div>
          ${v !== undefined ? `<div class="res"><div class="bar"><div style="width:${pa}%;background:var(--dk)">${pa}%</div><div style="width:${100 - pa}%;background:#7fd3a0">${100 - pa}%</div></div></div>` : ''}</div>`; }).join('')}
      `;
  };
  const moreView = () => { const a = auth(); return `<div class="page-title">더보기</div>
    <div class="grid2">
      <button class="shortcut" data-go="debate"><span class="i">🎤</span><b>토론 대회·투표</b><span>대진표·논제·관객 투표</span></button>
      <button class="shortcut" data-go="benefit"><span class="i">🏨</span><b>숙박 혜택</b><span>숙박 인증 보상</span></button>
      <button class="shortcut" data-go="order:my"><span class="i">🧾</span><b>내 주문·대기</b><span>대기번호 확인</span></button>
      <button class="shortcut" data-go="time:sun"><span class="i">🕒</span><b>시간표</b><span>금·토·일</span></button>
    </div>
    <div class="card"><b>${esc(a.name)}</b> · ${a.provider === 'kakao' ? '카카오 계정' : a.provider === 'google' ? '구글 계정' : '로그인 안 함(둘러보기)'}
      <p class="muted">언어: 한국어 (영어는 준비 중)</p>
      <p class="muted">문의 번호: 준비 중이에요. 정해지면 여기에 표시돼요.</p>
      <button class="btn ghost" data-act="logout2">로그아웃 (모의 데이터 초기화)</button></div>`; };

  Object.assign(window.VIEWS, { more: moreView });

  document.addEventListener('click', (e) => {
    const el = e.target.closest('[data-act]'); if (!el) return;
    if (el.dataset.act === 'vote2') {
      const votes = (store.get('votes', {}) || {}); if (votes[el.dataset.m] !== undefined) return;
      votes[el.dataset.m] = Number(el.dataset.c); store.set('votes', votes); render(); toast('투표했어요!');
    }
  });
  render();
})();
