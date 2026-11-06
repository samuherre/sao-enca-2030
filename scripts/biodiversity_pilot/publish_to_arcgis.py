#!/usr/bin/env python3
"""
Fase 3 (automatización — Camino 3) — Extraer, exportar y PUBLICAR en ArcGIS Online.

Flujo de una ejecución mensual:
    GBIF (agregados)                         [Fase 1/2: gbif_bird_counts_history]
       -> snapshot + history/*.csv
       -> CSV de publicación                 [Fase 3: export_for_arcgis]
       -> actualizar tabla(s) en ArcGIS      [este script, opción 3]
       -> registrar el resultado de la ejecución (run log)

Decisiones de diseño (seguridad y bajo acoplamiento):
  - El paquete `arcgis` (ArcGIS API for Python) se importa de forma PEREZOSA:
    solo se carga al publicar. Así la extracción/exportación y TODAS las pruebas
    funcionan sin tenerlo instalado.
  - Las credenciales se leen de VARIABLES DE ENTORNO (en GitHub Actions serán
    *secrets*). Nunca se escriben en el repositorio ni se imprimen en logs.
  - `--dry-run` ejecuta todo MENOS la subida: sirve para practicar sin tocar
    ArcGIS Online.
  - Actualización por REEMPLAZO del contenido de la tabla (truncate + append):
    como el histórico es append-only y cada fila lleva su fecha de corte, el
    reemplazo no duplica ni mezcla cifras. Evita además crear items nuevos por
    error: publica sobre items EXISTENTES identificados por su id.
  - Cada ejecución se registra en outputs/.../arcgis/run_log.csv con estado y
    detalle, haya o no publicación (requisito: "registrar los resultados de cada
    ejecución").

Variables de entorno para publicar (NO se almacenan en el repo):
  ARCGIS_URL                 p. ej. https://www.arcgis.com  (o el portal de SAO)
  ARCGIS_USERNAME            usuario-app con privilegio de publicación
  ARCGIS_PASSWORD            contraseña del usuario-app
  ARCGIS_NATIONAL_TABLE_ID   item id de la tabla de total nacional (ya creada)
  ARCGIS_PUBLISHER_TABLE_ID  item id de la tabla de publicadores (ya creada)

Uso:
    # Solo preparar (sin tocar ArcGIS):
    python scripts/biodiversity_pilot/publish_to_arcgis.py --dry-run
    # Flujo completo (requiere las variables de entorno y el paquete `arcgis`):
    python scripts/biodiversity_pilot/publish_to_arcgis.py
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# --- Cargar módulos de fases previas por ruta (reutilización, sin duplicar) --

_HERE = Path(__file__).resolve().parent


def _load(module_name: str, filename: str):
    spec = importlib.util.spec_from_file_location(module_name, _HERE / filename)
    if spec is None or spec.loader is None:  # pragma: no cover
        raise RuntimeError(f"No se pudo cargar {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


history = _load("gbif_bird_counts_history", "gbif_bird_counts_history.py")
exporter = _load("export_for_arcgis", "export_for_arcgis.py")

# --- Rutas -------------------------------------------------------------------

ARCGIS_DIR = exporter.ARCGIS_DIR
NATIONAL_CSV = exporter.NATIONAL_TOTAL_ARCGIS
PUBLISHER_CSV = exporter.PUBLISHER_COUNTS_ARCGIS
RUN_LOG = ARCGIS_DIR / "run_log.csv"

RUN_LOG_FIELDS = [
    "run_at_utc",
    "extraction_status",
    "total_bird_records",
    "publishers_in_ranking",
    "published",
    "publish_detail",
]

# --- Credenciales (desde entorno; nunca hardcodeadas) ------------------------

REQUIRED_ENV = [
    "ARCGIS_URL",
    "ARCGIS_USERNAME",
    "ARCGIS_PASSWORD",
    "ARCGIS_NATIONAL_TABLE_ID",
    "ARCGIS_PUBLISHER_TABLE_ID",
]


class PublishError(RuntimeError):
    """Error controlado durante la publicación."""


def read_arcgis_config(env: dict[str, str] | None = None) -> dict[str, str]:
    """Lee la configuración de ArcGIS del entorno. Lanza PublishError si falta algo.

    No registra ni devuelve nunca el valor de la contraseña en mensajes.
    """
    env = env if env is not None else dict(os.environ)
    missing = [key for key in REQUIRED_ENV if not env.get(key)]
    if missing:
        raise PublishError(
            "Faltan variables de entorno para publicar: " + ", ".join(missing)
        )
    return {key: env[key] for key in REQUIRED_ENV}


def _read_csv_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise PublishError(f"No existe el CSV de publicación: {path}")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


# --- Publicación en ArcGIS (import perezoso del paquete `arcgis`) ------------

def _connect(config: dict[str, str]):
    """Crea un GIS autenticado. Importa `arcgis` de forma perezosa.

    Se aísla para poder parchearlo en pruebas sin instalar el paquete.
    """
    try:
        from arcgis.gis import GIS  # import perezoso (dependencia opcional)
    except ImportError as error:  # pragma: no cover - depende del entorno
        raise PublishError(
            "El paquete 'arcgis' no está instalado. Instálalo solo en el entorno "
            "de publicación (p. ej. el runner de GitHub Actions): pip install arcgis"
        ) from error
    return GIS(config["ARCGIS_URL"], config["ARCGIS_USERNAME"], config["ARCGIS_PASSWORD"])


def _overwrite_table(gis: Any, item_id: str, rows: list[dict[str, Any]]) -> int:
    """Reemplaza el contenido de una hosted table por `rows` (truncate + append).

    Devuelve el nº de filas añadidas. No crea items: opera sobre uno existente.
    """
    item = gis.content.get(item_id)
    if item is None:
        raise PublishError(f"No se encontró el item de ArcGIS con id={item_id}")
    table = item.tables[0]
    # Vaciar y volver a cargar: evita duplicados y deja la tabla = histórico actual.
    table.delete_features(where="1=1")
    result = table.edit_features(adds=rows)
    added = result.get("addResults", []) if isinstance(result, dict) else []
    ok = [r for r in added if r.get("success")]
    return len(ok)


def publish(
    config: dict[str, str],
    national_rows: list[dict[str, Any]],
    publisher_rows: list[dict[str, Any]],
    connect=_connect,
) -> dict[str, Any]:
    """Publica ambos conjuntos en sus tablas de ArcGIS. `connect` es inyectable.

    Devuelve un resumen con el nº de filas escritas por tabla.
    """
    gis = connect(config)
    national_added = _overwrite_table(gis, config["ARCGIS_NATIONAL_TABLE_ID"], national_rows)
    publisher_added = _overwrite_table(gis, config["ARCGIS_PUBLISHER_TABLE_ID"], publisher_rows)
    return {
        "national_rows_published": national_added,
        "publisher_rows_published": publisher_added,
    }


# --- Registro de ejecuciones -------------------------------------------------

def append_run_log(row: dict[str, Any], path: Path = RUN_LOG) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists() or path.stat().st_size == 0
    with path.open("a", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=RUN_LOG_FIELDS, extrasaction="ignore")
        if write_header:
            writer.writeheader()
        writer.writerow(row)


# --- Orquestación ------------------------------------------------------------

def run_pipeline(
    do_publish: bool,
    facet_limit: int,
    timeout: int,
    resolve_names: bool,
    connect=_connect,
) -> dict[str, Any]:
    """Ejecuta extracción -> exportación -> (opcional) publicación y registra el run."""
    run_at = datetime.now(timezone.utc)
    now = run_at

    # 1) Extracción + histórico (Fase 2). Reutiliza su recolector y filtros.
    report = history.gbc.run(
        facet_limit=facet_limit, timeout=timeout, resolve_names=resolve_names
    )
    history.gbc.write_outputs(history.GBIF_DIR, now, report, report["publisher_ranking"])
    history.append_to_history(report)

    # 2) Exportación a CSV de publicación (Fase 3).
    exporter.export(write=True)

    published = False
    publish_detail = ""

    if do_publish:
        try:
            config = read_arcgis_config()
            national_rows = _read_csv_rows(NATIONAL_CSV)
            publisher_rows = _read_csv_rows(PUBLISHER_CSV)
            summary = publish(config, national_rows, publisher_rows, connect=connect)
            published = True
            publish_detail = (
                f"national={summary['national_rows_published']} "
                f"publisher={summary['publisher_rows_published']}"
            )
        except PublishError as error:
            publish_detail = f"publicación omitida/fallida: {error}"
    else:
        publish_detail = "dry-run: no se intentó publicar"

    # 3) Registrar el resultado de la ejecución (siempre).
    log_row = {
        "run_at_utc": run_at.isoformat(),
        "extraction_status": report.get("status"),
        "total_bird_records": (
            "" if report.get("total_bird_records_colombia") is None
            else report["total_bird_records_colombia"]
        ),
        "publishers_in_ranking": report.get("publishers_in_ranking", 0),
        "published": "yes" if published else "no",
        "publish_detail": publish_detail,
    }
    # Se lee RUN_LOG del módulo en tiempo de ejecución (no como default fijo),
    # para respetar reconfiguraciones de la ruta (p. ej. en pruebas).
    append_run_log(log_row, RUN_LOG)

    return {
        "extraction_status": report.get("status"),
        "published": published,
        "publish_detail": publish_detail,
        "log_row": log_row,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Camino 3: extrae cifras de GBIF, prepara CSV y los publica en "
            "ArcGIS Online (actualización mensual). Registra cada ejecución."
        )
    )
    parser.add_argument("--facet-limit", type=int, default=5)
    parser.add_argument("--timeout", type=int, default=history.gbc.DEFAULT_TIMEOUT)
    parser.add_argument("--no-resolve-names", action="store_true")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Extrae y exporta, pero NO publica en ArcGIS (para practicar).",
    )
    args = parser.parse_args(argv)

    result = run_pipeline(
        do_publish=not args.dry_run,
        facet_limit=args.facet_limit,
        timeout=args.timeout,
        resolve_names=not args.no_resolve_names,
    )

    print("Estado de extracción:", result["extraction_status"])
    print("Publicado:", "sí" if result["published"] else "no")
    print("Detalle:", result["publish_detail"])
    print(f"Registro añadido a: {RUN_LOG}", file=sys.stderr)

    # Si se pidió publicar y no se logró, señalar con código de salida != 0.
    if not args.dry_run and not result["published"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
