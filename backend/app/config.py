import os
import warnings
from dotenv import load_dotenv

load_dotenv()

class Settings:
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "groq")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
    LLM_MODEL_ID: str = os.getenv("LLM_MODEL_ID", "llama-3.3-70b-versatile")

    AMAP_API_KEY: str = os.getenv("AMAP_API_KEY", "")

    UNSPLASH_ACCESS_KEY: str = os.getenv("UNSPLASH_ACCESS_KEY", "")

    AMADEUS_API_KEY: str = os.getenv("AMADEUS_API_KEY", "")
    AMADEUS_API_SECRET: str = os.getenv("AMADEUS_API_SECRET", "")

    JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24  # 24h

    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "10"))

    CORS_ORIGINS: list[str] = [
        o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()
    ] or []

settings = Settings()

if settings.JWT_SECRET == "dev-secret-change-in-production":
    warnings.warn(
        "JWT_SECRET not set — using default dev secret. "
        "Set JWT_SECRET env var in production!",
        stacklevel=1,
    )
