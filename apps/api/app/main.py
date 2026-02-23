from fastapi import FastAPI, HTTPException
from sqlalchemy import text

from app.db.base import engine
from app.core.middleware import DemoGateMiddleware, RateLimitMiddleware
from app.routers import ask, documents

app = FastAPI(title="RAG Assistant API", version="0.1.0")

app.add_middleware(RateLimitMiddleware)
app.add_middleware(DemoGateMiddleware)


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


app.include_router(ask.router)
app.include_router(documents.router)
