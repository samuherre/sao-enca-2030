#!/usr/bin/env python3
"""
Fase 2 — Histórico mensual de cifras agregadas de AVES en Colombia (GBIF).

Qué hace:
  1. Ejecuta el recolector de Fase 1 (reutiliza `gbif_bird_counts.run`), con los
     MISMOS filtros acordados: country=CO, taxonKey=212, total nacional + top 5
     de publicadores. No descarga ocurrencias individuales.
  2. Guarda el *snapshot* de cada corte en un archivo propio con marca de tiempo
     UTC (reutiliza `gbif_bird_counts.write_outputs`), sin sobrescribir cortes
     anteriores ni los artefactos de Fase 1.
  3. Añade (append) el corte a un histórico consolidado en CSV que permite
     comparar, entre cortes, el total nacional y el conteo de cada publicador.

Reglas de integridad (requisitos de Fase 2):
  - El publicador se identifica por `org_key` (clave estable); el `publisher_name`
    se guarda como atributo que PUEDE cambiar entre cortes.
  - Una ejecución se marca `completed` o `completed_with_errors` según lo reporte
    Fase 1. Una consulta fallida NO introduce ceros ni reemplaza cifras válidas:
      * Si falta el total nacional, la fila del histórico de total guarda ese
        campo VACÍO (nunca 0) y conserva el estado de error.
      * Si no se obtuvo ni total ni ranking, NO se añade ninguna fila al
        histórico (no se contamina con una corrida vacía) y el proceso lo informa.
  - Las diferencias entre cortes son diferencias entre los valores AGREGADOS que
    GBIF reporta en cada fecha; NO representan necesariamente "registros nuevos".

Restricciones (no incluidas aquí a propósito): no hay programador automático, no
se publica en ArcGIS, no se añaden dependencias (solo stdlib), no hay desglose
por departamento.

Uso:
    python scripts/biodiversity_pilot/gbif_bird_counts_history.py
    python scripts/biodiversity_pilot/gbif_bird_counts_history.py --facet-limit 5
    python scripts/biodiversity_pilot/gbif_bird_counts_history.py --dry-run
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# --- Importar el módulo de Fase 1 por ruta (mismo directorio) ----------------
# Se carga por ruta para no depender de cómo se invoque el script (evita
# problemas de sys.path) y para reutilizar su lógica sin duplicarla.

_FASE1_PATH = Path(__file__).resolve().parent / "gbif_bird_counts.py"
_spec = importlib.util.spec_from_file_location("gbif_bird_counts", _FASE1_PATH)
if _spec is None or _spec.loader is None:  # pragma: no cover - entorno roto
    raise RuntimeError(f"No se pudo cargar el módulo de Fase 1: {_FASE1_PATH}")
gbc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gbc)

# --- Rutas de salida ---------------------------------------------------------

GBIF_DIR = (
    Path(__file__).resolve().parents[2]
    / "outputs"
    / "biodiversity_pilot"
    / "gbif"
)
HISTORY_DIR = GBIF_DIR / "history"
NATIONAL_TOTAL_HISTORY = HISTORY_DIR / "national_total_history.csv"
PUBLISHER_HISTORY = HISTORY_DIR / "publisher_history.csv"

NATIONAL_TOTAL_FIELDS = [
    "extracted_at_utc",
    "finished_at_utc",
    "status",
    "total_bird_records_colombia",
    "publishers_in_ranking",
    "source",
    "country",
    "taxon_key",
    "errors",
]

PUBLISHER_FIELDS = [
    "extracted_at_utc",
    "status",
    "rank",
    "org_key",
    "publisher_name",
    "occurrence_count",
]


def _param(report: dict[str, Any], query: str, key: str) -> Any:
    """Lee un parámetro de query_params sin fallar si falta."""
    return (report.get("query_params", {}).get(query, {}) or {}).get(key)


def _append_rows(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    """Añade filas a un CSV, escribiendo la cabecera solo si el archivo es nuevo.

    No sobrescribe el contenido previo: siempre abre en modo 'append'.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists() or path.stat().st_size == 0
    with path.open("a", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        if write_header:
            writer.writeheader()
        writer.writerows(rows)


def build_national_total_row(report: dict[str, Any]) -> dict[str, Any]:
    """Construye la fila del histórico de total nacional a partir del reporte."""
    total = report.get("total_bird_records_colombia")
    return {
        "extracted_at_utc": report.get("extracted_at_utc"),
        "finished_at_utc": report.get("finished_at_utc"),
        "status": report.get("status"),
        # Si no hay total, se deja VACÍO (nunca 0) para no inventar una cifra.
        "total_bird_records_colombia": "" if total is None else total,
        "publishers_in_ranking": report.get("publishers_in_ranking", 0),
        "source": report.get("source"),
        "country": _param(report, "total_count", "country"),
        "taxon_key": _param(report, "total_count", "taxonKey"),
        # Lista de errores serializada de forma legible; "" si no hubo.
        "errors": " | ".join(report.get("errors", [])),
    }


def build_publisher_rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    """Construye una fila por publicador del ranking del corte."""
    rows: list[dict[str, Any]] = []
    for position, pub in enumerate(report.get("publisher_ranking", []), start=1):
        rows.append(
            {
                "extracted_at_utc": report.get("extracted_at_utc"),
                "status": report.get("status"),
                "rank": position,
                "org_key": pub.get("org_key"),
                "publisher_name": pub.get("publisher_name") or "",
                "occurrence_count": pub.get("occurrence_count"),
            }
        )
    return rows


def has_usable_data(report: dict[str, Any]) -> bool:
    """True si el corte aporta algo real al histórico (total o ranking)."""
    return (
        report.get("total_bird_records_colombia") is not None
        or bool(report.get("publisher_ranking"))
    )


def append_to_history(
    report: dict[str, Any],
    national_total_path: Path = NATIONAL_TOTAL_HISTORY,
    publisher_path: Path = PUBLISHER_HISTORY,
) -> dict[str, Any]:
    """Añade el corte al histórico consolidado, respetando las reglas de integridad.

    Devuelve un pequeño resumen de lo que se escribió. Si el corte no tiene datos
    usables, NO escribe nada y lo indica en el resumen.
    """
    if not has_usable_data(report):
        return {
            "appended": False,
            "reason": "corrida sin datos usables (ni total ni ranking); no se contamina el histórico",
            "national_total_rows": 0,
            "publisher_rows": 0,
        }

    national_row = build_national_total_row(report)
    publisher_rows = build_publisher_rows(report)

    _append_rows(national_total_path, NATIONAL_TOTAL_FIELDS, [national_row])
    if publisher_rows:
        _append_rows(publisher_path, PUBLISHER_FIELDS, publisher_rows)

    return {
        "appended": True,
        "national_total_rows": 1,
        "publisher_rows": len(publisher_rows),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Fase 2: snapshot + histórico consolidado de cifras de aves de "
            "Colombia en GBIF (total + top publicadores)."
        )
    )
    parser.add_argument("--facet-limit", type=int, default=5,
                        help="Nº de publicadores del ranking (acordado: 5).")
    parser.add_argument("--timeout", type=int, default=gbc.DEFAULT_TIMEOUT,
                        help=f"Timeout por consulta (s). Def. {gbc.DEFAULT_TIMEOUT}.")
    parser.add_argument("--no-resolve-names", action="store_true",
                        help="No resolver org_key -> nombre del publicador.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Ejecuta y muestra el corte, pero no escribe nada.")
    args = parser.parse_args(argv)

    if args.facet_limit < 0:
        parser.error("--facet-limit no puede ser negativo.")

    now = datetime.now(timezone.utc)

    # 1) Recolección (reutiliza Fase 1; mismos filtros CO + 212).
    report = gbc.run(
        facet_limit=args.facet_limit,
        timeout=args.timeout,
        resolve_names=not args.no_resolve_names,
    )

    print("Estado de la corrida:", report["status"])
    print("Total nacional:", report["total_bird_records_colombia"])
    print("Publicadores en ranking:", report["publishers_in_ranking"])
    if report["errors"]:
        print("Errores:", " | ".join(report["errors"]), file=sys.stderr)

    if args.dry_run:
        print("\n[dry-run] No se escribieron snapshot ni histórico.", file=sys.stderr)
        return 0 if has_usable_data(report) else 1

    # 2) Snapshot del corte (reutiliza la escritura de Fase 1; no sobrescribe).
    snapshot_paths = gbc.write_outputs(GBIF_DIR, now, report, report["publisher_ranking"])

    # 3) Histórico consolidado (append; regla de integridad aplicada).
    hist = append_to_history(report)

    print(f"\nSnapshot:\n  CSV:  {snapshot_paths['csv']}\n  JSON: {snapshot_paths['json']}",
          file=sys.stderr)
    if hist["appended"]:
        print(
            f"Histórico actualizado:\n"
            f"  {NATIONAL_TOTAL_HISTORY}  (+{hist['national_total_rows']} fila)\n"
            f"  {PUBLISHER_HISTORY}  (+{hist['publisher_rows']} filas)",
            file=sys.stderr,
        )
    else:
        print(f"Histórico NO actualizado: {hist['reason']}", file=sys.stderr)

    return 0 if has_usable_data(report) else 1


if __name__ == "__main__":
    raise SystemExit(main())
