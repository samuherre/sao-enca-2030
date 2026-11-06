"""Pruebas unitarias del script de cifras GBIF (Fase 1 biodiversidad).

Objetivo: verificar el comportamiento del recolector de cifras de aves de GBIF
SIN acceso a red. Se parchea ``_get_json`` para simular respuestas de la API y
se comprueban:

- parseo del total y del ranking de publicadores,
- resolución de orgKey -> nombre (y su ausencia sin inventar),
- manejo de errores (una consulta falla, la otra continúa),
- principio de no invención (campos no detectados => null),
- que no se descargan ocurrencias (los parámetros usan limit=0 + facet).

El script vive fuera de ``backend/``; se carga por ruta con importlib para no
depender del paquete de backend ni de la base de datos.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

# --- Carga del módulo bajo prueba por ruta de archivo ------------------------

_SCRIPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "biodiversity_pilot"
    / "gbif_bird_counts.py"
)

_spec = importlib.util.spec_from_file_location("gbif_bird_counts", _SCRIPT_PATH)
assert _spec is not None and _spec.loader is not None
gbc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gbc)


# --- Dobles de prueba para _get_json -----------------------------------------

def _fake_api(responses: dict[str, object]):
    """Devuelve un sustituto de _get_json que responde por substring de URL."""

    def _fake(url: str, params: dict, timeout: int):
        if "/organization/" in url:
            key = url.rsplit("/", 1)[-1]
            value = responses.get(f"org:{key}")
            if isinstance(value, Exception):
                raise value
            return value
        if params.get("facet") == "publishingOrg":
            value = responses["facet"]
        else:
            value = responses["total"]
        if isinstance(value, Exception):
            raise value
        return value

    return _fake


# --- Pruebas de parseo del total ---------------------------------------------

class TestFetchTotalCount:
    def test_devuelve_count_entero(self, monkeypatch):
        monkeypatch.setattr(gbc, "_get_json", _fake_api({"total": {"count": 42}}))
        count, params = gbc.fetch_total_count(timeout=5)
        assert count == 42
        # No se descargan ocurrencias: limit=0.
        assert params["limit"] == 0
        assert params["country"] == "CO"
        assert params["taxonKey"] == 212

    def test_falta_count_lanza_error(self, monkeypatch):
        monkeypatch.setattr(gbc, "_get_json", _fake_api({"total": {"otro": 1}}))
        with pytest.raises(gbc.GbifError):
            gbc.fetch_total_count(timeout=5)

    def test_count_no_entero_lanza_error(self, monkeypatch):
        monkeypatch.setattr(gbc, "_get_json", _fake_api({"total": {"count": "x"}}))
        with pytest.raises(gbc.GbifError):
            gbc.fetch_total_count(timeout=5)


# --- Pruebas del ranking de publicadores -------------------------------------

class TestFetchPublisherFacet:
    def test_parsea_ranking(self, monkeypatch):
        facet = {
            "facets": [
                {
                    "field": "PUBLISHING_ORG",
                    "counts": [
                        {"name": "org-a", "count": 100},
                        {"name": "org-b", "count": 50},
                    ],
                }
            ]
        }
        monkeypatch.setattr(gbc, "_get_json", _fake_api({"facet": facet}))
        ranking, params = gbc.fetch_publisher_facet(facet_limit=10, timeout=5)
        assert ranking == [
            {"org_key": "org-a", "occurrence_count": 100},
            {"org_key": "org-b", "occurrence_count": 50},
        ]
        assert params["limit"] == 0
        assert params["facet"] == "publishingOrg"

    def test_sin_facetas_devuelve_lista_vacia(self, monkeypatch):
        monkeypatch.setattr(gbc, "_get_json", _fake_api({"facet": {"facets": []}}))
        ranking, _ = gbc.fetch_publisher_facet(facet_limit=10, timeout=5)
        assert ranking == []

    def test_omite_entradas_malformadas_sin_inventar(self, monkeypatch):
        facet = {
            "facets": [
                {
                    "counts": [
                        {"name": "org-a", "count": 100},
                        {"name": None, "count": 10},      # sin orgKey
                        {"name": "org-c", "count": "n/a"},  # conteo no entero
                    ]
                }
            ]
        }
        monkeypatch.setattr(gbc, "_get_json", _fake_api({"facet": facet}))
        ranking, _ = gbc.fetch_publisher_facet(facet_limit=10, timeout=5)
        assert ranking == [{"org_key": "org-a", "occurrence_count": 100}]


# --- Resolución de nombres de publicador -------------------------------------

class TestResolvePublisherName:
    def test_resuelve_titulo(self, monkeypatch):
        monkeypatch.setattr(
            gbc, "_get_json", _fake_api({"org:org-a": {"title": "Instituto X"}})
        )
        assert gbc.resolve_publisher_name("org-a", timeout=5) == "Instituto X"

    def test_sin_titulo_devuelve_none(self, monkeypatch):
        monkeypatch.setattr(gbc, "_get_json", _fake_api({"org:org-a": {}}))
        assert gbc.resolve_publisher_name("org-a", timeout=5) is None

    def test_error_api_devuelve_none_sin_inventar(self, monkeypatch):
        monkeypatch.setattr(
            gbc, "_get_json", _fake_api({"org:org-a": gbc.GbifError("boom")})
        )
        assert gbc.resolve_publisher_name("org-a", timeout=5) is None


# --- Orquestación: run() -----------------------------------------------------

class TestRun:
    def test_corrida_completa_feliz(self, monkeypatch):
        responses = {
            "total": {"count": 26_000_000},
            "facet": {
                "facets": [
                    {"counts": [{"name": "org-a", "count": 24_000_000}]}
                ]
            },
            "org:org-a": {"title": "Cornell Lab eBird"},
        }
        monkeypatch.setattr(gbc, "_get_json", _fake_api(responses))
        report = gbc.run(facet_limit=10, timeout=5, resolve_names=True)

        assert report["status"] == "completed"
        assert report["errors"] == []
        assert report["total_bird_records_colombia"] == 26_000_000
        assert report["publishers_in_ranking"] == 1
        assert report["publisher_names_resolved"] == 1
        assert report["publisher_ranking"][0]["publisher_name"] == "Cornell Lab eBird"

    def test_error_en_total_no_impide_ranking(self, monkeypatch):
        responses = {
            "total": gbc.GbifError("HTTP 500"),
            "facet": {
                "facets": [{"counts": [{"name": "org-a", "count": 10}]}]
            },
            "org:org-a": {"title": "Org A"},
        }
        monkeypatch.setattr(gbc, "_get_json", _fake_api(responses))
        report = gbc.run(facet_limit=10, timeout=5, resolve_names=True)

        assert report["status"] == "completed_with_errors"
        assert report["total_bird_records_colombia"] is None  # no se inventa
        assert any("total_count" in e for e in report["errors"])
        assert report["publishers_in_ranking"] == 1

    def test_no_resolver_nombres_deja_none(self, monkeypatch):
        responses = {
            "total": {"count": 5},
            "facet": {"facets": [{"counts": [{"name": "org-a", "count": 5}]}]},
        }
        monkeypatch.setattr(gbc, "_get_json", _fake_api(responses))
        report = gbc.run(facet_limit=10, timeout=5, resolve_names=False)
        assert report["publisher_names_resolved"] == 0
        assert report["publisher_ranking"][0]["publisher_name"] is None


# --- Escritura de salidas (sin red, en carpeta temporal) ---------------------

class TestWriteOutputs:
    def test_escribe_csv_y_json_sin_sobrescribir_piloto(self, tmp_path):
        from datetime import datetime, timezone

        now = datetime(2026, 10, 21, 16, 0, 0, tzinfo=timezone.utc)
        ranking = [
            {"org_key": "org-a", "occurrence_count": 100, "publisher_name": "Org A"},
            {"org_key": "org-b", "occurrence_count": 50, "publisher_name": None},
        ]
        report = {"total_bird_records_colombia": 150, "publisher_ranking": ranking}
        paths = gbc.write_outputs(tmp_path, now, report, ranking)

        csv_path = Path(paths["csv"])
        json_path = Path(paths["json"])
        assert csv_path.exists() and json_path.exists()
        # Nombres nuevos: no colisionan con occurrences.csv / summary.json.
        assert csv_path.name.startswith("bird_record_counts_")
        assert "20261021T160000Z" in csv_path.name

        content = csv_path.read_text(encoding="utf-8-sig")
        assert "rank,org_key,publisher_name,occurrence_count" in content
        assert "1,org-a,Org A,100" in content
        # publisher_name None => columna vacía, no la cadena "None".
        assert "2,org-b,,50" in content
