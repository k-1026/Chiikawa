# -*- coding: utf-8 -*-
"""kb 스키마 적재 스크립트 (Supabase Postgres + Storage).

기본은 사전 점검(dry-run)이다. DB에 쓰려면 --apply 를 명시해야 한다.
이 스크립트는 어떤 행도 지우지 않는다(DELETE/TRUNCATE/DROP 없음). 재실행하면 같은 ID 행을 갱신(upsert)한다.

환경변수(비밀값은 코드·파일에 쓰지 말 것):
  SUPABASE_DB_URL            Postgres 연결 문자열(service role 권한 DB 사용자). --apply, --check-db 에 필요
  SUPABASE_URL               https://<project>.supabase.co  (--upload-originals, --verify-storage 에 필요)
  SUPABASE_SERVICE_ROLE_KEY  Storage 업로드·확인용 키

사용 예:
  python -I database/load_kb.py                       # 사전 점검만(오프라인, DB 연결 없음)
  python -I database/load_kb.py --check-db            # DB 연결해 현재 건수·충돌 예상만 확인(쓰기 없음)
  python -I database/load_kb.py --apply               # 적재(한 트랜잭션). 잘못된 행이 있으면 중단
  python -I database/load_kb.py --apply --allow-partial  # 잘못된 행은 오류 파일로 빼고 나머지 적재
  python -I database/load_kb.py --upload-originals    # originals/ 파일을 Storage 버킷에 업로드(덮어쓰기)
  python -I database/load_kb.py --verify-storage      # Storage 파일을 내려받아 SHA-256 대조
"""
import argparse
import csv
import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

PKG = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PKG, "data")  # CSV 위치
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validate_package  # noqa: E402

PACKAGE_NAME = "kimseunghee_00_개요_원문DB"
BUCKET = "research-originals"

# 적재 순서 = FK 의존 순서
# (CSV 파일, 대상 테이블, 기본키, 타입 지정)
INT, NUM, BOOL, DATE = "int", "numeric", "bool", "date"
TABLES = [
    ("source_documents.csv", "kb.source_documents", "source_id", {"published_date": DATE, "accessed_at": DATE}),
    ("md_documents.csv", "kb.md_documents", "md_id", {"written_date": DATE}),
    ("source_sections.csv", "kb.source_sections", "section_id", {"order_no": INT}),
    ("knowledge_chunks.csv", "kb.knowledge_chunks", "chunk_id",
     {"order_no": INT, "char_count": INT, "text_is_excerpt": BOOL}),
    ("chunk_links.csv", "kb.chunk_links", "link_id", {}),
    ("md_claims.csv", "kb.md_claims", "claim_id", {"is_external": BOOL, "evidence_count": INT}),
    ("evidence_links.csv", "kb.evidence_links", "link_id", {"published_date": DATE, "accessed_at": DATE}),
    ("domain_figures.csv", "kb.domain_figures", "record_id",
     {"value_numeric": NUM, "base_year": INT, "period_start": DATE, "period_end": DATE}),
    ("domain_places.csv", "kb.domain_places", "place_id", {"list_order": INT}),
    ("operating_rules.csv", "kb.operating_rules", "rule_id", {}),
    ("review_issues.csv", "kb.review_issues", "issue_id", {}),
]
# 자기참조(parent_section_id)는 같은 표 안이라 부모 먼저 오도록 정렬
SELF_PARENT = {"kb.source_sections": "parent_section_id"}

# DB 쪽 FK 검사 쿼리(적재 후)
ORPHAN_CHECKS = [
    ("md_documents.source_id", "select count(*) from kb.md_documents m left join kb.source_documents s using (source_id) where m.source_id is not null and s.source_id is null"),
    ("source_sections.parent", "select count(*) from kb.source_sections a left join kb.source_sections p on p.section_id = a.parent_section_id where a.parent_section_id is not null and p.section_id is null"),
    ("knowledge_chunks.source_id", "select count(*) from kb.knowledge_chunks c left join kb.source_documents s using (source_id) where s.source_id is null"),
    ("knowledge_chunks.block", "select count(*) from kb.knowledge_chunks c left join kb.source_sections b on b.section_id = c.source_block_id where b.section_id is null"),
    ("evidence_links.claim_id", "select count(*) from kb.evidence_links e left join kb.md_claims m using (claim_id) where m.claim_id is null"),
    ("evidence_links.chunk_id", "select count(*) from kb.evidence_links e left join kb.knowledge_chunks c using (chunk_id) where e.chunk_id is not null and c.chunk_id is null"),
    ("domain_figures.chunk_id", "select count(*) from kb.domain_figures f left join kb.knowledge_chunks c using (chunk_id) where f.chunk_id is not null and c.chunk_id is null"),
    ("chunk_links", "select count(*) from kb.chunk_links l left join kb.knowledge_chunks a on a.chunk_id = l.from_chunk_id left join kb.knowledge_chunks b on b.chunk_id = l.to_chunk_id where a.chunk_id is null or b.chunk_id is null"),
]


def read_csv(name):
    with open(os.path.join(DATA_DIR, name), encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def convert(value, typ):
    if value is None or value == "":
        return None
    if typ == INT:
        return int(value)
    if typ == NUM:
        float(value)  # 형식 검사
        return value  # Postgres numeric 으로 문자열 전달(정밀도 보존)
    if typ == BOOL:
        if value not in ("true", "false"):
            raise ValueError(f"boolean 아님: {value}")
        return value == "true"
    if typ == DATE:
        datetime.strptime(value, "%Y-%m-%d")
        return value
    return value


def prepare(errors_dir):
    """CSV 를 읽어 타입 변환. 잘못된 행은 오류 목록으로 분리."""
    prepared, bad = {}, {}
    for fname, table, pk, types in TABLES:
        rows, errs = [], []
        for i, r in enumerate(read_csv(fname), start=2):
            try:
                if not r.get(pk):
                    raise ValueError(f"{pk} 비어 있음")
                rows.append({k: convert(v, types.get(k)) for k, v in r.items()})
            except Exception as e:  # noqa: BLE001
                errs.append(dict(r, _line=i, _error=str(e)))
        if table in SELF_PARENT:
            col = SELF_PARENT[table]
            rows.sort(key=lambda x: (x[col] is not None, x.get("level") == "block"))
        prepared[table] = rows
        bad[table] = errs
    total_bad = sum(len(v) for v in bad.values())
    if total_bad:
        os.makedirs(errors_dir, exist_ok=True)
        for table, errs in bad.items():
            if errs:
                path = os.path.join(errors_dir, f"{table.split('.')[-1]}_errors.csv")
                with open(path, "w", encoding="utf-8", newline="") as f:
                    w = csv.DictWriter(f, fieldnames=list(errs[0].keys()))
                    w.writeheader()
                    w.writerows(errs)
                print(f"  [오류 행] {table}: {len(errs)}건 → {path}")
    return prepared, bad, total_bad


def connect():
    url = os.environ.get("SUPABASE_DB_URL")
    if not url:
        sys.exit("SUPABASE_DB_URL 환경변수가 없습니다.")
    try:
        import psycopg  # type: ignore
    except ImportError:
        sys.exit('psycopg 가 없습니다. 먼저 설치하세요: pip install "psycopg[binary]"')
    return psycopg.connect(url)


def counts(cur):
    out = {}
    for _, table, _, _ in TABLES:
        cur.execute(f"select count(*) from {table}")
        out[table] = cur.fetchone()[0]
    return out


def upsert(cur, table, pk, rows):
    if not rows:
        return 0
    cols = list(rows[0].keys())
    updates = ", ".join(f"{c} = excluded.{c}" for c in cols if c != pk)
    sql = (f"insert into {table} ({', '.join(cols)}) values ({', '.join(['%s'] * len(cols))}) "
           f"on conflict ({pk}) do update set {updates}")
    cur.executemany(sql, [tuple(r[c] for c in cols) for r in rows])
    return len(rows)


def storage_request(method, key, data=None, content_type="application/octet-stream"):
    base = os.environ.get("SUPABASE_URL", "").rstrip("/")
    secret = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not base or not secret:
        sys.exit("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY 환경변수가 없습니다.")
    req = urllib.request.Request(f"{base}/storage/v1/object/{BUCKET}/{key}", data=data, method=method)
    req.add_header("Authorization", f"Bearer {secret}")
    req.add_header("apikey", secret)
    if data is not None:
        req.add_header("Content-Type", content_type)
        req.add_header("x-upsert", "true")
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def storage_key(row):
    # storage_object_path = "research-originals/<key>"
    return row["storage_object_path"].split("/", 1)[1]


def upload_originals():
    rows = [r for r in read_csv("source_documents.csv") if r["original_file_path"]]
    for r in rows:
        path = os.path.join(PKG, r["original_file_path"])
        ctype = "text/markdown; charset=utf-8" if path.endswith(".md") else "text/html; charset=utf-8"
        with open(path, "rb") as f:
            storage_request("POST", storage_key(r), f.read(), ctype)
        print(f"  업로드: {r['storage_object_path']}")
    print(f"업로드 {len(rows)}건 완료")


def verify_storage():
    rows = [r for r in read_csv("source_documents.csv") if r["original_file_path"]]
    bad = 0
    for r in rows:
        try:
            body = storage_request("GET", storage_key(r))
            ok = hashlib.sha256(body).hexdigest() == r["original_sha256"]
        except urllib.error.HTTPError as e:
            ok = False
            print(f"  [없음] {r['storage_object_path']} ({e.code})")
        if not ok:
            bad += 1
            print(f"  [불일치] {r['source_id']} {r['storage_object_path']}")
    print(f"Storage 대조: {len(rows) - bad}/{len(rows)} 일치")
    return bad == 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="DB 에 실제로 적재")
    ap.add_argument("--allow-partial", action="store_true", help="잘못된 행을 빼고 적재")
    ap.add_argument("--check-db", action="store_true", help="DB 연결해 건수만 확인(쓰기 없음)")
    ap.add_argument("--upload-originals", action="store_true")
    ap.add_argument("--verify-storage", action="store_true")
    ap.add_argument("--errors-dir", default=os.path.join(PKG, "load_errors"))
    args = ap.parse_args()

    print("1) 패키지 검증")
    if not validate_package.run(quiet=True):
        sys.exit("패키지 검증 실패 — database/validate_package.py 출력을 확인하세요.")
    print("  통과")

    print("2) 행 변환·형식 검사")
    prepared, _, total_bad = prepare(args.errors_dir)
    for _, table, _, _ in TABLES:
        print(f"  {table}: 적재 대상 {len(prepared[table])}행")
    if total_bad and args.apply and not args.allow_partial:
        sys.exit(f"잘못된 행 {total_bad}건 — 적재 중단(--allow-partial 로 제외 후 적재 가능)")

    if args.upload_originals:
        print("3) Storage 업로드")
        upload_originals()
    if args.verify_storage:
        print("3) Storage 대조")
        if not verify_storage():
            sys.exit(1)

    if not (args.apply or args.check_db):
        print("\n사전 점검 완료(DB 연결·쓰기 없음). 적재하려면 --apply")
        return

    conn = connect()
    with conn:
        cur = conn.cursor()
        before = counts(cur)
        print("4) 적재 전 건수", json.dumps(before, ensure_ascii=False))
        # 패키지에 없는데 DB에만 있는 ID(삭제하지 않고 보고만)
        for fname, table, pk, _ in TABLES:
            ids = [r[pk] for r in prepared[table]]
            cur.execute(f"select count(*) from {table} where not ({pk} = any(%s))", (ids,))
            extra = cur.fetchone()[0]
            if extra:
                print(f"  [참고] {table}: 패키지에 없는 기존 행 {extra}건 — 지우지 않음")
        if not args.apply:
            conn.rollback()
            print("\n--check-db: 쓰기 없이 종료")
            return
        cur.execute("insert into kb.load_runs (package_name, mode, counts_before, error_rows) values (%s, %s, %s, %s) returning run_id",
                    (PACKAGE_NAME, "apply_partial" if args.allow_partial else "apply", json.dumps(before), total_bad))
        run_id = cur.fetchone()[0]
        print("5) 적재(upsert)")
        for _, table, pk, _ in TABLES:
            n = upsert(cur, table, pk, prepared[table])
            print(f"  {table}: {n}행")
        after = counts(cur)
        print("6) 적재 후 건수", json.dumps(after, ensure_ascii=False))
        problems = 0
        for _, table, pk, _ in TABLES:
            ids = [r[pk] for r in prepared[table]]
            cur.execute(f"select count(*) from {table} where {pk} = any(%s)", (ids,))
            found = cur.fetchone()[0]
            if found != len(ids):
                problems += 1
                print(f"  [불일치] {table}: 패키지 {len(ids)} / DB {found}")
        for label, sql in ORPHAN_CHECKS:
            cur.execute(sql)
            n = cur.fetchone()[0]
            if n:
                problems += 1
                print(f"  [참조 오류] {label}: {n}건")
        if problems:
            conn.rollback()
            sys.exit("적재 후 검사 실패 — 전체 롤백했습니다.")
        cur.execute("update kb.load_runs set finished_at = %s, counts_after = %s where run_id = %s",
                    (datetime.now(timezone.utc), json.dumps(after), run_id))
    print("\n적재 완료(커밋됨). database/verify_after_load.sql 로 한 번 더 확인하세요.")


if __name__ == "__main__":
    main()
