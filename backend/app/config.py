from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    APP_NAME: str = "POS-AI SaaS"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "mysql+pymysql://root:password@db:3306/posai"

    # JWT
    SECRET_KEY: str = "change-this-in-production-very-secret-key-32chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480   # 8 jam
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # AI
    OPENAI_API_KEY: str = ""
    OLLAMA_HOST: str = "http://localhost:11434"

    # WhatsApp (WAHA)
    WAHA_URL: str = "http://localhost:3000"
    WAHA_SESSION: str = "default"

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
