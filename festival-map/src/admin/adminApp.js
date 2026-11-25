// 관리자 편집 화면(도구 막대, 구역·시설·아이콘 패널, 모드 전환)입니다.
// main.js가 개발 서버(npm run dev)에서만 이 파일을 불러오므로, 실제 배포(npm run build) 결과에는 들어가지 않습니다.
import './admin.css';
import { createZoneEditor } from './zoneEditor.js';
import { createMarkerEditor } from './markerEditor.js';
import { createIconPicker, fetchIconFiles } from './iconPicker.js';
import { loadLocal, saveLocal, downloadJson, readJsonFile } from './storage.js';
import { ZONE_NAME_EXAMPLES, SHAPE_TYPES, isLineType } from '../zones/zoneData.js';
import { iconForMarker, iconUrl, typeLabel, usedIconFiles } from '../markers/markerData.js';
import { checkImage, forgetImageChecks } from '../markers/markerLayer.js';
import { startVisitorView } from '../visitor.js';

// 도형별 그리는 방법 안내
const DRAW_HINTS = {
  polygon: ['지도를 클릭해 꼭짓점을 찍고, ', '첫 번째 점을 다시 클릭', '하면 완성돼요.'],
  polyline: ['지도를 클릭해 점을 찍고, ', '마지막 점은 더블클릭', '하면 완성돼요.'],
  arrow: ['시작점부터 클릭해 점을 찍고, ', '마지막 점(화살촉 자리)은 더블클릭', '하면 완성돼요.'],
  circle: ['중심을 클릭한 뒤 ', '마우스를 움직여 크기를 정하고 클릭', '하면 완성돼요.'],
  rectangle: ['한 모서리를 클릭한 뒤 ', '마우스를 움직여 반대쪽 모서리를 클릭', '하면 완성돼요.'],
  ellipse: ['한 모서리를 클릭한 뒤 ', '마우스를 움직여 반대쪽 모서리를 클릭', '하면 완성돼요.'],
};

// 도형별 고치는 방법 안내
const EDIT_HINTS = {
  polygon: '하얀 작은 네모(꼭짓점)를 끌면 모양이 바뀌고, 변 가운데 흐린 네모를 끌면 꼭짓점이 추가돼요. 안쪽을 끌면 통째로 옮겨져요.',
  polyline: '하얀 작은 네모(점)를 끌면 모양이 바뀌고, 선 가운데 흐린 네모를 끌면 점이 추가돼요. 선을 끌면 통째로 옮겨져요.',
  arrow: '하얀 작은 네모(점)를 끌면 모양이 바뀌고, 선 가운데 흐린 네모를 끌면 점이 추가돼요. 선을 끌면 통째로 옮겨져요.',
  circle: '가장자리의 작은 네모를 끌면 크기가 바뀌고, 안쪽을 끌면 통째로 옮겨져요.',
  rectangle: '모서리의 작은 네모를 끌면 크기가 바뀌고, 안쪽을 끌면 통째로 옮겨져요.',
  ellipse: '가장자리의 작은 네모를 끌면 크기가 바뀌고, 안쪽을 끌면 통째로 옮겨져요.',
};

function el(tag, attrs = {}, children = []) {
  const node = document.createElement(tag);
  Object.entries(attrs).forEach(([k, v]) => {
    if (k === 'class') node.className = v;
    else if (k === 'text') node.textContent = v;
    else node.setAttribute(k, v);
  });
  children.forEach((c) => node.append(c));
  return node;
}

const formatTime = (iso) =>
  new Date(iso).toLocaleString('ko-KR', { month: 'numeric', day: 'numeric', hour: 'numeric', minute: '2-digit' });

// published: { zones, markers, facilityTypes } (방문객용 최종 지도 데이터)
export function startAdminApp(map, published) {
  const { kakao } = window;
  const main = document.querySelector('main');
  const topbar = document.querySelector('.topbar');

  // ── 처음 불러올 데이터: 브라우저에 임시 저장된 작업 → 없으면 방문객용 최종 지도 데이터
  const local = loadLocal();
  const start = local.data || published;
  let dirty = false;
  let mode = 'admin';
  let visitorView = null;
  let activeTab = 'zones'; // zones | markers | icons
  let iconFiles = [];

  // ── 상단 모드 전환
  const adminBtn = el('button', { type: 'button', class: 'mode-btn is-active', text: '관리자 편집' });
  const visitorBtn = el('button', { type: 'button', class: 'mode-btn', text: '방문객 미리보기' });
  const modeSwitch = el('div', { class: 'mode-switch', role: 'group', 'aria-label': '화면 모드' }, [adminBtn, visitorBtn]);
  topbar.append(modeSwitch);

  // ── 도구 막대: 도형 종류 버튼(누르면 바로 그리기 시작)
  const shapeButtons = Object.entries(SHAPE_TYPES).map(([type, info]) => {
    const btn = el('button', { type: 'button', class: 'btn shape-btn', title: `${info.label} 그리기`, 'data-type': type }, [
      el('span', { class: 'shape-icon', 'aria-hidden': 'true', text: info.icon }),
      el('span', { text: info.label }),
    ]);
    btn.addEventListener('click', () => {
      markerEd.cancelPlacing();
      markerEd.deselect();
      editor.startDrawing(type);
    });
    return btn;
  });
  const drawLabel = el('span', { class: 'tool-label', text: '그리기' });
  const drawBtn = el('div', { class: 'shape-picker', role: 'group', 'aria-label': '그릴 도형 선택' }, [drawLabel, ...shapeButtons]);
  const cancelBtn = el('button', { type: 'button', class: 'btn btn-warn', text: '그리기 취소', hidden: '' });

  // ── 도구 막대: 시설 마커 놓기
  const placeTypeSelect = el('select', { class: 'place-type', 'aria-label': '놓을 시설 유형' });
  const placeBtn = el('button', { type: 'button', class: 'btn shape-btn', title: '시설 마커를 지도에 놓기' }, [
    el('span', { class: 'shape-icon', 'aria-hidden': 'true', text: '📍' }),
    el('span', { text: '마커 놓기' }),
  ]);
  const placeCancelBtn = el('button', { type: 'button', class: 'btn btn-warn', text: '놓기 취소', hidden: '' });
  const markerTools = el('div', { class: 'shape-picker', role: 'group', 'aria-label': '시설 마커' }, [
    el('span', { class: 'tool-label', text: '시설' }),
    placeTypeSelect,
    placeBtn,
    placeCancelBtn,
  ]);

  const saveBtn = el('button', { type: 'button', class: 'btn', text: '저장' });
  const exportBtn = el('button', { type: 'button', class: 'btn', text: 'JSON 내보내기' });
  const importBtn = el('button', { type: 'button', class: 'btn', text: 'JSON 가져오기' });
  const fileInput = el('input', { type: 'file', accept: '.json,application/json', hidden: '' });
  const status = el('span', { class: 'save-status', role: 'status' });
  const toolbar = el('div', { class: 'admin-toolbar' }, [
    el('div', { class: 'tool-group' }, [drawBtn, cancelBtn]),
    el('div', { class: 'tool-group' }, [markerTools]),
    el('div', { class: 'tool-group' }, [saveBtn, exportBtn, importBtn, fileInput]),
    status,
  ]);

  const hint = el('div', { class: 'admin-hint', hidden: '' });
  function renderDrawHint(type) {
    const [before, strong, after] = DRAW_HINTS[type] || DRAW_HINTS.polygon;
    hint.replaceChildren(
      el('strong', { text: `${SHAPE_TYPES[type].label} 그리는 중 · ` }),
      document.createTextNode(before),
      el('b', { text: strong }),
      document.createTextNode(`${after} 그만두려면 Esc 또는 [그리기 취소].`)
    );
  }
  function renderPlaceHint(typeId) {
    hint.replaceChildren(
      el('strong', { text: `${typeLabel(markerEd.getTypes(), typeId)} 마커 놓는 중 · ` }),
      document.createTextNode('지도에서 '),
      el('b', { text: '놓을 곳을 클릭' }),
      document.createTextNode('하세요. 그만두려면 Esc 또는 [놓기 취소].')
    );
  }

  const toast = el('div', { class: 'admin-toast', role: 'alert', hidden: '' });

  // ── 패널 탭
  const tabZones = el('button', { type: 'button', class: 'panel-tab', 'data-tab': 'zones' });
  const tabMarkers = el('button', { type: 'button', class: 'panel-tab', 'data-tab': 'markers' });
  const tabIcons = el('button', { type: 'button', class: 'panel-tab', 'data-tab': 'icons', text: '아이콘' });
  const tabs = el('div', { class: 'panel-tabs', role: 'tablist' }, [tabZones, tabMarkers, tabIcons]);
  [tabZones, tabMarkers, tabIcons].forEach((t) =>
    t.addEventListener('click', () => {
      activeTab = t.dataset.tab;
      renderPanel();
    })
  );

  // ── 구역 목록
  const list = el('ul', { class: 'zone-list' });
  const empty = el('p', { class: 'panel-empty', text: '아직 구역이 없어요. 위의 [그리기]에서 도형을 골라 시작하세요.' });
  const listView = el('section', { class: 'panel-view' }, [list, empty]);

  // ── 시설 마커 목록
  const markerList = el('ul', { class: 'zone-list' });
  const markerEmpty = el('p', {
    class: 'panel-empty',
    text: '아직 시설 마커가 없어요. 위의 [시설]에서 유형을 고르고 [마커 놓기]를 누른 뒤 지도를 클릭하세요.',
  });
  const markerListView = el('section', { class: 'panel-view', hidden: '' }, [markerList, markerEmpty]);

  // ── 아이콘 탭: 시설 유형별 아이콘
  const iconTypeSelect = el('select', { 'aria-label': '아이콘을 바꿀 시설 유형' });
  const iconTypeInfo = el('p', { class: 'panel-hint' });
  const applyAllBtn = el('button', { type: 'button', class: 'btn btn-small', text: '이 유형 마커 모두 유형 아이콘으로 맞추기' });
  const typePicker = createIconPicker({
    onChange: (icon) => {
      markerEd.updateTypeIcon(iconTypeSelect.value, icon);
      renderMarkerList();
      renderIconTabInfo();
    },
    onRefresh: refreshIconFiles,
  });
  const usedFilesList = el('ul', { class: 'used-files' });
  const iconTabView = el('section', { class: 'panel-view', hidden: '' }, [
    el('div', { class: 'field' }, [el('span', { class: 'field-label', text: '시설 유형' }), iconTypeSelect]),
    iconTypeInfo,
    applyAllBtn,
    typePicker.element,
    el('div', { class: 'field' }, [
      el('span', { class: 'field-label', text: '웹사이트로 옮길 때 함께 옮길 아이콘 파일' }),
      usedFilesList,
      el('p', { class: 'panel-hint', text: 'public/icons 폴더를 통째로 함께 옮기면 됩니다. JSON에는 경로(icons/…)만 저장돼요.' }),
    ]),
  ]);

  // ── 구역 편집 화면
  const nameInput = el('input', { type: 'text', list: 'zone-name-examples', maxlength: '40', placeholder: '예: 플리마켓' });
  const datalist = el('datalist', { id: 'zone-name-examples' }, ZONE_NAME_EXAMPLES.map((n) => el('option', { value: n })));
  const fillColor = el('input', { type: 'color' });
  const fillOpacity = el('input', { type: 'range', min: '0', max: '1', step: '0.05' });
  const fillOpacityValue = el('span', { class: 'range-value' });
  const strokeColor = el('input', { type: 'color' });
  const strokeOpacity = el('input', { type: 'range', min: '0.1', max: '1', step: '0.05' });
  const strokeOpacityValue = el('span', { class: 'range-value' });
  const strokeWeight = el('input', { type: 'range', min: '1', max: '10', step: '1' });
  const strokeWeightValue = el('span', { class: 'range-value' });
  const doneBtn = el('button', { type: 'button', class: 'btn btn-primary', text: '편집 완료' });
  const deleteBtn = el('button', { type: 'button', class: 'btn btn-danger', text: '구역 삭제' });

  const field = (label, ...controls) => el('label', { class: 'field' }, [el('span', { class: 'field-label', text: label }), ...controls]);
  // 선·화살표는 채우기가 없어서, 채우기 항목은 영역 도형에서만 보입니다.
  const typeBadge = el('span', { class: 'type-badge' });
  const fillColorField = field('채우기 색', fillColor);
  const fillOpacityField = field('채우기 투명도', el('div', { class: 'range-row' }, [fillOpacity, fillOpacityValue]));
  const strokeColorField = field('테두리 색', strokeColor);
  const strokeOpacityField = field('테두리 투명도', el('div', { class: 'range-row' }, [strokeOpacity, strokeOpacityValue]));
  const strokeWeightField = field('테두리 두께', el('div', { class: 'range-row' }, [strokeWeight, strokeWeightValue]));
  const editHint = el('p', { class: 'panel-hint' });
  const editView = el('section', { class: 'panel-view', hidden: '' }, [
    el('h2', {}, [document.createTextNode('구역 편집 '), typeBadge]),
    field('구역 이름', nameInput, datalist),
    el('div', { class: 'field-row' }, [fillColorField, strokeColorField]),
    fillOpacityField,
    strokeOpacityField,
    strokeWeightField,
    editHint,
    el('div', { class: 'panel-actions' }, [doneBtn, deleteBtn]),
  ]);

  // ── 시설 마커 편집 화면
  const mkBadge = el('span', { class: 'type-badge' });
  const mkName = el('input', { type: 'text', maxlength: '40', placeholder: '예: 의료실 1' });
  const mkType = el('select', { 'aria-label': '시설 유형' });
  const mkCoords = el('code', { class: 'icon-path' });
  const mkId = el('code', { class: 'icon-path' });
  const mkUseType = el('input', { type: 'radio', name: 'mk-icon-mode', value: 'type' });
  const mkUseOwn = el('input', { type: 'radio', name: 'mk-icon-mode', value: 'own' });
  const mkUseTypeLabel = el('span');
  const markerPicker = createIconPicker({
    onChange: (icon) => {
      const id = markerEd.getSelectedId();
      if (id) markerEd.updateMarker(id, { icon });
      renderMarkerList();
    },
    onRefresh: refreshIconFiles,
  });
  const mkApplyToType = el('button', { type: 'button', class: 'btn btn-small' });
  const mkOwnBox = el('div', { class: 'own-icon-box', hidden: '' }, [markerPicker.element, mkApplyToType]);
  const mkDone = el('button', { type: 'button', class: 'btn btn-primary', text: '편집 완료' });
  const mkDelete = el('button', { type: 'button', class: 'btn btn-danger', text: '마커 삭제' });
  const markerEditView = el('section', { class: 'panel-view', hidden: '' }, [
    el('h2', {}, [document.createTextNode('시설 편집 '), mkBadge]),
    field('이름', mkName),
    field('시설 유형', mkType),
    el('div', { class: 'field' }, [
      el('span', { class: 'field-label', text: '아이콘' }),
      el('label', { class: 'check-row' }, [mkUseType, mkUseTypeLabel]),
      el('label', { class: 'check-row' }, [mkUseOwn, el('span', { text: '이 마커만 다른 아이콘 쓰기' })]),
    ]),
    mkOwnBox,
    el('div', { class: 'field' }, [
      el('span', { class: 'field-label', text: '위치·고유 ID (아이콘을 바꿔도 그대로)' }),
      mkCoords,
      mkId,
    ]),
    el('p', { class: 'panel-hint', text: '지도에서 마커를 끌면 위치가 바뀌어요. 동그라미 가운데가 실제 위치(기준점)예요.' }),
    el('div', { class: 'panel-actions' }, [mkDone, mkDelete]),
  ]);

  const panel = el('aside', { class: 'admin-panel', 'aria-label': '구역·시설 관리' }, [
    tabs,
    listView,
    markerListView,
    iconTabView,
    editView,
    markerEditView,
  ]);
  const adminLayer = el('div', { class: 'admin-layer' }, [toolbar, hint, panel, toast]);
  main.append(adminLayer);

  const previewBadge = el('div', { class: 'preview-badge', hidden: '' }, [
    document.createTextNode('방문객 미리보기 · 구역 로고·번호는 끌어서 옮길 수 있어요'),
  ]);
  main.append(previewBadge);

  // ── 화면 갱신 도우미
  let toastTimer = 0;
  function showToast(text, kind = 'info') {
    toast.textContent = text;
    toast.dataset.kind = kind;
    toast.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
      toast.hidden = true;
    }, 4000);
  }

  let lastSavedAt = local.savedAt || null;
  function renderStatus() {
    if (dirty) {
      status.textContent = '● 저장 안 된 변경 있음';
      status.dataset.state = 'dirty';
    } else if (lastSavedAt) {
      status.textContent = `저장됨 (${formatTime(lastSavedAt)})`;
      status.dataset.state = 'saved';
    } else {
      status.textContent = '아직 저장한 작업 없음';
      status.dataset.state = 'none';
    }
  }

  function markDirty() {
    dirty = true;
    renderStatus();
  }

  // 지금 보여 줄 패널 화면을 정합니다: 구역 편집 > 시설 편집 > 선택한 탭
  function renderPanel() {
    const zoneEditing = Boolean(editor && editor.getEditingId());
    const markerEditing = Boolean(markerEd && markerEd.getSelectedId());
    const showTabs = !zoneEditing && !markerEditing;
    tabs.hidden = !showTabs;
    editView.hidden = !zoneEditing;
    markerEditView.hidden = zoneEditing || !markerEditing;
    listView.hidden = !showTabs || activeTab !== 'zones';
    markerListView.hidden = !showTabs || activeTab !== 'markers';
    iconTabView.hidden = !showTabs || activeTab !== 'icons';
    [tabZones, tabMarkers, tabIcons].forEach((t) => {
      const on = t.dataset.tab === activeTab;
      t.classList.toggle('is-active', on);
      t.setAttribute('aria-selected', String(on));
    });
    if (showTabs) {
      if (activeTab === 'zones') renderList();
      if (activeTab === 'markers') renderMarkerList();
      if (activeTab === 'icons') renderIconTab();
    }
    renderTabCounts();
  }

  function renderTabCounts() {
    tabZones.textContent = `구역 (${editor ? editor.getZones().length : 0})`;
    tabMarkers.textContent = `시설 (${markerEd ? markerEd.getMarkers().length : 0})`;
  }

  function renderList() {
    const zones = editor.getZones();
    list.replaceChildren(
      ...zones.map((z) => {
        const info = SHAPE_TYPES[z.type] || SHAPE_TYPES.polygon;
        const swatch = el('span', { class: 'swatch', title: info.label, text: info.icon });
        if (isLineType(z.type)) {
          swatch.classList.add('is-line');
          swatch.style.color = z.style.strokeColor;
        } else {
          swatch.style.background = z.style.fillColor;
          swatch.style.borderColor = z.style.strokeColor;
        }
        const btn = el('button', { type: 'button', class: 'zone-item' }, [
          swatch,
          el('span', { class: 'zone-name', text: z.name }),
          el('span', { class: 'zone-type', text: info.label }),
        ]);
        btn.addEventListener('click', () => {
          markerEd.cancelPlacing();
          markerEd.deselect();
          editor.select(z.id);
        });
        return el('li', {}, [btn]);
      })
    );
    empty.hidden = zones.length > 0;
    renderTabCounts();
  }

  function renderMarkerList() {
    if (!markerEd) return;
    const markers = markerEd.getMarkers();
    const types = markerEd.getTypes();
    markerList.replaceChildren(
      ...markers.map((m) => {
        const icon = iconForMarker(m, types);
        const thumb = el('img', { class: 'marker-thumb', src: iconUrl(icon.src), alt: '' });
        const btn = el('button', { type: 'button', class: 'zone-item' }, [
          thumb,
          el('span', { class: 'zone-name', text: m.name }),
          el('span', { class: 'zone-type', text: `${typeLabel(types, m.type)}${m.icon ? ' · 개별' : ''}` }),
        ]);
        btn.addEventListener('click', () => {
          markerEd.select(m.id);
          map.panTo(new kakao.maps.LatLng(m.lat, m.lng));
        });
        return el('li', {}, [btn]);
      })
    );
    markerEmpty.hidden = markers.length > 0;
    renderTabCounts();
  }

  function fillTypeOptions(select, selected) {
    const types = markerEd.getTypes();
    select.replaceChildren(...types.map((t) => el('option', { value: t.id, text: t.label })));
    if (selected && types.some((t) => t.id === selected)) select.value = selected;
  }

  function renderIconTab() {
    const current = iconTypeSelect.value;
    fillTypeOptions(iconTypeSelect, current);
    const t = markerEd.getTypes().find((x) => x.id === iconTypeSelect.value);
    if (t) typePicker.setIcon(t.icon);
    renderIconTabInfo();
    renderUsedFiles();
  }

  function renderIconTabInfo() {
    const typeId = iconTypeSelect.value;
    const ofType = markerEd.getMarkers().filter((m) => m.type === typeId);
    const own = ofType.filter((m) => m.icon).length;
    iconTypeInfo.textContent =
      `이 유형 마커 ${ofType.length}개` +
      (own ? ` 중 ${own}개는 개별 아이콘을 쓰고 있어요. 아래 버튼으로 모두 유형 아이콘으로 맞출 수 있어요.` : '에 아래 아이콘이 적용돼요.');
    applyAllBtn.hidden = own === 0;
  }

  async function renderUsedFiles() {
    const files = usedIconFiles(markerEd.getMarkers(), markerEd.getTypes());
    const rows = await Promise.all(
      files.map(async (f) => {
        const ok = await checkImage(iconUrl(f));
        return el('li', { class: ok ? '' : 'is-missing' }, [
          el('code', { text: `public/${f}` }),
          document.createTextNode(ok ? '' : ' — 파일 없음'),
        ]);
      })
    );
    usedFilesList.replaceChildren(...rows);
  }

  function fillMarkerForm(m) {
    const types = markerEd.getTypes();
    fillTypeOptions(mkType, m.type);
    mkBadge.textContent = typeLabel(types, m.type);
    mkName.value = m.name;
    mkCoords.textContent = `위도 ${m.lat.toFixed(6)}, 경도 ${m.lng.toFixed(6)}`;
    mkId.textContent = `ID ${m.id}`;
    mkUseTypeLabel.textContent = `${typeLabel(types, m.type)} 유형 아이콘 쓰기 (같은 유형 전체와 같이)`;
    mkUseType.checked = !m.icon;
    mkUseOwn.checked = Boolean(m.icon);
    mkOwnBox.hidden = !m.icon;
    mkApplyToType.textContent = `이 아이콘을 ${typeLabel(types, m.type)} 유형 전체에 적용`;
    if (m.icon) markerPicker.setIcon(m.icon);
  }

  async function refreshIconFiles() {
    forgetImageChecks();
    iconFiles = await fetchIconFiles();
    typePicker.setFiles(iconFiles);
    markerPicker.setFiles(iconFiles);
    if (markerEd) {
      markerEd.refreshIcons();
      renderMarkerList();
      renderUsedFiles();
    }
    showToast(`public/icons 폴더에서 아이콘 파일 ${iconFiles.length}개를 찾았어요.`);
  }

  // ── 구역 편집기 연결
  const editor = createZoneEditor(map, start.zones, {
    onChange() {
      markDirty();
      renderList();
    },
    onSelect(zone, info) {
      if (zone) {
        if (markerEd) {
          markerEd.cancelPlacing();
          markerEd.deselect();
        }
        fillEditForm(zone);
        if (info && info.isNew) {
          nameInput.focus();
          nameInput.select();
          showToast(`${(SHAPE_TYPES[zone.type] || SHAPE_TYPES.polygon).label}이(가) 만들어졌어요. 이름과 색을 정해 주세요.`);
        }
      }
      renderPanel();
    },
    onDrawingChange(type) {
      const isDrawing = Boolean(type);
      shapeButtons.forEach((b) => b.classList.toggle('is-active', b.dataset.type === type));
      cancelBtn.hidden = !isDrawing;
      hint.hidden = !isDrawing;
      if (isDrawing) renderDrawHint(type);
      adminLayer.classList.toggle('is-drawing', isDrawing);
    },
    onMessage(text) {
      showToast(text, 'warn');
    },
    // 마커를 놓는 중이면, 구역 위를 클릭해도 그 자리에 마커를 놓습니다.
    onPlainClick(zone, mouseEvent) {
      if (markerEd && markerEd.isPlacing()) {
        markerEd.placeAt(mouseEvent.latLng);
        return true;
      }
      return false;
    },
  });

  // ── 시설 마커 편집기 연결
  const markerEd = createMarkerEditor(
    map,
    { markers: start.markers || [], facilityTypes: start.facilityTypes || [] },
    {
      onChange() {
        markDirty();
        renderMarkerList();
      },
      onSelect(m, info) {
        if (m) {
          editor.cancelDrawing();
          editor.finishEditing();
          fillMarkerForm(m);
          if (info && info.isNew) {
            mkName.focus();
            mkName.select();
            showToast('시설 마커를 놓았어요. 이름을 정해 주세요. 마커를 끌어 위치를 옮길 수 있어요.');
          }
        }
        renderPanel();
      },
      onPlacingChange(typeId) {
        const placing = Boolean(typeId);
        placeBtn.classList.toggle('is-active', placing);
        placeCancelBtn.hidden = !placing;
        hint.hidden = !placing;
        if (placing) renderPlaceHint(typeId);
        adminLayer.classList.toggle('is-drawing', placing);
      },
    }
  );

  fillTypeOptions(placeTypeSelect);
  fillTypeOptions(iconTypeSelect);
  renderPanel();
  renderStatus();
  if (local.error) showToast(local.error, 'error');
  else if (local.data) {
    showToast(`임시 저장된 구역 ${local.data.zones.length}개, 시설 마커 ${local.data.markers.length}개를 불러왔어요.`);
  }
  fetchIconFiles().then((files) => {
    iconFiles = files;
    typePicker.setFiles(files);
    markerPicker.setFiles(files);
  });

  // ── 구역 편집 패널 입력
  function fillEditForm(zone) {
    const line = isLineType(zone.type);
    const info = SHAPE_TYPES[zone.type] || SHAPE_TYPES.polygon;
    typeBadge.textContent = `${info.icon} ${info.label}`;
    fillColorField.hidden = line;
    fillOpacityField.hidden = line;
    strokeColorField.querySelector('.field-label').textContent = line ? '선 색' : '테두리 색';
    strokeOpacityField.querySelector('.field-label').textContent = line ? '선 투명도' : '테두리 투명도';
    strokeWeightField.querySelector('.field-label').textContent = line ? '선 두께' : '테두리 두께';
    editHint.textContent = EDIT_HINTS[zone.type] || EDIT_HINTS.polygon;

    nameInput.value = zone.name;
    fillColor.value = zone.style.fillColor;
    strokeColor.value = zone.style.strokeColor;
    fillOpacity.value = String(zone.style.fillOpacity);
    strokeOpacity.value = String(zone.style.strokeOpacity);
    strokeWeight.value = String(zone.style.strokeWeight);
    fillOpacityValue.textContent = `${Math.round(zone.style.fillOpacity * 100)}%`;
    strokeOpacityValue.textContent = `${Math.round(zone.style.strokeOpacity * 100)}%`;
    strokeWeightValue.textContent = `${zone.style.strokeWeight}px`;
  }

  const editingId = () => editor.getEditingId();
  nameInput.addEventListener('input', () => {
    if (!editingId()) return;
    editor.updateZone(editingId(), { name: nameInput.value.trim() || '이름 없는 구역' });
  });
  fillColor.addEventListener('input', () => editingId() && editor.updateZone(editingId(), { style: { fillColor: fillColor.value } }));
  strokeColor.addEventListener('input', () => editingId() && editor.updateZone(editingId(), { style: { strokeColor: strokeColor.value } }));
  fillOpacity.addEventListener('input', () => {
    const v = Number(fillOpacity.value);
    fillOpacityValue.textContent = `${Math.round(v * 100)}%`;
    if (editingId()) editor.updateZone(editingId(), { style: { fillOpacity: v } });
  });
  strokeOpacity.addEventListener('input', () => {
    const v = Number(strokeOpacity.value);
    strokeOpacityValue.textContent = `${Math.round(v * 100)}%`;
    if (editingId()) editor.updateZone(editingId(), { style: { strokeOpacity: v } });
  });
  strokeWeight.addEventListener('input', () => {
    const v = Number(strokeWeight.value);
    strokeWeightValue.textContent = `${v}px`;
    if (editingId()) editor.updateZone(editingId(), { style: { strokeWeight: v } });
  });
  doneBtn.addEventListener('click', () => editor.finishEditing());
  deleteBtn.addEventListener('click', () => {
    const id = editingId();
    if (!id) return;
    const zone = editor.getZones().find((z) => z.id === id);
    if (!window.confirm(`'${zone ? zone.name : '이 구역'}'을(를) 삭제할까요?\n[저장]을 누르기 전까지는 임시 저장본에 남아 있어요.`)) return;
    editor.deleteZone(id);
    showToast('구역을 삭제했어요. [저장]을 누르면 반영돼요.');
  });

  // ── 시설 마커 편집 패널 입력
  const selectedMarker = () => {
    const id = markerEd.getSelectedId();
    return id ? markerEd.getMarkers().find((m) => m.id === id) : null;
  };
  mkName.addEventListener('input', () => {
    const m = selectedMarker();
    if (m) markerEd.updateMarker(m.id, { name: mkName.value.trim() || '이름 없는 시설' });
  });
  mkType.addEventListener('change', () => {
    const m = selectedMarker();
    if (!m) return;
    markerEd.updateMarker(m.id, { type: mkType.value });
    fillMarkerForm(selectedMarker());
  });
  mkUseType.addEventListener('change', () => {
    const m = selectedMarker();
    if (!m || !mkUseType.checked) return;
    markerEd.updateMarker(m.id, { icon: null });
    fillMarkerForm(selectedMarker());
    renderMarkerList();
  });
  mkUseOwn.addEventListener('change', () => {
    const m = selectedMarker();
    if (!m || !mkUseOwn.checked) return;
    // 지금 유형 아이콘을 복사해서 이 마커만의 아이콘으로 시작합니다.
    markerEd.updateMarker(m.id, { icon: { ...iconForMarker(m, markerEd.getTypes()) } });
    fillMarkerForm(selectedMarker());
    renderMarkerList();
  });
  mkApplyToType.addEventListener('click', () => {
    const m = selectedMarker();
    if (!m || !m.icon) return;
    const types = markerEd.getTypes();
    const count = markerEd.getMarkers().filter((x) => x.type === m.type).length;
    if (!window.confirm(`이 아이콘을 '${typeLabel(types, m.type)}' 유형 마커 ${count}개 모두에 적용할까요?\n(같은 유형 마커의 개별 아이콘은 없어져요. 위치·이름·ID는 그대로예요)`)) return;
    markerEd.updateTypeIcon(m.type, m.icon);
    const n = markerEd.applyTypeIconToAll(m.type);
    fillMarkerForm(selectedMarker());
    renderMarkerList();
    showToast(`'${typeLabel(types, m.type)}' 유형 마커 ${count}개에 같은 아이콘을 적용했어요.${n ? '' : ''}`);
  });
  mkDone.addEventListener('click', () => markerEd.deselect());
  mkDelete.addEventListener('click', () => {
    const m = selectedMarker();
    if (!m) return;
    if (!window.confirm(`'${m.name}' 마커를 삭제할까요?\n[저장]을 누르기 전까지는 임시 저장본에 남아 있어요.`)) return;
    markerEd.deleteMarker(m.id);
    showToast('마커를 삭제했어요. [저장]을 누르면 반영돼요.');
  });

  // ── 아이콘 탭 입력
  iconTypeSelect.addEventListener('change', renderIconTab);
  applyAllBtn.addEventListener('click', () => {
    const typeId = iconTypeSelect.value;
    const types = markerEd.getTypes();
    const n = markerEd.applyTypeIconToAll(typeId);
    renderIconTab();
    renderMarkerList();
    showToast(`'${typeLabel(types, typeId)}' 마커 ${n}개의 개별 아이콘을 없애고 유형 아이콘으로 맞췄어요.`);
  });

  // ── 도구 막대 동작 (도형 버튼은 위에서 연결)
  cancelBtn.addEventListener('click', () => editor.cancelDrawing());
  placeBtn.addEventListener('click', () => {
    editor.cancelDrawing();
    editor.finishEditing();
    markerEd.startPlacing(placeTypeSelect.value);
  });
  placeCancelBtn.addEventListener('click', () => markerEd.cancelPlacing());
  document.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape' || mode !== 'admin') return;
    if (editor.isDrawing()) editor.cancelDrawing();
    if (markerEd.isPlacing()) markerEd.cancelPlacing();
  });

  const currentState = () => ({
    zones: editor.getZones(),
    markers: markerEd.getMarkers(),
    facilityTypes: markerEd.getTypes(),
  });

  saveBtn.addEventListener('click', () => {
    try {
      lastSavedAt = saveLocal(currentState());
      dirty = false;
      renderStatus();
      showToast('이 브라우저에 저장했어요. 백업은 [JSON 내보내기]로 따로 받아 두세요.');
    } catch (err) {
      console.error('[festival-map] 저장 실패', err);
      showToast('저장하지 못했어요. 브라우저 저장 공간이 꽉 찼거나 막혀 있을 수 있어요. JSON 내보내기로 백업해 주세요.', 'error');
    }
  });

  exportBtn.addEventListener('click', () => {
    const state = currentState();
    const { fileName, iconFiles: used } = downloadJson(state);
    showToast(
      `구역 ${state.zones.length}개, 시설 마커 ${state.markers.length}개를 ${fileName} 파일로 내려받았어요. ` +
        `웹사이트로 옮길 땐 public/icons 폴더(아이콘 ${used.length}개 사용 중)도 함께 옮기세요.`
    );
  });

  importBtn.addEventListener('click', () => fileInput.click());
  fileInput.addEventListener('change', async () => {
    const file = fileInput.files && fileInput.files[0];
    fileInput.value = '';
    if (!file) return;
    try {
      const data = await readJsonFile(file);
      const cur = currentState();
      const lines = [`구역 ${cur.zones.length}개 → ${data.zones.length}개`];
      if (data.hasMarkers) lines.push(`시설 마커 ${cur.markers.length}개 → ${data.markers.length}개 (아이콘 설정도 파일 내용으로)`);
      else lines.push(`이 파일에는 시설 마커 정보가 없어서, 지금 마커 ${cur.markers.length}개와 아이콘 설정은 그대로 둬요.`);
      const hasAny = cur.zones.length > 0 || cur.markers.length > 0;
      if (hasAny && !window.confirm(`'${file.name}' 내용으로 바꿀까요?\n\n${lines.join('\n')}`)) return;
      editor.setZones(data.zones);
      if (data.hasMarkers) markerEd.setAll({ markers: data.markers, facilityTypes: data.facilityTypes });
      fillTypeOptions(placeTypeSelect, placeTypeSelect.value);
      markDirty();
      renderPanel();
      showToast(
        `구역 ${data.zones.length}개${data.hasMarkers ? `, 시설 마커 ${data.markers.length}개` : ''}를 가져왔어요. 새로고침 후에도 남기려면 [저장]을 눌러 주세요.`
      );
    } catch (err) {
      console.error('[festival-map] 가져오기 실패', err);
      showToast(`가져오지 못했어요: ${err.message}`, 'error');
    }
  });

  // 저장하지 않고 창을 닫거나 새로고침하면 한 번 묻습니다.
  window.addEventListener('beforeunload', (e) => {
    if (!dirty) return;
    e.preventDefault();
    e.returnValue = '';
  });

  // ── 모드 전환
  function setMode(next) {
    if (next === mode) return;
    mode = next;
    adminBtn.classList.toggle('is-active', mode === 'admin');
    visitorBtn.classList.toggle('is-active', mode === 'visitor');
    if (mode === 'visitor') {
      const state = currentState();
      editor.hide();
      markerEd.hide();
      adminLayer.hidden = true;
      previewBadge.hidden = false;
      visitorView = startVisitorView(map, state, {
        onMoveZonePin(zone, pos) {
          editor.updateZone(zone.id, { labelPos: pos });
          showToast(`"${zone.name}" 로고 위치를 옮겼어요. [관리자 편집]으로 돌아가 [저장]을 눌러 주세요.`);
        },
      });
    } else {
      if (visitorView) visitorView.destroy();
      visitorView = null;
      previewBadge.hidden = true;
      adminLayer.hidden = false;
      editor.show();
      markerEd.show();
      renderPanel();
    }
  }
  adminBtn.addEventListener('click', () => setMode('admin'));
  visitorBtn.addEventListener('click', () => setMode('visitor'));

  // 개발 중 확인용
  window.__festivalEditor = editor;
  window.__festivalMarkers = markerEd;
  return { editor, markerEd, setMode };
}
