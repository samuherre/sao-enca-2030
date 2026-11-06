"""Property test del Conector_OpenAlex (spec fuente-openalex, tarea 1.3).

Property 2 del design.md — "No-invención de campos ausentes":

    Para todo registro del Export_PoP_OpenAlex, cada campo del contrato que NO
    esté presente en el registro de entrada queda en ``None`` en el
    ``ArticleRecord`` producido (no se sustituye por un valor inventado).

    **Validates: Requirements 2.3**

Enfoque (Testing Strategy del design): se generan registros PoP/OpenAlex
sintéticos con subconjuntos aleatorios de las claves candidatas del conector
(``FIELD_CANDIDATES``). Para cada campo del contrato cuyas claves candidatas
estén TODAS ausentes de la entrada, se verifica que el campo del
``ArticleRecord`` producido por ``_record_from_mapping`` sea ``None``.

La verificación es por campo (no por clave): un campo mapeable solo debe quedar
en ``None`` cuando NINGUNA de sus claves candidatas está presente, porque el
conector toma la primera candidata no vacía. Varios campos comparten claves
(p. ej. ``url`` y ``source_url`` aceptan ambos ``id``/``url``), de modo que la
presencia de una clave compartida puede alimentar más de un campo; por eso el
criterio de ausencia se evalúa sobre el conjunto completo de candidatas.

Se EXCLUYEN de la aserción "debe ser None" los campos que NO provienen del
export y que el conector siempre fija: ``source`` (siempre "OpenAlex"),
``extraction_date``, ``extraction_method`` y ``article_id`` (id interno
determinista).

Los datos generados por hypothesis son SINTÉTICOS (datos de prueba, no reales).
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
    OPENALEX_SOURCE,
    _record_from_mapping,
)

# Campos del contrato que SIEMPRE se fijan aparte (no provienen del export):
# no deben entrar en la aserción "debe ser None".
ALWAYS_SET_FIELDS = {"source", "extraction_date", "extraction_method", "article_id"}

# Universo de claves candidatas que el conector sabe mapear (unión de todas las
# tuplas de FIELD_CANDIDATES). El generador elige subconjuntos de aquí.
_ALL_CANDIDATE_KEYS = sorted(
    {key for candidates in FIELD_CANDIDATES.values() for key in candidates}
)


@st.composite
def pop_openalex_record_subsets(draw: st.DrawFn) -> dict[str, str]:
    """Genera un registro PoP/OpenAlex sintético con un SUBCONJUNTO aleatorio de claves.

    - Elige un subconjunto (posiblemente vacío) de las claves candidatas.
    - Asigna a cada clave presente un valor no vacío (los valores vacíos
      equivalen a ausencia según ``_clean_str`` del conector, y aquí queremos
      que "presente" signifique realmente presente).
    - Las claves de año (``year``/``publication_year``) reciben un valor
      numérico de 4 dígitos para que sean interpretables.
    """
    present = draw(
        st.lists(
            st.sampled_from(_ALL_CANDIDATE_KEYS),
            unique=True,
            min_size=0,
            max_size=len(_ALL_CANDIDATE_KEYS),
        )
    )
    year_keys = set(FIELD_CANDIDATES["publication_year"])
    record: dict[str, str] = {}
    for key in present:
        if key in year_keys:
            year = draw(st.integers(min_value=1900, max_value=2100))
            record[key] = str(year)
        else:
            # Texto no vacío (sin espacios al borde que _clean_str recorte a vacío).
            value = draw(
                st.text(
                    alphabet=st.characters(
                        blacklist_categories=("Cs", "Cc"), min_codepoint=33
                    ),
                    min_size=1,
                    max_size=20,
                )
            )
            record[key] = value
    return record


# Feature: fuente-openalex, Property 2: No-invención de campos ausentes
@settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
@given(raw=pop_openalex_record_subsets())
def test_no_invencion_de_campos_ausentes(raw: dict[str, str]) -> None:
    """Un campo con TODAS sus claves candidatas ausentes queda en None.

    Validates: Requirements 2.3
    """
    record = _record_from_mapping(raw)
    present_keys = set(raw.keys())

    for contract_field, candidates in FIELD_CANDIDATES.items():
        if contract_field in ALWAYS_SET_FIELDS:
            continue
        # El campo solo debe ser None cuando NINGUNA candidata está presente;
        # el conector toma la primera candidata no vacía disponible.
        if present_keys.isdisjoint(candidates):
            value = getattr(record, contract_field)
            assert value is None, (
                f"Campo de contrato '{contract_field}' no es None pese a que "
                f"ninguna de sus claves candidatas {candidates} está presente: "
                f"{value!r} (no-invención violada)"
            )

    # Invariantes de los campos que SIEMPRE se fijan (nunca None por ausencia):
    # garantizan que la exclusión es correcta y que no se contaminan.
    assert record.source == OPENALEX_SOURCE
    assert record.article_id is not None
    assert record.extraction_date is not None
    assert record.extraction_method is not None
