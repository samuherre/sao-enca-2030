"""
_common.py — Helpers compartidos de los pipelines de ingesta (Componente B).

Reúne la lógica común que usan los pipelines de cada fuente (Boletín SAO,
Google Scholar, etc.) para no duplicarla (DRY). Se extrajo de
``process_boletin_sao.py`` SIN cambiar su comportamiento: misma lógica, mismas
salidas (JSON + CSV) y mismo resumen por consola.

Funciones:
    norm_title       — clave normalizada para dedupe simple por título.
    mark_duplicates  — marca is_duplicate / duplicate_of (in place).
    validate_period  — deja constancia si el año cae fuera del periodo.
    write_outputs    — escribe el dataset consolidado a JSON + CSV.
    print_summary    — imprime el resumen de completitud por consola.

REGLAS (steering Componente B §4):
    - No inventa datos (hereda la lógica de cada extractor).
    - No clasifica OFC (PENDING_VALIDATION).
    - No modifica los originales (data/raw es inmutable); solo escribe en
      data/processed/ a través de write_outputs.

El periodo de inclusión 2020–2030 y el orden de columnas del Article Data
Contract V1 se mantienen aquí como fuente única para todos los pipelines.
"""

from __future__ import annotations

import csv
import datetime as _dt
import json
import re
import unicodedata
from dataclasses import asdict
from pathlib import Path

PERIODO_MIN, PERIODO_MAX = 2020, 2030

# Columnas del CSV (orden del Article Data Contract V1).
CSV_FIELDS = [
    "article_id", "title", "doi", "url",
    "authors", "authors_list", "publication_year", "journal", "volume", "issue", "pages",
    "publisher", "language",
    "abstract", "keywords",
    "source", "source_url", "extraction_date", "extraction_method",
    "processing_status", "is_duplicate", "duplicate_of", "notes",
    "inclusion_status", "exclusion_reason",
    "ofcs", "classification_method", "classification_confidence",
]


def norm_title(title: str | None) -> str:
    """Clave normalizada para deteccion simple de duplicados por titulo."""
    if not title:
        return ""
    t = unicodedata.normalize("NFKD", title)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()
    return t


def mark_duplicates(records: list) -> None:
    """Marca is_duplicate / duplicate_of por titulo normalizado (in place).

    Deteccion CONSERVADORA V1: solo marca duplicado exacto de titulo. No borra
    nada; solo anota. La estrategia definitiva de deduplicacion sigue
    PENDING_VALIDATION (tech.md §24).
    """
    seen: dict[str, str] = {}
    for rec in records:
        key = norm_title(rec.title)
        if not key:
            continue
        if key in seen:
            rec.is_duplicate = True
            rec.duplicate_of = seen[key]
            nota = f"Posible duplicado de {seen[key]} (titulo identico)."
            rec.notes = f"{rec.notes} | {nota}" if rec.notes else nota
        else:
            seen[key] = rec.article_id


def validate_period(rec) -> None:
    """Asegura que el año este en 2020-2030; si no, deja constancia."""
    y = rec.publication_year
    if y is not None and not (PERIODO_MIN <= y <= PERIODO_MAX):
        nota = f"Año {y} fuera del periodo {PERIODO_MIN}-{PERIODO_MAX}."
        rec.notes = f"{rec.notes} | {nota}" if rec.notes else nota
        rec.inclusion_status = "PENDIENTE_REVISIÓN"


def write_outputs(records: list, out_dir: Path, basename: str) -> tuple[Path, Path]:
    """Escribe el dataset consolidado a JSON + CSV en ``out_dir``.

    ``basename`` es el prefijo del archivo (p. ej. ``"boletin_sao_dataset"``);
    se le añade la fecha de hoy y la extensión. Mantiene el formato exacto que
    producía ``process_boletin_sao.py`` (JSON indent=2, CSV utf-8-sig, ofcs como
    lista unida por ``;``).
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = _dt.date.today().isoformat()

    dicts = [asdict(r) for r in records]

    json_path = out_dir / f"{basename}_{stamp}.json"
    json_path.write_text(json.dumps(dicts, ensure_ascii=False, indent=2), encoding="utf-8")

    csv_path = out_dir / f"{basename}_{stamp}.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for d in dicts:
            row = dict(d)
            # ofcs es lista -> texto legible para CSV.
            row["ofcs"] = ";".join(row.get("ofcs") or [])
            # authors_list es lista -> texto legible para CSV (JSON la conserva).
            row["authors_list"] = "; ".join(row.get("authors_list") or [])
            writer.writerow(row)

    return json_path, csv_path


def print_summary(records: list, source_label: str) -> None:
    """Imprime el resumen de completitud por consola.

    ``source_label`` es el nombre de la fuente que aparece en el encabezado
    (p. ej. ``"Boletin SAO"``). El resto del formato es idéntico al original.
    """
    total = len(records)
    con_titulo = sum(1 for r in records if r.title)
    con_autores = sum(1 for r in records if r.authors)
    con_year = sum(1 for r in records if r.publication_year)
    con_abstract = sum(1 for r in records if r.abstract)
    con_keywords = sum(1 for r in records if r.keywords)
    duplicados = sum(1 for r in records if r.is_duplicate)

    def pct(n: int) -> str:
        return f"{n}/{total} ({(100*n/total):.0f}%)" if total else "0/0"

    print("\n" + "=" * 60)
    print(f"RESUMEN DE EXTRACCION — Fuente: {source_label}")
    print("=" * 60)
    print(f"  PDFs procesados     : {total}")
    print(f"  Con titulo          : {pct(con_titulo)}")
    print(f"  Con autores         : {pct(con_autores)}")
    print(f"  Con año             : {pct(con_year)}")
    print(f"  Con abstract        : {pct(con_abstract)}")
    print(f"  Con keywords        : {pct(con_keywords)}")
    print(f"  Posibles duplicados : {duplicados}")
    print(f"  Todos en estado     : PENDIENTE_REVISIÓN (relevancia + OFC)")
