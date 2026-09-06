from typing import Any
from duckdb import DuckDBPyConnection
from app.core.sources import SourceConfig


def quote_identifier(identifier: str) -> str:
    escaped_identifier = identifier.replace('"', '""')
    return f'"{escaped_identifier}"'

def rows_to_dictionaries(
    cursor,
) -> list[dict[str, Any]]:
    column_names = [
        column[0]
        for column in cursor.description
    ]

    return [
        dict(zip(column_names, row, strict=True))
        for row in cursor.fetchall()
    ]

def count_responses(
    connection: DuckDBPyConnection,
    source: SourceConfig,
) -> int:
    table_name = quote_identifier(source.table_name)

    result = connection.execute(
        f"SELECT COUNT(*) FROM {table_name}"
    ).fetchone()

    return int(result[0])

def list_responses(
    connection: DuckDBPyConnection,
    source: SourceConfig,
    *,
    limit: int,
    offset: int,
) -> list[dict[str, Any]]:
    table_name = quote_identifier(source.table_name)

    query = f"""
        SELECT
            {source.projection}
        FROM {table_name}
        ORDER BY "Id"
        LIMIT ?
        OFFSET ?
    """

    cursor = connection.execute(
        query,
        [
            source.key,
            limit,
            offset,
        ],
    )

    return rows_to_dictionaries(cursor)