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
