"""경로와 환경변수. 키·모델명은 환경변수(GEMINI_API_KEY, GEMINI_MODEL)에서 읽는다. 컴퓨터의 고정 경로를 쓰지 않는다."""
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOCS_DIR = HERE / 'docs'  # rgh.py, festival_table.csv (지침 문서 검색은 Supabase 표 knowledge_chunks 를 쓴다)
sys.path.append(str(DOCS_DIR))

import rgh  # noqa: E402

rgh.load_env()  # 환경변수가 이미 있으면 그대로 쓴다
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL")
if not GEMINI_API_KEY or not GEMINI_MODEL:
    raise ValueError("환경변수 GEMINI_API_KEY 와 GEMINI_MODEL 을 설정하세요.")
TABLE_CSV = DOCS_DIR / "festival_table.csv"
