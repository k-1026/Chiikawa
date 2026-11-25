// 지도를 처음 열었을 때의 표시 범위만 담당합니다.
// 여기서는 지도의 "보는 위치"만 바꾸고, 마커·폴리곤 좌표는 절대 건드리지 않습니다.
import { INITIAL_VIEW } from './config.js';

// 화면 너비에 따라 PC용/모바일용 초기 표시 설정을 고릅니다.
export function pickInitialViewProfile(container) {
  const isMobile = container.clientWidth <= INITIAL_VIEW.mobileMaxWidth;
  return { type: isMobile ? 'mobile' : 'desktop', ...(isMobile ? INITIAL_VIEW.mobile : INITIAL_VIEW.desktop) };
}

// 주소 하나를 카카오 주소 검색으로 좌표로 바꿉니다. 실패하면 이유와 함께 멈춥니다.
function geocode(geocoder, place) {
  const { Status } = window.kakao.maps.services;
  return new Promise((resolve, reject) => {
    geocoder.addressSearch(place.address, (result, status) => {
      if (status === Status.OK && result.length > 0) {
        resolve({ ...place, lat: Number(result[0].y), lng: Number(result[0].x) });
      } else if (status === Status.ZERO_RESULT) {
        reject(new Error(`"${place.name}" 주소(${place.address})의 검색 결과가 없습니다.`));
      } else {
        reject(new Error(`"${place.name}" 주소 검색 중 오류가 났습니다. (카카오 응답: ${status})`));
      }
    });
  });
}

// 설정의 장소들을 실제 좌표 목록으로 만듭니다.
// lat/lng가 적혀 있으면 그대로 쓰고, 주소만 있으면 주소 검색으로 찾습니다.
export function resolveViewPoints(profile) {
  const geocoder = new window.kakao.maps.services.Geocoder();
  return Promise.all(
    profile.places.map((place) =>
      typeof place.lat === 'number' && typeof place.lng === 'number'
        ? Promise.resolve(place)
        : geocode(geocoder, place)
    )
  );
}

// 좌표 목록이 모두 보이도록 LatLngBounds + setBounds로 지도 범위를 맞춥니다.
export function applyInitialView(map, points, profile, container) {
  const { kakao } = window;
  const bounds = new kakao.maps.LatLngBounds();
  points.forEach((p) => bounds.extend(new kakao.maps.LatLng(p.lat, p.lng)));

  // 위아래 여백은 화면 높이, 좌우 여백은 화면 너비를 기준으로 따로 계산합니다.
  // 화면이 작으면 여백도 줄어서 모바일에서도 장소들이 함께 보입니다.
  const padY = Math.round(Math.min(profile.padding, container.clientHeight * 0.12));
  const padX = Math.round(Math.min(profile.padding, container.clientWidth * 0.12));
  map.setBounds(bounds, padY, padX, padY, padX);

  console.info(`[festival-map] 처음 화면(${profile.type}) 기준 좌표`, points);
}
