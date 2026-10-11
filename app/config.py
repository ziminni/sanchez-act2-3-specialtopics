from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    app_env: str = 'development'
    database_url: str = 'sqlite:///./student_api.db'
    token_ttl_minutes: int = Field(default=120, ge=1, le=10080)
    cors_origins: list[str] = []
    seed_password: str = ''


settings = Settings()
