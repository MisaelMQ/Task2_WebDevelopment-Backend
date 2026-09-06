from typing import Literal

NpsCategory = Literal[
    "Detractor",
    "Pasivo",
    "Promotor",
]

def calculate_nps_category(
    score: int,
) -> NpsCategory:
    if 0 <= score <= 6:
        return "Detractor"

    if 7 <= score <= 8:
        return "Pasivo"

    if 9 <= score <= 10:
        return "Promotor"

    raise ValueError(
        "La puntuación NPS debe estar entre 0 y 10."
    )