import './style.css';
import { MARKERS } from './config.js';
import { pickInitialViewProfile, resolveViewPoints, applyInitialView } from './initialView.js';
import { drawMarkers } from './layers.js';
import { watchMapResize } from './resize.js';
import { parseMapFile } from './mapData.js';
import { defaultFacilityTypes } from './markers/markerData.js';
import { startVisitorView } from './visitor.js';
import { showOverview } from './overview.js';
import publishedMapUrl from '../지도 json/최종_v18.json?url&no-inline';

const PLACEHOLDER = '여기에_JavaScript_키를_붙여넣으세요';
const apiKey = (import.meta.env.VITE_KAKAO_MAP_KEY || '').trim();
const adminMode = import.meta.env.DEV && new URLSearchParams(location.search).get('view') !== 'visitor';

function showNotice(html) {
  const el = document.getElementById('notice');
  el.innerHTML = `<div>${html}</div>`;
  el.hidden = false;
}

function loadKakaoSdk(key) {
  return new Promise((resolve, reject) => {
    const script = document.createElement('script');
    // 구역 그리기 도구(drawing)는 관리자 편집용이라 개발 서버에서만 불러옵니다.
    const libraries = adminMode ? 'services,drawing' : 'services';
    script.src = `https://dapi.kakao.com/v2/maps/sdk.js?appkey=${encodeURIComponent(key)}&libraries=${libraries}&autoload=false`;
    script.onload = () => {
      if (!window.kakao || !window.kakao.maps) {
        reject(new Error('kakao.maps not available'));
        return;
      }
      window.kakao.maps.load(resolve);
    };
    script.onerror = () => reject(new Error('SDK load failed'));
    document.head.appendChild(script);
  });
}

const container = document.getElementById('map');
if (!adminMode) {
  document.body.classList.add('visitor-page');
  document.getElementById('visitor-map-title').hidden = false;
}
const viewProfile = pickInitialViewProfile(container);

// 윗지도와 아래지도는 같은 최종 작업본에서 구역, 마커, 아이콘 설정을 읽습니다.
// 없거나 잘못되면 구역·마커 없이 지도를 엽니다.
async function loadPublishedData() {
  const empty = { zones: [], markers: [], facilityTypes: defaultFacilityTypes() };
  try {
    const res = await fetch(publishedMapUrl, { cache: 'no-cache' });
    if (!res.ok) return empty;
    return parseMapFile(await res.json());
  } catch (err) {
    console.warn('[festival-map] 최종 지도 데이터를 읽지 못해 구역·마커 없이 표시합니다.', err);
    return empty;
  }
}

// 순서: ① 처음 화면 기준 좌표 찾기 → ② 지도 만들기 → ③ 처음 표시 범위 맞추기
//       → ④ 마커 올리기(실제 좌표 기준) → ⑤ 지도 상자 크기 변화 감시 → ⑥ 구역 표시
const publishedData = loadPublishedData();
if (!adminMode) publishedData.then(showOverview).catch((error) => {
  console.warn('[festival-map] 윗지도 이미지를 생성하지 못했습니다.', error);
});

async function drawMap(viewPoints) {
  const { kakao } = window;

  // 지도를 만들 때 중심점이 꼭 필요해서 첫 장소로 잠시 두고, 바로 applyInitialView에서 범위를 맞춥니다.
  const firstPoint = new kakao.maps.LatLng(viewPoints[0].lat, viewPoints[0].lng);
  const map = new kakao.maps.Map(container, { center: firstPoint, level: 5 });

  applyInitialView(map, viewPoints, viewProfile, container);
  map.addControl(new kakao.maps.ZoomControl(), kakao.maps.ControlPosition.BOTTOMLEFT);
  // 일반 지도 ↔ 스카이뷰(위성 사진) 전환 버튼. 위쪽 보기 버튼과 겹치지 않게 오른쪽 아래에 둡니다.
  map.addControl(new kakao.maps.MapTypeControl(), kakao.maps.ControlPosition.BOTTOMRIGHT);

  drawMarkers(map, MARKERS);

  watchMapResize(map, container);

  // 개발 중(npm run dev)에만 브라우저 콘솔에서 지도를 확인할 수 있게 열어 둡니다. 실제 배포 파일에는 들어가지 않습니다.
  if (import.meta.env.DEV) window.__festivalMap = map;

  // ⑥ 구역·시설 마커 표시
  // - 개발 서버(npm run dev): 관리자 편집 화면 + 방문객 미리보기 전환
  // - 실제 배포(npm run build): 방문객 화면만. 관리자 코드는 아예 포함되지 않습니다.
  const published = await publishedData;
  if (import.meta.env.DEV && adminMode) {
    const { startAdminApp } = await import('./admin/adminApp.js');
    startAdminApp(map, published);
  } else {
    startVisitorView(map, published);
  }
}

if (!apiKey || apiKey === PLACEHOLDER) {
  showNotice(
    '카카오 JavaScript 키가 아직 입력되지 않았습니다.<br />' +
      'festival-map 폴더의 <code>.env</code> 파일에 키를 넣고 저장한 뒤,<br />' +
      '실행 중인 창을 끄고 <code>npm run dev</code>로 다시 실행해 주세요.'
  );
} else {
  loadKakaoSdk(apiKey)
    .then(() => {
      return resolveViewPoints(viewProfile).then(drawMap, (err) => {
        console.error('[festival-map]', err);
        showNotice(
          '축제장 주소를 좌표로 바꾸지 못해 지도를 열지 않았습니다.<br />' +
            `원인: ${err.message}<br />` +
            '<code>src/config.js</code>의 주소가 맞는지 확인해 주세요.'
        );
      });
    })
    .catch((err) => {
      console.error('[festival-map]', err);
      showNotice(
        '지도를 불러오지 못했습니다.<br />' +
          '1) <code>.env</code>의 키가 <b>JavaScript 키</b>가 맞는지<br />' +
          '2) 카카오 개발자 사이트에 <code>http://localhost:5173</code> 도메인을 등록했는지<br />' +
          '3) 앱 설정에서 <b>카카오맵</b> 사용이 켜져 있는지 확인해 주세요.'
      );
    });
}
