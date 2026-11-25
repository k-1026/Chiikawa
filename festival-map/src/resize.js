// 지도 상자(컨테이너)의 크기가 바뀌면 카카오 지도에 알려 줍니다.
// 실제 웹페이지에 넣었을 때 탭 전환·접기/펼치기·화면 회전 등으로 크기가 바뀌어도 지도가 깨지지 않게 합니다.
// 사용자가 보고 있던 중심 위치는 그대로 유지하고, 처음 표시 범위로 되돌리지는 않습니다.
export function watchMapResize(map, container) {
  let lastWidth = container.clientWidth;
  let lastHeight = container.clientHeight;
  let frame = 0;

  const observer = new ResizeObserver(() => {
    cancelAnimationFrame(frame);
    frame = requestAnimationFrame(() => {
      const { clientWidth: w, clientHeight: h } = container;
      if (w === lastWidth && h === lastHeight) return;
      lastWidth = w;
      lastHeight = h;

      const center = map.getCenter();
      map.relayout();
      map.setCenter(center);
    });
  });

  observer.observe(container);
  return () => observer.disconnect();
}
