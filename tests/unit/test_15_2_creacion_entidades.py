"""Tarea 15.2 — Creación de cada entidad con datos válidos y asociación hija→padre.

Verifica la creación correcta de Eje, Meta, Objetivo, Indicador y Actividad con
datos válidos, y que cada entidad hija queda asociada al padre correcto mediante
la referencia ``*_id`` del contrato de salida.

Requisitos: 1.1, 2.1, 3.1, 4.1, 5.1, 8.1.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from backend.src.models import (
    ActividadModel,
    EjeModel,
    IndicadorModel,
    MetaModel,
    ObjetivoModel,
)

from helpers import (
    crear_actividad,
    crear_eje,
    crear_indicador,
    crear_meta,
    crear_objetivo,
)


class TestCreacionEje:
    """Req 1.1: crear un Eje con nombre válido y descripción opcional."""

    def test_crear_eje_con_nombre_valido_devuelve_201_e_id(self, client, db_session: Session):
        resp = client.post("/ejes", json={"nombre": "Eje 2", "descripcion": "Sectores"})
        assert resp.status_code == 201
        cuerpo = resp.json()
        assert isinstance(cuerpo["id"], int)
        assert cuerpo["nombre"] == "Eje 2"
        assert cuerpo["descripcion"] == "Sectores"
        # Persistido en la base.
        assert db_session.get(EjeModel, cuerpo["id"]) is not None

    def test_crear_eje_sin_descripcion_es_valido(self, client):
        resp = client.post("/ejes", json={"nombre": "Eje sin descripción"})
        assert resp.status_code == 201
        assert resp.json()["descripcion"] is None

    def test_nombre_se_normaliza_recortando_espacios(self, client):
        resp = client.post("/ejes", json={"nombre": "  Eje con espacios  "})
        assert resp.status_code == 201
        assert resp.json()["nombre"] == "Eje con espacios"


class TestCreacionMeta:
    """Req 2.1/8.1: crear Meta bajo un Eje existente y asociarla a él."""

    def test_crear_meta_asociada_al_eje(self, client, db_session: Session):
        eje = crear_eje(client)
        resp = client.post(f"/ejes/{eje['id']}/metas", json={"descripcion": "Meta A"})
        assert resp.status_code == 201
        cuerpo = resp.json()
        assert isinstance(cuerpo["id"], int)
        assert cuerpo["descripcion"] == "Meta A"
        # Asociación hija→padre correcta.
        assert cuerpo["eje_id"] == eje["id"]
        modelo = db_session.get(MetaModel, cuerpo["id"])
        assert modelo is not None
        assert modelo.eje_id == eje["id"]


class TestCreacionObjetivo:
    """Req 3.1/8.1: crear Objetivo bajo una Meta existente y asociarlo a ella."""

    def test_crear_objetivo_asociado_a_la_meta(self, client, db_session: Session):
        eje = crear_eje(client)
        meta = crear_meta(client, eje["id"])
        resp = client.post(f"/metas/{meta['id']}/objetivos", json={"descripcion": "Obj A"})
        assert resp.status_code == 201
        cuerpo = resp.json()
        assert cuerpo["meta_id"] == meta["id"]
        modelo = db_session.get(ObjetivoModel, cuerpo["id"])
        assert modelo is not None
        assert modelo.meta_id == meta["id"]


class TestCreacionIndicador:
    """Req 4.1/8.1: crear Indicador bajo un Objetivo existente y asociarlo a él."""

    def test_crear_indicador_asociado_al_objetivo(self, client, db_session: Session):
        eje = crear_eje(client)
        meta = crear_meta(client, eje["id"])
        objetivo = crear_objetivo(client, meta["id"])
        resp = client.post(
            f"/objetivos/{objetivo['id']}/indicadores",
            json={"nombre": "Ind A", "descripcion": "Desc A"},
        )
        assert resp.status_code == 201
        cuerpo = resp.json()
        assert cuerpo["nombre"] == "Ind A"
        assert cuerpo["descripcion"] == "Desc A"
        assert cuerpo["objetivo_id"] == objetivo["id"]
        modelo = db_session.get(IndicadorModel, cuerpo["id"])
        assert modelo is not None
        assert modelo.objetivo_id == objetivo["id"]


class TestCreacionActividad:
    """Req 5.1/8.1: crear Actividad bajo un Indicador existente y asociarla a él."""

    def test_crear_actividad_asociada_al_indicador(self, client, db_session: Session):
        eje = crear_eje(client)
        meta = crear_meta(client, eje["id"])
        objetivo = crear_objetivo(client, meta["id"])
        indicador = crear_indicador(client, objetivo["id"])
        resp = client.post(
            f"/indicadores/{indicador['id']}/actividades",
            json={"descripcion": "Act A"},
        )
        assert resp.status_code == 201
        cuerpo = resp.json()
        assert cuerpo["descripcion"] == "Act A"
        assert cuerpo["indicador_id"] == indicador["id"]
        modelo = db_session.get(ActividadModel, cuerpo["id"])
        assert modelo is not None
        assert modelo.indicador_id == indicador["id"]


class TestIdentificadoresUnicos:
    """Req 8.4: cada entidad creada recibe un identificador único en su tipo."""

    def test_dos_ejes_tienen_ids_distintos(self, client):
        primero = crear_eje(client, nombre="Eje uno")
        segundo = crear_eje(client, nombre="Eje dos")
        assert primero["id"] != segundo["id"]

    def test_dos_actividades_del_mismo_indicador_tienen_ids_distintos(self, client):
        eje = crear_eje(client)
        meta = crear_meta(client, eje["id"])
        objetivo = crear_objetivo(client, meta["id"])
        indicador = crear_indicador(client, objetivo["id"])
        a1 = crear_actividad(client, indicador["id"], descripcion="A1")
        a2 = crear_actividad(client, indicador["id"], descripcion="A2")
        assert a1["id"] != a2["id"]
