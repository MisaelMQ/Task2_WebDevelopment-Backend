from typing import Annotated

from duckdb import DuckDBPyConnection
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.sources import SOURCES, get_source_config
from app.db.connection import get_database
from app.repositories.responses_repository import count_responses
from app.api.dependencies.auth import get_current_user
from app.schemas.source import SourceSummary

router = APIRouter(
    prefix="/fuentes",
    tags=["Fuentes"],
    dependencies=[Depends(get_current_user)],
)

DatabaseDependency = Annotated[
    DuckDBPyConnection,
    Depends(get_database),
]


@router.get(
    "",
    response_model=list[SourceSummary],
    summary="Listar fuentes disponibles",
)
def list_sources(
    connection: DatabaseDependency,
) -> list[SourceSummary]:
    return [
        SourceSummary(
            key=source.key,
            name=source.display_name,
            description=source.description,
            record_count=count_responses(connection, source),
        )
        for source in SOURCES.values()
    ]


@router.get(
    "/{source_key}",
    response_model=SourceSummary,
    summary="Obtener una fuente",
)
def get_source(
    source_key: str,
    connection: DatabaseDependency,
) -> SourceSummary:
    source = get_source_config(source_key)

    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"La fuente '{source_key}' no existe.",
        )

    return SourceSummary(
        key=source.key,
        name=source.display_name,
        description=source.description,
        record_count=count_responses(connection, source),
    )