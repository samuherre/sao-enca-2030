"""
process_boletin_sao.py — Pipeline de ingesta en lote de la fuente Boletin SAO.

Recorre una carpeta de PDFs del Boletin SAO (1 PDF = 1 articulo) y produce un
dataset consolidado conforme al Article Data Contract V1.

Etapas (structure.md §15):
    carpeta de PDFs
        -> extraccion (ingestion/extract_boletin.py)
        -> validacion de periodo 2020-2030
        -> deteccion simple de duplicados (por title normalizado)
        -> consolidacion -> JSON + CSV
        -> resumen por consola

REGLAS:
    - No inventa datos (hereda la logica del extractor).
    - No clasifica OFC (PENDING_VALIDATION).
    - No modifica los PDFs originales (data/raw es inmutable).

Uso (con el .venv activado):
    python bibliometrics/pipelines/process_boletin_sao.py
    python bibliometrics/pipelines/process_boletin_sao.py --input data/raw/boletin_sao
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
# Permite importar el extractor (ingestion/) y los helpers (pipelines/).
if str(_REPO_ROOT / "bibliometrics") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "bibliometrics"))

from ingestion.extract_boletin import extract_article  # noqa: E402
from pipelines._common import (  # noqa: E402
    mark_duplicates,
    print_summary,
    validate_period,
    write_outputs,
)

DEFAULT_INPUT = _REPO_ROOT / "data" / "raw" / "boletin_sao"
# Fallback: si raw esta vacio, usar las muestras (utilidad para desarrollo).
SAMPLES_INPUT = _REPO_ROOT / "data" / "samples"
OUTPUT_DIR = _REPO_ROOT / "data" / "processed" / "boletin_sao"


def process_folder(input_dir: Path) -> list:
    pdfs = sorted(input_dir.glob("*.pdf"))
    records = []
    print(f"Procesando {len(pdfs)} PDF(s) en {input_dir}\n")
    for pdf_path in pdfs:
        try:
            rec = extract_article(pdf_path)
            validate_period(rec)
            records.append(rec)
            flag = "DUP" if rec.is_duplicate else "   "
            print(f"  [OK ] {flag} {pdf_path.name:40} vol={rec.volume} año={rec.publication_year}")
        except Exception as exc:  # noqa: BLE001 — queremos que un PDF roto no tumbe el lote
            print(f"  [ERR]     {pdf_path.name:40} -> {exc}")
    mark_duplicates(records)
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline de ingesta Boletin SAO")
    parser.add_argument(
        "--input", type=str, default=None,
        help="Carpeta con los PDFs (por defecto data/raw/boletin_sao).",
    )
    args = parser.parse_args()

    if args.input:
        input_dir = Path(args.input)
        if not input_dir.is_absolute():
            input_dir = _REPO_ROOT / input_dir
    else:
        input_dir = DEFAULT_INPUT
        # Si raw/boletin_sao no tiene PDFs todavia, caer a samples para no fallar.
        if not any(DEFAULT_INPUT.glob("*.pdf")) and any(SAMPLES_INPUT.glob("*.pdf")):
            print(f"(aviso) {DEFAULT_INPUT} sin PDFs; usando {SAMPLES_INPUT} para esta corrida.\n")
            input_dir = SAMPLES_INPUT

    if not input_dir.exists():
        print(f"ERROR: la carpeta {input_dir} no existe.")
        return

    records = process_folder(input_dir)
    if not records:
        print("No se extrajeron registros (¿hay PDFs en la carpeta?).")
        return

    json_path, csv_path = write_outputs(records, OUTPUT_DIR, "boletin_sao_dataset")
    print_summary(records, "Boletin SAO")
    print("\nArchivos generados:")
    print(f"  JSON: {json_path}")
    print(f"  CSV : {csv_path}")


if __name__ == "__main__":
    main()
