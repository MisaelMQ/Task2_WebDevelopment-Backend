from dataclasses import dataclass
from typing import Any
from duckdb import DuckDBPyConnection
from app.core.sources import SourceConfig


FILTER_COLUMNS: dict[str, dict[str, str]] = {
    "bm": {
        "canal": '"CANAL"',
        "periodo": '"PERIODO"',
        "categoria_nps": '"ET_NPS"',
        "nps": '"NPS"',
        "comentario": '"COMENTARIO"',
    },
    "ia": {
        "canal": '"SERVICIO"',
        "periodo": '"PERIODO"',
        "categoria_nps": '"ET_NPS"',
        "nps": '"NPS"',
        "comentario": '"COMENTARIO_CLIENTE"',
    },
    "qr": {
        "canal": '"CANAL"',
        "periodo": '"PERIODO"',
        "categoria_nps": '"ET_NPS"',
        "nps": '"NPS"',
        "comentario": '"COM_OTRO"',
    },
    "tp": {
        "canal": '"CANAL"',
        "periodo": '"PERIODO"',
        "categoria_nps": '"ET_NPS"',
        "nps": '"NPS"',
        "comentario": '"COMENTARIO"',
    },
}


@dataclass(frozen=True, slots=True)
class ResponseFilters:
    periodo: str | None = None
    categoria_nps: str | None = None
    canal: str | None = None
    nps: int | None = None
    buscar: str | None = None


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


def row_to_dictionary(
    cursor,
) -> dict[str, Any] | None:
    row = cursor.fetchone()

    if row is None:
        return None

    column_names = [
        column[0]
        for column in cursor.description
    ]

    return dict(zip(column_names, row, strict=True))


def build_filter_clause(
    source: SourceConfig,
    filters: ResponseFilters | None,
) -> tuple[str, list[Any]]:
    if filters is None:
        return "", []

    columns = FILTER_COLUMNS[source.key]
    conditions: list[str] = []
    parameters: list[Any] = []

    if filters.periodo:
        conditions.append(
            f"""
            LOWER(CAST({columns["periodo"]} AS VARCHAR))
            = LOWER(?)
            """
        )
        parameters.append(filters.periodo.strip())

    if filters.categoria_nps:
        conditions.append(
            f"""
            LOWER(CAST({columns["categoria_nps"]} AS VARCHAR))
            = LOWER(?)
            """
        )
        parameters.append(filters.categoria_nps.strip())

    if filters.canal:
        conditions.append(
            f"""
            LOWER(CAST({columns["canal"]} AS VARCHAR))
            = LOWER(?)
            """
        )
        parameters.append(filters.canal.strip())

    if filters.nps is not None:
        conditions.append(
            f"""
            TRY_CAST({columns["nps"]} AS INTEGER) = ?
            """
        )
        parameters.append(filters.nps)

    if filters.buscar:
        conditions.append(
            f"""
            COALESCE(
                CAST({columns["comentario"]} AS VARCHAR),
                ''
            ) ILIKE ?
            """
        )
        parameters.append(f"%{filters.buscar.strip()}%")

    if not conditions:
        return "", []

    where_clause = " WHERE " + " AND ".join(conditions)

    return where_clause, parameters


def count_responses(
    connection: DuckDBPyConnection,
    source: SourceConfig,
    *,
    filters: ResponseFilters | None = None,
) -> int:
    table_name = quote_identifier(source.table_name)

    where_clause, parameters = build_filter_clause(
        source,
        filters,
    )

    result = connection.execute(
        f"""
        SELECT COUNT(*)
        FROM {table_name}
        {where_clause}
        """,
        parameters,
    ).fetchone()

    return int(result[0])


def list_responses(
    connection: DuckDBPyConnection,
    source: SourceConfig,
    *,
    limit: int,
    offset: int,
    filters: ResponseFilters | None = None,
) -> list[dict[str, Any]]:
    table_name = quote_identifier(source.table_name)

    where_clause, filter_parameters = build_filter_clause(
        source,
        filters,
    )

    query = f"""
        SELECT
            {source.projection}
        FROM {table_name}
        {where_clause}
        ORDER BY "Id"
        LIMIT ?
        OFFSET ?
    """

    parameters = [
        source.key,
        *filter_parameters,
        limit,
        offset,
    ]

    cursor = connection.execute(
        query,
        parameters,
    )

    return rows_to_dictionaries(cursor)


def get_response_by_id(
    connection: DuckDBPyConnection,
    source: SourceConfig,
    *,
    record_id: int,
) -> dict[str, Any] | None:
    table_name = quote_identifier(source.table_name)

    query = f"""
        SELECT
            {source.projection}
        FROM {table_name}
        WHERE "Id" = ?
        LIMIT 1
    """

    cursor = connection.execute(
        query,
        [
            source.key,
            record_id,
        ],
    )

    return row_to_dictionary(cursor)