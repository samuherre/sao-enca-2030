"""Pruebas del filtro por año del resumen consolidado (Componente B).

Verifican el nuevo parámetro ``anio`` de
``BibliometriaService.resumen_consolidado`` sin tocar la base de datos: se
redirige el atributo de módulo ``_PROCESSED_DIR`` a un ``data/processed/`` de
prueba con datasets SINTÉTICOS (datos de prueba, no reales) y se comprueba que:

- ``anios_disponibles`` SIEMPRE lista todos los años del conjunto, con o sin
  filtro aplicado (para poblar el desplegable del frontend).
- Con ``anio``, todas las agregaciones (total, por_revista, completitud,
  aporte_por_fuente, OFC) se calculan solo sobre los artículos de ese año.
- Sin ``anio`` (``None``), el resumen abarca todos los años y
  ``anio_seleccionado`` es ``None``.
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


def _escribir(processed_dir: Path, carpeta: str, registros: list[dict]) -> None:
    destino = processed_dir / carpeta
    destino.mkdir(parents=True, exist_ok=True)
    archivo = destino / f"{carpeta}_dataset_2024-01-01.json"
    archivo.write_text(json.dumps(registros, ensure_ascii=False), encoding="utf-8")


def _resumen(coleccion: dict[str, list[dict]], anio: int | None):
    tmp_root = Path(tempfile.mkdtemp(prefix="sao_anio_"))
    processed_dir = tmp_root / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    for carpeta, registros in coleccion.items():
        _escribir(processed_dir, carpeta, registros)
    original = svc._PROCESSED_DIR
    try:
        svc._PROCESSED_DIR = processed_dir
        return svc.BibliometriaService().resumen_consolidado(anio=anio)
    finally:
        svc._PROCESSED_DIR = original
        shutil.rmtree(tmp_root, ignore_errors=True)


_DATASET = {
    "openalex": [
        {"source": "OpenAlex", "publication_year": 2020, "volume": "1", "title": "a"},
        {"source": "OpenAlex", "publication_year": 2020, "volume": "1", "title": "b"},
        {"source": "OpenAlex", "publication_year": 2022, "volume": "2", "title": "c"},
    ],
    "boletin_sao": [
        {"source": "Boletin SAO", "publication_year": 2022, "volume": "9", "title": "d"},
        {"source": "Boletin SAO", "publication_year": 2023, "volume": "9", "title": "e"},
    ],
}


def test_sin_filtro_abarca_todos_los_anios() -> None:
    r = _resumen(_DATASET, anio=None)
    assert r.total_articulos == 5
    assert r.anio_seleccionado is None
    assert r.anios_disponibles == [2020, 2022, 2023]


def test_por_revista_top_30_mas_otros() -> None:
    """La distribución por revista muestra el top 30 y agrupa el resto en 'Otros'.

    Se generan 35 revistas con conteos decrecientes; deben aparecer las 30 con
    más artículos más una barra 'Otros' con la suma de las 5 restantes. Los
    registros sin revista no se cuentan ni se inventan.
    """
    registros = []
    # 35 revistas: la revista i tiene (40 - i) artículos (conteos decrecientes).
    for i in range(1, 36):
        for _ in range(40 - i):
            registros.append(
                {"source": "OpenAlex", "publication_year": 2021, "journal": f"Revista {i:02d}"}
            )
    # Dos registros sin revista: no deben contarse.
    registros.append({"source": "OpenAlex", "publication_year": 2021, "journal": None})
    registros.append({"source": "OpenAlex", "publication_year": 2021})

    r = _resumen({"openalex": registros}, anio=None)
    por_revista = r.por_revista

    # 30 revistas individuales + 1 barra "Otros".
    assert len(por_revista) == 31
    assert por_revista[-1].clave == "Otros"
    # Las 30 primeras son las de mayor conteo (Revista 01..30), ordenadas desc.
    claves_top = [c.clave for c in por_revista[:30]]
    assert claves_top[0] == "Revista 01"  # la de más artículos
    assert "Revista 31" not in claves_top  # cae en "Otros"
    # "Otros" = suma de las revistas 31..35 = (9+8+7+6+5) = 35.
    assert por_revista[-1].conteo == 35
    # Ninguna barra cuenta los 2 registros sin revista.
    total_contado = sum(c.conteo for c in por_revista)
    assert total_contado == sum(40 - i for i in range(1, 36))


def test_resumen_incluye_explicacion_publica_de_ofc() -> None:
    """El consolidado trae el texto oficial y el catálogo de los 11 OFC.

    Permite que el dashboard explique al público qué son los OFC. El contenido
    proviene del catálogo oficial ENCA 2030 (no inventado).
    """
    r = _resumen(_DATASET, anio=None)
    assert "objetos focales" in r.ofc_descripcion.lower()
    assert len(r.catalogo_ofc) == 11
    primero = r.catalogo_ofc[0]
    assert primero.ofc_id == "OFC-01"
    assert primero.nombre and primero.definicion


def test_filtro_anio_recorta_el_total() -> None:
    r = _resumen(_DATASET, anio=2020)
    assert r.total_articulos == 2
    assert r.anio_seleccionado == 2020
    # Los años disponibles NO cambian con el filtro (para el desplegable).
    assert r.anios_disponibles == [2020, 2022, 2023]


def test_filtro_anio_recorta_por_fuente() -> None:
    r = _resumen(_DATASET, anio=2022)
    assert r.total_articulos == 2
    aporte = {a.fuente: a.total_articulos for a in r.aporte_por_fuente}
    # 2022 tiene 1 de OpenAlex y 1 de Boletin SAO.
    assert aporte.get("OpenAlex") == 1
    assert aporte.get("Boletin SAO") == 1


def test_filtro_anio_sin_articulos_devuelve_vacio_coherente() -> None:
    r = _resumen(_DATASET, anio=1800)
    assert r.total_articulos == 0
    assert r.anio_seleccionado == 1800
    # Aun sin resultados, el desplegable conserva los años reales del conjunto.
    assert r.anios_disponibles == [2020, 2022, 2023]


def test_anio_cero_o_invalido_no_aparece_en_el_desplegable() -> None:
    """Un ``publication_year`` 0/None es metadata errónea: no genera opción.

    Los artículos con año no fiable SIGUEN contando en el total de "Todos"
    (no se inventan ni se descartan), pero no producen una opción de año espuria.
    """
    coleccion = {
        "openalex": [
            {"source": "OpenAlex", "publication_year": 0, "title": "sin-anio-1"},
            {"source": "OpenAlex", "publication_year": None, "title": "sin-anio-2"},
            {"source": "OpenAlex", "publication_year": 2021, "title": "ok"},
        ],
    }
    r = _resumen(coleccion, anio=None)
    assert r.total_articulos == 3  # los 3 siguen contando en "Todos"
    assert r.anios_disponibles == [2021]  # ni 0 ni None como opción
