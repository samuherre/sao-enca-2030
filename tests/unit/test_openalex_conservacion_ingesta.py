"""Property test del pipeline OpenAlex — conservación aritmética de ingesta.

Spec: fuente-openalex, tarea 2.3.
Función bajo prueba: ``process_folder(input_dir)`` de
``bibliometrics/pipelines/process_openalex.py``, que devuelve la tupla
``(records, leidos, procesados, descartados)``.

Property 8 (design.md) — "Conservación aritmética del resumen de ingesta":

    Para toda ejecución del pipeline,
        ``registros_leídos == registros_procesados + registros_descartados``.

    **Validates: Requirements 1.6**

Enfoque (Testing Strategy del design): se generan mezclas arbitrarias de
registros válidos y malformados repartidos en uno o más archivos de entrada
(``.json`` y/o ``.csv``) dentro de una carpeta temporal **fuera de**
``data/raw`` (``tmp_path_factory`` de pytest). Se ejecuta ``process_folder``
sobre esa carpeta y se verifica la invariante aritmética
``leidos == procesados + descartados``.

Es el ESPEJO del test equivalente de Google Scholar
(``test_scholar_conservacion_ingesta.py``), apuntando al pipeline de OpenAlex.

- Los datos generados por hypothesis son SINTÉTICOS (datos de prueba, no reales).
- Cada ejemplo escribe en una subcarpeta propia y la limpia al terminar, de modo
  que los ejemplos no interfieran entre sí.
- Nunca se escribe en ``data/raw``: la entrada vive bajo ``tmp_path_factory``.
"""

from __future__ import annotations

import json
import shutil
import sys
import uuid
from pathlib import Path

# Permite importar el pipeline y el conector desde bibliometrics/ (mismo patrón
# que el resto de pruebas unitarias del Componente B).
_REPO_ROOT = Path(__file__).resolve().parents[2]
_BIBLIO = _REPO_ROOT / "bibliometrics"
if str(_BIBLIO) not in sys.path:
    sys.path.insert(0, str(_BIBLIO))

from hypothesis import HealthCheck, given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

from pipelines.process_openalex import process_folder  # noqa: E402


# --- Generadores de registros PoP/OpenAlex sintéticos ------------------------

# Claves PoP/OpenAlex mapeables que puede traer un registro válido (objeto
# clave→valor). Un subconjunto de ellas basta para ejercer la ingesta; el
# pipeline no necesita que estén todas presentes.
_POP_KEYS = ["title", "authors", "year", "doi", "source", "abstract"]


@st.composite
def _valid_json_record(draw: st.DrawFn) -> dict:
    """Objeto clave→valor (registro PoP/OpenAlex válido/procesable).

    Es un ``dict``, por lo que ``extract_records`` lo procesará (aunque le
    falten obligatorios: en ese caso queda PENDIENTE_REVISIÓN, pero cuenta como
    procesado, no descartado).
    """
    keys = draw(
        st.lists(
            st.sampled_from(_POP_KEYS),
            unique=True,
            min_size=0,
            max_size=len(_POP_KEYS),
        )
    )
    record: dict = {}
    for key in keys:
        if key == "year":
            record[key] = str(draw(st.integers(min_value=1990, max_value=2035)))
        else:
            record[key] = draw(st.text(min_size=1, max_size=15))
    return record


# Entradas JSON malformadas = elementos que NO son objetos clave→valor. El
# conector las cuenta como leídas pero las descarta (Req 1.5/1.6).
_malformed_json_entry = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(max_size=10),
    st.lists(st.integers(), max_size=3),
)

# Un elemento de una lista JSON: válido (dict) o malformado (no-dict).
_json_entry = st.one_of(_valid_json_record(), _malformed_json_entry)


@st.composite
def _csv_rows(draw: st.DrawFn) -> list[dict]:
    """Filas de un CSV de PoP/OpenAlex (cada fila es un dict vía DictReader).

    Las columnas son un subconjunto fijo por archivo; algunas celdas pueden ir
    vacías. Todas las filas son objetos clave→valor (el CSV no produce entradas
    "no-dict"), por lo que cuentan como leídas y procesadas.
    """
    columns = draw(
        st.lists(
            st.sampled_from(_POP_KEYS),
            unique=True,
            min_size=1,
            max_size=len(_POP_KEYS),
        )
    )
    n_rows = draw(st.integers(min_value=0, max_value=6))
    rows: list[dict] = []
    for _ in range(n_rows):
        row: dict = {}
        for col in columns:
            if col == "year":
                row[col] = draw(st.sampled_from(["", "2021", "2025", "abcd", "1999"]))
            else:
                # Se excluyen separadores de CSV y los surrogates (categoría
                # Unicode "Cs"): un surrogate suelto no es texto UTF-8 válido y
                # jamás aparecería en un Export_PoP real, pero ``csv.writer``
                # falla al intentar escribirlo. Restringir el alfabeto mantiene
                # el dato sintético pero representable como una celda CSV real.
                row[col] = draw(
                    st.text(
                        alphabet=st.characters(
                            blacklist_characters=',"\r\n',
                            blacklist_categories=("Cs",),
                        ),
                        max_size=12,
                    )
                )
        rows.append(row)
    return rows


def _write_csv(path: Path, rows: list[dict]) -> None:
    """Escribe filas como CSV sencillo. Si no hay filas, escribe solo cabecera."""
    import csv

    # La cabecera determina las columnas; si no hay filas no hay columnas
    # conocidas, así que se deja un CSV con solo una cabecera mínima.
    fieldnames = list(rows[0].keys()) if rows else ["title"]
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


# Especificación de un archivo de entrada: tipo + contenido sintético.
@st.composite
def _input_files_spec(draw: st.DrawFn) -> list[tuple[str, object]]:
    """Genera 0..N archivos de entrada, cada uno JSON (lista) o CSV (filas)."""
    n_files = draw(st.integers(min_value=0, max_value=4))
    specs: list[tuple[str, object]] = []
    for _ in range(n_files):
        kind = draw(st.sampled_from(["json", "csv"]))
        if kind == "json":
            entries = draw(st.lists(_json_entry, max_size=8))
            specs.append(("json", entries))
        else:
            rows = draw(_csv_rows())
            specs.append(("csv", rows))
    return specs


# Feature: fuente-openalex, Property 8: Conservación aritmética del resumen de ingesta
@settings(max_examples=150, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(files_spec=_input_files_spec())
def test_conservacion_aritmetica_del_resumen_de_ingesta(
    tmp_path_factory, files_spec: list[tuple[str, object]]
) -> None:
    """``leidos == procesados + descartados`` para cualquier mezcla de entradas.

    Validates: Requirements 1.6
    """
    # Carpeta de entrada propia de ESTE ejemplo, fuera de data/raw, para aislar
    # ejemplos entre sí y poder limpiarla de forma determinista.
    input_dir = tmp_path_factory.mktemp("oa_ingesta") / f"in_{uuid.uuid4().hex}"
    input_dir.mkdir(parents=True)

    try:
        for idx, (kind, content) in enumerate(files_spec):
            if kind == "json":
                path = input_dir / f"pop_{idx}.json"
                path.write_text(json.dumps(content), encoding="utf-8")
            else:
                path = input_dir / f"pop_{idx}.csv"
                _write_csv(path, content)  # type: ignore[arg-type]

        records, leidos, procesados, descartados = process_folder(input_dir)

        # Invariante central de la Property 8.
        assert leidos == procesados + descartados, (
            f"Conservación violada: leidos={leidos} != "
            f"procesados={procesados} + descartados={descartados}"
        )

        # Invariantes de apoyo: conteos no negativos y coherencia con records.
        assert leidos >= 0 and procesados >= 0 and descartados >= 0
        assert len(records) == procesados
    finally:
        # Limpieza del ejemplo (no dejar carpetas temporales acumuladas).
        shutil.rmtree(input_dir, ignore_errors=True)
