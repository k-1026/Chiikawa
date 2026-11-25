// 시설 마커 한 개를 아이콘 이미지와 함께 지도에 그립니다. 관리자·방문객 화면이 함께 씁니다.
// 아이콘 파일을 못 찾으면 회색 물음표 핀으로 바꿔 보여 줍니다(마커가 사라지지 않게).
import { iconUrl, FALLBACK_ICON_SRC } from './markerData.js';

const imageStatus = new Map(); // 주소 → Promise<boolean> (파일을 불러올 수 있는지)

export function checkImage(url) {
  if (!imageStatus.has(url)) {
    imageStatus.set(
      url,
      new Promise((resolve) => {
        const img = new Image();
        img.onload = () => resolve(true);
        img.onerror = () => resolve(false);
        img.src = url;
      })
    );
  }
  return imageStatus.get(url);
}

// 새 파일을 넣은 뒤 다시 확인할 수 있게 기록을 지웁니다.
export function forgetImageChecks() {
  imageStatus.clear();
}

function markerImage(icon, url) {
  const { kakao } = window;
  const size = new kakao.maps.Size(icon.width, icon.height);
  // offset: 이미지 안에서 실제 좌표에 닿는 점(기준점). anchorX·anchorY는 0~1 비율입니다.
  const offset = new kakao.maps.Point(Math.round(icon.width * icon.anchorX), Math.round(icon.height * icon.anchorY));
  return new kakao.maps.MarkerImage(url, size, { offset });
}

// options: { draggable, zIndex, onClick(marker, mouseEvent), onDragEnd({lat,lng}) }
export function drawFacilityMarker(map, marker, icon, options = {}) {
  const { kakao } = window;
  const url = iconUrl(icon.src);
  const kMarker = new kakao.maps.Marker({
    map,
    position: new kakao.maps.LatLng(marker.lat, marker.lng),
    image: markerImage(icon, url),
    title: marker.name,
    draggable: Boolean(options.draggable),
    zIndex: options.zIndex || 1,
    clickable: true,
  });

  checkImage(url).then((ok) => {
    if (!ok) kMarker.setImage(markerImage({ ...icon, width: 36, height: 46, anchorX: 0.5, anchorY: 1 }, FALLBACK_ICON_SRC));
  });

  if (options.onClick) {
    kakao.maps.event.addListener(kMarker, 'click', (e) => options.onClick(marker, e));
  }
  if (options.onDragEnd) {
    kakao.maps.event.addListener(kMarker, 'dragend', () => {
      const p = kMarker.getPosition();
      options.onDragEnd({ lat: p.getLat(), lng: p.getLng() });
    });
  }
  return kMarker;
}
