from typing import Annotated

from duckdb import DuckDBPyConnection
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from fastapi.security import OAuth2PasswordRequestForm

from app.api.dependencies.auth import (
    CurrentUser,
)
from app.core.security import (
    create_access_token,
    verify_password,
)
from app.db.application import (
    get_application_database,
)
from app.repositories.users_repository import (
    get_user_by_username,
)
from app.schemas.auth import TokenResponse
from app.schemas.user import (
    UserInDatabase,
    UserRead,
)

router = APIRouter(
    prefix="/auth",
    tags=["Autenticación"],
)

ApplicationDatabase = Annotated[
    DuckDBPyConnection,
    Depends(get_application_database),
]

LoginForm = Annotated[
    OAuth2PasswordRequestForm,
    Depends(),
]


def public_user(
    user: UserInDatabase,
) -> UserRead:
    public_data = user.model_dump(
        exclude={"password_hash"}
    )

    return UserRead.model_validate(
        public_data
    )

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Iniciar sesión",
)
def login(
    form_data: LoginForm,
    connection: ApplicationDatabase,
) -> TokenResponse:
    user_record = get_user_by_username(
        connection,
        form_data.username,
    )

    if user_record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    user = UserInDatabase.model_validate(
        user_record
    )

    valid_password = verify_password(
        form_data.password,
        user.password_hash,
    )

    if not valid_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    if not user.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario se encuentra inactivo.",
        )

    access_token, expires_in = create_access_token(
        user_id=user.id,
        username=user.username,
        role=user.rol,
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in,
        user=public_user(user),
    )

@router.get(
    "/me",
    response_model=UserRead,
    summary="Obtener el usuario autenticado",
)
def get_authenticated_user(
    current_user: CurrentUser,
) -> UserRead:
    return public_user(current_user)