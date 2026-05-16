from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "Mini Program API"
    app_version: str = "0.1.0"

    database_url: str = "sqlite:///./data/app.db"
    secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_days: int = 7

    ai_api_key: str | None = None
    ai_base_url: str | None = None

    log_level: str = "INFO"


settings = Settings()
