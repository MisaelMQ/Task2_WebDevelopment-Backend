from datetime import date, datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from app.core.nps import NpsCategory

SurveyStatus = Literal[
    "Pendiente",
    "Revisada",
]

class SurveyBase(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    canal_id: int = Field(
        gt=0,
        description="Identificador del canal relacionado.",
    )

    fecha_encuesta: date

    puntuacion_nps: int = Field(
        ge=0,
        le=10,
    )

    comentario: str | None = Field(
        default=None,
        max_length=1000,
    )

    estado: SurveyStatus = "Pendiente"

    @field_validator("comentario")
    @classmethod
    def normalize_comment(
        cls,
        value: str | None,
    ) -> str | None:
        if value == "":
            return None

        return value

class SurveyCreate(SurveyBase):
    pass

class SurveyUpdate(SurveyBase):
    pass

class SurveyRead(SurveyBase):
    id: int
    categoria_nps: NpsCategory

    canal_codigo: str
    canal_nombre: str

    created_at: datetime
    updated_at: datetime


class SurveyPaginationMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total: int = Field(ge=0)
    total_pages: int = Field(ge=0)

class PaginatedSurveys(BaseModel):
    model_config = ConfigDict(extra="forbid")

    data: list[SurveyRead]
    meta: SurveyPaginationMeta