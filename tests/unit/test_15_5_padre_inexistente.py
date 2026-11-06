"""Tarea 15.5 — Rechazo de referencia a un padre inexistente.

Crear una entidad hija bajo un id de padre inexistente se rechaza con **404**
(``InvalidParentReferenceError``) y no persiste la hija.

Requisitos: 2.2, 3.2, 4.2, 5.2, 8.2.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.src.models import (
    ActividadModel,
    IndicadorModel,
    MetaModel,
    ObjetivoModel,
)

ID_INEXISTENTE = 999999


def _contar(db_session: Session, modelo) -> int:
    return db_session.execute(select(func.count()).select_from(modelo)).scalar_one()


class TestMetaBajoEjeInexistente:
    """Req 2.2/8.2: crear Meta bajo Eje inexistente => 404 y no persiste."""

    def test_rechazo_404_y_sin_persistir(self, client, db_session: Session):
        resp = client.post(f"/ejes/{ID_INEXISTENTE}/metas", json={"descripcion": "M"})
        assert resp.status_code == 404
        assert _contar(db_session, MetaModel) == 0


class TestObjetivoBajoMetaInexistente:
    """Req 3.2/8.2: crear Objetivo bajo Meta inexistente => 404 y no persiste."""

    def test_rechazo_404_y_sin_persistir(self, client, db_session: Session):
        resp = client.post(f"/metas/{ID_INEXISTENTE}/objetivos", json={"descripcion": "O"})
        assert resp.status_code == 404
        assert _contar(db_session, ObjetivoModel) == 0


class TestIndicadorBajoObjetivoInexistente:
    """Req 4.2/8.2: crear Indicador bajo Objetivo inexistente => 404 y no persiste."""

    def test_rechazo_404_y_sin_persistir(self, client, db_session: Session):
        resp = client.post(
            f"/objetivos/{ID_INEXISTENTE}/indicadores",
            json={"nombre": "I", "descripcion": "D"},
        )
        assert resp.status_code == 404
        assert _contar(db_session, IndicadorModel) == 0


class TestActividadBajoIndicadorInexistente:
    """Req 5.2/8.2: crear Actividad bajo Indicador inexistente => 404 y no persiste."""

    def test_rechazo_404_y_sin_persistir(self, client, db_session: Session):
        resp = client.post(
            f"/indicadores/{ID_INEXISTENTE}/actividades", json={"descripcion": "A"}
        )
        assert resp.status_code == 404
        assert _contar(db_session, ActividadModel) == 0
