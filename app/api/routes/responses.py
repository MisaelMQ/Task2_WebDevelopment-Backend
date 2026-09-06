from math import ceil
from typing import Annotated

from duckdb import DuckDBPyConnection
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    Query,
    status,
)

from app.core.sources import get_source_config
from app.db.connection import get_database
from app.repositories.responses_repository import (
    ResponseFilters,
    count_responses,
    get_response_by_id,
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
            description="Cantidad de registros por página.",
        ),
    ] = 25,
    periodo: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=20,
            description="Periodo, por ejemplo Ago.26.",
        ),
    ] = None,
    categoria_nps: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=30,
            description="Promotor, Pasivo o Detractor.",
        ),
    ] = None,
    canal: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=100,
            description="Canal o servicio de la respuesta.",
        ),
    ] = None,
    nps: Annotated[
        int | None,
        Query(
            ge=0,
            le=10,
            description="Puntuación NPS entre 0 y 10.",
        ),
    ] = None,
    buscar: Annotated[
        str | None,
        Query(
            min_length=2,
            max_length=100,
            description="Texto contenido en el comentario.",
        ),
    ] = None,
) -> PaginatedResponses:
    source = get_source_config(source_key)

    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"La fuente '{source_key}' no existe.",
        )

    filters = ResponseFilters(
        periodo=periodo,
        categoria_nps=categoria_nps,
        canal=canal,
        nps=nps,
        buscar=buscar,
    )

    total = count_responses(
        connection,
        source,
        filters=filters,
    )

    offset = (page - 1) * page_size

    records = list_responses(
        connection,
        source,
        limit=page_size,
        offset=offset,
        filters=filters,
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


@router.get(
    "/{source_key}/{record_id}",
    response_model=ResponseSummary,
    summary="Obtener una respuesta por su identificador",
)
def get_response(
    source_key: str,
    record_id: Annotated[
        int,
        Path(
            gt=0,
            description="Identificador del registro en su fuente.",
        ),
    ],
    connection: DatabaseDependency,
) -> ResponseSummary:
    source = get_source_config(source_key)

    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"La fuente '{source_key}' no existe.",
        )

    record = get_response_by_id(
        connection,
        source,
        record_id=record_id,
    )

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"No existe el registro {record_id} "
                f"en la fuente '{source.key}'."
            ),
        )

    return ResponseSummary.model_validate(record)