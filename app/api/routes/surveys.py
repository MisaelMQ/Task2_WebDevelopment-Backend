from datetime import date
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

from app.core.nps import NpsCategory
from app.db.application import get_application_database
from app.api.dependencies.auth import get_current_user, require_admin
from app.repositories.channels_repository import (
    get_channel_by_id,
)
from app.repositories.surveys_repository import (
    count_surveys,
    create_survey,
    delete_survey,
    get_survey_by_id,
    list_surveys,
    update_survey,
)
from app.schemas.survey import (
    PaginatedSurveys,
    SurveyCreate,
    SurveyPaginationMeta,
    SurveyRead,
    SurveyStatus,
    SurveyUpdate,
)

router = APIRouter(
    prefix="/encuestas",
    tags=["Encuestas"],
)

ApplicationDatabase = Annotated[
    DuckDBPyConnection,
    Depends(get_application_database),
]

@router.get(
    "",
    response_model=PaginatedSurveys,
    summary="Listar encuestas",
    dependencies=[Depends(get_current_user)]
)
def get_surveys(
    connection: ApplicationDatabase,
    page: Annotated[
        int,
        Query(ge=1),
    ] = 1,
    page_size: Annotated[
        int,
        Query(ge=1, le=100),
    ] = 10,
    canal_id: Annotated[
        int | None,
        Query(gt=0),
    ] = None,
    categoria_nps: Annotated[
        NpsCategory | None,
        Query(),
    ] = None,
    estado: Annotated[
        SurveyStatus | None,
        Query(),
    ] = None,
    fecha_desde: Annotated[
        date | None,
        Query(),
    ] = None,
    fecha_hasta: Annotated[
        date | None,
        Query(),
    ] = None,
    buscar: Annotated[
        str | None,
        Query(min_length=2, max_length=100),
    ] = None,
) -> PaginatedSurveys:
    if (
        fecha_desde is not None
        and fecha_hasta is not None
        and fecha_desde > fecha_hasta
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "fecha_desde no puede ser posterior "
                "a fecha_hasta."
            ),
        )

    total = count_surveys(
        connection,
        canal_id=canal_id,
        categoria_nps=categoria_nps,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        buscar=buscar,
    )

    records = list_surveys(
        connection,
        limit=page_size,
        offset=(page - 1) * page_size,
        canal_id=canal_id,
        categoria_nps=categoria_nps,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        buscar=buscar,
    )

    return PaginatedSurveys(
        data=[
            SurveyRead.model_validate(record)
            for record in records
        ],
        meta=SurveyPaginationMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=ceil(total / page_size)
            if total
            else 0,
        ),
    )

@router.get(
    "/{survey_id}",
    response_model=SurveyRead,
    summary="Obtener una encuesta",
    dependencies=[Depends(get_current_user)]
)
def get_survey(
    survey_id: Annotated[
        int,
        Path(gt=0),
    ],
    connection: ApplicationDatabase,
) -> SurveyRead:
    record = get_survey_by_id(
        connection,
        survey_id,
    )

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe la encuesta {survey_id}.",
        )

    return SurveyRead.model_validate(record)

@router.post(
    "",
    response_model=SurveyRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una encuesta",
    dependencies=[Depends(require_admin)],
)
def post_survey(
    survey: SurveyCreate,
    connection: ApplicationDatabase,
) -> SurveyRead:
    channel = get_channel_by_id(
        connection,
        survey.canal_id,
    )

    if channel is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"No existe el canal "
                f"{survey.canal_id}."
            ),
        )

    created_survey = create_survey(
        connection,
        survey,
    )

    return SurveyRead.model_validate(
        created_survey
    )

@router.put(
    "/{survey_id}",
    response_model=SurveyRead,
    summary="Actualizar completamente una encuesta",
    dependencies=[Depends(require_admin)]
)
def put_survey(
    survey_id: Annotated[
        int,
        Path(gt=0),
    ],
    survey: SurveyUpdate,
    connection: ApplicationDatabase,
) -> SurveyRead:
    current_survey = get_survey_by_id(
        connection,
        survey_id,
    )

    if current_survey is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe la encuesta {survey_id}.",
        )

    channel = get_channel_by_id(
        connection,
        survey.canal_id,
    )

    if channel is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"No existe el canal "
                f"{survey.canal_id}."
            ),
        )

    updated_survey = update_survey(
        connection,
        survey_id,
        survey,
    )

    return SurveyRead.model_validate(
        updated_survey
    )

@router.delete(
    "/{survey_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Eliminar una encuesta",
    dependencies=[Depends(require_admin)]
)
def remove_survey(
    survey_id: Annotated[
        int,
        Path(gt=0),
    ],
    connection: ApplicationDatabase,
) -> Response:
    deleted = delete_survey(
        connection,
        survey_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe la encuesta {survey_id}.",
        )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )