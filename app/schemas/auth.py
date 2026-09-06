from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from app.schemas.user import UserRead


class TokenResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    access_token: str

    token_type: Literal["bearer"] = "bearer"

    expires_in: int = Field(
        gt=0,
        description="Vigencia del token en segundos.",
    )

    user: UserRead