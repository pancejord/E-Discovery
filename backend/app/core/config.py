from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Litigation & eDiscovery Analytics API"
    app_version: str = "0.1.0"
    database_url: str = "sqlite:///./dev.db"
    upload_dir: str = "storage/uploads"
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "document_chunks"
    qdrant_enabled: bool = False
    embedding_dimension: int = 384
    openai_api_key: str | None = None
    ai_provider: str = "local"
    ai_model: str = "gpt-4.1-mini"
    ai_external_enabled: bool = False
    auth_enabled: bool = False
    api_keys: str | None = None
    audit_retention_days: int = 365

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
