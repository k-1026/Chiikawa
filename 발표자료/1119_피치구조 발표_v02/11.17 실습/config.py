import os
from dotenv import load_dotenv

load_dotenv()  # .env 파일을 읽어서 환경변수로 등록

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # Gemini API 키
GEMINI_MODEL = os.getenv("GEMINI_MODEL")  # 사용할 Gemini 모델명

if not GEMINI_API_KEY or not GEMINI_MODEL:
    raise ValueError(".env 파일에 GEMINI_API_KEY와 GEMINI_MODEL을 설정하세요.")
