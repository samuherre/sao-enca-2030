"""
process_google_scholar.py — Pipeline de ingesta en lote de la fuente Google Scholar.

Recorre la carpeta de Export_PoP (Publish or Perish) de Google Scholar
(``data/raw/google_scholar/``, archivos ``.json`` / ``.csv``) y produce un
dataset consolidado conforme al Article Data Contract V1. Es el espejo del
pipeline del Boletín SAO (``process_boletin_sao.py``), reutilizando los helpers
compartidos de ``pipelines/_common.py``.

Etapas (structure.md §15):
    carpeta de Export_PoP (.json / .csv)
        -> extraccion (ingestion/extract_scholar.py)
        -> validacion de periodo 2020-2030 (_common.validate_period)
        -> deteccion simple de duplicados por title normalizado (_common.mark_duplicates)
        -> consolidacion -> JSON + CSV (_common.write_outputs)
        -> resumen por consola: leidos / procesados / descartados + completitud

REGLAS (steering Componente B §4):
    - No inventa datos (hereda la logica del conector).
    - No clasifica OFC (PENDING_VALIDATION).
    - data/raw es INMUTABLE: solo se LEE de raw; se ESCRIBE unicamente en
      data/processed/google_scholar/ (Req 1.1).

Manejo de ausencia / entrada vacia (Req 1.4):
    - Carpeta ausente, inaccesible o sin ningun ``.json`` ni ``.csv`` ->
      mensaje informativo y salida con EXITO sin procesar registros.

Manejo de registros malformados (Req 1.5, 1.6):
    - Un registro individual malformado se descarta registrando archivo +
      posicion dentro de ese archivo, y el lote continua.
    - Un archivo con formato/contenido no procesable (p. ej. JSON invalido o
      extension no soportada) se informa y se omite sin abortar el lote.
    - El resumen final conserva: leidos == procesados + descartados.

Uso (con el .venv activado) — un unico comando, sin UI (Req 5.3):
    python bibliometrics/pipelines/process_google_scholar.py
    python bibliometrics/pipelines/process_google_scholar.py --input data/raw/google_scholar
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
# Permite importar el conector (ingestion/) y los helpers (pipelines/).
if str(_REPO_ROOT / "bibliometrics") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "bibliometrics"))

from ingestion.extract_scholar import (  # noqa: E402
    detect_format,
    extract_records,
    _iter_csv_records,
    _iter_json_records,
)
from pipelines._common import (  # noqa: E402
    mark_duplicates,
    print_summary,
    validate_period,
    write_outputs,
)

DEFAULT_INPUT = _REPO_ROOT / "data" / "raw" / "google_scholar"
OUTPUT_DIR = _REPO_ROOT / "data" / "processed" / "google_scholar"
SOURCE_LABEL = "Google Scholar"


def _count_raw_records(path: Path, fmt: str) -> int:
    """Cuenta los registros crudos (entradas) de un Export_PoP.

    Sirve para calcular ``descartados = leidos - procesados`` por archivo, ya
    que ``extract_records`` devuelve solo los registros validos. Reutiliza los
    mismos lectores del conector para contar exactamente las mismas entradas que
    este intenta parsear.
    """
    if fmt == "json":
        return len(_iter_json_records(path))
    return len(_iter_csv_records(path))


def _report_discards(path: Path, raw_records: list, processed_count: int) -> None:
    """Registra archivo + posicion de los registros descartados (Req 1.5).

    ``extract_records`` descarta internamente los registros no-objeto o rotos;
    aqui reproducimos la deteccion de "no es un objeto clave->valor" para poder
    informar la posicion exacta dentro del archivo. Si el numero de descartados
    por posicion no coincide con ``leidos - procesados`` (p. ej. un objeto que
    el conector no pudo construir por otra razon), se informa el resto de forma
    agregada para mantener la trazabilidad.
    """
    read_count = len(raw_records)
    discarded_total = read_count - processed_count
    if discarded_total <= 0:
        return

    reported = 0
    for idx, raw in enumerate(raw_records):
        if not isinstance(raw, dict):
            print(
                f"  [DESCARTE] {path.name} registro #{idx}: "
                f"entrada malformada (no es un objeto); se descarta y continua."
            )
            reported += 1

    restante = discarded_total - reported
    if restante > 0:
        print(
            f"  [DESCARTE] {path.name}: {restante} registro(s) adicional(es) "
            f"no procesable(s); se descartan y continua el lote."
        )


def process_folder(input_dir: Path) -> tuple[list, int, int, int]:
    """Procesa todos los Export_PoP de ``input_dir``.

    :returns: ``(records, leidos, procesados, descartados)`` donde ``records``
        son los ``ArticleRecord`` validos (con duplicados ya marcados).
    """
    # Descubrimiento case-insensitive de .json / .csv (Req 1.2, 1.3). Se evita
    # depender del casing del glob en distintos sistemas de archivos.
    input_files = sorted(
        p for p in input_dir.iterdir()
        if p.is_file() and p.suffix.lower() in (".json", ".csv")
    )

    records: list = []
    leidos = 0
    procesados = 0
    descartados = 0

    print(f"Procesando {len(input_files)} archivo(s) de Export_PoP en {input_dir}\n")
    for file_path in input_files:
        try:
            fmt = detect_format(file_path)
            raw_records = (
                _iter_json_records(file_path) if fmt == "json"
                else _iter_csv_records(file_path)
            )
        except ValueError as exc:
            # Extension no soportada: no deberia ocurrir tras el filtro, pero se
            # maneja por robustez (Req: detect_format ValueError por archivo).
            print(f"  [ERR ] {file_path.name:40} -> formato no soportado: {exc}")
            continue
        except Exception as exc:  # noqa: BLE001 — un archivo roto no tumba el lote
            # JSON invalido, archivo ilegible, etc. Se informa y se omite.
            print(f"  [ERR ] {file_path.name:40} -> no procesable: {exc}")
            continue

        file_records = extract_records(file_path)
        file_read = len(raw_records)
        file_processed = len(file_records)
        file_discarded = file_read - file_processed

        leidos += file_read
        procesados += file_processed
        descartados += file_discarded

        for rec in file_records:
            validate_period(rec)
        records.extend(file_records)

        _report_discards(file_path, raw_records, file_processed)
        print(
            f"  [OK ] {file_path.name:40} "
            f"leidos={file_read} procesados={file_processed} descartados={file_discarded}"
        )

    mark_duplicates(records)
    return records, leidos, procesados, descartados


def _print_ingest_summary(leidos: int, procesados: int, descartados: int) -> None:
    """Resumen de ingesta: leidos / procesados / descartados (Req 1.6)."""
    print("\n" + "=" * 60)
    print(f"RESUMEN DE INGESTA — Fuente: {SOURCE_LABEL}")
    print("=" * 60)
    print(f"  Registros leidos      : {leidos}")
    print(f"  Procesados correctam. : {procesados}")
    print(f"  Descartados (malform.): {descartados}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pipeline de ingesta Google Scholar (Export Publish or Perish)",
    )
    parser.add_argument(
        "--input", type=str, default=None,
        help="Carpeta con los Export_PoP (por defecto data/raw/google_scholar).",
    )
    args = parser.parse_args()

    if args.input:
        input_dir = Path(args.input)
        if not input_dir.is_absolute():
            input_dir = _REPO_ROOT / input_dir
    else:
        input_dir = DEFAULT_INPUT

    # Entrada ausente / inaccesible / sin .json ni .csv -> mensaje informativo y
    # salida con EXITO sin procesar registros (Req 1.4).
    if not input_dir.exists() or not input_dir.is_dir():
        print(
            f"(info) La carpeta de entrada {input_dir} no existe o no es accesible. "
            f"No hay Export_PoP que procesar. Finalizando con exito sin registros."
        )
        return

    tiene_entrada = any(
        p.is_file() and p.suffix.lower() in (".json", ".csv")
        for p in input_dir.iterdir()
    )
    if not tiene_entrada:
        print(
            f"(info) {input_dir} no contiene archivos .json ni .csv de Export_PoP. "
            f"Coloque el export de Publish or Perish alli. "
            f"Finalizando con exito sin registros."
        )
        return

    records, leidos, procesados, descartados = process_folder(input_dir)

    _print_ingest_summary(leidos, procesados, descartados)

    if not records:
        print(
            "\nNo se produjeron registros validos a partir de los archivos de entrada."
        )
        return

    json_path, csv_path = write_outputs(records, OUTPUT_DIR, "google_scholar_dataset")
    print_summary(records, SOURCE_LABEL)
    print("\nArchivos generados:")
    print(f"  JSON: {json_path}")
    print(f"  CSV : {csv_path}")


if __name__ == "__main__":
    main()
