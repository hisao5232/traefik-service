# main_api.py
from fastapi import FastAPI, HTTPException
import asyncpg
import os
from typing import List
from pydantic import BaseModel
from datetime import datetime

app = FastAPI(title="Stock News API")

# DB接続情報
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_NAME = os.getenv("POSTGRES_DB")
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "5432")

class NewsArticle(BaseModel):
    source: str
    title: str
    url: str
    scraped_at: datetime

@app.get("/")
def read_root():
    return {"message": "Stock News API is running"}

@app.get("/news", response_model=List[NewsArticle])
async def get_news(limit: int = 30):
    try:
        conn = await asyncpg.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            host=DB_HOST,
            port=DB_PORT
        )
        
        query = "SELECT source, title, url, scraped_at FROM news_articles ORDER BY scraped_at DESC LIMIT $1"
        rows = await conn.fetch(query, limit)
        await conn.close()
        
        # asyncpgのRecordオブジェクトを辞書に変換
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))