
# pyrefly: ignore [missing-import]
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "Enterprise AI Assistant"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "CHANGE_THIS_TO_A_SECURE_SECRET_IN_PRODUCTION"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # Rate Limiting Defaults
    RATE_LIMIT_TOKENS: int = 20
    RATE_LIMIT_FILL_RATE: float = 1.0  # Tokens per second

    class Config:
        env_file = ".env"

settings = Settings()