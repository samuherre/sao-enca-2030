"""Property test del Servicio_Consolidado (spec multi-source-bibliometria, tarea 6.5).

Property 13 del design.md — "No hay deduplicación entre fuentes":

    Para todo conjunto combinado con títulos repetidos en fuentes distintas, el
    servicio no elimina ni combina esos registros: el ``total_articulos`` sigue
    siendo la suma de los totales por fuente.

    **Validates: Requirements 6.6**

Método bajo prueba: ``BibliometriaService.resumen_consolidado()`` en
``backend/src/services/bibliometria_service.py``. La estrategia de
deduplicación entre fuentes distintas es ``PENDING_VALIDATION`` (Req 6.6): el
servicio solo cuenta la deduplicación básica YA realizada dentro de cada
dataset y NO debe eliminar ni combinar registros duplicados entre fuentes.

Enfoque (Testing Strategy del design; espejo del patrón de
``test_bibliometria_consolidado_total_suma.py`` /
``test_consolidado_agregaciones.py``): se generan >= 2 datasets de fuente
SINTÉTICOS en carpetas temporales bajo un ``data/processed/`` de prueba, donde
ALGUNOS registros comparten un título idéntico (y por tanto su título
normalizado) ACROSS fuentes. El servicio agrupa por el campo ``source`` del
registro, así que a cada registro se le fija ``source`` igual al nombre de su
carpeta para garantizar que los títulos repetidos caen en fuentes distintas.

Se redirige el atributo de módulo ``_PROCESSED_DIR`` del servicio al directorio
temporal mediante asignación directa (restaurada en ``finally``) porque
hypothesis no reinicia las fixtures de ámbito de función entre ejemplos de
``@given``. La limpieza del temporal se hace por ejemplo.

Los datos generados por hypothesis son SINTÉTICOS (datos de prueba, no reales).
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

# Dos nombres de fuente distintos (carpetas) usados para repartir registros y
# garantizar duplicados CROSS-SOURCE. No terminan en ``_clasificado`` (ese caso
# lo cubre la Property 12), por lo que ambas cuentan al total.
_FUENTE_A = "fuente_alfa"
_FUENTE_B = "fuente_beta"

# Títulos compartidos candidatos a repetirse entre fuentes.
_titulo_compartido = st.text(
    alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),
        whitelist_characters=" ",
    ),
    min_size=1,
    max_size=15,
).map(lambda s: s.strip()).filter(lambda s: s != "")


def _registro(source: str, title: str) -> dict:
    """Registro sintético mínimo con ``source`` y ``title`` fijados.

    Solo el número de registros importa para el total; se incluyen pocos campos
    opcionales para no restar realismo sin afectar la invariante.
    """
    return {
        "source": source,
        "title": title,
        "publication_year": 2024,
        "is_duplicate": False,
    }


@st.composite
def datasets_con_titulos_cruzados(draw: st.DrawFn) -> tuple[list[dict], list[dict]]:
    """Genera (registros_fuente_A, registros_fuente_B) con títulos cruzados.

    Garantiza al menos un título compartido entre ambas fuentes: se toma una
    lista no vacía de títulos compartidos y cada uno se coloca en AMBAS fuentes
    (mismo texto => mismo título normalizado => duplicado cross-source bajo
    cualquier dedupe por título). Adicionalmente, cada fuente puede tener
    títulos propios no compartidos.
    """
    compartidos = draw(
        st.lists(_titulo_compartido, min_size=1, max_size=4, unique=True)
    )
    propios_a = draw(st.lists(_titulo_compartido, min_size=0, max_size=3))
    propios_b = draw(st.lists(_titulo_compartido, min_size=0, max_size=3))

    registros_a = [_registro(_FUENTE_A, t) for t in compartidos]
    registros_a += [_registro(_FUENTE_A, t) for t in propios_a]
    registros_b = [_registro(_FUENTE_B, t) for t in compartidos]
    registros_b += [_registro(_FUENTE_B, t) for t in propios_b]

    return registros_a, registros_b


# Feature: multi-source-bibliometria, Property 13: No hay deduplicación entre fuentes
@settings(max_examples=150, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(datasets=datasets_con_titulos_cruzados())
def test_no_dedup_entre_fuentes(datasets: tuple[list[dict], list[dict]]) -> None:
    """``total_articulos`` == suma de totales por fuente, pese a títulos cruzados.

    **Validates: Requirements 6.6**

    Pese a que algunos títulos se repiten en ``fuente_alfa`` y ``fuente_beta``,
    el servicio NO elimina ni combina esos registros entre fuentes: el total
    sigue siendo la suma de los conteos por fuente.
    """
    registros_a, registros_b = datasets

    # --- Montar un data/processed/ temporal con los dos datasets sintéticos. -
    tmp_root = Path(tempfile.mkdtemp(prefix="sao_processed_"))
    processed_dir = tmp_root / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    for carpeta, registros in ((_FUENTE_A, registros_a), (_FUENTE_B, registros_b)):
        carpeta_dir = processed_dir / carpeta
        carpeta_dir.mkdir(parents=True, exist_ok=True)
        archivo = carpeta_dir / f"{carpeta}_dataset_2024-01-01.json"
        archivo.write_text(
            json.dumps(registros, ensure_ascii=False), encoding="utf-8"
        )

    original = svc._PROCESSED_DIR
    try:
        svc._PROCESSED_DIR = processed_dir
        resumen = svc.BibliometriaService().resumen_consolidado()
    finally:
        svc._PROCESSED_DIR = original
        shutil.rmtree(tmp_root, ignore_errors=True)

    # Suma de registros reales por fuente (unión sin exclusión).
    suma_por_fuente = len(registros_a) + len(registros_b)

    # El total NO se reduce por deduplicación cross-source.
    assert resumen.total_articulos == suma_por_fuente, (
        f"total_articulos={resumen.total_articulos} != "
        f"suma por fuente={suma_por_fuente}: la deduplicación cross-source "
        "no debe eliminar ni combinar registros (Req 6.6)."
    )

    # Y coincide con la suma de los aportes reportados por fuente.
    suma_aportes = sum(a.total_articulos for a in resumen.aporte_por_fuente)
    assert resumen.total_articulos == suma_aportes, (
        f"total_articulos={resumen.total_articulos} != "
        f"suma aporte_por_fuente={suma_aportes}"
    )

    # Cada fuente conserva exactamente sus registros (ninguno se combina).
    aportes = {a.fuente: a.total_articulos for a in resumen.aporte_por_fuente}
    assert aportes.get(_FUENTE_A) == len(registros_a), (
        f"aporte de {_FUENTE_A}={aportes.get(_FUENTE_A)} != {len(registros_a)}"
    )
    assert aportes.get(_FUENTE_B) == len(registros_b), (
        f"aporte de {_FUENTE_B}={aportes.get(_FUENTE_B)} != {len(registros_b)}"
    )
