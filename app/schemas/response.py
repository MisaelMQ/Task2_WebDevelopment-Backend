from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class ResponseSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    fuente: str
    canal: str | None = None
    periodo: str | None = None
    per_semana: str | None = None
    fecha_encuesta: str | None = None
    nps: int | None = Field(default=None, ge=0, le=10)
    categoria_nps: str | None = None
    comentario: str | None = None
    etiqueta_general: str | None = None
    etiqueta_positiva: str | None = None
    etiqueta_negativa: str | None = None
    operacion: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class PaginationMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total: int = Field(ge=0)
    total_pages: int = Field(ge=0)


class PaginatedResponses(BaseModel):
    model_config = ConfigDict(extra="forbid")

    data: list[ResponseSummary]
    meta: PaginationMeta