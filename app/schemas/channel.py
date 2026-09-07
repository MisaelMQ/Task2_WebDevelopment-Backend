from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

ChannelSource = Literal[
    "Agente IA",
    "CleverTap",
    "Encuesta QR",
]


class ChannelBase(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    codigo: str = Field(
        min_length=2,
        max_length=30,
        pattern=r"^[A-Za-z0-9_-]+$",
        examples=["CAN-008"],
    )

    nombre: str = Field(
        min_length=2,
        max_length=100,
        examples=["Agente BCP"],
    )

    fuente: ChannelSource

    activo: bool = True

    descripcion: str | None = Field(
        default=None,
        max_length=255,
    )

    @field_validator("codigo")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.upper()

    @field_validator("descripcion")
    @classmethod
    def normalize_description(
        cls,
        value: str | None,
    ) -> str | None:
        if value == "":
            return None

        return value

class ChannelCreate(ChannelBase):
    pass


class ChannelUpdate(ChannelBase):
    pass

class ChannelRead(ChannelBase):
    id: int
    created_at: datetime
    updated_at: datetime


class ChannelPaginationMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total: int = Field(ge=0)
    total_pages: int = Field(ge=0)


class PaginatedChannels(BaseModel):
    model_config = ConfigDict(extra="forbid")

    data: list[ChannelRead]
    meta: ChannelPaginationMeta