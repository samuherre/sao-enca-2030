"""Tarea 15.3 — Consulta individual y por colección (incluida colección vacía).

Verifica obtener entidades por id existente, listar los hijos de un padre, listar
todos los Ejes y confirmar que una colección vacía se devuelve como ``[]`` sin
error.

Requisitos: 1.3, 1.4, 2.4, 2.5, 2.6, 3.4, 3.6, 4.4, 4.5, 5.4, 5.5, 5.6.
"""

from __future__ import annotations

from helpers import (
    crear_actividad,
    crear_eje,
    crear_indicador,
    crear_meta,
    crear_objetivo,
)


class TestListarTodosLosEjes:
    """Req 1.3: listar todos los Ejes, incluido el caso de colección vacía."""

    def test_lista_vacia_sin_ejes(self, client):
        resp = client.get("/ejes")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_lista_todos_los_ejes_registrados(self, client):
        crear_eje(client, nombre="Eje A")
        crear_eje(client, nombre="Eje B")
        resp = client.get("/ejes")
        assert resp.status_code == 200
        nombres = {e["nombre"] for e in resp.json()}
        assert nombres == {"Eje A", "Eje B"}


class TestObtenerPorId:
    """Req 1.4, 2.6, 3.6, 4.5, 5.6: obtener cada entidad por id existente."""

    def test_obtener_eje_por_id(self, client):
        eje = crear_eje(client, nombre="Eje X")
        resp = client.get(f"/ejes/{eje['id']}")
        assert resp.status_code == 200
        assert resp.json()["id"] == eje["id"]

    def test_obtener_meta_por_id_con_referencia_al_eje(self, client):
        eje = crear_eje(client)
        meta = crear_meta(client, eje["id"])
        resp = client.get(f"/metas/{meta['id']}")
        assert resp.status_code == 200
        cuerpo = resp.json()
        assert cuerpo["id"] == meta["id"]
        assert cuerpo["eje_id"] == eje["id"]

    def test_obtener_objetivo_por_id_con_referencia_a_la_meta(self, client):
        eje = crear_eje(client)
        meta = crear_meta(client, eje["id"])
        objetivo = crear_objetivo(client, meta["id"])
        resp = client.get(f"/objetivos/{objetivo['id']}")
        assert resp.status_code == 200
        assert resp.json()["meta_id"] == meta["id"]

    def test_obtener_indicador_por_id_con_referencia_al_objetivo(self, client):
        eje = crear_eje(client)
        meta = crear_meta(client, eje["id"])
        objetivo = crear_objetivo(client, meta["id"])
        indicador = crear_indicador(client, objetivo["id"])
        resp = client.get(f"/indicadores/{indicador['id']}")
        assert resp.status_code == 200
        assert resp.json()["objetivo_id"] == objetivo["id"]

    def test_obtener_actividad_por_id_con_referencia_al_indicador(self, client):
        eje = crear_eje(client)
        meta = crear_meta(client, eje["id"])
        objetivo = crear_objetivo(client, meta["id"])
        indicador = crear_indicador(client, objetivo["id"])
        actividad = crear_actividad(client, indicador["id"])
        resp = client.get(f"/actividades/{actividad['id']}")
        assert resp.status_code == 200
        assert resp.json()["indicador_id"] == indicador["id"]


class TestListarHijosNoVacios:
    """Req 2.4, 3.4, 4.4, 5.4: listar los hijos de un padre con elementos."""

    def test_listar_metas_de_un_eje(self, client):
        eje = crear_eje(client)
        crear_meta(client, eje["id"], descripcion="M1")
        crear_meta(client, eje["id"], descripcion="M2")
        resp = client.get(f"/ejes/{eje['id']}/metas")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_listar_objetivos_de_una_meta(self, client):
        eje = crear_eje(client)
        meta = crear_meta(client, eje["id"])
        crear_objetivo(client, meta["id"])
        resp = client.get(f"/metas/{meta['id']}/objetivos")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_listar_indicadores_de_un_objetivo(self, client):
        eje = crear_eje(client)
        meta = crear_meta(client, eje["id"])
        objetivo = crear_objetivo(client, meta["id"])
        crear_indicador(client, objetivo["id"])
        resp = client.get(f"/objetivos/{objetivo['id']}/indicadores")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_listar_actividades_de_un_indicador(self, client):
        eje = crear_eje(client)
        meta = crear_meta(client, eje["id"])
        objetivo = crear_objetivo(client, meta["id"])
        indicador = crear_indicador(client, objetivo["id"])
        crear_actividad(client, indicador["id"])
        resp = client.get(f"/indicadores/{indicador['id']}/actividades")
        assert resp.status_code == 200
        assert len(resp.json()) == 1


class TestColeccionHijosVacia:
    """Req 2.5, 3.4, 4.4, 5.5: colección de hijos vacía => ``[]`` sin error."""

    def test_metas_de_eje_sin_metas(self, client):
        eje = crear_eje(client)
        resp = client.get(f"/ejes/{eje['id']}/metas")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_objetivos_de_meta_sin_objetivos(self, client):
        eje = crear_eje(client)
        meta = crear_meta(client, eje["id"])
        resp = client.get(f"/metas/{meta['id']}/objetivos")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_indicadores_de_objetivo_sin_indicadores(self, client):
        eje = crear_eje(client)
        meta = crear_meta(client, eje["id"])
        objetivo = crear_objetivo(client, meta["id"])
        resp = client.get(f"/objetivos/{objetivo['id']}/indicadores")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_actividades_de_indicador_sin_actividades(self, client):
        eje = crear_eje(client)
        meta = crear_meta(client, eje["id"])
        objetivo = crear_objetivo(client, meta["id"])
        indicador = crear_indicador(client, objetivo["id"])
        resp = client.get(f"/indicadores/{indicador['id']}/actividades")
        assert resp.status_code == 200
        assert resp.json() == []
