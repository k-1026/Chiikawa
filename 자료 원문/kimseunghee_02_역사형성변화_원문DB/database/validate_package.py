# -*- coding: utf-8 -*-
"""패키지 오프라인 검증(DB 연결 없음).

검사 항목: CSV 인코딩·헤더, 중복 ID, FK, 빈 본문, 본문 잘림 표시, 글자 수, 허용값,
원문 파일 SHA-256, 청크 본문 원문 재대조(보관 원문), 관련 청크·링크 일치, JSON 유효성,
비밀값·휴대전화 번호 패턴, 승인 규칙(승인 청크는 공식 원문 보관 + 글자 대조 완료).

사용: python -I database/validate_package.py
"""
import csv
import glob
import hashlib
import html
import json
import os
import re
import sys

PKG = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PKG, "data")  # CSV 위치

FILES = {
    "source_documents.csv": "source_id", "md_documents.csv": "md_id", "source_sections.csv": "section_id",
    "knowledge_chunks.csv": "chunk_id", "chunk_links.csv": "link_id", "md_claims.csv": "claim_id",
    "evidence_links.csv": "link_id", "domain_figures.csv": "record_id", "domain_places.csv": "place_id",
    "operating_rules.csv": "rule_id", "review_issues.csv": "issue_id", "search_tests.csv": "test_id",
    "rule_tests.csv": "test_id",
}
ENUMS = {
    ("knowledge_chunks.csv", "info_type"): {"fact", "rule", "condition", "exception", "figure", "procedure", "example"},
    ("knowledge_chunks.csv", "approval_status"): {"approved", "reference_only", "internal", "pending"},
    ("source_documents.csv", "approval_status"): {"approved", "reference_only", "internal", "pending"},
    ("source_documents.csv", "source_grade"): {"S", "A", "B", "D", "E", "U"},
    ("evidence_links.csv", "verdict"): {"match", "faithful_summary", "interpretation", "overgeneralization",
                                        "scope_mismatch", "mismatch", "unverifiable"},
    ("evidence_links.csv", "source_relation"): {"original_confirmed", "alternative_official", "user_authored", "unverifiable"},
    ("domain_figures.csv", "value_status"): {"reported", "not_available", "unconfirmed", "not_applicable", "actual_zero"},
    ("domain_figures.csv", "domain"): {"statistic", "budget", "program", "operation", "price", "spec"},
    ("chunk_links.csv", "relation"): {"must_read_with", "conflicts_with", "exception_of", "rule_about"},
}
FKS = [
    ("md_documents.csv", "source_id", "source_documents.csv"),
    ("source_sections.csv", "source_id", "source_documents.csv"),
    ("source_sections.csv", "parent_section_id", "source_sections.csv"),
    ("knowledge_chunks.csv", "source_id", "source_documents.csv"),
    ("knowledge_chunks.csv", "md_id", "md_documents.csv"),
    ("knowledge_chunks.csv", "parent_section_id", "source_sections.csv"),
    ("knowledge_chunks.csv", "source_block_id", "source_sections.csv"),
    ("chunk_links.csv", "from_chunk_id", "knowledge_chunks.csv"),
    ("chunk_links.csv", "to_chunk_id", "knowledge_chunks.csv"),
    ("md_claims.csv", "md_id", "md_documents.csv"),
    ("evidence_links.csv", "claim_id", "md_claims.csv"),
    ("evidence_links.csv", "md_id", "md_documents.csv"),
    ("evidence_links.csv", "source_id", "source_documents.csv"),
    ("evidence_links.csv", "chunk_id", "knowledge_chunks.csv"),
    ("domain_figures.csv", "source_id", "source_documents.csv"),
    ("domain_figures.csv", "chunk_id", "knowledge_chunks.csv"),
    ("domain_figures.csv", "claim_id", "md_claims.csv"),
    ("domain_places.csv", "source_id", "source_documents.csv"),
    ("domain_places.csv", "chunk_id", "knowledge_chunks.csv"),
    ("operating_rules.csv", "rule_source_id", "source_documents.csv"),
    ("operating_rules.csv", "rule_chunk_id", "knowledge_chunks.csv"),
    ("search_tests.csv", "expected_chunk_id", "knowledge_chunks.csv"),
]
SECRET_PATTERNS = [r"eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}", r"sk_(live|test)_[A-Za-z0-9]{16,}",
                   r"(?i)service_role_key\s*=\s*\S{20,}", r"postgres(ql)?://[^\s:]+:[^\s@]+@"]
MOBILE = r"01[016789]-\d{3,4}-\d{4}"


def squash(s):
    return re.sub(r"\s+", "", s)


def html_to_text(raw):
    t = re.sub(r"(?s)<script.*?</script>|<style.*?</style>|<!--.*?-->", "", raw)
    return html.unescape(re.sub(r"<[^>]+>", "\n", t))


def run(quiet=False):
    problems, warnings = [], []
    data = {}
    for name, pk in FILES.items():
        path = os.path.join(DATA_DIR, name)
        raw = open(path, "rb").read()
        try:
            raw.decode("utf-8")
        except UnicodeDecodeError:
            problems.append(f"{name}: UTF-8 아님")
        if raw.startswith(b"\xef\xbb\xbf"):
            warnings.append(f"{name}: BOM 있음")
        with open(path, encoding="utf-8", newline="") as f:
            rd = csv.DictReader(f)
            for h in rd.fieldnames:
                if not re.fullmatch(r"[a-z][a-z0-9_]*", h):
                    problems.append(f"{name}: 영문 소문자 컬럼명이 아님 '{h}'")
            rows = list(rd)
        ids = [r[pk] for r in rows]
        dup = {i for i in ids if ids.count(i) > 1}
        if dup:
            problems.append(f"{name}: 중복 ID {sorted(dup)[:5]}")
        if any(not i for i in ids):
            problems.append(f"{name}: 빈 ID")
        data[name] = rows
    idx = {n: {r[FILES[n]] for r in rows} for n, rows in data.items()}

    for (name, col), allowed in ENUMS.items():
        bad = {r[col] for r in data[name] if r[col] not in allowed}
        if bad:
            problems.append(f"{name}.{col}: 허용되지 않은 값 {bad}")

    for name, col, target in FKS:
        missing = {r[col] for r in data[name] if r[col] and r[col] not in idx[target]}
        if missing:
            problems.append(f"FK {name}.{col} → {target}: 없는 ID {sorted(missing)[:5]}")

    # 원문 파일 해시
    src = {r["source_id"]: r for r in data["source_documents.csv"]}
    for r in src.values():
        if r["original_status"] == "stored":
            p = os.path.join(PKG, r["original_file_path"])
            if not os.path.exists(p):
                problems.append(f"원문 파일 없음: {r['original_file_path']}")
                continue
            if hashlib.sha256(open(p, "rb").read()).hexdigest() != r["original_sha256"]:
                problems.append(f"SHA-256 불일치: {r['source_id']}")
        elif r["original_file_path"]:
            problems.append(f"{r['source_id']}: 보관하지 않은 원문에 파일 경로가 있음")
    stored_files = {os.path.basename(r["original_file_path"]) for r in src.values() if r["original_file_path"]}
    for f in glob.glob(os.path.join(PKG, "originals", "*")):
        if os.path.basename(f) not in stored_files:
            warnings.append(f"originals/ 에 목록에 없는 파일: {os.path.basename(f)}")

    # 청크 검사
    cache = {}
    chunk_ids = idx["knowledge_chunks.csv"]
    link_pairs = {(r["from_chunk_id"], r["to_chunk_id"]) for r in data["chunk_links.csv"] if r["relation"] == "must_read_with"}
    for c in data["knowledge_chunks.csv"]:
        t = c["text_original"]
        if not t.strip():
            problems.append(f"{c['chunk_id']}: 빈 본문")
        if t.rstrip().endswith(("…", "...")) or "�" in t:
            problems.append(f"{c['chunk_id']}: 잘림·깨짐 표시")
        if int(c["char_count"]) != len(t):
            problems.append(f"{c['chunk_id']}: char_count 불일치")
        if len(t) > 400:
            warnings.append(f"{c['chunk_id']}: 400자 초과 — 복수 정보 포함 여부 검토")
        if len(squash(t)) < 6 and not c["related_chunk_ids"]:
            warnings.append(f"{c['chunk_id']}: 매우 짧고 연결 청크 없음 — 단독 의미 검토")
        if c["text_is_excerpt"] == "true" and len(t) > 200:
            warnings.append(f"{c['chunk_id']}: 언론 발췌 200자 초과")
        for r in filter(None, c["related_chunk_ids"].split(";")):
            if r not in chunk_ids:
                problems.append(f"{c['chunk_id']}: 관련 청크 없음 {r}")
            elif (c["chunk_id"], r) not in link_pairs:
                problems.append(f"{c['chunk_id']}: chunk_links 에 {r} 연결 없음")
        s = src[c["source_id"]]
        if c["approval_status"] == "approved":
            if s["source_grade"] not in ("S", "A") or c["text_check"] != "verified_in_stored_original":
                problems.append(f"{c['chunk_id']}: 승인 조건 위반(공식 원문 보관·대조 필요)")
        if c["text_check"] in ("not_found_in_original", "not_checked") and c["approval_status"] != "pending":
            problems.append(f"{c['chunk_id']}: 대조 안 된 청크가 pending 이 아님")
        # 보관 원문 재대조
        if s["original_status"] == "stored":
            if s["source_id"] not in cache:
                raw = open(os.path.join(PKG, s["original_file_path"]), encoding="utf-8", errors="replace").read()
                cache[s["source_id"]] = squash(html_to_text(raw) if raw.lstrip().startswith("<") or s["original_file_path"].endswith(".html") else raw)
            for ln in t.split("\n"):
                if squash(ln) not in cache[s["source_id"]]:
                    problems.append(f"{c['chunk_id']}: 원문에서 찾을 수 없음 '{ln[:30]}'")

    # 근거 연결
    claims_with_ev = {r["claim_id"] for r in data["evidence_links.csv"]}
    for c in data["md_claims.csv"]:
        if c["claim_id"] not in claims_with_ev:
            problems.append(f"{c['claim_id']}: 근거 연결 없음")
    for e in data["evidence_links.csv"]:
        if e["verdict"] != "unverifiable" and e["source_relation"] != "user_authored" and not e["chunk_id"]:
            problems.append(f"{e['link_id']}: 판정했는데 근거 청크 없음")
        if e["chunk_id"] and e["excerpt"] != next(c["text_original"] for c in data["knowledge_chunks.csv"] if c["chunk_id"] == e["chunk_id"]):
            problems.append(f"{e['link_id']}: excerpt 가 청크 본문과 다름")
    used_sources = ({r["source_id"] for r in data["knowledge_chunks.csv"]} | {r["source_id"] for r in data["evidence_links.csv"]})
    for sid in idx["source_documents.csv"] - used_sources:
        warnings.append(f"{sid}: 어떤 청크·근거에도 쓰이지 않은 원문")

    # 정형 데이터
    for f in data["domain_figures.csv"]:
        if f["value_status"] in ("unconfirmed", "not_available") and f["value_numeric"]:
            problems.append(f"{f['record_id']}: 미확인인데 값이 있음")
        if f["value_status"] == "reported" and not (f["value_numeric"] or f["value_text"]):
            problems.append(f"{f['record_id']}: reported 인데 값 없음")
        if f["value_numeric"]:
            try:
                float(f["value_numeric"])
            except ValueError:
                problems.append(f"{f['record_id']}: 숫자 아님")
        if f["currency"] and f["unit"] != f["currency"]:
            warnings.append(f"{f['record_id']}: unit/currency 다름")

    # JSON
    for p in glob.glob(os.path.join(PKG, "json", "*.json")):
        try:
            json.load(open(p, encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            problems.append(f"{os.path.basename(p)}: JSON 오류 {e}")

    # 비밀값·휴대전화
    for p in glob.glob(os.path.join(PKG, "**", "*"), recursive=True):
        if os.path.isdir(p) or "load_errors" in p:
            continue
        txt = open(p, encoding="utf-8", errors="ignore").read()
        for pat in SECRET_PATTERNS:
            if re.search(pat, txt):
                problems.append(f"비밀값 의심 패턴: {os.path.relpath(p, PKG)}")
        if re.search(MOBILE, txt):
            problems.append(f"휴대전화 번호 패턴: {os.path.relpath(p, PKG)}")

    # ---- 11절 추가 검사 -------------------------------------------------------
    chunks = data["knowledge_chunks.csv"]
    # (1) approved 본문이 보관 원문에 글자 그대로 없음 — 위 재대조에서 이미 오류. 승인 조건도 위에서 검사.
    # (2) Aside 보고만 있는 값이 approved
    for c in chunks:
        if c["approval_status"] == "approved" and c["text_check"] == "reported_by_aside_not_stored":
            problems.append(f"{c['chunk_id']}: Aside 보고만 있는데 approved")
    for e in data["evidence_links.csv"]:
        ck = next((c for c in chunks if c["chunk_id"] == e["chunk_id"]), None)
        if ck and ck["approval_status"] == "approved" and re.search(r"Aside", e["review_note"]) and e["verdict"] in ("match", "faithful_summary"):
            problems.append(f"{e['link_id']}: approved 근거 판정 메모에 Aside 보고가 섞임")
    for f in data.get("domain_figures.csv", []):
        if f["approval_status"] == "approved" and re.search(r"Aside", f["note"]):
            problems.append(f"{f['record_id']}: approved 수치에 Aside 보고가 섞임")
    # (3) 서지·메타 정보만 담은 청크
    for c in chunks:
        if c.get("block_type_hint") == "meta" or re.fullmatch(r"(?s)\s*(\[?시행[^\]]*\]?\s*\[[^\]]*\]|.{0,40}\n(저자|발행일|저널명|권|페이지|펴낸).*)\s*", c["text_original"]):
            problems.append(f"{c['chunk_id']}: 서지·메타 정보만 담은 청크")
    sec_meta = {r["section_id"] for r in data["source_sections.csv"] if r["block_type"] == "meta"}
    for c in chunks:
        if c["source_block_id"] in sec_meta:
            problems.append(f"{c['chunk_id']}: 메타 블록(서지·시행일)에서 만든 청크")
    # (4) 대상 0건인 차단·경고 규칙
    for r in data["operating_rules.csv"]:
        if r["enforcement"] not in ("block", "block_as_fact", "warn"):
            continue
        targets = [t for t in r.get("target_chunk_ids", "").split(";") if t]
        hit = [c for c in chunks if c["chunk_id"] in targets]
        col, op, val = r.get("match_column", ""), r.get("match_operator", ""), r.get("match_value", "")
        if col:
            hit += [c for c in chunks if (c.get(col, "") == val) == (op == "=")]
        if not hit:
            problems.append(f"{r['rule_id']}: 대상 청크 0건(규칙이 아무것도 막지 않음)")
    # (5) SQL 함수 안 규칙 ID 하드코딩 — 마이그레이션 순서상 마지막 정의 기준
    last_def = {}
    for p in sorted(glob.glob(os.path.join(PKG, "database", "migrations", "*.sql"))):
        sql = open(p, encoding="utf-8").read()
        for m in re.finditer(r"create (?:or replace )?function (kb\.\w+)\(.*?\$\$(.*?)\$\$", sql, re.S | re.I):
            last_def[m.group(1)] = (os.path.basename(p), m.group(2))
    for fn, (fname, body) in last_def.items():
        if re.search(r"RULE-[A-Z0-9-]*\d", body):
            problems.append(f"{fn}({fname}): 함수 안에 규칙 ID 하드코딩")
    # (6) 기준 MD SHA 가 현재 main 과 다른데 stale 표시 없음
    md = data["md_documents.csv"][0]
    try:
        import subprocess
        _r = subprocess.run(["git", "rev-parse", "--verify", "-q", "origin/main:" + md["repo_path"]], cwd=PKG, capture_output=True, text=True)
        cur = _r.stdout.strip() if _r.returncode == 0 and re.fullmatch(r"[0-9a-f]{40}", _r.stdout.strip()) else ""
    except Exception:  # noqa: BLE001
        cur = ""
    if cur and cur != md["git_blob_sha"]:
        if not any(c.get("stale") == "true" for c in data["md_claims.csv"]):
            problems.append(f"기준 MD blob {md['git_blob_sha'][:8]} ≠ 현재 main {cur[:8]} 인데 stale 표시 없음")
    elif not cur:
        warnings.append("현재 main 의 MD blob 을 확인하지 못함(git 없음)")
    # (7) rule_tests·search_tests 의 기대 chunk_id 존재
    ids = {c["chunk_id"] for c in chunks}
    for name in ("rule_tests.csv", "search_tests.csv"):
        p = os.path.join(DATA_DIR, name)
        if not os.path.exists(p):
            problems.append(f"{name} 없음")
            continue
        for r in csv.DictReader(open(p, encoding="utf-8")):
            for k in ("expected_chunk_id", "blocked_chunk_id", "passing_chunk_id"):
                if r.get(k) and r[k] not in ids:
                    problems.append(f"{name}:{r.get('test_id')} {k} 없음 {r[k]}")
    # (8) DDL 허용값·형식(지난 검증에서 놓친 것)
    import datetime
    for name, cols in [("source_documents.csv", ["published_date", "accessed_at"]), ("evidence_links.csv", ["published_date", "accessed_at"]),
                       ("domain_figures.csv", ["period_start", "period_end"])]:
        for r in data.get(name, []):
            for c in cols:
                if r.get(c):
                    try:
                        datetime.date.fromisoformat(r[c])
                    except ValueError:
                        problems.append(f"{name}:{r[list(r)[0]]}.{c} 날짜 형식 아님({r[c]})")
    for r in data["md_claims.csv"]:
        if r["claim_type"] not in ("fact", "figure", "rule", "quote", "proposal", "status"):
            problems.append(f"{r['claim_id']}: claim_type 허용값 아님({r['claim_type']})")
    for r in data["chunk_links.csv"]:
        if not re.match(r"CLK-K\d\d-", r["link_id"]):
            problems.append(f"{r['link_id']}: 패키지 접두어 없는 링크 ID(다른 패키지와 충돌)")

    if not quiet or problems:
        for w in warnings:
            print("  [경고]", w)
        for p in problems:
            print("  [오류]", p)
    if not quiet:
        print(f"\n행 수: " + ", ".join(f"{n}={len(r)}" for n, r in data.items()))
        print(f"오류 {len(problems)}건, 경고 {len(warnings)}건")
    return not problems


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
