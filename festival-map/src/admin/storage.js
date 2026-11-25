// 관리자 편집용 저장 기능입니다. (개발 서버에서만 쓰임)
// - localStorage: 지금 쓰는 브라우저에만 남는 임시 작업 보관함
// - JSON 파일: 따로 백업하거나 다른 컴퓨터로 옮길 수 있는 파일
// 저장 내용: 구역(도형) + 시설 마커 + 시설 유형별 아이콘 설정 (src/mapData.js)
import { toMapFile, parseMapFile } from '../mapData.js';

const STORAGE_KEY = 'festival-map:zones:v1'; // 예전 작업을 그대로 이어 쓰기 위해 이름은 바꾸지 않습니다.

// 저장된 작업을 읽습니다. 없으면 data: null, 망가져 있으면 이유를 담아 돌려줍니다.
export function loadLocal() {
  let raw;
  try {
    raw = localStorage.getItem(STORAGE_KEY);
  } catch (err) {
    return { data: null, error: '이 브라우저에서는 임시 저장소(localStorage)를 쓸 수 없습니다.' };
  }
  if (!raw) return { data: null, savedAt: null };
  try {
    const json = JSON.parse(raw);
    return { data: parseMapFile(json), savedAt: json.savedAt || null };
  } catch (err) {
    return { data: null, error: `임시 저장된 작업을 읽지 못했습니다: ${err.message}` };
  }
}

// 현재 작업을 브라우저에 임시 저장합니다. 실패하면 오류를 냅니다.
export function saveLocal(state) {
  const data = toMapFile(state);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  return data.savedAt;
}

function timestamp() {
  const d = new Date();
  const p = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}-${p(d.getHours())}${p(d.getMinutes())}`;
}

// 전체 데이터를 JSON 파일로 내려받게 합니다.
export function downloadJson(state) {
  const data = toMapFile(state);
  const text = JSON.stringify(data, null, 2);
  const blob = new Blob([text], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `daesape-zones-${timestamp()}.json`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  return { fileName: a.download, iconFiles: data.iconFiles };
}

// 사용자가 고른 JSON 파일을 읽습니다. 반환 모양은 parseMapFile과 같습니다.
export async function readJsonFile(file) {
  const text = await file.text();
  let data;
  try {
    data = JSON.parse(text);
  } catch (err) {
    throw new Error('JSON 파일 형식이 아닙니다. 내보내기로 만든 파일인지 확인해 주세요.');
  }
  return parseMapFile(data);
}
