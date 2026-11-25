"""범용 에이전트 루프 (google-genai 함수 호출). 도구와 시스템 프롬프트는 호출하는 쪽에서 넘긴다."""
import json

from google import genai
from google.genai import types


def run_agent(question, system_prompt, tool_specs, tool_funcs, model, api_key,
              max_steps=12, verbose=True):
    client = genai.Client(api_key=api_key)
    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        temperature=0,
        tools=[types.Tool(function_declarations=[
            types.FunctionDeclaration(
                name=s["name"], description=s["description"],
                parameters_json_schema=s["parameters"]) for s in tool_specs])],
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )
    contents = [types.Content(role="user", parts=[types.Part(text=question)])]

    for step in range(1, max_steps + 1):
        res = client.models.generate_content(model=model, contents=contents, config=config)
        content = res.candidates[0].content
        calls = [p.function_call for p in (content.parts or []) if p.function_call]
        if not calls:
            return res.text or ""

        contents.append(content)  # 모델 응답을 그대로 이어 붙인다
        parts = []
        for fc in calls:
            args = dict(fc.args or {})
            if verbose:
                print(f"[{step}] 도구 호출: {fc.name}({json.dumps(args, ensure_ascii=False)})")
            func = tool_funcs.get(fc.name)
            try:
                out = func(**args) if func else f"알 수 없는 도구: {fc.name}"
            except Exception as e:
                out = f"도구 실행 오류: {e}"
            parts.append(types.Part.from_function_response(
                name=fc.name, response={"result": out}))
        contents.append(types.Content(role="user", parts=parts))

    return "최대 단계 수에 도달해 답을 만들지 못했습니다."
