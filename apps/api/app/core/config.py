from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/rag_assistant"
    database_url_sync: str = "postgresql://postgres:postgres@localhost:5432/rag_assistant"

    # Demo gate
    demo_key: str | None = None  # DEMO_KEY env; if set, require x-demo-key header on non-public routes

    # Hard limits (config via env)
    max_pdf_mb: int = 10  # MAX_PDF_MB
    max_pdf_pages: int = 20  # MAX_PDF_PAGES
    max_chunks_per_doc: int = 300  # MAX_CHUNKS_PER_DOC
    top_k_max: int = 8  # TOP_K_MAX
    max_completion_tokens: int = 500  # MAX_COMPLETION_TOKENS


settings = Settings()
