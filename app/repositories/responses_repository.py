from duckdb import DuckDBPyConnection

from app.core.sources import SourceConfig


def quote_identifier(identifier: str) -> str:
    escaped_identifier = identifier.replace('"', '""')
    return f'"{escaped_identifier}"'


def count_responses(
    connection: DuckDBPyConnection,
    source: SourceConfig,
) -> int:
    table_name = quote_identifier(source.table_name)

    result = connection.execute(
        f"SELECT COUNT(*) FROM {table_name}"
    ).fetchone()

    return int(result[0])