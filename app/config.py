from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # ── Database ──────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/financeai"

    # ── JWT ───────────────────────────────────────────────────────────────
    JWT_SECRET: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440

    # ── AI provider selector ──────────────────────────────────────────────
    # "gemini"  → Google Gemini (google-genai SDK)
    # "openai"  → OpenAI or any OpenAI-compatible endpoint
    AI_PROVIDER: str = "gemini"

    # ── Google Gemini ─────────────────────────────────────────────────────
    # Key is treated as an opaque non-empty string.
    # No format validation — no AIza prefix check — no regex.
    # Set via environment variable GEMINI_API_KEY only.
    # NEVER exposed to the frontend.
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3-flash-preview"

    # ── OpenAI (fallback) ─────────────────────────────────────────────────
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # ── App / CORS ────────────────────────────────────────────────────────
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    APP_ENV: str = "development"
    DEBUG: bool = True

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }


settings = Settings()
