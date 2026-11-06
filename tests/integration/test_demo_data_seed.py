"""Integración 16.4 — Seed de desarrollo DEMO_DATA.

Reutiliza ``scripts/data/seed_demo_data.py`` (función ``seed(session)``) sobre la
sesión transaccional de integración y verifica que **todas** las entidades
sembradas conservan el marcador legible ``"[DEMO_DATA] "`` al inicio de sus
campos de texto (Req 10.1, 10.2, 10.3; tech.md §2.3). Al terminar la prueba, la
sesión transaccional revierte el seed (aislamiento).
"""

from __future__ import annotations

from sqlalchemy import select

from backend.src.models.actividad import ActividadModel
from backend.src.models.eje import EjeModel
from backend.src.models.indicador import IndicadorModel
from backend.src.models.meta import MetaModel
from backend.src.models.objetivo import ObjetivoModel
from scripts.data.seed_demo_data import DEMO_PREFIX, seed


def test_seed_inserta_jerarquia_con_marcador_demo_data(db_session):
    """Tras el seed, los campos de texto comienzan con ``[DEMO_DATA] ``."""
    eje = seed(db_session)

    # El seed devuelve el Eje raíz sembrado, con su id generado.
    assert eje.id is not None
    assert eje.nombre.startswith(DEMO_PREFIX)
    assert eje.descripcion.startswith(DEMO_PREFIX)

    # Verifica la jerarquía completa recuperándola desde la base.
    metas = db_session.execute(
        select(MetaModel).where(MetaModel.eje_id == eje.id)
    ).scalars().all()
    assert len(metas) >= 1
    for meta in metas:
        assert meta.descripcion.startswith(DEMO_PREFIX)

    objetivos = db_session.execute(
        select(ObjetivoModel).where(
            ObjetivoModel.meta_id.in_([m.id for m in metas])
        )
    ).scalars().all()
    assert len(objetivos) >= 1
    for objetivo in objetivos:
        assert objetivo.descripcion.startswith(DEMO_PREFIX)

    indicadores = db_session.execute(
        select(IndicadorModel).where(
            IndicadorModel.objetivo_id.in_([o.id for o in objetivos])
        )
    ).scalars().all()
    assert len(indicadores) >= 1
    for indicador in indicadores:
        assert indicador.nombre.startswith(DEMO_PREFIX)
        assert indicador.descripcion.startswith(DEMO_PREFIX)

    actividades = db_session.execute(
        select(ActividadModel).where(
            ActividadModel.indicador_id.in_([i.id for i in indicadores])
        )
    ).scalars().all()
    assert len(actividades) >= 1
    for actividad in actividades:
        assert actividad.descripcion.startswith(DEMO_PREFIX)


def test_seed_es_idempotente_a_nivel_de_ejecucion(db_session):
    """Re-ejecutar el seed no duplica la jerarquía DEMO_DATA (idempotencia)."""
    primero = seed(db_session)
    segundo = seed(db_session)
    assert primero.id == segundo.id

    ejes_demo = db_session.execute(
        select(EjeModel).where(EjeModel.nombre.startswith(DEMO_PREFIX))
    ).scalars().all()
    assert len(ejes_demo) == 1
