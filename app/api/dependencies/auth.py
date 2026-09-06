from typing import Annotated

from duckdb import DuckDBPyConnection
from fastapi import (
    Depends,
    HTTPException,
    status,
)
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError

from app.core.security import decode_access_token
from app.db.application import (
    get_application_database,
)
from app.repositories.users_repository import (
    get_user_by_id,
)
from app.schemas.user import UserInDatabase


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login"
)

TokenDependency = Annotated[
    str,
    Depends(oauth2_scheme),
]

ApplicationDatabase = Annotated[
    DuckDBPyConnection,
    Depends(get_application_database),
]

def credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=(
            "No se pudieron validar "
            "las credenciales."
        ),
        headers={
            "WWW-Authenticate": "Bearer",
        },
    )

def get_current_user(
    token: TokenDependency,
    connection: ApplicationDatabase,
) -> UserInDatabase:
    try:
        payload = decode_access_token(token)

        if payload.get("type") != "access":
            raise credentials_exception()

        subject = payload.get("sub")

        if subject is None:
            raise credentials_exception()

        user_id = int(subject)

    except (
        InvalidTokenError,
        TypeError,
        ValueError,
    ) as error:
        raise credentials_exception() from error

    user_record = get_user_by_id(
        connection,
        user_id,
    )

    if user_record is None:
        raise credentials_exception()

    user = UserInDatabase.model_validate(
        user_record
    )

    if not user.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario se encuentra inactivo.",
        )

    return user

CurrentUser = Annotated[
    UserInDatabase,
    Depends(get_current_user),
]

def require_admin(current_user: CurrentUser) -> UserInDatabase:
    if current_user.rol != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para realizar esta operación.",
        )

    return current_user

AdminUser = Annotated[
    UserInDatabase,
    Depends(require_admin),
]