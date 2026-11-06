"""Tarea 15.6 — Navegación jerárquica (árbol).

El árbol de ``GET /ejes/{eje_id}/arbol`` refleja la estructura creada; los nodos
sin hijos exponen ``[]``; el Eje raíz no incluye referencia a padre y la
operación no produce error.

Requisitos: 6.1, 6.2, 6.3, 6.4.
"""

from __future__ import annotations

from helpers import (
    crear_actividad,
    crear_eje,
    crear_indicador,
    crear_meta,
    crear_objetivo,
    crear_jerarquia_completa,
)


class TestArbolCompleto:
    """Req 6.1: el árbol abarca los cinco niveles anidados en la estructura."""

    def test_arbol_refleja_la_estructura_creada(self, client):
        ids = crear_jerarquia_completa(client)
        resp = client.get(f"/ejes/{ids['eje_id']}/arbol")
        assert resp.status_code == 200
        arbol = resp.json()

        assert arbol["id"] == ids["eje_id"]
        assert len(arbol["metas"]) == 1
        meta = arbol["metas"][0]
        assert meta["id"] == ids["meta_id"]

        assert len(meta["objetivos"]) == 1
        objetivo = meta["objetivos"][0]
        assert objetivo["id"] == ids["objetivo_id"]

        assert len(objetivo["indicadores"]) == 1
        indicador = objetivo["indicadores"][0]
        assert indicador["id"] == ids["indicador_id"]

        assert len(indicador["actividades"]) == 1
        actividad = indicador["actividades"][0]
        assert actividad["id"] == ids["actividad_id"]

    def test_arbol_refleja_multiples_ramas(self, client):
        eje = crear_eje(client)
        meta1 = crear_meta(client, eje["id"], descripcion="M1")
        meta2 = crear_meta(client, eje["id"], descripcion="M2")
        crear_objetivo(client, meta1["id"], descripcion="O1")

        resp = client.get(f"/ejes/{eje['id']}/arbol")
        assert resp.status_code == 200
        arbol = resp.json()
        metas_por_id = {m["id"]: m for m in arbol["metas"]}
        assert set(metas_por_id) == {meta1["id"], meta2["id"]}
        # M1 tiene un objetivo; M2 ninguno.
        assert len(metas_por_id[meta1["id"]]["objetivos"]) == 1
        assert metas_por_id[meta2["id"]]["objetivos"] == []


class TestNodosSinHijos:
    """Req 6.4: cada nodo sin hijos expone una colección de hijos vacía ``[]``."""

    def test_eje_sin_metas_tiene_lista_vacia(self, client):
        eje = crear_eje(client)
        resp = client.get(f"/ejes/{eje['id']}/arbol")
        assert resp.status_code == 200
        assert resp.json()["metas"] == []

    def test_cada_nivel_sin_hijos_expone_lista_vacia(self, client):
        eje = crear_eje(client)
        meta = crear_meta(client, eje["id"])
        objetivo = crear_objetivo(client, meta["id"])
        indicador = crear_indicador(client, objetivo["id"])
        # Sin actividades para el indicador.
        resp = client.get(f"/ejes/{eje['id']}/arbol")
        arbol = resp.json()
        ind = arbol["metas"][0]["objetivos"][0]["indicadores"][0]
        assert ind["id"] == indicador["id"]
        assert ind["actividades"] == []


class TestEjeRaizSinPadre:
    """Req 6.2/6.3: el Eje raíz no incluye referencia a padre y no da error."""

    def test_eje_raiz_no_expone_referencia_a_padre(self, client):
        ids = crear_jerarquia_completa(client)
        resp = client.get(f"/ejes/{ids['eje_id']}/arbol")
        assert resp.status_code == 200
        arbol = resp.json()
        # El nodo raíz no contiene ninguna referencia *_id a un padre.
        assert not any(clave.endswith("_id") for clave in arbol)

    def test_nodos_anidados_omiten_referencia_al_padre(self, client):
        """Req 6.2: en el árbol la referencia al padre es implícita (anidamiento)."""
        ids = crear_jerarquia_completa(client)
        arbol = client.get(f"/ejes/{ids['eje_id']}/arbol").json()
        meta = arbol["metas"][0]
        assert "eje_id" not in meta
        objetivo = meta["objetivos"][0]
        assert "meta_id" not in objetivo
        indicador = objetivo["indicadores"][0]
        assert "objetivo_id" not in indicador
        actividad = indicador["actividades"][0]
        assert "indicador_id" not in actividad
