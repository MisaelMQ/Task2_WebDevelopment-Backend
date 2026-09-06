from collections.abc import Generator
import duckdb
from duckdb import DuckDBPyConnection
from app.core.config import get_settings

def open_database(*, read_only: bool = True) -> DuckDBPyConnection:
    settings = get_settings()
    database_path = settings.resolved_duckdb_path

    if not database_path.is_file():
        raise FileNotFoundError(
            f"No se encontró la base DuckDB en: {database_path}"
        )

    return duckdb.connect(
        database=str(database_path),
        read_only=read_only,
    )

def get_database() -> Generator[DuckDBPyConnection, None, None]:
    connection = open_database(read_only=True)

    try:
        yield connection
    finally:
        connection.close()