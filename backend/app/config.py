from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import os


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/platform.db"

    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ENVIRONMENT: str = "development"

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # LLM providers
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_GATEWAY_AGENT_ID: str = ""

    # Slack (optional)
    SLACK_BOT_TOKEN: str = ""
    SLACK_APP_TOKEN: str = ""

    # Groq (optional — free tier at console.groq.com)
    GROQ_API_KEY: str = ""

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
