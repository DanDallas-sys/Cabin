from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database
    database_url: str = "postgresql://user:password@localhost:5432/cabin_db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # OpenAI
    openai_api_key: str = ""

    # Twilio
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_from: str = "whatsapp:+14155238886"

    # Mono
    mono_secret_key: str = ""

    # App
    app_env: str = "development"
    ai_confidence_threshold: float = 0.75

    # Auth
    api_key: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
