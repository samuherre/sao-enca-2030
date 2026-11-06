"""Tarea 15.4 — Validación de campos obligatorios (nulo/vacío/solo espacios).

Para cada campo obligatorio confirmado (nombre/descripción según entidad), un
valor nulo, vacío o compuesto solo por espacios se rechaza con **422** y no se
persiste ninguna entidad.

Requisitos: 1.2, 2.3, 3.3, 4.3, 5.3.
"""

from __future__ import annotations

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.src.models import (
    ActividadModel,
    EjeModel,
    IndicadorModel,
    MetaModel,
    ObjetivoModel,
)

from helpers import crear_eje, crear_indicador, crear_meta, crear_objetivo

# Valores que deben considerarse campo obligatorio inválido.
VALORES_INVALIDOS = [
    pytest.param(None, id="nulo"),
    pytest.param("", id="vacio"),
    pytest.param("   ", id="solo-espacios"),
    pytest.param("\t\n", id="tabs-y-saltos"),
]


def _contar(db_session: Session, modelo) -> int:
    return db_session.execute(select(func.count()).select_from(modelo)).scalar_one()


class TestValidacionEje:
    """Req 1.2: nombre del Eje nulo/vacío/espacios => 422 y nada persistido."""

    @pytest.mark.parametrize("valor", VALORES_INVALIDOS)
    def test_nombre_invalido_rechazado(self, client, db_session: Session, valor):
        payload = {} if valor is None else {"nombre": valor}
        resp = client.post("/ejes", json=payload)
        assert resp.status_code == 422
        assert _contar(db_session, EjeModel) == 0


class TestValidacionMeta:
    """Req 2.3: descripción de la Meta nula/vacía/espacios => 422, nada persiste."""

    @pytest.mark.parametrize("valor", VALORES_INVALIDOS)
    def test_descripcion_invalida_rechazada(self, client, db_session: Session, valor):
        eje = crear_eje(client)
        payload = {} if valor is None else {"descripcion": valor}
        resp = client.post(f"/ejes/{eje['id']}/metas", json=payload)
        assert resp.status_code == 422
        assert _contar(db_session, MetaModel) == 0


class TestValidacionObjetivo:
    """Req 3.3: descripción del Objetivo nula/vacía/espacios => 422, nada persiste."""

    @pytest.mark.parametrize("valor", VALORES_INVALIDOS)
    def test_descripcion_invalida_rechazada(self, client, db_session: Session, valor):
        eje = crear_eje(client)
        meta = crear_meta(client, eje["id"])
        payload = {} if valor is None else {"descripcion": valor}
        resp = client.post(f"/metas/{meta['id']}/objetivos", json=payload)
        assert resp.status_code == 422
        assert _contar(db_session, ObjetivoModel) == 0


class TestValidacionIndicador:
    """Req 4.3: nombre del Indicador nulo/vacío/espacios => 422, nada persiste."""

    @pytest.mark.parametrize("valor", VALORES_INVALIDOS)
    def test_nombre_invalido_rechazado(self, client, db_session: Session, valor):
        eje = crear_eje(client)
        meta = crear_meta(client, eje["id"])
        objetivo = crear_objetivo(client, meta["id"])
        payload = {"descripcion": "Desc válida"}
        if valor is not None:
            payload["nombre"] = valor
        resp = client.post(f"/objetivos/{objetivo['id']}/indicadores", json=payload)
        assert resp.status_code == 422
        assert _contar(db_session, IndicadorModel) == 0

    @pytest.mark.parametrize("valor", VALORES_INVALIDOS)
    def test_descripcion_invalida_rechazada(self, client, db_session: Session, valor):
        eje = crear_eje(client)
        meta = crear_meta(client, eje["id"])
        objetivo = crear_objetivo(client, meta["id"])
        payload = {"nombre": "Nombre válido"}
        if valor is not None:
            payload["descripcion"] = valor
        resp = client.post(f"/objetivos/{objetivo['id']}/indicadores", json=payload)
        assert resp.status_code == 422
        assert _contar(db_session, IndicadorModel) == 0


class TestValidacionActividad:
    """Req 5.3: descripción de la Actividad nula/vacía/espacios => 422, nada persiste."""

    @pytest.mark.parametrize("valor", VALORES_INVALIDOS)
    def test_descripcion_invalida_rechazada(self, client, db_session: Session, valor):
        eje = crear_eje(client)
        meta = crear_meta(client, eje["id"])
        objetivo = crear_objetivo(client, meta["id"])
        indicador = crear_indicador(client, objetivo["id"])
        payload = {} if valor is None else {"descripcion": valor}
        resp = client.post(f"/indicadores/{indicador['id']}/actividades", json=payload)
        assert resp.status_code == 422
        assert _contar(db_session, ActividadModel) == 0
