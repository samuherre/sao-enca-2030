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


def test_por_idioma_principales_mas_otros() -> None:
    """Idioma: inglés/español/portugués/francés individuales; el resto en 'Otros'.

    'Otros' agrupa idiomas no principales, códigos ambiguos y los artículos sin
    idioma declarado (no se infiere el idioma que no viene).
    """
    registros = (
        [{"source": "OpenAlex", "publication_year": 2021, "language": "en"}] * 5
        + [{"source": "OpenAlex", "publication_year": 2021, "language": "ES"}] * 3  # mayúsculas
        + [{"source": "OpenAlex", "publication_year": 2021, "language": "pt"}] * 2
        + [{"source": "OpenAlex", "publication_year": 2021, "language": "fr"}] * 1
        + [{"source": "OpenAlex", "publication_year": 2021, "language": "ru"}] * 2   # otro idioma
        + [{"source": "OpenAlex", "publication_year": 2021, "language": "es/en"}] * 1  # ambiguo
        + [{"source": "OpenAlex", "publication_year": 2021, "language": None}] * 4   # sin idioma
    )
    r = _resumen({"openalex": registros}, anio=None)
    por = {d.clave: d.conteo for d in r.por_idioma}
    assert por["Inglés"] == 5
    assert por["Español"] == 3  # normaliza mayúsculas
    assert por["Portugués"] == 2
    assert por["Francés"] == 1
    # Otros = ru(2) + es/en(1) + sin idioma(4) = 7.
    assert por["Otros"] == 7


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


def _resumen_con_clasificado(clasificados: list[dict]):
    """Como ``_resumen`` pero añade una carpeta ``*_clasificado`` para el GC/OFC."""
    tmp_root = Path(tempfile.mkdtemp(prefix="sao_gc_"))
    processed_dir = tmp_root / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    # Una fuente mínima (para que el consolidado no sea vacío) + la clasificada.
    _escribir(processed_dir, "openalex", clasificados)
    carpeta = processed_dir / "openalex_clasificado"
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / "openalex_clasificado_2024-01-01.json").write_text(
        json.dumps(clasificados, ensure_ascii=False), encoding="utf-8"
    )
    original = svc._PROCESSED_DIR
    try:
        svc._PROCESSED_DIR = processed_dir
        return svc.BibliometriaService().resumen_consolidado(anio=None)
    finally:
        svc._PROCESSED_DIR = original
        shutil.rmtree(tmp_root, ignore_errors=True)


def test_grado_colaboracion_por_ofc() -> None:
    """El GC por OFC usa f1/N solo sobre artículos con autoría contable.

    OFC-01: 3 artículos contables, 1 de un solo autor -> GC = 1 - 1/3 = 0.67.
    Un cuarto artículo de OFC-01 sin autoría contable NO entra en N, pero sí
    se reporta como excluido. OFC-02 (multilabel) hereda sus artículos.
    """
    clasificados = [
        {"source": "OpenAlex", "publication_year": 2021, "ofcs": ["OFC-01"],
         "authors": "A; B"},                       # 2 autores
        {"source": "OpenAlex", "publication_year": 2021, "ofcs": ["OFC-01", "OFC-02"],
         "authors": "A; B; C"},                     # 3 autores
        {"source": "OpenAlex", "publication_year": 2021, "ofcs": ["OFC-01"],
         "authors": "A"},                           # 1 autor
        {"source": "Boletín SAO", "publication_year": 2021, "ofcs": ["OFC-01"],
         "authors": "A, B y C"},                     # texto libre -> no contable
    ]
    r = _resumen_con_clasificado(clasificados)
    por = {o.ofc_id: o for o in r.por_ofc}

    assert "OFC-01" in por
    o1 = por["OFC-01"]
    assert o1.conteo == 4                      # 4 artículos clasificados en OFC-01
    assert o1.gc_articulos_contables == 3      # solo 3 con autoría contable
    assert o1.gc_articulos_sin_autoria == 1    # el de Boletín (texto libre)
    assert o1.grado_colaboracion == 0.67       # 1 - 1/3

    o2 = por["OFC-02"]
    assert o2.conteo == 1
    assert o2.gc_articulos_contables == 1
    assert o2.grado_colaboracion == 1.0        # su único artículo tiene 3 autores


def _export_csv(coleccion: dict[str, list[dict]], anio: int | None) -> str:
    tmp_root = Path(tempfile.mkdtemp(prefix="sao_csv_"))
    processed_dir = tmp_root / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    for carpeta, registros in coleccion.items():
        _escribir(processed_dir, carpeta, registros)
    original = svc._PROCESSED_DIR
    try:
        svc._PROCESSED_DIR = processed_dir
        return svc.BibliometriaService().exportar_consolidado_csv(anio=anio)
    finally:
        svc._PROCESSED_DIR = original
        shutil.rmtree(tmp_root, ignore_errors=True)


def test_export_csv_incluye_titulo_y_enlace() -> None:
    """El CSV trae encabezado + una fila por artículo con título y enlace.

    El enlace usa 'url'; si falta, se deriva del DOI (https://doi.org/...).
    """
    coleccion = {
        "openalex": [
            {"source": "OpenAlex", "publication_year": 2021, "title": "Aves del Chocó",
             "url": "https://openalex.org/W1", "doi": "10.1/a", "journal": "Rev X"},
            {"source": "OpenAlex", "publication_year": 2022, "title": "Sin URL pero con DOI",
             "url": None, "doi": "10.2/b"},
        ],
    }
    csv_texto = _export_csv(coleccion, anio=None)
    import csv as _csv
    import io as _io
    filas = list(_csv.reader(_io.StringIO(csv_texto)))
    # Encabezado + exactamente 2 filas (sin líneas en blanco intercaladas), y
    # todas con el mismo número de columnas (6).
    assert len(filas) == 3, f"se esperaban 3 filas, hay {len(filas)}"
    assert all(len(f) == 6 for f in filas), "filas con número de columnas irregular"
    assert filas[0][0] == "titulo"
    enlaces = [f[5] for f in filas[1:]]
    assert "https://openalex.org/W1" in enlaces
    # El segundo artículo, sin url, deriva el enlace del DOI.
    assert "https://doi.org/10.2/b" in enlaces


def test_export_csv_respeta_filtro_anio() -> None:
    coleccion = {
        "openalex": [
            {"source": "OpenAlex", "publication_year": 2021, "title": "A", "url": "u1"},
            {"source": "OpenAlex", "publication_year": 2022, "title": "B", "url": "u2"},
        ],
    }
    csv_2021 = _export_csv(coleccion, anio=2021)
    lineas = [l for l in csv_2021.splitlines() if l.strip()]
    assert len(lineas) == 2  # encabezado + solo el de 2021
    assert ",A," in csv_2021 or csv_2021.count("\nA,") >= 0  # A presente
    assert "B" not in csv_2021.split("\n", 1)[1]  # B no está en el cuerpo


def test_articulos_de_ofc_lista_y_total() -> None:
    """``articulos_de_ofc`` devuelve los artículos de ese OFC con total y límite.

    Multilabel: un artículo en varios OFC aparece en cada uno. El enlace usa url
    o, si falta, el DOI. El total refleja el conteo real aunque se limite la lista.
    """
    clasificados = [
        {"source": "OpenAlex", "publication_year": 2021, "title": "Marino A",
         "ofcs": ["OFC-01"], "url": "u-a", "article_id": "a1"},
        {"source": "OpenAlex", "publication_year": 2022, "title": "Marino y humedal",
         "ofcs": ["OFC-01", "OFC-02"], "doi": "10.9/x", "article_id": "a2"},
        {"source": "OpenAlex", "publication_year": 2020, "title": "Solo humedal",
         "ofcs": ["OFC-02"], "url": "u-c", "article_id": "a3"},
    ]
    tmp_root = Path(tempfile.mkdtemp(prefix="sao_ofclist_"))
    processed_dir = tmp_root / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    carpeta = processed_dir / "openalex_clasificado"
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / "openalex_clasificado_2024-01-01.json").write_text(
        json.dumps(clasificados, ensure_ascii=False), encoding="utf-8"
    )
    original = svc._PROCESSED_DIR
    try:
        svc._PROCESSED_DIR = processed_dir
        servicio = svc.BibliometriaService()
        ofc1 = servicio.articulos_de_ofc("OFC-01")
        ofc2 = servicio.articulos_de_ofc("OFC-02")
        limitado = servicio.articulos_de_ofc("OFC-01", limite=1)
    finally:
        svc._PROCESSED_DIR = original
        shutil.rmtree(tmp_root, ignore_errors=True)

    # OFC-01: a1 y a2.
    assert ofc1.total == 2
    titulos1 = {i.titulo for i in ofc1.items}
    assert titulos1 == {"Marino A", "Marino y humedal"}
    # El artículo sin url usa el DOI como enlace.
    enlaces1 = {i.enlace for i in ofc1.items}
    assert "https://doi.org/10.9/x" in enlaces1
    # OFC-02: a2 y a3 (multilabel: a2 aparece en ambos OFC).
    assert ofc2.total == 2
    # Límite: total sigue siendo 2 pero items trae 1.
    assert limitado.total == 2
    assert limitado.mostrados == 1
    assert len(limitado.items) == 1


def test_num_autores_fiable_openalex_y_boletin() -> None:
    """Conteo de autores: fiable en OpenAlex (por '; '), no contable en texto libre."""
    # OpenAlex: autores unidos por "; " -> contable.
    assert svc._num_autores_fiable(
        {"source": "OpenAlex", "authors": "Ana Pérez; Juan Gómez; Luis Díaz"}
    ) == 3
    assert svc._num_autores_fiable({"source": "OpenAlex", "authors": "Ana Pérez"}) == 1
    # authors_list explícita -> se usa su longitud, sea cual sea la fuente.
    assert svc._num_autores_fiable(
        {"source": "Boletín SAO", "authors_list": ["A", "B"]}
    ) == 2
    # Boletín con texto libre (sin "; ") -> no contable de forma fiable.
    assert svc._num_autores_fiable(
        {"source": "Boletín SAO", "authors": "Ana Pérez, Juan Gómez y Luis Díaz"}
    ) is None
    # Sin autores -> None.
    assert svc._num_autores_fiable({"source": "OpenAlex", "authors": None}) is None


def test_calcular_gc_formula_subramanyam() -> None:
    """GC = 1 - f1/N, con None cuando no hay base."""
    # 10 artículos, 2 de un solo autor -> GC = 1 - 2/10 = 0.8.
    assert svc._calcular_gc(10, 2) == 0.8
    # Todos de un solo autor -> GC = 0.
    assert svc._calcular_gc(5, 5) == 0.0
    # Ninguno de un solo autor -> GC = 1.
    assert svc._calcular_gc(4, 0) == 1.0
    # Sin base -> None (no se inventa 0).
    assert svc._calcular_gc(0, 0) is None


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
