"""Property test de la capa HTTP del Conector_OpenAlex_API (spec
fuente-openalex-api, tarea 2.3).

Property 8 del design.md — "Reintento solo ante errores transitorios":

    Para toda secuencia de respuestas HTTP, ``fetch_with_retry`` reintenta
    únicamente errores transitorios (429, 5xx) con espera creciente hasta
    ``max_retries``, no reintenta errores permanentes (p. ej. 400), y si agota
    los reintentos propaga el error para que el pipeline lo registre y continúe.

    **Validates: Requirements 2.2**

Enfoque (Testing Strategy del design, "Capa HTTP (sin red real)"): se SIMULA el
cliente HTTP con una sesión falsa (``FakeSession``) cuyo ``.get(...)`` devuelve
respuestas de una secuencia de códigos de estado generada por hypothesis
(mezcla de 200 / 429 / 5xx / 4xx). NINGÚN test golpea la red real.

Para que las esperas crecientes del backoff no bloqueen la suite, se MOCKEA
``openalex_api_client.time.sleep`` mediante ``monkeypatch`` y se registran las
esperas solicitadas para poder verificar que el backoff crece.

Lo que se verifica sobre cada secuencia generada:

  1. Un error PERMANENTE (p. ej. 400) en la primera respuesta se propaga de
     inmediato, SIN reintento (``.get`` se llamó exactamente una vez y no hubo
     ninguna espera).
  2. Un error TRANSITORIO (429 / 5xx) se reintenta hasta ``max_retries`` veces;
     si tras esos reintentos vuelve a fallar, se propaga ``HttpError`` (el
     número total de llamadas es ``max_retries + 1``).
  3. Un 200 tras algunos fallos transitorios devuelve el resultado y se detiene
     en cuanto llega el éxito (no consume más respuestas de las necesarias).
  4. Las esperas del backoff son NO decrecientes (espera creciente) y solo se
     producen entre reintentos de errores transitorios.

Los datos generados por hypothesis son SINTÉTICOS (DEMO_DATA, no reales).
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
from unittest import mock  # noqa: E402

import pytest  # noqa: E402
from hypothesis import HealthCheck, given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

from ingestion import openalex_api_client as api  # noqa: E402
from ingestion.openalex_api_client import (  # noqa: E402
    ApiConfig,
    Consulta,
    HttpError,
    fetch_with_retry,
)

# Un next_cursor arbitrario que devuelven las respuestas 200 simuladas; basta
# para comprobar que el éxito propaga su resultado tal cual.
_NEXT_CURSOR = "cursor-siguiente"


class FakeResponse:
    """Respuesta HTTP simulada estilo ``requests.Response`` (sin red real).

    Expone ``status_code`` y ``json()``. Para un 200 devuelve un payload con una
    página de ``results`` y un ``meta.next_cursor`` para que ``fetch_page`` pueda
    construir su tupla ``(results, next_cursor)``.
    """

    def __init__(self, status_code: int) -> None:
        self.status_code = status_code

    def json(self) -> dict[str, Any]:
        # Solo se consulta en el camino de éxito (status < 400). Payload mínimo
        # válido para la capa HTTP: una página con un work y un cursor siguiente.
        return {
            "results": [{"id": "https://openalex.org/W1"}],
            "meta": {"next_cursor": _NEXT_CURSOR},
        }


class FakeSession:
    """Sesión HTTP simulada: ``.get(...)`` devuelve respuestas de una secuencia.

    Recorre ``status_sequence`` en cada llamada a ``get`` y cuenta cuántas veces
    fue invocada, de modo que el test pueda afirmar el número exacto de intentos
    (reintentos) sin tocar la red real. Si la secuencia se agota, repite el
    último código (comportamiento defensivo; los tests acotan el tamaño para no
    depender de esto).
    """

    def __init__(self, status_sequence: list[int]) -> None:
        assert status_sequence, "la secuencia de estados no puede estar vacía"
        self._statuses = list(status_sequence)
        self.calls = 0

    def get(self, url: str, params: Optional[dict] = None, timeout: Any = None):
        idx = min(self.calls, len(self._statuses) - 1)
        status = self._statuses[idx]
        self.calls += 1
        return FakeResponse(status)


def _is_transient(status: int) -> bool:
    """Réplica de la clasificación del cliente: 429 y 5xx son transitorios."""
    return status == 429 or 500 <= status <= 599


# Códigos de ejemplo por categoría para construir secuencias realistas.
_TRANSIENT_CODES = st.sampled_from([429, 500, 502, 503, 504, 599])
_PERMANENT_CODES = st.sampled_from([400, 401, 403, 404, 410, 422])
_SUCCESS_CODE = st.just(200)
_ANY_CODE = st.one_of(_SUCCESS_CODE, _TRANSIENT_CODES, _PERMANENT_CODES)


# Feature: fuente-openalex-api, Property 8: Reintento solo ante errores transitorios
@settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
@given(
    sequence=st.lists(_ANY_CODE, min_size=1, max_size=12),
    max_retries=st.integers(min_value=0, max_value=6),
    backoff_base=st.floats(min_value=0.0, max_value=5.0, allow_nan=False),
)
def test_reintento_solo_ante_errores_transitorios(
    sequence: list[int],
    max_retries: int,
    backoff_base: float,
) -> None:
    """fetch_with_retry reintenta solo transitorios, con backoff creciente.

    Validates: Requirements 2.2
    """
    # Mockear time.sleep (vía unittest.mock, no una fixture de pytest) para que
    # el backoff no duerma de verdad; se registran las esperas solicitadas para
    # verificar que el backoff es creciente. mock.patch como context manager se
    # restablece en cada ejemplo generado por hypothesis.
    sleeps: list[float] = []
    with mock.patch.object(api.time, "sleep", side_effect=lambda s: sleeps.append(s)):
        _run_case(sequence, max_retries, backoff_base, sleeps)


def _run_case(
    sequence: list[int],
    max_retries: int,
    backoff_base: float,
    sleeps: list[float],
) -> None:
    """Ejecuta y verifica un caso con ``time.sleep`` ya mockeado."""
    session = FakeSession(sequence)
    config = ApiConfig(
        per_page=200,
        pace_seconds=0.0,
        max_retries=max_retries,
        backoff_base=backoff_base,
    )
    consulta = Consulta(term="aves conservación", year_from=2020, year_to=2030)

    # Calcular el desenlace esperado recorriendo la secuencia con la misma
    # lógica del cliente: se consume la secuencia hasta un éxito, un permanente
    # o hasta agotar los reintentos.
    expected_calls = 0
    outcome = None  # "success" | "permanent" | "exhausted"
    for i in range(max_retries + 1):
        status = sequence[min(i, len(sequence) - 1)]
        expected_calls += 1
        if status < 400:
            outcome = "success"
            break
        if not _is_transient(status):
            outcome = "permanent"
            break
        # Transitorio: si quedan reintentos, se seguirá; si no, se agota.
        if i == max_retries:
            outcome = "exhausted"
    if outcome is None:
        outcome = "exhausted"

    if outcome == "success":
        results, next_cursor = fetch_with_retry(session, consulta, "*", config)
        # (3) El éxito propaga el resultado de la página tal cual.
        assert results == [{"id": "https://openalex.org/W1"}]
        assert next_cursor == _NEXT_CURSOR
    else:
        # (1) Permanente y (2) reintentos agotados: ambos propagan HttpError.
        with pytest.raises(HttpError) as excinfo:
            fetch_with_retry(session, consulta, "*", config)
        if outcome == "permanent":
            # El permanente NO es transitorio y NO se reintenta.
            assert excinfo.value.transient is False
        else:
            # Agotamiento: el último error propagado es transitorio.
            assert excinfo.value.transient is True

    # Número exacto de llamadas = intentos realizados (incluye el inicial).
    assert session.calls == expected_calls, (
        f"intentos esperados {expected_calls}, reales {session.calls} "
        f"(outcome={outcome}, max_retries={max_retries}, seq={sequence})"
    )

    # (1) Permanente en el primer intento => exactamente una llamada y 0 esperas.
    first_status = sequence[0]
    if first_status >= 400 and not _is_transient(first_status):
        assert session.calls == 1, "un permanente no debe reintentarse"
        assert sleeps == [], "un permanente no debe generar ninguna espera"

    # (4) Solo se espera entre reintentos de transitorios; nunca más esperas que
    # reintentos efectivamente realizados (llamadas - 1).
    assert len(sleeps) <= max(session.calls - 1, 0)
    # El backoff es creciente (no decreciente) entre reintentos sucesivos.
    assert sleeps == sorted(sleeps), f"el backoff debe ser creciente: {sleeps}"
    # Si hubo esperas, cada una debe ser coherente con backoff_base creciente.
    for n, wait in enumerate(sleeps):
        assert wait == pytest.approx(backoff_base * (n + 1)), (
            f"espera {n} = {wait}, se esperaba {backoff_base * (n + 1)}"
        )
