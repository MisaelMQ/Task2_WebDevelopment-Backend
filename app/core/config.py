from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    app_name: str = "BCP Tablero NPS API"
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"
    duckdb_path: Path = Path("data/sharepoint_lists.duckdb")

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def resolved_duckdb_path(self) -> Path:
        path = self.duckdb_path.expanduser()

        if path.is_absolute():
            return path.resolve()

        return (BASE_DIR / path).resolve()

@lru_cache
def get_settings() -> Settings:
    return Settings()