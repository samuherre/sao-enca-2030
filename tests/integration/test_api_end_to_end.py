"""Integración 16.3 — Flujo extremo a extremo vía la API (TestClient).

Ejercita los endpoints reales de FastAPI para crear la jerarquía completa de
cinco niveles y recuperar el árbol anidado del Eje (Req 6.1, 2.1, 3.1, 4.1,
5.1). Usa ``api_client``, que comparte la sesión transaccional de la prueba
(ver ``conftest.py``), de modo que todo lo creado se revierte al terminar.

Secuencia:

    POST /ejes                                   → Eje
    POST /ejes/{eje_id}/metas                    → Meta
    POST /metas/{meta_id}/objetivos              → Objetivo
    POST /objetivos/{objetivo_id}/indicadores    → Indicador
    POST /indicadores/{indicador_id}/actividades → Actividad
    GET  /ejes/{eje_id}/arbol                     → árbol anidado (5 niveles)
"""

from __future__ import annotations


def test_crear_jerarquia_y_recuperar_arbol(api_client):
    """Crea Eje→Meta→Objetivo→Indicador→Actividad y recupera el árbol."""
    # Nivel 1 — Eje.
    r = api_client.post(
        "/ejes",
        json={"nombre": "Eje E2E", "descripcion": "Eje de prueba e2e"},
    )
    assert r.status_code == 201, r.text
    eje = r.json()
    eje_id = eje["id"]
    assert eje["nombre"] == "Eje E2E"
    # El Eje raíz no expone referencia a padre (Req 6.3).
    assert not any(k.endswith("_id") for k in eje)

    # Nivel 2 — Meta (padre vía ruta anidada).
    r = api_client.post(f"/ejes/{eje_id}/metas", json={"descripcion": "Meta E2E"})
    assert r.status_code == 201, r.text
    meta = r.json()
    meta_id = meta["id"]
    assert meta["eje_id"] == eje_id

    # Nivel 3 — Objetivo.
    r = api_client.post(
        f"/metas/{meta_id}/objetivos", json={"descripcion": "Objetivo E2E"}
    )
    assert r.status_code == 201, r.text
    objetivo = r.json()
    objetivo_id = objetivo["id"]
    assert objetivo["meta_id"] == meta_id

    # Nivel 4 — Indicador.
    r = api_client.post(
        f"/objetivos/{objetivo_id}/indicadores",
        json={"nombre": "Indicador E2E", "descripcion": "desc indicador"},
    )
    assert r.status_code == 201, r.text
    indicador = r.json()
    indicador_id = indicador["id"]
    assert indicador["objetivo_id"] == objetivo_id

    # Nivel 5 — Actividad.
    r = api_client.post(
        f"/indicadores/{indicador_id}/actividades",
        json={"descripcion": "Actividad E2E"},
    )
    assert r.status_code == 201, r.text
    actividad = r.json()
    actividad_id = actividad["id"]
    assert actividad["indicador_id"] == indicador_id

    # Recuperar el árbol anidado completo del Eje (Req 6.1).
    r = api_client.get(f"/ejes/{eje_id}/arbol")
    assert r.status_code == 200, r.text
    arbol = r.json()

    assert arbol["id"] == eje_id
    assert arbol["nombre"] == "Eje E2E"

    metas = arbol["metas"]
    assert len(metas) == 1
    assert metas[0]["id"] == meta_id

    objetivos = metas[0]["objetivos"]
    assert len(objetivos) == 1
    assert objetivos[0]["id"] == objetivo_id

    indicadores = objetivos[0]["indicadores"]
    assert len(indicadores) == 1
    assert indicadores[0]["id"] == indicador_id
    assert indicadores[0]["nombre"] == "Indicador E2E"

    actividades = indicadores[0]["actividades"]
    assert len(actividades) == 1
    assert actividades[0]["id"] == actividad_id
    assert actividades[0]["descripcion"] == "Actividad E2E"


def test_arbol_de_eje_inexistente_devuelve_404(api_client):
    """``GET /ejes/{id}/arbol`` de un Eje inexistente responde 404 (Req 6.5)."""
    r = api_client.get("/ejes/999999/arbol")
    assert r.status_code == 404, r.text


def test_crear_meta_bajo_eje_inexistente_devuelve_404(api_client):
    """Crear una Meta bajo un Eje inexistente responde 404 (Req 2.2, 8.2)."""
    r = api_client.post("/ejes/999999/metas", json={"descripcion": "x"})
    assert r.status_code == 404, r.text
