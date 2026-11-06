"""Property test de la transformación del Conector_OpenAlex_API (spec
fuente-openalex-api, tarea 3.2).

Property 1 del design.md — "Fuente fija y conformidad del contrato":

    Para todo ``work`` transformado por el conector, ``source == "OpenAlex"``
    (nunca otra fuente) y el registro cumple el contrato V1 (todos los
    obligatorios presentes, o bien ``inclusion_status == "PENDIENTE_REVISIÓN"``).

    **Validates: Requirements 3.1, 3.2**

Enfoque (Testing Strategy del design): la transformación se prueba con ``work``s
SINTÉTICOS marcados como ``DEMO_DATA`` (datos de prueba, NO reales; nunca se
presentan como resultados reales de SAO). Se generan con hypothesis variando la
presencia/ausencia de ``title``, ``authorships``, ``publication_year``, ``doi``,
``abstract_inverted_index`` y demás campos del esquema nativo de ``works`` de
OpenAlex, incluidos años dentro y fuera del Período_Inclusión 2020–2030 y valores
de año no interpretables.

Para cada ``work`` se invoca ``work_to_record(work)`` y se verifica:

  1. ``record.source == "OpenAlex"`` (fuente fija; nunca otra fuente — Req 3.1,
     3.2).
  2. O bien TODOS los campos obligatorios del Article Data Contract V1 están
     presentes, O BIEN ``record.inclusion_status == "PENDIENTE_REVISIÓN"``
     (conformidad del contrato V1).

Obligatorios del contrato V1 (``ArticleRecord``):
``article_id``, ``title``, ``authors``, ``publication_year``, ``source``,
``extraction_date``, ``processing_status``, ``is_duplicate``,
``inclusion_status``.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Permite importar el conector desde bibliometrics/ (mismo patrón que los demás
# tests de este paquete, p. ej. test_openalex_api_pagination.py).
_REPO_ROOT = Path(__file__).resolve().parents[2]
_BIBLIO = _REPO_ROOT / "bibliometrics"
if str(_BIBLIO) not in sys.path:
    sys.path.insert(0, str(_BIBLIO))

from typing import Any  # noqa: E402

from hypothesis import given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

from ingestion.openalex_api_client import (  # noqa: E402
    OPENALEX_SOURCE,
    work_to_record,
)

# Campos obligatorios del Article Data Contract V1 (ArticleRecord). Si alguno
# falta (None o vacío), el registro debe quedar en PENDIENTE_REVISIÓN.
_MANDATORY_FIELDS = (
    "article_id",
    "title",
    "authors",
    "publication_year",
    "source",
    "extraction_date",
    "processing_status",
    "is_duplicate",
    "inclusion_status",
)


def _is_present(value: Any) -> bool:
    """Un campo obligatorio está 'presente' si no es ``None`` ni cadena vacía.

    ``is_duplicate`` es booleano (``False`` es un valor presente válido), por eso
    solo ``None`` y las cadenas en blanco cuentan como ausentes.
    """
    if value is None:
        return False
    if isinstance(value, str) and value.strip() == "":
        return False
    return True


# --- Generadores de ``work``s sintéticos (DEMO_DATA) -------------------------

# Términos opcionales (pueden estar ausentes para ejercer la no-invención).
_maybe_text = st.one_of(st.none(), st.text(max_size=40))


@st.composite
def _authorships(draw: st.DrawFn) -> Any:
    """Genera ``authorships`` variados: ausente, lista vacía, o con autores.

    Imita el esquema nativo de OpenAlex:
    ``authorships[*].author.display_name``. A veces introduce entradas
    malformadas (sin ``author`` o con nombre vacío) para ejercer la robustez.
    """
    kind = draw(st.integers(min_value=0, max_value=2))
    if kind == 0:
        return draw(st.none())  # ausente → authors None → obligatorio faltante
    if kind == 1:
        return []  # lista vacía → sin autores utilizables
    n = draw(st.integers(min_value=1, max_value=3))
    authorships = []
    for _ in range(n):
        name = draw(st.one_of(st.none(), st.text(max_size=20)))
        if draw(st.booleans()):
            authorships.append({"author": {"display_name": name}})
        else:
            # Entrada malformada: sin clave ``author`` utilizable.
            authorships.append({"raw_author_name": name})
    return authorships


@st.composite
def _publication_year(draw: st.DrawFn) -> Any:
    """Año variado: ausente, dentro de rango, fuera de rango, o no interpretable."""
    kind = draw(st.integers(min_value=0, max_value=4))
    if kind == 0:
        return draw(st.none())  # ausente → obligatorio faltante
    if kind == 1:
        return draw(st.integers(min_value=2020, max_value=2030))  # dentro
    if kind == 2:
        return draw(st.integers(min_value=1900, max_value=2019))  # fuera (antes)
    if kind == 3:
        return draw(st.integers(min_value=2031, max_value=2100))  # fuera (después)
    return draw(st.text(max_size=10))  # texto → posiblemente no interpretable


@st.composite
def _inverted_index(draw: st.DrawFn) -> Any:
    """``abstract_inverted_index`` variado: ausente, vacío, o bien formado."""
    kind = draw(st.integers(min_value=0, max_value=2))
    if kind == 0:
        return draw(st.none())
    if kind == 1:
        return {}
    words = draw(st.lists(st.text(min_size=1, max_size=8), min_size=1, max_size=5))
    index: dict[str, list[int]] = {}
    pos = 0
    for word in words:
        occurrences = draw(st.integers(min_value=1, max_value=2))
        index[word] = [pos + i for i in range(occurrences)]
        pos += occurrences
    return index


@st.composite
def _synthetic_work(draw: st.DrawFn) -> dict:
    """Construye un ``work`` sintético (DEMO_DATA) variando campos del esquema.

    Cada clave se incluye u omite al azar para ejercer la presencia/ausencia de
    ``title``, ``authorships``, ``publication_year``, ``doi``,
    ``abstract_inverted_index``, ``id``, etc. Nunca representa datos reales.
    """
    work: dict[str, Any] = {}

    # title / display_name (obligatorio -> title). Pueden faltar ambos.
    if draw(st.booleans()):
        work["title"] = draw(st.one_of(st.none(), st.text(max_size=40)))
    if draw(st.booleans()):
        work["display_name"] = draw(st.one_of(st.none(), st.text(max_size=40)))

    # authorships (obligatorio -> authors).
    if draw(st.booleans()):
        work["authorships"] = draw(_authorships())

    # publication_year (obligatorio).
    if draw(st.booleans()):
        work["publication_year"] = draw(_publication_year())

    # doi (opcional) — con o sin prefijo URL.
    if draw(st.booleans()):
        work["doi"] = draw(
            st.one_of(
                st.none(),
                st.just("https://doi.org/10.1234/demo"),
                st.text(max_size=20),
            )
        )

    # id de OpenAlex (procedencia opcional).
    if draw(st.booleans()):
        work["id"] = draw(
            st.one_of(st.none(), st.just("https://openalex.org/W123DEMO"))
        )

    # abstract_inverted_index (opcional).
    if draw(st.booleans()):
        work["abstract_inverted_index"] = draw(_inverted_index())

    # Campos opcionales adicionales del esquema nativo.
    if draw(st.booleans()):
        work["language"] = draw(_maybe_text)
    if draw(st.booleans()):
        work["primary_location"] = {
            "landing_page_url": draw(_maybe_text),
            "source": {
                "display_name": draw(_maybe_text),
                "host_organization_name": draw(_maybe_text),
            },
        }
    if draw(st.booleans()):
        work["biblio"] = {
            "volume": draw(_maybe_text),
            "issue": draw(_maybe_text),
            "first_page": draw(_maybe_text),
            "last_page": draw(_maybe_text),
        }

    return work


# Feature: fuente-openalex-api, Property 1: Fuente fija y conformidad del contrato
@settings(max_examples=200)
@given(work=_synthetic_work())
def test_fuente_fija_y_conformidad_del_contrato(work: dict) -> None:
    """``source`` siempre "OpenAlex" y el registro cumple el contrato V1.

    Validates: Requirements 3.1, 3.2
    """
    record = work_to_record(work)

    # (1) Fuente fija: SIEMPRE "OpenAlex", nunca otra fuente (Req 3.1, 3.2).
    assert record.source == OPENALEX_SOURCE == "OpenAlex", (
        f"source debe ser 'OpenAlex'; fue {record.source!r}"
    )

    # (2) Conformidad del contrato V1: o bien todos los obligatorios están
    # presentes, o bien el registro queda en PENDIENTE_REVISIÓN.
    all_mandatory_present = all(
        _is_present(getattr(record, field)) for field in _MANDATORY_FIELDS
    )
    assert all_mandatory_present or record.inclusion_status == "PENDIENTE_REVISIÓN", (
        "Si falta algún obligatorio del contrato V1, inclusion_status debe ser "
        f"'PENDIENTE_REVISIÓN'; obligatorios_presentes={all_mandatory_present}, "
        f"inclusion_status={record.inclusion_status!r}"
    )
