"""Property test del Conector_Scholar (spec multi-source-bibliometria, tarea 2.3).

Property 2 del design.md — "No-invención de campos ausentes":

    Para todo registro del Export_PoP, cada campo del contrato que NO esté
    presente en el registro de entrada queda en ``None`` en el ``ArticleRecord``
    producido (no se sustituye por un valor inventado).

    **Validates: Requirements 2.2**

Enfoque (Testing Strategy del design): se generan registros PoP sintéticos con
subconjuntos aleatorios de las claves mapeables. Para cada clave mapeable
AUSENTE en la entrada, se verifica que el campo del contrato correspondiente sea
``None`` en el ``ArticleRecord`` producido por ``extract_records`` /
``_record_from_mapping``.

Se EXCLUYEN de la aserción "debe ser None" los campos que NO provienen del
export y que el conector siempre fija: ``source`` (siempre "Google Scholar"),
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

from ingestion.extract_scholar import _record_from_mapping  # noqa: E402

# Claves PoP mapeables → campo del contrato V1 que alimentan. Solo se usa la
# clave "canónica" por campo (la tabla del diseño permite alias, p. ej.
# authors/author; basta una por campo para ejercer la propiedad de ausencia).
# Pares (clave_pop, campo_contrato) sobre los que se genera el subconjunto.
MAPPABLE_KEYS: dict[str, str] = {
    "title": "title",
    "authors": "authors",
    "year": "publication_year",
    "doi": "doi",
    "url": "url",
    "source": "journal",          # PoP 'Source' = revista/medio -> journal
    "publisher": "publisher",
    "volume": "volume",
    "issue": "issue",
    "pages": "pages",
    "abstract": "abstract",
    "keywords": "keywords",
    "cites_url": "source_url",
    "language": "language",
}

# Campos del contrato que SIEMPRE se fijan aparte (no provienen del export):
# no deben entrar en la aserción "debe ser None".
ALWAYS_SET_FIELDS = {"source", "extraction_date", "extraction_method", "article_id"}

# Valores no vacíos plausibles para las claves presentes. Para 'year' usamos
# dígitos para que sea interpretable como año; el resto son textos no vacíos.
_POP_KEYS = sorted(MAPPABLE_KEYS.keys())


@st.composite
def pop_record_subsets(draw: st.DrawFn) -> dict[str, str]:
    """Genera un registro PoP sintético con un SUBCONJUNTO aleatorio de claves.

    - Elige un subconjunto (posiblemente vacío) de las claves mapeables.
    - Asigna a cada clave presente un valor no vacío (los valores vacíos
      equivalen a ausencia según ``_clean_str`` del conector, y aquí queremos
      que "presente" signifique realmente presente).
    - 'year' recibe un valor numérico de 4 dígitos para que sea interpretable.
    """
    present = draw(
        st.lists(st.sampled_from(_POP_KEYS), unique=True, min_size=0, max_size=len(_POP_KEYS))
    )
    record: dict[str, str] = {}
    for key in present:
        if key == "year":
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


# Feature: multi-source-bibliometria, Property 2: No-invención de campos ausentes
@settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
@given(raw=pop_record_subsets())
def test_no_invencion_de_campos_ausentes(raw: dict[str, str]) -> None:
    """Cada clave mapeable ausente deja su campo de contrato en None.

    Validates: Requirements 2.2
    """
    record = _record_from_mapping(raw)
    present_keys = set(raw.keys())

    for pop_key, contract_field in MAPPABLE_KEYS.items():
        if contract_field in ALWAYS_SET_FIELDS:
            continue
        if pop_key not in present_keys:
            value = getattr(record, contract_field)
            assert value is None, (
                f"Clave PoP '{pop_key}' ausente pero el campo de contrato "
                f"'{contract_field}' no es None: {value!r} (no-invención violada)"
            )

    # Invariantes de los campos que SIEMPRE se fijan (nunca None por ausencia):
    # garantizan que la exclusión es correcta y que no se contaminan.
    assert record.source == "Google Scholar"
    assert record.article_id is not None
    assert record.extraction_date is not None
    assert record.extraction_method is not None
