"""Pruebas unitarias del publicador a ArcGIS (Fase 3, Camino 3).

Verifican SIN red y SIN el paquete `arcgis` instalado:

- la configuración se lee del entorno y se detectan variables faltantes,
- la contraseña nunca aparece en los mensajes de error,
- la publicación usa truncate+append (delete_features where 1=1, luego adds) y
  opera sobre un item EXISTENTE por id (no crea items),
- el run log registra SIEMPRE la ejecución, publique o no,
- la credencial se inyecta vía `connect` (GIS simulado); no se toca ArcGIS real.

La subida real contra la cuenta de SAO NO se prueba aquí: requiere credenciales
y el paquete `arcgis`. Se valida manualmente al ejecutarlo con secrets reales.
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
    / "publish_to_arcgis.py"
)
_spec = importlib.util.spec_from_file_location("publish_to_arcgis", _SCRIPT_PATH)
assert _spec is not None and _spec.loader is not None
pub = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pub)


# --- Dobles de prueba: un GIS/tabla/item simulados ---------------------------

class _FakeTable:
    def __init__(self):
        self.deleted_where = None
        self.added = None

    def delete_features(self, where):
        self.deleted_where = where

    def edit_features(self, adds):
        self.added = adds
        return {"addResults": [{"success": True} for _ in adds]}


class _FakeItem:
    def __init__(self, table):
        self.tables = [table]


class _FakeContent:
    def __init__(self, items):
        self._items = items

    def get(self, item_id):
        return self._items.get(item_id)


class _FakeGIS:
    def __init__(self, items):
        self.content = _FakeContent(items)


def _config():
    return {
        "ARCGIS_URL": "https://example.invalid",
        "ARCGIS_USERNAME": "app_user",
        "ARCGIS_PASSWORD": "secret-value",
        "ARCGIS_NATIONAL_TABLE_ID": "nat-id",
        "ARCGIS_PUBLISHER_TABLE_ID": "pub-id",
    }


# --- read_arcgis_config ------------------------------------------------------

class TestReadConfig:
    def test_lee_config_completa(self):
        cfg = pub.read_arcgis_config(_config())
        assert cfg["ARCGIS_USERNAME"] == "app_user"

    def test_faltan_variables_lanza_error_sin_exponer_password(self):
        env = _config()
        del env["ARCGIS_PASSWORD"]
        del env["ARCGIS_NATIONAL_TABLE_ID"]
        with pytest.raises(pub.PublishError) as excinfo:
            pub.read_arcgis_config(env)
        msg = str(excinfo.value)
        assert "ARCGIS_PASSWORD" in msg          # nombra la variable que falta
        assert "ARCGIS_NATIONAL_TABLE_ID" in msg
        assert "secret-value" not in msg          # nunca el valor del secreto


# --- publish: truncate + append sobre item existente -------------------------

class TestPublish:
    def test_reemplaza_contenido_y_no_crea_items(self):
        nat_table, pub_table = _FakeTable(), _FakeTable()
        items = {"nat-id": _FakeItem(nat_table), "pub-id": _FakeItem(pub_table)}

        def fake_connect(config):
            return _FakeGIS(items)

        national_rows = [{"snapshot_date": "2026-10-21", "total_bird_records": "26753542"}]
        publisher_rows = [
            {"org_key": "org-a", "occurrence_count": "24154885"},
            {"org_key": "org-b", "occurrence_count": "437712"},
        ]

        summary = pub.publish(_config(), national_rows, publisher_rows, connect=fake_connect)

        # Se vació antes de insertar (sin duplicar / mezclar cortes viejos).
        assert nat_table.deleted_where == "1=1"
        assert pub_table.deleted_where == "1=1"
        # Se insertaron exactamente las filas provistas.
        assert summary["national_rows_published"] == 1
        assert summary["publisher_rows_published"] == 2
        assert nat_table.added == national_rows

    def test_item_inexistente_lanza_error(self):
        def fake_connect(config):
            return _FakeGIS({})  # content.get(...) -> None

        with pytest.raises(pub.PublishError):
            pub.publish(_config(), [], [], connect=fake_connect)


# --- run_pipeline: dry-run no publica, y siempre registra --------------------

class TestRunPipeline:
    @pytest.fixture()
    def _isolate(self, tmp_path, monkeypatch):
        """Aísla extracción/exportación/log en archivos temporales, sin red."""
        # 1) Extracción simulada (no toca GBIF).
        fake_report = {
            "status": "completed",
            "total_bird_records_colombia": 26753542,
            "publisher_ranking": [{"org_key": "org-a", "occurrence_count": 1,
                                   "publisher_name": "A"}],
            "publishers_in_ranking": 1,
            "extracted_at_utc": "2026-10-21T00:00:00+00:00",
        }
        monkeypatch.setattr(pub.history.gbc, "run", lambda **kw: dict(fake_report))
        monkeypatch.setattr(pub.history.gbc, "write_outputs",
                            lambda *a, **k: {"csv": "x", "json": "y"})
        monkeypatch.setattr(pub.history, "append_to_history",
                            lambda report: {"appended": True})
        # 2) Exportación simulada (no escribe los CSV reales del repo).
        monkeypatch.setattr(pub.exporter, "export", lambda write=True: {"written": write})
        # 3) Run log y CSV de publicación en tmp.
        monkeypatch.setattr(pub, "RUN_LOG", tmp_path / "run_log.csv")
        monkeypatch.setattr(pub, "NATIONAL_CSV", tmp_path / "nat.csv")
        monkeypatch.setattr(pub, "PUBLISHER_CSV", tmp_path / "pub.csv")
        (tmp_path / "nat.csv").write_text("snapshot_date\n2026-10-21\n", encoding="utf-8-sig")
        (tmp_path / "pub.csv").write_text("org_key\norg-a\n", encoding="utf-8-sig")
        return tmp_path

    def test_dry_run_no_publica_pero_registra(self, _isolate, monkeypatch):
        result = pub.run_pipeline(do_publish=False, facet_limit=5, timeout=10,
                                  resolve_names=True)
        assert result["published"] is False
        assert "dry-run" in result["publish_detail"]
        # Registró la ejecución igualmente.
        rows = list(csv.DictReader((_isolate / "run_log.csv").open(encoding="utf-8-sig")))
        assert len(rows) == 1
        assert rows[0]["extraction_status"] == "completed"
        assert rows[0]["published"] == "no"

    def test_publica_con_connect_inyectado(self, _isolate, monkeypatch):
        nat_table, pub_table = _FakeTable(), _FakeTable()
        items = {"nat-id": _FakeItem(nat_table), "pub-id": _FakeItem(pub_table)}
        monkeypatch.setattr(pub, "read_arcgis_config", lambda env=None: _config())

        result = pub.run_pipeline(
            do_publish=True, facet_limit=5, timeout=10, resolve_names=True,
            connect=lambda config: _FakeGIS(items),
        )
        assert result["published"] is True
        assert "national=" in result["publish_detail"]
        rows = list(csv.DictReader((_isolate / "run_log.csv").open(encoding="utf-8-sig")))
        assert rows[0]["published"] == "yes"

    def test_publicacion_fallida_se_registra_sin_romper(self, _isolate, monkeypatch):
        # Config incompleta => PublishError capturado, run se registra como 'no'.
        monkeypatch.setattr(pub, "read_arcgis_config",
                            lambda env=None: (_ for _ in ()).throw(
                                pub.PublishError("faltan variables")))
        result = pub.run_pipeline(do_publish=True, facet_limit=5, timeout=10,
                                  resolve_names=True)
        assert result["published"] is False
        assert "omitida/fallida" in result["publish_detail"]
        rows = list(csv.DictReader((_isolate / "run_log.csv").open(encoding="utf-8-sig")))
        assert rows[0]["published"] == "no"
