from functools import cached_property
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    openai_base_url: str = "https://api.openai.com/v1"
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"
    deepface_url: str = "http://deepface:8001"
    sensevoice_url: str = "http://sensevoice:8002"
    database_url: str = "postgresql+asyncpg://emotion:emotion@postgres:5432/emotion"
    auth_secret_key: str = "dev-only-change-this-secret-key-please"
    access_token_expire_minutes: int = 60 * 24
    backend_cors_origins: str = "http://localhost:5173"
    storage_dir: Path = Path("storage")

    @cached_property
    def cors_origins(self) -> list[str]:
        return [item.strip() for item in self.backend_cors_origins.split(",") if item.strip()]

    @cached_property
    def uploads_dir(self) -> Path:
        return self.storage_dir / "uploads"

    @cached_property
    def frames_dir(self) -> Path:
        return self.storage_dir / "frames"

    @cached_property
    def audio_dir(self) -> Path:
        return self.storage_dir / "audio"

    @cached_property
    def reports_dir(self) -> Path:
        return self.storage_dir / "reports"


settings = Settings()
