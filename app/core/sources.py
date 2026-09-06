from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class SourceConfig:
    key: str
    table_name: str
    display_name: str
    description: str
    projection: str


SOURCES: dict[str, SourceConfig] = {
    "bm": SourceConfig(
        key="bm",
        table_name="respuestas_bm",
        display_name="Banca Móvil",
        description="Respuestas de encuestas correspondientes a Banca Móvil.",
        projection="""
            CAST("Id" AS BIGINT) AS id,
            ? AS fuente,
            "CANAL" AS canal,
            "PERIODO" AS periodo,
            "PER-SEMANA" AS per_semana,
            "FECHA_ENCU" AS fecha_encuesta,
            TRY_CAST("NPS" AS INTEGER) AS nps,
            "ET_NPS" AS categoria_nps,
            "COMENTARIO" AS comentario,
            NULL::VARCHAR AS etiqueta_general,
            "ET_POS" AS etiqueta_positiva,
            "ET_NEG" AS etiqueta_negativa,
            "OPERACION" AS operacion,
            "Created" AS created_at,
            "Modified" AS updated_at
        """,
    ),
    "ia": SourceConfig(
        key="ia",
        table_name="respuestas_ia",
        display_name="Inteligencia Artificial",
        description="Respuestas procesadas por IA para ATM y Agentes BCP.",
        projection="""
            CAST("Id" AS BIGINT) AS id,
            ? AS fuente,
            "SERVICIO" AS canal,
            "PERIODO" AS periodo,
            "PER-SEMANA" AS per_semana,
            "FECHA" AS fecha_encuesta,
            TRY_CAST("NPS" AS INTEGER) AS nps,
            "ET_NPS" AS categoria_nps,
            "COMENTARIO_CLIENTE" AS comentario,
            "ETIQUETA_LIMPIA" AS etiqueta_general,
            NULL::VARCHAR AS etiqueta_positiva,
            NULL::VARCHAR AS etiqueta_negativa,
            "TIPOTRANSACCION" AS operacion,
            "Created" AS created_at,
            "Modified" AS updated_at
        """,
    ),
    "qr": SourceConfig(
        key="qr",
        table_name="respuestas_qr",
        display_name="QR",
        description="Respuestas de experiencia correspondientes al canal QR.",
        projection="""
            CAST("Id" AS BIGINT) AS id,
            ? AS fuente,
            "CANAL" AS canal,
            "PERIODO" AS periodo,
            "PER-SEMANA" AS per_semana,
            "FECHA_ENCU" AS fecha_encuesta,
            TRY_CAST("NPS" AS INTEGER) AS nps,
            "ET_NPS" AS categoria_nps,
            "COM_OTRO" AS comentario,
            NULL::VARCHAR AS etiqueta_general,
            "ET_POS" AS etiqueta_positiva,
            "ET_NEG" AS etiqueta_negativa,
            NULL::VARCHAR AS operacion,
            "Created" AS created_at,
            "Modified" AS updated_at
        """,
    ),
    "tp": SourceConfig(
        key="tp",
        table_name="respuestas_tp",
        display_name="Tarjeta Prepago",
        description="Respuestas correspondientes a Tarjeta Prepago.",
        projection="""
            CAST("Id" AS BIGINT) AS id,
            ? AS fuente,
            "CANAL" AS canal,
            "PERIODO" AS periodo,
            "PER-SEMANA" AS per_semana,
            "FECHA_ENCU" AS fecha_encuesta,
            TRY_CAST("NPS" AS INTEGER) AS nps,
            "ET_NPS" AS categoria_nps,
            "COMENTARIO" AS comentario,
            NULL::VARCHAR AS etiqueta_general,
            "ET_POS" AS etiqueta_positiva,
            "ET_NEG" AS etiqueta_negativa,
            "OPERACION" AS operacion,
            "Created" AS created_at,
            "Modified" AS updated_at
        """,
    ),
}


def get_source_config(source_key: str) -> SourceConfig | None:
    return SOURCES.get(source_key.strip().lower())