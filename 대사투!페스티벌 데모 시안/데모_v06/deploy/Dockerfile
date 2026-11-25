# 대사투! 페스티벌 v06 서버 (Render 등 컨테이너 호스팅용). 아직 실제 빌드·배포는 검증하지 않았다.
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends chromium fonts-noto-cjk && rm -rf /var/lib/apt/lists/*
ENV CHROME_BIN=/usr/bin/chromium HOST=0.0.0.0 PYTHONUNBUFFERED=1
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir "psycopg[binary]" psycopg_pool python-docx python-hwpx python-dotenv google-genai pyyaml pypdf numpy
CMD ["python3","-u","backend/server_v06.py"]
