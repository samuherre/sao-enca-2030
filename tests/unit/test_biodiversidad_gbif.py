"""Pruebas del backend de la vista de biodiversidad — Datos de GBIF.

Cubren el servicio (``BiodiversidadService``) y los dos endpoints, SIN acceso a
red y SIN tocar los artefactos reales del repositorio:

- ``resumen_almacenado`` lee el último corte y el histórico desde un directorio
  temporal (se parchean las rutas del módulo del servicio).
- La consulta ``en_vivo`` se prueba parcheando ``run`` del módulo de Fase 1, para
  no llamar a GBIF; se verifica que el resultado se marca ``origen="en_vivo"`` y
  que NO escribe archivos.
- El endpoint GET responde 404 cuando no hay artefactos (principio de no
  invención: no se fabrica un resumen vacío con ceros).

El servicio no usa base de datos; se reutiliza el ``client`` del conftest, cuyo
override de ``get_db`` es inocuo para estas rutas.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.src.services import biodiversidad_service as svc
from backend.src.services.biodiversidad_service import BiodiversidadService


# --- Datos de prueba ---------------------------------------------------------

_REPORT = {
    "source": "GBIF Occurrence API",
    "source_base_url": "https://api.gbif.org/v1",
    "extracted_at_utc": "2026-10-21T18:48:51.928093+00:00",
    "finished_at_utc": "2026-10-21T18:49:01.614127+00:00",
    "total_bird_records_colombia": 26753542,
    "publisher_ranking": [
        {
            "org_key": "e2e717bf-551a-4917-bdc9-4fa0f342c530",
            "occurrence_count": 24154885,
            "publisher_name": "Cornell Lab of Ornithology",
        },
        {
            "org_key": "sin-nombre-key",
            "occurrence_count": 100,
            "publisher_name": None,  # GBIF no resolvió el nombre: no se inventa
        },
    ],
    "publishers_in_ranking": 2,
    "errors": [],
    "status": "completed",
    "notes": "Conteos agregados de GBIF (limit=0 + facet).",
}

_HISTORY_CSV = (
    "extracted_at_utc,finished_at_utc,status,total_bird_records_colombia,"
    "publishers_in_ranking,source,country,taxon_key,errors\n"
    "2026-10-21T17:45:51.364310+00:00,2026-10-21T17:45:55.678198+00:00,completed,"
    "26753542,5,GBIF Occurrence API,CO,212,\n"
    "2026-10-21T18:48:51.928093+00:00,2026-10-21T18:49:01.614127+00:00,completed,"
    "26753542,5,GBIF Occurrence API,CO,212,\n"
)


@pytest.fixture()
def gbif_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Prepara un directorio GBIF temporal y redirige las rutas del servicio."""
    gbif = tmp_path / "gbif"
    history = gbif / "history"
    arcgis = gbif / "arcgis"
    history.mkdir(parents=True)
    arcgis.mkdir(parents=True)

    corte = gbif / "bird_record_counts_20261021T184851Z.json"
    corte.write_text(json.dumps(_REPORT), encoding="utf-8")
    (history / "national_total_history.csv").write_text(_HISTORY_CSV, encoding="utf-8-sig")
    (arcgis / "national_total_arcgis.csv").write_text(
        "snapshot_date,total_bird_records\n2026-10-21,26753542\n", encoding="utf-8-sig"
    )

    # Redirige TODAS las rutas que el servicio resuelve a nivel de módulo.
    monkeypatch.setattr(svc, "_GBIF_DIR", gbif)
    monkeypatch.setattr(svc, "_HISTORY_DIR", history)
    monkeypatch.setattr(svc, "_NATIONAL_TOTAL_HISTORY", history / "national_total_history.csv")
    monkeypatch.setattr(svc, "_ARCGIS_DIR", arcgis)
    monkeypatch.setattr(svc, "_REPO_ROOT", tmp_path)
    return gbif


# --- Servicio: resumen almacenado --------------------------------------------

def test_resumen_almacenado_lee_ultimo_corte(gbif_dir: Path) -> None:
    resumen = BiodiversidadService().resumen_almacenado()

    assert resumen.origen == "almacenado"
    assert resumen.total_registros_ocurrencia == 26753542
    assert resumen.estado == "completed"
    # Ranking: rangos correlativos y nombre None preservado (no inventado).
    assert [p.rank for p in resumen.publicadores] == [1, 2]
    assert resumen.publicadores[0].nombre == "Cornell Lab of Ornithology"
    assert resumen.publicadores[1].nombre is None
    # Histórico leído (2 cortes) y exportaciones listadas (1 CSV).
    assert resumen.cortes_historicos == 2
    assert len(resumen.historico) == 2
    assert len(resumen.exportaciones) == 1
    assert resumen.exportaciones[0].nombre == "national_total_arcgis.csv"


def test_resumen_almacenado_sin_artefactos_lanza_not_found(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from backend.src.domain.exceptions import NotFoundError

    vacio = tmp_path / "gbif_vacio"
    vacio.mkdir()
    monkeypatch.setattr(svc, "_GBIF_DIR", vacio)

    with pytest.raises(NotFoundError):
        BiodiversidadService().resumen_almacenado()


# --- Servicio: consulta en vivo (sin red) ------------------------------------

def test_consulta_en_vivo_usa_run_y_no_escribe(
    gbif_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    llamadas: dict[str, object] = {}

    def _fake_run(facet_limit: int, timeout: int, resolve_names: bool):
        llamadas["facet_limit"] = facet_limit
        llamadas["resolve_names"] = resolve_names
        return dict(_REPORT)

    # Parchea el módulo de Fase 1 que carga el servicio por importlib.
    fake_modulo = type("M", (), {"run": staticmethod(_fake_run)})
    monkeypatch.setattr(svc, "_cargar_modulo_fase1", lambda: fake_modulo)

    archivos_antes = {p.name for p in gbif_dir.glob("*")}
    resumen = BiodiversidadService().consulta_en_vivo()
    archivos_despues = {p.name for p in gbif_dir.glob("*")}

    assert resumen.origen == "en_vivo"
    assert resumen.total_registros_ocurrencia == 26753542
    assert llamadas["resolve_names"] is True
    # No se creó ningún artefacto nuevo: la consulta en vivo no persiste.
    assert archivos_antes == archivos_despues


# --- Endpoints ---------------------------------------------------------------

def test_endpoint_resumen_404_sin_artefactos(
    client, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    vacio = tmp_path / "gbif_vacio"
    vacio.mkdir()
    monkeypatch.setattr(svc, "_GBIF_DIR", vacio)

    resp = client.get("/biodiversidad/gbif/resumen")
    assert resp.status_code == 404
    body = resp.json()
    assert body["error"] == "not_found"


def test_endpoint_resumen_ok(client, gbif_dir: Path) -> None:
    resp = client.get("/biodiversidad/gbif/resumen")
    assert resp.status_code == 200
    body = resp.json()
    assert body["origen"] == "almacenado"
    assert body["total_registros_ocurrencia"] == 26753542
    assert body["grupo_taxonomico"].startswith("Aves")
    assert body["cobertura_geografica"].startswith("Colombia")


def test_endpoint_consultar_en_vivo_falla_sin_cifras(
    client, monkeypatch: pytest.MonkeyPatch
) -> None:
    # run() devuelve un report sin total ni ranking (p. ej. fallo de red).
    report_vacio = {
        "extracted_at_utc": "2026-10-22T00:00:00+00:00",
        "finished_at_utc": "2026-10-22T00:00:05+00:00",
        "total_bird_records_colombia": None,
        "publisher_ranking": [],
        "errors": ["total_count: Error de red/timeout"],
        "status": "completed_with_errors",
    }
    fake_modulo = type("M", (), {"run": staticmethod(lambda **_: dict(report_vacio))})
    monkeypatch.setattr(svc, "_cargar_modulo_fase1", lambda: fake_modulo)

    resp = client.post("/biodiversidad/gbif/consultar")
    assert resp.status_code == 422
    assert resp.json()["error"] == "gbif_query_failed"
