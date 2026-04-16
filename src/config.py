import os
import logging

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class Config:
    """Application configuration loaded from environment variables."""

    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # LLM settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")

    # Vector store settings
    VECTOR_STORE_PATH: str = os.getenv("VECTOR_STORE_PATH", "data/vector_store")
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "500"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "50"))

    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "*").split(",")

    # Upload settings
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "data/uploads")
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))

    @classmethod
    def validate(cls) -> list[str]:
        """Return a list of warnings for missing or default configuration."""
        warnings = []
        if cls.SECRET_KEY == "change-me-in-production":
            warnings.append("SECRET_KEY is using default value – set it in .env")
        if not cls.OPENAI_API_KEY:
            warnings.append("OPENAI_API_KEY is not set – LLM features will be unavailable")
        return warnings


config = Config()

# Log any configuration warnings at startup
for warning in Config.validate():
    logger.warning(warning)