from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


_BACKEND_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    GOOGLE_API_KEY: str
    QDRANT_URL: str
    QDRANT_API_KEY: str | None = None
    QDRANT_COLLECTION: str = "fr8labs_production"
    QDRANT_DENSE_VECTOR_NAME: str = "dense"
    QDRANT_SPARSE_VECTOR_NAME: str = "sparse"
    RAW_DOCUMENT_DIR: Path = Path("./document_store/raw")
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    DENSE_EMBEDDING_DIM: int = 3072
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-001"
    EMBEDDING_BATCH_SIZE: int = 5
    EMBEDDING_BATCH_DELAY_SEC: float = 2.0
    EMBEDDING_MAX_RETRIES: int = 5

    COHERE_API_KEY: str
    GENERATION_MODEL: str = "gemini-3.5-flash-lite"
    COHERE_RERANK_MODEL: str = "rerank-english-v3.0"
    RETRIEVAL_TOP_K: int = 30
    RERANK_TOP_N: int = 5
    EMAIL_MAX_CHARS: int = 8000
    GENERATION_MAX_OUTPUT_TOKENS: int = 768
    MAX_UPLOAD_BYTES: int = 20_971_520
    LOG_FILE: Path = Path("./logs/fr8labs.log")
    LOG_LEVEL: str = "INFO"
    DRAFT_REPLY_TIMEOUT_SEC: int = 180


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
