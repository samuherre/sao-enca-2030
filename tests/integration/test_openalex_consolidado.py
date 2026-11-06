"""Integración 6.1 (spec ``fuente-openalex``) — OpenAlex en el consolidado.

VERIFICACIÓN DE NO-REDISEÑO (Req 6.1–6.4): comprueba que la fuente **OpenAlex**
se incorpora al resumen consolidado **por convención**, sin tocar el servicio,
el endpoint, los schemas ni la vista. La incorporación ocurre porque:

- existe una carpeta ``data/processed/openalex/`` con un ``Dataset_Procesado``
  conforme al Article Data Contract V1, y
- cada registro lleva ``source = "OpenAlex"``.

El ``BibliometriaService`` descubre cualquier subcarpeta bajo
``data/processed/`` y agrupa por el campo ``source`` de cada registro
(``bibliometria_service.py``), por lo que OpenAlex aparece en ``total_articulos``
y en ``aporte_por_fuente`` con el nombre ``"OpenAlex"`` **sin cambios de código**.

Se verifica por dos vías equivalentes (diseño, Testing Strategy):

1. Directamente vía :class:`BibliometriaService`.
2. Vía el endpoint real ``GET /bibliometria/resumen`` con ``TestClient``.

Además se comprueba que el ``Dataset_Procesado`` de **Google Scholar** (otra
fuente) sigue contándose como su propia fuente y permanece intacto (Req 6.4).

Igual que el resto de pruebas bibliométricas de integración, estos endpoints NO
usan la base de datos: el servicio lee datasets procesados de archivos. Por eso
NO se usa ``api_client`` (que inyecta sesión de BD); se monkeypatchea el
directorio de módulo ``_PROCESSED_DIR`` del servicio hacia una carpeta temporal.
Todos los datos son SINTÉTICOS (``DEMO_DATA``), nunca datos reales de SAO, y las
carpetas temporales las limpia ``tmp_path`` de pytest.

Alineado con el patrón de ``test_bibliometria_endpoints.py``. El nombre de la
fuente (``"OpenAlex"``) se importa de ``OPENALEX_SOURCE`` para no hardcodear la
etiqueta y mantener la verificación acoplada al conector real.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import backend.src.services.bibliometria_service as svc
from backend.src.main import app
from backend.src.services.bibliometria_service import BibliometriaService
from bibliometrics.ingestion.extract_openalex import OPENALEX_SOURCE

# --- Datos sintéticos (DEMO_DATA) -------------------------------------------
# Registros conformes al Article Data Contract V1 (campos usados por las
# agregaciones del servicio). NO representan artículos reales de SAO.
#
# La fuente OpenAlex lleva ``source = OPENALEX_SOURCE`` ("OpenAlex"), el valor
# fijo que produce el conector real (``extract_openalex.OPENALEX_SOURCE``).
_OPENALEX_DEMO = [
    {
        "source": OPENALEX_SOURCE,
        "title": "DEMO OpenAlex uno",
        "authors": ["Autor Alfa"],
        "abstract": "Resumen demo OpenAlex 1.",
        "keywords": ["aves", "conservación"],
        "doi": "10.0000/demo-oa-1",
        "publication_year": 2023,
        "volume": "12",
        "inclusion_status": "INCLUIDO",
        "is_duplicate": False,
    },
    {
        "source": OPENALEX_SOURCE,
        "title": "DEMO OpenAlex dos",
        "authors": ["Autor Beta"],
        "abstract": None,
        "keywords": [],
        "doi": None,
        "publication_year": 2024,
        "volume": "13",
        "inclusion_status": "PENDIENTE_REVISIÓN",
        "is_duplicate": False,
    },
    {
        "source": OPENALEX_SOURCE,
        "title": "DEMO OpenAlex tres",
        "authors": ["Autor Gamma"],
        "abstract": "Resumen demo OpenAlex 3.",
        "keywords": ["humedales"],
        "doi": "10.0000/demo-oa-3",
        "publication_year": 2023,
        "volume": "12",
        "inclusion_status": "INCLUIDO",
        "is_duplicate": True,
    },
]

# Otra fuente que debe permanecer intacta y contarse por separado (Req 6.4).
_SCHOLAR_DEMO = [
    {
        "source": "Google Scholar",
        "title": "DEMO Scholar uno",
        "authors": ["Autor Delta"],
        "abstract": "Resumen demo Scholar 1.",
        "keywords": ["aviturismo"],
        "doi": "10.0000/demo-gs-1",
        "publication_year": 2022,
        "volume": "7",
        "inclusion_status": "INCLUIDO",
        "is_duplicate": False,
    },
]


def _seed_source(
    processed_dir: Path, carpeta: str, fecha: str, registros: list
) -> None:
    """Escribe un ``Dataset_Procesado`` de fuente sintético en un subdirectorio.

    El nombre del archivo incluye la fecha ``YYYY-MM-DD`` para que el servicio
    lo descubra igual que en producción (``*_dataset_YYYY-MM-DD.json``).
    """
    carpeta_dir = processed_dir / carpeta
    carpeta_dir.mkdir(parents=True, exist_ok=True)
    archivo = carpeta_dir / f"{carpeta}_dataset_{fecha}.json"
    archivo.write_text(json.dumps(registros), encoding="utf-8")


@pytest.fixture()
def processed_con_openalex_y_scholar(tmp_path: Path, monkeypatch) -> Path:
    """Prepara un ``data/processed/`` temporal con OpenAlex + Google Scholar.

    Apunta el ``_PROCESSED_DIR`` del servicio a la carpeta temporal para que el
    descubrimiento de fuentes opere sobre datos sintéticos controlados, sin
    tocar el ``data/processed/`` real del repositorio.
    """
    processed = tmp_path / "processed"
    processed.mkdir()
    _seed_source(processed, "openalex", "2026-10-10", _OPENALEX_DEMO)
    _seed_source(processed, "google_scholar", "2026-10-09", _SCHOLAR_DEMO)
    monkeypatch.setattr(svc, "_PROCESSED_DIR", processed)
    return processed


@pytest.fixture()
def client() -> TestClient:
    """``TestClient`` de la app real, sin overrides de base de datos."""
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# 1) Vía BibliometriaService (sin HTTP)
# ---------------------------------------------------------------------------
def test_openalex_aparece_en_consolidado_via_servicio(
    processed_con_openalex_y_scholar,
):
    """OpenAlex aparece en el total y en ``aporte_por_fuente`` (Req 6.1, 6.2).

    Y Google Scholar sigue contándose como su propia fuente (Req 6.4). No se
    modifica el servicio: la fuente entra por convención (carpeta + ``source``).
    """
    resumen = BibliometriaService().resumen_consolidado()

    # --- Alcance explícito del consolidado (Req 6.4) ------------------------
    assert resumen.alcance == "consolidado"

    # --- Total = unión sin exclusión: 3 OpenAlex + 1 Scholar (Req 6.1) ------
    assert resumen.total_articulos == 4

    # --- Aporte por fuente: OpenAlex presente con su nombre exacto ----------
    aporte = {a.fuente: a for a in resumen.aporte_por_fuente}
    assert OPENALEX_SOURCE in aporte
    assert aporte[OPENALEX_SOURCE].fuente == "OpenAlex"
    assert aporte[OPENALEX_SOURCE].total_articulos == 3

    # --- Google Scholar intacto como su propia fuente (Req 6.4) -------------
    assert "Google Scholar" in aporte
    assert aporte["Google Scholar"].total_articulos == 1

    # --- No hay cruce entre fuentes: la suma de aportes == total ------------
    assert sum(a.total_articulos for a in resumen.aporte_por_fuente) == 4

    # --- El aporte de OpenAlex trae su completitud por campo (Req 7.2) ------
    campos_oa = {c.campo for c in aporte[OPENALEX_SOURCE].completitud}
    assert campos_oa == {"title", "authors", "abstract", "keywords", "doi"}


# ---------------------------------------------------------------------------
# 2) Vía endpoint GET /bibliometria/resumen (HTTP real)
# ---------------------------------------------------------------------------
def test_openalex_aparece_en_consolidado_via_endpoint(
    client, processed_con_openalex_y_scholar
):
    """El endpoint consolidado expone OpenAlex sin tocar la ruta ni el schema."""
    r = client.get("/bibliometria/resumen")
    assert r.status_code == 200, r.text
    body = r.json()

    # --- Forma consolidada estable (schema sin cambios) ---------------------
    assert body["alcance"] == "consolidado"
    assert body["total_articulos"] == 4

    # --- OpenAlex en el desglose con el nombre exacto "OpenAlex" ------------
    aporte = {a["fuente"]: a for a in body["aporte_por_fuente"]}
    assert set(aporte) == {"OpenAlex", "Google Scholar"}
    assert aporte["OpenAlex"]["total_articulos"] == 3
    assert aporte["Google Scholar"]["total_articulos"] == 1

    # --- Distribución por año combinada: 2023 x2 (OA), 2024 x1 (OA), 2022 x1 (GS)
    por_anio = {d["clave"]: d["conteo"] for d in body["por_anio"]}
    assert por_anio == {"2022": 1, "2023": 2, "2024": 1}

    # --- Pendientes y duplicados provienen de OpenAlex en este dataset ------
    assert body["pendientes_revision"] == 1  # OpenAlex dos
    assert body["posibles_duplicados"] == 1  # OpenAlex tres

    # --- La suma de aportes coincide con el total (unión sin exclusión) -----
    assert (
        aporte["OpenAlex"]["total_articulos"]
        + aporte["Google Scholar"]["total_articulos"]
        == body["total_articulos"]
    )


# ---------------------------------------------------------------------------
# 3) OpenAlex como única fuente también entra al consolidado
# ---------------------------------------------------------------------------
def test_openalex_sola_aparece_en_consolidado(tmp_path, monkeypatch):
    """Con OpenAlex como única fuente procesada, aparece en el consolidado.

    Refuerza que la incorporación no depende de la presencia de otras fuentes:
    basta la carpeta ``openalex/`` y ``source = "OpenAlex"`` (Req 6.1).
    """
    processed = tmp_path / "processed"
    processed.mkdir()
    _seed_source(processed, "openalex", "2026-10-10", _OPENALEX_DEMO)
    monkeypatch.setattr(svc, "_PROCESSED_DIR", processed)

    resumen = BibliometriaService().resumen_consolidado()

    assert resumen.total_articulos == 3
    aporte = {a.fuente: a for a in resumen.aporte_por_fuente}
    assert list(aporte) == ["OpenAlex"]
    assert aporte["OpenAlex"].total_articulos == 3
