"""Tarea 15.7 — Omisión de atributos PENDING_VALIDATION en los contratos.

Los ``Response`` de Indicador y Actividad **no** contienen atributos
PENDING_VALIDATION, y un cuerpo de creación que los incluya se rechaza con
**422** (campos extra prohibidos por los schemas).

Requisitos: 4.7, 5.8, 9.1, 9.2, 9.4.
"""

from __future__ import annotations

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.src.models import ActividadModel, IndicadorModel

from helpers import crear_eje, crear_indicador, crear_meta, crear_objetivo

# Atributos PENDING_VALIDATION declarados en requirements.md por entidad.
INDICADOR_PENDING = {
    "unidad_de_medida",
    "valor_objetivo",
    "valor_actual",
    "fecha_de_medicion",
    "fuente",
    "evidencia",
    "estado",
}
ACTIVIDAD_PENDING = {
    "responsable",
    "fecha",
    "estado",
    "evidencia",
    "fuente",
    "region",
}


def _contar(db_session: Session, modelo) -> int:
    return db_session.execute(select(func.count()).select_from(modelo)).scalar_one()


class TestResponsesSinPendingValidation:
    """Req 4.7/5.8/9.1/9.2: los Response no exponen atributos PENDING_VALIDATION."""

    def test_indicador_response_solo_campos_confirmados(self, client):
        eje = crear_eje(client)
        meta = crear_meta(client, eje["id"])
        objetivo = crear_objetivo(client, meta["id"])
        indicador = crear_indicador(client, objetivo["id"])
        resp = client.get(f"/indicadores/{indicador['id']}")
        assert resp.status_code == 200
        cuerpo = resp.json()
        assert set(cuerpo) == {"id", "nombre", "descripcion", "objetivo_id"}
        assert INDICADOR_PENDING.isdisjoint(cuerpo)

    def test_actividad_response_solo_campos_confirmados(self, client):
        eje = crear_eje(client)
        meta = crear_meta(client, eje["id"])
        objetivo = crear_objetivo(client, meta["id"])
        indicador = crear_indicador(client, objetivo["id"])
        resp = client.post(
            f"/indicadores/{indicador['id']}/actividades", json={"descripcion": "A"}
        )
        assert resp.status_code == 201
        cuerpo = resp.json()
        assert set(cuerpo) == {"id", "descripcion", "indicador_id"}
        assert ACTIVIDAD_PENDING.isdisjoint(cuerpo)

    def test_indicador_en_arbol_no_expone_pending_validation(self, client):
        eje = crear_eje(client)
        meta = crear_meta(client, eje["id"])
        objetivo = crear_objetivo(client, meta["id"])
        crear_indicador(client, objetivo["id"])
        arbol = client.get(f"/ejes/{eje['id']}/arbol").json()
        indicador = arbol["metas"][0]["objetivos"][0]["indicadores"][0]
        assert INDICADOR_PENDING.isdisjoint(indicador)


class TestCuerpoConPendingValidationRechazado:
    """Req 9.4: enviar atributos PENDING_VALIDATION => 422 (extra prohibido)."""

    @pytest.mark.parametrize("atributo", sorted(INDICADOR_PENDING))
    def test_indicador_con_atributo_extra_rechazado(
        self, client, db_session: Session, atributo
    ):
        eje = crear_eje(client)
        meta = crear_meta(client, eje["id"])
        objetivo = crear_objetivo(client, meta["id"])
        payload = {"nombre": "Ind", "descripcion": "Desc", atributo: "valor-no-soportado"}
        resp = client.post(f"/objetivos/{objetivo['id']}/indicadores", json=payload)
        assert resp.status_code == 422
        assert _contar(db_session, IndicadorModel) == 0

    @pytest.mark.parametrize("atributo", sorted(ACTIVIDAD_PENDING))
    def test_actividad_con_atributo_extra_rechazado(
        self, client, db_session: Session, atributo
    ):
        eje = crear_eje(client)
        meta = crear_meta(client, eje["id"])
        objetivo = crear_objetivo(client, meta["id"])
        indicador = crear_indicador(client, objetivo["id"])
        payload = {"descripcion": "Act", atributo: "valor-no-soportado"}
        resp = client.post(f"/indicadores/{indicador['id']}/actividades", json=payload)
        assert resp.status_code == 422
        assert _contar(db_session, ActividadModel) == 0
