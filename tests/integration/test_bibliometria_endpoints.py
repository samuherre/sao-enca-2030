"""Integración 7.2 — Endpoints bibliométricos vía ``TestClient``.

Ejercita los endpoints reales de FastAPI del Componente B (Req 8.1–8.4):

- ``GET /bibliometria/resumen`` — resumen CONSOLIDADO de todas las fuentes
  descubiertas bajo ``data/processed/``. Dos escenarios:
  1. Con datasets de ejemplo sintéticos → la respuesta 200 cumple la forma
     (shape) definida en los Requisitos 6 y 7 (``alcance == "consolidado"``,
     ``total_articulos``, ``por_anio``, ``por_volumen``, ``completitud``,
     ``pendientes_revision``, ``posibles_duplicados``, ``aporte_por_fuente`` con
     ``completitud`` por fuente, etc.).
  2. Sin datasets → 200 con un resumen vacío coherente (estado vacío honesto,
     Req 8.3): ``total_articulos == 0`` y distribuciones vacías.
- ``GET /bibliometria/boletin-sao/resumen`` — la ruta del Boletín SAO sigue
  operativa durante la transición (Req 8.4): responde 200 con datos reales si
  existe dataset y 404 (``NotFoundError``) cuando su carpeta está vacía.

Estos endpoints NO usan la base de datos: el servicio lee datasets procesados
de archivos. Por eso estas pruebas NO usan ``api_client`` (que inyecta la
sesión de BD); construyen su propio ``TestClient`` y controlan los datasets
monkeypatcheando los directorios de módulo del servicio hacia carpetas
temporales. Todos los datos son SINTÉTICOS (``DEMO_DATA``), nunca datos reales
de SAO, y las carpetas temporales las limpia ``tmp_path`` de pytest.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import backend.src.services.bibliometria_service as svc
from backend.src.main import app

# --- Datos sintéticos (DEMO_DATA) -------------------------------------------
# Dos fuentes con registros conformes al Article Data Contract V1 (campos
# usados por las agregaciones del servicio). No representan artículos reales.
_BOLETIN_DEMO = [
    {
        "source": "Boletín SAO",
        "title": "DEMO artículo A",
        "authors": ["Autor Uno"],
        "abstract": "Resumen demo A.",
        "keywords": ["aves"],
        "doi": "10.0000/demo-a",
        "publication_year": 2021,
        "volume": "31",
        "inclusion_status": "INCLUIDO",
        "is_duplicate": False,
    },
    {
        "source": "Boletín SAO",
        "title": "DEMO artículo B",
        "authors": ["Autor Dos"],
        "abstract": None,
        "keywords": [],
        "doi": None,
        "publication_year": 2022,
        "volume": "32",
        "inclusion_status": "PENDIENTE_REVISIÓN",
        "is_duplicate": False,
    },
]

_SCHOLAR_DEMO = [
    {
        "source": "Google Scholar",
        "title": "DEMO artículo C",
        "authors": ["Autor Tres"],
        "abstract": "Resumen demo C.",
        "keywords": ["conservación"],
        "doi": "10.0000/demo-c",
        "publication_year": 2021,
        "volume": "5",
        "inclusion_status": "INCLUIDO",
        "is_duplicate": True,
    },
]


def _seed_source(processed_dir: Path, carpeta: str, fecha: str, registros: list) -> None:
    """Escribe un Dataset_Procesado de fuente sintético en un subdirectorio.

    El nombre del archivo incluye la fecha ``YYYY-MM-DD`` para que el servicio
    lo descubra y extraiga ``fechas_dataset`` igual que en producción.
    """
    carpeta_dir = processed_dir / carpeta
    carpeta_dir.mkdir(parents=True, exist_ok=True)
    archivo = carpeta_dir / f"{carpeta}_dataset_{fecha}.json"
    archivo.write_text(json.dumps(registros), encoding="utf-8")


@pytest.fixture()
def client() -> TestClient:
    """``TestClient`` de la app real, sin overrides de base de datos.

    Los endpoints bibliométricos no dependen de ``get_db``; basta con la app.
    """
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# GET /bibliometria/resumen — con datasets de ejemplo (shape Req 6 y 7)
# ---------------------------------------------------------------------------
def test_resumen_consolidado_con_datasets_cumple_shape(client, tmp_path, monkeypatch):
    """Con dos fuentes sintéticas responde 200 y la forma de Req 6 y 7."""
    processed = tmp_path / "processed"
    processed.mkdir()
    _seed_source(processed, "boletin_sao", "2026-10-08", _BOLETIN_DEMO)
    _seed_source(processed, "google_scholar", "2026-10-09", _SCHOLAR_DEMO)

    # El servicio descubre las fuentes bajo _PROCESSED_DIR (global del módulo).
    monkeypatch.setattr(svc, "_PROCESSED_DIR", processed)

    r = client.get("/bibliometria/resumen")
    assert r.status_code == 200, r.text
    body = r.json()

    # --- Alcance explícito del consolidado (Req 6.4) ------------------------
    assert body["alcance"] == "consolidado"

    # --- Total = unión sin exclusión de ambas fuentes (Req 6.1) -------------
    assert body["total_articulos"] == 3

    # --- Distribución por año (Req 6.2): 2021 x2 (A + C), 2022 x1 (B) -------
    por_anio = {d["clave"]: d["conteo"] for d in body["por_anio"]}
    assert por_anio == {"2021": 2, "2022": 1}

    # --- Distribución por volumen (Req 6.2): 31, 32, 5 ----------------------
    por_volumen = {d["clave"]: d["conteo"] for d in body["por_volumen"]}
    assert por_volumen == {"31": 1, "32": 1, "5": 1}

    # --- Completitud por campo sobre el conjunto combinado (Req 6.2) --------
    completitud = {c["campo"]: c for c in body["completitud"]}
    assert set(completitud) == {"title", "authors", "abstract", "keywords", "doi"}
    for campo in completitud.values():
        assert campo["total"] == 3
        assert 0 <= campo["con_dato"] <= 3
    # title/authors presentes en los 3; abstract/doi en 2 (B los tiene en None).
    assert completitud["title"]["con_dato"] == 3
    assert completitud["abstract"]["con_dato"] == 2
    assert completitud["doi"]["con_dato"] == 2

    # --- Pendientes y posibles duplicados (Req 6.2) -------------------------
    assert body["pendientes_revision"] == 1  # B
    assert body["posibles_duplicados"] == 1  # C

    # --- Fechas de dataset por fuente (una por cada fuente fechada) ---------
    assert body["fechas_dataset"] == ["2026-10-08", "2026-10-09"]

    # --- Sin dataset clasificado: sin OFC (PENDING_VALIDATION) --------------
    assert body["clasificacion_disponible"] is False
    assert body["por_ofc"] == []

    # --- Aporte por fuente como información complementaria (Req 7) ----------
    aporte = {a["fuente"]: a for a in body["aporte_por_fuente"]}
    assert set(aporte) == {"Boletín SAO", "Google Scholar"}
    assert aporte["Boletín SAO"]["total_articulos"] == 2
    assert aporte["Google Scholar"]["total_articulos"] == 1
    # El aporte de cada fuente trae su propia completitud por campo (Req 7.2).
    for a in aporte.values():
        campos = {c["campo"] for c in a["completitud"]}
        assert campos == {"title", "authors", "abstract", "keywords", "doi"}
    assert (
        aporte["Boletín SAO"]["total_articulos"]
        + aporte["Google Scholar"]["total_articulos"]
        == body["total_articulos"]
    )


# ---------------------------------------------------------------------------
# GET /bibliometria/resumen — sin datasets (estado vacío honesto, Req 8.3)
# ---------------------------------------------------------------------------
def test_resumen_consolidado_sin_datasets_estado_vacio(client, tmp_path, monkeypatch):
    """Sin ninguna fuente responde 200 con un resumen vacío coherente."""
    vacio = tmp_path / "processed_vacio"
    vacio.mkdir()
    monkeypatch.setattr(svc, "_PROCESSED_DIR", vacio)

    r = client.get("/bibliometria/resumen")
    assert r.status_code == 200, r.text
    body = r.json()

    assert body["alcance"] == "consolidado"
    assert body["total_articulos"] == 0
    assert body["por_anio"] == []
    assert body["por_volumen"] == []
    assert body["pendientes_revision"] == 0
    assert body["posibles_duplicados"] == 0
    assert body["fechas_dataset"] == []
    assert body["clasificacion_disponible"] is False
    assert body["por_ofc"] == []
    assert body["aporte_por_fuente"] == []
    # La completitud lista los campos aun sin registros, con total 0.
    for campo in body["completitud"]:
        assert campo["total"] == 0
        assert campo["con_dato"] == 0


# ---------------------------------------------------------------------------
# GET /bibliometria/boletin-sao/resumen — sigue operativa (Req 8.4)
# ---------------------------------------------------------------------------
def test_boletin_sao_resumen_con_dataset_responde_200(client, tmp_path, monkeypatch):
    """Con dataset del Boletín, la ruta de compatibilidad responde 200."""
    dataset_dir = tmp_path / "boletin_sao"
    dataset_dir.mkdir()
    archivo = dataset_dir / "boletin_sao_dataset_2026-10-08.json"
    archivo.write_text(json.dumps(_BOLETIN_DEMO), encoding="utf-8")

    clasificado_dir = tmp_path / "boletin_sao_clasificado"  # vacío → sin OFC

    # resumen() lee directamente estos globals de módulo.
    monkeypatch.setattr(svc, "_DATASET_DIR", dataset_dir)
    monkeypatch.setattr(svc, "_CLASIFICADO_DIR", clasificado_dir)

    r = client.get("/bibliometria/boletin-sao/resumen")
    assert r.status_code == 200, r.text
    body = r.json()

    assert body["fuente"] == "Boletín SAO"
    assert body["total_articulos"] == 2
    assert body["fecha_dataset"] == "2026-10-08"
    assert body["pendientes_revision"] == 1
    assert body["clasificacion_disponible"] is False


def test_boletin_sao_resumen_sin_dataset_responde_404(client, tmp_path, monkeypatch):
    """Sin dataset del Boletín, la ruta responde 404 (NotFoundError)."""
    dataset_dir = tmp_path / "boletin_sao_vacio"  # no se crea → inexistente
    monkeypatch.setattr(svc, "_DATASET_DIR", dataset_dir)

    r = client.get("/bibliometria/boletin-sao/resumen")
    assert r.status_code == 404, r.text
