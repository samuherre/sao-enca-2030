"""Integración 16.2 — Integridad referencial por clave foránea.

Confirma que la **clave foránea NOT NULL** de cada entidad hija impide
referencias colgantes **a nivel de base de datos**: insertar una fila hija cuyo
``*_id`` apunta a un padre inexistente debe fallar con un error de integridad
referencial (Req 8.1, 8.2; design.md "Reglas de integridad").

La verificación es a nivel de motor (no de la capa de servicios): se escribe
directamente con los modelos ORM y se fuerza el ``flush``. En PostgreSQL la FK
se aplica siempre; en SQLite se aplica porque la configuración de integración
activa ``PRAGMA foreign_keys=ON`` (ver ``conftest.py``).
"""

from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError

from backend.src.models.actividad import ActividadModel
from backend.src.models.indicador import IndicadorModel
from backend.src.models.meta import MetaModel
from backend.src.models.objetivo import ObjetivoModel

# ID de un padre que con certeza no existe en una base recién migrada/vacía.
_PADRE_INEXISTENTE = 999_999


def test_meta_con_eje_inexistente_falla(db_session):
    """Una Meta con ``eje_id`` inexistente viola la FK → ``IntegrityError``."""
    db_session.add(
        MetaModel(descripcion="meta huérfana", eje_id=_PADRE_INEXISTENTE)
    )
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_objetivo_con_meta_inexistente_falla(db_session):
    """Un Objetivo con ``meta_id`` inexistente viola la FK → ``IntegrityError``."""
    db_session.add(
        ObjetivoModel(descripcion="objetivo huérfano", meta_id=_PADRE_INEXISTENTE)
    )
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_indicador_con_objetivo_inexistente_falla(db_session):
    """Un Indicador con ``objetivo_id`` inexistente viola la FK → error."""
    db_session.add(
        IndicadorModel(
            nombre="indicador huérfano",
            descripcion="sin objetivo",
            objetivo_id=_PADRE_INEXISTENTE,
        )
    )
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_actividad_con_indicador_inexistente_falla(db_session):
    """Una Actividad con ``indicador_id`` inexistente viola la FK → error."""
    db_session.add(
        ActividadModel(
            descripcion="actividad huérfana", indicador_id=_PADRE_INEXISTENTE
        )
    )
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_fk_enforcement_esta_activa(uses_postgres, db_session):
    """Documenta que la verificación de FK está activa en el motor de prueba.

    En SQLite esto depende de ``PRAGMA foreign_keys=ON`` (habilitado en
    ``conftest.py``); en PostgreSQL es el comportamiento nativo. Si por alguna
    razón la verificación no estuviese activa, las pruebas anteriores no
    detectarían el fallo, por lo que se comprueba el PRAGMA en SQLite.
    """
    if uses_postgres:
        pytest.skip("PostgreSQL aplica integridad referencial de forma nativa.")
    activo = db_session.execute(
        __import__("sqlalchemy").text("PRAGMA foreign_keys")
    ).scalar()
    assert activo == 1
