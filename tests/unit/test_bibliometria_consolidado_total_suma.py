"""Property test del servicio consolidado (spec multi-source-bibliometria, tarea 6.2).

Property 10 del design.md — "El total consolidado es la suma por fuente":

    Para toda colección de datasets de fuente bajo ``data/processed/``, el
    ``total_articulos`` del resumen consolidado es igual a la suma de los totales
    de cada fuente (unión sin exclusión), y es igual a la suma de los
    ``aporte_por_fuente[*].total_articulos``.

    **Validates: Requirements 6.1, 7.1**

Método bajo prueba: ``BibliometriaService.resumen_consolidado()`` en
``backend/src/services/bibliometria_service.py``. El servicio descubre las
subcarpetas de ``data/processed/`` y agrupa los registros por su campo
``source``; las carpetas/archivos ``*_clasificado`` NO aportan artículos al
total (solo alimentan ``por_ofc``).

Enfoque (Testing Strategy del design): se generan datasets de fuente SINTÉTICOS
(datos de prueba, no reales) en carpetas temporales bajo un ``data/processed/``
de prueba, se redirige el atributo de módulo ``_PROCESSED_DIR`` del servicio a
ese directorio temporal mediante asignación directa (restaurada en ``finally``)
y se verifica la igualdad de totales.

Nota sobre hypothesis + temp dirs: los directorios temporales se crean DENTRO
del cuerpo del test (con ``tempfile.mkdtemp``) y se eliminan en cada ejemplo, en
lugar de usar la fixture ``tmp_path`` (de ámbito de función) a través de los
ejemplos. Así se evita el health-check de hypothesis sobre fixtures de ámbito de
función y se garantiza un ``data/processed/`` limpio por ejemplo.
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
# LPT1-9): no pueden usarse como componente de ruta. Escribir un archivo bajo
# una carpeta llamada "NUL" falla con FileNotFoundError en Windows. Se excluyen
# del generador de nombres de carpeta de PRUEBA para que el test sea
# determinista en cualquier Windows. No afecta al código de producción.
_WINDOWS_RESERVADOS = (
    {"CON", "PRN", "AUX", "NUL"}
    | {f"COM{i}" for i in range(1, 10)}
    | {f"LPT{i}" for i in range(1, 10)}
)


def _es_nombre_reservado_windows(nombre: str) -> bool:
    """True si ``nombre`` (ignorando extensión y mayúsculas) es reservado en Windows."""
    base = nombre.split(".")[0].strip().upper()
    return base in _WINDOWS_RESERVADOS

# --- Generadores de datos SINTÉTICOS (no reales) -----------------------------

# Nombres de fuente/carpeta plausibles, sin separadores de ruta ni el sufijo
# ``_clasificado`` (ese caso lo cubre la Property 12). Se restringe a
# letras/dígitos/guion bajo para nombres de carpeta válidos en Windows y POSIX.
_nombre_fuente = st.text(
    alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),
        whitelist_characters="_- ",
    ),
    min_size=1,
    max_size=20,
).map(lambda s: s.strip()).filter(
    lambda s: s != "" and not s.endswith("_clasificado") and not _es_nombre_reservado_windows(s)
)


def _registro(source: str) -> st.SearchStrategy[dict]:
    """Un registro sintético mínimo con su campo ``source`` fijado.

    Incluye algunos campos opcionales plausibles (año, volumen) para ejercer las
    agregaciones sin que ello afecte al conteo total, que solo depende del número
    de registros.
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
    """Genera un mapa carpeta_fuente -> lista de registros (puede ser vacío).

    Cada carpeta representa una fuente distinta; a cada registro se le fija su
    propio campo ``source`` igual al nombre de la carpeta para que el servicio
    agrupe de forma determinista por el valor del registro (Req 10.1). El número
    de fuentes y de registros por fuente es arbitrario, incluyendo 0 fuentes y
    fuentes sin registros (lista vacía).
    """
    nombres = draw(
        st.lists(_nombre_fuente, unique=True, min_size=0, max_size=5)
    )
    coleccion: dict[str, list[dict]] = {}
    for nombre in nombres:
        registros = draw(
            st.lists(_registro(nombre), min_size=0, max_size=8)
        )
        coleccion[nombre] = registros
    return coleccion


def _escribir_datasets(processed_dir: Path, coleccion: dict[str, list[dict]]) -> None:
    """Escribe cada fuente como ``<carpeta>/<carpeta>_dataset_YYYY-MM-DD.json``.

    El servicio elige el JSON de nombre mayor por carpeta; basta un único archivo
    fechado por carpeta. Los datos son SINTÉTICOS (datos de prueba).
    """
    for nombre, registros in coleccion.items():
        carpeta = processed_dir / nombre
        carpeta.mkdir(parents=True, exist_ok=True)
        archivo = carpeta / f"{nombre}_dataset_2024-01-01.json"
        archivo.write_text(
            json.dumps(registros, ensure_ascii=False), encoding="utf-8"
        )


# Feature: multi-source-bibliometria, Property 10: El total consolidado es la suma por fuente
@settings(max_examples=150, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(coleccion=coleccion_de_fuentes())
def test_total_consolidado_es_suma_por_fuente(coleccion: dict[str, list[dict]]) -> None:
    """``total_articulos`` == suma por fuente == suma de ``aporte_por_fuente``.

    **Validates: Requirements 6.1, 7.1**
    """
    tmp_root = Path(tempfile.mkdtemp(prefix="sao_processed_"))
    processed_dir = tmp_root / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    _escribir_datasets(processed_dir, coleccion)

    original = svc._PROCESSED_DIR
    try:
        # Redirigir el atributo de módulo usado por ``_carpetas_procesadas``.
        svc._PROCESSED_DIR = processed_dir
        resumen = svc.BibliometriaService().resumen_consolidado()
    finally:
        svc._PROCESSED_DIR = original
        shutil.rmtree(tmp_root, ignore_errors=True)

    # Suma de registros reales por fuente (unión sin exclusión).
    suma_por_fuente = sum(len(regs) for regs in coleccion.values())
    # Suma de los aportes reportados por el servicio.
    suma_aportes = sum(a.total_articulos for a in resumen.aporte_por_fuente)

    assert resumen.total_articulos == suma_por_fuente, (
        f"total_articulos={resumen.total_articulos} != "
        f"suma por fuente={suma_por_fuente}"
    )
    assert resumen.total_articulos == suma_aportes, (
        f"total_articulos={resumen.total_articulos} != "
        f"suma aporte_por_fuente={suma_aportes}"
    )
