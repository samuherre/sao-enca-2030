"""Property test del Conector_OpenAlex (spec fuente-openalex, tarea 1.8).

Property 11 del design.md — "Preservación de procedencia sin invención":

    Para todo registro que traiga un identificador o URL propio de OpenAlex, ese
    valor se preserva en ``source_url``; para todo registro que no lo traiga,
    ``source_url`` queda en ``None`` (no se inventa).

    **Validates: Requirements 7.3**

Enfoque (Testing Strategy del design): se generan registros PoP/OpenAlex
sintéticos (datos de prueba, no reales). El conector detecta la procedencia
mediante ``FIELD_CANDIDATES["source_url"] = ("id", "cites_url", "url")``,
buscando case-insensitive y tomando la PRIMERA candidata presente con valor no
vacío (en ese orden). La aserción es doble:

- Cuando al menos una candidata de ``source_url`` está presente con valor no
  vacío, ``record.source_url`` es exactamente el valor preservado de la primera
  candidata no vacía según el orden de ``FIELD_CANDIDATES``.
- Cuando NINGUNA candidata de ``source_url`` está presente (o todas tienen
  valor que el conector considera vacío), ``record.source_url is None``: no se
  inventa procedencia.

La búsqueda del conector es case-insensitive (``_lower_key_map``), por lo que el
generador produce tanto claves en su forma candidata como variantes de casing
para ejercitar esa ruta sin inventar comportamiento.
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

from hypothesis import HealthCheck, given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

from ingestion.extract_openalex import (  # noqa: E402
    FIELD_CANDIDATES,
    _record_from_mapping,
)

# Claves candidatas de source_url, en el ORDEN que el conector prueba
# (la primera no vacía gana). Tomadas directamente del conector para no
# duplicar la fuente de verdad.
SOURCE_URL_CANDIDATES = FIELD_CANDIDATES["source_url"]  # ("id", "cites_url", "url")

# Valores no vacíos plausibles para un identificador/URL de OpenAlex. Se evita
# el espacio en blanco al borde para que "presente" signifique realmente un
# valor que el conector conserva (no uno que _clean_str reduzca a None).
_url_values = st.one_of(
    st.just("https://openalex.org/W1234567890"),
    st.just("https://openalex.org/W999"),
    st.text(
        alphabet=st.characters(blacklist_categories=("Cs", "Cc"), min_codepoint=33),
        min_size=1,
        max_size=30,
    ),
)


def _expected_source_url(raw: dict[str, str]) -> str | None:
    """Replica la regla del conector: primera candidata no vacía (orden, case-insensitive).

    Devuelve el valor preservado esperado para ``source_url`` o ``None`` si
    ninguna candidata está presente con valor no vacío.
    """
    lowered = {
        (k.strip().lower() if isinstance(k, str) else k): v for k, v in raw.items()
    }
    for cand in SOURCE_URL_CANDIDATES:
        if cand in lowered:
            value = lowered[cand]
            if isinstance(value, str) and value.strip():
                return value.strip()
    return None


@st.composite
def pop_openalex_records(draw: st.DrawFn) -> dict[str, str]:
    """Genera un registro PoP/OpenAlex sintético enfocado en la procedencia.

    - Decide qué subconjunto (posiblemente vacío) de las candidatas de
      ``source_url`` incluir, y les asigna valores no vacíos.
    - Varía el casing de la clave para ejercitar la búsqueda case-insensitive.
    - Añade algunas claves de "ruido" no relacionadas con ``source_url`` para que
      el registro se parezca a un export real sin afectar la procedencia.
    """
    present = draw(
        st.lists(
            st.sampled_from(list(SOURCE_URL_CANDIDATES)),
            unique=True,
            min_size=0,
            max_size=len(SOURCE_URL_CANDIDATES),
        )
    )
    record: dict[str, str] = {}
    for cand in present:
        # Variantes de casing para probar la detección case-insensitive.
        key = draw(st.sampled_from([cand, cand.upper(), cand.capitalize()]))
        record[key] = draw(_url_values)

    # Ruido: claves que no son candidatas de source_url (p. ej. título/autores).
    if draw(st.booleans()):
        record["Title"] = draw(st.text(min_size=1, max_size=15))
    if draw(st.booleans()):
        record["Authors"] = draw(st.text(min_size=1, max_size=15))

    return record


# Feature: fuente-openalex, Property 11: Preservación de procedencia sin invención
@settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
@given(raw=pop_openalex_records())
def test_preservacion_de_procedencia_sin_invencion(raw: dict[str, str]) -> None:
    """source_url preserva la procedencia presente y queda None cuando no la hay.

    Validates: Requirements 7.3
    """
    record = _record_from_mapping(raw)
    expected = _expected_source_url(raw)

    if expected is not None:
        # Hay procedencia propia de OpenAlex → se preserva tal cual (la primera
        # candidata no vacía según el orden de FIELD_CANDIDATES).
        assert record.source_url == expected, (
            f"source_url debía preservar la procedencia {expected!r} pero fue "
            f"{record.source_url!r} para el registro {raw!r}"
        )
    else:
        # Ninguna candidata de procedencia presente → no se inventa.
        assert record.source_url is None, (
            f"source_url debía ser None (sin invención) pero fue "
            f"{record.source_url!r} para el registro {raw!r}"
        )
