// 카카오 Drawing Library(DrawingManager)로 도형을 그리고 고치는 핵심 로직입니다. (개발 서버 전용)
// 지원 도형: 다각형(polygon), 선(polyline), 화살표(arrow), 원(circle), 사각형(rectangle), 타원(ellipse)
//
// 왜 이렇게 만들었나:
// - Drawing Library는 데이터를 영구 저장하지 않습니다. 그래서 도형 목록(zones)은 이 파일이 직접 들고 있고,
//   저장·내보내기는 이 목록을 기준으로 합니다.
// - 공식 API의 put()으로 다시 올린 도형은 "그 순간 관리자에 설정된 스타일"을 따릅니다.
//   그래서 setStyle()로 그 도형의 색을 먼저 맞춘 뒤 put() 합니다.
//   put() 형식(공식 문서): 다각형·선·화살표 = 좌표 배열, 원 = 중심 + 반지름, 사각형·타원 = LatLngBounds
// - 되돌리기(undo) 등을 하면 DrawingManager 안의 도형 객체가 새로 만들어져, 도형 객체에 이름을 붙여 둘 수 없습니다.
//   그래서 "지금 편집 중인 도형 1개"만 DrawingManager에 올리고, 나머지는 일반 도형으로 그립니다.
//   편집이 끝나면 getData()로 좌표를 읽어 도형 목록에 반영합니다.
import { drawZone } from '../layers.js';
import {
  SHAPE_TYPES,
  isLineType,
  defaultStyle,
  newZoneId,
  cloneZones,
  boundsFromCorners,
  shapeProblem,
} from '../zones/zoneData.js';

const TYPES = Object.keys(SHAPE_TYPES);

export function createZoneEditor(map, initialZones, callbacks = {}) {
  const { kakao } = window;
  const notify = (name, ...args) => callbacks[name] && callbacks[name](...args);

  let zones = cloneZones(initialZones);
  let editingId = null; // DrawingManager에 올라가 있는 도형
  let drawingType = null; // 새로 그리는 중인 도형 종류 (아니면 null)
  let pendingStyle = null; // 새로 그릴 도형의 색
  let busy = false; // 코드가 직접 put/remove 하는 동안 변경 알림을 막음
  let visible = true;
  const plain = new Map(); // 편집 중이 아닌 도형의 일반 도형 (id → 카카오 도형)

  const editOptions = { draggable: true, editable: true, removable: false };
  const lineOptions = { ...editOptions, hintStrokeStyle: 'dash', hintStrokeOpacity: 0.6 };
  const manager = new kakao.maps.drawing.DrawingManager({
    map,
    drawingMode: TYPES,
    guideTooltip: ['draw', 'drag', 'edit'],
    polygonOptions: { ...lineOptions, ...defaultStyle(0) },
    polylineOptions: { ...lineOptions, ...defaultStyle(0) },
    arrowOptions: { ...lineOptions, ...defaultStyle(0) },
    circleOptions: { ...editOptions, ...defaultStyle(0) },
    rectangleOptions: { ...editOptions, ...defaultStyle(0) },
    ellipseOptions: { ...editOptions, ...defaultStyle(0) },
  });

  const findZone = (id) => zones.find((z) => z.id === id) || null;
  const ll = (p) => new kakao.maps.LatLng(p.lat, p.lng);
  const pt = (p) => ({ lat: p.y, lng: p.x }); // getData의 x = 경도, y = 위도

  // 같은 자리를 두 번 클릭해 생긴 겹친 점을 하나로 합칩니다.
  const dedupe = (path) =>
    path.filter((p, i) => i === 0 || Math.abs(p.lat - path[i - 1].lat) > 1e-9 || Math.abs(p.lng - path[i - 1].lng) > 1e-9);

  function applyManagerStyle(type, style) {
    manager.setStyle(type, 'strokeColor', style.strokeColor);
    manager.setStyle(type, 'strokeWeight', style.strokeWeight);
    manager.setStyle(type, 'strokeOpacity', style.strokeOpacity);
    if (!isLineType(type)) {
      manager.setStyle(type, 'fillColor', style.fillColor);
      manager.setStyle(type, 'fillOpacity', style.fillOpacity);
    }
  }

  // DrawingManager에 올라간 도형의 좌표를 getData()로 읽어, 우리 데이터 모양으로 바꿉니다.
  function readManagerGeometry(type) {
    const list = (manager.getData([type]) || {})[type] || [];
    if (!list.length) return null;
    const d = list[0];
    switch (type) {
      case 'polygon':
      case 'polyline':
      case 'arrow':
        return { path: dedupe(d.points.map(pt)) };
      case 'circle':
        return { center: pt(d.center), radius: d.radius };
      case 'rectangle':
        return { bounds: boundsFromCorners(pt(d.sPoint), pt(d.ePoint)) };
      case 'ellipse':
        return { bounds: boundsFromCorners(pt(d.sPoint), pt(d.ePoint)), center: pt(d.center), rx: d.rx, ry: d.ry };
      default:
        return null;
    }
  }

  function clearManager() {
    busy = true;
    const all = manager.getOverlays(TYPES) || {};
    TYPES.forEach((t) => (all[t] || []).forEach((o) => manager.remove(o)));
    busy = false;
  }

  // 공식 put()으로 도형을 DrawingManager에 올립니다(편집 가능 상태가 됨).
  function putToManager(zone) {
    busy = true;
    applyManagerStyle(zone.type, zone.style);
    switch (zone.type) {
      case 'circle':
        manager.put('circle', ll(zone.center), zone.radius);
        break;
      case 'rectangle':
      case 'ellipse':
        manager.put(zone.type, new kakao.maps.LatLngBounds(ll(zone.bounds.sw), ll(zone.bounds.ne)));
        break;
      default:
        manager.put(zone.type, zone.path.map(ll));
    }
    busy = false;
  }

  function drawPlain(zone) {
    removePlain(zone.id);
    if (!visible) return;
    plain.set(
      zone.id,
      drawZone(map, zone, (z, e) => {
        // 다른 작업(예: 시설 마커 놓기)이 이 클릭을 쓰면 구역 선택은 하지 않습니다.
        if (callbacks.onPlainClick && callbacks.onPlainClick(z, e)) return;
        select(z.id);
      })
    );
  }

  function removePlain(id) {
    const shape = plain.get(id);
    if (shape) shape.setMap(null);
    plain.delete(id);
  }

  // 편집 중인 도형의 최신 좌표를 도형 목록에 반영합니다(편집 상태는 유지).
  function syncEditingGeometry() {
    const zone = findZone(editingId);
    if (!zone) return;
    const geo = readManagerGeometry(zone.type);
    if (!geo) return;
    const next = { ...zone, ...geo };
    if (!shapeProblem(next)) Object.assign(zone, geo);
  }

  // 편집을 마치고 일반 도형으로 되돌립니다.
  function finishEditing() {
    if (!editingId) return;
    syncEditingGeometry();
    const zone = findZone(editingId);
    clearManager();
    editingId = null;
    if (zone) drawPlain(zone);
    notify('onSelect', null);
  }

  function select(id) {
    const zone = findZone(id);
    if (!zone || id === editingId) return;
    if (drawingType) cancelDrawing();
    finishEditing();
    removePlain(id);
    putToManager(zone);
    editingId = id;
    notify('onSelect', zone);
  }

  function startDrawing(type = 'polygon') {
    if (!SHAPE_TYPES[type]) return;
    if (drawingType) cancelDrawing();
    finishEditing();
    pendingStyle = defaultStyle(zones.length);
    busy = true;
    applyManagerStyle(type, pendingStyle);
    busy = false;
    manager.select(type);
    drawingType = type;
    notify('onDrawingChange', type);
  }

  function cancelDrawing() {
    if (!drawingType) return;
    drawingType = null;
    manager.cancel();
    notify('onDrawingChange', null);
  }

  // 선·화살표는 마지막 점을 더블클릭해 끝내는데, 지도가 더블클릭으로 확대되는 기본 동작도 함께 일어납니다.
  // 그래서 점을 찍을 때의 화면을 기억해 두었다가, 그리기가 끝난 직후의 확대는 되돌립니다.
  let lastView = null;
  let restoreView = null;
  const rememberView = () => {
    lastView = { level: map.getLevel(), center: map.getCenter() };
  };
  manager.addListener('drawstart', rememberView);
  manager.addListener('drawnext', rememberView);
  kakao.maps.event.addListener(map, 'zoom_changed', () => {
    if (!restoreView) return;
    const view = restoreView;
    restoreView = null;
    if (Date.now() > view.until) return;
    map.setLevel(view.level);
    map.setCenter(view.center);
  });

  // 그리기가 끝나면 새 도형을 만듭니다.
  manager.addListener('drawend', (e) => {
    const type = (e && e.overlayType) || drawingType;
    if (lastView) restoreView = { ...lastView, until: Date.now() + 800 };
    drawingType = null;
    notify('onDrawingChange', null);
    const geo = readManagerGeometry(type);
    const zone = {
      id: newZoneId(),
      name: `새 ${SHAPE_TYPES[type] ? SHAPE_TYPES[type].label : '도형'} ${zones.length + 1}`,
      type,
      style: pendingStyle || defaultStyle(zones.length),
      ...geo,
    };
    const problem = !geo ? '도형을 읽지 못했어요. 다시 그려 주세요.' : shapeProblem(zone);
    if (problem) {
      clearManager();
      notify('onMessage', problem);
      return;
    }
    zones.push(zone);
    editingId = zone.id;
    notify('onChange');
    notify('onSelect', zone, { isNew: true });
  });

  manager.addListener('cancel', () => {
    if (!drawingType) return;
    drawingType = null;
    notify('onDrawingChange', null);
  });

  // 꼭짓점·크기를 바꾸거나 도형을 끌어 옮기면 '저장 안 된 변경'으로 표시합니다.
  manager.addListener('state_changed', () => {
    if (busy || drawingType || !editingId) return;
    notify('onChange');
  });

  function updateZone(id, patch) {
    const zone = findZone(id);
    if (!zone) return;
    if (typeof patch.name === 'string') zone.name = patch.name;
    if (patch.labelPos !== undefined) {
      if (patch.labelPos) zone.labelPos = { lat: patch.labelPos.lat, lng: patch.labelPos.lng };
      else delete zone.labelPos;
    }
    if (patch.style) {
      zone.style = { ...zone.style, ...patch.style };
      if (id === editingId) {
        // 편집 중이면 지금 모양을 유지한 채 새 색으로 다시 올립니다.
        syncEditingGeometry();
        clearManager();
        putToManager(zone);
      } else {
        drawPlain(zone);
      }
    }
    notify('onChange');
  }

  function deleteZone(id) {
    const index = zones.findIndex((z) => z.id === id);
    if (index < 0) return;
    if (id === editingId) {
      clearManager();
      editingId = null;
    } else {
      removePlain(id);
    }
    zones.splice(index, 1);
    notify('onChange');
    notify('onSelect', null);
  }

  // 도형 전체를 바꿉니다(JSON 가져오기).
  function setZones(next) {
    cancelDrawing();
    clearManager();
    editingId = null;
    [...plain.keys()].forEach(removePlain);
    zones = cloneZones(next);
    zones.forEach(drawPlain);
    notify('onSelect', null);
  }

  // 저장·내보내기용: 편집 중인 도형의 최신 좌표까지 반영한 복사본
  function getZones() {
    if (editingId) syncEditingGeometry();
    return cloneZones(zones);
  }

  // 방문객 미리보기로 바꿀 때 편집 도형을 모두 숨기고, 돌아오면 다시 그립니다.
  function hide() {
    cancelDrawing();
    finishEditing();
    visible = false;
    [...plain.keys()].forEach(removePlain);
  }

  function show() {
    visible = true;
    zones.forEach(drawPlain);
  }

  zones.forEach(drawPlain);

  return {
    startDrawing,
    cancelDrawing,
    isDrawing: () => drawingType !== null,
    getDrawingType: () => drawingType,
    select,
    finishEditing,
    getEditingId: () => editingId,
    updateZone,
    deleteZone,
    setZones,
    getZones,
    hide,
    show,
  };
}
