"""Property test de la transformación del Conector_OpenAlex_API (spec
fuente-openalex-api, tarea 3.8).

Property 10 del design.md — "Procedencia preservada sin invención":

    Para todo ``work`` que trae su propio ``id`` de OpenAlex, ese valor se
    preserva en ``source_url``; para todo ``work`` que NO lo trae, ``source_url``
    es ``None`` (no se inventa).

    **Validates: Requirements 8.2**

Enfoque (Testing Strategy del design): se generan ``work``s sintéticos nativos
de la API_OpenAlex (``DEMO_DATA``, datos de prueba, NUNCA presentados como
resultados reales) INCLUYENDO u OMITIENDO aleatoriamente la clave ``id`` (URL del
work, p. ej. ``https://openalex.org/Wxxxx``). Se llama a ``work_to_record(work)``
y se verifica la procedencia (``source_url``).

Comportamiento del conector (verificado en ``openalex_api_client.py``):
``source_url = _clean_str(work.get("id"))``. ``_clean_str`` recorta cadenas y
reduce el vacío a ``None``. Por tanto:

    - ``id`` presente con un valor de texto utilizable → ``source_url`` = ese
      valor (recortado); se PRESERVA, no se inventa ni se altera su contenido.
    - ``id`` ausente, ``None``, vacío o solo espacios → ``source_url is None``
      (no se inventa una procedencia).
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

from typing import Any  # noqa: E402

from hypothesis import given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

from ingestion.openalex_api_client import work_to_record  # noqa: E402

# ---------------------------------------------------------------------------
# Generadores (DEMO_DATA) para el ``id`` de un ``work`` de la API_OpenAlex.
# ---------------------------------------------------------------------------

# Sufijo alfanumérico no vacío para construir una URL de work utilizable, sin
# espacios al borde que _clean_str recortaría (de modo que "presente con valor"
# signifique realmente un valor preservable).
_work_suffix = st.text(
    alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),
        max_codepoint=127,
    ),
    min_size=1,
    max_size=12,
)

# ``id`` con un valor utilizable: URL nativa del work de OpenAlex.
_usable_id = _work_suffix.map(lambda s: "https://openalex.org/W" + s)

# ``id`` presente pero NO utilizable (vacío o solo espacios): _clean_str → None.
_blank_id = st.sampled_from(["", "   ", "\t", "\n", "  \t ", None])


@st.composite
def synthetic_work(draw: st.DrawFn) -> dict[str, Any]:
    """Genera un ``work`` sintético (DEMO_DATA) con la clave ``id`` INCLUIDA o
    OMITIDA de forma aleatoria.

    Tres escenarios equiprobables para ejercer la procedencia:
      - ``id`` ausente por completo (clave no presente).
      - ``id`` presente con un valor de texto utilizable (URL del work).
      - ``id`` presente pero en blanco/``None`` (no utilizable).

    El resto del ``work`` puede traer campos irrelevantes para esta propiedad,
    para no acoplar el test a un ``work`` mínimo.
    """
    work: dict[str, Any] = {}

    # Campos de relleno irrelevantes para la procedencia (presencia variable).
    if draw(st.booleans()):
        work["title"] = draw(st.text(min_size=1, max_size=15))
    if draw(st.booleans()):
        work["publication_year"] = draw(st.integers(min_value=2020, max_value=2030))

    kind = draw(st.sampled_from(["absent", "usable", "blank"]))
    if kind == "usable":
        work["id"] = draw(_usable_id)
    elif kind == "blank":
        work["id"] = draw(_blank_id)
    # kind == "absent": no se agrega la clave ``id``.

    return work


# Feature: fuente-openalex-api, Property 10: Procedencia preservada sin invención
@settings(max_examples=200)
@given(work=synthetic_work())
def test_procedencia_preservada_sin_invencion(work: dict[str, Any]) -> None:
    """``source_url`` preserva el ``id`` del work cuando existe; si no, es None.

    - ``id`` presente con un valor de texto utilizable → ``source_url`` igual a
      ese valor (recortado): la procedencia se PRESERVA sin alterar su contenido.
    - ``id`` ausente o sin valor utilizable (vacío/espacios/``None``) →
      ``source_url is None``: no se inventa una procedencia (Req 8.2).

    **Validates: Requirements 8.2**
    """
    record = work_to_record(work)

    raw_id = work.get("id")
    usable = isinstance(raw_id, str) and raw_id.strip() != ""

    if usable:
        assert record.source_url == raw_id.strip(), (
            "La procedencia debe preservar el id del work (recortado): "
            f"esperado {raw_id.strip()!r}, obtenido {record.source_url!r}. "
            f"work={work!r}"
        )
    else:
        assert record.source_url is None, (
            "Sin un id utilizable en el work, la procedencia no debe inventarse: "
            f"source_url debe ser None, obtenido {record.source_url!r}. "
            f"work={work!r}"
        )
