"""Pruebas unitarias del histórico de cifras GBIF (Fase 2 biodiversidad).

Verifican, SIN acceso a red, el comportamiento del consolidado histórico:

- append sin sobrescribir cortes previos (dos cortes => dos filas),
- cabecera escrita una sola vez,
- regla de integridad: una corrida con el total ausente NO escribe 0, deja el
  campo vacío y conserva el estado de error,
- una corrida sin datos usables NO añade ninguna fila (no contamina),
- el publicador se identifica por org_key (clave estable) y el nombre es un
  atributo que puede variar entre cortes.

El script vive fuera de ``backend/``; se carga por ruta con importlib.
"""

from __future__ import annotations

import csv
import importlib.util
from pathlib import Path

# --- Carga del módulo bajo prueba por ruta -----------------------------------

_SCRIPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "biodiversity_pilot"
    / "gbif_bird_counts_history.py"
)
_spec = importlib.util.spec_from_file_location("gbif_bird_counts_history", _SCRIPT_PATH)
assert _spec is not None and _spec.loader is not None
hist = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(hist)


# --- Fábricas de reportes de ejemplo (equivalentes a la salida de run()) -----

def _report_ok(extracted_at: str, total: int, publishers: list[dict]) -> dict:
    return {
        "source": "GBIF Occurrence API",
        "extracted_at_utc": extracted_at,
        "finished_at_utc": extracted_at,
        "query_params": {
            "total_count": {"country": "CO", "taxonKey": 212, "limit": 0},
            "publisher_facet": {"country": "CO", "taxonKey": 212, "limit": 0,
                                 "facet": "publishingOrg", "facetLimit": 5},
        },
        "total_bird_records_colombia": total,
        "publisher_ranking": publishers,
        "publishers_in_ranking": len(publishers),
        "publisher_names_resolved": sum(1 for p in publishers if p.get("publisher_name")),
        "errors": [],
        "status": "completed",
    }


def _read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


# --- Pruebas -----------------------------------------------------------------

class TestAppendNoSobrescribe:
    def test_dos_cortes_producen_dos_filas_de_total(self, tmp_path):
        nat = tmp_path / "national_total_history.csv"
        pub = tmp_path / "publisher_history.csv"

        r1 = _report_ok("2026-10-21T10:00:00+00:00", 100,
                         [{"org_key": "org-a", "occurrence_count": 60,
                           "publisher_name": "Org A"}])
        r2 = _report_ok("2026-11-21T10:00:00+00:00", 110,
                         [{"org_key": "org-a", "occurrence_count": 66,
                           "publisher_name": "Org A renombrada"}])

        hist.append_to_history(r1, nat, pub)
        hist.append_to_history(r2, nat, pub)

        total_rows = _read_csv(nat)
        assert len(total_rows) == 2
        assert total_rows[0]["total_bird_records_colombia"] == "100"
        assert total_rows[1]["total_bird_records_colombia"] == "110"
        # Cabecera escrita una sola vez (no aparece repetida como dato).
        assert total_rows[0]["extracted_at_utc"] == "2026-10-21T10:00:00+00:00"

    def test_org_key_estable_nombre_puede_cambiar(self, tmp_path):
        nat = tmp_path / "national_total_history.csv"
        pub = tmp_path / "publisher_history.csv"

        r1 = _report_ok("2026-10-21T10:00:00+00:00", 100,
                         [{"org_key": "org-a", "occurrence_count": 60,
                           "publisher_name": "Nombre viejo"}])
        r2 = _report_ok("2026-11-21T10:00:00+00:00", 110,
                         [{"org_key": "org-a", "occurrence_count": 66,
                           "publisher_name": "Nombre nuevo"}])

        hist.append_to_history(r1, nat, pub)
        hist.append_to_history(r2, nat, pub)

        pub_rows = _read_csv(pub)
        assert len(pub_rows) == 2
        # Misma clave estable en ambos cortes...
        assert {row["org_key"] for row in pub_rows} == {"org-a"}
        # ...con nombres distintos conservados por corte.
        assert pub_rows[0]["publisher_name"] == "Nombre viejo"
        assert pub_rows[1]["publisher_name"] == "Nombre nuevo"


class TestIntegridadErrores:
    def test_total_ausente_no_escribe_cero(self, tmp_path):
        nat = tmp_path / "national_total_history.csv"
        pub = tmp_path / "publisher_history.csv"

        # Total falló pero el ranking sí llegó (corrida parcial).
        report = _report_ok("2026-10-21T10:00:00+00:00", 100,
                             [{"org_key": "org-a", "occurrence_count": 60,
                               "publisher_name": "Org A"}])
        report["total_bird_records_colombia"] = None
        report["status"] = "completed_with_errors"
        report["errors"] = ["total_count: HTTP 500 en ..."]

        result = hist.append_to_history(report, nat, pub)
        assert result["appended"] is True

        row = _read_csv(nat)[0]
        # Campo VACÍO, nunca "0".
        assert row["total_bird_records_colombia"] == ""
        assert row["status"] == "completed_with_errors"
        assert "total_count" in row["errors"]

    def test_corrida_vacia_no_contamina_historico(self, tmp_path):
        nat = tmp_path / "national_total_history.csv"
        pub = tmp_path / "publisher_history.csv"

        report = _report_ok("2026-10-21T10:00:00+00:00", 100, [])
        report["total_bird_records_colombia"] = None
        report["publisher_ranking"] = []
        report["status"] = "completed_with_errors"
        report["errors"] = ["total_count: ...", "publisher_facet: ..."]

        result = hist.append_to_history(report, nat, pub)
        assert result["appended"] is False
        # No se crea ningún archivo de histórico.
        assert not nat.exists()
        assert not pub.exists()

    def test_corrida_valida_tras_fallida_preserva_ambas(self, tmp_path):
        """Una corrida fallida (parcial) no borra ni reemplaza una válida previa."""
        nat = tmp_path / "national_total_history.csv"
        pub = tmp_path / "publisher_history.csv"

        ok = _report_ok("2026-10-21T10:00:00+00:00", 100,
                        [{"org_key": "org-a", "occurrence_count": 60,
                          "publisher_name": "Org A"}])
        partial = _report_ok("2026-11-21T10:00:00+00:00", 100,
                             [{"org_key": "org-a", "occurrence_count": 60,
                               "publisher_name": "Org A"}])
        partial["total_bird_records_colombia"] = None
        partial["status"] = "completed_with_errors"
        partial["errors"] = ["total_count: timeout"]

        hist.append_to_history(ok, nat, pub)
        hist.append_to_history(partial, nat, pub)

        rows = _read_csv(nat)
        assert len(rows) == 2
        # La cifra válida del primer corte permanece intacta.
        assert rows[0]["total_bird_records_colombia"] == "100"
        assert rows[1]["total_bird_records_colombia"] == ""


class TestHasUsableData:
    def test_con_total_es_usable(self):
        assert hist.has_usable_data({"total_bird_records_colombia": 5,
                                     "publisher_ranking": []}) is True

    def test_con_ranking_es_usable(self):
        assert hist.has_usable_data({"total_bird_records_colombia": None,
                                     "publisher_ranking": [{"org_key": "x"}]}) is True

    def test_sin_nada_no_es_usable(self):
        assert hist.has_usable_data({"total_bird_records_colombia": None,
                                     "publisher_ranking": []}) is False
