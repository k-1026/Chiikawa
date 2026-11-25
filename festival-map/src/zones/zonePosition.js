import { isLineType } from './zoneData.js';

export function isArea(zone) {
  return !isLineType(zone.type);
}

// Pick the midpoint of a wide interior horizontal slice, including for concave polygons.
export function zonePosition(zone) {
  if (zone.labelPos) return zone.labelPos;
  if (zone.center) return zone.center;
  if (zone.bounds) {
    const { sw, ne } = zone.bounds;
    return { lat: (sw.lat + ne.lat) / 2, lng: (sw.lng + ne.lng) / 2 };
  }

  const path = zone.path;
  const min = Math.min(...path.map((p) => p.lat));
  const max = Math.max(...path.map((p) => p.lat));
  let best = path[0];
  let width = 0;
  for (let sample = 0; sample < 24; sample++) {
    const lat = min + (max - min) * (sample + 0.5) / 24;
    const crossings = [];
    path.forEach((a, index) => {
      const b = path[(index + 1) % path.length];
      if ((a.lat > lat) !== (b.lat > lat)) {
        crossings.push(a.lng + (b.lng - a.lng) * (lat - a.lat) / (b.lat - a.lat));
      }
    });
    crossings.sort((a, b) => a - b);
    for (let i = 0; i + 1 < crossings.length; i += 2) {
      const span = crossings[i + 1] - crossings[i];
      if (span > width) {
        width = span;
        best = { lat, lng: (crossings[i + 1] + crossings[i]) / 2 };
      }
    }
  }
  return best;
}

export function zoneNumbers(zones) {
  const numbers = new Map();
  for (const { name } of zones.filter(isArea)) {
    if (!numbers.has(name)) numbers.set(name, numbers.size + 1);
  }
  return numbers;
}
