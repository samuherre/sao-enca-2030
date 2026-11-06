"""Property test del pipeline Google Scholar (spec multi-source-bibliometria, tarea 3.4).

Property 8 del design.md — "Inmutabilidad de ``data/raw``":

    Para cualquier conjunto de archivos de entrada en
    ``data/raw/google_scholar/``, tras ejecutar el pipeline el contenido, el
    nombre y la mtime de esos archivos permanecen idénticos, y no se produce
    ninguna escritura dentro de ``data/raw/google_scholar/``.

    **Validates: Requirements 1.1**

Enfoque (Testing Strategy del design):
    - Se crea un directorio TEMPORAL que actúa como sustituto de la carpeta raw
      de entrada (NO se toca la carpeta real ``data/raw``).
    - Se puebla con archivos arbitrarios: ``.json`` / ``.csv`` (válidos y
      malformados) y algún ``.txt`` (extensión no soportada que el pipeline
      debe ignorar). Los datos son SINTÉTICOS.
    - Se toma una instantánea de ``(nombre, hash de contenido, mtime)`` de cada
      archivo de entrada.
    - Se ejecuta el pipeline sobre ese directorio temporal mientras se redirige
      la salida a un directorio ``processed`` temporal, monkeypatcheando el
      atributo de módulo ``OUTPUT_DIR`` para que nada se escriba en la carpeta
      ``processed`` real.
    - Tras ejecutar, se verifica que ``(nombre, hash, mtime)`` de cada archivo
      de entrada no cambió y que NO se creó ningún archivo nuevo dentro del
      directorio de entrada (la carpeta raw es de solo lectura).

Nota: la propiedad ejerce la ruta de LECTURA del pipeline (``process_folder``,
que recorre el directorio, invoca el conector, valida período y marca
duplicados) y la ruta de ESCRITURA (``write_outputs`` vía ``OUTPUT_DIR``),
asegurando que ambas respetan la inmutabilidad del origen.
"""

from __future__ import annotations

import hashlib
import importlib
import sys
from pathlib import Path

# Permite importar el pipeline y el conector desde bibliometrics/ (mismo patrón
# que los demás tests de este paquete).
_REPO_ROOT = Path(__file__).resolve().parents[2]
_BIBLIO = _REPO_ROOT / "bibliometrics"
if str(_BIBLIO) not in sys.path:
    sys.path.insert(0, str(_BIBLIO))

import pytest  # noqa: E402
from hypothesis import HealthCheck, given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

# Se importa el MÓDULO (no solo la función) para poder monkeypatchear su
# atributo OUTPUT_DIR y redirigir la escritura a un directorio temporal.
process_google_scholar = importlib.import_module(
    "pipelines.process_google_scholar"
)


def _file_fingerprint(path: Path) -> tuple[str, str, int]:
    """Instantánea ``(nombre, hash SHA-256 del contenido, mtime_ns)`` del archivo."""
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    mtime_ns = path.stat().st_mtime_ns
    return (path.name, digest, mtime_ns)


# --- Estrategias de contenido sintético para los archivos de entrada ---------

# Un valor JSON plausible de un Export_PoP: lista de objetos-registro con un
# subconjunto de claves. Se incluyen valores no-objeto para forzar registros
# malformados que el pipeline debe descartar (sin tocar el archivo de origen).
_json_scalar = st.one_of(
    st.text(max_size=20),
    st.integers(min_value=1900, max_value=2100).map(str),
    st.none(),
)
_json_record = st.dictionaries(
    keys=st.sampled_from(["title", "authors", "year", "doi", "source"]),
    values=_json_scalar,
    max_size=5,
)
# Mezcla de objetos-registro y elementos malformados (no-objeto).
_json_payload = st.lists(
    st.one_of(_json_record, st.text(max_size=10), st.integers()),
    max_size=6,
)

# Contenido CSV arbitrario (cabecera + filas); puede estar bien o mal formado.
_csv_payload = st.text(
    alphabet=st.characters(blacklist_categories=("Cs",)),
    max_size=60,
)

# Contenido .txt / JSON crudo arbitrario (incluye JSON potencialmente inválido).
_raw_text = st.text(
    alphabet=st.characters(blacklist_categories=("Cs",)),
    max_size=60,
)


@st.composite
def input_files(draw: st.DrawFn) -> list[tuple[str, str]]:
    """Genera una lista de ``(nombre_archivo, contenido)`` arbitrarios.

    Incluye combinaciones de ``.json`` (válido/ inválido), ``.csv`` (válido/
    malformado) y ``.txt`` (extensión no soportada). Los nombres son únicos.
    Puede generar una lista vacía (carpeta de entrada sin archivos relevantes).
    """
    import json as _json

    n = draw(st.integers(min_value=0, max_value=5))
    files: list[tuple[str, str]] = []
    used_names: set[str] = set()
    for i in draw(st.permutations(range(n))) if n else []:
        kind = draw(st.sampled_from(["json_valid", "json_raw", "csv", "txt"]))
        if kind == "json_valid":
            payload = draw(_json_payload)
            content = _json.dumps(payload, ensure_ascii=False)
            ext = ".json"
        elif kind == "json_raw":
            content = draw(_raw_text)
            ext = ".json"
        elif kind == "csv":
            content = draw(_csv_payload)
            ext = ".csv"
        else:
            content = draw(_raw_text)
            ext = ".txt"

        # Alterna el casing de la extensión para ejercer el descubrimiento
        # case-insensitive sin crear colisiones de nombre.
        if draw(st.booleans()):
            ext = ext.upper()

        name = f"export_{i}{ext}"
        if name in used_names:
            continue
        used_names.add(name)
        files.append((name, content))
    return files


# Feature: multi-source-bibliometria, Property 8: Inmutabilidad de data/raw
# deadline=None: cada ejemplo realiza E/S de disco real (crear archivos,
# recorrer la carpeta, leer y hashear); el tiempo por ejemplo es variable en
# distintos sistemas de archivos y no debe hacer fallar la propiedad.
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(files=input_files())
def test_inmutabilidad_de_data_raw(
    files: list[tuple[str, str]], tmp_path_factory: pytest.TempPathFactory
) -> None:
    """El pipeline no modifica ni escribe dentro de la carpeta de entrada.

    Validates: Requirements 1.1
    """
    # Directorios temporales independientes por ejemplo: uno hace de "raw" de
    # entrada y otro de "processed" de salida. La carpeta real data/raw nunca
    # se toca.
    base = tmp_path_factory.mktemp("raw_inmutable")
    input_dir = base / "raw_input"
    output_dir = base / "processed_out"
    input_dir.mkdir()

    # Poblar la carpeta de entrada con los archivos sintéticos.
    for name, content in files:
        (input_dir / name).write_text(content, encoding="utf-8")

    # Instantánea previa: nombre + hash + mtime de cada archivo de entrada.
    before: dict[str, tuple[str, str, int]] = {
        p.name: _file_fingerprint(p)
        for p in input_dir.iterdir()
        if p.is_file()
    }
    names_before = set(before.keys())

    # Redirigir TODA escritura de salida a un directorio temporal: nada debe
    # escribirse en la carpeta processed real (ni en la de entrada).
    original_output = process_google_scholar.OUTPUT_DIR
    process_google_scholar.OUTPUT_DIR = output_dir
    try:
        # Ejecutar la ruta de LECTURA del pipeline sobre la carpeta de entrada.
        records, leidos, procesados, descartados = (
            process_google_scholar.process_folder(input_dir)
        )
        # Ejercer también la ruta de ESCRITURA cuando haya registros, para
        # confirmar que las salidas van al OUTPUT_DIR temporal y no al input.
        if records:
            from pipelines._common import write_outputs

            write_outputs(
                records, process_google_scholar.OUTPUT_DIR, "google_scholar_dataset"
            )
    finally:
        process_google_scholar.OUTPUT_DIR = original_output

    # --- Aserciones de inmutabilidad -----------------------------------------
    after: dict[str, tuple[str, str, int]] = {
        p.name: _file_fingerprint(p)
        for p in input_dir.iterdir()
        if p.is_file()
    }
    names_after = set(after.keys())

    # No se creó ningún archivo nuevo dentro de la carpeta de entrada...
    nuevos = names_after - names_before
    assert not nuevos, (
        f"El pipeline creó archivos dentro de la carpeta de entrada "
        f"(raw debe ser inmutable): {sorted(nuevos)}"
    )
    # ...ni se eliminó ninguno.
    eliminados = names_before - names_after
    assert not eliminados, (
        f"El pipeline eliminó archivos de la carpeta de entrada: {sorted(eliminados)}"
    )

    # El nombre, contenido (hash) y mtime de cada archivo permanecen idénticos.
    for name, fingerprint in before.items():
        assert after[name] == fingerprint, (
            f"El archivo de entrada '{name}' cambió tras ejecutar el pipeline "
            f"(nombre/contenido/mtime): antes={fingerprint!r} después={after[name]!r}"
        )

    # Si se escribió algo, debió ir al OUTPUT_DIR temporal, nunca al input.
    if output_dir.exists():
        assert input_dir not in output_dir.parents, (
            "La salida no debe anidarse dentro de la carpeta de entrada."
        )
