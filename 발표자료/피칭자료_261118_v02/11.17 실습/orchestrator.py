from google import genai
from google.genai import types
from config import GEMINI_API_KEY, GEMINI_MODEL
from subagents.calculator import calculate
from subagents.search import web_search

_client = genai.Client(api_key=GEMINI_API_KEY)

# 서브에이전트 함수들을 도구로 등록한 대화 세션 생성 (자동 함수 호출)
_chat = _client.chats.create(
    model=GEMINI_MODEL,
    config=types.GenerateContentConfig(tools=[calculate, web_search]),
)


def handle_message(message: str) -> dict:
    """사용자 메시지를 오케스트레이터에 전달하고, 최종 응답과 이번 턴의 에이전트 호출 기록을 반환"""
    before = len(_chat.get_history())  # 이번 턴 이전까지의 대화 길이
    response = _chat.send_message(message)
    new_turns = _chat.get_history()[before:]  # 이번 턴에서 새로 쌓인 부분만 추출

    steps = []
    for turn in new_turns:
        for part in turn.parts:
            if part.function_call:
                steps.append({
                    "agent": part.function_call.name,
                    "action": "call",
                    "detail": dict(part.function_call.args),
                })
            elif part.function_response:
                steps.append({
                    "agent": part.function_response.name,
                    "action": "result",
                    "detail": part.function_response.response,
                })

    return {"reply": response.text, "steps": steps}
