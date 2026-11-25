// 축제 구역(도형) 데이터의 모양을 정하고, 파일·저장소에서 읽은 데이터를 검사합니다.
// 관리자 편집 화면과 방문객 화면이 함께 씁니다.
//
// 도형 한 개의 모양:
// {
//   id: 'zone-xxxx',            // 도형마다 다른 고유 번호 (자동 생성)
//   name: '플리마켓',            // 이름
//   type: 'polygon',            // 도형 종류 (아래 SHAPE_TYPES 참고)
//   style: {
//     fillColor: '#ff6b6b',     // 채우기 색 (선·화살표는 쓰지 않음)
//     fillOpacity: 0.35,        // 채우기 투명도 0~1 (선·화살표는 쓰지 않음)
//     strokeColor: '#c92a2a',   // 테두리(선) 색
//     strokeOpacity: 1,         // 테두리(선) 투명도 0~1
//     strokeWeight: 3,          // 테두리(선) 두께(픽셀)
//   },
//   // 종류별 좌표 (모두 실제 위도·경도, 거리는 미터)
//   path: [{ lat, lng }, ...]                    // polygon(3점 이상), polyline·arrow(2점 이상)
//   center: { lat, lng }, radius: 40             // circle
//   bounds: { sw: { lat, lng }, ne: { lat, lng } } // rectangle, ellipse (남서·북동 모서리)
//   center, rx, ry                               // ellipse (가로·세로 반지름, 미터) — bounds로 자동 계산 가능
// }
//
// 버전 1 파일(종류 type이 없는 다각형만 있던 시절)도 그대로 읽습니다. type이 없으면 polygon으로 봅니다.

export const ZONE_FILE_FORMAT = 'festival-map-zones';
// 1: 다각형만, 2: 여러 도형, 3: 시설 마커·아이콘 설정 추가 (src/mapData.js)
export const ZONE_FILE_VERSION = 3;

// 도형 종류와 화면에 보일 이름
export const SHAPE_TYPES = {
  polygon: { label: '다각형', icon: '⬠' },
  polyline: { label: '선', icon: '╱' },
  arrow: { label: '화살표', icon: '➜' },
  circle: { label: '원', icon: '◯' },
  rectangle: { label: '사각형', icon: '▭' },
  ellipse: { label: '타원', icon: '⬭' },
};

// 채우기가 없는 선 종류
export const isLineType = (type) => type === 'polyline' || type === 'arrow';

// 이름 입력칸에서 고를 수 있는 예시입니다. 구역을 자동으로 만들지는 않습니다.
export const ZONE_NAME_EXAMPLES = [
  '10미 포장마차',
  '7구 맛집거리',
  '식사존',
  '플리마켓',
  '메인구역',
  '메인무대',
  '운영·관리 부스',
];

// 새 도형마다 차례로 다른 색을 줍니다.
const PALETTE = [
  { fillColor: '#ff6b6b', strokeColor: '#c92a2a' },
  { fillColor: '#4dabf7', strokeColor: '#1864ab' },
  { fillColor: '#69db7c', strokeColor: '#2b8a3e' },
  { fillColor: '#ffd43b', strokeColor: '#e67700' },
  { fillColor: '#b197fc', strokeColor: '#5f3dc4' },
  { fillColor: '#ffa94d', strokeColor: '#d9480f' },
  { fillColor: '#63e6be', strokeColor: '#087f5b' },
  { fillColor: '#f783ac', strokeColor: '#a61e4d' },
];

export function defaultStyle(index) {
  const colors = PALETTE[index % PALETTE.length];
  return { ...colors, fillOpacity: 0.35, strokeOpacity: 1, strokeWeight: 3 };
}

export function newZoneId() {
  return `zone-${Date.now().toString(36)}${Math.random().toString(36).slice(2, 6)}`;
}

const clonePoint = (p) => ({ lat: p.lat, lng: p.lng });

export function cloneZone(z) {
  const copy = { ...z, style: { ...z.style } };
  if (z.path) copy.path = z.path.map(clonePoint);
  if (z.center) copy.center = clonePoint(z.center);
  if (z.bounds) copy.bounds = { sw: clonePoint(z.bounds.sw), ne: clonePoint(z.bounds.ne) };
  if (z.labelPos) copy.labelPos = clonePoint(z.labelPos);
  if (z.code) copy.code = z.code;
  return copy;
}

export function cloneZones(zones) {
  return zones.map(cloneZone);
}

// 저장·내보내기용 전체 데이터 구조
export function toFileData(zones) {
  return {
    format: ZONE_FILE_FORMAT,
    version: ZONE_FILE_VERSION,
    savedAt: new Date().toISOString(),
    zones: cloneZones(zones),
  };
}

// 두 지점 사이 거리(미터)
export function distanceMeters(a, b) {
  const R = 6371008.8;
  const toRad = (d) => (d * Math.PI) / 180;
  const dLat = toRad(b.lat - a.lat);
  const dLng = toRad(b.lng - a.lng);
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(toRad(a.lat)) * Math.cos(toRad(b.lat)) * Math.sin(dLng / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(h));
}

// 두 모서리(순서 상관없음)로 남서·북동 bounds를 만듭니다.
export function boundsFromCorners(a, b) {
  return {
    sw: { lat: Math.min(a.lat, b.lat), lng: Math.min(a.lng, b.lng) },
    ne: { lat: Math.max(a.lat, b.lat), lng: Math.max(a.lng, b.lng) },
  };
}

// 타원의 중심·가로/세로 반지름을 bounds로 계산합니다.
export function ellipseFromBounds(bounds) {
  const center = { lat: (bounds.sw.lat + bounds.ne.lat) / 2, lng: (bounds.sw.lng + bounds.ne.lng) / 2 };
  const rx = distanceMeters({ lat: center.lat, lng: bounds.sw.lng }, { lat: center.lat, lng: bounds.ne.lng }) / 2;
  const ry = distanceMeters({ lat: bounds.sw.lat, lng: center.lng }, { lat: bounds.ne.lat, lng: center.lng }) / 2;
  return { center, rx, ry };
}

// 크기가 0이거나 점이 모자란 도형인지 검사합니다. 문제가 있으면 이유 문장을, 괜찮으면 null.
export function shapeProblem(zone) {
  const label = SHAPE_TYPES[zone.type] ? SHAPE_TYPES[zone.type].label : '도형';
  switch (zone.type) {
    case 'polygon':
      return zone.path && zone.path.length >= 3 ? null : `${label}은 꼭짓점이 3개 이상이어야 해요.`;
    case 'polyline':
    case 'arrow':
      return zone.path && zone.path.length >= 2 ? null : `${label}은 점이 2개 이상이어야 해요.`;
    case 'circle':
      return zone.radius >= 1 ? null : `${label}의 크기가 너무 작아요. 중심을 클릭한 뒤 마우스를 움직여 크기를 정하고 클릭해 주세요.`;
    case 'rectangle':
    case 'ellipse': {
      const b = zone.bounds;
      const tiny = !b || distanceMeters(b.sw, { lat: b.sw.lat, lng: b.ne.lng }) < 1 || distanceMeters(b.sw, { lat: b.ne.lat, lng: b.sw.lng }) < 1;
      return tiny ? `${label}의 크기가 너무 작아요. 한 모서리를 클릭한 뒤 마우스를 움직여 반대쪽 모서리를 클릭해 주세요.` : null;
    }
    default:
      return '알 수 없는 도형 종류예요.';
  }
}

const clamp = (n, min, max) => Math.min(max, Math.max(min, n));

function normalizeColor(value, fallback) {
  if (typeof value !== 'string') return fallback;
  const v = value.trim();
  if (/^#[0-9a-f]{6}$/i.test(v)) return v.toLowerCase();
  if (/^#[0-9a-f]{3}$/i.test(v)) return `#${v[1]}${v[1]}${v[2]}${v[2]}${v[3]}${v[3]}`.toLowerCase();
  return fallback;
}

function readPoint(p, what) {
  const lat = Number(p && p.lat);
  const lng = Number(p && p.lng);
  if (!Number.isFinite(lat) || !Number.isFinite(lng) || Math.abs(lat) > 90 || Math.abs(lng) > 180) {
    throw new Error(`${what} 좌표가 올바르지 않습니다.`);
  }
  return { lat, lng };
}

function normalizeZone(raw, index) {
  if (!raw || typeof raw !== 'object') throw new Error(`${index + 1}번째 도형의 형식이 올바르지 않습니다.`);
  const label = typeof raw.name === 'string' && raw.name.trim() ? raw.name.trim() : `이름 없는 구역 ${index + 1}`;
  const type = raw.type === undefined ? 'polygon' : raw.type;
  if (!SHAPE_TYPES[type]) throw new Error(`"${label}"의 도형 종류(${type})를 알 수 없습니다.`);

  const base = defaultStyle(index);
  const s = raw.style && typeof raw.style === 'object' ? raw.style : {};
  const num = (v) => (v === undefined || v === null || v === '' ? NaN : Number(v));
  const fillOpacity = num(s.fillOpacity);
  const strokeOpacity = num(s.strokeOpacity);
  const strokeWeight = num(s.strokeWeight);

  const zone = {
    id: typeof raw.id === 'string' && raw.id ? raw.id : newZoneId(),
    name: label,
    type,
    style: {
      fillColor: normalizeColor(s.fillColor, base.fillColor),
      fillOpacity: Number.isFinite(fillOpacity) ? clamp(fillOpacity, 0, 1) : base.fillOpacity,
      strokeColor: normalizeColor(s.strokeColor, base.strokeColor),
      strokeOpacity: Number.isFinite(strokeOpacity) ? clamp(strokeOpacity, 0, 1) : base.strokeOpacity,
      strokeWeight: Number.isFinite(strokeWeight) ? clamp(Math.round(strokeWeight), 1, 20) : base.strokeWeight,
    },
  };

  if (type === 'polygon' || type === 'polyline' || type === 'arrow') {
    if (!Array.isArray(raw.path)) throw new Error(`"${label}"의 점 목록(path)이 없습니다.`);
    zone.path = raw.path.map((p, i) => readPoint(p, `"${label}"의 ${i + 1}번째 점`));
  } else if (type === 'circle') {
    zone.center = readPoint(raw.center, `"${label}"의 중심`);
    zone.radius = Number(raw.radius);
    if (!Number.isFinite(zone.radius)) throw new Error(`"${label}"의 반지름(radius)이 올바르지 않습니다.`);
  } else {
    if (!raw.bounds) throw new Error(`"${label}"의 범위(bounds)가 없습니다.`);
    zone.bounds = boundsFromCorners(readPoint(raw.bounds.sw, `"${label}"의 남서쪽 모서리`), readPoint(raw.bounds.ne, `"${label}"의 북동쪽 모서리`));
    if (type === 'ellipse') {
      const calc = ellipseFromBounds(zone.bounds);
      const rx = Number(raw.rx);
      const ry = Number(raw.ry);
      zone.center = raw.center ? readPoint(raw.center, `"${label}"의 중심`) : calc.center;
      zone.rx = Number.isFinite(rx) && rx > 0 ? rx : calc.rx;
      zone.ry = Number.isFinite(ry) && ry > 0 ? ry : calc.ry;
    }
  }

  // 방문객 지도에서 구역 로고·번호를 직접 옮긴 위치(없으면 자동 위치)
  if (raw.labelPos) {
    try {
      zone.labelPos = readPoint(raw.labelPos, `"${label}"의 로고 위치`);
    } catch {
      // 잘못된 위치는 버리고 자동 위치를 씁니다.
    }
  }

  // 우리끼리 쓰는 (m-n) 코드(2장). 방문객 화면에는 안 보이고, 문서·디자인 작업에서 구역을 가리킬 때만 씀.
  if (typeof raw.code === 'string' && raw.code.trim()) zone.code = raw.code.trim();

  const problem = shapeProblem(zone);
  if (problem) throw new Error(`"${label}": ${problem}`);
  return zone;
}

// 파일이나 저장소에서 읽은 데이터를 검사해 도형 목록으로 돌려줍니다.
// 문제가 있으면 이유를 담은 오류를 냅니다(일부만 잘못 가져오지 않도록 전부 멈춤).
export function parseFileData(data) {
  if (!data || typeof data !== 'object') throw new Error('JSON 내용이 비어 있거나 형식이 다릅니다.');
  if (data.format !== ZONE_FILE_FORMAT) throw new Error('축제 지도 구역 파일이 아닙니다. (format 항목이 다릅니다)');
  if (typeof data.version === 'number' && data.version > ZONE_FILE_VERSION) {
    throw new Error(`더 새로운 버전(${data.version})의 파일이라 읽을 수 없습니다.`);
  }
  if (!Array.isArray(data.zones)) throw new Error('구역 목록(zones)이 없습니다.');

  const zones = data.zones.map(normalizeZone);
  const seen = new Set();
  zones.forEach((z) => {
    if (seen.has(z.id)) z.id = newZoneId();
    seen.add(z.id);
  });
  return zones;
}
