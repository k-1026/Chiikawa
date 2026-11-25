// 지도 저장 파일(JSON) 전체 모양입니다. 구역(도형) + 시설 마커 + 시설 유형별 아이콘 설정을 한 파일에 담습니다.
//
// {
//   format: 'festival-map-zones',
//   version: 3,
//   savedAt: '2026-11-23T...',
//   zones: [...],            // 구역·도형 (src/zones/zoneData.js)
//   markers: [...],          // 시설 마커 (src/markers/markerData.js)
//   facilityTypes: [...],    // 시설 유형별 이름·아이콘 설정
//   iconFiles: ['icons/...'] // 이 데이터가 쓰는 아이콘 파일 목록(웹사이트로 옮길 때 함께 옮길 파일, 참고용)
// }
//
// 예전 버전(1·2) 파일에는 markers·facilityTypes가 없습니다. 그런 파일은 구역만 읽고,
// 마커는 "정보 없음(null)"으로 돌려줘서 지금 있는 마커를 지우지 않도록 합니다.
import { ZONE_FILE_FORMAT, ZONE_FILE_VERSION, cloneZones, parseFileData } from './zones/zoneData.js';
import { cloneMarkers, cloneTypes, mergeFacilityTypes, normalizeMarkers, usedIconFiles } from './markers/markerData.js';

export function toMapFile({ zones, markers, facilityTypes }) {
  return {
    format: ZONE_FILE_FORMAT,
    version: ZONE_FILE_VERSION,
    savedAt: new Date().toISOString(),
    zones: cloneZones(zones),
    markers: cloneMarkers(markers),
    facilityTypes: cloneTypes(facilityTypes),
    iconFiles: usedIconFiles(markers, facilityTypes),
  };
}

// 반환: { zones, markers, facilityTypes, hasMarkers }
// - hasMarkers가 false면 파일에 마커 정보가 없던 것(예전 파일). 이때 markers는 [], facilityTypes는 기본값.
export function parseMapFile(data) {
  const zones = parseFileData(data);
  const hasMarkers = Array.isArray(data.markers);
  return {
    zones,
    markers: hasMarkers ? normalizeMarkers(data.markers) : [],
    facilityTypes: mergeFacilityTypes(data.facilityTypes),
    hasMarkers,
    hasTypes: Array.isArray(data.facilityTypes),
  };
}
