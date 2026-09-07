from math import ceil
from typing import Annotated

from duckdb import DuckDBPyConnection
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    Query,
    Response,
    status,
)

from app.db.application import get_application_database
from app.api.dependencies.auth import get_current_user, require_admin
from app.repositories.channels_repository import (
    count_channels,
    create_channel,
    delete_channel as delete_channel_record,
    get_channel_by_code,
    get_channel_by_id,
    list_channels,
    update_channel,
)
from app.schemas.channel import (
    ChannelCreate,
    ChannelPaginationMeta,
    ChannelRead,
    ChannelSource,
    ChannelUpdate,
    PaginatedChannels,
)

from app.repositories.surveys_repository import (
    count_surveys_by_channel,
)

router = APIRouter(
    prefix="/canales",
    tags=["Canales"],
)

ApplicationDatabase = Annotated[
    DuckDBPyConnection,
    Depends(get_application_database),
]


@router.get(
    "",
    response_model=PaginatedChannels,
    summary="Listar canales",
    dependencies=[Depends(get_current_user)]
)
def get_channels(
    connection: ApplicationDatabase,
    page: Annotated[
        int,
        Query(ge=1),
    ] = 1,
    page_size: Annotated[
        int,
        Query(ge=1, le=100),
    ] = 10,
    buscar: Annotated[
        str | None,
        Query(min_length=1, max_length=100),
    ] = None,
    fuente: Annotated[
        ChannelSource | None,
        Query(),
    ] = None,
) -> PaginatedChannels:
    total = count_channels(
        connection,
        buscar=buscar,
        fuente=fuente,
    )

    records = list_channels(
        connection,
        limit=page_size,
        offset=(page - 1) * page_size,
        buscar=buscar,
        fuente=fuente,
    )

    return PaginatedChannels(
        data=[
            ChannelRead.model_validate(record)
            for record in records
        ],
        meta=ChannelPaginationMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=ceil(total / page_size)
            if total
            else 0,
        ),
    )

@router.get(
    "/{channel_id}",
    response_model=ChannelRead,
    summary="Obtener un canal",
    dependencies=[Depends(get_current_user)]
)
def get_channel(
    channel_id: Annotated[
        int,
        Path(gt=0),
    ],
    connection: ApplicationDatabase,
) -> ChannelRead:
    record = get_channel_by_id(
        connection,
        channel_id,
    )

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe el canal {channel_id}.",
        )

    return ChannelRead.model_validate(record)

@router.post(
    "",
    response_model=ChannelRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un canal",
    dependencies=[Depends(require_admin)],
)
def post_channel(
    channel: ChannelCreate,
    connection: ApplicationDatabase,
) -> ChannelRead:
    duplicated_channel = get_channel_by_code(
        connection,
        channel.codigo,
    )

    if duplicated_channel is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Ya existe un canal con el código "
                f"'{channel.codigo}'."
            ),
        )

    created_channel = create_channel(
        connection,
        channel,
    )

    return ChannelRead.model_validate(
        created_channel
    )

@router.put(
    "/{channel_id}",
    response_model=ChannelRead,
    summary="Actualizar completamente un canal",
    dependencies=[Depends(require_admin)],
)
def put_channel(
    channel_id: Annotated[
        int,
        Path(gt=0),
    ],
    channel: ChannelUpdate,
    connection: ApplicationDatabase,
) -> ChannelRead:
    current_channel = get_channel_by_id(
        connection,
        channel_id,
    )

    if current_channel is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe el canal {channel_id}.",
        )

    duplicated_channel = get_channel_by_code(
        connection,
        channel.codigo,
    )

    if (
        duplicated_channel is not None
        and duplicated_channel["id"] != channel_id
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Ya existe otro canal con el código "
                f"'{channel.codigo}'."
            ),
        )

    updated_channel = update_channel(
        connection,
        channel_id,
        channel,
    )

    return ChannelRead.model_validate(
        updated_channel
    )

@router.delete(
    "/{channel_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Eliminar un canal",
    dependencies=[Depends(require_admin)],
)
def remove_channel(
    channel_id: Annotated[
        int,
        Path(gt=0),
    ],
    connection: ApplicationDatabase,
) -> Response:
    associated_surveys = count_surveys_by_channel(
        connection,
        channel_id,
    )

    if associated_surveys > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"No se puede eliminar el canal "
                f"{channel_id} porque tiene "
                f"{associated_surveys} encuesta(s) "
                f"asociada(s)."
            ),
        )

    deleted = delete_channel_record(
        connection,
        channel_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe el canal {channel_id}.",
        )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )