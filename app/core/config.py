from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application configuration, sourced from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "embedding-reranking"
    app_env: str = "development"
    log_level: str = "INFO"

    auth_service_base_url: str = "http://localhost:8081"

    embedding_model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"
    embedding_device: str = "cpu"

    vector_db_base_url: str = "http://vector-db:8002"
    vector_db_timeout_seconds: int = 30


@lru_cache
def get_settings() -> Settings:
    return Settings()
