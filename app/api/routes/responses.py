from math import ceil
from typing import Annotated

from duckdb import DuckDBPyConnection
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.sources import get_source_config
from app.db.connection import get_database
from app.repositories.responses_repository import (
    count_responses,
    list_responses,
)
from app.schemas.response import (
    PaginatedResponses,
    PaginationMeta,
    ResponseSummary,
)

router = APIRouter(
    prefix="/respuestas",
    tags=["Respuestas"],
)

DatabaseDependency = Annotated[
    DuckDBPyConnection,
    Depends(get_database),
]


@router.get(
    "/{source_key}",
    response_model=PaginatedResponses,
    summary="Listar respuestas de una fuente",
)
def get_responses(
    source_key: str,
    connection: DatabaseDependency,
    page: Annotated[
        int,
        Query(
            ge=1,
            description="Número de página solicitado.",
        ),
    ] = 1,
    page_size: Annotated[
        int,
        Query(
            ge=1,
            le=100,
            description="Registros por página.",
        ),
    ] = 25,
) -> PaginatedResponses:
    source = get_source_config(source_key)

    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"La fuente '{source_key}' no existe.",
        )

    total = count_responses(connection, source)
    offset = (page - 1) * page_size

    records = list_responses(
        connection,
        source,
        limit=page_size,
        offset=offset,
    )

    return PaginatedResponses(
        data=[
            ResponseSummary.model_validate(record)
            for record in records
        ],
        meta=PaginationMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=ceil(total / page_size) if total else 0,
        ),
    )