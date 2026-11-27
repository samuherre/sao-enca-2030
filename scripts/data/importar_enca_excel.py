"""Importa la jerarquía ENCA real de SAO desde el Excel de ejes estratégicos.

Lee el CSV exportado de la hoja "Ejes estratégicos ENCA" (datos REALES de SAO,
no DEMO_DATA) y puebla la base de datos con la jerarquía de cinco niveles:

    Eje → Meta → Objetivo SMART → Indicador → Actividad

ORIGEN Y COLUMNAS (solo A–H; el resto del Excel se ignora a propósito)
----------------------------------------------------------------------
    A  LINEAS ESTRATEGICAS ENCA 2030  -> Eje (fila que empieza por "EJE N:")
    C  METAS                          -> Meta (texto)
    D  (código objetivo, 1.1.)        -> se antepone al texto del objetivo
    E  OBJETIVO SMART                 -> Objetivo (texto)
    F  INDICADORES                    -> Indicador (texto)
    G  (código actividad, 1.1.1)      -> se antepone al texto de la actividad
    H  Actividades                    -> Actividad (texto)
Las columnas I en adelante (progreso regional, comentarios) NO se importan:
Julián pidió mostrar solo de ejes a actividades.

REGLA DE AGRUPACIÓN — "empaquetar hacia arriba" (decisión de Julián)
--------------------------------------------------------------------
El Excel usa celdas COMBINADAS: una meta/objetivo/indicador ocupa varias filas
y las de abajo quedan vacías. Se aplica FORWARD-FILL: cada fila hereda el último
valor NO vacío de su columna. Así, un objetivo pertenece a la meta vigente (la
más reciente vista), un indicador al objetivo vigente, y una actividad al
indicador vigente. Esto resuelve, de forma determinista y fiel a la indicación
de Julián, los ejes con varias metas (2, 4, 5), donde el Excel no dice
explícitamente qué objetivo va con qué meta: se asigna a la meta inmediatamente
anterior ("hacia arriba").

NO INVENTA (product.md §15): el texto va tal cual del Excel (solo se normaliza
el espaciado y se antepone el código cuando existe). Las celdas vacías reales no
se rellenan. Un indicador/actividad sin un objetivo/indicador vigente se omite y
se reporta (no se cuelga de una raíz inventada).

USO (desde la raíz, con el .venv activado)
------------------------------------------
    # Previsualizar sin tocar la base (recomendado primero):
    python scripts/data/importar_enca_excel.py --dry-run

    # Importar contra la base configurada (DATABASE_URL). --reset BORRA la
    # jerarquía existente (incluye DEMO_DATA) antes de insertar la real:
    python scripts/data/importar_enca_excel.py --reset

    # Verificación sin PostgreSQL (SQLite en memoria, no persiste):
    python scripts/data/importar_enca_excel.py --sqlite-memory --dry-run
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from sqlalchemy import create_engine, delete  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

from backend.src.models.actividad import ActividadModel  # noqa: E402
from backend.src.models.base import Base  # noqa: E402
from backend.src.models.eje import EjeModel  # noqa: E402
from backend.src.models.indicador import IndicadorModel  # noqa: E402
from backend.src.models.meta import MetaModel  # noqa: E402
from backend.src.models.objetivo import ObjetivoModel  # noqa: E402

# Ruta del CSV fuente (datos reales de SAO).
_CSV_DEFAULT = (
    _PROJECT_ROOT
    / "data"
    / "raw"
    / "enca"
    / "Copia de Ejes estratégicos ENCA - Hoja 1.csv"
)

# Índices de columna (0-based) de interés.
_COL_EJE = 0
_COL_META = 2
_COL_OBJ_COD = 3
_COL_OBJ_TXT = 4
_COL_IND = 5
_COL_ACT_COD = 6
_COL_ACT_TXT = 7


def _limpiar(texto: str | None) -> str:
    """Normaliza espacios/saltos de línea a un espacio simple; '' si es None."""
    if not texto:
        return ""
    return re.sub(r"\s+", " ", texto.strip())


def _con_codigo(codigo: str, texto: str) -> str:
    """Antepone el código (p. ej. '1.1.') al texto, sin duplicar si ya lo trae."""
    codigo = codigo.strip()
    if not codigo:
        return texto
    if texto.startswith(codigo):
        return texto
    return f"{codigo} {texto}"


class _EjeParseado:
    """Eje con su jerarquía anidada, tal como se reconstruye del CSV."""

    def __init__(self, nombre: str) -> None:
        self.nombre = nombre
        # metas: lista de dicts {descripcion, objetivos: [...]}
        self.metas: list[dict] = []


def parsear_csv(path: Path) -> tuple[list[_EjeParseado], list[str]]:
    """Reconstruye la jerarquía del CSV aplicando forward-fill.

    Devuelve ``(ejes, avisos)``. ``avisos`` recoge incoherencias no fatales
    (p. ej. un indicador sin objetivo vigente), para reportarlas sin inventar.
    """
    with path.open(encoding="utf-8") as handle:
        filas = list(csv.reader(handle))

    ejes: list[_EjeParseado] = []
    avisos: list[str] = []

    eje_actual: _EjeParseado | None = None
    meta_actual: dict | None = None
    obj_actual: dict | None = None
    ind_actual: dict | None = None

    for n, fila in enumerate(filas, start=1):
        def celda(i: int) -> str:
            return _limpiar(fila[i]) if len(fila) > i else ""

        a = celda(_COL_EJE)

        # Cabecera repetida antes de cada eje: se ignora.
        if a.upper().startswith("LINEAS ESTRA"):
            continue

        # Nueva fila de Eje: reinicia los "vigentes" de niveles inferiores.
        if a.upper().startswith("EJE"):
            # El nombre del eje se conserva COMPLETO ("EJE 1: ...") tal como en
            # la fuente; es el identificador que SAO reconoce.
            eje_actual = _EjeParseado(a)
            ejes.append(eje_actual)
            meta_actual = obj_actual = ind_actual = None

        if eje_actual is None:
            # Fila de datos antes del primer eje (no debería pasar): se omite.
            continue

        meta_txt = celda(_COL_META)
        obj_cod = celda(_COL_OBJ_COD)
        obj_txt = celda(_COL_OBJ_TXT)
        ind_txt = celda(_COL_IND)
        act_cod = celda(_COL_ACT_COD)
        act_txt = celda(_COL_ACT_TXT)

        # --- Meta (forward-fill: una nueva meta arrastra hacia abajo) --------
        # IMPORTANTE: una meta nueva NO reinicia el objetivo/indicador vigentes.
        # En el Excel, las metas "extra" de un eje aparecen en celdas sueltas
        # físicamente intercaladas entre las actividades de un objetivo (p. ej.
        # la meta "300.000 ha" cae entre las actividades 4.3.2 y 4.3.3 del
        # objetivo 4.3). Resetear aquí cortaría ese objetivo y perdería sus
        # actividades. La meta solo se registra; el SIGUIENTE objetivo con texto
        # se le asignará por forward-fill normal.
        if meta_txt:
            meta_actual = {"descripcion": meta_txt, "objetivos": []}
            eje_actual.metas.append(meta_actual)

        # --- Objetivo --------------------------------------------------------
        # Al entrar un objetivo nuevo se reinicia el indicador vigente: los
        # indicadores pertenecen al objetivo y no deben cruzar su frontera.
        if obj_txt:
            if meta_actual is None:
                avisos.append(
                    f"Fila {n}: objetivo sin meta vigente en {eje_actual.nombre!r}; omitido."
                )
            else:
                obj_actual = {
                    "descripcion": _con_codigo(obj_cod, obj_txt),
                    "indicadores": [],
                }
                meta_actual["objetivos"].append(obj_actual)
                ind_actual = None

        # --- Indicador -------------------------------------------------------
        if ind_txt:
            if obj_actual is None:
                avisos.append(
                    f"Fila {n}: indicador sin objetivo vigente en "
                    f"{eje_actual.nombre!r}; omitido: {ind_txt[:50]!r}"
                )
            else:
                ind_actual = {"texto": ind_txt, "actividades": []}
                obj_actual["indicadores"].append(ind_actual)

        # --- Actividad -------------------------------------------------------
        # En el Excel, la ACTIVIDAD pertenece al OBJETIVO (su código es 4.2.x
        # bajo el objetivo 4.2), mientras que el INDICADOR es una columna
        # paralela: un objetivo tiene varias actividades y varios indicadores sin
        # correspondencia 1-a-1. El modelo del sistema cuelga la actividad de un
        # indicador, así que la asociamos al ÚLTIMO indicador del objetivo
        # vigente (forward-fill dentro del objetivo). Si el objetivo aún no tiene
        # indicador (las actividades vienen antes), se crea un indicador
        # contenedor explícito y señalado como "(sin indicador en el Excel)"
        # para no perder la actividad ni inventar un indicador real.
        if act_txt:
            if obj_actual is None:
                avisos.append(
                    f"Fila {n}: actividad sin objetivo vigente en "
                    f"{eje_actual.nombre!r}; omitida: {act_txt[:50]!r}"
                )
            else:
                if ind_actual is None:
                    ind_actual = {
                        "texto": "(sin indicador asociado en el Excel)",
                        "actividades": [],
                        "placeholder": True,
                    }
                    obj_actual["indicadores"].append(ind_actual)
                ind_actual["actividades"].append(_con_codigo(act_cod, act_txt))

    return ejes, avisos


def _contar(ejes: list[_EjeParseado]) -> dict[str, int]:
    """Conteo total por nivel, para el resumen."""
    metas = sum(len(e.metas) for e in ejes)
    objs = sum(len(m["objetivos"]) for e in ejes for m in e.metas)
    inds = sum(
        len(o["indicadores"]) for e in ejes for m in e.metas for o in m["objetivos"]
    )
    acts = sum(
        len(i["actividades"])
        for e in ejes
        for m in e.metas
        for o in m["objetivos"]
        for i in o["indicadores"]
    )
    return {"ejes": len(ejes), "metas": metas, "objetivos": objs,
            "indicadores": inds, "actividades": acts}


def _borrar_jerarquia(session: Session) -> None:
    """Borra TODA la jerarquía existente (hijos primero por las FK)."""
    session.execute(delete(ActividadModel))
    session.execute(delete(IndicadorModel))
    session.execute(delete(ObjetivoModel))
    session.execute(delete(MetaModel))
    session.execute(delete(EjeModel))


def persistir(session: Session, ejes: list[_EjeParseado]) -> None:
    """Inserta la jerarquía reconstruida en la base vía los modelos ORM.

    El Indicador exige ``nombre`` y ``descripcion``; como el Excel solo trae un
    texto de indicador, se usa ese texto para ambos (no se inventa un nombre).
    """
    for e in ejes:
        eje = EjeModel(nombre=e.nombre, descripcion=None)
        for m in e.metas:
            meta = MetaModel(descripcion=m["descripcion"], eje=eje)
            for o in m["objetivos"]:
                obj = ObjetivoModel(descripcion=o["descripcion"], meta=meta)
                for i in o["indicadores"]:
                    ind = IndicadorModel(
                        nombre=i["texto"], descripcion=i["texto"], objetivo=obj
                    )
                    for act_txt in i["actividades"]:
                        ActividadModel(descripcion=act_txt, indicador=ind)
        session.add(eje)
    session.commit()


def _build_sqlite_memory_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    return factory()


def _build_configured_session() -> Session:
    from backend.src.core.database import SessionLocal

    return SessionLocal()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Importa la jerarquía ENCA REAL de SAO (Eje→Meta→Objetivo→"
            "Indicador→Actividad) desde el CSV del Excel de ejes estratégicos."
        )
    )
    parser.add_argument(
        "--csv", type=Path, default=_CSV_DEFAULT, help="Ruta del CSV fuente."
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Parsea y muestra el resumen SIN tocar la base de datos.",
    )
    parser.add_argument(
        "--reset", action="store_true",
        help="Borra la jerarquía existente (incluye DEMO_DATA) antes de insertar.",
    )
    parser.add_argument(
        "--sqlite-memory", action="store_true",
        help="Usa SQLite en memoria (verificación sin PostgreSQL).",
    )
    args = parser.parse_args(argv)

    if not args.csv.exists():
        print(f"ERROR: no existe el CSV {args.csv}", file=sys.stderr)
        return 1

    ejes, avisos = parsear_csv(args.csv)
    conteo = _contar(ejes)

    print("Jerarquía reconstruida del Excel (forward-fill, regla de Julián):")
    for clave in ("ejes", "metas", "objetivos", "indicadores", "actividades"):
        print(f"  {clave:12}: {conteo[clave]}")
    for e in ejes:
        print(f"  - {e.nombre[:60]} ({len(e.metas)} meta/s)")
    if avisos:
        print(f"\nAvisos ({len(avisos)}) — filas no encajadas (no se inventan):")
        for a in avisos:
            print(f"  · {a}")

    if args.dry_run:
        print("\n--dry-run: no se escribió en la base de datos.")
        return 0

    if args.sqlite_memory:
        session = _build_sqlite_memory_session()
        print("\nModo verificación: SQLite en memoria (no persiste).")
    else:
        session = _build_configured_session()

    try:
        if args.reset:
            _borrar_jerarquia(session)
            print("\nJerarquía previa borrada (--reset).")
        persistir(session, ejes)
    finally:
        session.close()

    print("\nImportación completada: datos REALES de SAO en la base.")
    print("AVISO: no son DEMO_DATA; provienen del Excel oficial de ejes ENCA.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
