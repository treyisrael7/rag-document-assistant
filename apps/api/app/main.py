from fastapi import FastAPI, HTTPException
from sqlalchemy import text

from app.db.base import engine

app = FastAPI(title="RAG Assistant API", version="0.1.0")


@app.get("/health")
async def health():
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail={"status": "error", "database": "disconnected", "detail": str(e)})


@app.get("/")
async def root():
    return {"message": "RAG Assistant API"}
