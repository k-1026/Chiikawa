# -*- coding: utf-8 -*-
"""대구·경북 사투리 자료집 생성 스크립트 (J파트 v3).

에이전트가 읽는 파일은 J사투리사전_자료집.md 하나뿐이다. 이 스크립트가 그 파일을 만든다.
규칙 원문: J02_표기규칙.md 2-5·2-6(표기 위험), J03_검수절차.md 2-7(대구·경북 근거·검증 상태).
위험 단어 목록은 J02 2-5 표의 "스크립트용 목록" 열과 "표준어 차단 목록"에서 직접 읽는다(손으로 옮긴 목록 없음).

실행: 이 폴더에서  python -I J자료집생성.py
입력: ../J01_사투리사전.md (본문표 D01~), ../J02_표기규칙.md,
      원천자료(AI 미사용)/*.csv (열: 단어, 표준어 뜻, 지역 표시, 출처 사이트, URL)
출력: J사투리사전_자료집.md (대구·경북 근거 있는 단어만),
      원천자료(AI 미사용)/대구경북미확인_보관.md (근거 없는 단어 — 에이전트 사용 금지)
"""
import csv
import hashlib
import re
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
PART = HERE.parent
RAW = HERE / "원천자료(AI 미사용)"
OUT = HERE / "J사투리사전_자료집.md"
OUT_HOLD = RAW / "대구경북미확인_보관.md"


# ---------------------------------------------------------------- 공통
def norm(w):
    return re.sub(r"[\s\-^~]", "", w)


def tokens(word):
    """'디비지다 / 디지다', '머시마 - 가시나', '-나?, -노?' 같은 묶음을 단어 하나씩으로."""
    parts = re.split(r"\s+/\s+|/|\s+-\s+|,", word)
    return [norm(p) for p in parts if norm(p)]


def table_rows(text, header_start):
    lines = text.split("\n")
    i = next(k for k, l in enumerate(lines) if l.startswith(header_start))
    head = [c.strip() for c in lines[i].strip().strip("|").split(" | ")]
    rows = []
    for l in lines[i + 2:]:
        if not l.startswith("|"):
            break
        cells = [c.strip() for c in l.strip().strip("|").split(" | ")]
        rows.append(dict(zip(head, cells)))
    return rows


# ---------------------------------------------------------------- J-2 목록 읽기
j02 = (PART / "J02_표기규칙.md").read_text(encoding="utf-8")
BLOCK, CAUTION = {}, {}
SUFFIX_CAUTION = {}  # "-노"처럼 "-"로 시작하는 항목 = 말끝. 말끝이 그것으로 끝나는 단어·문구에 W7
for r in table_rows(j02, "| 단어 | 위험 유형 |"):
    for part in r["스크립트용 목록"].split(" / "):
        kind, _, words = part.partition(":")
        for w in words.split(","):
            label = f"{r['위험 유형']}({r['단어'].split('(')[0]})"
            if w.strip().startswith("-") and kind.strip() == "주의":
                SUFFIX_CAUTION[w.strip().lstrip("-")] = label
                continue
            w = norm(w)
            if w:
                (BLOCK if kind.strip() == "반려" else CAUTION)[w] = label
STD_BLOCK = set(norm(x) for x in re.search(r"- 표준어 반려: (.+)", j02).group(1).split(","))
STD_CAUTION = set(norm(x) for x in re.search(r"- 표준어 주의: (.+)", j02).group(1).split(","))
BLOCK_MEANING = ["비속", "속되게", "낮잡", "얕잡"]

# ---------------------------------------------------------------- 대구·경북 근거
# 강한 근거(G1~G3·G5~G7)가 있으면 근거 때문에 ⚠️가 붙지 않는다. G4·G8만 있으면 ⚠️ W1.
G_LABEL = {
    "G1": "G1 국립국어원 지역어 조사(대구 달성군)",
    "G2": "G2 대구시 공식 블로그(대구 명시)",
    "G3": "G3 대구 지역 언론·연구의 대구 사용 사례",
    "G4": "G4 비공식 자료의 대구 표시(Quizlet '대구 사투리' 세트)",
    "G5": "G5 대구시 공식 블로그(경상도로 소개)",
    "G6": "G6 공식 자료의 경북 표시",
    "G7": "G7 공식 자료의 경상 표시(경상도 전체 — 경북 포함)",
    "G8": "G8 비공식 자료의 경북·경상 표시(InterAI 경상북도·Quizlet 경상도)",
    "G9": "G9 D파트 굿즈 문구(대키미 대사, 작성자 제안)",
}
GOODS = "D파트 굿즈 문구"
STRONG = {"G1", "G2", "G3", "G5", "G6", "G7"}
OFFICIAL = {"우리말샘", "지역어 종합 정보", "대구광역시 공식 블로그", "매일신문"}
GRADE = {"우리말샘": 0, "지역어 종합 정보": 1}  # 나머지(InterAI·Quizlet·블로그·언론)는 2
GRADE_LABEL = ["사전만(적게)", "현장조사(적당히)", "생활자료(많이)"]
EXCLUDE_NOT_DIALECT = {"쌔비다": "우리말샘에서 방언이 아니라 속어로 확인(J-1 7절 1-3)"}


def region_codes(site, region):
    """출처 한 행의 지역 표시 → 근거 코드들."""
    c = set()
    if site == GOODS:
        return {"G9"}
    gb = "경북" in region or "경상북도" in region
    gs = re.search(r"경상(?!남도)", region.replace("경상북도", "")) is not None
    if "대구" in region:
        c.add({"지역어 종합 정보": "G1", "대구광역시 공식 블로그": "G2", "매일신문": "G3"}.get(site, "G4"))
    elif site == "대구광역시 공식 블로그":
        c.add("G5")
    elif site in OFFICIAL and gb:
        c.add("G6")
    elif site in OFFICIAL and gs:
        c.add("G7")
    elif gb or gs:
        c.add("G8")
    return c


def standard_word(meaning, site):
    m = re.findall(r"‘([^’]+)’의 방언", meaning)
    if m:
        return m[-1]
    if site == "우리말샘":
        return None
    t = meaning
    if any(c in t for c in "()=") or re.search(r"[A-Za-z]", t) or len(t) > 12:
        return None
    return t


# ---------------------------------------------------------------- 입력 읽기
raw = []
for f in sorted(RAW.glob("*.csv")):
    for r in csv.DictReader(open(f, encoding="utf-8-sig")):
        word = r["단어"].strip()
        accent = ""
        m = re.search(r"\(=([^)]*)\)", word)  # 지역어 조사의 억양 표기, 예: 가거(=가'거)
        if m:
            accent, word = m.group(1), (word[:m.start()] + word[m.end():]).strip()
        region = r["지역 표시"].strip()
        if not region:  # 우리말샘 일부 행은 지역 표시 칸이 비어 있고 뜻풀이 괄호에만 지역이 있다
            mm = re.search(r"의 방언\(([^)]*)\)", r["표준어 뜻"])
            region = mm.group(1) if mm else ""
        raw.append({"word": word, "meaning": r["표준어 뜻"].strip(), "region": region,
                    "site": r["출처 사이트"].strip(), "url": r["URL"].strip(), "accent": accent})

groups = defaultdict(list)
for r in raw:
    if norm(r["word"]) not in EXCLUDE_NOT_DIALECT:
        groups[(r["word"], r["meaning"])].append(r)

entries = []
for (word, meaning), rs in groups.items():
    entries.append({
        "word": word, "meaning": meaning, "std": standard_word(meaning, rs[0]["site"]),
        "sites": sorted({r["site"] for r in rs}), "urls": sorted({r["url"] for r in rs}),
        "regions": sorted({r["region"] for r in rs}),
        "accent": ", ".join(sorted({r["accent"] for r in rs if r["accent"]})),
        "codes": set().union(*[region_codes(r["site"], r["region"]) for r in rs]),
        "grade": max(GRADE.get(r["site"], 2) for r in rs), "j1": None,
    })

j1_entries = []
for r in table_rows((PART / "J01_사투리사전.md").read_text(encoding="utf-8"), "| ID | 표제어 |"):
    region = r["지역 범위"]
    codes = set()
    m = re.match(r"(G\d)", r["대구 근거(직접 확인분)"])
    if m:
        codes.add(m.group(1))
    # J-1 지역 범위 열은 사람이 우리말샘 등 공식 출처로 확인한 값이다. "(대구 포함)" 같은 추정 문구는 근거로 안 씀.
    rg = re.sub(r"\(대구 포함[^)]*\)|대구 포함", "", region)
    if "경북" in rg:
        codes.add("G6")
    elif re.search(r"경상(?!남도)", rg):
        codes.add("G7")
    j1_entries.append({"word": r["표기(자료집용)"], "meaning": r["표준어 뜻"], "std": r["표준어(병기용)"],
                       "sites": ["J-1 본문표"], "urls": [], "regions": [region], "accent": "", "codes": codes,
                       "grade": GRADE_LABEL.index(r["출처 기반 사용 근거"]), "j1": r,
                       "manual": r["대구 근거(직접 확인분)"]})

# J-1 단어와 표기가 같은 원천 행은 따로 싣지 않고 D행 출처 칸에만 덧붙인다(사람이 확인한 D행 우선).
j1_by_word = {norm(e["word"]): e for e in j1_entries}

# ---------------------------------------------------------------- 교차 대조
evid_word, evid_sentence, std_of = defaultdict(set), defaultdict(set), defaultdict(set)
for e in entries + j1_entries:
    if not e["codes"]:
        continue
    is_sentence = " " in e["word"].replace(" / ", "/").replace(" - ", "-") or "?" in e["word"]
    for t in tokens(e["word"]):
        if is_sentence:
            for t2 in re.split(r"\s+", e["word"]):
                evid_sentence[norm(t2.strip("?~"))] |= e["codes"]
        else:
            evid_word[t] |= e["codes"]
            if e["std"]:
                std_of[t].add(norm(e["std"]))

all_entries = list(j1_entries)
for e in entries:
    j = j1_by_word.get(norm(e["word"]))
    if j:
        j["sites"] = sorted(set(j["sites"]) | set(e["sites"]))
        j["urls"] = sorted(set(j["urls"]) | set(e["urls"]))
    else:
        all_entries.append(e)

for e in all_entries:
    own = set(e["codes"])
    cross, cross_diff, weak = set(), set(), set()
    for t in tokens(e["word"]):
        c = evid_word.get(t, set()) - own
        if c and (not e["std"] or not std_of.get(t) or norm(e["std"]) in std_of[t]):
            cross |= c
        elif c:
            cross_diff |= c
        weak |= evid_sentence.get(t, set())
    e["own"], e["cross"] = own, cross
    e["cross_diff"] = cross_diff - own - cross
    e["weak"] = weak - own - cross - e["cross_diff"]

std_by_word = defaultdict(set)
for e in all_entries:
    std_by_word[norm(e["word"])].add(norm(e["std"] or e["meaning"]))


# ---------------------------------------------------------------- 판정
def judge(e):
    X, W = [], []
    toks = tokens(e["word"])
    for t in toks:
        if t in BLOCK:
            X.append(f"X1 {BLOCK[t]}")
    if any(k in e["meaning"] for k in BLOCK_MEANING):
        X.append("X2 뜻풀이에 비속·낮잡는 표현")
    if e["std"] and norm(e["std"]) in STD_BLOCK:
        X.append(f"X3 표준어가 욕설·비하어({e['std']})")
    for t in toks:
        if t in CAUTION:
            W.append(f"W7 주의 단어 — {CAUTION[t]}")
    if e["std"] and norm(e["std"]) in STD_CAUTION and not any(w.startswith("W7") for w in W):
        W.append(f"W7 주의 단어({e['std']})")
    # 말끝 주의("-노" 등): J-1 본문표 단어(와이카노·뭐라카노)는 사람이 출처·맥락을 확인했으므로 제외
    # 우리말샘 "'항라'의 방언"처럼 뜻이 명사인 단어는 말끝이 아니므로 제외(예: 항노)
    is_noun_entry = bool(re.search(r"‘[^’]+’의 방언", e["meaning"])) and not (e["std"] or "").endswith(("니", "냐", "까", "나"))
    if e["j1"] is None and not is_noun_entry and not any(w.startswith("W7") for w in W):
        for chunk in re.split(r"[\s/,]+", e["word"]):
            c2 = chunk.strip("?.!~…-^")
            hit = next((s for s in SUFFIX_CAUTION if c2.endswith(s)), None)
            if hit:
                W.append(f"W7 주의 말끝 — {SUFFIX_CAUTION[hit]}")
                break
    if e["j1"] is not None and "⚠️" in " ".join(e["j1"].values()) and not any(w.startswith("W7") for w in W):
        W.append("W9 J-1에 ⚠️ 사람 확인 콜아웃")
    codes = e["own"] | e["cross"]
    only_goods = set(e["sites"]) == {GOODS}
    if not codes & STRONG:
        if codes == {"G9"} or (only_goods and not codes - {"G9"}):
            W.append("W11 출처가 D파트 굿즈 문구(작성자 제안)뿐 — 외부 출처 확인 전")
        elif codes:
            W.append("W1 대구·경북 근거가 비공식 자료뿐")
        elif e["cross_diff"]:
            W.append("W10 같은 표기의 대구·경북 자료가 있으나 뜻 표현이 달라 같은 말인지 사람 확인")
        elif e["weak"]:
            W.append("W8 대구·경북 자료의 문장 속에서만 확인")
    if e["j1"] is None:
        if not set(e["sites"]) & OFFICIAL and not only_goods and not any(w.startswith("W1") for w in W):
            W.append("W1 출처가 비공식(InterAI·Quizlet)뿐")
        if set(e["word"]) & set(" ?^()~,/"):
            W.append("W2 문장·구·묶음 표제어")
        core = norm(e["word"])
        if e["word"].startswith("-") or core.endswith("다") or (e["std"] or "").endswith("다"):
            W.append("W3 용언·어미(활용형 필요)")
        if len(std_by_word[norm(e["word"])]) > 1:
            W.append("W4 같은 표제어에 뜻 여러 개")
        if e["std"] is None:
            W.append("W6 표준어 병기 단어 추출 불가")
        elif len(e["std"]) < 2:
            W.append("W6 표준어가 한 글자라 뜻이 모호함")
    W = list(dict.fromkeys(W))
    if X:
        return "반려", X + W
    if W:
        return "⚠️ 사람 확인", W
    return "자동 사용", []


def evidence_text(e):
    parts = []
    manual = e.get("manual", "")
    if e["j1"] is not None and manual.startswith("G"):
        parts.append(manual)
    parts += [G_LABEL[c] for c in sorted(e["own"]) if not (manual.startswith(c))]
    parts += [G_LABEL[c] + " — 같은 단어·뜻의 다른 행으로 교차 확인" for c in sorted(e["cross"])]
    if not (e["own"] | e["cross"]) and e["cross_diff"]:
        parts += [G_LABEL[c] + " — 같은 표기의 다른 행(뜻 표현 다름)" for c in sorted(e["cross_diff"])]
    elif not (e["own"] | e["cross"]) and e["weak"]:
        parts += [G_LABEL[c] + " — 문장 속 단어로만" for c in sorted(e["weak"])]
    return " / ".join(parts)


def eid(e):
    if e["j1"] is not None:
        return e["j1"]["ID"]
    return "S-" + hashlib.md5(f"{e['word']}|{e['meaning']}".encode("utf-8")).hexdigest()[:5]


def esc(s):
    return s.replace("|", "／")


keep, hold = [], []
for e in all_entries:
    e["verdict"], e["why"] = judge(e)
    (keep if (e["own"] | e["cross"] | e["cross_diff"] | e["weak"]) else hold).append(e)

order = {"자동 사용": 0, "⚠️ 사람 확인": 1, "반려": 2}
keep.sort(key=lambda e: (e["j1"] is None, order[e["verdict"]], -e["grade"], norm(e["word"])))
hold.sort(key=lambda e: (e["j1"] is None, norm(e["word"])))
cnt = defaultdict(int)
for e in keep:
    cnt[e["verdict"]] += 1


def source_cell(e):
    links = " ".join(f"[링크{i + 1}]({u})" for i, u in enumerate(e["urls"]) if u.startswith("http"))
    files = " · ".join(u for u in e["urls"] if u.startswith("세부지침안/"))  # 굿즈 문구: 시트 경로 + 문구 ID
    return esc(", ".join(e["sites"]) + (" · " + links if links else "") + (" · " + files if files else ""))


def row(e):
    spell = e["word"].replace("-", "") if (e["j1"] is None and e["verdict"] == "자동 사용") else e["word"]
    j = e["j1"] or {}
    acc = f" (억양 표기: {esc(e['accent'])})" if e["accent"] else ""
    return (f"| {eid(e)} | {esc(spell)} | {e['std'] or '—'} | {e['verdict']} | {', '.join(e['why']) or '—'} | "
            f"{esc(evidence_text(e))} | {GRADE_LABEL[e['grade']]} | {esc(j.get('품사', '—'))} | {esc(j.get('예문', '—'))} | "
            f"{esc(e['meaning'])}{acc} | {source_cell(e)} |")


def hold_row(e):
    return (f"| {eid(e)} | {esc(e['word'])} | {e['std'] or '—'} | {esc(e['meaning'])} | "
            f"{esc(' / '.join(e['regions']))} | {source_cell(e)} |")


HEAD = """# J 대구·경북 사투리 자료집

> **에이전트가 사투리 단어를 찾을 때 읽는 파일은 이것 하나뿐이다.** 대구 또는 경북에서 쓰인다는 근거가 있는 단어만 들어 있다(2026-11-18 기준 결정: 대구·경북).
> 이 파일은 `J자료집생성.py`가 만든다 — **손으로 고치지 않는다.** 단어를 더하거나 고치려면 `../J01_사투리사전.md` 본문표나 `원천자료(AI 미사용)/`의 CSV를 고치고, 위험 단어는 `../J02_표기규칙.md` 2-5 표를 고친 뒤 이 폴더에서 `python -I J자료집생성.py`를 실행한다.
> 규칙: `../J02_표기규칙.md` 2-5·2-6(표기 위험), `../J03_검수절차.md` 2-7(대구·경북 근거·검증 상태)

## 에이전트 사용법 (이것만 지키면 된다)

1. **이 표에 없는 단어는 사투리로 쓰지 않는다** — 표준어로 두고 반환의 '질문'에 "J 자료집에 없음: (단어)"를 적는다(J-1 3절 10번). `원천자료(AI 미사용)/` 폴더의 파일은 읽지 않는다.
2. **판정 열을 따른다** — `자동 사용`은 바로 쓴다. `⚠️ 사람 확인`은 써도 되지만 결과에 "⚠️ 사람 확인 필요 — (ID), (걸린 항목)"을 달고 반환 상태를 `질문 필요`로 한다. `반려`는 쓰지 않는다.
3. **범위는 대구·경북 하나로 본다** — 이 표의 단어는 모두 대구·경북 사투리로 소개해도 된다. 억수로·와이카노처럼 경상도 전체에서 널리 쓰는 말도 대구에서 쓰는 말이므로 그대로 쓴다. 대구에서 쓰인다는 걸 따로 입증할 필요는 없다.
4. **표기는 "표기" 열, 병기는 "표준어(병기용)" 열 그대로** — "표준어(표기)" 꼴로 쓴다. 예: `두부(조피) 조림`.
5. **뜻을 바꾸거나 활용형·합성어를 새로 만들지 않는다** — D로 시작하는 J-1 단어는 품사·예문 열을 참고해 써도 되고, S로 시작하는 단어는 표기 열 형태 그대로만 쓴다.
6. **쓴 단어의 ID를 결과 파일에 적는다** — J-3 검수(체크리스트 1번)가 ID로 대조한다.
7. 같은 뜻의 단어가 여럿이면 D 단어를 먼저, 그다음 "출처 기반 사용 근거"가 `생활자료(많이)` → `현장조사(적당히)` → `사전만(적게)` 순으로 고른다. 이 값은 실제 사용 빈도가 아니라 **어떤 종류의 출처에 실렸는지**다.

## 열 설명

- **ID**: D로 시작 = J-1 본문표(사람이 품사·예문까지 확인), S로 시작 = 원천자료 자동 판정(표제어·뜻으로 만든 고정 번호)
- **근거**: G1 국립국어원 지역어 조사(대구 달성군) · G2 대구시 공식 블로그(대구 명시) · G3 대구 지역 언론·연구의 대구 사례 · G4 Quizlet "대구 사투리" 세트(비공식) · G5 대구시 블로그(경상도로 소개) · G6 공식 자료의 경북 표시 · G7 공식 자료의 경상 표시(경상도 전체, 경북 포함) · G8 비공식 자료의 경북·경상 표시 · G9 D파트 굿즈 문구(작성자 제안, 출처 칸에 시트 경로·문구 ID). G4·G8만 있으면 ⚠️ W1, G9만 있으면 ⚠️ W11(출처가 비공식이라서이지, 대구를 입증 못 해서가 아니다). 근거 칸은 어디서 확인했는지를 보여 줄 뿐이다. "교차 확인"은 같은 표기·같은 표준어의 다른 출처 행에 근거가 있다는 뜻이다.
- **걸린 항목**: X = 반려 사유(J-2 2-6), W = ⚠️ 사유(J-3 2-7-3).
- 경남만 표시됐거나 지역 표시가 없는 단어는 이 파일에 넣지 않았다(`원천자료(AI 미사용)/대구경북미확인_보관.md`).
"""

table_head = ("| ID | 표기 | 표준어(병기용) | 판정 | 걸린 항목 | 근거 | 출처 기반 사용 근거 | 품사 | 예문 | 원문 뜻 | 출처 |\n"
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
summary = (f"## 수록 현황\n\n- 대구·경북 근거 있는 단어 {len(keep)}개: "
           f"자동 사용 {cnt['자동 사용']} · ⚠️ 사람 확인 {cnt['⚠️ 사람 확인']} · 반려 {cnt['반려']} "
           f"(J-1 본문표 {sum(e['j1'] is not None for e in keep)}개 포함)\n"
           f"- 근거 없어 뺀 단어: {len(hold)}개(보관 파일)\n")
OUT.write_text("\n".join([HEAD, summary, "## 사전\n", table_head] + [row(e) for e in keep]) + "\n", encoding="utf-8")

hold_head = f"""# 대구·경북 미확인 보관 — 에이전트 사용 금지

> `J자료집생성.py`가 만든다. 원천자료 중 **대구·경북 근거(G1~G8, 교차 확인, 문장 속 확인)가 하나도 없는 단어**다(경남만 표시, 지역 표시 없음, 경북·경상이 아닌 다른 지역만 표시 등).
> 근거를 새로 찾으면: J-1 본문표의 "대구 근거(직접 확인분)"·"지역 범위" 열에 적거나(J-1 단어), `대구_추가조사(...).csv`에 행을 더하고(그 외) 스크립트를 다시 돌린다.

- 수록: {len(hold)}개 (J-1 본문표 {sum(e['j1'] is not None for e in hold)}개 포함)

| ID | 표제어 | 표준어 | 원문 뜻 | 지역 표시 | 출처 |
| --- | --- | --- | --- | --- | --- |
"""
OUT_HOLD.write_text(hold_head + "\n".join(hold_row(e) for e in hold) + "\n", encoding="utf-8")
old = RAW / "대구미확인_보관.md"
if old.exists():
    old.unlink()

print({"자료집": len(keep), **cnt, "보관": len(hold),
       "보관_J1": [e["j1"]["ID"] + " " + e["word"] for e in hold if e["j1"] is not None]})
