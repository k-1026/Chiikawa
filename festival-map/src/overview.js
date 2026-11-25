import { isArea, zoneNumbers, zonePosition } from './zones/zonePosition.js';
import { iconForMarker, iconUrl } from './markers/markerData.js';
import { ZONE_LOGOS } from './config.js';
import background from './overview-background.json';

const zoneColors = {
  '사투리한마당': '#A7D9C9',
  '7구 맛집거리': '#E9878B',
  '밥묵자 존': '#F6D481',
  '운영부스': '#88AFD7',
  '플리마켓': '#A4CE81',
  '굿즈샵·이벤트 부스': '#F2B679',
  '10미 포장마차': '#8C54B4',
};

const displayNames = { '밥묵자 존': '밥 묵자! 존' };

// The park data contains the amphitheater footprint and its front lawn as separate areas.
const amphitheaterAreas = [
  { kind: 'green', coordinate: [35.851216, 128.55565] },
  { kind: 'building', coordinate: [35.851133, 128.555942] },
].map(({ kind, coordinate }) => background.find((feature) =>
  feature.kind === kind && feature.closed && feature.points.some(([lat, lng]) =>
    lat === coordinate[0] && lng === coordinate[1]
  )
)).filter(Boolean).map(({ points }) => points.map(([lat, lng]) => ({ lat, lng })));

async function loadMapImage(src) {
  const image = new Image();
  const url = iconUrl(src);
  if (new URL(url, location.href).origin !== location.origin) image.crossOrigin = 'anonymous';
  image.src = url;
  await image.decode();
  return { image, url };
}

function contains(path, [x, y]) {
  let inside = false;
  for (let i = 0, j = path.length - 1; i < path.length; j = i++) {
    const [ax, ay] = path[i];
    const [bx, by] = path[j];
    if ((ay > y) !== (by > y) && x < ax + (bx - ax) * (y - ay) / (by - ay)) inside = !inside;
  }
  return inside;
}

function outline(zone) {
  if (zone.path) return zone.path;
  if (zone.bounds) {
    const { sw, ne } = zone.bounds;
    return [sw, { lat: sw.lat, lng: ne.lng }, ne, { lat: ne.lat, lng: sw.lng }];
  }
  const { center, radius, rx = radius, ry = radius } = zone;
  const metersPerLng = 111320 * Math.cos(center.lat * Math.PI / 180);
  return Array.from({ length: 64 }, (_, index) => {
    const angle = index * Math.PI / 32;
    return {
      lat: center.lat + Math.sin(angle) * ry / 111320,
      lng: center.lng + Math.cos(angle) * rx / metersPerLng,
    };
  });
}

function traceRoundedPolygon(ctx, points, preserveNarrowStrip) {
  const distance = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1]);
  const vertices = points.filter((point, i) => i === 0 || distance(point, points[i - 1]) > 0.1);
  if (vertices.length > 3 && distance(vertices[0], vertices.at(-1)) < 0.1) vertices.pop();
  if (vertices.length < 3) {
    points.forEach(([x, y], i) => i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y));
    return;
  }
  const corners = vertices.filter((point, i) => {
    const previous = vertices[(i + vertices.length - 1) % vertices.length];
    const next = vertices[(i + 1) % vertices.length];
    const span = distance(previous, next);
    if (span === 0) return true;
    const area = Math.abs((next[0] - previous[0]) * (point[1] - previous[1]) -
      (next[1] - previous[1]) * (point[0] - previous[0]));
    const projection = (point[0] - previous[0]) * (next[0] - previous[0]) +
      (point[1] - previous[1]) * (next[1] - previous[1]);
    return area / span >= 2.5 || projection < 0 || projection > span * span;
  });
  const path = !preserveNarrowStrip && corners.length >= 3 ? corners : vertices;
  const towards = (a, b, fraction) => a.map((value, axis) => value + (b[axis] - value) * fraction);
  path.forEach((point, i) => {
    const previous = path[(i + path.length - 1) % path.length];
    const next = path[(i + 1) % path.length];
    const before = distance(point, previous);
    const after = distance(point, next);
    const radius = Math.min(preserveNarrowStrip ? 3 : 10, before * 0.28, after * 0.28);
    const entry = towards(point, previous, before ? radius / before : 0);
    const exit = towards(point, next, after ? radius / after : 0);
    if (i === 0) ctx.moveTo(...entry);
    else ctx.lineTo(...entry);
    ctx.quadraticCurveTo(...point, ...exit);
  });
}

export async function showOverview({ zones, markers, facilityTypes }) {
  const section = document.getElementById('overview');
  if (!zones.length) return;
  const numbers = zoneNumbers(zones);
  const isMainArea = (zone) => zone.name === '사투리한마당';
  const isFoodStallStrip = (zone) => zone.id === 'zone-mwoqkm1p4825';
  const paintOrder = (zone) => isFoodStallStrip(zone) ? 2 : isMainArea(zone) ? 0 : 1;
  const shapes = [...zones].sort((a, b) => paintOrder(a) - paintOrder(b))
    .flatMap((zone) => (isMainArea(zone) && amphitheaterAreas.length === 2 ? amphitheaterAreas : [outline(zone)])
      .map((path) => ({ zone, path })));
  const access = markers.filter(({ type }) => type === 'gate' || type === 'barricade');
  const points = [...shapes.flatMap(({ path }) => path), ...access];
  const west = Math.min(...points.map(({ lng }) => lng));
  const north = Math.max(...points.map(({ lat }) => lat));
  const lonScale = Math.cos(north * Math.PI / 180);
  const width = (Math.max(...points.map(({ lng }) => lng)) - west) * lonScale;
  const height = north - Math.min(...points.map(({ lat }) => lat));
  const margin = 126;
  const scale = 1180 / Math.max(width, height);
  const canvas = document.createElement('canvas');
  canvas.width = Math.ceil(width * scale + 2 * margin);
  canvas.height = Math.ceil(height * scale + 2 * margin);
  const ctx = canvas.getContext('2d');
  const xy = ({ lat, lng }) => [margin + (lng - west) * lonScale * scale, margin + (north - lat) * scale];

  ctx.fillStyle = '#edf1e4';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.lineJoin = 'round';
  ctx.lineCap = 'round';
  const palette = {
    green: '#d1e3ba', water: '#a7d4db', building: '#ccc5b7', road: '#fdfbf5', path: '#f9f3e0',
  };
  for (const kind of ['green', 'water', 'building', 'road', 'path']) {
    for (const feature of background.filter((entry) => entry.kind === kind)) {
      ctx.beginPath();
      feature.points.forEach(([lat, lng], i) => {
        const position = xy({ lat, lng });
        if (i === 0) ctx.moveTo(...position);
        else ctx.lineTo(...position);
      });
      if (feature.closed && kind !== 'road' && kind !== 'path') {
        ctx.closePath();
        ctx.fillStyle = palette[kind];
        ctx.fill();
      } else if (kind === 'road' || kind === 'path') {
        ctx.strokeStyle = kind === 'road' ? '#d6d4c8' : '#e2dfcf';
        ctx.lineWidth = kind === 'road' ? 13 : 6;
        ctx.stroke();
        ctx.strokeStyle = palette[kind];
        ctx.lineWidth = kind === 'road' ? 10 : 4;
        ctx.stroke();
      }
    }
  }
  ctx.globalAlpha = 1;
  for (const { zone, path } of shapes) {
    const narrowStrip = isFoodStallStrip(zone);
    ctx.beginPath();
    if (zone.type === 'polygon' || isMainArea(zone)) {
      traceRoundedPolygon(ctx, path.map(xy), narrowStrip);
    } else {
      ctx.moveTo(...xy(path[0]));
      path.slice(1).forEach((point) => ctx.lineTo(...xy(point)));
    }
    if (isArea(zone)) {
      ctx.closePath();
      ctx.fillStyle = zoneColors[zone.name] ?? zone.style.fillColor;
      ctx.fill();
      if (isMainArea(zone)) {
        const boundary = path.map(xy);
        ctx.save();
        ctx.clip();
        // Keep mapped through paths visible in the parent area. Detailed zones are painted above them.
        for (const feature of background.filter(({ kind, closed }) => kind === 'path' && !closed)) {
          const route = feature.points.map(([lat, lng]) => xy({ lat, lng }));
          if (contains(boundary, route[0]) || contains(boundary, route.at(-1)) ||
            !route.some((point) => contains(boundary, point))) continue;
          ctx.beginPath();
          ctx.moveTo(...route[0]);
          route.slice(1).forEach((point) => ctx.lineTo(...point));
          ctx.strokeStyle = '#FFF7EB';
          ctx.lineWidth = 7;
          ctx.stroke();
        }
        ctx.restore();
        ctx.beginPath();
        ctx.moveTo(...boundary[0]);
        boundary.slice(1).forEach((point) => ctx.lineTo(...point));
        ctx.closePath();
      }
    }
    ctx.globalAlpha = 1;
    ctx.strokeStyle = isArea(zone) ? (zoneColors[zone.name] ?? zone.style.fillColor) : zone.style.strokeColor;
    ctx.lineWidth = narrowStrip ? 2 : 2.5;
    ctx.stroke();
  }
  ctx.globalAlpha = 1;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.font = '800 28px sans-serif';
  const accessIcons = await Promise.all(access.map(async (marker) => {
    const icon = iconForMarker(marker, facilityTypes);
    const { image, url } = await loadMapImage(icon.src);
    const size = marker.type === 'gate' ? 54 : 42;
    const [x, y] = xy(marker);
    return { marker, image, url, size, left: x - size * icon.anchorX, top: y - size * icon.anchorY };
  }));
  const logoNames = [...numbers.keys()].filter((name) => ZONE_LOGOS[displayNames[name] ?? name]);
  const logos = new Map(await Promise.all(logoNames.map(async (name) => {
    const { src, width } = ZONE_LOGOS[displayNames[name] ?? name];
    const { image } = await loadMapImage(src);
    return [name, { image, width: width * 1.65 }];
  })));
  const occupied = accessIcons.map(({ left, top, size }) => ({
    left, top, right: left + size, bottom: top + size,
  }));
  const areas = shapes.filter(({ zone }) => isArea(zone)).map(({ zone, path }) => ({ zone, path: path.map(xy) }));
  const overlap = (a, b) => a.left < b.right + 6 && a.right > b.left - 6 &&
    a.top < b.bottom + 6 && a.bottom > b.top - 6;
  function badge(point, logo, color, area, anchors = [point]) {
    const [x, y] = xy(point);
    const logoHeight = logo.width * logo.image.height / logo.image.width;
    const width = logo.width + 14;
    const height = logoHeight + 8;
    function drawLogo(cx, cy) {
      ctx.save();
      ctx.shadowColor = '#202026';
      ctx.shadowBlur = 4;
      ctx.drawImage(logo.image, cx - logo.width / 2, cy - logoHeight / 2, logo.width, logoHeight);
      ctx.restore();
    }
    const inline = { left: x - width / 2, right: x + width / 2, top: y - height / 2, bottom: y + height / 2 };
    if (area && !isFoodStallStrip(area.zone) && !occupied.some((box) => overlap(inline, box))) {
      const checks = [[inline.left, inline.top], [inline.right, inline.top],
        [inline.left, inline.bottom], [inline.right, inline.bottom], [x, y]];
      const coversLabel = ({ zone, path }) => zone.id !== area.zone.id &&
        paintOrder(zone) >= paintOrder(area.zone) && checks.some((p) => contains(path, p));
      if (checks.every((p) => contains(area.path, p)) && !areas.some(coversLabel)) {
        occupied.push(inline);
        drawLogo(x, y);
        return;
      }
    }
    const candidates = [];
    for (const offset of [42, 80, 122, 166, 214]) {
      for (const [dx, dy] of [[0, -1], [1, 0], [0, 1], [-1, 0], [1, -1], [-1, -1], [1, 1], [-1, 1]]) {
        const left = Math.max(8, Math.min(canvas.width - width - 8, x + dx * (offset + width / 2) - width / 2));
        const top = Math.max(8, Math.min(canvas.height - height - 8, y + dy * offset - height / 2));
        candidates.push({ left, top, right: left + width, bottom: top + height });
      }
    }
    const box = candidates.find((candidate) => !occupied.some((other) => overlap(candidate, other))) || candidates[0];
    occupied.push(box);
    const middleX = box.left + width / 2;
    const middleY = box.top + height / 2;
    for (const anchor of anchors) {
      const [ax, ay] = xy(anchor);
      const dx = ax - middleX;
      const dy = ay - middleY;
      const edge = Math.min(1, 1 / Math.max(Math.abs(dx) / (width / 2), Math.abs(dy) / (height / 2)));
      ctx.beginPath();
      ctx.moveTo(ax, ay);
      ctx.lineTo(middleX + dx * edge, middleY + dy * edge);
      ctx.strokeStyle = '#fff';
      ctx.lineWidth = 6;
      ctx.stroke();
      ctx.strokeStyle = color;
      ctx.lineWidth = 2.5;
      ctx.stroke();
      ctx.beginPath();
      ctx.arc(ax, ay, 4, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.fill();
    }
    drawLogo(middleX, middleY);
  }
  const labelOrder = areas.filter((area, index) =>
    area.zone.id !== areas[index - 1]?.zone.id
  ).reverse();
  const foodStreetName = '7구 맛집거리';
  const foodStreet = labelOrder.filter(({ zone }) => zone.name === foodStreetName);
  if (foodStreet.length > 1 && logos.has(foodStreetName)) {
    const anchors = foodStreet.map(({ zone }) => zonePosition(zone));
    const middle = {
      lat: anchors.reduce((sum, point) => sum + point.lat, 0) / anchors.length,
      lng: anchors.reduce((sum, point) => sum + point.lng, 0) / anchors.length,
    };
    badge(middle, logos.get(foodStreetName), foodStreet[0].zone.style.strokeColor, null, anchors);
  }
  labelOrder.forEach((area) => {
    const { zone } = area;
    if (zone.name === foodStreetName && foodStreet.length > 1) return;
    const logo = logos.get(zone.name);
    if (logo) badge(zone.labelPos ?? zonePosition(zone), logo, zone.style.strokeColor, area);
  });
  for (const { image, left, top, size } of accessIcons) {
    ctx.drawImage(image, left, top, size, size);
  }

  ctx.textAlign = 'left';
  ctx.fillStyle = '#263d30';
  ctx.font = '800 34px sans-serif';
  ctx.fillText('대사투! 페스티벌 지도', 28, 40);
  ctx.font = '600 18px sans-serif';
  ctx.fillText('두류공원', 29, 68);
  ctx.textAlign = 'right';
  ctx.font = '600 14px sans-serif';
  ctx.fillText('© OpenStreetMap contributors · openstreetmap.org/copyright', canvas.width - 20, canvas.height - 18);

  const image = section.querySelector('img');
  const png = await new Promise((resolve) => canvas.toBlob(resolve, 'image/png'));
  if (!png) throw new Error('PNG encoding failed');
  image.src = URL.createObjectURL(png);
  section.querySelector('.overview-download').href = image.src;
  section.querySelector('.overview-enlarge').href = image.src;
  const legend = section.querySelector('ul');
  for (const name of numbers.keys()) {
    const item = document.createElement('li');
    item.style.setProperty('--legend-color', zoneColors[name] ?? zones.find((zone) => zone.name === name).style.fillColor);
    item.textContent = displayNames[name] ?? name;
    legend.append(item);
  }
  for (const [type, label] of [['gate', '축제 출입로'], ['barricade', '차량 통제']]) {
    const accessIcon = accessIcons.find(({ marker }) => marker.type === type);
    if (!accessIcon) continue;
    const item = document.createElement('li');
    item.className = 'map-legend-icon';
    const icon = document.createElement('img');
    icon.src = accessIcon.url;
    icon.alt = '';
    item.append(icon, label);
    legend.append(item);
  }
  section.hidden = false;
}
