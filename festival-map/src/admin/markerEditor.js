// 시설 마커를 놓고·옮기고·고치고·지우는 관리자 편집 로직입니다. (개발 서버 전용)
// - 마커 위치(위도·경도)·이름·고유 ID는 아이콘을 바꿔도 그대로 유지됩니다.
// - 아이콘은 "시설 유형별 아이콘"을 기본으로 쓰고, 필요하면 마커 한 개만 다른 아이콘을 쓸 수 있습니다.
import { drawFacilityMarker } from '../markers/markerLayer.js';
import { cloneMarkers, cloneTypes, cloneIcon, iconForMarker, newMarkerId, typeLabel } from '../markers/markerData.js';

export function createMarkerEditor(map, initial, callbacks = {}) {
  const { kakao } = window;
  const notify = (name, ...args) => callbacks[name] && callbacks[name](...args);

  let markers = cloneMarkers(initial.markers || []);
  let types = cloneTypes(initial.facilityTypes || []);
  let selectedId = null;
  let placingType = null; // 지도에 놓을 시설 유형 (놓는 중이 아니면 null)
  let visible = true;
  let lastPlaceAt = 0;
  const shown = new Map(); // id → 카카오 마커

  // 선택한 마커 아래에 표시하는 동그라미(기준점 위치도 함께 보여 줌)
  const ringEl = document.createElement('div');
  ringEl.className = 'marker-ring';
  const ring = new kakao.maps.CustomOverlay({ content: ringEl, xAnchor: 0.5, yAnchor: 0.5, zIndex: 0 });

  const find = (id) => markers.find((m) => m.id === id) || null;

  function draw(m) {
    hideOne(m.id);
    if (!visible) return;
    shown.set(
      m.id,
      drawFacilityMarker(map, m, iconForMarker(m, types), {
        draggable: true,
        zIndex: m.id === selectedId ? 20 : 5,
        onClick: () => {
          if (placingType) return;
          select(m.id);
        },
        onDragEnd: (pos) => {
          m.lat = pos.lat;
          m.lng = pos.lng;
          if (m.id === selectedId) updateRing();
          notify('onChange');
          if (m.id === selectedId) notify('onSelect', m);
        },
      })
    );
  }

  function hideOne(id) {
    const k = shown.get(id);
    if (k) k.setMap(null);
    shown.delete(id);
  }

  function redrawAll() {
    [...shown.keys()].forEach(hideOne);
    if (visible) markers.forEach(draw);
    updateRing();
  }

  function updateRing() {
    const m = find(selectedId);
    if (!m || !visible) {
      ring.setMap(null);
      return;
    }
    ring.setPosition(new kakao.maps.LatLng(m.lat, m.lng));
    ring.setMap(map);
  }

  function select(id) {
    const m = find(id);
    if (!m) return;
    cancelPlacing();
    const prev = selectedId;
    selectedId = id;
    if (prev && find(prev)) draw(find(prev));
    draw(m);
    updateRing();
    notify('onSelect', m);
  }

  function deselect() {
    if (!selectedId) return;
    const prev = find(selectedId);
    selectedId = null;
    if (prev) draw(prev);
    updateRing();
    notify('onSelect', null);
  }

  // ── 지도에 새 마커 놓기
  function startPlacing(typeId) {
    deselect();
    placingType = typeId;
    notify('onPlacingChange', typeId);
  }

  function cancelPlacing() {
    if (!placingType) return;
    placingType = null;
    notify('onPlacingChange', null);
  }

  // 지도(또는 구역 도형 위)를 클릭한 위치에 마커를 놓습니다.
  function placeAt(latLng) {
    if (!placingType) return false;
    const now = Date.now();
    if (now - lastPlaceAt < 300) return true; // 같은 클릭이 두 번 들어오는 것 방지
    lastPlaceAt = now;
    const type = placingType;
    const count = markers.filter((m) => m.type === type).length + 1;
    const m = {
      id: newMarkerId(),
      name: `${typeLabel(types, type)} ${count}`,
      type,
      lat: latLng.getLat(),
      lng: latLng.getLng(),
      icon: null,
    };
    markers.push(m);
    placingType = null;
    notify('onPlacingChange', null);
    notify('onChange');
    selectedId = m.id;
    draw(m);
    updateRing();
    notify('onSelect', m, { isNew: true });
    return true;
  }

  kakao.maps.event.addListener(map, 'click', (e) => {
    if (placingType && visible) placeAt(e.latLng);
  });

  // ── 고치기
  function updateMarker(id, patch) {
    const m = find(id);
    if (!m) return;
    if (typeof patch.name === 'string') m.name = patch.name;
    if (typeof patch.type === 'string') m.type = patch.type;
    if ('icon' in patch) m.icon = cloneIcon(patch.icon);
    draw(m);
    notify('onChange');
  }

  function deleteMarker(id) {
    const i = markers.findIndex((m) => m.id === id);
    if (i < 0) return;
    hideOne(id);
    markers.splice(i, 1);
    if (selectedId === id) {
      selectedId = null;
      updateRing();
      notify('onSelect', null);
    }
    notify('onChange');
  }

  // ── 시설 유형별 아이콘
  function updateTypeIcon(typeId, icon) {
    const t = types.find((x) => x.id === typeId);
    if (!t) return;
    t.icon = cloneIcon(icon);
    markers.filter((m) => m.type === typeId).forEach(draw);
    notify('onChange');
  }

  // 같은 유형 마커 전부에 유형 아이콘을 일괄 적용합니다(개별 아이콘을 지움). 바뀐 마커 수를 돌려줍니다.
  function applyTypeIconToAll(typeId) {
    let n = 0;
    markers.forEach((m) => {
      if (m.type === typeId && m.icon) {
        m.icon = null;
        n += 1;
      }
    });
    markers.filter((m) => m.type === typeId).forEach(draw);
    if (n) notify('onChange');
    if (selectedId && find(selectedId) && find(selectedId).type === typeId) notify('onSelect', find(selectedId));
    return n;
  }

  // ── 전체 데이터
  function setAll(next) {
    cancelPlacing();
    selectedId = null;
    markers = cloneMarkers(next.markers);
    types = cloneTypes(next.facilityTypes);
    redrawAll();
    notify('onSelect', null);
  }

  function hide() {
    cancelPlacing();
    deselect();
    visible = false;
    redrawAll();
  }

  function show() {
    visible = true;
    redrawAll();
  }

  redrawAll();

  return {
    startPlacing,
    cancelPlacing,
    placeAt,
    isPlacing: () => placingType !== null,
    getPlacingType: () => placingType,
    select,
    deselect,
    getSelectedId: () => selectedId,
    updateMarker,
    deleteMarker,
    updateTypeIcon,
    applyTypeIconToAll,
    getMarkers: () => cloneMarkers(markers),
    getTypes: () => cloneTypes(types),
    setAll,
    hide,
    show,
    refreshIcons: redrawAll,
  };
}
