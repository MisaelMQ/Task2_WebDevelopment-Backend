from collections.abc import Generator

import duckdb
from duckdb import DuckDBPyConnection

from app.core.config import get_settings


def open_application_database() -> DuckDBPyConnection:
    settings = get_settings()
    database_path = settings.resolved_app_duckdb_path

    database_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    return duckdb.connect(
        database=str(database_path),
        read_only=False,
    )


def get_application_database() -> (
    Generator[DuckDBPyConnection, None, None]
):
    connection = open_application_database()

    try:
        yield connection
    finally:
        connection.close()


def initialize_application_database() -> None:
    connection = open_application_database()

    try:
        connection.execute(
            """
            CREATE SEQUENCE IF NOT EXISTS
                canales_id_seq
            START 1
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS canales (
                id BIGINT PRIMARY KEY
                    DEFAULT nextval('canales_id_seq'),

                codigo VARCHAR NOT NULL UNIQUE,
                nombre VARCHAR NOT NULL,

                fuente VARCHAR NOT NULL
                    CHECK (
                        fuente IN (
                            'Agente IA',
                            'CleverTap',
                            'Encuesta QR'
                        )
                    ),

                activo BOOLEAN NOT NULL
                    DEFAULT TRUE,

                descripcion VARCHAR,

                created_at TIMESTAMP NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                updated_at TIMESTAMP NOT NULL
                    DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    finally:
        connection.close()