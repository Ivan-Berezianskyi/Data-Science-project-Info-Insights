from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    # Database settings
    database_url: str = "postgresql+psycopg://admin:admin@localhost:5432/chat_history"
    
    # Optional pagination defaults
    default_page_size: int = 20
    max_page_size: int = 100
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


settings = Settings()

