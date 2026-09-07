import argparse
import shutil
from datetime import datetime
from pathlib import Path

import duckdb
from duckdb import DuckDBPyConnection

from app.core.config import get_settings
from app.db.application import initialize_application_database


CHANNELS = (
    (
        "BM",
        "Banca Móvil",
        "CleverTap",
        "Canal histórico de Banca Móvil importado desde respuestas_bm.",
    ),
    (
        "ATM",
        "ATM",
        "Agente IA",
        "Canal histórico de cajeros automáticos importado desde respuestas_ia.",
    ),
    (
        "AGENTES_BCP",
        "Agentes BCP",
        "Agente IA",
        "Canal histórico de agentes BCP importado desde respuestas_ia.",
    ),
    (
        "VENT",
        "Ventanilla",
        "Encuesta QR",
        "Canal histórico de ventanilla importado desde respuestas_qr.",
    ),
    (
        "PLA",
        "Plataforma",
        "Encuesta QR",
        "Canal histórico de plataforma importado desde respuestas_qr.",
    ),
    (
        "TP",
        "Tarjeta Prepago",
        "CleverTap",
        "Canal histórico de Tarjeta Prepago importado desde respuestas_tp.",
    ),
)


HISTORICAL_SOURCES = (
    {
        "table": "respuestas_bm",
        "channel_column": "CANAL",
        "date_column": "FECHA_ENCU",
        "comment_column": "COMENTARIO",
        "channel_mapping": {"BM": "BM"},
    },
    {
        "table": "respuestas_ia",
        "channel_column": "SERVICIO",
        "date_column": "FECHA",
        "comment_column": "COMENTARIO_CLIENTE",
        "channel_mapping": {
            "ATM": "ATM",
            "AGENTES BCP": "AGENTES_BCP",
        },
    },
    {
        "table": "respuestas_qr",
        "channel_column": "CANAL",
        "date_column": "FECHA_ENCU",
        "comment_column": "COM_OTRO",
        "channel_mapping": {
            "VENT": "VENT",
            "PLA": "PLA",
        },
    },
    {
        "table": "respuestas_tp",
        "channel_column": "CANAL",
        "date_column": "FECHA_ENCU",
        "comment_column": "COMENTARIO",
        "channel_mapping": {"TP": "TP"},
    },
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Importar las respuestas históricas con NPS válido en las tablas "
            "canales y encuestas de application.duckdb."
        )
    )
    parser.add_argument(
        "--without-backup",
        action="store_true",
        help="No crear una copia de seguridad antes de importar.",
    )
    return parser.parse_args()


def quote_identifier(identifier: str) -> str:
    return f'"{identifier.replace(chr(34), chr(34) * 2)}"'


def quote_path(path: Path) -> str:
    return str(path).replace("'", "''")


def create_backup(database_path: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = database_path.with_name(
        f"{database_path.stem}.before-historical-import-{timestamp}"
        f"{database_path.suffix}"
    )
    shutil.copy2(database_path, backup_path)
    return backup_path


def count_rows(
    connection: DuckDBPyConnection,
    table_name: str,
) -> int:
    result = connection.execute(
        f"SELECT COUNT(*) FROM {quote_identifier(table_name)}"
    ).fetchone()
    return int(result[0]) if result is not None else 0


def ensure_empty_destination(
    connection: DuckDBPyConnection,
) -> None:
    channel_count = count_rows(connection, "canales")
    survey_count = count_rows(connection, "encuestas")

    if channel_count or survey_count:
        raise RuntimeError(
            "La importación se canceló para evitar duplicados: "
            f"application.duckdb ya contiene {channel_count} canal(es) y "
            f"{survey_count} encuesta(s)."
        )


def insert_channels(connection: DuckDBPyConnection) -> None:
    connection.executemany(
        """
        INSERT INTO canales (
            codigo,
            nombre,
            fuente,
            activo,
            descripcion
        )
        VALUES (?, ?, ?, TRUE, ?)
        """,
        CHANNELS,
    )


def import_source(
    connection: DuckDBPyConnection,
    source: dict,
) -> int:
    table = quote_identifier(source["table"])
    channel_column = quote_identifier(source["channel_column"])
    date_column = quote_identifier(source["date_column"])
    comment_column = quote_identifier(source["comment_column"])
    channel_mapping = source["channel_mapping"]
    mapping_values = ", ".join("(?, ?)" for _ in channel_mapping)
    mapping_parameters = [
        value
        for source_channel, destination_code in channel_mapping.items()
        for value in (source_channel, destination_code)
    ]
    surveys_before = count_rows(connection, "encuestas")

    connection.execute(
        f"""
        INSERT INTO encuestas (
            canal_id,
            fecha_encuesta,
            puntuacion_nps,
            categoria_nps,
            comentario,
            estado,
            created_at,
            updated_at
        )
        WITH channel_mapping(source_channel, destination_code) AS (
            VALUES {mapping_values}
        )
        SELECT
            c.id,
            CAST(TRY_STRPTIME(h.{date_column}, '%d/%m/%Y') AS DATE),
            TRY_CAST(h."NPS" AS INTEGER) AS puntuacion_nps,
            CASE
                WHEN TRY_CAST(h."NPS" AS INTEGER) BETWEEN 9 AND 10
                    THEN 'Promotor'
                WHEN TRY_CAST(h."NPS" AS INTEGER) BETWEEN 7 AND 8
                    THEN 'Pasivo'
                ELSE 'Detractor'
            END AS categoria_nps,
            NULLIF(
                LEFT(TRIM(CAST(h.{comment_column} AS VARCHAR)), 1000),
                ''
            ) AS comentario,
            'Revisada' AS estado,
            COALESCE(h."Created", CURRENT_TIMESTAMP) AS created_at,
            COALESCE(h."Modified", h."Created", CURRENT_TIMESTAMP)
                AS updated_at
        FROM historical.{table} AS h
        INNER JOIN channel_mapping AS mapping
            ON mapping.source_channel = CAST(h.{channel_column} AS VARCHAR)
        INNER JOIN main.canales AS c
            ON c.codigo = mapping.destination_code
        WHERE
            TRY_CAST(h."NPS" AS INTEGER) BETWEEN 0 AND 10
            AND TRY_STRPTIME(h.{date_column}, '%d/%m/%Y') IS NOT NULL
        """,
        mapping_parameters,
    )

    return count_rows(connection, "encuestas") - surveys_before


def validate_result(
    connection: DuckDBPyConnection,
    expected_surveys: int,
) -> None:
    channel_count = count_rows(connection, "canales")
    survey_count = count_rows(connection, "encuestas")

    if channel_count != len(CHANNELS):
        raise RuntimeError(
            f"Se esperaban {len(CHANNELS)} canales y se obtuvieron "
            f"{channel_count}."
        )

    if survey_count != expected_surveys:
        raise RuntimeError(
            f"Se esperaban {expected_surveys} encuestas y se obtuvieron "
            f"{survey_count}."
        )

    invalid_surveys = connection.execute(
        """
        SELECT COUNT(*)
        FROM encuestas
        WHERE
            puntuacion_nps NOT BETWEEN 0 AND 10
            OR fecha_encuesta IS NULL
            OR categoria_nps NOT IN ('Promotor', 'Pasivo', 'Detractor')
        """
    ).fetchone()

    if invalid_surveys is None or int(invalid_surveys[0]) != 0:
        raise RuntimeError(
            "La validación encontró encuestas inválidas después de importar."
        )


def main() -> int:
    arguments = parse_arguments()
    settings = get_settings()
    historical_path = settings.resolved_duckdb_path
    application_path = settings.resolved_app_duckdb_path

    if not historical_path.is_file():
        print(f"No se encontró la base histórica: {historical_path}")
        return 1

    if historical_path == application_path:
        print("Las bases histórica y de aplicación deben ser archivos distintos.")
        return 1

    initialize_application_database()

    validation_connection = duckdb.connect(
        str(application_path),
        read_only=True,
    )
    try:
        ensure_empty_destination(validation_connection)
    except RuntimeError as error:
        print(f"Error: {error}")
        return 1
    finally:
        validation_connection.close()

    backup_path = None
    if not arguments.without_backup:
        backup_path = create_backup(application_path)

    connection = duckdb.connect(str(application_path), read_only=False)

    try:
        connection.execute(
            f"ATTACH '{quote_path(historical_path)}' "
            "AS historical (READ_ONLY)"
        )
        connection.execute("BEGIN TRANSACTION")

        try:
            insert_channels(connection)
            imported_by_source = {
                source["table"]: import_source(connection, source)
                for source in HISTORICAL_SOURCES
            }
            expected_surveys = sum(imported_by_source.values())
            validate_result(connection, expected_surveys)
            connection.execute("COMMIT")
        except Exception:
            connection.execute("ROLLBACK")
            raise
    except (duckdb.Error, RuntimeError) as error:
        print(f"Error: {error}")
        if backup_path is not None:
            print(f"Copia de seguridad disponible en: {backup_path}")
        return 1
    finally:
        connection.close()

    print("Importación completada correctamente.")
    for table_name, imported_count in imported_by_source.items():
        print(f"{table_name}: {imported_count} encuesta(s)")
    print(f"Canales importados: {len(CHANNELS)}")
    print(f"Encuestas importadas: {expected_surveys}")
    if backup_path is not None:
        print(f"Copia de seguridad: {backup_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
