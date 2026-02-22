from fastapi import FastAPI

app = FastAPI(title="RAG Assistant API", version="0.1.0")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/")
async def root():
    return {"message": "RAG Assistant API"}
