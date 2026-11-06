"""Seed de desarrollo DEMO_DATA — jerarquía ENCA de ejemplo.

Tarea 13 (tasks.md, spec ``enca-strategy-tracking``). Inserta una jerarquía de
ejemplo **completa** de cinco niveles:

    Eje → Meta → Objetivo SMART → Indicador → Actividad

Cada campo de texto (``nombre`` / ``descripcion``) de cada entidad sembrada
comienza con el prefijo legible ``"[DEMO_DATA] "`` (Req 10.1). Estos datos son
**sintéticos** y están pensados exclusivamente para desarrollo y pruebas; nunca
deben confundirse ni presentarse como información oficial de SAO (Req 10.2,
10.3; tech.md §2.3; data-and-domain.md §37).

Este módulo es **solo para desarrollo**. Reutiliza los modelos ORM
(``backend/src/models/``) y la sesión de base de datos del backend.

Uso (desde la raíz del proyecto)::

    # Contra la base configurada por DATABASE_URL (p. ej. PostgreSQL local):
    python scripts/data/seed_demo_data.py

    # Verificación/exploración sin PostgreSQL, con SQLite en memoria:
    python scripts/data/seed_demo_data.py --sqlite-memory

El seed es *idempotente a nivel de ejecución*: antes de insertar comprueba si ya
existe el Eje DEMO_DATA de referencia y, de ser así, no vuelve a sembrar (evita
duplicar la jerarquía en ejecuciones repetidas durante el desarrollo).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Permite ejecutar el script directamente (``python scripts/data/seed_demo_data.py``)
# añadiendo la raíz del proyecto al ``sys.path`` para resolver los imports
# absolutos ``backend.src...`` (convención del proyecto). No usa rutas
# absolutas de una máquina concreta (structure.md §26): la raíz se deriva de la
# ubicación de este archivo.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from sqlalchemy import create_engine, select  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

from backend.src.models.actividad import ActividadModel  # noqa: E402
from backend.src.models.base import Base  # noqa: E402
from backend.src.models.eje import EjeModel  # noqa: E402
from backend.src.models.indicador import IndicadorModel  # noqa: E402
from backend.src.models.meta import MetaModel  # noqa: E402
from backend.src.models.objetivo import ObjetivoModel  # noqa: E402

# Prefijo legible que marca todo dato como DEMO_DATA (Req 10.1). El espacio
# final separa el marcador del texto de ejemplo.
DEMO_PREFIX = "[DEMO_DATA] "

# Nombre del Eje raíz de la jerarquía DEMO_DATA. Se usa como ancla para detectar
# si el seed ya se ejecutó (idempotencia a nivel de ejecución).
_DEMO_EJE_NOMBRE = f"{DEMO_PREFIX}Eje estratégico de ejemplo"


def _demo_hierarchy_exists(session: Session) -> bool:
    """Indica si la jerarquía DEMO_DATA ya fue sembrada en esta base.

    Comprueba la existencia del Eje raíz DEMO_DATA de referencia. Permite que el
    seed sea seguro de re-ejecutar durante el desarrollo sin duplicar datos.
    """
    stmt = select(EjeModel.id).where(EjeModel.nombre == _DEMO_EJE_NOMBRE)
    return session.execute(stmt).first() is not None


def seed(session: Session) -> EjeModel:
    """Inserta una jerarquía DEMO_DATA completa de 5 niveles y la devuelve.

    Todos los campos de texto de las entidades creadas comienzan con
    ``DEMO_PREFIX`` (``"[DEMO_DATA] "``). Si la jerarquía ya existe (detectada
    por el Eje raíz DEMO_DATA), no inserta nada y devuelve el Eje existente.

    La transacción se confirma (``commit``) al finalizar la inserción.
    """
    existente = session.execute(
        select(EjeModel).where(EjeModel.nombre == _DEMO_EJE_NOMBRE)
    ).scalar_one_or_none()
    if existente is not None:
        print(
            "La jerarquía DEMO_DATA ya existe (Eje id="
            f"{existente.id}); no se vuelve a sembrar."
        )
        return existente

    # Nivel 1 — Eje (nombre obligatorio, descripción opcional).
    eje = EjeModel(
        nombre=_DEMO_EJE_NOMBRE,
        descripcion=f"{DEMO_PREFIX}Descripción de ejemplo del Eje para desarrollo.",
    )

    # Nivel 2 — Meta (descripción obligatoria).
    meta = MetaModel(
        descripcion=f"{DEMO_PREFIX}Meta de ejemplo asociada al Eje de demostración.",
        eje=eje,
    )

    # Nivel 3 — Objetivo SMART (descripción obligatoria).
    objetivo = ObjetivoModel(
        descripcion=(
            f"{DEMO_PREFIX}Objetivo SMART de ejemplo asociado a la Meta de "
            "demostración."
        ),
        meta=meta,
    )

    # Nivel 4 — Indicador (nombre y descripción obligatorios).
    indicador = IndicadorModel(
        nombre=f"{DEMO_PREFIX}Indicador de ejemplo",
        descripcion=(
            f"{DEMO_PREFIX}Descripción de ejemplo del Indicador para "
            "desarrollo."
        ),
        objetivo=objetivo,
    )

    # Nivel 5 — Actividad (nombre/descripción obligatorio).
    actividad = ActividadModel(
        descripcion=(
            f"{DEMO_PREFIX}Actividad de ejemplo asociada al Indicador de "
            "demostración."
        ),
        indicador=indicador,
    )

    # Al añadir el Eje raíz, la cascada de relaciones persiste toda la jerarquía
    # conectada mediante los objetos relacionados.
    session.add(eje)
    session.add(meta)
    session.add(objetivo)
    session.add(indicador)
    session.add(actividad)
    session.commit()
    session.refresh(eje)

    print(
        "Seed DEMO_DATA insertado: 1 Eje, 1 Meta, 1 Objetivo, 1 Indicador y "
        f"1 Actividad (Eje id={eje.id})."
    )
    print(
        "AVISO: estos son datos de demostración (DEMO_DATA), NO información "
        "oficial de SAO."
    )
    return eje


def _build_sqlite_memory_session() -> Session:
    """Crea una sesión sobre una base SQLite en memoria con el esquema creado.

    Útil para verificación/exploración del seed sin PostgreSQL. El esquema se
    crea desde ``Base.metadata`` (equivalente al que generan las migraciones de
    Alembic para estas tablas). No usa ``DATABASE_URL``.
    """
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    return factory()


def _build_configured_session() -> Session:
    """Crea una sesión usando ``SessionLocal`` del backend (DATABASE_URL).

    Importa ``SessionLocal`` de ``backend.src.core.database`` de forma perezosa
    porque ese módulo construye el engine a partir de ``DATABASE_URL`` en tiempo
    de import; así, el modo ``--sqlite-memory`` no requiere la variable.
    """
    from backend.src.core.database import SessionLocal

    return SessionLocal()


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada CLI del seed de desarrollo DEMO_DATA."""
    parser = argparse.ArgumentParser(
        description=(
            "Seed de desarrollo DEMO_DATA: inserta una jerarquía ENCA de "
            "ejemplo (Eje→Meta→Objetivo→Indicador→Actividad) marcada como "
            "DEMO_DATA. Solo para desarrollo/pruebas; no es información "
            "oficial de SAO."
        )
    )
    parser.add_argument(
        "--sqlite-memory",
        action="store_true",
        help=(
            "Ejecuta el seed sobre una base SQLite en memoria (verificación "
            "local sin PostgreSQL). No persiste datos."
        ),
    )
    args = parser.parse_args(argv)

    if args.sqlite_memory:
        session = _build_sqlite_memory_session()
        print("Modo verificación: SQLite en memoria (los datos no se conservan).")
    else:
        session = _build_configured_session()

    try:
        seed(session)
    finally:
        session.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
