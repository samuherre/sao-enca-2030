"""Property test del Pipeline_OpenAlex (spec fuente-openalex, tarea 2.2).

Property 7 del design.md — "Robustez ante registros malformados":

    Para toda mezcla de registros válidos y malformados en la entrada, el
    pipeline produce exactamente los registros válidos, descarta solo los
    malformados y no aborta el lote.

    **Validates: Requirements 1.5**

Enfoque (Testing Strategy del design): se generan entradas sintéticas que
mezclan, en orden aleatorio, registros VÁLIDOS (objetos clave→valor, con
subconjuntos variables de campos del contrato) y registros MALFORMADOS (entradas
que NO son un objeto: cadenas, enteros, listas, ``null``, booleanos). La mezcla
se escribe como un Export_PoP_OpenAlex JSON en una carpeta de entrada temporal y
se ejecuta el pipeline sobre ella (``process_folder``, el mismo recorrido que usa
la CLI). Para cada mezcla se verifica que:

  1. El pipeline NO aborta el lote (no lanza excepción) pese a los malformados.
  2. Produce EXACTAMENTE los registros válidos: el número de ``ArticleRecord``
     devueltos es igual al número de objetos válidos de la entrada.
  3. Descarta SOLO los malformados: ``descartados`` es igual al número de
     entradas no-objeto, y ``procesados`` es igual al número de válidos.
  4. Se conserva la invariante de ingesta ``leídos == procesados + descartados``
     (Req 1.6), coherente con el descarte robusto de Req 1.5.
  5. Todos los registros producidos son de la fuente fija ``"OpenAlex"`` (no se
     contaminan con otra fuente al procesar un lote mixto).

Los datos generados por hypothesis son SINTÉTICOS (datos de prueba, no reales);
se escriben en un directorio temporal y nunca tocan ``data/raw/openalex/``.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Permite importar el pipeline y el conector desde bibliometrics/ (mismo patrón
# que los demás tests de este paquete).
_REPO_ROOT = Path(__file__).resolve().parents[2]
_BIBLIO = _REPO_ROOT / "bibliometrics"
if str(_BIBLIO) not in sys.path:
    sys.path.insert(0, str(_BIBLIO))

import json  # noqa: E402
import tempfile  # noqa: E402

from hypothesis import HealthCheck, given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

from ingestion.extract_openalex import OPENALEX_SOURCE  # noqa: E402
from pipelines.process_openalex import process_folder  # noqa: E402


@st.composite
def valid_record(draw: st.DrawFn) -> dict[str, object]:
    """Registro VÁLIDO: un objeto clave→valor con subconjunto variable de campos.

    Un registro es "válido" para el pipeline si es un objeto parseable (dict),
    aun cuando le falten obligatorios (en ese caso el conector lo conserva con
    ``inclusion_status = "PENDIENTE_REVISIÓN"``, pero SÍ se produce). Se varían
    los campos presentes para no depender de una forma fija de la entrada.
    """
    record: dict[str, object] = {}
    if draw(st.booleans()):
        record["title"] = draw(
            st.sampled_from(
                [
                    "Conservación de aves en los Andes",
                    "Bird conservation in Antioquia",
                    "Aves de humedales interiores",
                ]
            )
        )
    if draw(st.booleans()):
        record["authors"] = draw(
            st.text(min_size=1, max_size=20).filter(lambda s: s.strip() != "")
        )
    if draw(st.booleans()):
        record["year"] = draw(st.integers(min_value=2015, max_value=2031).map(str))
    if draw(st.booleans()):
        record["doi"] = draw(
            st.text(min_size=1, max_size=20).filter(lambda s: s.strip() != "")
        )
    return record


# Entradas MALFORMADAS: cualquier cosa que NO sea un objeto clave→valor. El
# conector/pipeline debe descartarlas de forma robusta sin abortar el lote.
malformed_entry = st.one_of(
    st.text(max_size=20),                       # cadena suelta
    st.integers(),                              # entero suelto
    st.floats(allow_nan=False, allow_infinity=False),  # número suelto
    st.booleans(),                              # booleano suelto
    st.none(),                                  # null
    st.lists(st.integers(), max_size=3),        # lista (no objeto)
)


@st.composite
def mixed_entries(draw: st.DrawFn) -> tuple[list[object], int, int]:
    """Mezcla en orden aleatorio registros válidos y entradas malformadas.

    Devuelve ``(entries, n_validos, n_malformados)`` para contrastar contra la
    salida del pipeline. Se garantiza al menos una entrada para ejercer
    efectivamente el recorrido; la proporción válidos/malformados varía libremente
    (incluyendo lotes solo-válidos o solo-malformados).
    """
    valids = draw(st.lists(valid_record(), min_size=0, max_size=6))
    malformed = draw(st.lists(malformed_entry, min_size=0, max_size=6))

    entries: list[object] = list(valids) + list(malformed)
    # Orden aleatorio: los malformados pueden aparecer entremezclados, no solo
    # al final, para ejercer el descarte en cualquier posición del archivo.
    entries = draw(st.permutations(entries))
    return list(entries), len(valids), len(malformed)


# Feature: fuente-openalex, Property 7: Robustez ante registros malformados
@settings(max_examples=150, suppress_health_check=[HealthCheck.too_slow])
@given(data=mixed_entries())
def test_robustez_ante_registros_malformados(
    data: tuple[list[object], int, int],
) -> None:
    """El pipeline produce solo los válidos, descarta los malformados y no aborta.

    Validates: Requirements 1.5
    """
    entries, n_validos, n_malformados = data

    with tempfile.TemporaryDirectory() as tmp:
        input_dir = Path(tmp)
        export_path = input_dir / "export_pop_openalex.json"
        # Un Export_PoP JSON es una lista de objetos; aquí la contaminamos
        # deliberadamente con entradas no-objeto (malformadas).
        export_path.write_text(json.dumps(entries), encoding="utf-8")

        # (1) No aborta el lote: ejecutar el pipeline no debe lanzar excepción
        # pese a la presencia de registros malformados.
        records, leidos, procesados, descartados = process_folder(input_dir)

    # (2) Produce EXACTAMENTE los registros válidos.
    assert len(records) == n_validos, (
        f"el pipeline debe producir exactamente {n_validos} registro(s) válido(s), "
        f"produjo {len(records)}"
    )
    assert procesados == n_validos, (
        f"procesados debe ser {n_validos}, fue {procesados}"
    )

    # (3) Descarta SOLO los malformados.
    assert descartados == n_malformados, (
        f"descartados debe ser {n_malformados} (solo los malformados), "
        f"fue {descartados}"
    )

    # (4) Invariante de ingesta: leídos == procesados + descartados (Req 1.6).
    assert leidos == len(entries)
    assert leidos == procesados + descartados, (
        f"leídos ({leidos}) debe ser procesados ({procesados}) + "
        f"descartados ({descartados})"
    )

    # (5) Fuente fija: ningún registro producido cambia de origen en lote mixto.
    for rec in records:
        assert rec.source == OPENALEX_SOURCE == "OpenAlex", (
            f"source debe ser 'OpenAlex', fue {rec.source!r}"
        )
