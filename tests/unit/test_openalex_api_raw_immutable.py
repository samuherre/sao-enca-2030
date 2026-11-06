"""Property test del pipeline OpenAlex por API (spec fuente-openalex-api,
tarea 4.3).

Property 11 del design.md — "Inmutabilidad de ``data/raw/``":

    Para toda ejecución del pipeline, ninguna escritura ocurre dentro de
    ``data/raw/``; el pipeline solo escribe en ``data/processed/openalex/``.

    **Validates: Requirements 6.4**

Enfoque (Testing Strategy del design):
    - El pipeline por API (``process_openalex_api.run_pipeline``) NO lee de
      ``data/raw/``: su entrada son las ``Consulta``s y una ``session`` HTTP. El
      módulo expone una constante ``_RAW_DIR`` (la carpeta inmutable) y
      ``OUTPUT_DIR`` (la salida en ``data/processed/openalex/``). Esta propiedad
      verifica que correr el pipeline NO toca ``_RAW_DIR`` y que todo lo que se
      escribe cae dentro del ``out_dir`` temporal.
    - Se crea un directorio TEMPORAL que hace de ``data/raw/`` sustituto (la
      carpeta real nunca se toca) y se puebla con archivos fixtura arbitrarios
      (``.pdf``/``.json``/``.csv``/``.txt``) con contenido SINTÉTICO.
    - Se monkeypatchea ``process_openalex_api._RAW_DIR`` para que apunte a ese
      directorio temporal, y se toma una instantánea recursiva
      ``(ruta_relativa, hash SHA-256, mtime_ns)`` de todo su contenido ANTES.
    - Se ejecuta ``run_pipeline`` con una ``session`` HTTP **falsa** (sin red
      real) que sirve ``works`` sintéticos generados por hypothesis, escribiendo
      en un ``out_dir`` temporal (NO en ``data/processed`` real) y con
      ``pace_seconds=0`` para no dormir.
    - Tras correr, se verifica que la instantánea recursiva del ``_RAW_DIR``
      temporal es IDÉNTICA (ningún archivo nuevo, eliminado ni modificado) y que
      las salidas del pipeline cayeron únicamente dentro del ``out_dir`` temporal
      y nunca dentro del ``_RAW_DIR``.

Los ``works`` generados son SINTÉTICOS (``DEMO_DATA``, datos de prueba) y nunca
se presentan como resultados reales.
"""

from __future__ import annotations

import hashlib
import importlib
import sys
from pathlib import Path
from typing import Any, Optional

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
# atributo _RAW_DIR y apuntarlo a un directorio temporal.
process_openalex_api = importlib.import_module("pipelines.process_openalex_api")

from ingestion.openalex_api_client import ApiConfig, Consulta  # noqa: E402


# ---------------------------------------------------------------------------
# Sesión HTTP falsa (sin red real)
# ---------------------------------------------------------------------------
class _FakeResponse:
    """Respuesta HTTP falsa mínima: expone ``status_code`` y ``.json()``."""

    def __init__(self, payload: dict[str, Any]) -> None:
        self.status_code = 200
        self._payload = payload

    def json(self) -> dict[str, Any]:
        return self._payload


class _FakePagedSession:
    """Sesión HTTP falsa que sirve ``works`` sintéticos paginados por cursor.

    Replica el patrón de los demás tests de la capa HTTP: parte de ``cursor="*"``
    y encadena páginas vía ``meta.next_cursor`` hasta agotar el conjunto. Todo se
    resuelve en memoria; nunca golpea la red.
    """

    def __init__(self, works: list[dict], per_page: int) -> None:
        self._pages: list[list[dict]] = [
            works[i : i + per_page] for i in range(0, len(works), per_page)
        ] or [[]]

    def _page_index_for_cursor(self, cursor: str) -> int:
        if cursor == "*":
            return 0
        if cursor.startswith("c"):
            return int(cursor[1:])
        raise AssertionError(f"cursor inesperado en test: {cursor!r}")

    def get(
        self,
        url: str,
        params: Optional[dict[str, Any]] = None,
        timeout: Optional[int] = None,
    ) -> _FakeResponse:
        params = params or {}
        cursor = params.get("cursor", "*")
        idx = self._page_index_for_cursor(cursor)
        results = self._pages[idx] if 0 <= idx < len(self._pages) else []
        next_idx = idx + 1
        next_cursor = f"c{next_idx}" if next_idx < len(self._pages) else None
        return _FakeResponse({"results": results, "meta": {"next_cursor": next_cursor}})


# ---------------------------------------------------------------------------
# Generadores de datos sintéticos (DEMO_DATA)
# ---------------------------------------------------------------------------
@st.composite
def _works(draw: st.DrawFn) -> list[dict]:
    """Genera una lista de ``work``s sintéticos nativos de OpenAlex (DEMO_DATA).

    Incluye works bien formados (título, autores, año, abstract invertido) y
    works malformados (sin obligatorios, no-dict) para ejercer tanto la ruta de
    transformación como la de descarte robusto, todo sin tocar ``data/raw/``.
    """
    n = draw(st.integers(min_value=0, max_value=8))
    works: list[dict] = []
    for i in range(n):
        kind = draw(st.sampled_from(["full", "no_authors", "no_year", "malformed"]))
        if kind == "malformed":
            # Entrada no-dict: el pipeline debe descartarla sin abortar.
            works.append(draw(st.one_of(st.text(max_size=8), st.integers(), st.none())))
            continue
        work: dict[str, Any] = {
            "id": f"https://openalex.org/W{i}",
            "display_name": f"DEMO_DATA work {i}",
            "title": f"DEMO_DATA work {i}",
        }
        if kind != "no_authors":
            work["authorships"] = [
                {"author": {"display_name": f"DEMO Author {i}"}}
            ]
        if kind != "no_year":
            work["publication_year"] = draw(st.integers(min_value=2018, max_value=2031))
        if draw(st.booleans()):
            work["abstract_inverted_index"] = {"DEMO": [0], "abstract": [1]}
        if draw(st.booleans()):
            work["doi"] = f"https://doi.org/10.1234/demo.{i}"
        works.append(work)
    return works


# Archivos fixtura que pueblan el ``data/raw/`` temporal; contenido sintético.
@st.composite
def _raw_fixture_files(draw: st.DrawFn) -> list[tuple[str, bytes]]:
    """Genera ``(ruta_relativa, contenido_bytes)`` para poblar el raw temporal.

    Simula PDFs originales y otros artefactos inmutables, incluyendo algún
    archivo anidado en una subcarpeta (p. ej. ``boletin_sao/...``).
    """
    n = draw(st.integers(min_value=0, max_value=5))
    files: list[tuple[str, bytes]] = []
    used: set[str] = set()
    for i in range(n):
        ext = draw(st.sampled_from([".pdf", ".json", ".csv", ".txt"]))
        subdir = draw(st.sampled_from(["", "boletin_sao/", "openalex/"]))
        name = f"{subdir}fixture_{i}{ext}"
        if name in used:
            continue
        used.add(name)
        content = draw(st.binary(min_size=0, max_size=48))
        files.append((name, content))
    return files


def _snapshot(root: Path) -> dict[str, tuple[str, int]]:
    """Instantánea recursiva ``{ruta_relativa: (hash SHA-256, mtime_ns)}``."""
    snap: dict[str, tuple[str, int]] = {}
    for p in sorted(root.rglob("*")):
        if p.is_file():
            data = p.read_bytes()
            rel = p.relative_to(root).as_posix()
            snap[rel] = (hashlib.sha256(data).hexdigest(), p.stat().st_mtime_ns)
    return snap


# Feature: fuente-openalex-api, Property 11: Inmutabilidad de data/raw/
# deadline=None: cada ejemplo hace E/S de disco real (crear fixtures, recorrer,
# hashear, escribir salidas); el tiempo por ejemplo varía por sistema de archivos
# y no debe hacer fallar la propiedad.
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(works=_works(), raw_files=_raw_fixture_files())
def test_inmutabilidad_de_data_raw(
    works: list[dict],
    raw_files: list[tuple[str, bytes]],
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    """Correr el pipeline por API no escribe ni modifica nada en ``data/raw/``.

    Validates: Requirements 6.4
    """
    base = tmp_path_factory.mktemp("raw_inmutable_openalex_api")
    raw_dir = base / "raw"
    out_dir = base / "processed_out"
    raw_dir.mkdir()

    # Poblar el data/raw temporal con los archivos fixtura sintéticos.
    for rel, content in raw_files:
        dest = raw_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)

    # Instantánea recursiva del raw ANTES de correr el pipeline.
    before = _snapshot(raw_dir)

    session = _FakePagedSession(works, per_page=3)
    consultas = [Consulta(term="DEMO_DATA aves", year_from=2020, year_to=2030)]
    config = ApiConfig(per_page=3, max_results=None, pace_seconds=0.0)

    # Monkeypatchear la carpeta inmutable del módulo para que apunte al raw
    # temporal; ejecutar escribiendo SOLO en el out_dir temporal.
    original_raw = process_openalex_api._RAW_DIR
    process_openalex_api._RAW_DIR = raw_dir
    try:
        records, stats, json_path, csv_path = process_openalex_api.run_pipeline(
            consultas, config, session=session, out_dir=out_dir
        )
    finally:
        process_openalex_api._RAW_DIR = original_raw

    # --- Aserciones de inmutabilidad del raw ---------------------------------
    after = _snapshot(raw_dir)

    nuevos = set(after) - set(before)
    assert not nuevos, (
        f"El pipeline creó archivos dentro de data/raw/ (debe ser inmutable): "
        f"{sorted(nuevos)}"
    )
    eliminados = set(before) - set(after)
    assert not eliminados, (
        f"El pipeline eliminó archivos de data/raw/: {sorted(eliminados)}"
    )
    for rel, fingerprint in before.items():
        assert after[rel] == fingerprint, (
            f"El archivo '{rel}' bajo data/raw/ cambió tras correr el pipeline "
            f"(contenido/mtime): antes={fingerprint!r} después={after[rel]!r}"
        )

    # --- Las salidas caen SOLO dentro del out_dir temporal, nunca en raw -----
    for path in (json_path, csv_path):
        if path is None:
            continue
        resolved = Path(path).resolve()
        # Debe estar dentro del out_dir temporal...
        assert resolved.is_relative_to(out_dir.resolve()), (
            f"La salida {resolved} debe escribirse dentro del out_dir temporal "
            f"{out_dir}."
        )
        # ...y jamás dentro del data/raw temporal.
        assert not resolved.is_relative_to(raw_dir.resolve()), (
            f"La salida {resolved} NO debe escribirse dentro de data/raw/."
        )

    # Si se produjeron registros, debió escribirse el dataset en el out_dir.
    if records:
        assert json_path is not None and csv_path is not None
        assert Path(json_path).exists() and Path(csv_path).exists()
