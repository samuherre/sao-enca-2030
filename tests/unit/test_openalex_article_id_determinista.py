"""Property test del Conector_OpenAlex (spec fuente-openalex, tarea 1.7).

Property 6 del design.md — "``article_id`` determinista, reproducible y con
prefijo propio":

    Para todo registro de entrada, aplicar el conector dos veces produce el mismo
    ``article_id``, el ``article_id`` empieza por ``oa-``, y nunca coincide con el
    prefijo ``gs-`` de Google Scholar.

    **Validates: Requirements 2.6**

Enfoque (Testing Strategy del design): se generan registros PoP/OpenAlex
sintéticos con presencia variable de campos (con y SIN DOI, años dentro/fuera de
rango o ausentes, títulos repetidos). Para cada registro se verifica que:

  1. Aplicar el conector dos veces sobre el MISMO registro produce idéntico
     ``article_id`` (determinismo / reproducibilidad entre corridas).
  2. ``article_id`` empieza por el prefijo propio ``"oa-"`` (Req 2.6).
  3. ``article_id`` nunca empieza por ``"gs-"`` (prefijo de Google Scholar), para
     evitar colisiones de identificador entre fuentes.

Se ejerce tanto la ruta pura (``_record_from_mapping``) como la interfaz pública
``extract_records`` (JSON y CSV), para garantizar la propiedad extremo a extremo.

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

from ingestion.extract_openalex import (  # noqa: E402
    _record_from_mapping,
    extract_records,
)

# Prefijos de identificador por fuente: propio de OpenAlex vs. el de Scholar.
OPENALEX_PREFIX = "oa-"
SCHOLAR_PREFIX = "gs-"


def _assert_property_6(article_id: str) -> None:
    """Verifica las garantías de prefijo de Property 6 sobre un ``article_id``."""
    assert article_id.startswith(OPENALEX_PREFIX), (
        f"article_id debe empezar por {OPENALEX_PREFIX!r}, fue {article_id!r}"
    )
    assert not article_id.startswith(SCHOLAR_PREFIX), (
        f"article_id nunca debe empezar por el prefijo de Scholar "
        f"{SCHOLAR_PREFIX!r}, fue {article_id!r}"
    )


@st.composite
def openalex_record(draw: st.DrawFn) -> dict[str, str]:
    """Genera un registro PoP/OpenAlex sintético con presencia variable de campos.

    - ``doi`` puede estar presente o ausente, para ejercer ambas ramas del
      cálculo del ``article_id`` (con DOI vs. título+año).
    - ``title`` puede estar presente o ausente; se usa un conjunto pequeño de
      títulos para provocar repeticiones (títulos repetidos).
    - ``year`` puede ser válido en rango, fuera de rango, no interpretable o
      ausente, cubriendo las distintas ramas de normalización del año.
    """
    record: dict[str, str] = {}

    if draw(st.booleans()):
        record["title"] = draw(
            st.sampled_from(
                [
                    "Conservación de aves en los Andes",
                    "Bird conservation in Antioquia",
                    "Aves de humedales interiores",
                    "A STUDY OF URBAN BIRDS",
                ]
            )
        )
    if draw(st.booleans()):
        record["authors"] = draw(
            st.text(min_size=1, max_size=30).filter(lambda s: s.strip() != "")
        )
    if draw(st.booleans()):
        record["year"] = draw(
            st.one_of(
                st.integers(min_value=2020, max_value=2030).map(str),  # en rango
                st.integers(min_value=1900, max_value=2019).map(str),  # fuera (bajo)
                st.integers(min_value=2031, max_value=2100).map(str),  # fuera (alto)
                st.text(min_size=1, max_size=6).filter(
                    lambda s: s.strip() != "" and not s.strip().isdigit()
                ),  # no interpretable (ambiguo)
            )
        )
    if draw(st.booleans()):
        record["doi"] = draw(
            st.text(min_size=1, max_size=25).filter(lambda s: s.strip() != "")
        )

    return record


# Feature: fuente-openalex, Property 6: article_id determinista, reproducible y con prefijo propio
@settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
@given(raw=openalex_record())
def test_article_id_determinista_reproducible_y_prefijo_propio(
    raw: dict[str, str],
) -> None:
    """El article_id es determinista, empieza por 'oa-' y nunca por 'gs-'.

    Validates: Requirements 2.6
    """
    # (1) Determinismo / reproducibilidad en la ruta pura: dos aplicaciones del
    # conector sobre el MISMO registro producen idéntico article_id.
    id_pura_1 = _record_from_mapping(raw).article_id
    id_pura_2 = _record_from_mapping(raw).article_id
    assert id_pura_1 == id_pura_2, (
        "article_id no es reproducible entre corridas para el mismo registro: "
        f"{id_pura_1!r} != {id_pura_2!r}"
    )

    # (2) y (3) Prefijo propio 'oa-' y nunca 'gs-'.
    _assert_property_6(id_pura_1)

    # Ruta extremo a extremo (interfaz pública extract_records) en JSON y CSV:
    # se verifica igualdad entre dos corridas y las garantías de prefijo.
    with tempfile.TemporaryDirectory() as tmp:
        # --- JSON ---
        json_path = Path(tmp) / "export.json"
        json_path.write_text(json.dumps([raw]), encoding="utf-8")
        json_ids_1 = [r.article_id for r in extract_records(json_path)]
        json_ids_2 = [r.article_id for r in extract_records(json_path)]
        assert json_ids_1 == json_ids_2, (
            "article_id no reproducible vía extract_records (JSON): "
            f"{json_ids_1!r} != {json_ids_2!r}"
        )
        for article_id in json_ids_1:
            _assert_property_6(article_id)
        # Coherencia entre la ruta pura y la pública para el mismo registro.
        assert json_ids_1 == [id_pura_1]

        # --- CSV ---
        csv_path = Path(tmp) / "export.csv"
        buffer = io.StringIO()
        fieldnames = sorted(raw.keys())
        writer = csv.DictWriter(buffer, fieldnames=fieldnames)
        writer.writeheader()
        if fieldnames:
            writer.writerow(raw)
        csv_path.write_text(buffer.getvalue(), encoding="utf-8")
        csv_ids_1 = [r.article_id for r in extract_records(csv_path)]
        csv_ids_2 = [r.article_id for r in extract_records(csv_path)]
        assert csv_ids_1 == csv_ids_2, (
            "article_id no reproducible vía extract_records (CSV): "
            f"{csv_ids_1!r} != {csv_ids_2!r}"
        )
        for article_id in csv_ids_1:
            _assert_property_6(article_id)
