"""Property test de la capa HTTP del Conector_OpenAlex_API (spec
fuente-openalex-api, tarea 2.2).

Property 7 del design.md — "Paginación recupera todos los resultados hasta el
límite":

    Para toda Consulta cuyos resultados abarquen varias páginas, ``iter_works``
    recupera todos los works siguiendo el cursor hasta agotarlo, o exactamente
    ``max_results`` works cuando hay un límite configurado (nunca más que el
    límite, nunca menos que el total cuando no hay límite).

    **Validates: Requirements 1.3**

Enfoque (Testing Strategy del design): la capa HTTP se prueba con el cliente
HTTP **simulado**; NINGÚN test golpea la red real. Se construye un objeto
``session`` falso cuyo método ``.get(url, params=..., timeout=...)`` devuelve una
respuesta falsa (con ``.status_code`` y ``.json()``) que sirve ``works``
sintéticos paginados por cursor, encadenando las páginas mediante
``meta.next_cursor`` (igual que la API real de OpenAlex, que arranca en
``cursor="*"`` y entrega ``next_cursor``/``None`` al final).

Los ``works`` generados por hypothesis son SINTÉTICOS (``DEMO_DATA``, datos de
prueba, no reales) y nunca se presentan como resultados reales. Se fija
``pace_seconds=0`` para no dormir realmente entre páginas durante los tests.

Qué verifica, para páginas encadenadas por cursor y variando número de páginas,
``per_page``, total de works y ``max_results`` (de ``None`` a valores por
debajo/por encima del total):

  1. Sin límite (``max_results=None``): ``iter_works`` entrega EXACTAMENTE todos
     los works del conjunto, en orden, agotando el cursor.
  2. Con límite: ``iter_works`` entrega EXACTAMENTE ``min(max_results, total)``
     works (nunca más que el límite, nunca menos que el total cuando el límite lo
     supera), y son el prefijo del conjunto completo.
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

from typing import Any, Optional  # noqa: E402

from hypothesis import given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

from ingestion.openalex_api_client import (  # noqa: E402
    ApiConfig,
    Consulta,
    iter_works,
)


class _FakeResponse:
    """Respuesta HTTP falsa mínima: expone ``status_code`` y ``.json()``.

    Imita la forma que ``fetch_page`` consume de una respuesta estilo
    ``requests`` sin tocar la red: ``status_code`` (siempre 200 aquí, porque esta
    propiedad valida la paginación exitosa) y un ``json()`` con ``results`` y
    ``meta.next_cursor``.
    """

    def __init__(self, payload: dict[str, Any]) -> None:
        self.status_code = 200
        self._payload = payload

    def json(self) -> dict[str, Any]:
        return self._payload


class _FakePagedSession:
    """Sesión HTTP falsa que sirve ``works`` sintéticos paginados por cursor.

    Divide ``works`` en páginas de tamaño ``per_page`` y responde cada
    ``.get(...)`` según el ``cursor`` recibido en ``params``:

    - El cliente arranca con ``cursor="*"`` → se sirve la página 0.
    - Cada página n (salvo la última con contenido) devuelve
      ``meta.next_cursor = "c{n+1}"`` para encadenar; la última devuelve
      ``next_cursor = None`` para detener la paginación.

    No hay red: todo se resuelve en memoria. Registra el número de llamadas para
    poder razonar sobre el recorrido si hiciera falta.
    """

    def __init__(self, works: list[dict], per_page: int) -> None:
        self._per_page = per_page
        # Particiona en páginas de a ``per_page``; lista vacía => una página vacía
        # (cursor "*" devuelve resultados vacíos y next_cursor None).
        self._pages: list[list[dict]] = [
            works[i : i + per_page] for i in range(0, len(works), per_page)
        ] or [[]]
        self.calls = 0

    def _page_index_for_cursor(self, cursor: str) -> int:
        # "*" es el inicio (página 0); "c{n}" apunta a la página n.
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
        self.calls += 1
        params = params or {}
        cursor = params.get("cursor", "*")
        idx = self._page_index_for_cursor(cursor)

        results = self._pages[idx] if 0 <= idx < len(self._pages) else []
        # next_cursor apunta a la siguiente página con contenido; None si no hay.
        next_idx = idx + 1
        next_cursor = f"c{next_idx}" if next_idx < len(self._pages) else None

        return _FakeResponse({"results": results, "meta": {"next_cursor": next_cursor}})


@st.composite
def _works_and_config(draw: st.DrawFn) -> tuple[list[dict], int, Optional[int]]:
    """Genera ``(works, per_page, max_results)`` sintéticos (DEMO_DATA).

    - ``works``: lista de works sintéticos con ``id`` único y secuencial para
      poder verificar identidad y orden del recorrido. El total varía de 0 a 25.
    - ``per_page``: entre 1 y 10 (<=200, el máximo de OpenAlex), para forzar que
      los conjuntos abarquen VARIAS páginas.
    - ``max_results``: ``None`` (sin límite) o un entero que puede quedar por
      debajo, igual o por encima del total, para ejercer los tres casos.
    """
    total = draw(st.integers(min_value=0, max_value=25))
    # DEMO_DATA: works sintéticos, no reales. ``id`` secuencial estable.
    works = [
        {"id": f"https://openalex.org/W{n}", "display_name": f"DEMO_DATA work {n}"}
        for n in range(total)
    ]
    per_page = draw(st.integers(min_value=1, max_value=10))

    # max_results: None, o un valor que cruce por debajo/igual/encima del total.
    upper = max(total + 3, 3)
    max_results = draw(st.one_of(st.none(), st.integers(min_value=0, max_value=upper)))
    return works, per_page, max_results


# Feature: fuente-openalex-api, Property 7: Paginación recupera todos los resultados hasta el límite
@settings(max_examples=200)
@given(data=_works_and_config())
def test_paginacion_recupera_todos_hasta_el_limite(
    data: tuple[list[dict], int, Optional[int]],
) -> None:
    """``iter_works`` agota el cursor o se detiene exactamente en el límite.

    Validates: Requirements 1.3
    """
    works, per_page, max_results = data

    session = _FakePagedSession(works, per_page)
    consulta = Consulta(term="DEMO_DATA aves", year_from=2020, year_to=2030)
    # pace_seconds=0 evita dormir de verdad entre páginas durante el test.
    config = ApiConfig(per_page=per_page, max_results=max_results, pace_seconds=0.0)

    recovered = list(iter_works(session, consulta, config))

    total = len(works)
    if max_results is None:
        # (1) Sin límite: se recuperan EXACTAMENTE todos los works del conjunto.
        esperado = total
    else:
        # (2) Con límite: exactamente min(max_results, total) — nunca más que el
        # límite, nunca menos que el total cuando el límite lo supera.
        esperado = min(max_results, total)

    assert len(recovered) == esperado, (
        f"iter_works debe recuperar {esperado} works "
        f"(total={total}, per_page={per_page}, max_results={max_results}); "
        f"recuperó {len(recovered)}"
    )

    # Nunca excede el límite configurado.
    if max_results is not None:
        assert len(recovered) <= max_results

    # Los works recuperados son el PREFIJO del conjunto completo, en orden de
    # paginación por cursor (identidad por ``id`` secuencial).
    ids_recuperados = [w["id"] for w in recovered]
    ids_esperados = [w["id"] for w in works[:esperado]]
    assert ids_recuperados == ids_esperados, (
        "los works recuperados deben ser el prefijo del conjunto en orden de cursor"
    )
