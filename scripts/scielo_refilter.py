"""
scielo_refilter.py — Re-aplica el filtro de aves CORREGIDO al dataset SciELO.

Contexto: la primera cosecha usó un filtro con un bug (términos cortos como
"pato"/"ave" encajaban como prefijo de "patógeno"/"averrhoa"), que metió ~266
falsos positivos (fitopatología, salud, horticultura). El filtro se corrigió en
``scielo_api_client.es_sobre_aves`` (palabra completa para términos cortos). Como
el dataset ya tiene el texto completo de cada artículo, este script RE-FILTRA el
JSON existente con el filtro corregido y reescribe JSON+CSV con el MISMO formato
que el pipeline (``_common.write_outputs``), sin re-descargar de la API.

Es equivalente a volver a correr el pipeline (mismos registros, mismo filtro),
pero sin ~45 min de llamadas de red redundantes. NO inventa datos: solo descarta
los que el filtro corregido ya no considera de aves.

Uso:
    python scripts/scielo_refilter.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "bibliometrics"))

from ingestion.article_record import ArticleRecord  # noqa: E402
from ingestion.scielo_api_client import es_sobre_aves  # noqa: E402
from pipelines._common import mark_duplicates, write_outputs  # noqa: E402

OUT_DIR = _REPO_ROOT / "data" / "processed" / "scielo"
BASENAME = "scielo_dataset"


def main() -> int:
    candidatos = sorted(OUT_DIR.glob("scielo_dataset_*.json"))
    if not candidatos:
        print("No hay dataset SciELO que re-filtrar.")
        return 1
    origen = candidatos[-1]
    data = json.loads(origen.read_text(encoding="utf-8"))
    print(f"Dataset origen: {origen.name} ({len(data)} registros)")

    keep_dicts = [
        d for d in data
        if es_sobre_aves(d.get("title"), d.get("abstract"), d.get("keywords"))
    ]
    print(f"Tras filtro corregido: {len(keep_dicts)} (se descartan {len(data) - len(keep_dicts)})")

    # Reconstruye ArticleRecord desde cada dict para reescribir con el mismo
    # camino que el pipeline. Solo se pasan las claves conocidas del contrato.
    campos = set(ArticleRecord.__dataclass_fields__.keys())
    records = []
    for d in keep_dicts:
        kwargs = {k: v for k, v in d.items() if k in campos}
        # is_duplicate/duplicate_of se recalculan abajo; se parte limpio.
        kwargs["is_duplicate"] = False
        kwargs["duplicate_of"] = None
        records.append(ArticleRecord(**kwargs))

    mark_duplicates(records)
    json_path, csv_path = write_outputs(records, OUT_DIR, BASENAME)

    # Si el archivo re-escrito tiene el mismo nombre (misma fecha), ya quedó
    # sobrescrito con el conjunto corregido. Si el origen tuviera otra fecha,
    # se elimina para no dejar el dataset viejo con falsos positivos.
    if origen.resolve() != json_path.resolve():
        origen.unlink(missing_ok=True)
        csv_viejo = origen.with_suffix(".csv")
        csv_viejo.unlink(missing_ok=True)
        print(f"Eliminado dataset antiguo con falsos positivos: {origen.name}")

    print(f"JSON: {json_path}")
    print(f"CSV : {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
