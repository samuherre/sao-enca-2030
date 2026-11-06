"""Property test de la transformación del Conector_OpenAlex_API (spec
fuente-openalex-api, tarea 3.5).

Property 4 del design.md — "Año fuera de período marca revisión sin descartar":

    Para todo ``work`` con ``publication_year`` fuera de 2020–2030, el conector
    conserva el registro con ese año y fija
    ``inclusion_status = "PENDIENTE_REVISIÓN"`` con una nota; para años dentro
    del rango no fuerza ese estado POR MOTIVO DE PERÍODO.

    **Validates: Requirements 4.2**

Enfoque (Testing Strategy del design): se generan ``work``s nativos de OpenAlex
SINTÉTICOS (``DEMO_DATA``, datos de prueba, NUNCA reales) con los campos
obligatorios del contrato V1 SIEMPRE completos (``title`` + ``authorships`` con
``author.display_name`` + ``publication_year``) y un año generado por hypothesis
tanto DENTRO (2020–2030) como FUERA del rango. Cada ``work`` se transforma con
``work_to_record`` y se comprueba la propiedad sobre el ``ArticleRecord``.

Precisión importante sobre la cláusula "dentro del rango" (confirmada leyendo
``work_to_record``): en V1 el conector marca TODO registro como
``PENDIENTE_REVISIÓN`` (porque la relevancia temática y la clasificación OFC
permanecen ``PENDING_VALIDATION``), de modo que el ``inclusion_status`` por sí
solo NO distingue el motivo de período. Por eso la propiedad para años dentro
del rango se verifica como: la nota NO contiene el mensaje de fuera de período.
Para años fuera del rango se verifica lo contrario: la nota SÍ contiene ese
mensaje y el ``publication_year`` conserva EXACTAMENTE el año de entrada (no se
descarta ni se anula el registro).

El texto exacto de la nota de fuera de período y el rango se toman directamente
del módulo del conector (``PERIODO_MIN``/``PERIODO_MAX`` y la f-string de la
nota verificada en ``work_to_record``), para no duplicar literales frágiles.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Permite importar el conector desde bibliometrics/ (mismo patrón que los demás
# tests de este paquete).
_REPO_ROOT = Path(__file__).resolve().parents[2]
_BIBLIO = _REPO_ROOT / "bibliometrics"
if str(_BIBLIO) not in sys.path:
    sys.path.insert(0, str(_BIBLIO))

from hypothesis import given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

from ingestion.openalex_api_client import (  # noqa: E402
    PERIODO_MAX,
    PERIODO_MIN,
    work_to_record,
)

# Texto EXACTO de la nota de fuera de período, derivado de la lógica verificada
# en ``work_to_record``:
#   f"Año {year} fuera del periodo {PERIODO_MIN}-{PERIODO_MAX}."
# Se construye con la misma plantilla para no acoplar a un literal frágil.
def _out_of_period_note(year: int) -> str:
    return f"Año {year} fuera del periodo {PERIODO_MIN}-{PERIODO_MAX}."


# Fragmento estable del mensaje (independiente del año) para comprobar que la
# nota de un registro DENTRO del rango NO lo contiene.
_OUT_OF_PERIOD_FRAGMENT = f"fuera del periodo {PERIODO_MIN}-{PERIODO_MAX}."


# Texto no vacío plausible, sin bordes que ``_clean_str`` recorte a vacío.
_non_empty_text = st.text(
    alphabet=st.characters(blacklist_categories=("Cs", "Cc"), min_codepoint=33),
    min_size=1,
    max_size=30,
)

# Año DENTRO del Período_Inclusión 2020–2030.
_year_in_range = st.integers(min_value=PERIODO_MIN, max_value=PERIODO_MAX)

# Año FUERA del Período_Inclusión: por debajo de 2020 o por encima de 2030.
# Se acotan los extremos a un rango plausible de años (evitar valores absurdos
# que no aportan a la propiedad). Son interpretables como año (enteros).
_year_below = st.integers(min_value=1500, max_value=PERIODO_MIN - 1)
_year_above = st.integers(min_value=PERIODO_MAX + 1, max_value=3000)
_year_out_of_range = st.one_of(_year_below, _year_above)


@st.composite
def works_con_obligatorios_completos(draw: st.DrawFn) -> dict:
    """Genera un ``work`` OpenAlex SINTÉTICO (DEMO_DATA) con obligatorios OK.

    Garantiza SIEMPRE presentes los tres obligatorios del contrato V1:
      - ``title`` (texto no vacío),
      - ``authorships`` con al menos un ``author.display_name`` no vacío,
      - ``publication_year`` (entero), dentro O fuera del rango 2020–2030.

    De este modo, la ÚNICA causa posible de la nota de fuera de período es el
    año, aislando la propiedad bajo prueba (ningún obligatorio faltante enturbia
    el resultado). Se añaden algunas claves opcionales de ruido que no deben
    afectar la lógica de período.
    """
    in_range = draw(st.booleans())
    year = draw(_year_in_range if in_range else _year_out_of_range)

    # authorships: 1..3 autores con display_name no vacío.
    n_authors = draw(st.integers(min_value=1, max_value=3))
    authorships = [
        {"author": {"display_name": draw(_non_empty_text)}} for _ in range(n_authors)
    ]

    work: dict = {
        "title": draw(_non_empty_text),
        "authorships": authorships,
        "publication_year": year,
    }

    # Ruido opcional: no debe afectar la clasificación por período.
    if draw(st.booleans()):
        work["id"] = "https://openalex.org/W" + draw(
            st.text(alphabet="0123456789", min_size=1, max_size=10)
        )
    if draw(st.booleans()):
        work["doi"] = "https://doi.org/10.1234/" + draw(
            st.text(
                alphabet=st.characters(
                    blacklist_categories=("Cs", "Cc"), min_codepoint=33
                ),
                min_size=1,
                max_size=12,
            )
        )
    if draw(st.booleans()):
        work["language"] = draw(st.sampled_from(["es", "en", "pt"]))

    return work


# Feature: fuente-openalex-api, Property 4: Año fuera de período marca revisión sin descartar
@settings(max_examples=200)
@given(work=works_con_obligatorios_completos())
def test_ano_fuera_de_periodo_marca_revision_sin_descartar(work: dict) -> None:
    """Año fuera de 2020–2030 → PENDIENTE_REVISIÓN con nota, sin descartar.

    - FUERA del rango: ``publication_year`` conserva EXACTAMENTE el año de
      entrada (no se descarta ni se anula), ``inclusion_status`` es
      ``PENDIENTE_REVISIÓN`` y la ``notes`` contiene el mensaje de fuera de
      período con ese año.
    - DENTRO del rango (con obligatorios completos): la ``notes`` NO contiene el
      mensaje de fuera de período; es decir, el estado no se marca POR MOTIVO DE
      PERÍODO (en V1 todo registro entra como PENDIENTE_REVISIÓN por relevancia /
      OFC, lo cual es independiente de esta propiedad).

    **Validates: Requirements 4.2**
    """
    year = work["publication_year"]
    record = work_to_record(work)
    notes = record.notes or ""

    in_range = PERIODO_MIN <= year <= PERIODO_MAX

    if not in_range:
        # Conserva el registro con ESE año exacto (no descarta ni anula).
        assert record.publication_year == year, (
            "Un año fuera de período debe CONSERVARSE tal cual en el registro "
            f"(no descartar/anular); entrada year={year!r}, "
            f"publication_year={record.publication_year!r}"
        )
        # Marcado para revisión.
        assert record.inclusion_status == "PENDIENTE_REVISIÓN", (
            "Año fuera de período debe fijar inclusion_status="
            f"'PENDIENTE_REVISIÓN'; year={year!r}, "
            f"inclusion_status={record.inclusion_status!r}"
        )
        # Nota explícita con el mensaje de fuera de período para ese año.
        expected_note = _out_of_period_note(year)
        assert expected_note in notes, (
            "Se esperaba la nota de fuera de período para el año; "
            f"year={year!r}, esperado={expected_note!r}, notes={notes!r}"
        )
    else:
        # Dentro del rango: el estado NO se marca por motivo de período. La nota
        # NO debe contener el mensaje de fuera de período.
        assert _OUT_OF_PERIOD_FRAGMENT not in notes, (
            "Un año dentro del período 2020–2030 NO debe generar la nota de "
            f"fuera de período; year={year!r}, notes={notes!r}"
        )
        # El año válido se conserva igualmente (no se altera).
        assert record.publication_year == year, (
            "Un año dentro de rango debe conservarse tal cual; "
            f"year={year!r}, publication_year={record.publication_year!r}"
        )
