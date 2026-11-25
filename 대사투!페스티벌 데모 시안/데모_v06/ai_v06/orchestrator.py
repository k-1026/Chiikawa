"""오케스트레이터: 사용자 질문을 다시 써서 서브에이전트(Agents/*.yaml)에게 지시하고 답을 모은다.
11.17/orchestrator.py 구조(자동 함수 호출 + 호출 기록)를 그대로 쓰고, 도구를 서브에이전트 호출로 바꿨다.
agent_loop.py 는 서브에이전트 실행에 그대로 쓴다."""
import threading
from pathlib import Path

import yaml
from google import genai
from google.genai import types

from agent_loop import run_agent
from config import GEMINI_API_KEY, GEMINI_MODEL
from tool import TOOL_FUNCS, TOOL_SPECS

HERE = Path(__file__).resolve().parent
_client = genai.Client(api_key=GEMINI_API_KEY)
_local = threading.local()

TEMPLATE = (HERE / "지침/서브에이전트_공용템플릿.md").read_text(encoding="utf-8")
REPORT = (HERE / "지침/보고양식.md").read_text(encoding="utf-8")


def load_agents() -> dict:
    agents = {}
    for p in sorted((HERE / "Agents").glob("*.yaml")):
        a = yaml.safe_load(p.read_text(encoding="utf-8"))
        agents[a["name"]] = a
    return agents


AGENTS = load_agents()


def subagent_prompt(a: dict) -> str:
    tools = "\n".join(f"- {t}: {TOOL_SPECS[t]['description']}" for t in a["tools"])
    body = TEMPLATE.format(name=a["name"], role=a["role"].strip(), tools=tools)
    return f"{body}\n\n## 보고 양식\n{REPORT}"


def run_subagent(name: str, instruction: str) -> str:
    a = AGENTS[name]
    searches = []

    def recorder(tool_name):
        def f(**kw):
            searches.append(f"{tool_name}: {next(iter(kw.values()), '')}")
            return TOOL_FUNCS[tool_name](**kw)
        return f

    report = run_agent(
        instruction, subagent_prompt(a),
        [TOOL_SPECS[t] for t in a["tools"]], {t: recorder(t) for t in a["tools"]},
        GEMINI_MODEL, GEMINI_API_KEY, verbose=False)
    _local.steps.append({"agent": name, "instruction": instruction,
                         "searches": searches, "report": report})
    return report


def _make_tool(name: str):
    def tool(instruction: str) -> str:
        return run_subagent(name, instruction)
    tool.__name__ = f"ask_{name}"
    tool.__doc__ = (f"{AGENTS[name]['description']}\n\nArgs:\n"
                    "    instruction: 사용자 질문을 그대로 옮기지 말고, 이 서브에이전트가 찾을 내용 하나를 "
                    "구체적인 지시문으로 다시 쓴 것")
    return tool


SYSTEM_PROMPT = """너는 대구 사투리 축제 기획 질문에 답하는 오케스트레이터야. 직접 검색하지 않고, 서브에이전트에게 지시해서 받은 보고로 답한다.

서브에이전트:
- ask_doc_searcher: 축제 세부지침 문서에서 내용 찾기
- ask_data_analyst: festival_table.csv 수치 표 조회·비교·계산
- ask_web_searcher: 웹에서 외부 사실 찾기 (외부 사실은 이쪽을 먼저)
- ask_researcher: web_searcher가 '일부 못 찾음' 또는 '못 찾음'으로 보고한 외부 사실만 다시 조사

규칙:
- 사용자의 질문을 그대로 넘기지 마. 질문을 서브에이전트가 찾기 좋은 구체적인 지시문으로 다시 쓰고, 질문에 주제가 여럿이면 주제마다 따로 지시해.
- 축제 내부 결정은 docs 폴더(문서·수치 표)에서, 외부 사실은 웹에서 검색한다.
- 답의 문장마다 출처를 괄호로 표기한다.
- 한 출처에서 못 찾은 내용이 있다면 다른 출처로 메꾸지 마. 못 찾은 내용은 '문서에서 찾지 못했습니다' 또는 '웹에서 찾지 못했습니다'로 답한다.
- 일반상식이라 검색이 필요 없는 질문은 서브에이전트를 부르지 않고 답한다.
- 서브에이전트의 보고에 없는 내용은 덧붙이지 않는다.
- 답은 사투리 없이 표준어 존댓말로 쓴다."""


def handle_message(message: str) -> dict:
    """질문 하나를 처리하고, 최종 응답과 이번 턴의 서브에이전트 호출 기록을 반환한다."""
    _local.steps = []
    tools = [_make_tool(n) for n in AGENTS]
    chat = _client.chats.create(
        model=GEMINI_MODEL,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT, tools=tools, temperature=0))
    response = chat.send_message(message)
    return {"reply": response.text, "steps": _local.steps}


if __name__ == "__main__":
    import json
    import sys
    r = handle_message(sys.argv[1])
    for s in r["steps"]:
        print(f"\n[서브에이전트 {s['agent']}] 지시: {s['instruction']}\n  도구: {s['searches']}")
    print("\n== 답변 ==\n" + r["reply"])
