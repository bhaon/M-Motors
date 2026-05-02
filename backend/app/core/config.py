from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # App
    APP_NAME: str = "M-Motors API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql://mmotors:mmotors@db:5432/mmotors"

    # Security
    SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-32"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24h

    # CORS — Next.js frontend
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://mmotors-frontend:3000",
    ]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
