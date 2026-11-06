"""Property test del Pipeline_OpenAlex_API (spec fuente-openalex-api, tarea 4.2).

Property 9 del design.md — "Deduplicación básica sobre el conjunto combinado":

    Para todo dataset resultante de una o varias ``Consulta``s, dos registros
    con el mismo título normalizado hacen que el segundo quede marcado
    ``is_duplicate = true`` con ``duplicate_of`` apuntando al primero, sin
    eliminar ningún registro, aplicado sobre el conjunto COMBINADO de todas las
    ``Consulta``s.

    **Validates: Requirements 5.1, 5.2**

Enfoque (Testing Strategy del design): se ejercita ``run_pipeline`` del pipeline
``process_openalex_api.py`` con una ``session`` HTTP **inyectada y falsa** (sin
red real) que sirve ``works`` sintéticos (``DEMO_DATA``) repartidos en una o
VARIAS ``Consulta``s. Esto cubre explícitamente el aspecto del "conjunto
combinado" (Req 5.2): la deduplicación se aplica sobre la unión de los
resultados de todas las ``Consulta``s, no por ``Consulta`` aislada.

Algunos títulos se repiten a propósito (incluso ENTRE ``Consulta``s distintas)
para forzar duplicados cruzados. Se usa el MISMO año para los works que comparten
título, de modo que son genuinamente el mismo trabajo y comparten ``article_id``
(esquema ``oa-`` por título+año cuando no hay DOI), coherente con la dedupe por
título normalizado de ``_common.mark_duplicates``.

Qué verifica sobre el dataset combinado producido por el pipeline:

  1. No se elimina ningún registro: el número de registros procesados es igual al
     número de works servidos por todas las ``Consulta``s (ninguno válido se
     descarta; todos los works sintéticos son transformables).
  2. Para cada grupo de registros con el mismo título normalizado (en el orden en
     que el pipeline los combina), EXACTAMENTE la PRIMERA ocurrencia NO es
     duplicado y cada ocurrencia posterior tiene ``is_duplicate == True`` con
     ``duplicate_of`` apuntando al ``article_id`` de la primera.

Se escribe en un ``out_dir`` TEMPORAL y se limpia (nunca en el
``data/processed/`` real); ``pace_seconds=0`` para no dormir entre páginas.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

# Permite importar el conector y el pipeline desde bibliometrics/ (mismo patrón
# que los demás tests de este paquete).
_REPO_ROOT = Path(__file__).resolve().parents[2]
_BIBLIO = _REPO_ROOT / "bibliometrics"
if str(_BIBLIO) not in sys.path:
    sys.path.insert(0, str(_BIBLIO))

from typing import Any, Optional  # noqa: E402

from hypothesis import given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

from ingestion.openalex_api_client import ApiConfig, Consulta  # noqa: E402
from pipelines._common import norm_title  # noqa: E402
from pipelines.process_openalex_api import run_pipeline  # noqa: E402


class _FakeResponse:
    """Respuesta HTTP falsa mínima: expone ``status_code`` y ``.json()``."""

    def __init__(self, payload: dict[str, Any]) -> None:
        self.status_code = 200
        self._payload = payload

    def json(self) -> dict[str, Any]:
        return self._payload


class _FakeMultiConsultaSession:
    """Sesión HTTP falsa que sirve works por ``Consulta`` paginados por cursor.

    La petición incluye ``params["search"]`` (el término de la ``Consulta``) y un
    ``cursor``. La sesión busca los works asignados a ese término y los sirve en
    páginas de ``per_page``, encadenando ``meta.next_cursor`` como la API real:
    arranca en ``cursor="*"`` y entrega ``next_cursor``/``None`` al final.

    Todo en memoria; NINGÚN test golpea la red real.
    """

    def __init__(self, works_por_termino: dict[str, list[dict]], per_page: int) -> None:
        self._per_page = per_page
        self._paginas_por_termino: dict[str, list[list[dict]]] = {}
        for term, works in works_por_termino.items():
            paginas = [
                works[i : i + per_page] for i in range(0, len(works), per_page)
            ] or [[]]
            self._paginas_por_termino[term] = paginas

    def _idx_de_cursor(self, cursor: str) -> int:
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
        paginas = self._paginas_por_termino.get(term, [[]])
        idx = self._idx_de_cursor(cursor)

        results = paginas[idx] if 0 <= idx < len(paginas) else []
        next_idx = idx + 1
        next_cursor = f"c{next_idx}" if next_idx < len(paginas) else None

        return _FakeResponse({"results": results, "meta": {"next_cursor": next_cursor}})


@st.composite
def _consultas_y_works(draw: st.DrawFn):
    """Genera ``(works_por_termino, orden_terminos, per_page)`` (DEMO_DATA).

    - Se arma un pequeño "catálogo" de títulos, algunos destinados a repetirse.
    - Se reparten works entre 1..N ``Consulta``s (términos distintos), con años
      fijos por título para que un mismo título sea el mismo trabajo.
    - Al menos un título se repite ENTRE ``Consulta``s distintas cuando hay más
      de una, para ejercer la dedupe sobre el conjunto COMBINADO (Req 5.2).
    """
    num_consultas = draw(st.integers(min_value=1, max_value=3))
    terminos = [f"DEMO_DATA termino {i}" for i in range(num_consultas)]

    # Catálogo de títulos base; algunos se reutilizan para forzar duplicados.
    # Año fijo por título (mismo título => mismo trabajo => mismo article_id).
    num_titulos = draw(st.integers(min_value=1, max_value=5))
    catalogo = [
        {"title": f"DEMO_DATA Bird Study {t}", "year": 2020 + (t % 11)}
        for t in range(num_titulos)
    ]

    # Para cada Consulta, elegir cuántos works sirve y qué títulos (con repetición
    # permitida dentro y entre Consultas).
    works_por_termino: dict[str, list[dict]] = {}
    contador = 0
    for term in terminos:
        n = draw(st.integers(min_value=0, max_value=4))
        works: list[dict] = []
        for _ in range(n):
            elegido = draw(st.sampled_from(catalogo))
            # Work sintético mínimo: título + autores + año (obligatorios OK) para
            # que todos sean transformables (ninguno se descarta). Sin DOI → el
            # article_id depende de norm_title(title)+año.
            works.append(
                {
                    "id": f"https://openalex.org/W{contador}",
                    "title": elegido["title"],
                    "authorships": [
                        {"author": {"display_name": "DEMO_DATA Autor"}}
                    ],
                    "publication_year": elegido["year"],
                }
            )
            contador += 1
        works_por_termino[term] = works

    per_page = draw(st.integers(min_value=1, max_value=4))
    return works_por_termino, terminos, per_page


# Feature: fuente-openalex-api, Property 9: Deduplicación básica sobre el conjunto combinado
@settings(max_examples=150, deadline=None)
@given(data=_consultas_y_works())
def test_dedupe_sobre_conjunto_combinado(data) -> None:
    """La dedupe por título normalizado se aplica sobre el conjunto COMBINADO.

    Validates: Requirements 5.1, 5.2
    """
    works_por_termino, terminos, per_page = data

    consultas = [
        Consulta(term=term, year_from=2015, year_to=2030) for term in terminos
    ]
    config = ApiConfig(per_page=per_page, pace_seconds=0.0)
    session = _FakeMultiConsultaSession(works_por_termino, per_page)

    total_servidos = sum(len(ws) for ws in works_por_termino.values())

    with tempfile.TemporaryDirectory() as tmp:
        out_dir = Path(tmp) / "openalex"
        records, _stats, json_path, csv_path = run_pipeline(
            consultas, config, session=session, out_dir=out_dir
        )

        # (1) No se elimina ningún registro: se conservan todos los works servidos.
        assert len(records) == total_servidos, (
            f"la dedupe NO debe eliminar registros: servidos={total_servidos}, "
            f"procesados={len(records)}"
        )

        # Si hubo registros, el pipeline escribió en el out_dir TEMPORAL (nunca en
        # el data/processed real).
        if records:
            assert json_path is not None and csv_path is not None
            assert out_dir in json_path.parents
            assert out_dir in csv_path.parents

    # (2) Por cada grupo con el mismo título normalizado, en el orden combinado:
    # la PRIMERA ocurrencia no es duplicado; las siguientes son is_duplicate con
    # duplicate_of apuntando al article_id de la primera.
    primero_por_clave: dict[str, Any] = {}
    for rec in records:
        clave = norm_title(rec.title)
        if not clave:
            # Título vacío/ausente no participa en la dedupe por título.
            assert rec.is_duplicate is False
            assert rec.duplicate_of is None
            continue
        if clave not in primero_por_clave:
            # Primera ocurrencia del título normalizado: NO es duplicado.
            primero_por_clave[clave] = rec
            assert rec.is_duplicate is False, (
                f"la primera ocurrencia del título '{rec.title}' no debe marcarse "
                f"como duplicado"
            )
            assert rec.duplicate_of is None
        else:
            # Ocurrencia posterior: duplicado del primero (apunta a su article_id).
            primero = primero_por_clave[clave]
            assert rec.is_duplicate is True, (
                f"la ocurrencia posterior del título '{rec.title}' debe marcarse "
                f"como duplicado"
            )
            assert rec.duplicate_of == primero.article_id, (
                f"duplicate_of debe apuntar al primero ({primero.article_id}); "
                f"fue {rec.duplicate_of}"
            )
