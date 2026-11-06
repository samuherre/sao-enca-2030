"""Property test del Conector_Scholar (spec multi-source-bibliometria, tarea 2.5).

Property 4 del design.md — "Obligatorio faltante o ambiguo marca revisión":

    Para todo registro al que le falte ``title``, ``authors`` o
    ``publication_year``, o cuya detección sea ambigua, el conector fija
    ``inclusion_status = "PENDIENTE_REVISIÓN"`` con una nota NO vacía, sin
    eliminar el registro.

    **Validates: Requirements 2.3, 3.2**

Enfoque (Testing Strategy del design): se generan registros PoP sintéticos en
los que SIEMPRE falta al menos un campo obligatorio (title / authors / year), o
bien el año es AMBIGUO (texto no interpretable como año). Para cada registro se
verifica que ``_record_from_mapping`` produce un ``ArticleRecord`` con:

  - ``inclusion_status == "PENDIENTE_REVISIÓN"``,
  - ``notes`` no vacío,
  - y que el registro SÍ se produce (no se descarta), comprobando además que
    ``extract_records`` tampoco lo elimina.

Caso específico de Req 3.2 (año faltante o no detectable): además de marcar
revisión con nota, ``publication_year`` debe quedar en ``None``.

Los datos generados por hypothesis son SINTÉTICOS (datos de prueba, no reales).
"""

from __future__ import annotations

import csv
import json
import sys
import tempfile
from pathlib import Path

# Permite importar el conector desde bibliometrics/ (mismo patrón que el resto
# de pruebas unitarias del Componente B).
_REPO_ROOT = Path(__file__).resolve().parents[2]
_BIBLIO = _REPO_ROOT / "bibliometrics"
if str(_BIBLIO) not in sys.path:
    sys.path.insert(0, str(_BIBLIO))

from hypothesis import HealthCheck, given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

from ingestion.extract_scholar import (  # noqa: E402
    _record_from_mapping,
    extract_records,
)

# Las tres claves PoP que alimentan los campos OBLIGATORIOS del contrato V1.
# 'year' se trata aparte porque puede faltar o ser ambiguo (texto no numérico).
_REQUIRED_POP_KEYS = ("title", "authors", "year")

# Claves PoP opcionales que pueden estar presentes sin afectar la propiedad.
_OPTIONAL_POP_KEYS = (
    "doi",
    "url",
    "source",       # -> journal
    "publisher",
    "volume",
    "issue",
    "pages",
    "abstract",
    "keywords",
    "cites_url",
    "language",
)

# Texto no vacío plausible para valores presentes (sin bordes que _clean_str
# recorte a vacío). Excluye sustitutos y controles.
_non_empty_text = st.text(
    alphabet=st.characters(blacklist_categories=("Cs", "Cc"), min_codepoint=33),
    min_size=1,
    max_size=20,
)

# Valor de año AMBIGUO: presente pero no interpretable como un año de 4 dígitos
# al inicio (p. ej. "mil", "N/A", "veinte"). Se excluye todo lo que empiece por
# 4 dígitos, que _parse_year sí interpretaría.
_ambiguous_year = st.text(
    alphabet=st.characters(blacklist_categories=("Cs", "Cc", "Nd"), min_codepoint=33),
    min_size=1,
    max_size=10,
).filter(lambda s: s.strip() != "" and not s.strip()[:4].isdigit())


@st.composite
def pop_records_que_requieren_revision(draw: st.DrawFn) -> dict[str, str]:
    """Genera un registro PoP que DEBE caer en PENDIENTE_REVISIÓN.

    Garantiza que al menos uno de los obligatorios esté ausente, o que el año
    sea ambiguo. Estrategia:

    1. Año: FALTANTE, AMBIGUO o VÁLIDO (numérico de 4 dígitos).
    2. title y authors: presentes o ausentes de forma independiente.
    3. Si tras lo anterior el registro NO requiere revisión por obligatorios
       (title y authors presentes y año válido), se FUERZA la condición
       eliminando un obligatorio o volviendo ambiguo el año.
    4. Se añaden claves opcionales aleatorias (ruido) que no deben afectar.
    """
    record: dict[str, str] = {}

    # --- Año: faltante / ambiguo / válido ---
    year_mode = draw(st.sampled_from(["missing", "ambiguous", "valid"]))
    if year_mode == "ambiguous":
        record["year"] = draw(_ambiguous_year)
    elif year_mode == "valid":
        record["year"] = str(draw(st.integers(min_value=2020, max_value=2030)))
    # "missing" → no se añade la clave.

    # --- title / authors: presentes o ausentes ---
    title_present = draw(st.booleans())
    authors_present = draw(st.booleans())
    if title_present:
        record["title"] = draw(_non_empty_text)
    if authors_present:
        record["authors"] = draw(_non_empty_text)

    # --- Forzar que el registro requiera revisión ---
    # Requiere revisión si: falta title, falta authors, o el año no es válido
    # (faltante o ambiguo). Si por azar todo quedó válido, se rompe un obligatorio.
    year_ok = year_mode == "valid"
    if title_present and authors_present and year_ok:
        broken = draw(st.sampled_from(["title", "authors", "year"]))
        if broken == "title":
            record.pop("title", None)
        elif broken == "authors":
            record.pop("authors", None)
        else:  # year → ambiguo
            record["year"] = draw(_ambiguous_year)

    # --- Ruido: claves opcionales aleatorias (no deben afectar la propiedad) ---
    optional_present = draw(
        st.lists(
            st.sampled_from(_OPTIONAL_POP_KEYS),
            unique=True,
            min_size=0,
            max_size=len(_OPTIONAL_POP_KEYS),
        )
    )
    for key in optional_present:
        record[key] = draw(_non_empty_text)

    return record


def _year_is_missing_or_ambiguous(raw: dict[str, str]) -> bool:
    """True si 'year' está ausente o no es interpretable como año (Req 3.2)."""
    value = raw.get("year")
    if value is None:
        return True
    s = str(value).strip()
    if s == "":
        return True
    if s.isdigit():
        return False
    if len(s) >= 4 and s[:4].isdigit():
        return False
    return True


# Feature: multi-source-bibliometria, Property 4: Obligatorio faltante o ambiguo marca revisión
@settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
@given(raw=pop_records_que_requieren_revision())
def test_obligatorio_faltante_o_ambiguo_marca_revision(raw: dict[str, str]) -> None:
    """Obligatorio faltante/ambiguo → PENDIENTE_REVISIÓN + nota, sin eliminar.

    **Validates: Requirements 2.3, 3.2**
    """
    record = _record_from_mapping(raw)

    # El registro SE PRODUCE (no se descarta) y queda marcado para revisión.
    assert record is not None
    assert record.inclusion_status == "PENDIENTE_REVISIÓN", (
        f"Se esperaba PENDIENTE_REVISIÓN; entrada={raw!r}"
    )

    # La nota explicativa NO puede ser vacía (Req 2.3).
    assert record.notes is not None and record.notes.strip() != "", (
        f"Se esperaba una nota no vacía; entrada={raw!r}, notes={record.notes!r}"
    )

    # Req 3.2: año faltante o no detectable → publication_year None + revisión.
    if _year_is_missing_or_ambiguous(raw):
        assert record.publication_year is None, (
            "Año faltante/ambiguo debe dejar publication_year en None "
            f"(sin inventar); entrada={raw!r}, year={record.publication_year!r}"
        )


# Feature: multi-source-bibliometria, Property 4: Obligatorio faltante o ambiguo marca revisión
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture])
@given(raw=pop_records_que_requieren_revision())
def test_extract_records_no_descarta_registro_en_revision(raw: dict[str, str]) -> None:
    """``extract_records`` conserva (no elimina) el registro que requiere revisión.

    Complementa la propiedad escribiendo el registro a un Export_PoP real
    (JSON y CSV) y verificando que el conector lo devuelve, con el mismo estado
    de revisión y una nota no vacía. Esto cubre explícitamente la cláusula
    "sin eliminar el registro" de la Property 4.

    **Validates: Requirements 2.3, 3.2**
    """
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        # --- JSON: lista con un único objeto-registro ---
        json_file = tmp_path / "export.json"
        json_file.write_text(json.dumps([raw]), encoding="utf-8")
        json_records = extract_records(json_file)
        assert len(json_records) == 1, (
            f"El registro no debe eliminarse (JSON); entrada={raw!r}"
        )
        assert json_records[0].inclusion_status == "PENDIENTE_REVISIÓN"
        assert json_records[0].notes and json_records[0].notes.strip() != ""

        # --- CSV: cabecera con TODAS las claves posibles; valores vacíos para
        #     las ausentes (equivalen a ausencia según _clean_str del conector).
        csv_file = tmp_path / "export.csv"
        all_keys = list(_REQUIRED_POP_KEYS) + list(_OPTIONAL_POP_KEYS)
        with csv_file.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=all_keys)
            writer.writeheader()
            writer.writerow({k: raw.get(k, "") for k in all_keys})
        csv_records = extract_records(csv_file)
        assert len(csv_records) == 1, (
            f"El registro no debe eliminarse (CSV); entrada={raw!r}"
        )
        assert csv_records[0].inclusion_status == "PENDIENTE_REVISIÓN"
        assert csv_records[0].notes and csv_records[0].notes.strip() != ""
