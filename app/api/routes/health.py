import duckdb
from fastapi import APIRouter, HTTPException, status

from app.core.config import get_settings
from app.db.connection import open_database

router = APIRouter(tags=["Health"])

def quote_identifier(identifier: str) -> str:
    escaped_identifier = identifier.replace('"', '""')
    return f'"{escaped_identifier}"'


@router.get(
    "/health",
    summary="Verificar el estado de la API",
)
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "message": "BCP Tablero NPS API is running",
    }

@router.get(
    "/database",
    summary="Verificar la conexión con DuckDB",
)
def database_check() -> dict:
    settings = get_settings()
    connection = None

    try:
        connection = open_database(read_only=True)

        table_rows = connection.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'main'
              AND table_type = 'BASE TABLE'
            ORDER BY table_name
            """
        ).fetchall()

        tables = []

        for (table_name,) in table_rows:
            quoted_table = quote_identifier(table_name)

            row_count = connection.execute(
                f"SELECT COUNT(*) FROM {quoted_table}"
            ).fetchone()[0]

            tables.append(
                {
                    "name": table_name,
                    "row_count": row_count,
                }
            )

        return {
            "status": "ok",
            "database": "connected",
            "read_only": True,
            "path": settings.duckdb_path.as_posix(),
            "table_count": len(tables),
            "tables": tables,
        }

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error

    except duckdb.Error as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No se pudo consultar la base de datos DuckDB.",
        ) from error

    finally:
        if connection is not None:
            connection.close()