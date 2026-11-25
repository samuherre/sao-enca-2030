"""
process_scielo_api.py — Pipeline de ingesta por API de la fuente SciELO.

Cosecha artículos de la **colección Colombia** de SciELO vía ArticleMeta y
produce un dataset conforme al Article Data Contract V1 en
``data/processed/scielo/``. Es el análogo del pipeline de OpenAlex, pero para
una API de COSECHA (no de búsqueda): recorre revistas → códigos de artículo →
artículo, aplicando un FILTRO ESTRICTO de aves para no colar ruido.

Flujo (steering bibliometrics.md §7.3; structure.md §15):
    colección 'col'
      -> listar revistas  (iter_journal_issns)
      -> filtrar a áreas relevantes (Biológicas/Agrícolas) por v441
      -> por revista: listar códigos de artículo (iter_article_codes)
      -> bajar cada artículo (fetch_article)
      -> FILTRO de aves (es_sobre_aves) + FILTRO de año 2020-2030
      -> artículo -> ArticleRecord (article_to_record)
      -> dedupe simple por título dentro de SciELO (_common.mark_duplicates)
      -> JSON + CSV (_common.write_outputs)
      -> resumen (revistas / artículos vistos / aceptados / errores)

REGLAS (steering Componente B §4):
    - No inventa: campo ausente → None; artículo que no es de aves → se DESCARTA
      (no se incluye como "sin dato").
    - No clasifica OFC (lo hace el clasificador después, igual que OpenAlex).
    - Alcance SOLO Colombia: la colección 'col' ya es Colombia por definición.
    - data/raw es inmutable: la salida es ÚNICAMENTE data/processed/scielo/.
    - La deduplicación ENTRE fuentes (DOI/título) la aplica el servicio
      consolidado (``_dedup_entre_fuentes``), no este pipeline.

Uso (con el .venv activado) — un único comando, sin UI:
    python bibliometrics/pipelines/process_scielo_api.py
    python bibliometrics/pipelines/process_scielo_api.py --max-journals 3
    python bibliometrics/pipelines/process_scielo_api.py --issn 0366-5232 --issn 0124-5376
    python bibliometrics/pipelines/process_scielo_api.py --year-from 2020 --year-to 2030
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT / "bibliometrics") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "bibliometrics"))

from ingestion.scielo_api_client import (  # noqa: E402
    AREAS_RELEVANTES,
    ApiConfig,
    COLOMBIA_COLLECTION,
    PERIODO_MAX,
    PERIODO_MIN,
    article_to_record,
    es_sobre_aves,
    fetch_article,
    iter_article_codes,
    iter_journal_issns,
    journal_area,
    journal_metadata,
    journal_title,
)
from pipelines._common import (  # noqa: E402
    mark_duplicates,
    print_summary,
    write_outputs,
)

OUTPUT_DIR = _REPO_ROOT / "data" / "processed" / "scielo"
SOURCE_LABEL = "SciELO"
BASENAME = "scielo_dataset"


@dataclass
class _Stats:
    """Contadores del resumen de cosecha."""

    revistas_total: int = 0
    revistas_relevantes: int = 0
    articulos_vistos: int = 0
    aceptados_aves: int = 0
    descartados_no_aves: int = 0
    descartados_anio: int = 0
    errores: int = 0
    revistas_procesadas: list[str] = field(default_factory=list)
    errores_detalle: list[str] = field(default_factory=list)


def _crear_sesion() -> Any:
    """Crea la sesión HTTP real (``requests.Session``). Inyectable en tests."""
    import requests

    s = requests.Session()
    s.headers.update({"User-Agent": "sao-enca-bibliometria/0.1 (SciELO ArticleMeta)"})
    return s


def _seleccionar_revistas(
    session: Any,
    config: ApiConfig,
    stats: _Stats,
    *,
    issns_explicitos: Optional[list[str]],
    max_journals: Optional[int],
) -> list[tuple[str, str]]:
    """Devuelve ``[(issn, título)]`` de las revistas a recorrer.

    - Si se pasan ``--issn`` explícitos, se usan esos (sin filtrar por área).
    - Si no, se listan todas las de la colección y se filtran a las ÁREAS
      relevantes (Biológicas/Agrícolas) por el campo v441.
    - ``max_journals`` recorta la lista final (útil para pruebas rápidas).
    """
    if issns_explicitos:
        seleccion: list[tuple[str, str]] = []
        for issn in issns_explicitos:
            meta = journal_metadata(session, issn, config)
            seleccion.append((issn, journal_title(meta) or issn))
        stats.revistas_total = len(seleccion)
        stats.revistas_relevantes = len(seleccion)
        return seleccion[:max_journals] if max_journals else seleccion

    issns = iter_journal_issns(session, config)
    stats.revistas_total = len(issns)
    print(f"Revistas en la colección '{COLOMBIA_COLLECTION}': {len(issns)}")

    seleccion = []
    for issn in issns:
        meta = journal_metadata(session, issn, config)
        area = journal_area(meta)
        if area in AREAS_RELEVANTES:
            seleccion.append((issn, journal_title(meta) or issn))
    stats.revistas_relevantes = len(seleccion)
    print(
        f"Revistas en áreas relevantes (Biológicas/Agrícolas): "
        f"{len(seleccion)} de {len(issns)}"
    )
    return seleccion[:max_journals] if max_journals else seleccion


def run_pipeline(
    *,
    config: ApiConfig,
    year_from: int,
    year_to: int,
    issns_explicitos: Optional[list[str]] = None,
    max_journals: Optional[int] = None,
    max_articles_per_journal: Optional[int] = None,
    session: Optional[Any] = None,
    out_dir: Path = OUTPUT_DIR,
) -> tuple[list, _Stats, Optional[Path], Optional[Path]]:
    """Ejecuta la cosecha completa y escribe el dataset.

    :returns: ``(records, stats, json_path, csv_path)``. Los paths son ``None``
        si no se aceptó ningún artículo de aves.
    """
    if session is None:
        session = _crear_sesion()

    stats = _Stats()
    revistas = _seleccionar_revistas(
        session,
        config,
        stats,
        issns_explicitos=issns_explicitos,
        max_journals=max_journals,
    )

    # Pre-filtro grueso por fecha de PROCESAMIENTO: un año antes de year_from
    # para no recorrer décadas de artículos antiguos. El año de publicación real
    # se valida después, por artículo (filtro fino y preciso).
    from_date = f"{max(1900, year_from - 1)}-01-01"

    records: list = []
    for issn, titulo in revistas:
        print(f"\n  -> Revista {issn}  {titulo}")
        aceptados_revista = 0
        vistos_revista = 0
        try:
            for code in iter_article_codes(session, issn, config, from_date=from_date):
                stats.articulos_vistos += 1
                vistos_revista += 1
                if (
                    max_articles_per_journal is not None
                    and vistos_revista > max_articles_per_journal
                ):
                    break
                try:
                    payload = fetch_article(session, code, config)
                except Exception as exc:  # noqa: BLE001 — un artículo roto no aborta
                    stats.errores += 1
                    stats.errores_detalle.append(f"{issn}/{code}: {exc}")
                    continue

                rec = article_to_record(payload)

                # Filtro de año 2020-2030 (descartar, no marcar): el corpus es
                # comparable con OpenAlex.
                if rec.publication_year is None or not (
                    year_from <= rec.publication_year <= year_to
                ):
                    stats.descartados_anio += 1
                    continue

                # Filtro ESTRICTO de aves.
                if not es_sobre_aves(rec.title, rec.abstract, rec.keywords):
                    stats.descartados_no_aves += 1
                    continue

                records.append(rec)
                stats.aceptados_aves += 1
                aceptados_revista += 1
        except Exception as exc:  # noqa: BLE001 — error listando: registrar y seguir
            stats.errores += 1
            stats.errores_detalle.append(f"{issn} (listado): {exc}")

        stats.revistas_procesadas.append(
            f"{issn} {titulo}: {aceptados_revista} de aves / {vistos_revista} vistos"
        )
        print(f"     aceptados de aves: {aceptados_revista} (de {vistos_revista} vistos)")

    # Dedupe simple por título DENTRO de SciELO (la dedup entre fuentes la hace
    # el servicio consolidado).
    mark_duplicates(records)

    json_path: Optional[Path] = None
    csv_path: Optional[Path] = None
    if records:
        json_path, csv_path = write_outputs(records, out_dir, BASENAME)

    return records, stats, json_path, csv_path


def _print_stats(stats: _Stats, procesados: int) -> None:
    print("\n" + "=" * 60)
    print(f"RESUMEN DE COSECHA — Fuente: {SOURCE_LABEL}")
    print("=" * 60)
    print(f"  Revistas en colección    : {stats.revistas_total}")
    print(f"  Revistas relevantes      : {stats.revistas_relevantes}")
    print(f"  Artículos vistos         : {stats.articulos_vistos}")
    print(f"  Aceptados (de aves)      : {stats.aceptados_aves}")
    print(f"  Descartados (no aves)    : {stats.descartados_no_aves}")
    print(f"  Descartados (año fuera)  : {stats.descartados_anio}")
    print(f"  Errores                  : {stats.errores}")
    print(f"  Registros escritos       : {procesados}")
    if stats.errores_detalle:
        print("  Errores (detalle, hasta 10):")
        for linea in stats.errores_detalle[:10]:
            print(f"    - {linea}")


def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Pipeline de cosecha de SciELO (colección Colombia) por API "
            "ArticleMeta. Filtro estricto de aves. Escribe en data/processed/scielo/."
        ),
    )
    p.add_argument(
        "--issn", action="append", default=[], metavar="ISSN",
        help="Recorrer SOLO esta(s) revista(s) por ISSN (repetible). Si se omite, "
        "se recorren todas las revistas de áreas Biológicas/Agrícolas.",
    )
    p.add_argument(
        "--year-from", type=int, default=PERIODO_MIN, dest="year_from",
        help=f"Año inicial del período (por defecto {PERIODO_MIN}).",
    )
    p.add_argument(
        "--year-to", type=int, default=PERIODO_MAX, dest="year_to",
        help=f"Año final del período (por defecto {PERIODO_MAX}).",
    )
    p.add_argument(
        "--max-journals", type=int, default=None, dest="max_journals",
        help="Límite de revistas a recorrer (para pruebas rápidas).",
    )
    p.add_argument(
        "--max-articles-per-journal", type=int, default=None,
        dest="max_articles_per_journal",
        help="Límite de artículos VISTOS por revista (para pruebas rápidas).",
    )
    p.add_argument(
        "--pace-seconds", type=float, default=0.2, dest="pace_seconds",
        help="Pausa entre solicitudes para acotar el ritmo.",
    )
    return p.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = _parse_args(argv)
    config = ApiConfig(pace_seconds=args.pace_seconds)

    try:
        records, stats, json_path, csv_path = run_pipeline(
            config=config,
            year_from=args.year_from,
            year_to=args.year_to,
            issns_explicitos=args.issn or None,
            max_journals=args.max_journals,
            max_articles_per_journal=args.max_articles_per_journal,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"\n[ERROR] La cosecha de SciELO falló: {exc}")
        return 2

    _print_stats(stats, len(records))

    if not records:
        print("\nNo se aceptó ningún artículo de aves (no se escribió dataset).")
        return 0

    print_summary(records, SOURCE_LABEL)
    print("\nArchivos generados:")
    print(f"  JSON: {json_path}")
    print(f"  CSV : {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
