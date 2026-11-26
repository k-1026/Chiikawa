"""대화 내용을 '대사투! 페스티벌 기획안(8개 항목)' 필드로 정리하는 에이전트.
search_docs 로 main 자료를 찾아 사실(기간·장소 등)을 확인하고, 대화에서 정해진 것만 채운다."""
import json
import re

from agent_loop import run_agent
from config import GEMINI_API_KEY, GEMINI_MODEL
from tool import TOOL_FUNCS, TOOL_SPECS

KEYS = {
    "festival_name": "축제 이름(컨셉 포함)", "concept": "컨셉 한 줄", "period": "개최 기간", "place": "개최 장소",
    "host": "주최·주관", "visitors": "예상 관람객 / 순간 최대 인원", "budget_total": "총 사업비",
    "goal": "핵심 목표", "necessity": "필요성", "differentiation": "차별화 전략",
    "programs": "[{name, desc}] 프로그램 3~5개", "schedule": "일정표 행들. 한 행은 [구분(낮/저녁/밤), 1일차, 2일차, …]이며 개최 기간의 날짜 수만큼 칸을 둔다(selections 의 schedule_days 참고). 마지막 날 행사는 마지막 칸에 둔다",
    "layout": "배치도 설명", "stay_link": "체류·상권 연결", "mascot": "마스코트(대키미·외지몽) 활용",
    "scale": "운영 규모(부스·인력)", "partners": "협력 기관·네트워크", "prep": "준비 단계 일정",
    "budget_items": "[{item, basis, amount}] 사업비 항목", "safety_staff": "안전 인력", "safety_peak": "순간 최대·동시 수용 인원",
    "safety_org": "안전관리 조직·인파·교통 대책", "heat": "폭염 대응", "cautions": "유의 사항",
    "effects": "기대효과",
    "scope": "사업 범위·구역(장소의 구역 범위)", "budget_vat": "예산의 부가세 포함 여부", "prep_period": "준비 기간", "report_due": "결과보고 제출 기한(행사 종료 후 며칠 이내)",
    "promo_pre": "사전 홍보 전략", "promo_off": "오프라인 홍보(옥외·인쇄물)", "promo_on": "온라인 홍보(SNS·유튜브·언론)", "report_plan": "보고 일정(착수·중간·결과)",
    "permits": "인허가·민원 대응", "opinion": "주민·상인 의견수렴 방법", "kpi": "[{metric, method, target}] 성과지표(예: 방문객 수, 매출 변동, 참여 인원)와 측정 방법", "org_intro": "신청 단체 소개", "track_record": "동종 행사 실적", "commitment": "자기부담 확약",
}

SYSTEM = f"""너는 대구 사투리 축제 '대사투! 페스티벌'의 기획안을 정리하는 에이전트야.
입력: 사용자와 대키미봇의 대화 기록과, 사용자가 고른 선택지(있다면).
할 일: 대화에서 정해진 내용을 아래 키에 맞춰 정리한다. 기간·장소·프로그램 같은 사실은 search_docs로 확인해 근거 자료와 어긋나지 않게 쓴다.

규칙
1. 대화나 search_docs 결과에 근거가 없는 값은 지어내지 말고 빈 문자열 ""로 둔다(문서에서 '미입력'으로 표시된다). 배열 값은 빈 배열 []로 둔다.
   특히 주최·주관, 예상 관람객·순간 최대 인원, 총 사업비와 사업비 항목, 협력 기관, 신청 단체 소개·실적·확약, 준비 일정, 안전관리 조직은
   사용자가 말했거나 문서에 적혀 있을 때만 쓴다. 그럴듯한 숫자나 기관명을 만들어 넣지 않는다.
2. 사용자가 말한 방향을 문서의 수치로 구체화했다면 문장 끝에 [가정]을, 문서의 추정값이면 [추정]을 붙인다. 문서·대화에서 확인한 사실은 그대로 쓴다.
3. 문장은 공공기관 사업계획서처럼 간결한 평서문(~함, ~한다)으로 쓴다. 과장하지 않는다.
4. 할매 말투·지역 비하 콘셉트 금지, 12~16시 야외 핵심 프로그램 금지(폭염) 원칙을 지킨다.
5. 검색은 최대 5번.
6. '사용자가 고른 선택'의 conditions(저장한 조건)는 이전 초안(previous_draft)과 검색 결과보다 항상 우선한다.
   연도·기간·장소·주최·컨셉·목표·규모·프로그램이 조건과 다르면 조건을 따른다. 조건의 프로그램은 빠짐없이 programs 에 넣는다.
7. 출력은 JSON 객체 하나뿐이다. 설명·코드블록 표시를 붙이지 않는다.

JSON 키와 뜻:
{json.dumps(KEYS, ensure_ascii=False, indent=1)}
추가 키 "missing": 대화에서 더 물어봐야 채울 수 있는 항목을 한국어 이름(예: "주최·주관", "총 사업비")으로 적은 배열(최대 8개)."""


def _parse(text: str) -> dict:
    t = re.sub(r"^```(?:json)?|```$", "", (text or "").strip(), flags=re.M).strip()
    a, b = t.find("{"), t.rfind("}")
    if a < 0 or b < 0:
        raise ValueError("JSON을 찾지 못했어요")
    return json.loads(t[a:b + 1])


def write_plan(transcript: list, selections: str = "") -> dict:
    lines = [f"{'사용자' if m.get('role') == 'user' else '대키미봇'}: {str(m.get('text', ''))[:600]}"
             for m in transcript[-40:] if str(m.get("text", "")).strip()]
    q = "## 대화 기록\n" + "\n".join(lines) + (f"\n\n## 사용자가 고른 선택\n{selections}" if selections else "") + \
        "\n\n위 내용으로 기획안 JSON을 작성해."
    searches = []

    def search(query):
        searches.append(query)
        return TOOL_FUNCS["search_docs"](query)

    raw = run_agent(q, SYSTEM, [TOOL_SPECS["search_docs"]], {"search_docs": search},
                    GEMINI_MODEL, GEMINI_API_KEY, max_steps=8, verbose=False)
    f = _parse(raw)
    f["_searches"] = searches
    return f
