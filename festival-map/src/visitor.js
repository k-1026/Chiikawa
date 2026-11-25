// 방문객 화면: 구역 대표 아이콘과 시설 마커를 보여 주고, 누르면 이름을 띄웁니다.
// 편집 기능은 없습니다. 지도 드래그·확대·축소는 그대로 됩니다.
import { drawZones, removeOverlays } from './layers.js';
import { drawFacilityMarker } from './markers/markerLayer.js';
import { iconForMarker, iconUrl, typeLabel } from './markers/markerData.js';
import { ZONE_LOGOS } from './config.js';
import { isArea, zoneNumbers, zonePosition } from './zones/zonePosition.js';

// [구역] 보기에서 구역 로고와 함께 보여 줄 시설 유형(무대, 출입로)
const ZONE_VIEW_TYPES = ['stage', 'gate'];

// 직접 옮긴 위치(labelPos)를 뺀 자동 기본 위치
const autoZonePosition = (zone) => zonePosition({ ...zone, labelPos: undefined });

// 점이 구역 안에 있는지 (자동 배치가 구역 밖으로 나가지 않게)
function insideZone(zone, lat, lng) {
  const mPerLat = 111320;
  const mPerLng = 111320 * Math.cos((lat * Math.PI) / 180);
  if (zone.type === 'circle') {
    return Math.hypot((lat - zone.center.lat) * mPerLat, (lng - zone.center.lng) * mPerLng) <= zone.radius;
  }
  if (zone.type === 'ellipse') {
    const dx = ((lng - zone.center.lng) * mPerLng) / zone.rx;
    const dy = ((lat - zone.center.lat) * mPerLat) / zone.ry;
    return dx * dx + dy * dy <= 1;
  }
  if (zone.type === 'rectangle') {
    const { sw, ne } = zone.bounds;
    return lat >= sw.lat && lat <= ne.lat && lng >= sw.lng && lng <= ne.lng;
  }
  if (!zone.path) return true;
  let inside = false;
  const path = zone.path;
  for (let i = 0, j = path.length - 1; i < path.length; j = i++) {
    const a = path[i];
    const b = path[j];
    if ((a.lat > lat) !== (b.lat > lat) && lng < ((b.lng - a.lng) * (lat - a.lat)) / (b.lat - a.lat) + a.lng) inside = !inside;
  }
  return inside;
}

// data: { zones, markers, facilityTypes }
// options.onMoveZonePin(zone, {lat, lng}): 있으면 구역 로고·번호를 끌어서 옮길 수 있습니다(관리자 미리보기 전용).
export function startVisitorView(map, data, options = {}) {
  const { kakao } = window;
  const zones = data.zones || [];
  const markers = data.markers || [];
  const types = data.facilityTypes || [];
  let label = null;
  let justOpened = false;

  const closeLabel = () => {
    if (label) label.setMap(null);
    label = null;
  };

  // 이름표를 띄웁니다. liftPx만큼 위로 올려(아이콘 위쪽에) 표시합니다.
  function openLabel(text, position, sub, liftPx = 10) {
    closeLabel();
    const el = document.createElement('div');
    el.className = 'zone-label';
    el.textContent = text; // 이름은 글자로만 넣어 HTML로 해석되지 않게 합니다.
    if (sub) {
      const small = document.createElement('small');
      small.textContent = sub;
      el.append(small);
    }
    const wrap = document.createElement('div');
    wrap.style.paddingBottom = `${liftPx}px`;
    wrap.append(el);
    label = new kakao.maps.CustomOverlay({ map, position, content: wrap, xAnchor: 0.5, yAnchor: 1, zIndex: 30 });
    justOpened = true;
    setTimeout(() => {
      justOpened = false;
    }, 0);
  }

  const shapes = drawZones(map, zones.filter((zone) => !isArea(zone)), (zone, event) => {
    openLabel(zone.name, event.latLng);
  });
  const numbers = zoneNumbers(zones);
  const zoneRecords = []; // 자동 배치용: { zone, overlay, badge, home, manual }
  const zonePins = zones.filter(isArea).flatMap((zone) => {
    const point = zonePosition(zone);
    // The saved stage marker already represents the main stage inside its circle.
    if (zone.name === '메인무대' && zone.type === 'circle' && markers.some((marker) => {
      return marker.type === 'stage' &&
        Math.hypot((marker.lat - point.lat) * 111320, (marker.lng - point.lng) * 90200) <= zone.radius;
    })) return [];

    const position = new kakao.maps.LatLng(point.lat, point.lng);
    const badge = document.createElement('button');
    badge.type = 'button';
    badge.className = 'zone-pin';
    badge.style.setProperty('--zone-color', zone.style.strokeColor);
    badge.setAttribute('aria-label', zone.name);
    const logo = ZONE_LOGOS[zone.name];
    let lift = 23;
    if (logo) {
      // 로고가 있는 구역은 번호 대신 로고 그림을 보여 줍니다. 그림을 못 불러오면 번호로 돌아갑니다.
      const img = document.createElement('img');
      img.src = iconUrl(logo.src);
      img.alt = zone.name;
      img.style.width = `${logo.width}px`;
      img.addEventListener('error', () => {
        badge.className = 'zone-pin';
        badge.textContent = numbers.get(zone.name);
      });
      badge.className = 'zone-logo';
      badge.append(img);
      lift = Math.round(logo.width * 0.2) + 6;
    } else {
      badge.textContent = numbers.get(zone.name);
    }
    // 구역 아이콘은 시설 아이콘(zIndex 5)보다 항상 위에 보이게 합니다.
    const overlay = new kakao.maps.CustomOverlay({ map, position, content: badge, clickable: true, zIndex: 20 });
    const record = { zone, overlay, badge, home: autoZonePosition(zone), manual: Boolean(zone.labelPos) };
    zoneRecords.push(record);
    let dragged = false;
    badge.addEventListener('click', () => {
      if (dragged) return;
      // 이름표는 그림 위쪽에 띄웁니다(그림 실제 높이 기준).
      openLabel(zone.name, overlay.getPosition(), null, logo ? Math.round(badge.offsetHeight / 2) + 6 : lift);
    });
    if (options.onMoveZonePin) makeDraggable(badge, overlay, zone);
    return [overlay];

    // 관리자 미리보기에서만: 로고·번호를 끌어서 옮기면 그 위치를 구역에 저장합니다.
    function makeDraggable(el, ov, z) {
      el.classList.add('is-draggable');
      el.addEventListener('dragstart', (e) => e.preventDefault());
      el.addEventListener('pointerdown', (e) => {
        if (e.button !== 0) return;
        e.preventDefault();
        e.stopPropagation();
        dragged = false;
        const proj = map.getProjection();
        const start = proj.containerPointFromCoords(ov.getPosition());
        const sx = e.clientX;
        const sy = e.clientY;
        map.setDraggable(false);
        el.setPointerCapture(e.pointerId);
        const move = (ev) => {
          const dx = ev.clientX - sx;
          const dy = ev.clientY - sy;
          if (!dragged && Math.hypot(dx, dy) < 4) return;
          dragged = true;
          closeLabel();
          ov.setPosition(proj.coordsFromContainerPoint(new kakao.maps.Point(start.x + dx, start.y + dy)));
        };
        const up = () => {
          el.removeEventListener('pointermove', move);
          el.removeEventListener('pointerup', up);
          el.removeEventListener('pointercancel', up);
          map.setDraggable(true);
          if (dragged) {
            const p = ov.getPosition();
            record.manual = true; // 직접 옮긴 위치는 자동 배치가 건드리지 않습니다.
            options.onMoveZonePin(z, { lat: p.getLat(), lng: p.getLng() });
            // 끌기 직후의 클릭으로 이름표가 뜨지 않게 잠깐 막습니다.
            setTimeout(() => {
              dragged = false;
            }, 0);
          }
        };
        el.addEventListener('pointermove', move);
        el.addEventListener('pointerup', up);
        el.addEventListener('pointercancel', up);
      });
    }
  });

  const pinIcons = markers.map((m) => iconForMarker(m, types));
  const pins = markers.map((m, i) => {
    const icon = pinIcons[i];
    return drawFacilityMarker(map, m, icon, {
      zIndex: 5,
      onClick: () => {
        // 이름표를 아이콘 위쪽(기준점에서 아이콘 윗부분 높이만큼 위)에 띄웁니다.
        const position = new kakao.maps.LatLng(m.lat, m.lng);
        const stageName = { '무대 1': '사투리한마당 무대', '무대 2': '메인무대 생중계 화면' };
        openLabel(m.type === 'stage' ? stageName[m.name] || m.name : m.name,
          position, typeLabel(types, m.type), Math.round(icon.height * icon.anchorY) + 6);
      },
    });
  });

  // ── 보기 버튼: 구역 / 시설 유형별로 골라 보기
  // 처음엔 구역만 보입니다. [시설 전체]는 구역을 빼고 모든 시설, 시설 버튼은 그 시설만 보여 줍니다.
  const groups = new Map(); // id → { label, iconSrc, overlays }
  groups.set('zones', { label: '구역', iconSrc: null, overlays: [...shapes, ...zonePins] });
  types.forEach((t) => {
    const overlays = pins.filter((_, i) => markers[i].type === t.id);
    if (overlays.length) groups.set(t.id, { label: t.label, iconSrc: t.icon && t.icon.src, overlays });
  });
  // 유형 목록에 없는 마커도 빠지지 않게 '기타'로 묶습니다.
  const others = pins.filter((_, i) => !types.some((t) => t.id === markers[i].type));
  if (others.length) groups.set('others', { label: '기타', iconSrc: null, overlays: others });

  // 처음엔 구역만 보입니다. 'zones' = 구역만, 'facilities' = 시설 전체(구역 제외), 그 밖 = 그 시설 유형만
  let selected = 'zones';
  const frame = document.getElementById('map').parentElement;
  const bar = document.createElement('div');
  bar.className = 'map-filter';
  bar.setAttribute('role', 'group');
  bar.setAttribute('aria-label', '지도에 보일 항목 고르기');

  const chip = (id, text, iconSrc) => {
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'filter-chip';
    b.dataset.id = id;
    if (iconSrc) {
      const img = document.createElement('img');
      img.src = iconUrl(iconSrc);
      img.alt = '';
      img.addEventListener('error', () => img.remove());
      b.append(img);
    }
    b.append(document.createTextNode(text));
    b.addEventListener('click', () => toggle(id));
    bar.append(b);
    return b;
  };
  const chips = [chip('zones', '구역'), chip('facilities', '시설 전체')];
  // 시설 버튼 순서. 목록에 없는 유형은 맨 뒤에 붙습니다.
  const order = ['toilet', 'shelter', 'medical', 'emergency', 'nursing', 'gate', 'stage', 'lost'];
  // 버튼을 만들지 않는 유형 ([시설 전체]에서는 보입니다)
  const noChip = ['barricade'];
  // 버튼에만 짧게 보일 이름 (시설 유형 이름 자체는 그대로)
  const rank = (id) => (order.includes(id) ? order.indexOf(id) : order.length);
  [...groups.keys()]
    .filter((id) => id !== 'zones' && !noChip.includes(id))
    .sort((a, b) => rank(a) - rank(b))
    .forEach((id) => chips.push(chip(id, groups.get(id).label, groups.get(id).iconSrc)));

  function toggle(id) {
    // 한 번에 하나만 켜집니다. 이미 켜진 버튼을 다시 누르면 처음(구역만)으로 돌아갑니다.
    selected = selected === id ? 'zones' : id;
    applyFilter();
  }

  function applyFilter() {
    closeLabel();
    groups.forEach((g, id) => {
      // [구역] 화면에는 구역 로고와 함께 무대·출입로 아이콘도 보여 줍니다.
      const show = selected === 'facilities' ? id !== 'zones'
        : selected === 'zones' ? id === 'zones' || ZONE_VIEW_TYPES.includes(id)
        : selected === id;
      g.overlays.forEach((o) => o.setMap(show ? map : null));
    });
    chips.forEach((c) => c.setAttribute('aria-pressed', String(c.dataset.id === selected)));
    layoutZonePins();
  }

  // ── 구역 아이콘 자동 배치
  // 구역 안에서 기본 위치 가까운 곳 중, 보이는 시설 아이콘·다른 구역 아이콘과 가장 덜 겹치는 자리를 고릅니다.
  // 확대·축소할 때마다 다시 계산합니다. 관리자 미리보기에서 직접 옮긴 위치는 그대로 둡니다.
  function layoutZonePins() {
    const proj = map.getProjection();
    const toPx = (lat, lng) => proj.containerPointFromCoords(new kakao.maps.LatLng(lat, lng));
    const occupied = [];
    pins.forEach((pin, i) => {
      if (!pin.getMap()) return;
      const icon = pinIcons[i];
      const p = toPx(markers[i].lat, markers[i].lng);
      const left = p.x - icon.width * icon.anchorX;
      const top = p.y - icon.height * icon.anchorY;
      occupied.push({ left, top, right: left + icon.width, bottom: top + icon.height });
    });
    const boxAt = (x, y, w, h) => ({ left: x - w / 2, top: y - h / 2, right: x + w / 2, bottom: y + h / 2 });
    const overlapArea = (a) => occupied.reduce((sum, b) => {
      const w = Math.min(a.right, b.right) - Math.max(a.left, b.left) + 4;
      const h = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top) + 4;
      return w > 0 && h > 0 ? sum + w * h : sum;
    }, 0);

    // 직접 옮긴 아이콘을 먼저 자리 잡게 합니다.
    const ordered = [...zoneRecords].sort((a, b) => Number(b.manual) - Number(a.manual));
    ordered.forEach((rec) => {
      if (!rec.overlay.getMap()) return;
      const w = rec.badge.offsetWidth || 40;
      const h = rec.badge.offsetHeight || 40;
      if (rec.manual) {
        const p = proj.containerPointFromCoords(rec.overlay.getPosition());
        occupied.push(boxAt(p.x, p.y, w, h));
        return;
      }
      const home = toPx(rec.home.lat, rec.home.lng);
      let best = null;
      for (const r of [0, 14, 28, 42, 56, 72, 90, 110, 130]) {
        const steps = r ? 16 : 1;
        for (let k = 0; k < steps; k++) {
          const a = (k / steps) * Math.PI * 2 - Math.PI / 2;
          const x = home.x + Math.cos(a) * r;
          const y = home.y + Math.sin(a) * r;
          const ll = proj.coordsFromContainerPoint(new kakao.maps.Point(x, y));
          if (r && !insideZone(rec.zone, ll.getLat(), ll.getLng())) continue;
          const score = overlapArea(boxAt(x, y, w, h)) * 10 + r;
          if (!best || score < best.score) best = { score, r, x, y, ll };
        }
        if (best && best.score === best.r) break; // 안 겹치는 자리를 찾았으면 더 멀리 가지 않습니다.
      }
      rec.overlay.setPosition(best.ll);
      occupied.push(boxAt(best.x, best.y, w, h));
    });
  }

  if (groups.size > 1) frame.append(bar);
  applyFilter();
  // 그림(로고) 크기가 정해진 뒤와 확대·축소 때마다 다시 배치합니다.
  setTimeout(layoutZonePins, 0);
  zoneRecords.forEach((rec) => {
    const img = rec.badge.querySelector('img');
    if (img && !img.complete) img.addEventListener('load', layoutZonePins, { once: true });
  });
  kakao.maps.event.addListener(map, 'zoom_changed', layoutZonePins);

  // 빈 곳을 누르면 이름표를 닫습니다.
  const onMapClick = () => {
    if (!justOpened) closeLabel();
  };
  kakao.maps.event.addListener(map, 'click', onMapClick);

  // ── 지도 범례 (방문객 페이지에서만, 지도 바로 아래)
  // 지도에 실제로 놓인 시설만 아이콘·이름으로 보여 줍니다.
  let legend = null;
  if (document.body.classList.contains('visitor-page')) {
    // 위쪽 보기 버튼과 같은 순서, 차량 통제 바리게이트는 맨 끝
    const legendOrder = [...order, 'barricade'];
    const legendRank = (id) => (legendOrder.includes(id) ? legendOrder.indexOf(id) : legendOrder.length);
    const items = types
      .map((t) => ({ t, n: markers.filter((m) => m.type === t.id).length }))
      .filter(({ n }) => n > 0)
      .sort((a, b) => legendRank(a.t.id) - legendRank(b.t.id));
    if (items.length) {
      legend = document.createElement('section');
      legend.className = 'facility-legend';
      legend.setAttribute('aria-label', '지도 범례');
      const title = document.createElement('h3');
      title.textContent = '📍 지도 범례';
      const list = document.createElement('ul');
      items.forEach(({ t }) => {
        const li = document.createElement('li');
        const img = document.createElement('img');
        img.src = iconUrl(t.icon && t.icon.src);
        img.alt = '';
        const text = document.createElement('span');
        text.textContent = t.label;
        li.append(img, text);
        list.append(li);
      });
      legend.append(title, list);
      frame.after(legend);
    }
  }

  return {
    destroy() {
      if (legend) legend.remove();
      closeLabel();
      bar.remove();
      removeOverlays(shapes);
      removeOverlays(zonePins);
      removeOverlays(pins);
      kakao.maps.event.removeListener(map, 'click', onMapClick);
      kakao.maps.event.removeListener(map, 'zoom_changed', layoutZonePins);
    },
  };
}
