from typing import Any
from duckdb import DuckDBPyConnection

from app.schemas.channel import (
    ChannelCreate,
    ChannelUpdate,
)

CHANNEL_COLUMNS = """
    id,
    codigo,
    nombre,
    fuente,
    activo,
    descripcion,
    created_at,
    updated_at
"""

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

def count_channels(
    connection: DuckDBPyConnection,
    *,
    buscar: str | None = None,
    fuente: str | None = None,
) -> int:
    where_clause, parameters = build_channel_filters(
        buscar=buscar,
        fuente=fuente,
    )

    result = connection.execute(
        f"""
        SELECT COUNT(*)
        FROM canales
        {where_clause}
        """,
        parameters,
    ).fetchone()

    return int(result[0])

def build_channel_filters(
    *,
    buscar: str | None,
    fuente: str | None,
) -> tuple[str, list[Any]]:
    conditions: list[str] = []
    parameters: list[Any] = []

    if buscar:
        search_pattern = f"%{buscar.strip()}%"

        conditions.append(
            """
            (
                codigo ILIKE ?
                OR nombre ILIKE ?
            )
            """
        )

        parameters.extend([
            search_pattern,
            search_pattern,
        ])

    if fuente:
        conditions.append(
            "LOWER(fuente) = LOWER(?)"
        )
        parameters.append(fuente.strip())

    if not conditions:
        return "", []

    return (
        " WHERE " + " AND ".join(conditions),
        parameters,
    )

def list_channels(
    connection: DuckDBPyConnection,
    *,
    limit: int,
    offset: int,
    buscar: str | None = None,
    fuente: str | None = None,
) -> list[dict[str, Any]]:
    where_clause, parameters = build_channel_filters(
        buscar=buscar,
        fuente=fuente,
    )

    cursor = connection.execute(
        f"""
        SELECT
            {CHANNEL_COLUMNS}
        FROM canales
        {where_clause}
        ORDER BY created_at DESC, id DESC
        LIMIT ?
        OFFSET ?
        """,
        [
            *parameters,
            limit,
            offset,
        ],
    )

    return rows_to_dictionaries(cursor)

def get_channel_by_id(
    connection: DuckDBPyConnection,
    channel_id: int,
) -> dict[str, Any] | None:
    cursor = connection.execute(
        f"""
        SELECT
            {CHANNEL_COLUMNS}
        FROM canales
        WHERE id = ?
        LIMIT 1
        """,
        [channel_id],
    )

    return row_to_dictionary(cursor)

def get_channel_by_code(
    connection: DuckDBPyConnection,
    code: str,
) -> dict[str, Any] | None:
    cursor = connection.execute(
        f"""
        SELECT
            {CHANNEL_COLUMNS}
        FROM canales
        WHERE LOWER(codigo) = LOWER(?)
        LIMIT 1
        """,
        [code],
    )

    return row_to_dictionary(cursor)

def create_channel(
    connection: DuckDBPyConnection,
    channel: ChannelCreate,
) -> dict[str, Any]:
    cursor = connection.execute(
        f"""
        INSERT INTO canales (
            codigo,
            nombre,
            fuente,
            activo,
            descripcion
        )
        VALUES (?, ?, ?, ?, ?)
        RETURNING
            {CHANNEL_COLUMNS}
        """,
        [
            channel.codigo,
            channel.nombre,
            channel.fuente,
            channel.activo,
            channel.descripcion,
        ],
    )

    return row_to_dictionary(cursor)

def update_channel(
    connection: DuckDBPyConnection,
    channel_id: int,
    channel: ChannelUpdate,
) -> dict[str, Any] | None:
    cursor = connection.execute(
        f"""
        UPDATE canales
        SET
            codigo = ?,
            nombre = ?,
            fuente = ?,
            activo = ?,
            descripcion = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        RETURNING
            {CHANNEL_COLUMNS}
        """,
        [
            channel.codigo,
            channel.nombre,
            channel.fuente,
            channel.activo,
            channel.descripcion,
            channel_id,
        ],
    )

    return row_to_dictionary(cursor)

def delete_channel(
    connection: DuckDBPyConnection,
    channel_id: int,
) -> bool:
    deleted_row = connection.execute(
        """
        DELETE FROM canales
        WHERE id = ?
        RETURNING id
        """,
        [channel_id],
    ).fetchone()

    return deleted_row is not None