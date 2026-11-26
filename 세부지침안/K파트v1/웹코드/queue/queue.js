/* K10 대기번호·주문 현황. 대기열 시뮬레이션은 모의 — 실제는 서버·직원용 관리 화면(K10.md) */
(() => {
  const { S, esc, st, src, seg, store, toast, go, render } = window.H;
  const K = window.K;
  const { won, boothOf } = K;

  const orders = () => (store.get('orders', []) || []);
  const waitingAt = (b) => b.base + orders().filter((o) => o.boothId === b.id && o.status === 'wait').length;
  setInterval(() => {
    const os = orders(); let ch = false;
    os.forEach((o) => { if (o.status === 'wait') { o.ahead = Math.max(0, o.ahead - 1); ch = true; if (o.ahead === 0) { o.status = 'call'; toast(`🔔 ${o.no}번 호출! (카카오 알림톡 모의 발송)`); } } });
    if (ch) { store.set('orders', os); const h = location.hash; if (/^#(home|order|my)/.test(h) || h === '') render(); }
  }, 12000);
  K.orders = orders; K.waitingAt = waitingAt;

  window.homeBanner = () => {
    const sv = window.surveyCard ? window.surveyCard() : '';
    const os = orders().filter((o) => o.status !== 'done');
    if (!os.length) return sv;
    return sv + os.map((o) => o.status === 'call'
      ? `<div class="alim">🔔 카카오 알림톡(모의) · ${esc(o.no)}번 호출됐어요! ${esc(boothOf(o.boothId).name)}으로 오세요.</div>`
      : `<div class="card"><span class="badge">내 주문</span> ${esc(boothOf(o.boothId).name)} · 번호 <b>${esc(o.no)}</b> · 앞 대기 <b>${o.ahead}</b>팀</div>`).join('');
  };
  function myView() {
    const os = orders();
    return `<div class="page-title">내 주문</div>
      ${os.length ? os.slice().reverse().map((o) => {
        const b = boothOf(o.boothId);
        return `<div class="ticket"><div class="muted">${esc(b.name)}</div><div class="no">${esc(o.no)}</div>
          ${o.status === 'wait' ? `<p>앞 대기 <b>${o.ahead}</b>팀 · 약 ${o.ahead * 3}분</p>` : o.status === 'call' ? '<p><span class="badge call">호출됐어요! 부스로 오세요</span></p>' : '<p class="muted">수령 완료</p>'}
          <div class="muted">${o.lines.map(esc).join(' · ')} · ${won(o.total)}</div>
          ${o.status === 'wait' ? `<button class="btn ghost" data-act="ff" data-no="${esc(o.no)}">⏩ 데모: 순서 1칸 진행</button>` : ''}
          ${o.status === 'call' ? `<button class="btn pri" data-act="pickup" data-no="${esc(o.no)}">수령했어요</button>` : ''}</div>`;
      }).join('') : '<div class="card">아직 주문이 없어요.</div>'}
      <p class="foot-note">대기번호 호출은 웹 화면과 카카오 알림톡(모의)으로 알려요. 현장 주문은 부스에서 구두로 안내해요.</p>`;
  }
  K.myView = myView;

  document.addEventListener('click', (e) => {
    const el = e.target.closest('[data-act]'); if (!el) return; const a = el.dataset.act;
    if (a === 'ff') {
      const os = orders(); const o = os.find((x) => x.no === el.dataset.no); o.ahead = Math.max(0, o.ahead - 1);
      if (o.ahead === 0) { o.status = 'call'; toast(`🔔 ${o.no}번 호출! (카카오 알림톡 모의)`); } store.set('orders', os); render();
    } else if (a === 'pickup') {
      const os = orders(); os.find((x) => x.no === el.dataset.no).status = 'done'; store.set('orders', os); render();
    }
  });
})();
