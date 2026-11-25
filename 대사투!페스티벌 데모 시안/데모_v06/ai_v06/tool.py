"""서브에이전트가 쓰는 도구: search_docs, web_search, query_table (명세 TOOL_SPECS + 함수 TOOL_FUNCS)."""
import csv

from google import genai

from config import GEMINI_API_KEY, GEMINI_MODEL, TABLE_CSV, rgh  # config 가 docs 경로를 등록한다

_client = genai.Client(api_key=GEMINI_API_KEY)
TOP_K = 4


def search_docs(query: str) -> str:
    """축제 세부지침 문서에서 query와 가까운 조각을 찾아 본문과 출처 파일명을 문자열로 돌려준다."""
    query = (query or "").strip()
    if not query:
        return "검색어가 비어 있습니다."
    hits = rgh.retrieve(_client, query, TOP_K)
    return "\n\n".join(
        f"[결과 {n}] 출처 파일: {c['file']} (제목: {c['heading']})\n{c['text']}"
        for n, (c, _s) in enumerate(hits, 1))


def web_search(query: str) -> str:
    """구글 검색으로 최신 외부 정보를 찾아 답변한다. (기존 11.17 web_search 와 같은 방식)"""
    interaction = _client.interactions.create(
        model=GEMINI_MODEL, input=query, tools=[{"type": "google_search"}])
    return interaction.output_text


def query_table(keyword: str, column: str = "") -> str:
    """festival_table.csv 에서 keyword가 들어 있는 행을 돌려준다. column을 주면 그 열에서만 찾는다."""
    keyword = (keyword or "").strip()
    with open(TABLE_CSV, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if column and rows and column not in rows[0]:
        return f"없는 열입니다. 열 이름: {', '.join(rows[0].keys())}"
    hit = [r for r in rows
           if keyword in (r[column] if column else " ".join(r.values()))]
    if not hit:
        return f"'{keyword}'에 해당하는 행이 없습니다. (표 파일: {TABLE_CSV.name})"
    return "\n".join(" | ".join(f"{k}={v}" for k, v in r.items() if v != "") for r in hit)


TOOL_FUNCS = {"search_docs": search_docs, "web_search": web_search, "query_table": query_table}

TOOL_SPECS = {
    "search_docs": {
        "name": "search_docs",
        "description": "축제 세부지침 문서에서 검색어와 의미가 가까운 조각을 찾는다. 결과는 조각 본문과 출처 파일명이 든 문자열이다. 한 번에 한 주제만 검색한다.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string", "description": "핵심 키워드 위주의 검색어"}}, "required": ["query"]},
    },
    "web_search": {
        "name": "web_search",
        "description": "구글 검색으로 문서 밖의 최신 외부 정보(교통·시간표·날씨·타 축제 사례 등)를 찾는다.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string", "description": "검색할 질문이나 키워드"}}, "required": ["query"]},
    },
    "query_table": {
        "name": "query_table",
        "description": ("festival_table.csv(축제 수치 표: 숙박 보상·쿠폰 금액 3안, 수수료율, 수용 인원)에서 행을 찾는다. "
                        "열: 항목, 분류, 최소, 기본, 확장, 단위, 상태, 출처파일."),
        "parameters": {"type": "object", "properties": {
            "keyword": {"type": "string", "description": "찾을 단어 (예: 숙박, 쿠폰, 수수료)"},
            "column": {"type": "string", "description": "특정 열에서만 찾을 때 열 이름. 비우면 모든 열"}},
            "required": ["keyword"]},
    },
}
