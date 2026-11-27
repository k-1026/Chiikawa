# -*- coding: utf-8 -*-
"""한글 검색 점검: data/search_tests.csv 를 kb.search_chunks 로 실행해 결과를 판정한다(읽기 전용).

expect 값
  hit     기대 청크가 상위 k 안에 나와야 함
  warn    기대 청크가 나오고, 결과의 warnings 칸에 경고가 붙어야 함
  blocked 기대 청크가 결과에 나오면 안 됨(차단 규칙)

  SUPABASE_DB_URL  Postgres 연결 문자열(환경변수)
  python -I database/run_search_tests.py [--k 5] [--offline]
--offline 은 DB 없이 '기대 청크가 패키지에 있는지'만 본다(적중률 아님).
"""
import argparse
import csv
import os
import sys

PKG = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PKG, "data")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--offline", action="store_true")
    a = ap.parse_args()
    tests = list(csv.DictReader(open(os.path.join(DATA_DIR, "search_tests.csv"), encoding="utf-8", newline="")))
    if a.offline:
        ids = {r["chunk_id"] for r in csv.DictReader(open(os.path.join(DATA_DIR, "knowledge_chunks.csv"), encoding="utf-8"))}
        miss = [t["test_id"] for t in tests if t["expected_chunk_id"] not in ids]
        kinds = {k: sum(1 for t in tests if t["query_type"] == k) for k in ("keyword", "sentence", "blocked")}
        print(f"오프라인 점검: 기대 청크 존재 {len(tests) - len(miss)}/{len(tests)}, 유형 {kinds}. 실제 적중률은 미실행")
        return
    url = os.environ.get("SUPABASE_DB_URL")
    if not url:
        sys.exit("SUPABASE_DB_URL 환경변수가 없습니다(적재 후 실행). DB 없이 보려면 --offline")
    try:
        import psycopg  # type: ignore
    except ImportError:
        sys.exit('psycopg 가 없습니다: pip install "psycopg[binary]"')
    out, ok = [], 0
    with psycopg.connect(url) as conn, conn.cursor() as cur:
        cur.execute("set transaction read only")
        for t in tests:
            cur.execute("select chunk_id, warnings from kb.search_chunks(%s, %s, %s)", (t["query"], t["include_reference"] == "true", a.k))
            rows = cur.fetchall()
            got = [r[0] for r in rows]
            warn = {r[0]: r[1] for r in rows}
            if t["expect"] == "blocked":
                passed = t["expected_chunk_id"] not in got
            elif t["expect"] == "warn":
                passed = t["expected_chunk_id"] in got and bool(warn.get(t["expected_chunk_id"]))
            else:
                passed = t["expected_chunk_id"] in got
            ok += passed
            out.append(dict(test_id=t["test_id"], query_type=t["query_type"], expect=t["expect"], passed=passed, top_results=";".join(got)))
            print(f"  {t['test_id']} {'통과' if passed else '실패'} [{t['query_type']}/{t['expect']}] {t['query']}")
    os.makedirs(os.path.join(PKG, "load_errors"), exist_ok=True)
    with open(os.path.join(PKG, "load_errors", "search_test_result.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)
    by = {}
    for o in out:
        by.setdefault(o["query_type"], [0, 0])
        by[o["query_type"]][0] += o["passed"]
        by[o["query_type"]][1] += 1
    print(f"\n상위 {a.k}개 기준 통과 {ok}/{len(tests)} — " + ", ".join(f"{k} {v[0]}/{v[1]}" for k, v in by.items()))


if __name__ == "__main__":
    main()
