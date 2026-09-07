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
        create_channels_schema(connection)
        create_surveys_schema(connection)
        create_users_schema(connection)
    finally:
        connection.close()


def create_channels_schema(
    connection: DuckDBPyConnection,
) -> None:
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


def create_surveys_schema(
    connection: DuckDBPyConnection,
) -> None:
    connection.execute(
        """
        CREATE SEQUENCE IF NOT EXISTS
            encuestas_id_seq
        START 1
        """
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS encuestas (
            id BIGINT PRIMARY KEY
                DEFAULT nextval('encuestas_id_seq'),

            canal_id BIGINT NOT NULL
                REFERENCES canales(id),

            fecha_encuesta DATE NOT NULL,

            puntuacion_nps INTEGER NOT NULL
                CHECK (
                    puntuacion_nps BETWEEN 0 AND 10
                ),

            categoria_nps VARCHAR NOT NULL
                CHECK (
                    categoria_nps IN (
                        'Detractor',
                        'Pasivo',
                        'Promotor'
                    )
                ),

            comentario VARCHAR,

            estado VARCHAR NOT NULL
                DEFAULT 'Pendiente'
                CHECK (
                    estado IN (
                        'Pendiente',
                        'Revisada'
                    )
                ),

            created_at TIMESTAMP NOT NULL
                DEFAULT CURRENT_TIMESTAMP,

            updated_at TIMESTAMP NOT NULL
                DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

def create_users_schema(
    connection: DuckDBPyConnection,
) -> None:
    connection.execute(
        """
        CREATE SEQUENCE IF NOT EXISTS
            usuarios_id_seq
        START 1
        """
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id BIGINT PRIMARY KEY
                DEFAULT nextval('usuarios_id_seq'),

            username VARCHAR NOT NULL UNIQUE,

            password_hash VARCHAR NOT NULL,

            nombre VARCHAR NOT NULL,

            rol VARCHAR NOT NULL
                CHECK (
                    rol IN (
                        'admin',
                        'lector'
                    )
                ),

            activo BOOLEAN NOT NULL
                DEFAULT TRUE,

            created_at TIMESTAMP NOT NULL
                DEFAULT CURRENT_TIMESTAMP,

            updated_at TIMESTAMP NOT NULL
                DEFAULT CURRENT_TIMESTAMP
        )
        """
    )