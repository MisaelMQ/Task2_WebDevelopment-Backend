from typing import Any
from duckdb import DuckDBPyConnection
from app.schemas.user import UserCreate

USER_PUBLIC_COLUMNS = """
    id,
    username,
    nombre,
    rol,
    activo,
    created_at,
    updated_at
"""

USER_PRIVATE_COLUMNS = """
    id,
    username,
    password_hash,
    nombre,
    rol,
    activo,
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

def get_user_by_username(
    connection: DuckDBPyConnection,
    username: str,
) -> dict[str, Any] | None:
    cursor = connection.execute(
        f"""
        SELECT
            {USER_PRIVATE_COLUMNS}
        FROM usuarios
        WHERE LOWER(username) = LOWER(?)
        LIMIT 1
        """,
        [username.strip()],
    )

    return row_to_dictionary(cursor)

def get_user_by_id(
    connection: DuckDBPyConnection,
    user_id: int,
) -> dict[str, Any] | None:
    cursor = connection.execute(
        f"""
        SELECT
            {USER_PRIVATE_COLUMNS}
        FROM usuarios
        WHERE id = ?
        LIMIT 1
        """,
        [user_id],
    )

    return row_to_dictionary(cursor)

def create_user(
    connection: DuckDBPyConnection,
    user: UserCreate,
    password_hash: str,
) -> dict[str, Any]:
    cursor = connection.execute(
        f"""
        INSERT INTO usuarios (
            username,
            password_hash,
            nombre,
            rol,
            activo
        )
        VALUES (?, ?, ?, ?, ?)
        RETURNING
            {USER_PUBLIC_COLUMNS}
        """,
        [
            user.username,
            password_hash,
            user.nombre,
            user.rol,
            user.activo,
        ],
    )

    return row_to_dictionary(cursor)