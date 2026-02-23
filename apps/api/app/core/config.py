from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/rag_assistant"
    database_url_sync: str = "postgresql://postgres:postgres@localhost:5432/rag_assistant"


settings = Settings()
