"""Configuração central da aplicação via variáveis de ambiente."""
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Gamificação QR - Evento IFMT"
    app_env: str = "development"
    app_base_url: str = "http://127.0.0.1:8000"
    event_timezone: str = "America/Cuiaba"
    log_level: str = "INFO"

    supabase_url: str = ""
    supabase_secret_key: str = ""

    participant_cookie_name: str = "event_session"
    participant_session_days: int = 30
    session_cookie_secure: bool = False

    admin_password_hash: str = ""
    admin_session_secret: str = Field(default="change-me", min_length=8)
    admin_cookie_name: str = "event_admin"
    admin_session_hours: int = 12

    blocked_nick_terms: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
