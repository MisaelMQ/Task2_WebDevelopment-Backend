from pydantic import BaseModel, ConfigDict, Field

class SourceSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str = Field(description="Identificador utilizado en las rutas de la API.")
    name: str = Field(description="Nombre visible de la fuente.")
    description: str
    record_count: int = Field(ge=0)