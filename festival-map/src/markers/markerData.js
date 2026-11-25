// 시설 마커와 시설 유형(아이콘 설정) 데이터의 모양을 정하고 검사합니다.
// 관리자 편집 화면과 방문객 화면이 함께 씁니다.
//
// 시설 유형 한 개:
// { id: 'medical', label: '의료실', icon: { src: 'icons/default-medical.svg', width: 36, height: 46, anchorX: 0.5, anchorY: 1 } }
//
// 시설 마커 한 개:
// {
//   id: 'mk-xxxx',          // 고유 번호 (아이콘을 바꿔도 그대로)
//   name: '의료실 1',        // 이름
//   type: 'medical',        // 시설 유형 id
//   lat: 35.85, lng: 128.56, // 위치 (아이콘을 바꿔도 그대로)
//   icon: null              // null이면 유형 아이콘을 따름. 이 마커만 다른 아이콘이면 { src, width, height, anchorX, anchorY }
// }
//
// 아이콘 src는 'icons/파일이름' 처럼 public 폴더 기준 상대 경로로 저장합니다.
// 그래서 실제 웹사이트로 옮길 때 public/icons 폴더만 함께 옮기면 경로가 그대로 맞습니다.
import { BARRICADE_TYPE, FACILITY_TYPES, LEGACY_DEFAULT_PIN } from '../config.js';

const PREVIOUS_BADGE_SIZES = new Map([['barricade', 42], ['gate', 48], ['stage', 52]]);

// 예전 기본 핀(아무것도 바꾸지 않은 그대로)인지 확인합니다.
function isUntouchedLegacyPin(typeId, icon) {
  return (
    Boolean(icon) &&
    icon.src === `icons/default-${typeId}.svg` &&
    icon.width === LEGACY_DEFAULT_PIN.width &&
    icon.height === LEGACY_DEFAULT_PIN.height &&
    icon.anchorX === LEGACY_DEFAULT_PIN.anchorX &&
    icon.anchorY === LEGACY_DEFAULT_PIN.anchorY
  );
}

// 이전 기본 배지와 바리게이트를 기본 크기와 기준점 그대로 쓰던 설정만 교체합니다.
function isUntouchedLegacyBadge(typeId, icon, currentIcon) {
  if (typeId === BARRICADE_TYPE.id) {
    const wasDefault = (icon.src === 'icons/barricade.svg' && icon.width === 44 && icon.height === 34) ||
      ((icon.src === 'icons/white-barricade.png' || icon.src === currentIcon.src) && icon.width === 32 && icon.height === 32);
    return wasDefault &&
      icon.anchorX === 0.5 && icon.anchorY === 0.5;
  }
  if (typeId === 'gate') {
    return (icon.src === 'icons/badge-gate.svg' || icon.src === currentIcon.src) &&
      icon.width === 32 && icon.height === 32 && icon.anchorX === 0.5 && icon.anchorY === 0.5;
  }
  return (
    currentIcon.src === `icons/white-${typeId}.png` &&
    icon.src === `icons/badge-${typeId}.svg` &&
    ([32, currentIcon.width].includes(icon.width) && icon.height === icon.width) &&
    icon.anchorX === currentIcon.anchorX &&
    icon.anchorY === currentIcon.anchorY
  );
}

// 아이콘 파일을 못 찾을 때 대신 보여 줄 회색 물음표 핀(파일이 없어도 항상 표시됨)
export const FALLBACK_ICON_SRC =
  'data:image/svg+xml;charset=utf-8,' +
  encodeURIComponent(
    '<svg xmlns="http://www.w3.org/2000/svg" width="36" height="46" viewBox="0 0 36 46"><path d="M18 45C18 45 3 28.5 3 17a15 15 0 1 1 30 0c0 11.5-15 28-15 28z" fill="#868e96" stroke="#fff" stroke-width="2"/><text x="18" y="23" text-anchor="middle" font-family="Arial,sans-serif" font-size="16" font-weight="700" fill="#fff">?</text></svg>'
  );

export const DEFAULT_ICON = { src: '', width: 36, height: 46, anchorX: 0.5, anchorY: 1 };

// 기준점(Anchor) 빠른 선택
export const ANCHOR_PRESETS = [
  { id: 'bottom', label: '아래 가운데 (핀 끝)', anchorX: 0.5, anchorY: 1 },
  { id: 'center', label: '정가운데', anchorX: 0.5, anchorY: 0.5 },
  { id: 'top', label: '위 가운데', anchorX: 0.5, anchorY: 0 },
  { id: 'bottom-left', label: '왼쪽 아래', anchorX: 0, anchorY: 1 },
  { id: 'bottom-right', label: '오른쪽 아래', anchorX: 1, anchorY: 1 },
];

const clamp = (n, min, max) => Math.min(max, Math.max(min, n));

export function newMarkerId() {
  return `mk-${Date.now().toString(36)}${Math.random().toString(36).slice(2, 6)}`;
}

// 아이콘 경로가 안전한지 검사합니다. public 폴더 기준 상대 경로, http(s), data: 이미지만 허용합니다.
function normalizeSrc(src) {
  if (typeof src !== 'string') return '';
  const s = src.trim().replace(/\\/g, '/');
  if (!s) return '';
  if (/^data:image\//i.test(s) || /^https?:\/\//i.test(s)) return s;
  if (s.startsWith('/') || s.split('/').includes('..') || /^[a-z]+:/i.test(s)) return '';
  return s;
}

export function normalizeIcon(raw, fallback = DEFAULT_ICON) {
  if (!raw || typeof raw !== 'object') return { ...fallback };
  const num = (v, d) => (Number.isFinite(Number(v)) && v !== null && v !== '' ? Number(v) : d);
  return {
    src: normalizeSrc(raw.src) || fallback.src,
    width: clamp(Math.round(num(raw.width, fallback.width)), 8, 200),
    height: clamp(Math.round(num(raw.height, fallback.height)), 8, 200),
    anchorX: clamp(num(raw.anchorX, fallback.anchorX), 0, 1),
    anchorY: clamp(num(raw.anchorY, fallback.anchorY), 0, 1),
  };
}

export function cloneIcon(icon) {
  return icon ? { ...icon } : null;
}

export function defaultFacilityTypes() {
  return FACILITY_TYPES.map((t) => ({ id: t.id, label: t.label, icon: normalizeIcon(t.icon) }));
}

export function cloneTypes(types) {
  return types.map((t) => ({ ...t, icon: cloneIcon(t.icon) }));
}

export function cloneMarkers(markers) {
  return markers.map((m) => ({ ...m, icon: cloneIcon(m.icon) }));
}

// 저장 파일의 시설 유형을 기본 목록과 합칩니다.
// - 같은 id는 파일 값(바꾼 아이콘·이름)을 씁니다.
// - 파일에만 있는 유형도 지우지 않고 그대로 둡니다.
// - 예전 기본 핀·배지를 바꾸지 않고 쓰던 유형은 현재 기본 아이콘으로 바꿉니다.
export function mergeFacilityTypes(rawTypes) {
  const base = defaultFacilityTypes();
  if (!Array.isArray(rawTypes)) return base;
  const byId = new Map(base.map((t) => [t.id, t]));
  rawTypes.forEach((raw) => {
    if (!raw || typeof raw.id !== 'string' || !raw.id.trim()) return;
    const id = raw.id.trim();
    const prev = byId.get(id);
    const label = typeof raw.label === 'string' && raw.label.trim() ? raw.label.trim() : prev ? prev.label : id;
    let icon = normalizeIcon(raw.icon, prev ? prev.icon : DEFAULT_ICON);
    if (prev && (isUntouchedLegacyPin(id, icon) || isUntouchedLegacyBadge(id, icon, prev.icon))) {
      icon = { ...prev.icon };
    }
    // 바리게이트 예전 그림으로 저장된 파일도 지금 기본 아이콘으로 보여 줍니다. 크기·기준점은 저장값 그대로.
    const oldBarricadeIcons = ['icons/fence.png', 'icons/badge-barricade-gray.svg'];
    if (prev && id === BARRICADE_TYPE.id && oldBarricadeIcons.includes(icon.src)) {
      icon = { ...icon, src: prev.icon.src };
    }
    if (prev && icon.src === prev.icon.src && icon.anchorX === prev.icon.anchorX && icon.anchorY === prev.icon.anchorY) {
      const previousSize = PREVIOUS_BADGE_SIZES.get(id) ?? 32;
      if (icon.width === previousSize && icon.height === previousSize) {
        icon = { ...prev.icon };
      }
    }
    byId.set(id, { id, label, icon });
  });
  return [...byId.values()];
}

export function normalizeMarkers(rawMarkers) {
  if (!Array.isArray(rawMarkers)) return [];
  const seen = new Set();
  return rawMarkers.map((raw, i) => {
    if (!raw || typeof raw !== 'object') throw new Error(`${i + 1}번째 시설 마커의 형식이 올바르지 않습니다.`);
    const name = typeof raw.name === 'string' && raw.name.trim() ? raw.name.trim() : `이름 없는 시설 ${i + 1}`;
    const lat = Number(raw.lat);
    const lng = Number(raw.lng);
    if (!Number.isFinite(lat) || !Number.isFinite(lng) || Math.abs(lat) > 90 || Math.abs(lng) > 180) {
      throw new Error(`"${name}" 시설 마커의 좌표가 올바르지 않습니다.`);
    }
    let id = typeof raw.id === 'string' && raw.id ? raw.id : newMarkerId();
    if (seen.has(id)) id = newMarkerId();
    seen.add(id);
    return {
      id,
      name,
      type: typeof raw.type === 'string' && raw.type ? raw.type : 'info',
      lat,
      lng,
      icon: raw.icon ? normalizeIcon(raw.icon) : null,
    };
  });
}

// 마커가 실제로 쓸 아이콘: 개별 아이콘 → 유형 아이콘 → 대체 아이콘
export function iconForMarker(marker, types) {
  if (marker.icon && marker.icon.src) return marker.icon;
  const type = types.find((t) => t.id === marker.type);
  if (type && type.icon && type.icon.src) return type.icon;
  return { ...DEFAULT_ICON, src: FALLBACK_ICON_SRC };
}

export function typeLabel(types, id) {
  const t = types.find((x) => x.id === id);
  return t ? t.label : `알 수 없는 유형(${id})`;
}

// 아이콘 경로를 실제 주소로 바꿉니다. (한글·공백 파일 이름도 동작하도록 부분별로 인코딩)
export function iconUrl(src) {
  if (!src) return FALLBACK_ICON_SRC;
  if (/^(data:|https?:\/\/)/i.test(src)) return src;
  const base = import.meta.env.BASE_URL || '/';
  return base + src.split('/').map(encodeURIComponent).join('/');
}

// 저장 데이터가 쓰는 아이콘 파일 목록 (웹사이트로 옮길 때 함께 옮길 파일)
export function usedIconFiles(markers, types) {
  const files = new Set();
  types.forEach((t) => t.icon && t.icon.src && !/^(data:|https?:)/i.test(t.icon.src) && files.add(t.icon.src));
  markers.forEach((m) => m.icon && m.icon.src && !/^(data:|https?:)/i.test(m.icon.src) && files.add(m.icon.src));
  return [...files].sort();
}
