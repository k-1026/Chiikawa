// 지도 위에 올리는 마커·구역(폴리곤)을 담당합니다.
// 모두 실제 위도·경도 좌표로 그리기 때문에, 처음 화면 위치나 확대 수준을 바꿔도 제자리에 그대로 있습니다.

import { BARRICADE_TYPE } from './config.js';
import { drawFacilityMarker } from './markers/markerLayer.js';

export function drawMarkers(map, markers) {
  const { kakao } = window;
  return markers.map((place) => {
    const position = new kakao.maps.LatLng(place.lat, place.lng);
    const marker = new kakao.maps.Marker({ map, position, title: place.name });
    const info = new kakao.maps.InfoWindow({
      content: `<div style="padding:6px 10px;font-size:13px;">${place.name}</div>`,
    });
    kakao.maps.event.addListener(marker, 'click', () => info.open(map, marker));
    return marker;
  });
}

// 구역(도형) 하나를 보기 전용 도형으로 그립니다. onClick이 있으면 클릭 시 호출합니다.
// 종류(type)에 맞는 카카오 기본 도형(Polygon, Polyline, Circle, Rectangle, Ellipse)을 씁니다.
export function drawZone(map, zone, onClick) {
  const { kakao } = window;
  const ll = (p) => new kakao.maps.LatLng(p.lat, p.lng);
  const s = zone.style;
  const stroke = {
    map,
    strokeColor: s.strokeColor,
    strokeWeight: s.strokeWeight,
    strokeOpacity: s.strokeOpacity === undefined ? 1 : s.strokeOpacity,
  };
  const fill = { fillColor: s.fillColor, fillOpacity: s.fillOpacity };

  let shape;
  switch (zone.type || 'polygon') {
    case 'polyline':
    case 'arrow': {
      // 선은 가늘어서 누르기 어렵기 때문에, 보이지 않는 굵은 선을 겹쳐 눌리는 범위를 넓힙니다.
      const path = zone.path.map(ll);
      const line = new kakao.maps.Polyline({ ...stroke, path, endArrow: zone.type === 'arrow' });
      const hitArea = new kakao.maps.Polyline({
        map,
        path,
        strokeWeight: Math.max(18, s.strokeWeight + 12),
        strokeColor: '#000000',
        strokeOpacity: 0.01,
      });
      if (onClick) {
        kakao.maps.event.addListener(line, 'click', (e) => onClick(zone, e));
        kakao.maps.event.addListener(hitArea, 'click', (e) => onClick(zone, e));
      }
      // 두 선을 한 도형처럼 다룰 수 있게 setMap 하나로 묶습니다.
      return {
        setMap(m) {
          line.setMap(m);
          hitArea.setMap(m);
        },
      };
    }
    case 'circle':
      shape = new kakao.maps.Circle({ ...stroke, ...fill, center: ll(zone.center), radius: zone.radius });
      break;
    case 'rectangle':
      shape = new kakao.maps.Rectangle({
        ...stroke,
        ...fill,
        bounds: new kakao.maps.LatLngBounds(ll(zone.bounds.sw), ll(zone.bounds.ne)),
      });
      break;
    case 'ellipse':
      shape = new kakao.maps.Ellipse({ ...stroke, ...fill, center: ll(zone.center), rx: zone.rx, ry: zone.ry });
      break;
    default:
      shape = new kakao.maps.Polygon({ ...stroke, ...fill, path: zone.path.map(ll) });
  }
  if (onClick) kakao.maps.event.addListener(shape, 'click', (e) => onClick(zone, e));

  // 이전 저장본의 바리게이트는 사각형으로 저장되어 있어 중심에 아이콘을 함께 표시합니다.
  if (zone.type === 'rectangle' && zone.name === BARRICADE_TYPE.label) {
    const { sw, ne } = zone.bounds;
    const center = { lat: (sw.lat + ne.lat) / 2, lng: (sw.lng + ne.lng) / 2 };
    const icon = drawFacilityMarker(map, { ...center, name: zone.name }, BARRICADE_TYPE.icon, {
      onClick: onClick && (() => onClick(zone, { latLng: ll(center) })),
    });
    return {
      setMap(nextMap) {
        shape.setMap(nextMap);
        icon.setMap(nextMap);
      },
    };
  }
  return shape;
}

export function drawZones(map, zones, onClick) {
  return zones.map((zone) => drawZone(map, zone, onClick));
}

export function removeOverlays(overlays) {
  overlays.forEach((o) => o.setMap(null));
}
