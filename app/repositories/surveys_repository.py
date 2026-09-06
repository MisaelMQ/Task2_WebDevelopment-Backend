from datetime import date
from typing import Any

from duckdb import DuckDBPyConnection

from app.core.nps import calculate_nps_category
from app.schemas.survey import (
    SurveyCreate,
    SurveyUpdate,
)

SURVEY_COLUMNS = """
    e.id,
    e.canal_id,
    c.codigo AS canal_codigo,
    c.nombre AS canal_nombre,
    e.fecha_encuesta,
    e.puntuacion_nps,
    e.categoria_nps,
    e.comentario,
    e.estado,
    e.created_at,
    e.updated_at
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

def build_survey_filters(
    *,
    canal_id: int | None,
    categoria_nps: str | None,
    estado: str | None,
    fecha_desde: date | None,
    fecha_hasta: date | None,
    buscar: str | None,
) -> tuple[str, list[Any]]:
    conditions: list[str] = []
    parameters: list[Any] = []

    if canal_id is not None:
        conditions.append("e.canal_id = ?")
        parameters.append(canal_id)

    if categoria_nps:
        conditions.append(
            "LOWER(e.categoria_nps) = LOWER(?)"
        )
        parameters.append(categoria_nps)

    if estado:
        conditions.append(
            "LOWER(e.estado) = LOWER(?)"
        )
        parameters.append(estado)

    if fecha_desde is not None:
        conditions.append("e.fecha_encuesta >= ?")
        parameters.append(fecha_desde)

    if fecha_hasta is not None:
        conditions.append("e.fecha_encuesta <= ?")
        parameters.append(fecha_hasta)

    if buscar:
        conditions.append(
            """
            COALESCE(e.comentario, '') ILIKE ?
            """
        )
        parameters.append(f"%{buscar.strip()}%")

    if not conditions:
        return "", []

    return (
        " WHERE " + " AND ".join(conditions),
        parameters,
    )

def count_surveys(
    connection: DuckDBPyConnection,
    *,
    canal_id: int | None = None,
    categoria_nps: str | None = None,
    estado: str | None = None,
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
    buscar: str | None = None,
) -> int:
    where_clause, parameters = build_survey_filters(
        canal_id=canal_id,
        categoria_nps=categoria_nps,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        buscar=buscar,
    )

    result = connection.execute(
        f"""
        SELECT COUNT(*)
        FROM encuestas e
        {where_clause}
        """,
        parameters,
    ).fetchone()

    return int(result[0]) if result is not None else 0

def list_surveys(
    connection: DuckDBPyConnection,
    *,
    limit: int,
    offset: int,
    canal_id: int | None = None,
    categoria_nps: str | None = None,
    estado: str | None = None,
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
    buscar: str | None = None,
) -> list[dict[str, Any]]:
    where_clause, parameters = build_survey_filters(
        canal_id=canal_id,
        categoria_nps=categoria_nps,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        buscar=buscar,
    )

    cursor = connection.execute(
        f"""
        SELECT
            {SURVEY_COLUMNS}
        FROM encuestas e
        INNER JOIN canales c
            ON c.id = e.canal_id
        {where_clause}
        ORDER BY e.fecha_encuesta DESC, e.id DESC
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

def get_survey_by_id(
    connection: DuckDBPyConnection,
    survey_id: int,
) -> dict[str, Any] | None:
    cursor = connection.execute(
        f"""
        SELECT
            {SURVEY_COLUMNS}
        FROM encuestas e
        INNER JOIN canales c
            ON c.id = e.canal_id
        WHERE e.id = ?
        LIMIT 1
        """,
        [survey_id],
    )

    return row_to_dictionary(cursor)
def create_survey(
    connection: DuckDBPyConnection,
    survey: SurveyCreate,
) -> dict[str, Any]:
    category = calculate_nps_category(
        survey.puntuacion_nps
    )

    created_row = connection.execute(
        """
        INSERT INTO encuestas (
            canal_id,
            fecha_encuesta,
            puntuacion_nps,
            categoria_nps,
            comentario,
            estado
        )
        VALUES (?, ?, ?, ?, ?, ?)
        RETURNING id
        """,
        [
            survey.canal_id,
            survey.fecha_encuesta,
            survey.puntuacion_nps,
            category,
            survey.comentario,
            survey.estado,
        ],
    ).fetchone()

    if created_row is None:
        raise RuntimeError("No se pudo crear la encuesta.")

    survey_data = get_survey_by_id(
        connection,
        int(created_row[0]),
    )
    if survey_data is None:
        raise RuntimeError("No se pudo recuperar la encuesta creada.")
    return survey_data

def update_survey(
    connection: DuckDBPyConnection,
    survey_id: int,
    survey: SurveyUpdate,
) -> dict[str, Any] | None:
    category = calculate_nps_category(
        survey.puntuacion_nps
    )

    updated_row = connection.execute(
        """
        UPDATE encuestas
        SET
            canal_id = ?,
            fecha_encuesta = ?,
            puntuacion_nps = ?,
            categoria_nps = ?,
            comentario = ?,
            estado = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        RETURNING id
        """,
        [
            survey.canal_id,
            survey.fecha_encuesta,
            survey.puntuacion_nps,
            category,
            survey.comentario,
            survey.estado,
            survey_id,
        ],
    ).fetchone()

    if updated_row is None:
        return None

    return get_survey_by_id(
        connection,
        int(updated_row[0]),
    )

def delete_survey(
    connection: DuckDBPyConnection,
    survey_id: int,
) -> bool:
    deleted_row = connection.execute(
        """
        DELETE FROM encuestas
        WHERE id = ?
        RETURNING id
        """,
        [survey_id],
    ).fetchone()

    return deleted_row is not None

def count_surveys_by_channel(
    connection: DuckDBPyConnection,
    channel_id: int,
) -> int:
    result = connection.execute(
        """
        SELECT COUNT(*)
        FROM encuestas
        WHERE canal_id = ?
        """,
        [channel_id],
    ).fetchone()

    return int(result[0]) if result is not None else 0