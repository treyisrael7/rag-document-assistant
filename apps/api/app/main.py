import asyncio

from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from starlette.responses import JSONResponse

from app.core.config import settings
from app.core.middleware import DemoGateMiddleware, RateLimitMiddleware
from app.routers import ask, documents

app = FastAPI(title="RAG Assistant API", version="0.1.0")

app.add_middleware(RateLimitMiddleware)
app.add_middleware(DemoGateMiddleware)


async def _check_db() -> tuple[bool, str | None]:
    """Returns (ok, error_msg). Uses fresh engine to avoid event loop issues in tests."""
    engine = create_async_engine(settings.database_url, echo=False)
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        await engine.dispose()


@app.get("/health")
async def health():
    ok, err = await _check_db()
    if ok:
        return {"status": "ok", "database": "connected"}
    return JSONResponse(
        status_code=503,
        content={"status": "error", "database": "disconnected", "detail": err or "unknown"},
    )


@app.get("/")
async def root():
    return {"message": "RAG Assistant API"}


app.include_router(ask.router)
app.include_router(documents.router)
