"""Property test del Conector_Scholar (spec multi-source-bibliometria, tarea 2.4).

Property 3 del design.md — "Fuente fija y conformidad del contrato":

    Para todo registro producido por el conector de Google Scholar,
    ``source == "Google Scholar"`` y el registro cumple el contrato V1 (todos
    los obligatorios presentes, o bien ``inclusion_status == "PENDIENTE_REVISIÓN"``).

    **Validates: Requirements 2.1**

Enfoque (Testing Strategy del design): se generan registros PoP sintéticos con
subconjuntos aleatorios de claves mapeables (campos obligatorios presentes o
ausentes, años válidos o inválidos). Para cada ``ArticleRecord`` producido por
``extract_records`` / ``_record_from_mapping`` se verifica:

  1. ``record.source == "Google Scholar"`` (fuente de ingesta fija, Req 2.1).
  2. Conformidad del contrato V1: TODOS los obligatorios
     (``title``, ``authors``, ``publication_year``) están presentes, O BIEN
     ``inclusion_status == "PENDIENTE_REVISIÓN"``.

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

import csv  # noqa: E402
import io  # noqa: E402
import json  # noqa: E402
import tempfile  # noqa: E402

from hypothesis import HealthCheck, given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

from ingestion.extract_scholar import (  # noqa: E402
    SCHOLAR_SOURCE,
    _record_from_mapping,
    extract_records,
)

# Campos obligatorios del contrato V1 según el conector Scholar (design.md).
REQUIRED_FIELDS = ("title", "authors", "publication_year")

# Claves PoP mapeables sobre las que se construyen los registros sintéticos.
# Incluye las tres obligatorias y una muestra de opcionales para variar la forma
# de la entrada sin depender de la tabla completa.
_OPTIONAL_KEYS = ["doi", "url", "source", "publisher", "abstract", "keywords", "language"]


def _assert_property_3(record) -> None:
    """Verifica Property 3 sobre un ``ArticleRecord`` producido por el conector."""
    # (1) Fuente fija.
    assert record.source == SCHOLAR_SOURCE == "Google Scholar", (
        f"source debe ser 'Google Scholar', fue {record.source!r}"
    )

    # (2) Conformidad del contrato V1: obligatorios presentes O marca de revisión.
    todos_obligatorios = all(
        getattr(record, campo) is not None for campo in REQUIRED_FIELDS
    )
    marcado_revision = record.inclusion_status == "PENDIENTE_REVISIÓN"
    assert todos_obligatorios or marcado_revision, (
        "El registro no cumple el contrato V1: faltan obligatorios "
        f"(title={record.title!r}, authors={record.authors!r}, "
        f"publication_year={record.publication_year!r}) y no está marcado como "
        f"PENDIENTE_REVISIÓN (inclusion_status={record.inclusion_status!r})."
    )


@st.composite
def pop_record(draw: st.DrawFn) -> dict[str, str]:
    """Genera un registro PoP sintético con presencia variable de obligatorios.

    - Cada campo obligatorio (title, authors, year) puede estar presente o no.
    - El año, cuando está presente, puede ser válido en rango (2020–2030), fuera
      de rango, o un valor no interpretable (texto), para ejercer las ramas de
      año válido / período fuera de rango / año ambiguo.
    - Se añade un subconjunto aleatorio de claves opcionales con texto no vacío.
    """
    record: dict[str, str] = {}

    if draw(st.booleans()):
        record["title"] = draw(
            st.text(min_size=1, max_size=30).filter(lambda s: s.strip() != "")
        )
    if draw(st.booleans()):
        record["authors"] = draw(
            st.text(min_size=1, max_size=30).filter(lambda s: s.strip() != "")
        )
    if draw(st.booleans()):
        year_value = draw(
            st.one_of(
                st.integers(min_value=2020, max_value=2030).map(str),  # en rango
                st.integers(min_value=1900, max_value=2019).map(str),  # fuera (bajo)
                st.integers(min_value=2031, max_value=2100).map(str),  # fuera (alto)
                st.text(min_size=1, max_size=6).filter(
                    lambda s: s.strip() != "" and not s.strip().isdigit()
                ),  # no interpretable (ambiguo)
            )
        )
        record["year"] = year_value

    present_optionals = draw(
        st.lists(st.sampled_from(_OPTIONAL_KEYS), unique=True, min_size=0)
    )
    for key in present_optionals:
        record[key] = draw(
            st.text(min_size=1, max_size=20).filter(lambda s: s.strip() != "")
        )
    return record


# Feature: multi-source-bibliometria, Property 3: Fuente fija y conformidad del contrato
@settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
@given(raw=pop_record())
def test_fuente_fija_y_conformidad_contrato(raw: dict[str, str]) -> None:
    """Todo registro del conector tiene source fijo y cumple el contrato V1.

    Se ejerce la ruta pura (``_record_from_mapping``) y, además, la ruta de
    ``extract_records`` escribiendo el registro como JSON y como CSV en archivos
    temporales, para garantizar la propiedad sobre la interfaz pública.

    **Validates: Requirements 2.1**
    """
    # Ruta pura (mapeo directo).
    _assert_property_3(_record_from_mapping(raw))

    # Ruta JSON de extract_records.
    with tempfile.TemporaryDirectory() as tmp:
        json_path = Path(tmp) / "export.json"
        json_path.write_text(json.dumps([raw]), encoding="utf-8")
        for rec in extract_records(json_path):
            _assert_property_3(rec)

        # Ruta CSV de extract_records (todas las claves presentes como columnas).
        csv_path = Path(tmp) / "export.csv"
        buffer = io.StringIO()
        fieldnames = sorted(raw.keys())
        writer = csv.DictWriter(buffer, fieldnames=fieldnames)
        writer.writeheader()
        if fieldnames:
            writer.writerow(raw)
        csv_path.write_text(buffer.getvalue(), encoding="utf-8")
        for rec in extract_records(csv_path):
            _assert_property_3(rec)
