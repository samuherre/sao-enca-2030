"""Property test del conector OpenAlex (spec fuente-openalex, tarea 1.6).

Property 5 del design.md — "Validación de período no descarta":

    Para todo registro con ``publication_year`` fuera de 2020–2030, el conector
    fija ``inclusion_status = "PENDIENTE_REVISIÓN"`` con una nota y CONSERVA el
    registro; para años dentro del rango no fuerza ese estado por motivo de
    período.

    **Validates: Requirements 3.1**

Enfoque (Testing Strategy del design): se generan registros PoP/OpenAlex
sintéticos COMPLETOS en los obligatorios (``title`` y ``authors`` presentes) con
años tanto DENTRO como FUERA del periodo 2020–2030, de modo que el ÚNICO
disparador de revisión bajo prueba sea el período. Se ejercen a través de
``_record_from_mapping`` directamente y, de extremo a extremo, vía
``extract_records`` parseando un archivo temporal ``.json``.

Aserciones:
  - Año FUERA de rango → el registro se PRODUCE (no se descarta),
    ``inclusion_status == "PENDIENTE_REVISIÓN"`` y ``notes`` menciona el período
    ("fuera del periodo") y el año.
  - Año DENTRO de rango → el conector NO marca revisión *por motivo de período*:
    ``notes`` NO contiene el mensaje de fuera-de-período. (En V1
    ``PENDIENTE_REVISIÓN`` es el estado base del contrato con una nota sobre
    relevancia/OFC pendiente; por eso NO se afirma que el estado cambie, solo
    que no aparece la nota de período.)

Los datos generados por hypothesis son SINTÉTICOS (datos de prueba, no reales).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Permite importar el conector desde bibliometrics/ (mismo patrón que el resto
# de pruebas unitarias del Componente B).
_REPO_ROOT = Path(__file__).resolve().parents[2]
_BIBLIO = _REPO_ROOT / "bibliometrics"
if str(_BIBLIO) not in sys.path:
    sys.path.insert(0, str(_BIBLIO))

from hypothesis import HealthCheck, given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

from ingestion.extract_openalex import (  # noqa: E402
    PERIODO_MAX,
    PERIODO_MIN,
    _record_from_mapping,
    extract_records,
)

# Fragmento de la nota que el conector añade SOLO cuando el año está fuera de
# rango (ver ``_record_from_mapping``: "Año {year} fuera del periodo ...").
_OUT_OF_PERIOD_MARK = "fuera del periodo"


# Años fuera del periodo 2020–2030 (por debajo o por encima), acotados a un
# rango plausible de 4 cifras para que ``_parse_year`` los interprete como año.
_years_out_of_range = st.one_of(
    st.integers(min_value=1000, max_value=PERIODO_MIN - 1),
    st.integers(min_value=PERIODO_MAX + 1, max_value=9999),
)

# Años dentro del periodo (inclusive en ambos extremos).
_years_in_range = st.integers(min_value=PERIODO_MIN, max_value=PERIODO_MAX)

# Texto no vacío para los obligatorios (title, authors). Se evitan caracteres de
# control/surrogates y espacios al borde que ``_clean_str`` recortaría a vacío.
_nonempty_text = st.text(
    alphabet=st.characters(blacklist_categories=("Cs", "Cc"), min_codepoint=33),
    min_size=1,
    max_size=40,
)


def _build_pop_record(title: str, authors: str, year: int) -> dict[str, str]:
    """Registro PoP/OpenAlex sintético COMPLETO en obligatorios, con el año dado."""
    return {"title": title, "authors": authors, "year": str(year)}


# Feature: fuente-openalex, Property 5: Validación de período no descarta
@settings(max_examples=150, suppress_health_check=[HealthCheck.too_slow])
@given(title=_nonempty_text, authors=_nonempty_text, year=_years_out_of_range)
def test_periodo_fuera_de_rango_marca_revision_sin_descartar(
    title: str, authors: str, year: int
) -> None:
    """Año fuera de 2020–2030: se conserva, marca revisión y la nota cita el período.

    ``_record_from_mapping`` SIEMPRE devuelve un ``ArticleRecord`` (nunca lanza
    ni descarta por período): obtener un registro ya evidencia la conservación.
    Se afirma además el estado de revisión y el contenido de la nota.

    **Validates: Requirements 3.1**
    """
    raw = _build_pop_record(title, authors, year)
    record = _record_from_mapping(raw)

    # Conservado (no descartado) y con el año fuera de rango intacto.
    assert record is not None
    assert record.publication_year == year

    assert record.inclusion_status == "PENDIENTE_REVISIÓN", (
        f"Año {year} fuera de rango debe quedar en PENDIENTE_REVISIÓN; "
        f"se obtuvo {record.inclusion_status!r}."
    )
    assert record.notes is not None
    assert _OUT_OF_PERIOD_MARK in record.notes, (
        f"La nota debe mencionar el período fuera de rango; notes={record.notes!r}."
    )
    assert str(year) in record.notes, (
        f"La nota debe citar el año fuera de rango ({year}); notes={record.notes!r}."
    )


# Feature: fuente-openalex, Property 5: Validación de período no descarta
@settings(max_examples=150, suppress_health_check=[HealthCheck.too_slow])
@given(title=_nonempty_text, authors=_nonempty_text, year=_years_in_range)
def test_periodo_en_rango_no_marca_por_motivo_de_periodo(
    title: str, authors: str, year: int
) -> None:
    """Año dentro de 2020–2030: la nota NO contiene el mensaje de fuera-de-período.

    No se afirma que ``inclusion_status`` cambie: en V1 PENDIENTE_REVISIÓN es el
    estado base del contrato (relevancia/OFC pendiente). La propiedad solo exige
    que el período NO sea el motivo de revisión para años en rango, con los
    obligatorios completos.

    **Validates: Requirements 3.1**
    """
    raw = _build_pop_record(title, authors, year)
    record = _record_from_mapping(raw)

    assert record.notes is not None
    assert _OUT_OF_PERIOD_MARK not in record.notes, (
        f"Año {year} está en rango; la nota NO debe marcar fuera-de-período; "
        f"notes={record.notes!r}."
    )
    # El registro se produce y conserva el año tal cual.
    assert record.publication_year == year


# Verificación complementaria (no es la propiedad núcleo): confirma de extremo a
# extremo —vía extract_records parseando un archivo real— que un registro con
# año fuera de rango NO se descarta. Se deja fuera del bucle de hypothesis para
# no incurrir en I/O de disco por cada ejemplo.
def test_extract_records_no_descarta_ano_fuera_de_rango(tmp_path: Path) -> None:
    """Un Export_PoP_OpenAlex con año fuera de 2020–2030 produce el registro."""
    out_of_range_year = PERIODO_MIN - 5  # claramente fuera del periodo
    raw = _build_pop_record("Un título de prueba", "Autor A; Autor B", out_of_range_year)

    input_path = tmp_path / "export_pop_openalex.json"
    input_path.write_text(json.dumps([raw]), encoding="utf-8")

    records = extract_records(input_path)

    assert len(records) == 1, (
        "Un registro válido con año fuera de rango NO debe descartarse."
    )
    produced = records[0]
    assert produced.publication_year == out_of_range_year
    assert produced.inclusion_status == "PENDIENTE_REVISIÓN"
    assert produced.notes is not None and _OUT_OF_PERIOD_MARK in produced.notes
