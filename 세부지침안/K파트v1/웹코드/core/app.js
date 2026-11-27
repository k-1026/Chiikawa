(() => {
  const S = window.SITE;
  const $view = document.getElementById('view');
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const ST = { ok: ['확정', 'st-ok'], plan: ['예정', 'st-plan'], tbd: ['미정', 'st-tbd'] };
  const st = (k) => (k && ST[k] ? `<span class="st ${ST[k][1]}">${ST[k][0]}</span>` : '');
  const src = (s) => `<div class="src">출처: ${esc(s)}</div>`;

  // localStorage는 데모 편의용 (막혀 있어도 화면은 정상 동작)
  const store = {
    get(k, d) { try { const v = localStorage.getItem('dst:' + k); return v ? JSON.parse(v) : d; } catch { return d; } },
    set(k, v) { try { localStorage.setItem('dst:' + k, JSON.stringify(v)); } catch { /* 무시 */ } },
  };
  const toast = (msg) => {
    const t = document.getElementById('toast');
    t.textContent = msg; t.classList.add('show');
    clearTimeout(toast._t); toast._t = setTimeout(() => t.classList.remove('show'), 2200);
  };
  const seg = (name, items, cur) => `<div class="seg" role="tablist">${items.map(([k, l]) =>
    `<button role="tab" data-seg="${name}" data-k="${k}" aria-selected="${k === cur}">${l}</button>`).join('')}</div>`;

  /* ---------------- 홈 ---------------- */
  function home() {
    const f = S.festival;
    const [dk, om] = S.mascots;
    return `
      <section class="hero">
        <div class="hero-top">
          <span class="chip">${esc(f.fullName)} · ${esc(f.place)}</span>
          <h1>대구말 몰라도,<br><em>같이 놀자!</em></h1>
          <p class="lead">${esc(dk.role)} ${esc(dk.name)} & ${esc(om.role)} ${esc(om.name)}이<br>티격태격하다 친구가 되는 사흘.</p>
          <div class="date">${esc(f.dates)}</div>
          <div class="place">${esc(f.placeDetail)}</div>
        </div>
        <div class="duo">
          <figure><img src="${dk.img}" alt="${esc(dk.alt)}"><figcaption style="color:#0f6f93">${esc(dk.name)}</figcaption></figure>
          <span class="and">&</span>
          <figure><img src="${om.img}" alt="${esc(om.alt)}"><figcaption style="color:${om.color}">${esc(om.name)}</figcaption></figure>
        </div>
      </section>

      <div class="message">
        <div class="q">“${esc(f.message)}”</div>
        <div class="s">${esc(f.welcome)}</div>
      </div>

      ${window.homeBanner ? window.homeBanner() : ''}
      <div class="sec-h">⚡ 바로가기</div>
      <div class="grid2">
        ${S.shortcuts.map((s) => `<button class="shortcut" data-go="${s.go}"><span class="i">${s.icon}</span><b>${esc(s.title)}</b><span>${esc(s.desc)}</span></button>`).join('')}
      </div>

      <div class="sec-h">👋 대키미 & 외지몽</div>
      ${S.mascots.map((m) => `
        <div class="card mascot-card">
          <img src="${m.img}" alt="${esc(m.alt)}">
          <div>
            <div class="nm" style="color:${m.id === 'dk' ? '#0f6f93' : m.color}">${esc(m.name)}</div>
            <div class="kd muted">${esc(m.role)} · ${esc(m.kind)}</div>
            <div class="bubble">${esc(m.line)}</div>
          </div>
        </div>`).join('')}

      <div class="card">
        <h3>🕒 운영 시간</h3>
        <p>${esc(f.hours)}</p>
        <p class="muted" style="margin-top:6px">토론 대회는 <b>일요일</b> 하루에 본선·결승을 모두 해요.</p>
      </div>

      <p class="foot-note">웹을 쓰지 않아도 축제에 똑같이 참여할 수 있어요 (현장 결제·스탬프 북·구두 대기번호).<br>2027 세부 콘셉트·출전자·논제 등은 아직 미정이라 바뀔 수 있어요.<br>기준: ${esc(S.meta.basis)} · ${esc(S.meta.updated)}</p>`;
  }

  /* ---------------- 행사개요 ---------------- */
  function about(sub) {
    sub = sub || 'intro';
    const f = S.festival;
    let body = '';
    if (sub === 'intro') {
      body = `
        <div class="card">
          <table class="kv">
            <tr><th>행사명</th><td><b>${esc(f.name)}</b> (${esc(f.fullName)})</td></tr>
            <tr><th>기간</th><td>${esc(f.datesKo)}</td></tr>
            <tr><th>장소</th><td>${esc(f.placeDetail)}</td></tr>
            <tr><th>운영</th><td>${esc(f.hours)}</td></tr>
            <tr><th>콘셉트</th><td>${esc(f.concept)}</td></tr>
            <tr><th>2027</th><td>${esc(f.yearConcept.text)} ${st(f.yearConcept.status)}</td></tr>
          </table>
          ${src(f.src)}
        </div>
        <div class="message"><div class="q">“${esc(f.message)}”</div><div class="s">${esc(f.value)}</div></div>
        <div class="card">
          <h3>🎪 3대 프로그램</h3>
          ${S.programs.map((p) => `<p style="margin-top:6px">${p.icon} <b style="color:var(--ink)">${esc(p.title)}</b></p>`).join('')}
          <div style="margin-top:12px"><button class="btn ghost" data-go="about:prog">프로그램 자세히 보기 →</button> <button class="btn ghost" data-go="time:sun">🕒 시간표</button></div>
        </div>`;
    } else if (sub === 'prog') {
      body = `
        ${S.programs.map((p) => `
          <div class="card prog">
            <div class="pi">${p.icon}</div>
            <div><div class="part">${p.part}파트</div><h3>${esc(p.title)}</h3><p>${esc(p.desc)}</p>
              <div class="tags">${p.tags.map((t) => `<span class="tag">${esc(t)}</span>`).join('')}</div></div>
          </div>`).join('')}
        <div class="sec-h">🎭 메인무대 부대 콘텐츠</div>
        ${S.stageExtras.map((e) => `
          <div class="card prog">
            <div class="pi">${e.icon}</div>
            <div><h3>${esc(e.title)} ${st(e.status)}</h3><p class="muted" style="margin-bottom:4px">📅 ${esc(e.when)}</p><p>${esc(e.desc)}</p>
              <details class="more"><summary>더 보기</summary><p>${esc(e.more)}</p></details>${e.form && window.formBtn ? window.formBtn(e.form) : ''}</div>
          </div>`).join('')}
        <div class="callout blue">메인무대는 <b>1개</b>예요. 토론·골든벨·뮤지컬이 모두 코오롱 야외음악당에서 열려요.</div>`;
    } else if (sub === 'food') {
      body = `
        <div class="card">
          <h3>🥘 대구 10미 포장마차</h3>
          <p>대구 대표 음식 10가지를 한자리에서! 품목당 최소 2부스, 25~30부스.</p>
          <div class="chips" style="margin-top:12px">${S.tenFoods.map((x) => `<span class="food-chip">${esc(x)}</span>`).join('')}</div>
        </div>
        <div class="card">
          <h3>🍢 7구 맛집거리</h3>
          <p>구별 유명 음식점 60~70부스. 축제 뒤에도 그 동네로 다시 찾아가 보세요.</p>
          <div class="chips" style="margin-top:12px">${S.sevenGu.map((x) => `<span class="gu-chip">${esc(x)}</span>`).join('')}</div>
          <ul class="dots">${S.foodNotes.map((x) => `<li>${esc(x)}</li>`).join('')}</ul>
        </div>
        <div class="card">
          <h3>🏮 소상공인 플리마켓</h3>
          <p>대구 소상공인·로컬 브랜드 50~60부스. 판매와 체험 어느 한쪽도 70%를 넘지 않게 섞어요.</p>
          <ul class="dots">${S.fleaNotes.map((x) => `<li>${esc(x)}</li>`).join('')}</ul>
          ${src('B02·B04·C01·C02 / K06')}
        </div>
        <button class="btn ghost" data-go="map">🗺 지도에서 위치 보기</button>`;
    }
    return `<div class="page-title">행사개요</div>
      ${seg('about', [['intro', '축제 소개'], ['prog', '프로그램'], ['food', '먹거리·마켓']], sub)}
      <div class="fade-in">${body}</div>`;
  }

  /* ---------------- 시간표 ---------------- */
  function time(sub) {
    const day = S.schedule.find((d) => d.key === sub) || S.schedule[2];
    return `<div class="page-title">시간표</div>
      ${seg('time', S.schedule.map((d) => [d.key, d.label]), day.key)}
      <div class="card fade-in">
        <p class="muted" style="margin-bottom:10px">운영 ${day.open} ~ ${day.close}</p>
        <table class="tt">
          <thead><tr><th>시간</th><th>내용</th><th>장소</th></tr></thead>
          <tbody>${day.rows.map((r) => `<tr class="${/결승/.test(r.what) ? 'hl' : ''}"><td class="time">${esc(r.time)}</td><td>${esc(r.what)} ${r.status !== 'ok' ? st(r.status) : ''}</td><td class="where">${esc(r.where)}</td></tr>`).join('')}</tbody>
        </table>
        ${day.note ? `<div class="callout">☔ ${esc(day.note)}</div>` : ''}
        ${src('P0-4 · A06~A09 / K04')}
      </div>
      <p class="foot-note">먹거리·플리마켓은 개장과 함께 열고, 그날 폐막 시각에 닫아요.</p>`;
  }

  /* ---------------- 토론대회 ---------------- */
  function debate(sub) {
    sub = sub || 'intro';
    const D = S.debate;
    let body = '';
    if (sub === 'intro') {
      body = `
        <div class="card">
          <h3>🗣 대구 vs 타지역, 말로 한판!</h3>
          <p>진지한 찬반 토론이 아니라, “이 말이 더 귀엽다!” 같은 <b>이지선다 말싸움</b>이에요.</p>
          <table class="kv" style="margin-top:10px">${D.facts.map(([k, v]) => `<tr><th>${esc(k)}</th><td>${esc(v)}</td></tr>`).join('')}</table>
          ${src(D.src)}
        </div>
        <div class="card">
          <h3>📊 점수는 이렇게</h3>
          <div class="bar" style="margin-top:10px">${D.score.map((s) => `<div style="width:${s.value}%;background:${s.color};${s.label === '심사위원' ? 'color:#fff' : ''}">${esc(s.label)} ${s.value}</div>`).join('')}</div>
          <p style="margin-top:8px">+ <b>${esc(D.bonus)}</b></p>
          <ul class="dots">
            <li>채점: ${esc(D.judgeItems)}</li>
            <li>${esc(D.judges)}</li>
            <li>${esc(D.tie)}</li>
          </ul>
        </div>`;
    } else if (sub === 'bracket') {
      body = `
        <div class="legend"><span><i style="background:var(--dk)"></i>대구</span><span><i style="background:var(--om)"></i>타지역</span></div>
        <div class="card">
          <h3>본선 8강 · 일요일 ${st('plan')}</h3>
          <p class="muted" style="margin-bottom:12px">경기당 30분 · 메인무대</p>
          ${D.bracket.map(([a, b]) => `<div class="vsrow"><div class="pl dk">${esc(a)}</div><div class="vs">VS</div><div class="pl om">${esc(b)}</div></div>`).join('')}
        </div>
        <div class="card">
          <h3>4강 → 결승</h3>
          <div class="vsrow"><div class="pl dk">대구 1위</div><div class="vs">VS</div><div class="pl om">타지역 2위</div></div>
          <div class="vsrow"><div class="pl om">타지역 1위</div><div class="vs">VS</div><div class="pl dk">대구 2위</div></div>
          <div class="vsrow" style="grid-template-columns:1fr"><div class="pl" style="background:#fff1c2">🏆 결승 16:00–17:00 · 단판 + 시상</div></div>
          <div class="callout">${esc(D.bracketNote)}</div>
        </div>`;
    } else if (sub === 'topic') {
      const ex = D.topicExamples[0];
      body = `
        <div class="card">
          <h3>논제는 이런 모양이에요</h3>
          <p>${esc(D.topicForm)}</p>
          <div class="topic"><div class="w" style="color:#0f6f93">${esc(ex.a)}</div><div class="vs">VS</div><div class="w" style="color:var(--om)">${esc(ex.b)}</div></div>
          <p style="text-align:center;margin-top:8px"><b>${esc(ex.q)}</b></p>
          <p class="muted" style="text-align:center">※ 예시예요. 실제 확정 논제가 아니에요.</p>
        </div>
        <div class="card">
          <h3>📮 논제 공개 · 추천</h3>
          <ul class="dots">${D.topicRules.map((x) => `<li>${esc(x)}</li>`).join('')}</ul>
          <div class="callout red">이 웹사이트에는 논제 추천 칸이 없어요. 메인구역 입구 쪽지함을 이용해 주세요!</div>
        </div>
        <div class="card">
          <h3>🚫 이런 논제는 안 돼요</h3>
          <ul class="dots banned">${D.banned.map((x) => `<li>${esc(x)}</li>`).join('')}</ul>
          ${src(D.src)}
        </div>`;
    } else if (sub === 'vote') {
      body = window.voteView2();
    }
    return `<div class="page-title">토론 대회</div>
      ${seg('debate', [['intro', '대회 소개'], ['bracket', '대진표'], ['topic', '논제'], ['vote', '관객 투표']], sub)}
      <div class="fade-in">${body}</div>`;
  }

  // 관객 투표 데모 — 로그인(데모) 후 경기마다 1인 1표. 개인정보는 받지 않음.
  const SEED = [[132, 118], [97, 141], [120, 120], [88, 103]];
  function voteView() {
    const user = store.get('user', null);
    if (!user) {
      return `
        <div class="card">
          <h3>🔐 로그인 후 투표할 수 있어요 <span class="st st-plan">데모</span></h3>
          <p>관객 투표는 <b>1인 1계정, 경기마다 1표</b>예요. 관객 점수는 최종 점수의 40%를 차지해요.</p>
          <label class="fld" for="nick">닉네임 (데모용 — 실제 가입·저장 없음)</label>
          <input type="text" id="nick" maxlength="12" placeholder="예: 대구초보">
          <div style="margin-top:12px"><button class="btn pri" data-act="login">데모 로그인</button></div>
          <p class="muted" style="margin-top:10px">실제 서비스에서는 회원가입·동의 절차가 들어가요(K파트 소관). 휴대폰이 없으면 투표할 수 없어요.</p>
        </div>
        <div class="callout">투표해도 스탬프는 적립되지 않아요.</div>`;
    }
    const votes = store.get('votes', {});
    return `
      <div class="card">
        <div class="row" style="justify-content:space-between;align-items:center">
          <div><b>${esc(user)}</b>님, 반가워요! <span class="st st-plan">데모</span></div>
          <button class="tag" style="border:0" data-act="logout">로그아웃</button>
        </div>
        <p class="muted" style="margin-top:6px">경기마다 한 번만 투표할 수 있어요. 결과는 예시 데이터에 내 표를 더한 값이에요.</p>
      </div>
      ${S.debate.bracket.map(([a, b], i) => {
        const v = votes[i];
        const [x, y] = SEED[i].map((n, j) => n + (v === j ? 1 : 0));
        const pa = Math.round((x / (x + y)) * 100);
        return `<div class="vote-match">
          <div class="lbl">8강 ${i + 1}경기</div>
          <div class="vote-opts">
            <button class="dk" data-act="vote" data-m="${i}" data-c="0" aria-pressed="${v === 0}" ${v !== undefined ? 'disabled' : ''}>${esc(a)}</button>
            <button class="om" data-act="vote" data-m="${i}" data-c="1" aria-pressed="${v === 1}" ${v !== undefined ? 'disabled' : ''}>${esc(b)}</button>
          </div>
          ${v !== undefined ? `<div class="res"><div class="bar"><div style="width:${pa}%;background:var(--dk)">${pa}%</div><div style="width:${100 - pa}%;background:#7fd3a0">${100 - pa}%</div></div></div>` : ''}
        </div>`;
      }).join('')}
      <div class="callout">투표해도 스탬프는 적립되지 않아요.</div>`;
  }

  /* ---------------- 지도 ---------------- */
  function map(sub) {
    const z = S.zones.find((x) => x.id === sub) || S.zones.find((x) => x.id === 'main');
    return `<div class="page-title">축제장 지도</div>
      <div class="map-wrap">
        <img src="assets/map_full.png" alt="두류공원 지도 — 코오롱 야외음악당, 두류도서관, 2.28기념탑, 2.28 자유광장 일대. 축제 구역은 지도 위 아이콘으로 표시">
        ${S.zones.map((x) => `<button class="pin ${x.id === z.id ? 'on' : ''}" style="left:${x.x}%;top:${x.y}%;--c:${x.color}" data-seg="map" data-k="${x.id}" aria-label="${esc(x.name)}">${x.icon}</button>`).join('')}
      </div>
      <div class="zone-list">${S.zones.map((x) => `<button style="--c:${x.color}" data-seg="map" data-k="${x.id}" aria-pressed="${x.id === z.id}">${x.icon} ${esc(x.name)}</button>`).join('')}</div>
      <div class="card zone-info fade-in" style="--c:${z.color}">
        <h3><span class="dot"></span>${esc(z.name)}</h3>
        <p>${esc(z.desc)}</p>
      </div>
      <p class="foot-note">${esc(S.mapNote)}</p>`;
  }

  /* ---------------- 혜택 (스탬프·숙박) ---------------- */
  function benefit(sub) {
    return `<div class="page-title">숙박 혜택</div>
      <div class="fade-in">${stayView()}</div>`;
  }

  function stampView() {
    const T = S.stamp;
    return `
      <div class="card">
        <h3>📒 스탬프 북은 현장에서 받아요</h3>
        <p>운영·안전 부스에서 종이 스탬프 북을 나눠 드려요. ${T.slots}칸 중 <b>${T.goal}개 이상</b> 모으면 완성!</p>
      </div>
      <div class="card">
        <h3>🖐 도장 받는 곳</h3>
        ${T.groups.map((g) => `<div class="grp" style="margin-top:12px"><div class="gi">${g.icon}</div><div><b>${esc(g.title)}</b><div class="muted">${esc(g.rule)}</div></div></div>`).join('')}
        <div class="callout red">🎤 ${esc(T.noStamp)}</div>
      </div>
      <div class="card">
        <h3>🎁 완성하면</h3>
        ${T.rewards.map((r) => `<div class="grp" style="margin-top:12px"><div class="gi">${r.icon}</div><div><b>${esc(r.title)}</b><div class="muted">${esc(r.desc)}</div></div></div>`).join('')}
        <div class="callout blue">📍 ${esc(T.where)}<br>${esc(T.offlineOnly)}</div>
        ${src(T.src)}
      </div>`;
  }

  // 숙박 인증 데모: 신청 → 1박 → 인증 → 보상. 파일·개인정보는 저장하지 않음.
  function stayView() {
    const Y = S.stay;
    const step = store.get('stayStep', 0);
    const stepsHtml = `<ol class="steps">${Y.steps.map((s, i) => `<li class="${i < step ? 'past' : i === step ? 'cur' : ''}"><b>${esc(s.t)}</b><span>${esc(s.d)}</span></li>`).join('')}</ol>`;
    let panel = '';
    if (step === 0) {
      panel = `
        <label class="fld" for="region">사는 곳 (주소지 기준)</label>
        <select id="region">
          <option value="">선택해 주세요</option>
          <option value="out">대구 밖 (서울, 부산, 경북 …)</option>
          <option value="dg">대구</option>
        </select>
        <label class="chk"><input type="checkbox" id="agree"> 데모 화면이라 실제로 신청되지 않는다는 것을 알아요.</label>
        <div style="margin-top:12px"><button class="btn pri" data-act="stay-apply">사전 신청하기 (데모)</button></div>`;
    } else if (step === 1) {
      panel = `<div class="callout blue">✅ 사전 신청 완료(데모). 축제 기간에 대구 숙소 아무 곳에서나 1박 해 주세요.</div>
        <div style="margin-top:12px"><button class="btn pri" data-act="stay-next">1박 했어요 → 인증하러 가기</button></div>`;
    } else if (step === 2) {
      panel = `<label class="fld" for="proof">영수증 또는 예약 확인 화면 (데모 — 파일은 저장하지 않아요)</label>
        <input type="file" id="proof" accept="image/*">
        <p class="muted" style="margin-top:6px">결제 정보는 가리고 올려 주세요. 현장에서 주소지도 함께 확인해요.</p>
        <div style="margin-top:12px"><button class="btn pri" data-act="stay-proof">인증 제출 (데모)</button></div>`;
    } else {
      panel = `<div class="callout blue">🎉 인증 완료(데모)! 아래 장소에서 대구로페이 보상을 받아 가세요.</div>
        <ul class="dots">${Y.pickup.map((p) => `<li>📍 ${esc(p)}</li>`).join('')}</ul>
        <div style="margin-top:12px"><button class="btn ghost" data-act="stay-reset">데모 처음부터</button></div>`;
    }
    return `
      <div class="card">
        <h3>🏨 대구에서 하룻밤 묵고 가면 혜택!</h3>
        <p>대상: <b>${esc(Y.who)}</b></p>
        <table class="kv" style="margin-top:8px">
          <tr><th>보상</th><td>${esc(Y.reward.text)} ${st(Y.reward.status)}</td></tr>
          <tr><th>인원</th><td>${esc(Y.limit.text)} ${st(Y.limit.status)}</td></tr>
          <tr><th>받는 곳</th><td>${Y.pickup.map(esc).join(' · ')}</td></tr>
        </table>
      </div>
      <div class="card">${stepsHtml}${panel}</div>
      <p class="foot-note">${esc(Y.note)}<br>숙박 인증 보상은 아직 초안 단계라 금액·인원이 바뀔 수 있어요.</p>
      ${src(Y.src)}`;
  }

  /* ---------------- 라우팅 ---------------- */
  const VIEWS = window.VIEWS = { home, about, time, debate, map, benefit };
  window.H = { S, esc, st, src, seg, store, toast, go: (t, k) => go(t, k), render: () => render() };
  const TABOF = { time: 'about', debate: 'more', benefit: 'more', my: 'more', survey: 'home' };
  function render() {
    if (window.GATE && window.GATE()) return;
    const [tab, sub] = (location.hash.slice(1) || 'home').split(':');
    const fn = VIEWS[tab] || home;
    $view.innerHTML = fn(sub);
    document.querySelectorAll('.tabbar button').forEach((b) => {
      if (b.dataset.go === (VIEWS[tab] ? (TABOF[tab] || tab) : 'home')) b.setAttribute('aria-current', 'page'); else b.removeAttribute('aria-current');
    });
  }
  function go(target, keepScroll) {
    const h = '#' + target;
    if (location.hash !== h) history.pushState(null, '', h);
    render();
    if (!keepScroll) window.scrollTo({ top: 0 });
  }
  window.addEventListener('popstate', render);

  document.addEventListener('click', (e) => {
    const el = e.target.closest('[data-go],[data-seg],[data-act]');
    if (!el) return;
    if (el.dataset.go) return go(el.dataset.go);
    if (el.dataset.seg) return go(`${el.dataset.seg}:${el.dataset.k}`, true);
    const a = el.dataset.act;
    if (a === 'login') {
      const nick = document.getElementById('nick').value.trim();
      if (!nick) return toast('닉네임을 넣어 주세요 (데모)');
      store.set('user', nick); render(); toast('데모 로그인 완료!');
    } else if (a === 'logout') {
      store.set('user', null); store.set('votes', {}); render();
    } else if (a === 'vote') {
      const votes = store.get('votes', {});
      if (votes[el.dataset.m] !== undefined) return;
      votes[el.dataset.m] = Number(el.dataset.c); store.set('votes', votes); render(); toast('투표했어요! (데모)');
    } else if (a === 'stay-apply') {
      const r = document.getElementById('region').value;
      if (!r) return toast('사는 곳을 골라 주세요');
      if (r !== 'out') return toast('대구 밖에 사는 분만 받을 수 있어요');
      if (!document.getElementById('agree').checked) return toast('데모 안내에 체크해 주세요');
      store.set('stayStep', 1); render();
    } else if (a === 'stay-next') {
      store.set('stayStep', 2); render();
    } else if (a === 'stay-proof') {
      const f = document.getElementById('proof');
      if (!f.files.length) return toast('사진을 골라 주세요 (저장되지 않아요)');
      f.value = ''; store.set('stayStep', 3); render();
    } else if (a === 'stay-reset') {
      store.set('stayStep', 0); render();
    }
  });

  render();
})();
