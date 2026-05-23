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

    wechat_appid: str | None = None
    wechat_appsecret: str | None = None
    wechat_api_base_url: str = "https://api.weixin.qq.com"
    wechat_api_timeout_seconds: float = 10.0

    ai_api_key: str | None = None
    ai_base_url: str | None = None
    ai_provider: str = "coze"
    coze_stream_run_url: str | None = None
    coze_token: str | None = None
    coze_project_id: int | None = None

    chukou_api_base_url: str | None = None
    chukou_access_token: str | None = None
    chukou_timeout_seconds: float = 30.0

    log_level: str = "INFO"


settings = Settings()
