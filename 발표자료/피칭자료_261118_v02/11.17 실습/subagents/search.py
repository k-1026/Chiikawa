from google import genai
from config import GEMINI_API_KEY, GEMINI_MODEL

_client = genai.Client(api_key=GEMINI_API_KEY)


def web_search(query: str) -> str:
    """구글 검색으로 최신 정보를 찾아서 답변합니다.

    Args:
        query: 검색할 질문이나 키워드
    """
    # Gemini의 내장 구글 검색 그라운딩 도구를 사용해 검색 기반 답변을 생성
    interaction = _client.interactions.create(
        model=GEMINI_MODEL,
        input=query,
        tools=[{"type": "google_search"}],
    )
    return interaction.output_text
