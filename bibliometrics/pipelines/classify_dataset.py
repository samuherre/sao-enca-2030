"""
classify_dataset.py — Clasificación por OFC de un dataset procesado (Comp. B).

Toma un dataset ya extraído (p. ej. data/processed/<fuente>/*.json), clasifica
cada artículo por OFC (reglas-keywords-v1, multilabel) y escribe un dataset
CLASIFICADO (JSON + CSV) en data/processed/<fuente>_clasificado/ sin modificar
la entrada.

Generalizado para CUALQUIER fuente (ADR-010, multi-source-bibliometria):
  - --source <nombre>: usa data/processed/<nombre>/ como entrada y
    data/processed/<nombre>_clasificado/ como salida; el prefijo de archivo es
    <nombre>_clasificado_<fecha>. Por defecto es "boletin_sao" (compatibilidad).
  - --input <ruta.json>: clasifica un JSON concreto. Si no se da --source, la
    salida se deriva del nombre de la carpeta de entrada.
  - El servicio consolidado descubre automáticamente las carpetas *_clasificado
    y suma su distribución por OFC (sin contarlas al total). No se asume ningún
    nombre de fuente fijo en el backend.

Reglas (ADR-010, steering bibliometrics.md):
  - Rellena ofcs / classification_method / classification_confidence.
  - Añade la evidencia (términos coincidentes) a 'notes' para trazabilidad.
  - Sin coincidencias -> ofcs vacío; permanece PENDIENTE_REVISIÓN.
  - No modifica el dataset de entrada (raw/processed inmutables).

Uso (con el .venv activado):
    python bibliometrics/pipelines/classify_dataset.py
    python bibliometrics/pipelines/classify_dataset.py --source openalex
    python bibliometrics/pipelines/classify_dataset.py --input <ruta.json>
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT / "bibliometrics") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "bibliometrics"))

from classification.ofc_classifier import OFCClassifier  # noqa: E402

PROCESSED_ROOT = _REPO_ROOT / "data" / "processed"
DEFAULT_SOURCE = "boletin_sao"

CSV_FIELDS = [
    "article_id", "title", "authors", "publication_year", "volume", "pages",
    "keywords", "source", "inclusion_status",
    "ofcs", "classification_method", "classification_confidence", "notes",
]


def _ultimo_dataset(source_dir: Path, source: str) -> Path | None:
    """Devuelve el JSON de entrada más reciente de la carpeta de la fuente.

    Prefiere el patrón <source>_dataset_*.json; si no hay, toma cualquier .json
    que NO sea un *_clasificado_*.json (para no reclasificar una salida previa).
    """
    if not source_dir.exists():
        return None
    candidatos = sorted(source_dir.glob(f"{source}_dataset_*.json"))
    if not candidatos:
        candidatos = sorted(
            p for p in source_dir.glob("*.json")
            if "_clasificado_" not in p.name
        )
    return candidatos[-1] if candidatos else None


def clasificar_dataset(registros: list[dict], clasificador: OFCClassifier) -> list[dict]:
    """Devuelve una copia de los registros con la clasificación OFC rellenada."""
    salida = []
    for r in registros:
        rec = dict(r)  # no mutar la entrada
        resultado = clasificador.clasificar_articulo(rec)
        rec["ofcs"] = resultado.ofcs
        rec["classification_method"] = resultado.method
        rec["classification_confidence"] = resultado.confianza
        nota_ofc = f"[OFC] {resultado.evidencia_texto()}"
        rec["notes"] = f"{rec.get('notes')} | {nota_ofc}" if rec.get("notes") else nota_ofc
        salida.append(rec)
    return salida


def _write_outputs(registros: list[dict], out_dir: Path, source: str) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = _dt.date.today().isoformat()

    json_path = out_dir / f"{source}_clasificado_{stamp}.json"
    json_path.write_text(json.dumps(registros, ensure_ascii=False, indent=2), encoding="utf-8")

    csv_path = out_dir / f"{source}_clasificado_{stamp}.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for r in registros:
            row = dict(r)
            row["ofcs"] = ";".join(row.get("ofcs") or [])
            writer.writerow(row)
    return json_path, csv_path


def _resumen(registros: list[dict], source: str) -> None:
    total = len(registros)
    clasificados = sum(1 for r in registros if r.get("ofcs"))
    sin_ofc = total - clasificados
    multilabel = sum(1 for r in registros if len(r.get("ofcs") or []) > 1)

    # Distribución por OFC.
    from collections import Counter
    dist = Counter()
    for r in registros:
        for ofc in r.get("ofcs") or []:
            dist[ofc] += 1

    print("\n" + "=" * 60)
    print(f"RESUMEN DE CLASIFICACIÓN OFC — {source}")
    print("=" * 60)
    print(f"  Artículos                : {total}")
    print(f"  Con al menos 1 OFC       : {clasificados}")
    print(f"  Sin OFC (NO_CLASIFICADO) : {sin_ofc}")
    print(f"  Multilabel (>1 OFC)      : {multilabel}")
    print("  Distribución por OFC:")
    for ofc_id, n in sorted(dist.items()):
        print(f"    {ofc_id}: {n}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Clasificación OFC de un dataset")
    parser.add_argument("--source", type=str, default=None,
                        help="Nombre lógico de la fuente (p. ej. openalex, boletin_sao, "
                             "google_scholar). Por defecto boletin_sao.")
    parser.add_argument("--input", type=str, default=None,
                        help="Dataset JSON de entrada (anula el descubrimiento por --source).")
    args = parser.parse_args()

    # Resolución de fuente, entrada y salida.
    if args.input:
        input_path = Path(args.input)
        if not input_path.is_absolute():
            input_path = _REPO_ROOT / input_path
        # Si no se dio --source, derivarlo del nombre de la carpeta de entrada.
        source = args.source or input_path.parent.name
    else:
        source = args.source or DEFAULT_SOURCE
        source_dir = PROCESSED_ROOT / source
        input_path = _ultimo_dataset(source_dir, source)

    out_dir = PROCESSED_ROOT / f"{source}_clasificado"

    if not input_path or not input_path.exists():
        print(f"ERROR: no se encontró dataset de entrada para la fuente '{source}'. "
              "Ejecute primero la ingesta.")
        return

    print(f"Clasificando: {input_path}")
    print(f"Fuente: {source}  ->  salida: {out_dir}")
    registros = json.loads(input_path.read_text(encoding="utf-8"))
    clasificador = OFCClassifier()
    clasificados = clasificar_dataset(registros, clasificador)

    json_path, csv_path = _write_outputs(clasificados, out_dir, source)
    _resumen(clasificados, source)
    print("\nArchivos generados:")
    print(f"  JSON: {json_path}")
    print(f"  CSV : {csv_path}")


if __name__ == "__main__":
    main()
