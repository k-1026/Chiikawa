from google import genai
from config import GEMINI_API_KEY, GEMINI_MODEL

# Gemini 클라이언트 생성
client = genai.Client(api_key=GEMINI_API_KEY)

# 간단한 메시지를 보내 연결 확인
response = client.models.generate_content(
    model=GEMINI_MODEL,
    contents="안녕",
)

print(response.text)
