from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


BASE_DIR = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    app_name: str = "BCP Tablero NPS API"
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"

    duckdb_path: Path = Path(
        "data/sharepoint_lists.duckdb"
    )

    app_duckdb_path: Path = Path(
        "data/application.duckdb"
    )

    jwt_secret_key: SecretStr

    jwt_algorithm: str = "HS256"

    access_token_expire_minutes: int = Field(
        default=60,
        ge=5,
        le=1440,
    )

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    cors_origins: str = (
    "http://localhost:5173,"
    "http://127.0.0.1:5173,"
    "http://localhost:3000,"
    "http://127.0.0.1:3000"
)

    @staticmethod
    def resolve_path(path: Path) -> Path:
        expanded_path = path.expanduser()

        if expanded_path.is_absolute():
            return expanded_path.resolve()

        return (BASE_DIR / expanded_path).resolve()

    @property
    def resolved_duckdb_path(self) -> Path:
        return self.resolve_path(self.duckdb_path)

    @property
    def resolved_app_duckdb_path(self) -> Path:
        return self.resolve_path(
            self.app_duckdb_path
        )
    
    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # pyright: ignore[reportCallIssue]