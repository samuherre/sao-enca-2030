"""Ayudas compartidas por las pruebas unitarias de la jerarquía ENCA.

Funciones pequeñas para construir entidades a través de la API (``TestClient``)
y así reutilizarlas en varias pruebas (tareas 15.2–15.8). No contienen lógica de
negocio: solo encapsulan llamadas HTTP de creación y devuelven el ``id`` creado.
"""

from __future__ import annotations

from fastapi.testclient import TestClient


def crear_eje(client: TestClient, nombre: str = "Eje de prueba", descripcion=None) -> dict:
    """Crea un Eje y devuelve el cuerpo de la respuesta (201)."""
    payload: dict = {"nombre": nombre}
    if descripcion is not None:
        payload["descripcion"] = descripcion
    resp = client.post("/ejes", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


def crear_meta(client: TestClient, eje_id: int, descripcion: str = "Meta de prueba") -> dict:
    """Crea una Meta bajo ``eje_id`` y devuelve el cuerpo (201)."""
    resp = client.post(f"/ejes/{eje_id}/metas", json={"descripcion": descripcion})
    assert resp.status_code == 201, resp.text
    return resp.json()


def crear_objetivo(
    client: TestClient, meta_id: int, descripcion: str = "Objetivo de prueba"
) -> dict:
    """Crea un Objetivo bajo ``meta_id`` y devuelve el cuerpo (201)."""
    resp = client.post(f"/metas/{meta_id}/objetivos", json={"descripcion": descripcion})
    assert resp.status_code == 201, resp.text
    return resp.json()


def crear_indicador(
    client: TestClient,
    objetivo_id: int,
    nombre: str = "Indicador de prueba",
    descripcion: str = "Descripción del indicador",
) -> dict:
    """Crea un Indicador bajo ``objetivo_id`` y devuelve el cuerpo (201)."""
    resp = client.post(
        f"/objetivos/{objetivo_id}/indicadores",
        json={"nombre": nombre, "descripcion": descripcion},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def crear_actividad(
    client: TestClient, indicador_id: int, descripcion: str = "Actividad de prueba"
) -> dict:
    """Crea una Actividad bajo ``indicador_id`` y devuelve el cuerpo (201)."""
    resp = client.post(
        f"/indicadores/{indicador_id}/actividades", json={"descripcion": descripcion}
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def crear_jerarquia_completa(client: TestClient) -> dict[str, int]:
    """Crea una cadena Eje→Meta→Objetivo→Indicador→Actividad.

    Devuelve un diccionario con los ids de cada nivel para su uso en pruebas de
    navegación y consulta.
    """
    eje = crear_eje(client, nombre="Eje raíz")
    meta = crear_meta(client, eje["id"], descripcion="Meta 1")
    objetivo = crear_objetivo(client, meta["id"], descripcion="Objetivo 1")
    indicador = crear_indicador(client, objetivo["id"], nombre="Indicador 1")
    actividad = crear_actividad(client, indicador["id"], descripcion="Actividad 1")
    return {
        "eje_id": eje["id"],
        "meta_id": meta["id"],
        "objetivo_id": objetivo["id"],
        "indicador_id": indicador["id"],
        "actividad_id": actividad["id"],
    }
