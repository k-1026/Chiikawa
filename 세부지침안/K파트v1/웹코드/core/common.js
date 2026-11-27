/* 공용 도구: 기능 파일들이 함께 쓰는 K 네임스페이스. 기능 코드이므로 에이전트가 고치지 않는다 */
(() => {
  const { store } = window.H;
  const B = window.BOOTHS;
  window.K = {
    $view: document.getElementById('view'),
    $app: document.getElementById('app'),
    won: (n) => n.toLocaleString('ko-KR') + '원',
    auth: () => store.get('auth', null),
    boothOf: (id) => B.find((b) => b.id === id),
  };
})();
