"""Pruebas unitarias del exportador a ArcGIS (Fase 3, preparación local).

Verifican, sin red y sobre archivos temporales:

- la fecha se normaliza a YYYY-MM-DD (snapshot_date) y se conserva el timestamp,
- un total ausente se exporta VACÍO, nunca como 0 (no invención),
- el org_key (clave estable) se conserva y el nombre puede variar por corte,
- si no hay histórico, se lanza ExportError,
- los CSV de salida respetan el contrato de campos,
- no se inventan coordenadas (los contratos no tienen campos de geometría).

El script vive fuera de backend/; se carga por ruta con importlib.
"""

from __future__ import annotations

import csv
import importlib.util
from pathlib import Path

import pytest

_SCRIPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "biodiversity_pilot"
    / "export_for_arcgis.py"
)
_spec = importlib.util.spec_from_file_location("export_for_arcgis", _SCRIPT_PATH)
assert _spec is not None and _spec.loader is not None
exp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(exp)


def _write(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _read(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


# --- snapshot_date -----------------------------------------------------------

class TestSnapshotDate:
    def test_iso_completo_da_fecha(self):
        assert exp._snapshot_date("2026-10-21T17:45:51.364310+00:00") == "2026-10-21"

    def test_vacio_o_invalido_da_cadena_vacia(self):
        assert exp._snapshot_date("") == ""
        assert exp._snapshot_date(None) == ""
        assert exp._snapshot_date("no-es-fecha") == ""


# --- Transformaciones --------------------------------------------------------

class TestTransformNationalTotal:
    def test_mapea_campos_y_estado(self):
        rows = [
            {
                "extracted_at_utc": "2026-10-21T17:45:51.364310+00:00",
                "status": "completed",
                "total_bird_records_colombia": "26753542",
                "publishers_in_ranking": "5",
                "source": "GBIF Occurrence API",
                "country": "CO",
                "taxon_key": "212",
                "errors": "",
            }
        ]
        out = exp.transform_national_total(rows)[0]
        assert out["snapshot_date"] == "2026-10-21"
        assert out["total_bird_records"] == "26753542"
        assert out["run_status"] == "completed"
        assert out["country"] == "CO"
        assert out["taxon_key"] == "212"

    def test_total_ausente_queda_vacio_no_cero(self):
        rows = [
            {
                "extracted_at_utc": "2026-11-21T10:00:00+00:00",
                "status": "completed_with_errors",
                "total_bird_records_colombia": "",
                "publishers_in_ranking": "5",
                "source": "GBIF Occurrence API",
                "country": "CO",
                "taxon_key": "212",
                "errors": "total_count: timeout",
            }
        ]
        out = exp.transform_national_total(rows)[0]
        assert out["total_bird_records"] == ""   # nunca "0"
        assert out["run_status"] == "completed_with_errors"


class TestTransformPublisher:
    def test_org_key_estable_nombre_variable(self):
        rows = [
            {"extracted_at_utc": "2026-10-21T10:00:00+00:00", "status": "completed",
             "rank": "1", "org_key": "org-a", "publisher_name": "Nombre viejo",
             "occurrence_count": "100"},
            {"extracted_at_utc": "2026-11-21T10:00:00+00:00", "status": "completed",
             "rank": "1", "org_key": "org-a", "publisher_name": "Nombre nuevo",
             "occurrence_count": "110"},
        ]
        out = exp.transform_publisher(rows)
        assert {r["org_key"] for r in out} == {"org-a"}
        assert out[0]["publisher_name"] == "Nombre viejo"
        assert out[1]["publisher_name"] == "Nombre nuevo"
        assert out[0]["snapshot_date"] == "2026-10-21"


# --- No invención de geometría ----------------------------------------------

class TestSinGeometria:
    def test_contratos_no_tienen_campos_de_coordenadas(self):
        prohibidos = {"lat", "latitude", "lon", "lng", "longitude", "x", "y",
                      "geometry", "shape"}
        for field in exp.NATIONAL_TOTAL_OUT_FIELDS + exp.PUBLISHER_OUT_FIELDS:
            assert field.lower() not in prohibidos


# --- export() end-to-end sobre archivos temporales ---------------------------

class TestExport:
    def _seed_history(self, tmp_path: Path) -> tuple[Path, Path]:
        nat_in = tmp_path / "history" / "national_total_history.csv"
        pub_in = tmp_path / "history" / "publisher_history.csv"
        _write(
            nat_in,
            ["extracted_at_utc", "finished_at_utc", "status",
             "total_bird_records_colombia", "publishers_in_ranking", "source",
             "country", "taxon_key", "errors"],
            [{
                "extracted_at_utc": "2026-10-21T17:45:51.364310+00:00",
                "finished_at_utc": "2026-10-21T17:45:55.678198+00:00",
                "status": "completed", "total_bird_records_colombia": "26753542",
                "publishers_in_ranking": "5", "source": "GBIF Occurrence API",
                "country": "CO", "taxon_key": "212", "errors": "",
            }],
        )
        _write(
            pub_in,
            ["extracted_at_utc", "status", "rank", "org_key", "publisher_name",
             "occurrence_count"],
            [{
                "extracted_at_utc": "2026-10-21T17:45:51.364310+00:00",
                "status": "completed", "rank": "1", "org_key": "org-a",
                "publisher_name": "Org A", "occurrence_count": "24154885",
            }],
        )
        return nat_in, pub_in

    def test_export_escribe_ambos_csv(self, tmp_path):
        nat_in, pub_in = self._seed_history(tmp_path)
        nat_out = tmp_path / "arcgis" / "national_total_arcgis.csv"
        pub_out = tmp_path / "arcgis" / "publisher_counts_arcgis.csv"

        result = exp.export(nat_in, pub_in, nat_out, pub_out, write=True)
        assert result["national_total_rows"] == 1
        assert result["publisher_rows"] == 1
        assert nat_out.exists() and pub_out.exists()

        nat_data = _read(nat_out)[0]
        assert nat_data["snapshot_date"] == "2026-10-21"
        assert nat_data["total_bird_records"] == "26753542"
        assert list(nat_data.keys()) == exp.NATIONAL_TOTAL_OUT_FIELDS

        pub_data = _read(pub_out)[0]
        assert pub_data["org_key"] == "org-a"
        assert list(pub_data.keys()) == exp.PUBLISHER_OUT_FIELDS

    def test_dry_run_no_escribe(self, tmp_path):
        nat_in, pub_in = self._seed_history(tmp_path)
        nat_out = tmp_path / "arcgis" / "national_total_arcgis.csv"
        pub_out = tmp_path / "arcgis" / "publisher_counts_arcgis.csv"
        result = exp.export(nat_in, pub_in, nat_out, pub_out, write=False)
        assert result["written"] is False
        assert not nat_out.exists() and not pub_out.exists()

    def test_sin_historico_lanza_error(self, tmp_path):
        with pytest.raises(exp.ExportError):
            exp.export(
                tmp_path / "no.csv", tmp_path / "no2.csv",
                tmp_path / "o1.csv", tmp_path / "o2.csv", write=True,
            )
