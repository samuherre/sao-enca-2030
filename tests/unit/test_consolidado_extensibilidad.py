"""Property test del servicio consolidado (spec multi-source-bibliometria, tarea 6.6).

Property 14 del design.md — "Extensibilidad por descubrimiento":

    Para toda carpeta de fuente nueva en ``data/processed/{fuente}/`` con
    registros conformes al contrato V1, el resumen consolidado incorpora esa
    fuente (en el total y en ``aporte_por_fuente``) SIN cambios de código en el
    servicio ni en la vista.

    **Validates: Requirements 10.1**

Método bajo prueba: ``BibliometriaService.resumen_consolidado()`` en
``backend/src/services/bibliometria_service.py``. El servicio descubre las
subcarpetas de ``data/processed/`` y agrupa los registros por su campo
``source``; añadir una fuente conforme al contrato NO debe requerir editar el
servicio ni la vista (descubrimiento dinámico, Req 10.1).

Enfoque (Testing Strategy del design): se monta un ``data/processed/`` temporal
con cero o más fuentes SINTÉTICAS (datos de prueba, no reales), se computa el
resumen; luego se añade una carpeta de fuente NUEVA (nombre y campo ``source``
arbitrarios, distintos de los ya presentes) con registros conformes, se
recomputa el resumen y se verifica que:

- el total de la nueva fuente aparece reflejado en ``total_articulos``
  (incremento exactamente igual al número de registros nuevos), y
- ``aporte_por_fuente`` contiene una entrada para la nueva fuente con el conteo
  correcto.

El test no modifica el código del servicio: solo redirige el atributo de módulo
``_PROCESSED_DIR`` a un directorio temporal mediante asignación directa
(restaurada en ``finally``), igual que el resto de pruebas del Componente B.

Nota sobre hypothesis + temp dirs: el directorio temporal se crea DENTRO del
cuerpo del test y se elimina en cada ejemplo, en lugar de usar la fixture
``tmp_path`` (de ámbito de función) a través de los ejemplos; así se evita el
health-check de hypothesis sobre fixtures function-scoped y se garantiza un
``data/processed/`` limpio por ejemplo.

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

# Nombres de dispositivo RESERVADOS en Windows: no pueden usarse como nombre de
# archivo/carpeta. En particular, una ruta que contenga "NUL" como componente
# de carpeta falla con FileNotFoundError al escribir dentro (Windows lo trata
# como el dispositivo nulo). El resto (CON, PRN, AUX, COM1-9, LPT1-9) también se
# excluye para que el test sea determinista en cualquier Windows. El código de
# producción no se ve afectado: esto solo acota el generador de nombres de
# carpeta de PRUEBA a nombres de fuente válidos en el sistema de archivos.
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
# ``_clasificado`` (ese caso es de la Property 12). Se restringe a
# letras/dígitos/guion bajo/espacio para nombres válidos en Windows y POSIX.
_nombre_fuente = (
    st.text(
        alphabet=st.characters(
            whitelist_categories=("Lu", "Ll", "Nd"),
            whitelist_characters="_- ",
        ),
        min_size=1,
        max_size=20,
    )
    .map(lambda s: s.strip())
    .filter(lambda s: s != "" and not s.endswith("_clasificado") and not _es_nombre_reservado_windows(s))
)


def _registro(source: str) -> st.SearchStrategy[dict]:
    """Un registro sintético conforme (parcial) al contrato V1 con ``source`` fijo.

    Incluye campos opcionales plausibles (año, volumen, estado, duplicado) para
    ejercer el descubrimiento sin afectar el conteo total, que solo depende del
    número de registros.
    """
    return st.fixed_dictionaries(
        {"source": st.just(source)},
        optional={
            "title": st.text(min_size=0, max_size=12),
            "publication_year": st.integers(min_value=2015, max_value=2031),
            # ``volume`` conforme pero no adversarial: numérico o texto ASCII.
            # (La robustez del ordenamiento de volúmenes ante cadenas Unicode
            # arbitrarias es un concern aparte de esta propiedad de
            # extensibilidad; aquí basta con registros conformes al contrato.)
            "volume": st.one_of(
                st.integers(min_value=1, max_value=60).map(str),
                st.text(
                    alphabet=st.characters(
                        whitelist_categories=("Lu", "Ll"),
                        max_codepoint=0x7F,
                    ),
                    min_size=1,
                    max_size=4,
                ),
            ),
            "inclusion_status": st.sampled_from(["INCLUIDO", "PENDIENTE_REVISIÓN"]),
            "is_duplicate": st.booleans(),
        },
    )


@st.composite
def escenario(draw: st.DrawFn) -> tuple[dict[str, list[dict]], str, list[dict]]:
    """Genera (fuentes_iniciales, nombre_nueva_fuente, registros_nuevos).

    - ``fuentes_iniciales``: mapa fuente -> registros (puede estar vacío). El
      nombre de la carpeta coincide con el campo ``source`` de sus registros.
    - ``nombre_nueva_fuente``: nombre/``source`` de una fuente NUEVA, garantizado
      distinto de las iniciales (para verificar una entrada propia en
      ``aporte_por_fuente``).
    - ``registros_nuevos``: al menos un registro conforme para la fuente nueva.
    """
    nombres = draw(st.lists(_nombre_fuente, unique=True, min_size=0, max_size=4))
    iniciales: dict[str, list[dict]] = {}
    for nombre in nombres:
        iniciales[nombre] = draw(st.lists(_registro(nombre), min_size=0, max_size=6))

    # Fuente nueva: nombre arbitrario distinto de los existentes.
    nueva = draw(_nombre_fuente.filter(lambda s: s not in iniciales))
    # Al menos un registro para que el aporte sea observable (min_size=1).
    registros_nuevos = draw(st.lists(_registro(nueva), min_size=1, max_size=6))
    return iniciales, nueva, registros_nuevos


def _escribir_fuente(processed_dir: Path, nombre: str, registros: list[dict]) -> None:
    """Escribe una fuente como ``<nombre>/<nombre>_dataset_YYYY-MM-DD.json``.

    El servicio elige el JSON de nombre mayor por carpeta; basta un único archivo
    fechado por carpeta. Los datos son SINTÉTICOS (datos de prueba).
    """
    carpeta = processed_dir / nombre
    carpeta.mkdir(parents=True, exist_ok=True)
    archivo = carpeta / f"{nombre}_dataset_2024-01-01.json"
    archivo.write_text(json.dumps(registros, ensure_ascii=False), encoding="utf-8")


def _aporte_de(resumen, fuente: str):
    """Devuelve la entrada de ``aporte_por_fuente`` para ``fuente``, o None."""
    for a in resumen.aporte_por_fuente:
        if a.fuente == fuente:
            return a
    return None


# Feature: multi-source-bibliometria, Property 14: Extensibilidad por descubrimiento
@settings(max_examples=150, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(caso=escenario())
def test_extensibilidad_por_descubrimiento(
    caso: tuple[dict[str, list[dict]], str, list[dict]],
) -> None:
    """Añadir una fuente nueva conforme se refleja en total y aporte_por_fuente.

    **Validates: Requirements 10.1**

    Sin tocar el código del servicio: se computa el resumen con las fuentes
    iniciales, se añade una carpeta de fuente nueva con registros conformes y se
    recomputa. El incremento del total debe igualar el número de registros
    nuevos y debe aparecer una entrada propia en ``aporte_por_fuente`` con el
    conteo correcto.
    """
    iniciales, nueva, registros_nuevos = caso

    tmp_root = Path(tempfile.mkdtemp(prefix="sao_processed_"))
    processed_dir = tmp_root / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    original = svc._PROCESSED_DIR
    try:
        svc._PROCESSED_DIR = processed_dir

        # --- 1) Estado inicial: solo las fuentes iniciales -------------------
        for nombre, registros in iniciales.items():
            _escribir_fuente(processed_dir, nombre, registros)
        resumen_antes = svc.BibliometriaService().resumen_consolidado()

        total_antes = resumen_antes.total_articulos
        # La fuente nueva aún no existe, por lo que no tiene aporte.
        assert _aporte_de(resumen_antes, nueva) is None, (
            f"la fuente nueva {nueva!r} no debería existir antes de añadirla"
        )

        # --- 2) Descubrimiento: añadir la carpeta de la fuente NUEVA ---------
        # No se modifica NINGÚN código del servicio ni de la vista: solo aparece
        # una carpeta nueva conforme al contrato bajo data/processed/.
        _escribir_fuente(processed_dir, nueva, registros_nuevos)
        resumen_despues = svc.BibliometriaService().resumen_consolidado()
    finally:
        svc._PROCESSED_DIR = original
        shutil.rmtree(tmp_root, ignore_errors=True)

    n_nuevos = len(registros_nuevos)

    # a) El total refleja la incorporación de la nueva fuente (unión, sin dedup).
    assert resumen_despues.total_articulos == total_antes + n_nuevos, (
        f"total tras añadir {nueva!r}: esperado {total_antes + n_nuevos}, "
        f"obtenido {resumen_despues.total_articulos}"
    )

    # b) aporte_por_fuente contiene una entrada para la fuente nueva con el
    #    conteo correcto.
    aporte_nuevo = _aporte_de(resumen_despues, nueva)
    assert aporte_nuevo is not None, (
        f"aporte_por_fuente no incorporó la fuente nueva {nueva!r}"
    )
    assert aporte_nuevo.total_articulos == n_nuevos, (
        f"aporte de {nueva!r}: esperado {n_nuevos}, "
        f"obtenido {aporte_nuevo.total_articulos}"
    )
