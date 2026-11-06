"""Tests del único cambio de código del spec estrategia-bibliometrica-api
(tareas 2.4, 2.5, 2.6 y 2.7): soporte de ``OPENALEX_API_KEY`` en el conector
OpenAlex para habilitar la paginación por cursor más allá de la primera página.

Este módulo agrupa DELIBERADAMENTE las tres propiedades del diseño (Property 1,
2 y 3) y los tests de ejemplo/integración simulada (Req 7.5, 7.6, 7.7) porque
todos cubren el MISMO cambio de código (el parámetro ``api_key``): mantenerlos
juntos evita conflictos de escritura y comparte el cliente HTTP simulado.

Enfoque (design.md, Testing Strategy):

  - **Property-based tests** (Property 1, 2, 3) con **hypothesis** (ya pinado),
    **mínimo 100 iteraciones** cada uno, un único test por propiedad del diseño,
    etiquetado con el comentario
    ``# Feature: estrategia-bibliometrica-api, Property N: <texto>``.
  - **Cliente HTTP simulado**: NINGÚN test realiza solicitudes de red reales. La
    ``session`` se inyecta por el parámetro de ``run_pipeline`` / las funciones
    de fetch, igual que los demás tests de este paquete.
  - Las API keys generadas por hypothesis son SINTÉTICAS (``DEMO_DATA``, datos de
    prueba, no secretos reales) y nunca se presentan como valores reales.

Propiedades (design.md, Correctness Properties):

  - **Property 1** — Inclusión condicional del parámetro ``api_key``
    (Validates: Requirements 7.1, 7.2).
  - **Property 2** — Resolución de la API key desde el entorno
    (Validates: Requirements 7.3).
  - **Property 3** — El valor de la API key nunca se filtra en textos
    (Validates: Requirements 7.4).

Tests de ejemplo / integración simulada (design.md, Testing Strategy):

  - **Req 7.5** — con ``api_key`` en la config, la paginación por cursor recorre
    TODAS las páginas (no se corta en la primera) y CADA solicitud lleva
    ``api_key``.
  - **Req 7.6** — no-regresión: ``OPENALEX_MAILTO`` sigue poblándose junto a
    ``api_key``; la transformación, el ritmo y los reintentos no se tocan.
  - **Req 7.7** — verificación de contenido de ``.env.example`` (placeholder
    comentado presente, sin valor real).
"""

from __future__ import annotations

import sys
from pathlib import Path

# Permite importar el conector y el pipeline desde bibliometrics/ (mismo patrón
# que los demás tests de este paquete).
_REPO_ROOT = Path(__file__).resolve().parents[2]
_BIBLIO = _REPO_ROOT / "bibliometrics"
if str(_BIBLIO) not in sys.path:
    sys.path.insert(0, str(_BIBLIO))

import shutil  # noqa: E402
import tempfile  # noqa: E402
from typing import Any, Optional  # noqa: E402
from unittest import mock  # noqa: E402

from hypothesis import given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

from ingestion.openalex_api_client import (  # noqa: E402
    API_KEY_ENV_VAR,
    MAILTO_ENV_VAR,
    ApiConfig,
    Consulta,
    HttpError,
    _build_params,
    fetch_with_retry,
    resolve_api_key,
    resolve_mailto,
)
from pipelines import process_openalex_api as pipeline  # noqa: E402
from pipelines.process_openalex_api import run_pipeline  # noqa: E402


# ---------------------------------------------------------------------------
# Estrategias y utilidades compartidas (DEMO_DATA)
# ---------------------------------------------------------------------------
# Caracteres válidos para una API key en una variable de entorno: se excluye el
# carácter nulo porque ``os.environ`` no admite nulos embebidos (no es parte del
# dominio real de una variable de entorno).
_env_safe_text = st.text(
    alphabet=st.characters(blacklist_categories=("Cs",), blacklist_characters="\x00"),
    min_size=1,
    max_size=40,
)

# API keys SINTÉTICAS no vacías tras recortar: su valor recortado es no vacío.
_non_empty_keys = _env_safe_text.filter(lambda s: s.strip() != "")

# API keys que deben resolverse a None: ausente (None), vacía o solo espacios.
_empty_like_keys = st.one_of(
    st.none(),
    st.just(""),
    st.text(alphabet=" \t\r\n", min_size=1, max_size=6),  # solo espacios
)

# Cursores arbitrarios para _build_params; "*" es el inicio de la paginación.
_cursors = st.one_of(st.just("*"), st.text(min_size=1, max_size=20).filter(bool))

# Términos de búsqueda sintéticos y años dentro/alrededor del período 2020–2030.
_terms = st.text(min_size=1, max_size=30).map(lambda s: s.strip()).filter(bool)
_years = st.integers(min_value=2018, max_value=2032)


@st.composite
def _consulta_strategy(draw: st.DrawFn) -> Consulta:
    """Genera una ``Consulta`` sintética (DEMO_DATA)."""
    term = draw(_terms)
    year_from = draw(_years)
    year_to = draw(_years)
    return Consulta(term=term, year_from=year_from, year_to=year_to)


# ---------------------------------------------------------------------------
# Property 1 (tarea 2.4) — inclusión condicional del parámetro api_key
# ---------------------------------------------------------------------------
# Feature: estrategia-bibliometrica-api, Property 1: Inclusión condicional del parámetro api_key
@settings(max_examples=200)
@given(
    consulta=_consulta_strategy(),
    cursor=_cursors,
    api_key=st.one_of(_non_empty_keys, _empty_like_keys),
    per_page=st.integers(min_value=1, max_value=200),
)
def test_inclusion_condicional_del_parametro_api_key(
    consulta: Consulta,
    cursor: str,
    api_key: Optional[str],
    per_page: int,
) -> None:
    """``_build_params`` incluye ``api_key`` sii ``config.api_key`` es no vacío;
    el resto de parámetros es invariante en ambos casos.

    Validates: Requirements 7.1, 7.2
    """
    # Config SIN api_key (línea base) y config CON la api_key generada. Todo lo
    # demás idéntico (mismo per_page, sin mailto) para aislar el efecto de la key.
    config_sin = ApiConfig(per_page=per_page)
    config_con = ApiConfig(per_page=per_page, api_key=api_key)

    params_sin = _build_params(consulta, cursor, config_sin)
    params_con = _build_params(consulta, cursor, config_con)

    # El resto de parámetros (search, filter, per_page, cursor) debe coincidir
    # EXACTAMENTE con lo esperado en ambos casos (invariancia respecto a la key).
    esperado_resto = {
        "search": consulta.term,
        "filter": f"publication_year:{consulta.year_from}-{consulta.year_to}",
        "per_page": per_page,
        "cursor": cursor,
    }
    # La config base nunca lleva api_key.
    assert params_sin == esperado_resto

    # ``_build_params`` NO recorta: usa la condición ``if config.api_key``. Por
    # tanto incluye la clave sii ``config.api_key`` es un valor TRUTHY (una
    # cadena no vacía, aunque sea solo espacios); None y "" son falsy.
    # Nota: la normalización de espacios la hace ``resolve_api_key`` (Property 2),
    # no ``_build_params``; aquí ``ApiConfig`` recibe el valor crudo.
    if api_key:  # truthy ⇔ cadena no vacía (incluye solo-espacios)
        # Con key no vacía: aparece ``api_key`` con el valor EXACTO de config.
        assert params_con.get("api_key") == config_con.api_key
        assert config_con.api_key == api_key  # no se recorta dentro de la config
        # El resto de parámetros es invariante respecto a la línea base.
        resto_con = {k: v for k, v in params_con.items() if k != "api_key"}
        assert resto_con == esperado_resto
    else:
        # Con key None o "": la clave ``api_key`` NO aparece y el dict completo
        # es idéntico al de la línea base.
        assert "api_key" not in params_con
        assert params_con == esperado_resto
        assert params_con == params_sin


# ---------------------------------------------------------------------------
# Property 2 (tarea 2.5) — resolución de la API key desde el entorno
# ---------------------------------------------------------------------------
class _ExplodingPath:
    """Centinela: cualquier acceso a disco a través de ``open`` explota.

    Se usa para verificar que ``resolve_api_key`` obtiene el valor ÚNICAMENTE del
    entorno del proceso y NUNCA lee de un archivo (Req 7.3). Si la función
    intentara abrir un archivo, el test fallaría con ``AssertionError``.
    """

    def __call__(self, *args: Any, **kwargs: Any) -> Any:  # pragma: no cover
        raise AssertionError(
            "resolve_api_key() no debe acceder a disco: debe leer solo del entorno"
        )


# Feature: estrategia-bibliometrica-api, Property 2: Resolución de la API key desde el entorno
@settings(max_examples=200, deadline=None)
@given(raw=st.one_of(_non_empty_keys, _empty_like_keys))
def test_resolucion_de_la_api_key_desde_el_entorno(raw: Optional[str]) -> None:
    """``resolve_api_key()`` devuelve None si ausente/vacía/espacios y el valor
    recortado si es no vacía; el valor viene solo del entorno, sin tocar disco.

    Validates: Requirements 7.3
    """
    # monkeypatch manual del entorno (dentro del cuerpo porque hypothesis no se
    # combina con la fixture monkeypatch de pytest). Se restaura siempre.
    sentinel_absent = object()
    previo = __import__("os").environ.get(API_KEY_ENV_VAR, sentinel_absent)
    import os as _os

    try:
        if raw is None:
            _os.environ.pop(API_KEY_ENV_VAR, None)  # variable AUSENTE
        else:
            _os.environ[API_KEY_ENV_VAR] = raw

        # Bloquear cualquier lectura de disco mientras se resuelve la key: si la
        # función intentara abrir un archivo, ``open`` lanzaría AssertionError.
        with mock.patch("builtins.open", _ExplodingPath()):
            resolved = resolve_api_key()

        esperado = raw.strip() if isinstance(raw, str) else None
        esperado = esperado or None  # "" o solo-espacios → None

        if esperado is None:
            assert resolved is None, (
                f"ausente/vacía/espacios debe resolver a None; raw={raw!r}"
            )
        else:
            assert resolved == esperado, (
                f"una key no vacía debe devolverse recortada; "
                f"raw={raw!r}, esperado={esperado!r}, obtenido={resolved!r}"
            )
            # El valor proviene EXACTAMENTE del entorno (recortado).
            assert resolved == _os.environ[API_KEY_ENV_VAR].strip()
    finally:
        # Restaurar el estado previo del entorno.
        if previo is sentinel_absent:
            _os.environ.pop(API_KEY_ENV_VAR, None)
        else:
            _os.environ[API_KEY_ENV_VAR] = previo  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Property 3 (tarea 2.6) — el valor de la API key nunca se filtra en textos
# ---------------------------------------------------------------------------
class _ErrorResponse:
    """Respuesta HTTP falsa con un ``status_code`` de error (sin red real).

    ``json()`` no debería invocarse en el camino de error (``fetch_page`` lanza
    ``HttpError`` antes de parsear), pero se define por robustez.
    """

    def __init__(self, status_code: int) -> None:
        self.status_code = status_code

    def json(self) -> dict[str, Any]:  # pragma: no cover - no se usa en error
        return {"results": [], "meta": {"next_cursor": None}}


class _ErrorSession:
    """Sesión HTTP falsa que SIEMPRE responde con un código de error fijo.

    Registra los ``params`` de cada solicitud para poder verificar luego que,
    aunque la key viaje en los params (comportamiento correcto), NUNCA aparece en
    los textos emitidos (mensajes/representaciones/prints).
    """

    def __init__(self, status_code: int) -> None:
        self._status_code = status_code
        self.params_vistos: list[dict] = []

    def get(
        self,
        url: str,
        params: Optional[dict[str, Any]] = None,
        timeout: Any = None,
    ) -> _ErrorResponse:
        self.params_vistos.append(dict(params or {}))
        return _ErrorResponse(self._status_code)


# Códigos de error que fuerzan las rutas de error: 401 (falta de key en la
# paginación), 429 (rate limit, transitorio) y 400/permanente.
_error_codes = st.sampled_from([401, 429, 500, 400, 403])


# La key lleva un prefijo centinela único que NO puede aparecer en el término de
# búsqueda ni en los años de la Consulta. Así, si la key apareciera en un texto
# emitido sería por una FILTRACIÓN real y no por coincidir con el término (que sí
# aparece legítimamente en los mensajes de error). El sufijo aleatorio ejerce
# valores variados de key sin reintroducir esa ambigüedad.
_API_KEY_SENTINEL = "APIKEYSENTINEL_"
_key_suffix = st.text(
    alphabet=st.characters(
        blacklist_categories=("Cs", "Cc", "Zs"), blacklist_characters="\x00"
    ),
    min_size=1,
    max_size=24,
)


# Feature: estrategia-bibliometrica-api, Property 3: El valor de la API key nunca se filtra en textos
@settings(max_examples=150, deadline=None)
@given(
    api_key_suffix=_key_suffix,
    status_code=_error_codes,
    consulta=_consulta_strategy(),
)
def test_el_valor_de_la_api_key_nunca_se_filtra_en_textos(
    api_key_suffix: str,
    status_code: int,
    consulta: Consulta,
) -> None:
    """Ningún texto emitido (HttpError, repr de excepciones, prints del
    pipeline) contiene el valor literal de la key, aun forzando errores HTTP.

    Validates: Requirements 7.4
    """
    api_key = _API_KEY_SENTINEL + api_key_suffix
    # Config CON la api_key sintética: aunque viaje en los params de la petición,
    # no debe aparecer en ningún texto emitido.
    config = ApiConfig(
        per_page=200,
        max_results=None,
        pace_seconds=0.0,
        max_retries=0,  # sin reintentos: error inmediato, suite rápida
        backoff_base=0.0,
        api_key=api_key,
    )
    textos: list[str] = []

    # (a) fetch_with_retry propaga HttpError: su mensaje NO debe incluir la key.
    session_fetch = _ErrorSession(status_code)
    try:
        fetch_with_retry(session_fetch, consulta, "*", config)
    except HttpError as exc:
        textos.append(str(exc))
        textos.append(repr(exc))

    # Confirmación de que la key SÍ viajó en los params (comportamiento correcto)
    # pero nunca se filtra en los textos: valida que el test no es trivial.
    assert any(p.get("api_key") == api_key for p in session_fetch.params_vistos)

    # (b) run_pipeline con sesión de error: recorre la ruta de error del pipeline
    # (_iter_consulta_pages imprime [ERR ] ...). Capturamos TODO lo impreso.
    import io
    from contextlib import redirect_stdout

    session_pipeline = _ErrorSession(status_code)
    out_dir = Path(tempfile.mkdtemp(prefix="demo_api_key_leak_"))
    buffer = io.StringIO()
    try:
        with redirect_stdout(buffer):
            records, stats, json_path, csv_path = run_pipeline(
                [consulta], config, session=session_pipeline, out_dir=out_dir
            )
            # Resumen de ingesta (otra ruta que emite texto).
            pipeline._print_ingest_summary(stats, len(records))
    finally:
        shutil.rmtree(out_dir, ignore_errors=True)

    textos.append(buffer.getvalue())
    # Representaciones de las etiquetas de páginas con error acumuladas.
    textos.extend(stats.paginas_con_error)
    textos.append(repr(stats.paginas_con_error))

    # La key viajó en cada solicitud del pipeline también.
    assert any(p.get("api_key") == api_key for p in session_pipeline.params_vistos)

    # Afirmación central: la key NO aparece en NINGÚN texto emitido.
    for texto in textos:
        assert api_key not in texto, (
            "el valor de la API key no debe filtrarse en ningún texto emitido "
            f"(status={status_code})"
        )


# ===========================================================================
# Tests de ejemplo / integración simulada (tarea 2.7, OPCIONAL)
# ===========================================================================
class _OkResponse:
    """Respuesta HTTP falsa 200 con payload de una página (sin red real)."""

    def __init__(self, payload: dict[str, Any]) -> None:
        self.status_code = 200
        self._payload = payload

    def json(self) -> dict[str, Any]:
        return self._payload


class _MultiPageSession:
    """Sesión falsa de 2–3 páginas encadenadas por ``next_cursor``.

    Registra los ``params`` de cada ``.get`` para poder verificar que CADA
    solicitud llevó ``api_key`` y que se recorrieron TODAS las páginas.
    """

    def __init__(self, pages: list[list[dict]]) -> None:
        assert pages, "debe haber al menos una página"
        self._pages = pages
        self.params_vistos: list[dict] = []

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
        timeout: Any = None,
    ) -> _OkResponse:
        self.params_vistos.append(dict(params or {}))
        cursor = (params or {}).get("cursor", "*")
        idx = self._page_index_for_cursor(cursor)
        results = self._pages[idx] if 0 <= idx < len(self._pages) else []
        next_idx = idx + 1
        next_cursor = f"c{next_idx}" if next_idx < len(self._pages) else None
        return _OkResponse({"results": results, "meta": {"next_cursor": next_cursor}})


def _work_valido(n: int) -> dict:
    """Work sintético VÁLIDO (DEMO_DATA) transformable por ``work_to_record``."""
    return {
        "id": f"https://openalex.org/W{n}",
        "title": f"DEMO_DATA work numero {n}",
        "publication_year": 2021,
        "authorships": [{"author": {"display_name": f"DEMO Autor {n}"}}],
    }


def test_req_7_5_paginacion_recorre_todas_las_paginas_con_api_key() -> None:
    """Req 7.5: con api_key, el pipeline recorre TODAS las páginas por cursor
    (no se corta en la primera) y CADA solicitud lleva ``api_key``.
    """
    # Tres páginas con dos works cada una (DEMO_DATA).
    pages = [
        [_work_valido(0), _work_valido(1)],
        [_work_valido(2), _work_valido(3)],
        [_work_valido(4), _work_valido(5)],
    ]
    session = _MultiPageSession(pages)
    config = ApiConfig(per_page=2, max_results=None, pace_seconds=0.0, api_key="demo-key-123")
    consulta = Consulta(term="DEMO_DATA aves", year_from=2020, year_to=2030)

    out_dir = Path(tempfile.mkdtemp(prefix="demo_api_key_pages_"))
    try:
        records, stats, _json, _csv = run_pipeline(
            [consulta], config, session=session, out_dir=out_dir
        )
    finally:
        shutil.rmtree(out_dir, ignore_errors=True)

    # Se recorrieron las 3 páginas (más la consulta final que devuelve cursor
    # None tras la tercera): al menos 3 solicitudes, una por página con contenido.
    assert len(session.params_vistos) >= 3, (
        "la paginación debe avanzar más allá de la primera página con api_key"
    )
    # Todos los works de las 3 páginas se recuperaron (no se cortó en la primera).
    assert stats.works_recuperados == 6
    assert len(records) == 6

    # CADA solicitud llevó la api_key.
    assert session.params_vistos, "debe haberse hecho al menos una solicitud"
    for params in session.params_vistos:
        assert params.get("api_key") == "demo-key-123", (
            "cada solicitud a OpenAlex debe incluir el parámetro api_key"
        )


def test_req_7_6_no_regresion_mailto_junto_a_api_key(monkeypatch) -> None:
    """Req 7.6: no-regresión — ``OPENALEX_MAILTO`` sigue poblándose junto a
    ``api_key`` en la config construida por el pipeline; la transformación, el
    ritmo y los reintentos conservan sus valores.
    """
    monkeypatch.setenv(MAILTO_ENV_VAR, "demo-contacto@ejemplo.org")
    monkeypatch.setenv(API_KEY_ENV_VAR, "demo-key-xyz")

    # resolve_* leen del entorno (ya mockeado); la config del pipeline debe
    # poblar AMBOS campos.
    args = pipeline._parse_args(["--term", "DEMO_DATA aves"])
    config = pipeline._build_config(args)

    assert config.mailto == "demo-contacto@ejemplo.org", (
        "OPENALEX_MAILTO debe seguir poblándose (no-regresión)"
    )
    assert config.api_key == "demo-key-xyz", (
        "OPENALEX_API_KEY debe poblar api_key junto a mailto"
    )

    # Ritmo y reintentos conservan sus defaults del CLI (lógica intacta).
    assert config.pace_seconds == 0.2
    assert config.max_retries == 5
    # El default de --max-results sigue siendo None (no se cambió — Req 11.8).
    assert config.max_results is None

    # La transformación work → ArticleRecord sigue intacta: un work válido
    # produce un registro con source "OpenAlex" y método "OpenAlex API V1".
    from ingestion.openalex_api_client import work_to_record

    record = work_to_record(_work_valido(7))
    assert record.source == "OpenAlex"
    assert record.extraction_method == "OpenAlex API V1"


def test_req_7_7_env_example_documenta_placeholder_sin_valor_real() -> None:
    """Req 7.7: ``.env.example`` documenta ``OPENALEX_API_KEY`` como placeholder
    comentado, sin un valor real asignado.
    """
    env_example = _REPO_ROOT / ".env.example"
    assert env_example.is_file(), "debe existir .env.example en la raíz del repo"

    lineas = env_example.read_text(encoding="utf-8").splitlines()
    key_lines = [ln for ln in lineas if "OPENALEX_API_KEY" in ln]
    assert key_lines, "`.env.example` debe mencionar OPENALEX_API_KEY"

    for ln in key_lines:
        stripped = ln.strip()
        # Debe estar COMENTADO (placeholder), nunca como asignación activa.
        assert stripped.startswith("#"), (
            f"OPENALEX_API_KEY debe ir comentado como placeholder: {ln!r}"
        )
        # Si la línea comentada tiene la forma `# OPENALEX_API_KEY=...`, el valor
        # a la derecha del `=` debe estar VACÍO (sin valor real).
        sin_comentario = stripped.lstrip("#").strip()
        if sin_comentario.startswith("OPENALEX_API_KEY") and "=" in sin_comentario:
            _, _, valor = sin_comentario.partition("=")
            assert valor.strip() == "", (
                f"OPENALEX_API_KEY no debe tener un valor real en .env.example: {ln!r}"
            )
