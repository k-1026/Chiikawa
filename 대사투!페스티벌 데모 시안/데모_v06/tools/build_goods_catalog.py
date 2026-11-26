"""팀의 D03 품목 시트(세부지침안/D파트v1/D03_품목별수치/*/..._시트.md)에서 굿즈 계획서에 쓸 표를 뽑아
goods_catalog_v06.json 으로 저장한다. 시트가 바뀌면 이 도구를 다시 돌려 최신 값을 반영한다.
사용: python3 tools/build_goods_catalog.py [--repo 저장소폴더]"""
import argparse, glob, json, re, sys, unicodedata
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
ITEMS = {'D0301': 'keyring', 'D0302': 'sticker', 'D0303': 'headband', 'D0304': 'magnet', 'D0305': 'ecobag', 'D0306': 'tshirt', 'D0307': 'eyemask', 'D0308': 'tumbler'}

def nfc(s): return unicodedata.normalize('NFC', s)

def section(text, num):
    m = re.search(r'^## %d\.[^\n]*\n(.*?)(?=^## \d+\.|\Z)' % num, text, re.S | re.M)
    return m.group(1) if m else ''

def first_table(block):
    rows = []
    started = False
    for line in block.split('\n'):
        if line.strip().startswith('|'):
            started = True
            cells = [c.strip() for c in line.strip().strip('|').split('|')]
            if all(re.fullmatch(r':?-{2,}:?', c) for c in cells): continue
            rows.append(cells)
        elif started:
            break
    return rows

def clean(c):
    c = re.sub(r'\*\*|`', '', c)
    c = re.sub(r'\[(.*?)\]\((.*?)\)', r'\1', c)
    return c.strip()

def tables(block, limit=3):
    out, cur = [], []
    for line in block.split('\n'):
        if line.strip().startswith('|'):
            cells = [clean(c) for c in line.strip().strip('|').split('|')]
            if all(re.fullmatch(r':?-{2,}:?', c) for c in cells): continue
            cur.append(cells)
        elif cur:
            out.append(cur); cur = []
    if cur: out.append(cur)
    return out[:limit]

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--repo', default=None); a = ap.parse_args()
    repo = Path(a.repo) if a.repo else ROOT.parents[1]
    base = repo / '세부지침안' / 'D파트v1' / 'D03_품목별수치'
    out = {}
    for code, key in ITEMS.items():
        files = glob.glob(str(base / (code + '_*') / '*_시트.md'))
        if not files: print('없음', code); continue
        text = nfc(Path(files[0]).read_text(encoding='utf-8'))
        name = re.search(r'^# D0?3?-?0?\d*[\.\s]*([^\n]*?) 시트', text, re.M)
        purpose = ''
        t1 = first_table(section(text, 1))
        for r in t1:
            if r and r[0].strip('* ') == '상품 목적': purpose = clean(r[1])
        out[key] = {
            'code': code, 'sheet': nfc(Path(files[0]).name),
            'purpose': purpose,
            'fixed_change_ban': [[clean(c) for c in r] for r in first_table(section(text, 3))],
            'faces': [[clean(c) for c in r] for r in first_table(section(text, 4))],
            'spec': [[clean(c) for c in r] for r in first_table(section(text, 5))],
        }
        print(code, key, 'spec행', len(out[key]['spec']), 'faces행', len(out[key]['faces']), '목적' if purpose else '목적없음')
    (ROOT / 'goods_catalog_v06.json').write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
    print('저장:', ROOT / 'goods_catalog_v06.json')
