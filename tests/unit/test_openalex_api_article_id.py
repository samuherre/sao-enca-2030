"""Property test del Conector_OpenAlex_API (spec fuente-openalex-api, tarea 3.6).

Property 5 del design.md — "``article_id`` determinista, reproducible y con
esquema compartido":

    Para todo ``work``, transformarlo dos veces produce el mismo ``article_id``,
    el id empieza por ``oa-``, y para un ``work`` con el mismo DOI (o mismo
    título+año) el id coincide con el que produciría la vía PoP para esos mismos
    datos.

    **Validates: Requirements 3.6**

Enfoque (Testing Strategy del design): se generan ``work``s sintéticos
(``DEMO_DATA``) nativos de la API_OpenAlex con presencia variable de campos (con
y SIN ``doi``, títulos variados y repetidos, años dentro/fuera de rango o
ausentes). Para cada ``work`` se verifica:

  1. Determinismo: ``work_to_record(work).article_id`` es igual en dos llamadas.
  2. Esquema compartido: el id empieza por el prefijo propio ``"oa-"``.
  3. Igualdad entre vías (cross-path): el id de la vía API coincide con el que
     produce el id-maker de la vía PoP (``extract_openalex._make_article_id``)
     alimentado con los MISMOS datos.
       - Con DOI: la vía API pela el prefijo ``https://doi.org/`` (ver
         ``openalex_api_client._strip_doi_prefix``); por eso la comparación
         alimenta a la vía PoP con el DOI YA PELADO, que es la forma en que el
         export de PoP entrega el DOI. Así el MISMO work produce el MISMO id por
         ambas vías y ambas cuentan como la fuente "OpenAlex".
       - Sin DOI: ambas vías usan ``norm_title(title) + "|" + año``.

Los datos generados por hypothesis son SINTÉTICOS (``DEMO_DATA``, no reales).
"""

from __future__ import annotations

import sys
from pathlib import Path

# Permite importar los conectores desde bibliometrics/ (mismo patrón que los
# demás tests de este paquete, p. ej. test_openalex_fuente_contrato.py).
_REPO_ROOT = Path(__file__).resolve().parents[2]
_BIBLIO = _REPO_ROOT / "bibliometrics"
if str(_BIBLIO) not in sys.path:
    sys.path.insert(0, str(_BIBLIO))

from hypothesis import HealthCheck, given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

# Vía API (bajo prueba): transformación work -> ArticleRecord y el id-maker.
from ingestion.openalex_api_client import (  # noqa: E402
    _api_make_article_id,
    _strip_doi_prefix,
    work_to_record,
)

# Vía PoP (referencia cruzada): el id-maker del export manual con Publish or
# Perish. El MISMO esquema debe producir el MISMO id para los mismos datos.
from ingestion.extract_openalex import _make_article_id as _pop_make_article_id  # noqa: E402

OPENALEX_PREFIX = "oa-"

# Títulos reutilizados para provocar repeticiones (mismo título+año → mismo id).
_TITLES = [
    "Conservación de aves en los Andes",
    "Bird conservation in Antioquia",
    "Aves de humedales interiores",
    "A STUDY OF URBAN BIRDS",
]

# Fragmentos de DOI (sin prefijo) para construir el ``doi`` nativo de la API.
_DOI_SUFFIXES = [
    "10.1234/abc.2021",
    "10.5555/XYZ-987",
    "10.1000/Bird.Cons",
    "10.9999/aves-antioquia",
]


@st.composite
def openalex_work(draw: st.DrawFn) -> dict:
    """Genera un ``work`` sintético (DEMO_DATA) nativo de la API_OpenAlex.

    - ``title`` puede venir en ``title`` o en ``display_name`` (o ausente), con
      un conjunto pequeño de títulos para provocar repeticiones.
    - ``publication_year`` puede ser válido, fuera de rango o ausente.
    - ``doi`` puede estar presente como URL completa
      (``https://doi.org/<suffix>``), como DOI pelado, o ausente, para ejercer
      ambas ramas del id (con DOI vs. título+año) y el pelado del prefijo.
    """
    work: dict = {}

    if draw(st.booleans()):
        title = draw(st.sampled_from(_TITLES))
        # El título puede venir en "title" o en "display_name" (respaldo).
        if draw(st.booleans()):
            work["title"] = title
        else:
            work["display_name"] = title

    if draw(st.booleans()):
        work["publication_year"] = draw(
            st.one_of(
                st.integers(min_value=2020, max_value=2030),  # en rango
                st.integers(min_value=1900, max_value=2019),  # fuera (bajo)
                st.integers(min_value=2031, max_value=2100),  # fuera (alto)
            )
        )

    if draw(st.booleans()):
        suffix = draw(st.sampled_from(_DOI_SUFFIXES))
        prefix = draw(
            st.sampled_from(
                ["https://doi.org/", "http://doi.org/", "doi.org/", ""]
            )
        )
        work["doi"] = prefix + suffix

    return work


# Feature: fuente-openalex-api, Property 5: article_id determinista, reproducible y con esquema compartido
@settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
@given(work=openalex_work())
def test_api_article_id_determinista_reproducible_y_esquema_compartido(
    work: dict,
) -> None:
    """El article_id de la vía API es determinista, empieza por 'oa-' y coincide
    con el de la vía PoP para los mismos datos.

    Validates: Requirements 3.6
    """
    # (1) Determinismo / reproducibilidad: dos transformaciones del MISMO work
    # producen idéntico article_id.
    id_1 = work_to_record(work).article_id
    id_2 = work_to_record(work).article_id
    assert id_1 == id_2, (
        "article_id no es reproducible entre corridas para el mismo work: "
        f"{id_1!r} != {id_2!r}"
    )

    # (2) Esquema compartido: prefijo propio 'oa-'.
    assert id_1.startswith(OPENALEX_PREFIX), (
        f"article_id debe empezar por {OPENALEX_PREFIX!r}, fue {id_1!r}"
    )

    # (3) Igualdad entre vías (cross-path). Reproducimos los MISMOS datos que la
    # transformación de la vía API deriva del work:
    #   - title: "title" con respaldo en "display_name" (igual que work_to_record).
    #   - year: publication_year (int) o None.
    #   - doi: pelado del prefijo https://doi.org/ (como lo hace la vía API).
    title = work.get("title") or work.get("display_name")
    year = work.get("publication_year")
    if not isinstance(year, int):
        year = None
    stripped_doi = _strip_doi_prefix(work.get("doi"))

    # El id-maker de la vía API debe coincidir exactamente con el de la vía PoP
    # alimentado con el DOI YA PELADO (que es como PoP entrega el DOI) o, sin
    # DOI, con el mismo título+año.
    api_id = _api_make_article_id(stripped_doi, title, year)
    pop_id = _pop_make_article_id(stripped_doi, title, year)
    assert api_id == pop_id, (
        "El article_id de la vía API no coincide con el de la vía PoP para los "
        f"mismos datos (doi={stripped_doi!r}, title={title!r}, year={year!r}): "
        f"API={api_id!r} != PoP={pop_id!r}"
    )

    # Y ese id compartido es exactamente el que produce la transformación real.
    assert api_id == id_1, (
        "El article_id producido por work_to_record no coincide con el esquema "
        f"compartido esperado: {id_1!r} != {api_id!r}"
    )
