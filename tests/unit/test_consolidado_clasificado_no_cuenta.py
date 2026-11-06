"""Property test del servicio consolidado (spec multi-source-bibliometria, tarea 6.4).

Property 12 del design.md — "Los datasets clasificados no se cuentan como fuente":

    Para toda presencia de un dataset clasificado (``*_clasificado``) derivado de
    una fuente ya contada, el ``total_articulos`` consolidado no cambia respecto
    a contar solo las fuentes; el dataset clasificado solo contribuye a
    ``por_ofc``.

    **Validates: Requirements 6.7**

Método bajo prueba: ``BibliometriaService.resumen_consolidado()`` en
``backend/src/services/bibliometria_service.py``. El servicio detecta los
datasets clasificados por carpeta cuyo nombre termina en ``_clasificado`` o que
contiene archivos ``*_clasificado_*.json``; esas carpetas NO aportan artículos
al total: solo alimentan ``por_ofc`` / ``sin_ofc``.

Enfoque (Testing Strategy del design): se generan datasets de fuente SINTÉTICOS
(datos de prueba, no reales) en carpetas temporales bajo un ``data/processed/``
de prueba. Se calcula el resumen SIN carpeta clasificada; luego se añade una
carpeta ``*_clasificado`` (con registros que tienen ``ofcs``) y se recalcula. Se
verifica que ``total_articulos`` NO cambia y que ``por_ofc`` pasa a reflejar la
clasificación (``clasificacion_disponible == True``).

Para aislar el servicio del repo real, se redirige el atributo de módulo
``_PROCESSED_DIR`` mediante asignación directa, restaurada en un ``finally``, y
se crea/limpia un directorio temporal propio por ejemplo (hypothesis no reinicia
fixtures function-scoped entre ejemplos de ``@given``).

Los datos generados por hypothesis son SINTÉTICOS (DEMO_DATA, no reales).
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

# El servicio importa desde el paquete ``backend.src``; aseguramos la raíz del
# repo en sys.path (mismo patrón que el resto de pruebas del Componente B).
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from hypothesis import HealthCheck, given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

from backend.src.services import bibliometria_service as svc  # noqa: E402

# Nombres de dispositivo RESERVADOS en Windows (CON, PRN, AUX, NUL, COM1-9,
# LPT1-9): no pueden usarse como componente de ruta. En particular, escribir un
# archivo bajo una carpeta llamada "NUL" falla con FileNotFoundError (Windows lo
# trata como el dispositivo nulo). Se excluyen del generador de nombres de
# carpeta de PRUEBA para que el test sea determinista en cualquier Windows. No
# afecta al código de producción.
_WINDOWS_RESERVADOS = (
    {"CON", "PRN", "AUX", "NUL"}
    | {f"COM{i}" for i in range(1, 10)}
    | {f"LPT{i}" for i in range(1, 10)}
)


def _es_nombre_reservado_windows(nombre: str) -> bool:
    """True si ``nombre`` (ignorando extensión y mayúsculas) es reservado en Windows."""
    base = nombre.split(".")[0].strip().upper()
    return base in _WINDOWS_RESERVADOS

# Los 11 OFC válidos del catálogo (ids). Los registros clasificados referencian
# estos ids en su campo ``ofcs`` (relación multilabel).
_OFC_IDS = [f"OFC-{n:02d}" for n in range(1, 12)]


def _nombre_fuente_strategy() -> st.SearchStrategy[str]:
    """Nombres de carpeta de fuente válidos, SIN el sufijo ``_clasificado``.

    Se restringe a letras/dígitos/guion/guion_bajo/espacio para nombres de
    carpeta válidos en Windows y POSIX, y se descartan los que terminan en
    ``_clasificado`` (ese es el caso que el test añade aparte).
    """
    return (
        st.text(
            alphabet=st.characters(
                whitelist_categories=("Lu", "Ll", "Nd"),
                whitelist_characters="_- ",
            ),
            min_size=1,
            max_size=18,
        )
        .map(lambda s: s.strip())
        .filter(lambda s: s != "" and not s.endswith("_clasificado") and not _es_nombre_reservado_windows(s))
    )


def _registro_fuente(source: str) -> st.SearchStrategy[dict]:
    """Un registro de fuente sintético con su campo ``source`` fijado.

    Incluye campos opcionales plausibles (año, volumen) que ejercen las
    agregaciones sin afectar el conteo total (que solo depende del número de
    registros). Ningún registro de fuente trae ``ofcs``: la distribución por OFC
    proviene exclusivamente del dataset clasificado.
    """
    return st.fixed_dictionaries(
        {"source": st.just(source)},
        optional={
            "title": st.text(min_size=0, max_size=12),
            "publication_year": st.integers(min_value=2015, max_value=2031),
            "volume": st.one_of(
                st.integers(min_value=1, max_value=60).map(str),
                st.text(min_size=1, max_size=4),
            ),
            "inclusion_status": st.sampled_from(["INCLUIDO", "PENDIENTE_REVISIÓN"]),
            "is_duplicate": st.booleans(),
        },
    )


@st.composite
def coleccion_de_fuentes(draw: st.DrawFn) -> dict[str, list[dict]]:
    """Mapa carpeta_fuente -> registros sintéticos (una o más fuentes).

    Se exige al menos una fuente con al menos un registro para que el dataset
    clasificado sea "derivado de una fuente ya contada" (enunciado de la
    propiedad). El resto de fuentes/registros es arbitrario.
    """
    nombres = draw(
        st.lists(_nombre_fuente_strategy(), unique=True, min_size=1, max_size=4)
    )
    coleccion: dict[str, list[dict]] = {}
    for i, nombre in enumerate(nombres):
        min_size = 1 if i == 0 else 0  # la primera fuente aporta >= 1 registro.
        registros = draw(st.lists(_registro_fuente(nombre), min_size=min_size, max_size=8))
        coleccion[nombre] = registros
    return coleccion


@st.composite
def registros_clasificados(draw: st.DrawFn) -> list[dict]:
    """Registros de un dataset clasificado: cada uno con 0+ ids OFC en ``ofcs``.

    Al menos un registro para que la clasificación sea "disponible". Un ``ofcs``
    vacío cuenta como ``sin_ofc``; los ids presentes alimentan ``por_ofc``.
    """
    def _registro() -> st.SearchStrategy[dict]:
        return st.fixed_dictionaries(
            {
                "source": st.sampled_from(["Fuente X", "Boletín SAO"]),
                "ofcs": st.lists(
                    st.sampled_from(_OFC_IDS), min_size=0, max_size=4, unique=True
                ),
            }
        )

    return draw(st.lists(_registro(), min_size=1, max_size=10))


def _escribir_fuentes(processed_dir: Path, coleccion: dict[str, list[dict]]) -> None:
    """Escribe cada fuente como ``<carpeta>/<carpeta>_dataset_YYYY-MM-DD.json``."""
    for nombre, registros in coleccion.items():
        carpeta = processed_dir / nombre
        carpeta.mkdir(parents=True, exist_ok=True)
        archivo = carpeta / f"{nombre}_dataset_2024-01-01.json"
        archivo.write_text(json.dumps(registros, ensure_ascii=False), encoding="utf-8")


def _esperado_por_ofc(clasificados: list[dict]) -> tuple[dict[str, int], int]:
    """Distribución esperada (ofc_id -> conteo) y ``sin_ofc`` a partir de ``ofcs``."""
    dist: dict[str, int] = {}
    sin_ofc = 0
    for r in clasificados:
        ofcs = r.get("ofcs") or []
        if not ofcs:
            sin_ofc += 1
        for ofc_id in ofcs:
            dist[ofc_id] = dist.get(ofc_id, 0) + 1
    return dist, sin_ofc


# Feature: multi-source-bibliometria, Property 12: Los datasets clasificados no se cuentan como fuente
@settings(max_examples=150, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(coleccion=coleccion_de_fuentes(), clasificados=registros_clasificados())
def test_clasificado_no_cuenta_como_fuente(
    coleccion: dict[str, list[dict]], clasificados: list[dict]
) -> None:
    """El dataset clasificado no altera el total; solo aporta ``por_ofc``.

    **Validates: Requirements 6.7**
    """
    # --- 1) Resumen SOLO con fuentes (sin carpeta clasificada). --------------
    tmp_sin = Path(tempfile.mkdtemp(prefix="sao_processed_sin_"))
    processed_sin = tmp_sin / "processed"
    processed_sin.mkdir(parents=True, exist_ok=True)
    _escribir_fuentes(processed_sin, coleccion)

    original = svc._PROCESSED_DIR
    try:
        svc._PROCESSED_DIR = processed_sin
        resumen_sin = svc.BibliometriaService().resumen_consolidado()
    finally:
        svc._PROCESSED_DIR = original
        shutil.rmtree(tmp_sin, ignore_errors=True)

    # --- 2) Resumen con fuentes + una carpeta ``*_clasificado``. -------------
    tmp_con = Path(tempfile.mkdtemp(prefix="sao_processed_con_"))
    processed_con = tmp_con / "processed"
    processed_con.mkdir(parents=True, exist_ok=True)
    _escribir_fuentes(processed_con, coleccion)

    # Carpeta clasificada: nombre terminado en ``_clasificado`` y archivo con el
    # patrón ``*_clasificado_*.json`` (ambas señales que el servicio reconoce).
    carpeta_clasif = processed_con / "boletin_sao_clasificado"
    carpeta_clasif.mkdir(parents=True, exist_ok=True)
    (carpeta_clasif / "boletin_sao_clasificado_2024-01-01.json").write_text(
        json.dumps(clasificados, ensure_ascii=False), encoding="utf-8"
    )

    try:
        svc._PROCESSED_DIR = processed_con
        resumen_con = svc.BibliometriaService().resumen_consolidado()
    finally:
        svc._PROCESSED_DIR = original
        shutil.rmtree(tmp_con, ignore_errors=True)

    # --- 3) El total NO cambia al añadir el dataset clasificado. -------------
    suma_por_fuente = sum(len(regs) for regs in coleccion.values())
    assert resumen_sin.total_articulos == suma_por_fuente, (
        f"total sin clasificado ({resumen_sin.total_articulos}) != "
        f"suma por fuente ({suma_por_fuente})"
    )
    assert resumen_con.total_articulos == resumen_sin.total_articulos, (
        f"el dataset clasificado alteró el total: "
        f"con={resumen_con.total_articulos}, sin={resumen_sin.total_articulos}"
    )

    # El aporte por fuente tampoco incorpora la carpeta clasificada como fuente.
    fuentes_reportadas = {a.fuente for a in resumen_con.aporte_por_fuente}
    assert "boletin_sao_clasificado" not in fuentes_reportadas, (
        "la carpeta clasificada no debe aparecer como fuente en aporte_por_fuente"
    )
    assert sum(a.total_articulos for a in resumen_con.aporte_por_fuente) == (
        resumen_con.total_articulos
    )

    # --- 4) Sin clasificado no hay OFC; con clasificado sí (solo ``por_ofc``).
    assert resumen_sin.clasificacion_disponible is False
    assert resumen_sin.por_ofc == []

    assert resumen_con.clasificacion_disponible is True, (
        "la presencia de un dataset clasificado debe activar clasificacion_disponible"
    )

    esperado_dist, esperado_sin_ofc = _esperado_por_ofc(clasificados)
    obtenido_dist = {c.ofc_id: c.conteo for c in resumen_con.por_ofc}
    assert obtenido_dist == esperado_dist, (
        f"distribución por OFC inesperada: obtenido={obtenido_dist}, "
        f"esperado={esperado_dist}"
    )
    assert resumen_con.sin_ofc == esperado_sin_ofc, (
        f"sin_ofc inesperado: obtenido={resumen_con.sin_ofc}, "
        f"esperado={esperado_sin_ofc}"
    )
