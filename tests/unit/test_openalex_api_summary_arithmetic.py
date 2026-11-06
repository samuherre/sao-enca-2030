"""Property test del Pipeline_OpenAlex_API (spec fuente-openalex-api, tarea 4.4).

Property 12 del design.md — "Conservación aritmética del resumen":

    Para toda corrida del pipeline, el resumen cumple que el número de registros
    procesados es igual a los works recuperados que pudieron transformarse, y el
    resumen informa de forma consistente los works recuperados, las páginas
    consultadas y los errores encontrados.

    **Validates: Requirements 2.5, 6.2**

Enfoque (Testing Strategy del design): se ejecuta ``run_pipeline`` con una
SESIÓN HTTP INYECTADA y simulada (sin red real), que sirve mezclas —generadas
por hypothesis— de works VÁLIDOS (dicts) y works MALFORMADOS (entradas que NO
son dict) repartidos en 1..N Consultas y en páginas variadas, encadenadas por
cursor como la API real de OpenAlex (arranca en ``cursor="*"`` y entrega
``meta.next_cursor``/``None`` al final).

Los works son SINTÉTICOS (``DEMO_DATA``, datos de prueba, no reales) y nunca se
presentan como resultados reales. Se fija ``pace_seconds=0`` para no dormir
realmente entre páginas y se escribe en un ``out_dir`` temporal que se limpia.

Invariante exacta (leída de ``process_openalex_api.py`` y ``_common.py``):

  - ``run_pipeline`` devuelve ``(records, stats, json_path, csv_path)`` con
    ``stats`` un ``_IngestStats`` (``works_recuperados``, ``paginas_consultadas``,
    ``errores``, ``paginas_con_error``).
  - ``works_recuperados`` = total de works CRUDOS servidos por las páginas
    exitosas, sumado sobre todas las Consultas.
  - ``_transformar_works`` DESCARTA (y cuenta como error) exactamente las
    entradas que NO son dict (o los dicts cuya transformación lanza; aquí no se
    generan porque ``work_to_record`` es robusto). ``mark_duplicates`` solo
    anota, NO elimina registros.
  - Por tanto: ``len(records) == works_recuperados - descartes``, donde
    ``descartes`` = número de entradas malformadas (no-dict) servidas.
  - En esta corrida NO hay errores de página (todas las respuestas son 200), de
    modo que ``stats.errores`` cuenta ÚNICAMENTE los descartes de works
    malformados: ``stats.errores == descartes``.

Qué verifica, variando número de Consultas, works por Consulta, proporción de
malformados y ``per_page``:

  1. ``len(records) == stats.works_recuperados - descartes`` (conservación
     aritmética: procesados = recuperados transformables).
  2. ``stats.errores == descartes`` (sin errores de página, los únicos errores
     son descartes de works malformados).
  3. ``stats.works_recuperados`` == total de entradas servidas en páginas
     exitosas (válidas + malformadas), sumado sobre todas las Consultas.
  4. Contadores no negativos y coherentes:
     ``works_recuperados >= 0``, ``paginas_consultadas >= 0``,
     ``errores >= 0``, ``len(records) >= 0`` y ``len(records) <=
     works_recuperados``.
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Optional

# Permite importar el conector y el pipeline desde bibliometrics/ (mismo patrón
# que los demás tests de este paquete).
_REPO_ROOT = Path(__file__).resolve().parents[2]
_BIBLIO = _REPO_ROOT / "bibliometrics"
if str(_BIBLIO) not in sys.path:
    sys.path.insert(0, str(_BIBLIO))

from hypothesis import given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

from ingestion.openalex_api_client import ApiConfig, Consulta  # noqa: E402
from pipelines.process_openalex_api import run_pipeline  # noqa: E402


class _FakeResponse:
    """Respuesta HTTP falsa mínima: expone ``status_code`` y ``.json()``.

    Siempre 200 (esta propiedad valida corridas exitosas: la única fuente de
    "errores" son los works malformados que descarta la transformación).
    """

    def __init__(self, payload: dict[str, Any]) -> None:
        self.status_code = 200
        self._payload = payload

    def json(self) -> dict[str, Any]:
        return self._payload


class _FakeMultiConsultaSession:
    """Sesión HTTP falsa que sirve páginas por Consulta (identificada por término).

    Para cada término se particiona su lista de entradas (works válidos +
    malformados, en el orden generado) en páginas de tamaño ``per_page`` y se
    responde cada ``.get(...)`` según el ``cursor`` recibido en ``params``:

    - El pipeline arranca cada Consulta con ``cursor="*"`` → página 0.
    - Cada página n (salvo la última con contenido) devuelve
      ``meta.next_cursor = "c{n+1}"``; la última devuelve ``None`` para detener.

    No hay red: todo se resuelve en memoria. Las respuestas son SIEMPRE 200.
    """

    def __init__(self, entradas_por_termino: dict[str, list], per_page: int) -> None:
        self._per_page = per_page
        self._pages_por_termino: dict[str, list[list]] = {}
        for term, entradas in entradas_por_termino.items():
            paginas = [
                entradas[i : i + per_page]
                for i in range(0, len(entradas), per_page)
            ] or [[]]
            self._pages_por_termino[term] = paginas

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
        term = params.get("search", "")
        cursor = params.get("cursor", "*")
        paginas = self._pages_por_termino.get(term, [[]])
        idx = self._page_index_for_cursor(cursor)

        results = paginas[idx] if 0 <= idx < len(paginas) else []
        next_idx = idx + 1
        next_cursor = f"c{next_idx}" if next_idx < len(paginas) else None

        return _FakeResponse({"results": results, "meta": {"next_cursor": next_cursor}})


def _work_valido(n: int) -> dict:
    """Work sintético VÁLIDO (dict) — DEMO_DATA. ``work_to_record`` lo transforma.

    Se le da ``id``, ``title`` y ``publication_year`` en rango para que sea un
    dict transformable; el título incluye ``n`` para variar la clave de dedupe.
    """
    return {
        "id": f"https://openalex.org/W{n}",
        "title": f"DEMO_DATA work numero {n}",
        "publication_year": 2021,
        "authorships": [
            {"author": {"display_name": f"DEMO Autor {n}"}}
        ],
    }


# Entradas MALFORMADAS: NO son dict, por lo que _transformar_works las descarta
# y las cuenta como error (Req 3.4). Se usan tipos variados no-dict.
_MALFORMADOS: list = [None, "DEMO_DATA cadena suelta", 123, 3.14, ["lista"], True]


@st.composite
def _corrida(draw: st.DrawFn) -> tuple[dict[str, list], list[Consulta], int, int]:
    """Genera una corrida sintética (DEMO_DATA).

    Devuelve ``(entradas_por_termino, consultas, per_page, descartes_totales)``:

    - 1..3 Consultas, cada una con su término único.
    - Cada Consulta sirve una mezcla de works válidos (dicts) y malformados
      (no-dict), repartidos en varias páginas según ``per_page``.
    - ``descartes_totales`` = número de entradas malformadas sobre el conjunto.
    """
    num_consultas = draw(st.integers(min_value=1, max_value=3))
    per_page = draw(st.integers(min_value=1, max_value=5))

    entradas_por_termino: dict[str, list] = {}
    consultas: list[Consulta] = []
    descartes_totales = 0
    contador_valido = 0

    for c in range(num_consultas):
        term = f"DEMO_DATA consulta {c}"
        # Número de entradas de esta Consulta (0..8) y cuántas son malformadas.
        total_entradas = draw(st.integers(min_value=0, max_value=8))
        num_malformados = draw(st.integers(min_value=0, max_value=total_entradas))
        num_validos = total_entradas - num_malformados

        entradas: list = []
        for _ in range(num_validos):
            entradas.append(_work_valido(contador_valido))
            contador_valido += 1
        for _ in range(num_malformados):
            entradas.append(draw(st.sampled_from(_MALFORMADOS)))

        # Mezcla el orden de válidos y malformados dentro de la Consulta.
        entradas = draw(st.permutations(entradas))
        entradas = list(entradas)

        entradas_por_termino[term] = entradas
        consultas.append(Consulta(term=term, year_from=2020, year_to=2030))
        descartes_totales += num_malformados

    return entradas_por_termino, consultas, per_page, descartes_totales


# Feature: fuente-openalex-api, Property 12: Conservación aritmética del resumen
@settings(max_examples=150, deadline=None)
@given(data=_corrida())
def test_conservacion_aritmetica_del_resumen(
    data: tuple[dict[str, list], list[Consulta], int, int],
) -> None:
    """Procesados = recuperados transformables; contadores coherentes.

    Validates: Requirements 2.5, 6.2
    """
    entradas_por_termino, consultas, per_page, descartes = data

    # Total de entradas servidas en páginas exitosas (válidas + malformadas).
    total_servidas = sum(len(v) for v in entradas_por_termino.values())

    session = _FakeMultiConsultaSession(entradas_por_termino, per_page)
    config = ApiConfig(per_page=per_page, max_results=None, pace_seconds=0.0)

    out_dir = Path(tempfile.mkdtemp(prefix="demo_openalex_api_summary_"))
    try:
        records, stats, json_path, csv_path = run_pipeline(
            consultas, config, session=session, out_dir=out_dir
        )

        # (3) works_recuperados == total de entradas servidas (válidas + malformadas).
        assert stats.works_recuperados == total_servidas, (
            f"works_recuperados debe ser el total servido ({total_servidas}); "
            f"fue {stats.works_recuperados}"
        )

        # (1) Conservación aritmética: procesados = recuperados - descartes.
        assert len(records) == stats.works_recuperados - descartes, (
            f"len(records)={len(records)} debe ser works_recuperados"
            f"({stats.works_recuperados}) - descartes({descartes})"
        )

        # (2) Sin errores de página (todo 200): los únicos errores son descartes.
        assert stats.errores == descartes, (
            f"stats.errores={stats.errores} debe igualar los descartes "
            f"({descartes}); no hay errores de página en esta corrida"
        )
        assert stats.paginas_con_error == [], (
            "no debe haber páginas con error en una corrida 100% exitosa"
        )

        # (4) Contadores no negativos y coherentes.
        assert stats.works_recuperados >= 0
        assert stats.paginas_consultadas >= 0
        assert stats.errores >= 0
        assert len(records) >= 0
        assert len(records) <= stats.works_recuperados, (
            "los registros procesados nunca exceden los works recuperados"
        )
    finally:
        shutil.rmtree(out_dir, ignore_errors=True)
