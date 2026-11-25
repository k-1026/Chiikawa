// ───────────────────────────────────────────────
// 지도 설정 파일입니다. 숫자·주소만 바꾸면 되고, 다른 코드는 건드리지 않아도 됩니다.
// ───────────────────────────────────────────────

// 처음 화면에 꼭 들어와야 하는 기준 장소들입니다.
// 각 장소는 address(주소, 카카오 주소 검색으로 좌표 찾기) 또는 lat/lng(위도·경도 직접 입력) 중 하나로 적습니다.
const MAIN_GATE = {
  name: '메인 출입로 (2.28자유광장)',
  // 도로명 '공원순환로 7'은 카카오 주소 검색에 없어, 카카오에 등록된 지번 주소를 씁니다.
  address: '대구 달서구 두류동 581-2',
};
const MAIN_STAGE = {
  name: '메인 스테이지 (코오롱야외음악당)',
  address: '대구 달서구 야외음악당로 180',
};

// 처음 화면(초기 표시 범위) 설정입니다.
// - 화면 너비가 mobileMaxWidth 이하이면 mobile, 그보다 넓으면 desktop 설정을 씁니다.
// - places: 이 장소들이 모두 한 화면에 들어오도록 지도가 자동으로 맞춰집니다.
// - padding: 장소가 가장자리에 붙지 않도록 두는 여백(픽셀). 화면이 작으면 자동으로 줄어듭니다.
// 지금은 PC·모바일이 같은 값입니다. 최종 배치가 정해지면 각각 따로 바꾸면 됩니다.
export const INITIAL_VIEW = {
  mobileMaxWidth: 767,
  desktop: {
    places: [MAIN_GATE, MAIN_STAGE],
    padding: 60,
  },
  mobile: {
    places: [MAIN_GATE, MAIN_STAGE],
    padding: 60,
  },
};

// 지도에 고정으로 표시할 단순 마커 목록입니다(카카오 기본 핀). 실제 위도·경도로 적습니다.
// 축제 시설 마커는 여기 말고 관리자 편집 화면의 [시설] 탭에서 만듭니다.
// 예: { name: '장소 이름', lat: 35.85, lng: 128.56 }
export const MARKERS = [];

// 시설 유형 목록입니다. 관리자 화면의 [시설] 탭에서 이 유형으로 마커를 만듭니다.
// - id: 영어 고유 이름(한 번 정하면 바꾸지 않기. 저장 파일이 이 이름으로 유형을 찾습니다)
// - label: 화면에 보일 이름
// - icon: 기본 아이콘(public/icons 폴더 기준 경로)과 크기(px), 기준점(anchorX·anchorY: 0~1, 0.5·0.5 = 정가운데)
// 아이콘은 관리자 화면 [아이콘] 탭에서 바꿀 수 있고, 바꾼 값은 저장 파일(JSON)에 들어갑니다.
//
// 시설 유형별 기본 아이콘입니다.
// - 시설별 색상의 원형 배지(white-*.png, badge-*.svg): 이미지 가운데가 실제 위치.
// (예전 기본이던 핀 모양 default-*.svg 파일도 폴더에 남아 있어 [아이콘] 탭에서 골라 쓸 수 있습니다)
const BADGE = { width: 25, height: 25, anchorX: 0.5, anchorY: 0.5 };
const MAJOR_BADGE = { ...BADGE, width: 40, height: 40 };
export const BARRICADE_TYPE = {
  id: 'barricade',
  label: '차량 통제',
  icon: { src: 'icons/badge-barricade-gray-2.svg', ...BADGE },
};

export const FACILITY_TYPES = [
  { id: 'medical', label: '의료실', icon: { src: 'icons/white-medical.png', ...BADGE } },
  { id: 'info', label: '안내소', icon: { src: 'icons/white-info.png', ...BADGE } },
  { id: 'toilet', label: '화장실', icon: { src: 'icons/white-toilet.png', ...BADGE } },
  { id: 'locker', label: '물품보관소', icon: { src: 'icons/badge-locker.svg', ...BADGE } },
  { id: 'lost', label: '분실물센터', icon: { src: 'icons/white-lost.png', ...BADGE } },
  { id: 'smoking', label: '흡연구역', icon: { src: 'icons/badge-smoking.svg', ...BADGE } },
  { id: 'parking', label: '주차장', icon: { src: 'icons/badge-parking.svg', ...BADGE } },
  { id: 'gate', label: '축제 출입로', icon: { src: 'icons/start.png', ...MAJOR_BADGE } },
  { id: 'stage', label: '무대', icon: { src: 'icons/festival-stage.png', ...MAJOR_BADGE } },
  { id: 'shelter', label: '더위쉼터', icon: { src: 'icons/white-shelter.png', ...BADGE } },
  { id: 'emergency', label: '소방·응급차', icon: { src: 'icons/white-emergency.png', ...BADGE } },
  { id: 'nursing', label: '수유실', icon: { src: 'icons/white-nursing.png', ...BADGE } },
  BARRICADE_TYPE,
];

// 예전 기본 핀 아이콘(설정을 바꾸지 않은 상태 그대로 저장된 것)을 알아보기 위한 값입니다.
// 저장 파일에 이 값 그대로 남아 있으면 현재 기본 아이콘으로 자동으로 바꿔 보여 줍니다.
// 직접 고른 아이콘이나 크기·기준점을 바꾼 설정은 그대로 둡니다.
export const LEGACY_DEFAULT_PIN = { width: 36, height: 46, anchorX: 0.5, anchorY: 1 };

// 방문객용 구역과 마커는 지도 json/최종_v18.json에서 읽습니다.

// 구역 로고입니다. 구역 이름이 똑같으면 방문객 지도에서 번호 대신 이 로고 그림이 보입니다.
// - src: public 폴더 기준 경로(로고 파일은 public/logos 폴더에 넣기)
// - width: 지도에 보일 가로 크기(px). 세로는 그림 비율대로 자동.
// 다른 구역도 같은 모양으로 한 줄씩 추가하면 됩니다. 예: '사투리한마당': { src: 'logos/saturi.webp', width: 110 },
export const ZONE_LOGOS = {
  플리마켓: { src: 'logos/flea-market.webp', width: 110 },
  운영부스: { src: 'logos/operation-booth.webp', width: 68 },
  // 예전 이름으로 저장된 데이터에도 같은 로고가 붙도록 남겨 둡니다.
  '운영·관리 본부': { src: 'logos/operation-booth.webp', width: 68 },
  '굿즈샵·이벤트 부스': { src: 'logos/goods-event.webp', width: 80 },
  // 표기를 '밥 묵자! 존'으로 바꾸는 중이라, 지도에 저장된 지금 이름과 새 이름 둘 다 연결해 둡니다.
  '밥묵자 존': { src: 'logos/bab-mukja.webp', width: 100 },
  '밥 묵자! 존': { src: 'logos/bab-mukja.webp', width: 100 },
  사투리한마당: { src: 'logos/saturi.webp', width: 83 },
  '7구 맛집거리': { src: 'logos/7gu-street.webp', width: 75 },
  '10미 포장마차': { src: 'logos/10mi-pocha.webp', width: 75 },
};
