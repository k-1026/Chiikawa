"""공식 표정·자세 시트(흰 배경 원페이지)에서 포즈를 하나씩 오려 assets_v06/poses/ 에 투명 PNG 로 저장하고 poses.json 을 만든다.
- 캐릭터를 새로 그리지 않는다. 승인된 시트의 그림을 그대로 오려 낸다(배경·그림자·글씨만 제거).
사용: python3 tools/build_pose_library.py [--repo 저장소폴더]"""
import argparse, json, os, sys
from collections import deque
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend' / 'vendor'))
import numpy as np
from PIL import Image, ImageFilter

CAPTION_BANDS = {  # 시트 그림에서 확인한 이름 글씨의 세로 범위(px). 이 띠는 통째로 지운다.
    'oejimong': [(366, 402), (670, 704), (967, 1001)],
    'daekimi': [(396, 436), (692, 730), (1030, 1070)],
}
SHEETS = {
    'oejimong': ('캐릭터 정보/character/외지몽_성체_표정자세_확정본_v01/외지몽_성체_표정자세_확정레퍼런스_v01.png', '확정 (사용자 확정 2026-11-18)',
                 ['기본 미소', '활짝 웃음', '깜짝 놀람', '시무룩·서운', '반가워 꼬리붕붕', '궁금해 가우뚱', '쿵쿵 발견', '손! 칭찬해', '놀아줘 앞발쪽', '신나서 발라당', '으르렁 경계', '졸려 꾸벅']),
    'daekimi': ('캐릭터 정보/character/대키미_성체_표정자세_v01/대키미_성체_표정자세_레퍼런스_v01.png', '시트 v01 (승인 상태 확인 필요)',
                ['별빛 냥인사', '골골 행복', '꾹꾹 좋아', '냥당당', '사냥 집중', '깜짝 꼬리펑', '하악! 저리가', '삐짐 꼬리탁', '눈치 슬쩍', '애교 부비부비', '메롱 장난', '졸려 식빵']),
}
# 축제 굿즈에 쓰기 어려운 분위기는 자동 추천에서 뺀다 (경계·삐짐·시무룩). 잠자는 포즈는 수면 관련 품목에만 쓴다.
DEBUG = bool(os.environ.get('POSE_DEBUG'))
AVOID = {'시무룩·서운', '으르렁 경계', '하악! 저리가', '삐짐 꼬리탁', '사냥 집중'}
SLEEP = {'졸려 꾸벅', '졸려 식빵'}


def label(mask):
    """4-연결 성분 라벨링 (scipy 없이). 반환: labels(int32), 개수"""
    h, w = mask.shape
    lab = np.zeros((h, w), np.int32)
    n = 0
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not lab[y, x]:
                n += 1
                dq = deque([(y, x)]); lab[y, x] = n
                while dq:
                    cy, cx = dq.popleft()
                    for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not lab[ny, nx]:
                            lab[ny, nx] = n; dq.append((ny, nx))
    return lab, n


def dilate(arr, k):
    im = Image.fromarray((arr * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(k))
    return np.array(im) > 127


def extract(sheet_path, names, outdir, prefix):
    bands = CAPTION_BANDS[prefix]
    im = Image.open(sheet_path).convert('RGB')
    a = np.array(im).astype(np.int16)
    H, W = a.shape[:2]
    mx, mn = a.max(2), a.min(2)
    obj = ((mx - mn) > 17) | (mx < 110)          # 채도가 있거나 어두운 픽셀 = 캐릭터·글씨 (옅은 회색 그림자는 제외)
    obj[: int(H * 0.11), :] = False              # 제목 영역 제외
    for y0_, y1_ in bands:
        obj[y0_:y1_, :] = False                  # 이름 글씨 띠 제외
    S = 2
    small = obj[::S, ::S]
    lab, n = label(dilate(small, 5))
    areas = np.bincount(lab.ravel(), minlength=n + 1); areas[0] = 0
    boxes = {}
    for i in range(1, n + 1):
        ys, xs = np.where(lab == i)
        boxes[i] = (xs.min(), ys.min(), xs.max(), ys.max(), len(xs))
    big = [i for i in boxes if boxes[i][4] >= 0.22 * areas.max()]
    # 위→아래, 왼→오른 순서
    cy = {i: (boxes[i][1] + boxes[i][3]) / 2 for i in big}
    rows = sorted(big, key=lambda i: cy[i]); R = len(names) // 4
    ordered = []
    for r in range(R):
        grp = sorted(rows[r * 4:(r + 1) * 4], key=lambda i: boxes[i][0]); ordered += grp
    outdir.mkdir(parents=True, exist_ok=True)
    result = []
    for k, bi in enumerate(ordered):
        bx0, by0, bx1, by1, _ = boxes[bi]
        group = [bi]
        for j in boxes:
            if j == bi or j in big: continue
            x0, y0, x1, y1, ar = boxes[j]
            near = x1 >= bx0 - 30 and x0 <= bx1 + 30 and y1 >= by0 - 30 and y0 <= by1 + 8
            w_, h_ = x1 - x0 + 1, y1 - y0 + 1
            caption = (y0 >= by1 - 6) or (w_ >= 20 and h_ <= 18 and w_ / h_ >= 1.8)   # 이름 글씨: 몸 아래에 있거나 가로로 긴 글줄 모양
            if near and not caption:
                group.append(j)
        region = np.isin(lab, group)
        # 구멍(눈 속 하이라이트 등) 메우기: 테두리에서 닿지 않는 배경 성분
        inv, m = label(~region)
        edge = set(np.unique(np.concatenate([inv[0], inv[-1], inv[:, 0], inv[:, -1]])))
        # 구멍 메우기: 눈 속 흰 반짝임처럼 '어두운 픽셀로 둘러싸인 작은 구멍'만 메운다. 꼬리·다리 사이 배경 틈은 투명하게 둔다.
        inv, m = label(~region)
        edge = set(np.unique(np.concatenate([inv[0], inv[-1], inv[:, 0], inv[:, -1]])))
        dark_small = (mx < 110)[::S, ::S][: region.shape[0], : region.shape[1]]
        darkish_small = (mx < 170)[::S, ::S][: region.shape[0], : region.shape[1]]   # 파랑·초록·분홍 몸색은 밝아서(>=200) 제외된다
        sat_small = (mx - mn)[::S, ::S][: region.shape[0], : region.shape[1]]
        filled = region.copy()
        for t in range(1, m + 1):
            if t in edge: continue
            hole = (inv == t)
            if hole.sum() > 1500: continue
            ring = dilate(hole, 5) & ~hole
            dark_ring = darkish_small[ring].mean() if ring.sum() else 0
            whiteish = sat_small[hole].mean() < 8          # 순수한 흰색에 가까움 = 배경 틈이거나 눈 속 반짝임
            if DEBUG and prefix == 'daekimi' and k == 0 and hole.sum() > 30: print('  구멍', int(hole.sum()), '둘레어두움 %.2f' % dark_ring, '흰색' if whiteish else '색있음', 'edge' if t in edge else '')
            if dark_ring > 0.15 or not whiteish: filled |= hole   # 눈 속 반짝임(어두운 테두리)·크림색 부분은 메우고, 몸 사이 흰 틈은 투명하게 둔다
        full_region = np.kron(filled, np.ones((S, S), bool))[:H, :W]
        alpha = full_region.copy()
        # 흰 배경·옅은 그림자는 '가장자리 근처'에서만 지운다. 몸 안쪽의 흰 반짝임·크림색 주둥이는 그대로 둔다.
        inner = np.array(Image.fromarray((full_region * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(15))) > 127
        edge_zone = full_region & ~inner
        alpha &= ~(((mn > 238) & ~obj) & edge_zone)
        alpha &= ~((((mx - mn) < 14) & (mx > 175) & (mx < 246) & ~obj) & edge_zone)
        ys, xs = np.where(alpha)
        y1_ = ys.max()
        # 발밑 바닥 그림자(옅은 푸른 회색)는 몸 아래쪽 띠에서 지운다. 발·젤리패드는 채도가 높아 남는다.
        foot_band = np.zeros_like(alpha); foot_band[max(0, y1_ - 30): y1_ + 1, :] = True
        alpha &= ~(foot_band & ((mx - mn) < 34) & (mn > 185) & (mx >= 110))
        ys, xs = np.where(alpha)
        x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
        pad = 6
        box = (int(max(0, x0 - pad)), int(max(0, y0 - pad)), int(min(W, x1 + pad + 1)), int(min(H, y1 + pad + 1)))
        a_crop = alpha[box[1]:box[3], box[0]:box[2]].copy()
        rgb_crop = a[box[1]:box[3], box[0]:box[2]]
        # 마무리: 최종 결과 안의 작은 구멍 중 어두운 눈에 둘러싸인 것(눈 속 반짝임)을 메운다
        hl, hn = label(~a_crop)
        hedge = set(np.unique(np.concatenate([hl[0], hl[-1], hl[:, 0], hl[:, -1]])))
        dark_c = rgb_crop.max(2) < 170
        for t in range(1, hn + 1):
            if t in hedge: continue
            hole = (hl == t)
            if hole.sum() > 2500: continue
            ring = dilate(hole, 5) & ~hole
            if ring.sum() and dark_c[ring].mean() > 0.35: a_crop |= hole
        am = Image.fromarray((a_crop * 255).astype(np.uint8))
        am = am.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.9))   # 흰 테두리 제거 + 가장자리 부드럽게
        rgba = im.crop(box).convert('RGBA'); rgba.putalpha(am)
        pid = '%s_%02d' % (prefix, k + 1)
        rgba.save(outdir / (pid + '.png'))
        name = names[k]
        use = 'avoid' if name in AVOID else 'sleep' if name in SLEEP else 'general'
        result.append({'id': pid, 'char': prefix, 'name': name, 'use': use, 'size': list(rgba.size)})
        print(pid, name, rgba.size, use)
    return result


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--repo', default=None); a = ap.parse_args()
    repo = Path(a.repo) if a.repo else ROOT.parents[1]
    out = ROOT / 'assets_v06' / 'poses'
    lib = {'note': '공식 표정·자세 시트에서 그대로 오린 포즈입니다. 생김새·색은 원본과 같습니다.', 'poses': []}
    for char, (rel, status, names) in SHEETS.items():
        sheet = repo / rel
        res = extract(sheet, names, out, char)
        for r in res:
            r['sheet'] = rel; r['status'] = status
        lib['poses'] += res
    (out / 'poses.json').write_text(json.dumps(lib, ensure_ascii=False, indent=1), encoding='utf-8')
    print('저장:', out)
