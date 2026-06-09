from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Litigation & eDiscovery Analytics API"
    app_version: str = "0.1.0"
    database_url: str = "sqlite:///./dev.db"
    upload_dir: str = "storage/uploads"
    qdrant_url: str = "http://localhost:6333"
    openai_api_key: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
