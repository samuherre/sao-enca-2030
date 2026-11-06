"""Integración 7.1 (spec ``fuente-openalex-api``) — OpenAlex por API en el consolidado.

VERIFICACIÓN DE NO-REDISEÑO (Req 7.1–7.4): comprueba que la fuente **OpenAlex**,
obtenida por la vía de **consulta directa a la API** (Componente B de este spec),
se incorpora al resumen consolidado **por convención**, sin tocar el servicio
(``bibliometria_service.py``), el endpoint (``api/bibliometria.py``), los schemas
ni la ``BibliometriaPage``. La incorporación ocurre porque:

- existe una carpeta ``data/processed/openalex/`` con un ``Dataset_Procesado``
  conforme al Article Data Contract V1, y
- cada registro lleva ``source = "OpenAlex"``.

El ``BibliometriaService`` descubre cualquier subcarpeta bajo
``data/processed/`` y agrupa por el campo ``source`` de cada registro, por lo que
OpenAlex aparece en ``total_articulos`` y en ``aporte_por_fuente`` con el nombre
exacto ``"OpenAlex"`` **sin cambios de código**.

FIDELIDAD DEL DATASET (design.md, Testing Strategy; tarea 7.1):
A diferencia del test hermano de la vía PoP (``test_openalex_consolidado.py``,
que escribe registros a mano), aquí el ``Dataset_Procesado`` de OpenAlex se
construye con el **pipeline real por API** (``process_openalex_api.run_pipeline``)
a partir de ``work``s nativos sintéticos (``DEMO_DATA``) servidos por una **sesión
HTTP simulada**. Así el dataset pasa por el conector real
(``work_to_record`` → ``validate_period`` → ``mark_duplicates`` → ``write_outputs``)
y refleja el contrato V1 tal como lo produce la corrida de verdad. **Ningún test
golpea la red real** (design.md, Testing Strategy).

Se verifica por dos vías equivalentes:

1. Directamente vía :class:`BibliometriaService`.
2. Vía el endpoint real ``GET /bibliometria/resumen`` con ``TestClient``.

Además se comprueba que el ``Dataset_Procesado`` de **Google Scholar** (otra
fuente) sigue contándose como su propia fuente y permanece intacto (Req 7.4).

Igual que el resto de pruebas bibliométricas de integración, estos endpoints NO
usan la base de datos: el servicio lee datasets procesados de archivos. Por eso
NO se usa ``api_client`` (que inyecta sesión de BD); se monkeypatchea el
directorio de módulo ``_PROCESSED_DIR`` del servicio hacia una carpeta temporal.
Todos los datos son SINTÉTICOS (``DEMO_DATA``), nunca datos reales de SAO, y las
carpetas temporales las limpia ``tmp_path`` de pytest.

El nombre de la fuente (``"OpenAlex"``) se importa de ``OPENALEX_SOURCE`` del
conector por API para no hardcodear la etiqueta y mantener la verificación
acoplada al conector real.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import backend.src.services.bibliometria_service as svc
from backend.src.main import app
from bibliometrics.ingestion.openalex_api_client import (
    OPENALEX_SOURCE,
    ApiConfig,
    Consulta,
)
from bibliometrics.pipelines.process_openalex_api import run_pipeline
from backend.src.services.bibliometria_service import BibliometriaService


# --- works nativos sintéticos (DEMO_DATA) -----------------------------------
# Forma del JSON NATIVO de la API de OpenAlex (``work``), NO del contrato V1: el
# pipeline real los transforma al Article Data Contract V1. NO representan
# trabajos reales de SAO. Cubren año en rango, año fuera de rango (→ revisión),
# con/sin DOI, abstract como índice invertido y un título repetido para que la
# deduplicación básica del pipeline marque un duplicado sobre el conjunto.
_OPENALEX_WORKS_DEMO = [
    {
        "id": "https://openalex.org/W1000000001",
        "doi": "https://doi.org/10.0000/demo-oa-1",
        "title": "DEMO OpenAlex API uno",
        "display_name": "DEMO OpenAlex API uno",
        "publication_year": 2023,
        "authorships": [
            {"author": {"display_name": "Autor Alfa"}},
            {"author": {"display_name": "Autor Beta"}},
        ],
        "primary_location": {
            "landing_page_url": "https://example.org/oa-1",
            "source": {"display_name": "Revista Demo"},
        },
        "biblio": {"volume": "12", "issue": "1", "first_page": "1", "last_page": "9"},
        "abstract_inverted_index": {"Resumen": [0], "demo": [1], "uno": [2]},
        "concepts": [{"display_name": "aves"}, {"display_name": "conservación"}],
        "language": "es",
    },
    {
        "id": "https://openalex.org/W1000000002",
        "doi": None,
        "title": "DEMO OpenAlex API dos",
        "display_name": "DEMO OpenAlex API dos",
        "publication_year": 2024,
        "authorships": [{"author": {"display_name": "Autor Gamma"}}],
        "primary_location": {"source": {"display_name": "Revista Demo"}},
        "biblio": {"volume": "13"},
        "abstract_inverted_index": None,
        "concepts": [],
        "language": "en",
    },
    {
        # Título idéntico al primero -> la dedupe básica marca este como duplicado.
        "id": "https://openalex.org/W1000000003",
        "doi": "https://doi.org/10.0000/demo-oa-3",
        "title": "DEMO OpenAlex API uno",
        "display_name": "DEMO OpenAlex API uno",
        "publication_year": 2023,
        "authorships": [{"author": {"display_name": "Autor Delta"}}],
        "primary_location": {"source": {"display_name": "Revista Demo"}},
        "biblio": {"volume": "12"},
        "abstract_inverted_index": {"Otro": [0], "resumen": [1]},
        "concepts": [{"display_name": "humedales"}],
        "language": "es",
    },
]

# Otra fuente que debe permanecer intacta y contarse por separado (Req 7.4).
# Esta se escribe a mano (registros YA conformes al contrato V1), pues no pasa
# por el pipeline de OpenAlex: representa un Dataset_Procesado existente.
_SCHOLAR_DEMO = [
    {
        "source": "Google Scholar",
        "title": "DEMO Scholar uno",
        "authors": "Autor Épsilon",
        "abstract": "Resumen demo Scholar 1.",
        "keywords": "aviturismo",
        "doi": "10.0000/demo-gs-1",
        "publication_year": 2022,
        "volume": "7",
        "inclusion_status": "INCLUIDO",
        "is_duplicate": False,
    },
    {
        "source": "Google Scholar",
        "title": "DEMO Scholar dos",
        "authors": "Autor Zeta",
        "abstract": None,
        "keywords": None,
        "doi": None,
        "publication_year": 2021,
        "volume": "6",
        "inclusion_status": "PENDIENTE_REVISIÓN",
        "is_duplicate": False,
    },
]


class _FakeResponse:
    """Respuesta HTTP simulada (sin red real)."""

    def __init__(self, payload: dict, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def json(self) -> dict:
        return self._payload


class _FakeSession:
    """Sesión HTTP simulada: sirve todos los works en UNA página, sin red.

    Reproduce la interfaz mínima que usa el conector (``get(url, params, timeout)``
    → objeto con ``.status_code`` y ``.json()``). Devuelve ``next_cursor = None``
    para agotar la paginación en una sola página. NO toca la red real
    (design.md, Testing Strategy).
    """

    def __init__(self, works: list[dict]) -> None:
        self._works = works

    def get(self, url, params=None, timeout=None):  # noqa: ANN001, D401
        return _FakeResponse({"results": self._works, "meta": {"next_cursor": None}})


def _seed_openalex_via_pipeline(processed_dir: Path) -> list:
    """Produce el Dataset_Procesado de OpenAlex con el PIPELINE REAL por API.

    Usa una sesión HTTP simulada (``_FakeSession``) para no tocar la red y
    escribe en ``processed_dir/openalex`` vía ``run_pipeline(..., out_dir=...)``,
    de modo que el dataset recorre el conector real y queda conforme al contrato
    V1 con ``source = "OpenAlex"``. Devuelve los ``ArticleRecord`` producidos.
    """
    out_dir = processed_dir / "openalex"
    session = _FakeSession(_OPENALEX_WORKS_DEMO)
    # ``pace_seconds=0`` evita cualquier espera; una sola Consulta basta porque
    # la sesión simulada entrega todos los works en una página.
    config = ApiConfig(per_page=200, pace_seconds=0.0, max_retries=0)
    records, _stats, json_path, _csv_path = run_pipeline(
        [Consulta(term="DEMO aves", year_from=2020, year_to=2030)],
        config,
        session=session,
        out_dir=out_dir,
    )
    assert json_path is not None, "El pipeline debió escribir el dataset de OpenAlex."
    return records


def _seed_source_json(
    processed_dir: Path, carpeta: str, fecha: str, registros: list
) -> None:
    """Escribe a mano un Dataset_Procesado de otra fuente (p. ej. Scholar).

    El nombre del archivo incluye la fecha ``YYYY-MM-DD`` para que el servicio lo
    descubra igual que en producción (``*_dataset_YYYY-MM-DD.json``).
    """
    carpeta_dir = processed_dir / carpeta
    carpeta_dir.mkdir(parents=True, exist_ok=True)
    archivo = carpeta_dir / f"{carpeta}_dataset_{fecha}.json"
    archivo.write_text(json.dumps(registros), encoding="utf-8")


@pytest.fixture()
def processed_con_openalex_api_y_scholar(tmp_path: Path, monkeypatch) -> dict:
    """Prepara un ``data/processed/`` temporal con OpenAlex (API) + Google Scholar.

    OpenAlex se genera con el pipeline real por API (sesión simulada); Google
    Scholar se siembra a mano. Apunta el ``_PROCESSED_DIR`` del servicio a la
    carpeta temporal para que el descubrimiento de fuentes opere sobre datos
    sintéticos controlados, sin tocar el ``data/processed/`` real del repo.
    """
    processed = tmp_path / "processed"
    processed.mkdir()
    oa_records = _seed_openalex_via_pipeline(processed)
    _seed_source_json(processed, "google_scholar", "2026-11-09", _SCHOLAR_DEMO)
    monkeypatch.setattr(svc, "_PROCESSED_DIR", processed)
    return {"processed": processed, "oa_records": oa_records}


@pytest.fixture()
def client() -> TestClient:
    """``TestClient`` de la app real, sin overrides de base de datos."""
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# 1) Vía BibliometriaService (sin HTTP)
# ---------------------------------------------------------------------------
def test_openalex_api_aparece_en_consolidado_via_servicio(
    processed_con_openalex_api_y_scholar,
):
    """OpenAlex (vía API) aparece en el total y en ``aporte_por_fuente`` (Req 7.1, 7.2).

    Y Google Scholar sigue contándose como su propia fuente, intacto (Req 7.4).
    No se modifica el servicio: la fuente entra por convención (carpeta +
    ``source = "OpenAlex"``).
    """
    oa_records = processed_con_openalex_api_y_scholar["oa_records"]
    n_openalex = len(oa_records)
    assert n_openalex == len(_OPENALEX_WORKS_DEMO)  # 3 works -> 3 registros

    resumen = BibliometriaService().resumen_consolidado()

    # --- Total = unión sin exclusión: OpenAlex + Scholar (Req 7.1) ----------
    assert resumen.total_articulos == n_openalex + len(_SCHOLAR_DEMO)

    # --- Aporte por fuente: OpenAlex presente con su nombre exacto (Req 7.2) -
    aporte = {a.fuente: a for a in resumen.aporte_por_fuente}
    assert OPENALEX_SOURCE in aporte
    assert aporte[OPENALEX_SOURCE].fuente == "OpenAlex"
    assert aporte[OPENALEX_SOURCE].total_articulos == n_openalex

    # --- Google Scholar intacto como su propia fuente (Req 7.4) -------------
    assert "Google Scholar" in aporte
    assert aporte["Google Scholar"].total_articulos == len(_SCHOLAR_DEMO)

    # --- Ninguna otra fuente espuria y suma de aportes == total (Req 7.3/7.4)
    assert set(aporte) == {"OpenAlex", "Google Scholar"}
    assert (
        sum(a.total_articulos for a in resumen.aporte_por_fuente)
        == resumen.total_articulos
    )

    # --- El aporte de OpenAlex trae su completitud por campo (Req 7.2) ------
    campos_oa = {c.campo for c in aporte[OPENALEX_SOURCE].completitud}
    assert campos_oa == {"title", "authors", "abstract", "keywords", "doi"}


# ---------------------------------------------------------------------------
# 2) Vía endpoint GET /bibliometria/resumen (HTTP real)
# ---------------------------------------------------------------------------
def test_openalex_api_aparece_en_consolidado_via_endpoint(
    client, processed_con_openalex_api_y_scholar
):
    """El endpoint consolidado expone OpenAlex sin tocar la ruta ni el schema."""
    oa_records = processed_con_openalex_api_y_scholar["oa_records"]
    n_openalex = len(oa_records)

    r = client.get("/bibliometria/resumen")
    assert r.status_code == 200, r.text
    body = r.json()

    # --- Total consolidado (schema sin cambios) -----------------------------
    assert body["total_articulos"] == n_openalex + len(_SCHOLAR_DEMO)

    # --- OpenAlex en el desglose con el nombre exacto "OpenAlex" (Req 7.2) --
    aporte = {a["fuente"]: a for a in body["aporte_por_fuente"]}
    assert set(aporte) == {"OpenAlex", "Google Scholar"}
    assert aporte["OpenAlex"]["total_articulos"] == n_openalex
    assert aporte["Google Scholar"]["total_articulos"] == len(_SCHOLAR_DEMO)

    # --- La suma de aportes coincide con el total (unión sin exclusión) -----
    assert (
        aporte["OpenAlex"]["total_articulos"]
        + aporte["Google Scholar"]["total_articulos"]
        == body["total_articulos"]
    )

    # --- El dataset de OpenAlex pasó por el conector real: todos sus registros
    #     entran como PENDIENTE_REVISIÓN (V1), por lo que el consolidado reporta
    #     al menos esos pendientes (Req 7.1).
    assert body["pendientes_revision"] >= n_openalex

    # --- La dedupe básica del pipeline marcó el título repetido (Req 7.1) ---
    assert body["posibles_duplicados"] >= 1


# ---------------------------------------------------------------------------
# 3) OpenAlex (API) como única fuente también entra al consolidado
# ---------------------------------------------------------------------------
def test_openalex_api_sola_aparece_en_consolidado(tmp_path, monkeypatch):
    """Con OpenAlex (API) como única fuente, aparece en el consolidado.

    Refuerza que la incorporación no depende de la presencia de otras fuentes:
    basta la carpeta ``openalex/`` con ``source = "OpenAlex"`` producida por el
    pipeline real (Req 7.1).
    """
    processed = tmp_path / "processed"
    processed.mkdir()
    oa_records = _seed_openalex_via_pipeline(processed)
    monkeypatch.setattr(svc, "_PROCESSED_DIR", processed)

    resumen = BibliometriaService().resumen_consolidado()

    assert resumen.total_articulos == len(oa_records)
    aporte = {a.fuente: a for a in resumen.aporte_por_fuente}
    assert list(aporte) == ["OpenAlex"]
    assert aporte["OpenAlex"].total_articulos == len(oa_records)
