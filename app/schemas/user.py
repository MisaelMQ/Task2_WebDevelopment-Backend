from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

UserRole = Literal[
    "admin",
    "lector",
]

class UserCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    username: str = Field(
        min_length=3,
        max_length=50,
        pattern=r"^[A-Za-z0-9._-]+$",
    )

    nombre: str = Field(
        min_length=2,
        max_length=100,
    )

    rol: UserRole = "lector"

    activo: bool = True

    @field_validator("username")
    @classmethod
    def normalize_username(
        cls,
        value: str,
    ) -> str:
        return value.lower()

class UserRead(UserCreate):
    id: int
    created_at: datetime
    updated_at: datetime

class UserInDatabase(UserRead):
    password_hash: str