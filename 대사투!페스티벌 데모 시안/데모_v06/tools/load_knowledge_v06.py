"""지침 문서 조각(chunks.json)과 임베딩(embeddings.npy)을 Supabase 표 daesatu.knowledge_chunks 로 올린다.
사용: python3 tools/load_knowledge_v06.py [--index 폴더] [--apply]   (DATABASE_URL 은 환경변수)
--apply 가 없으면 건수만 확인한다. 이미 데이터가 있으면 덮어쓰지 않고 멈춘다(--replace 로 비우고 다시 올림)."""
import argparse, json, os, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend' / 'vendor'))
DEFAULT = Path('/Users/seunghui/Desktop/대외활동/CJ AI x AX/실습자료/1118 먼크이성 실습/Chiikawa-main/docs/rag_index')

def read_npy(path):
    import struct
    raw = path.read_bytes()
    hl = struct.unpack('<H', raw[8:10])[0]
    header = raw[10:10 + hl].decode('latin1')
    shape = eval(header.split("'shape':")[1].split('}')[0].strip().rstrip(','))
    data = struct.unpack('<%df' % (shape[0] * shape[1]), raw[10 + hl:10 + hl + shape[0] * shape[1] * 4])
    return shape, data

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--index', type=Path, default=DEFAULT); ap.add_argument('--apply', action='store_true'); ap.add_argument('--replace', action='store_true')
    a = ap.parse_args()
    chunks = json.loads((a.index / 'chunks.json').read_text(encoding='utf-8'))
    (n, d), flat = read_npy(a.index / 'embeddings.npy')
    assert n == len(chunks), 'chunk/embedding count mismatch'
    print(json.dumps({'chunks': n, 'dim': d, 'apply': a.apply}))
    if not a.apply: sys.exit(0)
    import psycopg
    with psycopg.connect(os.environ['DATABASE_URL'], sslmode='require', connect_timeout=15) as con:
        con.execute((ROOT / 'supabase/002_knowledge.sql').read_text())
        have = con.execute('SELECT count(*) FROM daesatu.knowledge_chunks').fetchone()[0]
        if have and not a.replace: raise SystemExit('이미 %d건이 있어 중단합니다(--replace 로 다시 올림).' % have)
        if have: con.execute('TRUNCATE daesatu.knowledge_chunks')
        with con.cursor() as cur:
            cur.executemany('INSERT INTO daesatu.knowledge_chunks(id,source,file,heading,seq,text,embedding) VALUES(%s,%s,%s,%s,%s,%s,%s::extensions.vector)',
                [(str(c['id']), c.get('source', ''), c['file'], c.get('heading', ''), int(c.get('seq', 0)), c['text'],
                  '[' + ','.join('%.7g' % v for v in flat[i * d:(i + 1) * d]) + ']') for i, c in enumerate(chunks)])
        got = con.execute('SELECT count(*) FROM daesatu.knowledge_chunks').fetchone()[0]
        assert got == n, 'row count mismatch'
        print(json.dumps({'loaded': got}))
