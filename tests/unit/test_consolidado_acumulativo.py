"""Pruebas del MODELO ACUMULATIVO del servicio consolidado.

Verifican el comportamiento nuevo (decisión de producto: el dashboard de
bibliometría muestra el corpus ACUMULADO a lo largo del tiempo, no solo la
última corrida):

  - El servicio combina TODOS los datasets ``*.json`` de cada carpeta de fuente
    (histórico de corridas), no solo el más reciente.
  - Deduplica por ``article_id`` DENTRO de la fuente: la misma publicación
    recuperada en dos corridas cuenta UNA vez; la versión del dataset más
    reciente gana.
  - Registros sin ``article_id`` se conservan (no se pueden deduplicar sin clave).

Se redirige el atributo de módulo ``_PROCESSED_DIR`` a un directorio temporal
(restaurado en ``finally``), igual que el resto de pruebas del Componente B.
Los datos son SINTÉTICOS (DEMO_DATA, no reales).
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from backend.src.services import bibliometria_service as svc  # noqa: E402


def _escribir(carpeta: Path, nombre: str, registros: list[dict]) -> None:
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / nombre).write_text(json.dumps(registros, ensure_ascii=False), encoding="utf-8")


def test_acumula_varios_datasets_de_una_fuente() -> None:
    """Dos corridas de la misma fuente se ACUMULAN (unión por article_id)."""
    tmp = Path(tempfile.mkdtemp(prefix="sao_acum_"))
    processed = tmp / "processed"
    carpeta = processed / "openalex"
    # Corrida 1 (más antigua): 2 artículos.
    _escribir(carpeta, "openalex_dataset_2026-10-28.json", [
        {"article_id": "oa-1", "source": "OpenAlex", "title": "A"},
        {"article_id": "oa-2", "source": "OpenAlex", "title": "B"},
    ])
    # Corrida 2 (más reciente): oa-2 repetido + oa-3 nuevo.
    _escribir(carpeta, "openalex_dataset_2026-10-30.json", [
        {"article_id": "oa-2", "source": "OpenAlex", "title": "B"},
        {"article_id": "oa-3", "source": "OpenAlex", "title": "C"},
    ])

    original = svc._PROCESSED_DIR
    try:
        svc._PROCESSED_DIR = processed
        r = svc.BibliometriaService().resumen_consolidado()
    finally:
        svc._PROCESSED_DIR = original
        shutil.rmtree(tmp, ignore_errors=True)

    # Unión deduplicada por article_id: oa-1, oa-2, oa-3 = 3 (no 4).
    assert r.total_articulos == 3
    aporte = {a.fuente: a.total_articulos for a in r.aporte_por_fuente}
    assert aporte == {"OpenAlex": 3}


def test_version_mas_reciente_gana_en_duplicado() -> None:
    """Si el mismo article_id aparece en dos corridas, gana la más reciente."""
    tmp = Path(tempfile.mkdtemp(prefix="sao_acum_"))
    processed = tmp / "processed"
    carpeta = processed / "openalex"
    _escribir(carpeta, "openalex_dataset_2026-10-28.json", [
        {"article_id": "oa-1", "source": "OpenAlex", "title": "viejo", "publication_year": 2020},
    ])
    _escribir(carpeta, "openalex_dataset_2026-10-30.json", [
        {"article_id": "oa-1", "source": "OpenAlex", "title": "nuevo", "publication_year": 2021},
    ])

    original = svc._PROCESSED_DIR
    try:
        svc._PROCESSED_DIR = processed
        regs, fechas = svc._acumular_json(carpeta)
    finally:
        svc._PROCESSED_DIR = original
        shutil.rmtree(tmp, ignore_errors=True)

    assert len(regs) == 1
    assert regs[0]["title"] == "nuevo"       # la versión reciente gana
    assert regs[0]["publication_year"] == 2021
    assert "2026-10-28" in fechas and "2026-10-30" in fechas  # lee ambos


def test_registros_sin_article_id_se_conservan() -> None:
    """Registros sin article_id no se pueden deduplicar: se conservan todos."""
    tmp = Path(tempfile.mkdtemp(prefix="sao_acum_"))
    processed = tmp / "processed"
    carpeta = processed / "fuente_x"
    _escribir(carpeta, "fuente_x_dataset_2026-10-01.json", [
        {"source": "Fuente X", "title": "sin id 1"},
        {"source": "Fuente X", "title": "sin id 2"},
    ])

    original = svc._PROCESSED_DIR
    try:
        svc._PROCESSED_DIR = processed
        regs, _ = svc._acumular_json(carpeta)
    finally:
        svc._PROCESSED_DIR = original
        shutil.rmtree(tmp, ignore_errors=True)

    assert len(regs) == 2  # ambos conservados


def test_carpeta_vacia_devuelve_vacio() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="sao_acum_"))
    processed = tmp / "processed"
    (processed / "vacia").mkdir(parents=True, exist_ok=True)
    try:
        regs, fechas = svc._acumular_json(processed / "vacia")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    assert regs == [] and fechas == []
