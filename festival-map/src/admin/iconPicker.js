// 아이콘 고르기 화면 조각입니다. (개발 서버 전용)
// - public/icons 폴더의 PNG·SVG 중에서 고르기
// - 표시 크기(가로·세로 px), 기준점(Anchor) 조정
// - 미리보기: 빨간 점이 실제 위치(위도·경도)에 닿는 기준점
import { ANCHOR_PRESETS, iconUrl } from '../markers/markerData.js';
import { checkImage } from '../markers/markerLayer.js';

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

// 개발 서버에 public/icons 폴더 목록을 물어봅니다.
export async function fetchIconFiles() {
  try {
    const res = await fetch('/__festival/icons', { cache: 'no-store' });
    if (!res.ok) return [];
    const data = await res.json();
    return Array.isArray(data.files) ? data.files : [];
  } catch (err) {
    return [];
  }
}

export function createIconPicker({ onChange, onRefresh }) {
  let icon = null;
  let files = [];
  let keepRatio = true;

  // 미리보기
  const previewImg = el('img', { alt: '' });
  const anchorDot = el('span', { class: 'anchor-dot', title: '기준점: 이 점이 지도 위 실제 위치에 닿아요' });
  const previewBox = el('div', { class: 'icon-preview-box' }, [previewImg, anchorDot]);
  const pathText = el('code', { class: 'icon-path' });
  const warn = el('p', { class: 'icon-warn', hidden: '' });
  const preview = el('div', { class: 'icon-preview' }, [previewBox, el('div', { class: 'icon-preview-info' }, [pathText, warn])]);

  // 파일 목록
  const grid = el('div', { class: 'icon-grid', role: 'listbox', 'aria-label': '아이콘 파일' });
  const refreshBtn = el('button', { type: 'button', class: 'btn btn-small', text: '목록 새로고침' });
  const gridHelp = el('p', {
    class: 'panel-hint',
    text: 'Figma 등에서 만든 PNG·SVG를 festival-map/public/icons 폴더에 넣고 [목록 새로고침]을 누르세요.',
  });

  // 크기
  const widthInput = el('input', { type: 'number', min: '8', max: '200', step: '1' });
  const heightInput = el('input', { type: 'number', min: '8', max: '200', step: '1' });
  const ratioCheck = el('input', { type: 'checkbox', checked: '' });
  const sizeRow = el('div', { class: 'size-row' }, [
    el('label', {}, [el('span', { text: '가로' }), widthInput]),
    el('span', { class: 'size-x', text: '×' }),
    el('label', {}, [el('span', { text: '세로' }), heightInput]),
    el('span', { class: 'size-unit', text: 'px' }),
  ]);
  const ratioLabel = el('label', { class: 'check-row' }, [ratioCheck, el('span', { text: '원본 비율 유지' })]);

  // 기준점
  const presetSelect = el('select', {}, [
    ...ANCHOR_PRESETS.map((p) => el('option', { value: p.id, text: p.label })),
    el('option', { value: 'custom', text: '직접 입력' }),
  ]);
  const ax = el('input', { type: 'number', min: '0', max: '100', step: '5' });
  const ay = el('input', { type: 'number', min: '0', max: '100', step: '5' });
  const anchorRow = el('div', { class: 'size-row' }, [
    el('label', {}, [el('span', { text: '가로 위치' }), ax]),
    el('label', {}, [el('span', { text: '세로 위치' }), ay]),
    el('span', { class: 'size-unit', text: '%' }),
  ]);

  const field = (label, ...controls) => el('div', { class: 'field' }, [el('span', { class: 'field-label', text: label }), ...controls]);
  const element = el('div', { class: 'icon-picker' }, [
    preview,
    field('아이콘 파일', grid, el('div', { class: 'grid-actions' }, [refreshBtn]), gridHelp),
    field('표시 크기', sizeRow, ratioLabel),
    field('기준점 (Anchor)', presetSelect, anchorRow),
  ]);

  function emit() {
    renderPreview();
    if (onChange) onChange({ ...icon });
  }

  async function renderPreview() {
    if (!icon) return;
    const url = iconUrl(icon.src);
    previewImg.src = url;
    previewImg.style.width = `${icon.width}px`;
    previewImg.style.height = `${icon.height}px`;
    previewBox.style.width = `${icon.width}px`;
    previewBox.style.height = `${icon.height}px`;
    anchorDot.style.left = `${icon.anchorX * icon.width}px`;
    anchorDot.style.top = `${icon.anchorY * icon.height}px`;
    pathText.textContent = icon.src || '(아이콘 없음)';
    const ok = icon.src ? await checkImage(url) : false;
    warn.hidden = ok;
    warn.textContent = icon.src
      ? `public/${icon.src} 파일을 찾을 수 없어요. 지도에는 회색 물음표 핀으로 보여요.`
      : '아이콘이 정해지지 않았어요.';
  }

  function renderGrid() {
    const list = [...files];
    if (icon && icon.src && !list.includes(icon.src)) list.unshift(icon.src); // 폴더에 없는 파일도 현재 값으로 표시
    grid.replaceChildren(
      ...list.map((src) => {
        const btn = el('button', { type: 'button', class: 'icon-option', title: src, role: 'option' }, [
          el('img', { src: iconUrl(src), alt: '' }),
          el('span', { text: src.replace(/^icons\//, '') }),
        ]);
        if (icon && icon.src === src) {
          btn.classList.add('is-selected');
          btn.setAttribute('aria-selected', 'true');
        }
        btn.addEventListener('click', () => pickFile(src));
        return btn;
      })
    );
    if (!list.length) grid.append(el('p', { class: 'panel-empty', text: 'public/icons 폴더에 아이콘 파일이 없어요.' }));
  }

  function renderInputs() {
    widthInput.value = String(icon.width);
    heightInput.value = String(icon.height);
    ax.value = String(Math.round(icon.anchorX * 100));
    ay.value = String(Math.round(icon.anchorY * 100));
    const preset = ANCHOR_PRESETS.find((p) => p.anchorX === icon.anchorX && p.anchorY === icon.anchorY);
    presetSelect.value = preset ? preset.id : 'custom';
  }

  // 새 파일을 고르면, '원본 비율 유지'일 때 가로는 그대로 두고 세로를 원본 비율에 맞춥니다.
  function pickFile(src) {
    icon = { ...icon, src };
    const img = new Image();
    img.onload = () => {
      if (keepRatio && img.naturalWidth && img.naturalHeight) {
        icon.height = Math.max(8, Math.min(200, Math.round((icon.width * img.naturalHeight) / img.naturalWidth)));
        renderInputs();
      }
      emit();
    };
    img.onerror = () => emit();
    img.src = iconUrl(src);
    renderGrid();
  }

  function clampInt(v, min, max, fallback) {
    const n = Math.round(Number(v));
    return Number.isFinite(n) ? Math.min(max, Math.max(min, n)) : fallback;
  }

  widthInput.addEventListener('change', () => {
    const w = clampInt(widthInput.value, 8, 200, icon.width);
    if (keepRatio && icon.width) icon.height = clampInt((w * icon.height) / icon.width, 8, 200, icon.height);
    icon.width = w;
    renderInputs();
    emit();
  });
  heightInput.addEventListener('change', () => {
    const h = clampInt(heightInput.value, 8, 200, icon.height);
    if (keepRatio && icon.height) icon.width = clampInt((h * icon.width) / icon.height, 8, 200, icon.width);
    icon.height = h;
    renderInputs();
    emit();
  });
  ratioCheck.addEventListener('change', () => {
    keepRatio = ratioCheck.checked;
  });
  presetSelect.addEventListener('change', () => {
    const p = ANCHOR_PRESETS.find((x) => x.id === presetSelect.value);
    if (!p) return;
    icon.anchorX = p.anchorX;
    icon.anchorY = p.anchorY;
    renderInputs();
    emit();
  });
  const onAnchorInput = () => {
    icon.anchorX = clampInt(ax.value, 0, 100, Math.round(icon.anchorX * 100)) / 100;
    icon.anchorY = clampInt(ay.value, 0, 100, Math.round(icon.anchorY * 100)) / 100;
    renderInputs();
    emit();
  };
  ax.addEventListener('change', onAnchorInput);
  ay.addEventListener('change', onAnchorInput);
  refreshBtn.addEventListener('click', () => onRefresh && onRefresh());

  return {
    element,
    setIcon(next) {
      icon = { ...next };
      renderInputs();
      renderGrid();
      renderPreview();
    },
    setFiles(next) {
      files = [...next];
      renderGrid();
      renderPreview();
    },
  };
}
