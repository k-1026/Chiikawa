"""저장소(main)의 문서를 AI가 참고하는 지식 DB(Supabase daesatu.knowledge_chunks)에 맞춘다.
- 저장소 안의 지정한 폴더(.md/.csv)를 조각내고, 내용이 바뀐 조각만 새로 임베딩한다(이미 있는 조각은 재사용).
- 저장소에서 사라진 문서의 조각은 DB에서도 지운다. → main 이 바뀔 때마다 한 번 돌리면 DB가 main 과 같아진다.

사용:  python3 tools/sync_knowledge_from_repo.py [--repo 저장소폴더] [--dirs 세부지침안,대사투] [--apply]
  --apply 가 없으면 무엇이 바뀔지(추가·삭제 건수)만 보여 준다.
환경변수: DATABASE_URL, GEMINI_API_KEY, EMBEDDING_MODEL, EMBEDDING_DIM  (로컬은 v06/.env, 자동 실행은 GitHub Secrets)
"""
import argparse, hashlib, json, os, re, sys, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend' / 'vendor'))
sys.path.insert(0, str(ROOT / 'ai_v06' / 'docs'))
import rgh  # 조각내기·임베딩 규칙을 기존 것과 똑같이 쓴다

EXTS = {'.md'}  # csv 는 표·좌표 원자료라 검색에 방해가 되어 뺀다
# 이름에 이 글자가 있으면 뺀다: 합본(내용 중복), 빈 양식, 작업 메모
SKIP = ('통합본', '묶음본', '_양식.md', '_품목시트_양식', '인수인계', 'README', '수정이력')
DEFAULT_DIRS = ['세부지침안', '대사투']


def nfc(s): return unicodedata.normalize('NFC', s)


def repo_root(p):
    p = Path(p).resolve()
    for d in [p, *p.parents]:
        if (d / '.git').exists():
            return d
    return p


def collect(repo, dirs):
    """[(source, file, relpath, text)] — 폴더 구조를 그대로 출처(source)로 쓴다."""
    out = []
    for d in dirs:
        base = repo / d
        if not base.is_dir():
            print('  (없는 폴더 건너뜀) %s' % d); continue
        for p in sorted(base.rglob('*')):
            if not p.is_file() or p.suffix.lower() not in EXTS:
                continue
            name = nfc(p.name)
            if any(k in name for k in SKIP):
                continue
            parts = [nfc(x) for x in p.relative_to(base).parts[:-1]]
            src = '/'.join([nfc(d)] + parts) if d != '세부지침안' else ('/'.join(parts) or '(루트)')
            out.append((src, name, nfc(p.relative_to(repo).as_posix()), nfc(p.read_text(encoding='utf-8'))))
    return out


def make_chunks(files):
    chunks = []
    for src, name, rel, text in files:
        for i, (heading, body) in enumerate(rgh.chunk_text(text)):
            h = hashlib.sha1(('%s|%s|%d|%s' % (src, name, i, body)).encode('utf-8')).hexdigest()[:20]
            chunks.append({'id': h, 'source': src, 'file': name, 'heading': heading, 'seq': i, 'text': body})
    return chunks


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', default=None, help='저장소 폴더(기본: 이 파일이 들어 있는 저장소)')
    ap.add_argument('--dirs', default=','.join(DEFAULT_DIRS))
    ap.add_argument('--apply', action='store_true')
    a = ap.parse_args()
    repo = repo_root(a.repo or ROOT)
    files = collect(repo, [x.strip() for x in a.dirs.split(',') if x.strip()])
    chunks = make_chunks(files)
    want = {c['id']: c for c in chunks}
    print(json.dumps({'repo': repo.name, 'files': len(files), 'chunks': len(chunks)}, ensure_ascii=False))

    import psycopg
    rgh.load_env()
    url = os.environ.get('DATABASE_URL')
    if not url:
        sys.exit('DATABASE_URL 이 없습니다.')
    with psycopg.connect(url, sslmode='require', connect_timeout=15) as con:
        con.execute((ROOT / 'supabase/002_knowledge.sql').read_text())
        have = {r[0] for r in con.execute('SELECT id FROM daesatu.knowledge_chunks').fetchall()}
        add = [want[i] for i in want if i not in have]
        drop = [i for i in have if i not in want]
        print(json.dumps({'DB에 있음': len(have), '추가할 조각': len(add), '지울 조각': len(drop)}, ensure_ascii=False))
        if not a.apply:
            print('(미리보기) --apply 를 붙이면 DB에 반영합니다.'); sys.exit(0)
        if add:
            emb = rgh.embed_texts(rgh.get_client(), [rgh.embed_input(c) for c in add], 'RETRIEVAL_DOCUMENT',
                                  partial_path=Path(os.environ.get('SYNC_PARTIAL', '/tmp/sync_partial.npy')))
            dim = emb.shape[1]
            with con.cursor() as cur:
                cur.executemany(
                    'INSERT INTO daesatu.knowledge_chunks(id,source,file,heading,seq,text,embedding) '
                    'VALUES(%s,%s,%s,%s,%s,%s,%s::extensions.vector) ON CONFLICT (id) DO NOTHING',
                    [(c['id'], c['source'], c['file'], c['heading'], c['seq'], c['text'],
                      '[' + ','.join('%.7g' % float(v) for v in emb[i]) + ']') for i, c in enumerate(add)])
        if drop:
            con.execute('DELETE FROM daesatu.knowledge_chunks WHERE id = ANY(%s)', (drop,))
        n = con.execute('SELECT count(*) FROM daesatu.knowledge_chunks').fetchone()[0]
        print(json.dumps({'완료': True, 'DB 조각 수': n}, ensure_ascii=False))
        try:
            os.remove(os.environ.get('SYNC_PARTIAL', '/tmp/sync_partial.npy'))
        except OSError:
            pass
