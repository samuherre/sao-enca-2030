#!/usr/bin/env python3
"""
Fase 3 (preparación LOCAL) — Exportar el histórico de cifras GBIF a CSV
aptos para ArcGIS Online.

Qué hace:
  Lee el histórico consolidado de Fase 2
    - outputs/biodiversity_pilot/gbif/history/national_total_history.csv
    - outputs/biodiversity_pilot/gbif/history/publisher_history.csv
  y produce DOS CSV "limpios para ArcGIS" en
    - outputs/biodiversity_pilot/gbif/arcgis/national_total_arcgis.csv
    - outputs/biodiversity_pilot/gbif/arcgis/publisher_counts_arcgis.csv

Por qué un artefacto derivado (no subir el histórico tal cual):
  - ArcGIS Online parsea mejor una fecha normalizada (snapshot_date = YYYY-MM-DD)
    que un timestamp con microsegundos y offset.
  - Conviene un campo de estado explícito (run_status) y un identificador estable
    del publicador (org_key) como clave entre cortes.
  - El histórico interno sigue siendo la fuente de verdad; estos CSV son SOLO
    para publicación.

Lo que este script NO hace (a propósito):
  - NO publica nada en ArcGIS Online.
  - NO pide ni almacena credenciales.
  - NO instala dependencias (solo biblioteca estándar).
  - NO modifica el histórico ni los artefactos de Fase 1/2.
  - NO inventa coordenadas: las cifras son agregados, no entidades geográficas.
  - NO inventa cifras: una fila sin total se exporta con el campo vacío, no 0.

Uso:
    python scripts/biodiversity_pilot/export_for_arcgis.py
    python scripts/biodiversity_pilot/export_for_arcgis.py --dry-run
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Any

# --- Rutas -------------------------------------------------------------------

GBIF_DIR = (
    Path(__file__).resolve().parents[2]
    / "outputs"
    / "biodiversity_pilot"
    / "gbif"
)
HISTORY_DIR = GBIF_DIR / "history"
NATIONAL_TOTAL_HISTORY = HISTORY_DIR / "national_total_history.csv"
PUBLISHER_HISTORY = HISTORY_DIR / "publisher_history.csv"

ARCGIS_DIR = GBIF_DIR / "arcgis"
NATIONAL_TOTAL_ARCGIS = ARCGIS_DIR / "national_total_arcgis.csv"
PUBLISHER_COUNTS_ARCGIS = ARCGIS_DIR / "publisher_counts_arcgis.csv"

# Contratos de salida (nombres de campo estables para la capa de ArcGIS).
NATIONAL_TOTAL_OUT_FIELDS = [
    "snapshot_date",            # YYYY-MM-DD (UTC), apto para ArcGIS Date
    "extracted_at_utc",         # timestamp original (trazabilidad)
    "source",
    "country",
    "taxon_key",
    "total_bird_records",       # entero; vacío si no se obtuvo (nunca 0)
    "publishers_in_ranking",
    "run_status",
]

PUBLISHER_OUT_FIELDS = [
    "snapshot_date",
    "extracted_at_utc",
    "org_key",                  # identificador ESTABLE del publicador
    "publisher_name",           # atributo que puede cambiar entre cortes
    "rank",
    "occurrence_count",
    "run_status",
]


class ExportError(RuntimeError):
    """Error controlado durante la exportación."""


# --- Utilidades --------------------------------------------------------------

def _snapshot_date(extracted_at_utc: str | None) -> str:
    """Deriva YYYY-MM-DD a partir del timestamp ISO. '' si no es parseable.

    No usa dependencias: toma los 10 primeros caracteres de un ISO-8601
    (``2026-10-21T...`` -> ``2026-10-21``) validando que tengan forma de fecha.
    """
    if not extracted_at_utc or len(extracted_at_utc) < 10:
        return ""
    candidate = extracted_at_utc[:10]
    parts = candidate.split("-")
    if len(parts) == 3 and all(p.isdigit() for p in parts):
        return candidate
    return ""


def _read_history(path: Path) -> list[dict[str, str]]:
    """Lee un CSV de histórico. Lista vacía si el archivo no existe."""
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


# --- Transformaciones --------------------------------------------------------

def transform_national_total(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    """Convierte filas del histórico nacional al contrato de publicación."""
    out: list[dict[str, Any]] = []
    for row in rows:
        extracted = row.get("extracted_at_utc", "")
        total_raw = (row.get("total_bird_records_colombia") or "").strip()
        out.append(
            {
                "snapshot_date": _snapshot_date(extracted),
                "extracted_at_utc": extracted,
                "source": row.get("source", ""),
                "country": row.get("country", ""),
                "taxon_key": row.get("taxon_key", ""),
                # Se conserva el vacío tal cual: no se sustituye por 0.
                "total_bird_records": total_raw,
                "publishers_in_ranking": row.get("publishers_in_ranking", ""),
                "run_status": row.get("status", ""),
            }
        )
    return out


def transform_publisher(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    """Convierte filas del histórico de publicadores al contrato de publicación."""
    out: list[dict[str, Any]] = []
    for row in rows:
        extracted = row.get("extracted_at_utc", "")
        out.append(
            {
                "snapshot_date": _snapshot_date(extracted),
                "extracted_at_utc": extracted,
                "org_key": row.get("org_key", ""),
                "publisher_name": row.get("publisher_name", ""),
                "rank": row.get("rank", ""),
                "occurrence_count": row.get("occurrence_count", ""),
                "run_status": row.get("status", ""),
            }
        )
    return out


# --- Orquestación ------------------------------------------------------------

def export(
    national_in: Path = NATIONAL_TOTAL_HISTORY,
    publisher_in: Path = PUBLISHER_HISTORY,
    national_out: Path = NATIONAL_TOTAL_ARCGIS,
    publisher_out: Path = PUBLISHER_COUNTS_ARCGIS,
    write: bool = True,
) -> dict[str, Any]:
    """Lee los históricos, transforma y (opcionalmente) escribe los CSV ArcGIS."""
    national_rows = _read_history(national_in)
    publisher_rows = _read_history(publisher_in)

    if not national_rows and not publisher_rows:
        raise ExportError(
            "No se encontró histórico para exportar. Ejecuta antes la Fase 2 "
            "(gbif_bird_counts_history.py) para generar history/*.csv."
        )

    national_out_rows = transform_national_total(national_rows)
    publisher_out_rows = transform_publisher(publisher_rows)

    if write:
        _write_csv(national_out, NATIONAL_TOTAL_OUT_FIELDS, national_out_rows)
        _write_csv(publisher_out, PUBLISHER_OUT_FIELDS, publisher_out_rows)

    return {
        "national_total_rows": len(national_out_rows),
        "publisher_rows": len(publisher_out_rows),
        "national_out": str(national_out),
        "publisher_out": str(publisher_out),
        "written": write,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Exporta el histórico de cifras GBIF a CSV aptos para ArcGIS Online "
            "(no publica nada; solo prepara archivos locales)."
        )
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Transforma y reporta, pero no escribe archivos.",
    )
    args = parser.parse_args(argv)

    try:
        result = export(write=not args.dry_run)
    except ExportError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print("Filas exportadas:")
    print(f"  national_total: {result['national_total_rows']}")
    print(f"  publisher:      {result['publisher_rows']}")

    if args.dry_run:
        print("\n[dry-run] No se escribieron archivos.", file=sys.stderr)
    else:
        print(
            f"\nArchivos para ArcGIS:\n  {result['national_out']}\n  {result['publisher_out']}",
            file=sys.stderr,
        )
        print(
            "\nRecuerda: estos CSV son para SUBIR MANUALMENTE a tu carpeta de "
            "pruebas en ArcGIS Online (privado). Este script NO publica nada.",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
