# Dockerfile.api
FROM python:3.10-slim

WORKDIR /app

# 必要なライブラリをインストール
RUN pip install --no-cache-dir fastapi uvicorn asyncpg pydantic

COPY main.py .

# ポート8000で起動
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
