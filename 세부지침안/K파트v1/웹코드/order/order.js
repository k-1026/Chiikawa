/* K09 주문·결제. 결제는 모의 — 실제 카카오페이는 K09.md */
(() => {
  const { S, esc, st, src, seg, store, toast, go, render } = window.H;
  const K = window.K;
  const B = window.BOOTHS;
  const { won, boothOf, auth, orders, waitingAt } = K;

  const cart = () => (store.get('cart', { b: null, q: {} }) || { b: null, q: {} });
  const cartCount = () => Object.values(cart().q).reduce((a, b) => a + b, 0);
  const cartTotal = () => { const c = cart(); const b = c.b && boothOf(c.b); return b ? b.menus.reduce((s, m) => s + (c.q[m.id] || 0) * m.price, 0) : 0; };

  function orderView(sub) {
    sub = sub || 'list';
    if (sub.startsWith('b-')) return boothView(boothOf(sub.slice(2)));
    if (sub === 'cart') return cartView();
    if (sub === 'my') return K.myView();
    const kind = sub === 'gu7' ? 'gu7' : 'ten';
    const list = B.filter((b) => b.kind === kind);
    return `<div class="page-title">주문</div>
      ${seg('order', [['list', '10미 포장마차'], ['gu7', '7구 맛집'], ['my', '내 주문']], kind === 'ten' && sub === 'list' ? 'list' : sub)}
      <div class="callout blue">현장 주문(구두)도 같은 줄에 서요 — 부스 POS 대기 순서가 그대로 보여요. 플리마켓·굿즈는 현장 결제만 해요.</div>
      ${list.map((b) => `<button class="card shortcut" style="text-align:left;width:100%" data-go="order:b-${b.id}">
        <b>${esc(b.name)}</b> <span class="badge ${waitingAt(b) > 3 ? 'hot' : ''}">대기 ${waitingAt(b)}팀 · 약 ${waitingAt(b) * 3}분</span>
        <span class="muted">${b.menus.map((m) => esc(m.name)).join(' · ')}</span></button>`).join('')}
      ${cartCount() ? `<button class="btn pri cartbar" style="width:100%" data-go="order:cart">🛒 장바구니 ${cartCount()}개 · ${won(cartTotal())}</button>` : ''}
      <p class="foot-note">부스·메뉴·가격은 예시예요(업소는 심사 후 확정). 메뉴는 표준어와 사투리를 함께 적어요. 사투리로 주문하지 않아도 똑같이 주문할 수 있어요.</p>`;
  }
  function boothView(b) {
    if (!b) return '<div class="card">부스를 찾을 수 없어요.</div>';
    const c = cart(); const q = c.b === b.id ? c.q : {};
    return `<div class="page-title">${esc(b.name)}</div>
      <div class="card"><span class="badge ${waitingAt(b) > 3 ? 'hot' : ''}">대기 ${waitingAt(b)}팀 · 약 ${waitingAt(b) * 3}분</span>
        <p class="muted" style="margin-top:6px">부스 단위로 주문해요. 다른 부스 메뉴를 담으면 장바구니가 바뀌어요.</p></div>
      <div class="card">${b.menus.map((m) => `<div class="qrow"><div><b>${esc(m.name)}</b><div class="price">${won(m.price)}</div></div>
        ${m.soldout ? '<span class="badge call">품절</span>' : `<div class="qty"><button data-act="qty" data-b="${b.id}" data-m="${m.id}" data-d="-1" aria-label="빼기">−</button><b>${q[m.id] || 0}</b><button data-act="qty" data-b="${b.id}" data-m="${m.id}" data-d="1" aria-label="담기">+</button></div>`}</div>`).join('')}</div>
      ${cartCount() ? `<button class="btn pri cartbar" style="width:100%" data-go="order:cart">🛒 장바구니 ${cartCount()}개 · ${won(cartTotal())}</button>` : ''}
      <button class="btn ghost" data-go="order">← 부스 목록</button>`;
  }
  function cartView() {
    const c = cart(); const b = c.b && boothOf(c.b);
    if (!b || !cartCount()) return `<div class="page-title">장바구니</div><div class="card">담긴 메뉴가 없어요.</div><button class="btn ghost" data-go="order">부스 보러 가기</button>`;
    const a = auth();
    const items = b.menus.filter((m) => c.q[m.id]);
    return `<div class="page-title">장바구니</div>
      <div class="card"><b>${esc(b.name)}</b>
        ${items.map((m) => `<div class="qrow"><span>${esc(m.name)} × ${c.q[m.id]}</span><span class="price">${won(m.price * c.q[m.id])}</span></div>`).join('')}
        <div class="qrow"><b>합계</b><b class="price">${won(cartTotal())}</b></div>
        <p class="muted">현재 대기 ${waitingAt(b)}팀 — 결제하면 대기번호가 나와요.</p></div>
      ${a.provider === 'kakao'
        ? `<button class="btn-kakao" data-act="pay">💛 카카오페이로 결제하기 (모의)</button>`
        : a.provider === 'guest' ? `<div class="callout red">온라인 주문은 카카오 로그인 후에 할 수 있어요. 로그인 없이는 부스에서 현장 주문(구두)해 주세요.</div><button class="btn-kakao" data-act="relogin">로그인하러 가기</button>`
        : `<div class="callout red">구글 계정은 온라인 구매를 할 수 없어요. 부스에서 현장 결제(구두 주문)해 주세요. 대기번호도 현장에서 안내해 드려요.</div>`}
      <button class="btn ghost" data-go="order:b-${b.id}" style="margin-top:8px">← 메뉴로</button>`;
  }
  Object.assign(window.VIEWS, { order: orderView, my: () => orderView('my') });

  document.addEventListener('click', (e) => {
    const el = e.target.closest('[data-act]'); if (!el) return; const a = el.dataset.act;
    if (a === 'qty') {
      const c = cart(); if (c.b !== el.dataset.b) { c.b = el.dataset.b; c.q = {}; }
      c.q[el.dataset.m] = Math.max(0, (c.q[el.dataset.m] || 0) + Number(el.dataset.d)); store.set('cart', c); render();
    } else if (a === 'pay') {
      const c = cart(); const b = boothOf(c.b); const os = orders();
      const lines = b.menus.filter((m) => c.q[m.id]).map((m) => `${m.name}×${c.q[m.id]}`);
      const no = (b.kind === 'ten' ? 'T' : 'G') + b.id.slice(1).padStart(2, '0') + '-' + String(os.length + 101);
      os.push({ no, boothId: b.id, lines, total: cartTotal(), ahead: waitingAt(b), status: 'wait', ts: Date.now() });
      store.set('orders', os); store.set('cart', { b: null, q: {} }); toast('결제 완료(모의) — 대기번호가 나왔어요'); go('order:my');
    }
  });
})();
