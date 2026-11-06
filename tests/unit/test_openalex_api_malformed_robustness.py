"""Property test del Pipeline_OpenAlex_API (spec fuente-openalex-api, tarea 4.5).

Property 13 del design.md — "Robustez ante works malformados":

    Para toda mezcla de works válidos y malformados recuperados de la API, la
    transformación produce registros para los válidos, descarta de forma robusta
    los malformados y NO aborta la corrida.

    **Validates: Requirements 2.3, 3.4**

Enfoque (Testing Strategy del design): se inyecta una SESIÓN HTTP FALSA en
``run_pipeline`` (``bibliometrics/pipelines/process_openalex_api.py``); NINGÚN
test golpea la red real. La sesión falsa sirve, paginada por cursor (igual que la
API real: arranca en ``cursor="*"`` y encadena con ``meta.next_cursor``), una
MEZCLA generada por hypothesis de:

  - works VÁLIDOS: ``dict`` con campos utilizables (``id``/``title``/``authors``/
    ``publication_year``). Un dict válido SIEMPRE se transforma con éxito a un
    ``ArticleRecord`` (aunque le falten obligatorios, en cuyo caso queda
    PENDIENTE_REVISIÓN, pero igualmente se produce).
  - entradas MALFORMADAS: valores que NO son dict (``None``/``int``/``str``/
    ``list``/``bool``) o un ``dict`` "venenoso" cuyo ``.get`` lanza, forzando que
    ``work_to_record`` eleve una excepción. En ambos casos ``_transformar_works``
    los descarta de forma robusta y los cuenta en ``stats.errores``.

Todas las páginas responden HTTP 200 (no hay errores HTTP en esta propiedad), de
modo que ``stats.errores`` cuenta EXCLUSIVAMENTE los works malformados
descartados. Se fija ``pace_seconds=0`` para no dormir entre páginas y se escribe
a un ``out_dir`` temporal que se limpia al terminar; nunca se toca ``data/raw/``
ni ``data/processed/openalex/`` real.

Los works generados por hypothesis son SINTÉTICOS (``DEMO_DATA``, datos de
prueba, no reales) y nunca se presentan como resultados reales.

Qué verifica, para cualquier mezcla de válidos y malformados repartida en una o
varias páginas:

  1. La corrida COMPLETA sin lanzar excepción pese a los malformados (Req 2.3).
  2. Los works válidos producen registros: ``len(records)`` es exactamente el
     número de works válidos de la entrada (Req 3.4).
  3. Los malformados se descartan y se cuentan en ``stats.errores``
     (``stats.errores == número de entradas malformadas``), y no quedan como
     registros.
  4. El pipeline ESCRIBE la salida (JSON+CSV) cuando hay al menos un registro
     válido, y NO escribe cuando no hay ninguno.
  5. Todo registro producido conserva la fuente fija ``"OpenAlex"``.
"""

from __future__ import annotations

import shutil
import sys
import uuid
from pathlib import Path

# Permite importar el pipeline y el conector desde bibliometrics/ (mismo patrón
# que los demás tests de este paquete).
_REPO_ROOT = Path(__file__).resolve().parents[2]
_BIBLIO = _REPO_ROOT / "bibliometrics"
if str(_BIBLIO) not in sys.path:
    sys.path.insert(0, str(_BIBLIO))

from typing import Any, Optional  # noqa: E402

from hypothesis import HealthCheck, given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

from ingestion.openalex_api_client import (  # noqa: E402
    ApiConfig,
    Consulta,
    OPENALEX_SOURCE,
)
from pipelines.process_openalex_api import run_pipeline  # noqa: E402


class _PoisonWork(dict):
    """``dict`` "venenoso": pasa ``isinstance(x, dict)`` pero su ``.get`` lanza.

    Modela un work malformado que supera el guardarraíl de tipo de
    ``_transformar_works`` (es un dict) pero rompe ``work_to_record`` en el
    primer acceso a un campo, forzando la rama ``except Exception`` que lo
    descarta de forma robusta sin abortar la corrida (Req 2.3, 3.4).
    """

    def get(self, *args: Any, **kwargs: Any) -> Any:  # type: ignore[override]
        raise ValueError("DEMO_DATA work venenoso: acceso a campo no soportado")


class _FakeResponse:
    """Respuesta HTTP falsa mínima: expone ``status_code`` y ``.json()``.

    Siempre 200: esta propiedad valida el descarte de works malformados, no los
    errores HTTP (que son otra propiedad). El ``json()`` entrega ``results`` y
    ``meta.next_cursor`` con la forma de la API real de OpenAlex.
    """

    def __init__(self, payload: dict[str, Any]) -> None:
        self.status_code = 200
        self._payload = payload

    def json(self) -> dict[str, Any]:
        return self._payload


class _FakeMixedSession:
    """Sesión HTTP falsa que sirve una mezcla de works paginada por cursor.

    Divide las ``entries`` (mezcla de works válidos y malformados) en páginas de
    tamaño ``per_page`` y responde cada ``.get(...)`` según el ``cursor``:
    ``"*"`` sirve la página 0 y cada página encadena con ``meta.next_cursor``
    hasta agotarse (``None``). Todo en memoria; no hay red.

    Las entradas se sirven TAL CUAL (incluidos valores no-dict y dicts
    venenosos), de modo que lleguen sin alterar a ``_transformar_works``.
    """

    def __init__(self, entries: list[Any], per_page: int) -> None:
        self._pages: list[list[Any]] = [
            entries[i : i + per_page] for i in range(0, len(entries), per_page)
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


@st.composite
def _valid_work(draw: st.DrawFn) -> dict:
    """Work VÁLIDO (``DEMO_DATA``): dict con subconjunto variable de campos.

    Es un objeto clave→valor, por lo que ``work_to_record`` lo transforma SIEMPRE
    con éxito (aunque le falten obligatorios: queda PENDIENTE_REVISIÓN, pero se
    produce). Se le da un ``id`` único para poder distinguirlo si hiciera falta.
    """
    work: dict = {"id": f"https://openalex.org/W{uuid.uuid4().hex[:8]}"}
    if draw(st.booleans()):
        work["title"] = draw(
            st.sampled_from(
                [
                    "Conservación de aves en los Andes",
                    "Bird conservation in Antioquia",
                    "Aves de humedales interiores",
                    "DEMO_DATA bird study",
                ]
            )
        )
    if draw(st.booleans()):
        work["display_name"] = draw(st.text(min_size=1, max_size=20))
    if draw(st.booleans()):
        work["publication_year"] = draw(st.integers(min_value=2015, max_value=2031))
    if draw(st.booleans()):
        work["doi"] = draw(
            st.text(min_size=1, max_size=20).filter(lambda s: s.strip() != "")
        )
    return work


# Entradas MALFORMADAS: valores que NO son dict, o un dict "venenoso" que rompe
# ``work_to_record``. Todas deben descartarse de forma robusta y contarse como
# error, sin abortar la corrida.
_malformed_entry = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(max_size=20),
    st.lists(st.integers(), max_size=3),
    st.builds(lambda: _PoisonWork()),
)


@st.composite
def _mixed_entries(draw: st.DrawFn) -> tuple[list[Any], int, int, int]:
    """Mezcla en orden aleatorio works válidos y entradas malformadas.

    Devuelve ``(entries, n_validos, n_malformados, per_page)``. La proporción
    válidos/malformados varía libremente (incluye lotes solo-válidos o
    solo-malformados). ``per_page`` es pequeño (1..5) para forzar que la mezcla
    abarque VARIAS páginas y ejercer el descarte en cualquier posición.
    """
    valids = draw(st.lists(_valid_work(), min_size=0, max_size=6))
    malformed = draw(st.lists(_malformed_entry, min_size=0, max_size=6))

    entries: list[Any] = list(valids) + list(malformed)
    entries = list(draw(st.permutations(entries)))
    per_page = draw(st.integers(min_value=1, max_value=5))
    return entries, len(valids), len(malformed), per_page


# Feature: fuente-openalex-api, Property 13: Robustez ante works malformados
@settings(max_examples=150, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(data=_mixed_entries())
def test_robustez_ante_works_malformados(
    tmp_path_factory, data: tuple[list[Any], int, int, int]
) -> None:
    """La corrida produce los válidos, descarta los malformados y no aborta.

    Validates: Requirements 2.3, 3.4
    """
    entries, n_validos, n_malformados, per_page = data

    out_dir = tmp_path_factory.mktemp("oa_api_malformed") / f"out_{uuid.uuid4().hex}"

    session = _FakeMixedSession(entries, per_page)
    consultas = [Consulta(term="DEMO_DATA aves", year_from=2020, year_to=2030)]
    # pace_seconds=0 evita dormir de verdad entre páginas durante el test.
    config = ApiConfig(per_page=per_page, pace_seconds=0.0)

    try:
        # (1) No aborta la corrida: ejecutar el pipeline no debe lanzar excepción
        # pese a la presencia de works malformados.
        records, stats, json_path, csv_path = run_pipeline(
            consultas, config, session=session, out_dir=out_dir
        )

        # (2) Los works válidos producen registros: exactamente n_validos.
        assert len(records) == n_validos, (
            f"deben producirse exactamente {n_validos} registro(s) para los works "
            f"válidos; se produjeron {len(records)}"
        )

        # (3) Los malformados se descartan y se cuentan en stats.errores. Como
        # todas las páginas responden 200, stats.errores cuenta SOLO los works
        # malformados descartados (no hay errores HTTP en esta propiedad).
        assert stats.errores == n_malformados, (
            f"stats.errores debe ser {n_malformados} (solo los malformados "
            f"descartados); fue {stats.errores}"
        )

        # Todos los works (válidos + malformados) se recuperaron de la API.
        assert stats.works_recuperados == len(entries)

        # (4) Escribe la salida si y solo si hay al menos un registro válido.
        if n_validos > 0:
            assert json_path is not None and csv_path is not None, (
                "con al menos un registro válido el pipeline debe escribir JSON+CSV"
            )
            assert json_path.is_file() and csv_path.is_file(), (
                "los archivos de salida deben existir en disco"
            )
        else:
            assert json_path is None and csv_path is None, (
                "sin registros válidos no debe escribirse ningún dataset"
            )

        # (5) Fuente fija: ningún registro producido cambia de origen en la
        # corrida mixta.
        for rec in records:
            assert rec.source == OPENALEX_SOURCE == "OpenAlex", (
                f"source debe ser 'OpenAlex', fue {rec.source!r}"
            )
    finally:
        # Limpieza del ejemplo: no dejar carpetas temporales de salida acumuladas.
        shutil.rmtree(out_dir, ignore_errors=True)
