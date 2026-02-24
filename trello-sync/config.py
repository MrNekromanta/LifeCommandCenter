"""Configuration via environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    trello_api_key: str
    trello_token: str
    database_url: str = "postgresql://postgres:postgres@localhost:5432/trello_sync"
    sync_interval_minutes: int = 60
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
