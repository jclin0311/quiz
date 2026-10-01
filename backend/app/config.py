import os
from dataclasses import dataclass


def _bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./quiz.db")
    google_client_id: str = os.getenv("GOOGLE_CLIENT_ID", "")
    # Dev login lets you try the app without configuring Google OAuth.
    # It defaults to on only when no Google client id is configured.
    allow_dev_login: bool = _bool("ALLOW_DEV_LOGIN", not os.getenv("GOOGLE_CLIENT_ID"))
    session_days: int = int(os.getenv("SESSION_DAYS", "30"))
    cookie_secure: bool = _bool("COOKIE_SECURE", False)
    llm_model: str = os.getenv("LLM_MODEL", "claude-opus-5-5")
    llm_timeout_seconds: float = float(os.getenv("LLM_TIMEOUT_SECONDS", "30"))
    llm_enabled: bool = _bool("LLM_ENABLED", True)


settings = Settings()

SESSION_COOKIE = "quiz_session"
