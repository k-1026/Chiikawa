# -*- coding: utf-8 -*-
"""한글 검색 품질 점검: data/search_tests.csv 의 질의를 kb.search_chunks 로 실행해 적중률을 보고한다.

적재가 끝난 DB 에서만 실행한다(읽기 전용, 쓰기 없음).
  SUPABASE_DB_URL  Postgres 연결 문자열(환경변수)

  python -I database/run_search_tests.py            # 상위 5개 기준
  python -I database/run_search_tests.py --k 3
결과는 load_errors/search_test_result.csv 에도 저장한다.
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
    args = ap.parse_args()
    url = os.environ.get("SUPABASE_DB_URL")
    if not url:
        sys.exit("SUPABASE_DB_URL 환경변수가 없습니다(적재 후 실행하는 스크립트입니다).")
    try:
        import psycopg  # type: ignore
    except ImportError:
        sys.exit('psycopg 가 없습니다: pip install "psycopg[binary]"')
    tests = list(csv.DictReader(open(os.path.join(DATA_DIR, "search_tests.csv"), encoding="utf-8", newline="")))
    out, hits = [], 0
    with psycopg.connect(url) as conn, conn.cursor() as cur:
        for t in tests:
            cur.execute("select chunk_id from kb.search_chunks(%s, %s, %s)",
                        (t["query"], t["include_reference"] == "true", args.k))
            got = [r[0] for r in cur.fetchall()]
            rank = got.index(t["expected_chunk_id"]) + 1 if t["expected_chunk_id"] in got else 0
            hits += rank > 0
            out.append(dict(test_id=t["test_id"], query=t["query"], expected_chunk_id=t["expected_chunk_id"],
                            rank=rank, top_results=";".join(got)))
            print(f"  {t['test_id']} {'적중' if rank else '실패'}(순위 {rank or '-'}) — {t['query']}")
    os.makedirs(os.path.join(PKG, "load_errors"), exist_ok=True)
    with open(os.path.join(PKG, "load_errors", "search_test_result.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)
    print(f"\n상위 {args.k}개 적중률: {hits}/{len(tests)} ({hits / len(tests):.0%})")


if __name__ == "__main__":
    main()
