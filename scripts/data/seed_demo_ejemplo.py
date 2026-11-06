"""Seed de EJEMPLO ampliado (DEMO_DATA) — jerarquía ENCA rica para demostración.

Objetivo: poblar la base con una jerarquía más completa que el seed mínimo, para
mostrar el caso de uso de la aplicación (varios Ejes, Metas, Objetivos,
Indicadores y Actividades, con ramas de distinta profundidad y algún nodo sin
hijos para ver el estado "vacío").

IMPORTANTE (principio de no invención — product.md §15, §22; tech.md §2.3):
- TODOS los textos van prefijados con "[DEMO_DATA] " para que NUNCA se confundan
  con información oficial de SAO; la interfaz muestra además el badge DEMO_DATA.
- La ESTRUCTURA se inspira en los Ejes 2 y 5 de la ENCA (prioritarios para SAO,
  ver data-and-domain.md §30, §31), pero los enunciados concretos son de ejemplo
  y no representan metas, indicadores ni cifras oficiales.

Uso (desde la raíz del proyecto, con el .env apuntando a PostgreSQL):

    python scripts/data/seed_demo_ejemplo.py

Es idempotente a nivel de ejecución: si ya existe el Eje de ejemplo "[DEMO_DATA]
Eje 2 ...", no vuelve a insertar (evita duplicados al re-ejecutar).
"""

from __future__ import annotations

import sys
from pathlib import Path

# Permite ejecutar el script directamente añadiendo la raíz del proyecto al
# sys.path (misma convención que seed_demo_data.py). No usa rutas absolutas.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from backend.src.models.actividad import ActividadModel  # noqa: E402
from backend.src.models.eje import EjeModel  # noqa: E402
from backend.src.models.indicador import IndicadorModel  # noqa: E402
from backend.src.models.meta import MetaModel  # noqa: E402
from backend.src.models.objetivo import ObjetivoModel  # noqa: E402

# Prefijo DEMO_DATA (coherente con scripts/data/seed_demo_data.py).
DEMO = "[DEMO_DATA] "

# Estructura de ejemplo. Cada Eje -> Metas -> Objetivos -> Indicadores ->
# Actividades. Se incluye deliberadamente alguna rama sin hijos para que la
# interfaz muestre el estado "vacío" (p. ej. una Meta sin Objetivos).
EJEMPLO = [
    {
        "nombre": f"{DEMO}Eje 2 — Incidencia en sectores productivos",
        "descripcion": (
            f"{DEMO}Promover buenas prácticas de conservación de aves en "
            "sectores productivos y de servicios (estructura de ejemplo)."
        ),
        "metas": [
            {
                "descripcion": (
                    f"{DEMO}Meta 2.1 — Vincular organizaciones de sectores "
                    "productivos a iniciativas de conservación."
                ),
                "objetivos": [
                    {
                        "descripcion": (
                            f"{DEMO}Objetivo 2.1.1 — Identificar y caracterizar "
                            "organizaciones aliadas potenciales."
                        ),
                        "indicadores": [
                            {
                                "nombre": f"{DEMO}Organizaciones vinculadas",
                                "descripcion": (
                                    f"{DEMO}Número de organizaciones que adoptan "
                                    "buenas prácticas (indicador de ejemplo)."
                                ),
                                "actividades": [
                                    f"{DEMO}Elaborar un directorio de organizaciones aliadas.",
                                    f"{DEMO}Realizar talleres de buenas prácticas.",
                                ],
                            },
                            {
                                "nombre": f"{DEMO}Acuerdos firmados",
                                "descripcion": (
                                    f"{DEMO}Acuerdos de colaboración suscritos "
                                    "(indicador de ejemplo)."
                                ),
                                # Indicador sin actividades: muestra estado vacío.
                                "actividades": [],
                            },
                        ],
                    },
                ],
            },
            {
                "descripcion": (
                    f"{DEMO}Meta 2.2 — Difundir guías de buenas prácticas "
                    "(sin objetivos aún, para ver el estado vacío)."
                ),
                # Meta sin objetivos: muestra el estado "vacío" en Objetivos.
                "objetivos": [],
            },
        ],
    },
    {
        "nombre": f"{DEMO}Eje 5 — Generación y gestión del conocimiento",
        "descripcion": (
            f"{DEMO}Fortalecer la investigación y la gestión del conocimiento "
            "sobre las aves y sus hábitats (estructura de ejemplo)."
        ),
        "metas": [
            {
                "descripcion": (
                    f"{DEMO}Meta 5.1 — Consolidar información científica "
                    "relevante para la conservación."
                ),
                "objetivos": [
                    {
                        "descripcion": (
                            f"{DEMO}Objetivo 5.1.1 — Organizar la información "
                            "científica disponible de forma consultable."
                        ),
                        "indicadores": [
                            {
                                "nombre": f"{DEMO}Documentos organizados",
                                "descripcion": (
                                    f"{DEMO}Volumen de documentos sistematizados "
                                    "(indicador de ejemplo)."
                                ),
                                "actividades": [
                                    f"{DEMO}Definir una estructura de catalogación.",
                                    f"{DEMO}Cargar los documentos priorizados.",
                                    f"{DEMO}Revisar la calidad de los metadatos.",
                                ],
                            },
                        ],
                    },
                    {
                        "descripcion": (
                            f"{DEMO}Objetivo 5.1.2 — Identificar vacíos de "
                            "conocimiento prioritarios."
                        ),
                        # Objetivo sin indicadores: estado vacío en Indicadores.
                        "indicadores": [],
                    },
                ],
            },
        ],
    },
]


def _ya_sembrado(session: Session) -> bool:
    """Indica si el ejemplo ampliado ya existe (ancla en el primer Eje)."""
    nombre_ancla = EJEMPLO[0]["nombre"]
    return (
        session.execute(
            select(EjeModel.id).where(EjeModel.nombre == nombre_ancla)
        ).first()
        is not None
    )


def sembrar(session: Session) -> int:
    """Inserta la jerarquía de ejemplo. Devuelve el número de Ejes creados."""
    if _ya_sembrado(session):
        print(
            "El ejemplo ampliado DEMO_DATA ya existe; no se vuelve a insertar "
            "(idempotente)."
        )
        return 0

    ejes_creados = 0
    for eje_def in EJEMPLO:
        eje = EjeModel(
            nombre=eje_def["nombre"], descripcion=eje_def["descripcion"]
        )
        session.add(eje)
        ejes_creados += 1

        for meta_def in eje_def["metas"]:
            meta = MetaModel(descripcion=meta_def["descripcion"], eje=eje)
            session.add(meta)

            for obj_def in meta_def["objetivos"]:
                objetivo = ObjetivoModel(
                    descripcion=obj_def["descripcion"], meta=meta
                )
                session.add(objetivo)

                for ind_def in obj_def["indicadores"]:
                    indicador = IndicadorModel(
                        nombre=ind_def["nombre"],
                        descripcion=ind_def["descripcion"],
                        objetivo=objetivo,
                    )
                    session.add(indicador)

                    for descripcion_actividad in ind_def["actividades"]:
                        session.add(
                            ActividadModel(
                                descripcion=descripcion_actividad,
                                indicador=indicador,
                            )
                        )

    session.commit()
    print(
        f"Ejemplo DEMO_DATA insertado: {ejes_creados} Ejes con su jerarquía "
        "(Metas, Objetivos, Indicadores y Actividades)."
    )
    print(
        "AVISO: son datos de DEMOSTRACIÓN (DEMO_DATA), NO información oficial "
        "de SAO."
    )
    return ejes_creados


def main() -> int:
    """Punto de entrada: usa la sesión configurada por DATABASE_URL (.env)."""
    from backend.src.core.database import SessionLocal

    session = SessionLocal()
    try:
        sembrar(session)
    finally:
        session.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
