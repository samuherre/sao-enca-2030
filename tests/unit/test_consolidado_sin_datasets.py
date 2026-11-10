"""Test de ejemplo del Servicio_Consolidado (spec multi-source-bibliometria, tarea 6.7).

Sin datasets bajo ``data/processed/`` → resumen vacío coherente.

    **Validates: Requirements 6.5**

A diferencia de :meth:`BibliometriaService.resumen` (fuente Boletín), que lanza
``NotFoundError`` cuando no hay dataset, :meth:`resumen_consolidado` NO lanza
excepción: el estado vacío es un resultado válido (todo en 0) para que el
frontend muestre un estado vacío honesto (Req 6.5, 8.3). El servicio no inventa
datos.

Enfoque (igual que ``test_consolidado_agregaciones.py``): se apunta el
``_PROCESSED_DIR`` del módulo a un directorio temporal vacío y se restaura en un
``finally``, limpiando el directorio temporal al terminar.
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from backend.src.services import bibliometria_service as svc

# Campos cuya completitud reporta el servicio (ver _CAMPOS_COMPLETITUD).
_CAMPOS_COMPLETITUD = ["title", "authors", "abstract", "keywords", "doi"]


def test_resumen_consolidado_sin_datasets_es_vacio_coherente() -> None:
    """Sin datasets procesados, el consolidado es un resumen vacío coherente.

    Validates: Requirements 6.5
    """
    # --- data/processed/ temporal VACÍO (sin subcarpetas ni datasets). -------
    processed_dir = Path(tempfile.mkdtemp(prefix="sao_processed_vacio_"))
    original_processed_dir = svc._PROCESSED_DIR
    try:
        svc._PROCESSED_DIR = processed_dir
        # No debe lanzar excepción (a diferencia de resumen()).
        resumen = svc.BibliometriaService().resumen_consolidado()
    finally:
        svc._PROCESSED_DIR = original_processed_dir
        shutil.rmtree(processed_dir, ignore_errors=True)

    # Alcance explícito del resumen consolidado (Req 6.4).
    assert resumen.alcance == "consolidado"

    # Total y distribuciones vacías.
    assert resumen.total_articulos == 0
    assert resumen.por_anio == []
    assert resumen.por_revista == []

    # Completitud: un entry por campo, todos en cero (no es lista vacía; el
    # servicio reporta cada campo con con_dato=0 y total=0).
    assert [c.campo for c in resumen.completitud] == _CAMPOS_COMPLETITUD
    for comp in resumen.completitud:
        assert comp.con_dato == 0, f"con_dato no es 0 para {comp.campo}"
        assert comp.total == 0, f"total no es 0 para {comp.campo}"

    # Conteos de revisión/duplicados en cero.
    assert resumen.pendientes_revision == 0
    assert resumen.posibles_duplicados == 0

    # Sin aporte por fuente ni fechas de dataset.
    assert resumen.aporte_por_fuente == []
    assert resumen.fechas_dataset == []

    # Clasificación por OFC no disponible.
    assert resumen.clasificacion_disponible is False
    assert resumen.por_ofc == []
    assert resumen.sin_ofc == 0


def test_resumen_consolidado_directorio_inexistente_es_vacio_coherente() -> None:
    """Si ``data/processed/`` no existe, el consolidado también es vacío coherente.

    Validates: Requirements 6.5
    """
    # Ruta inexistente: creamos y borramos un temporal para obtener un path que
    # no existe en el sistema de archivos.
    tmp = Path(tempfile.mkdtemp(prefix="sao_processed_inexistente_"))
    shutil.rmtree(tmp, ignore_errors=True)
    assert not tmp.exists()

    original_processed_dir = svc._PROCESSED_DIR
    try:
        svc._PROCESSED_DIR = tmp
        resumen = svc.BibliometriaService().resumen_consolidado()
    finally:
        svc._PROCESSED_DIR = original_processed_dir

    assert resumen.alcance == "consolidado"
    assert resumen.total_articulos == 0
    assert resumen.por_anio == []
    assert resumen.por_revista == []
    assert resumen.aporte_por_fuente == []
    assert resumen.fechas_dataset == []
    assert resumen.clasificacion_disponible is False
    assert resumen.por_ofc == []
    assert resumen.sin_ofc == 0
