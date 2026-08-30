import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Enterprise AI Assistant"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "CHANGE_THIS_TO_A_SECURE_SECRET_IN_PRODUCTION"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # Rate Limiting Defaults
    RATE_LIMIT_TOKENS: int = 20
    RATE_LIMIT_FILL_RATE: float = 1.0  # Tokens per second

    # OpenAI & Embedding Config
    OPENAI_API_KEY: str = ""
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSION: int = 1536

    # Pinecone Vector DB Config
    PINECONE_API_KEY: str = ""
    PINECONE_INDEX_NAME: str = "enterprise-knowledge-base"
    PINECONE_ENVIRONMENT: Optional[str] = None

    # LangSmith Observability
    LANGSMITH_TRACING: str = "true"
    LANGSMITH_ENDPOINT: str = "https://api.smith.langchain.com"
    LANGSMITH_API_KEY: Optional[str] = None
    LANGSMITH_PROJECT: str = "enterprise-ai-assistant"

    LANGCHAIN_TRACING_V2: str = "true"
    LANGCHAIN_ENDPOINT: str = "https://api.smith.langchain.com"
    LANGCHAIN_API_KEY: Optional[str] = None
    LANGCHAIN_PROJECT: str = "enterprise-ai-assistant"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

# Synchronize settings into os.environ for LangChain and LangSmith automatic tracing
api_key = settings.LANGSMITH_API_KEY or settings.LANGCHAIN_API_KEY
project_name = settings.LANGSMITH_PROJECT or settings.LANGCHAIN_PROJECT or "enterprise-ai-assistant"
endpoint = settings.LANGSMITH_ENDPOINT or settings.LANGCHAIN_ENDPOINT or "https://api.smith.langchain.com"

if api_key:
    os.environ["LANGSMITH_API_KEY"] = api_key
    os.environ["LANGCHAIN_API_KEY"] = api_key

os.environ["LANGSMITH_TRACING"] = settings.LANGSMITH_TRACING or settings.LANGCHAIN_TRACING_V2 or "true"
os.environ["LANGCHAIN_TRACING_V2"] = os.environ["LANGSMITH_TRACING"]
os.environ["LANGSMITH_ENDPOINT"] = endpoint
os.environ["LANGCHAIN_ENDPOINT"] = endpoint
os.environ["LANGSMITH_PROJECT"] = project_name
os.environ["LANGCHAIN_PROJECT"] = project_name

if settings.OPENAI_API_KEY:
    os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY