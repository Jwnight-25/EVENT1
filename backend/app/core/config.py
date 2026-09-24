from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    database_url: str | None = None
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    ai_provider: str = "openai"
    openai_api_key: str | None = None
    openai_model: str = "gpt-6-luna"
    ai_web_search_enabled: bool = True
    max_csv_upload_bytes: int = 25 * 1024 * 1024

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
