"""Pruebas de CORS para el consumo del frontend (tarea 22 — integración FE↔BE).

El frontend React (Vite) se sirve en http://localhost:5173 y consume la API del
backend desde el navegador (Req 7.1). Para que el navegador no bloquee esas
peticiones, el backend debe emitir las cabeceras CORS adecuadas para el origen
del frontend local.

Estas pruebas verifican que:
- Una petición "simple" (GET) desde el origen local recibe la cabecera
  ``access-control-allow-origin`` con ese origen.
- La verificación previa (preflight ``OPTIONS``) de una creación (POST con
  ``Content-Type: application/json``) es aceptada y refleja el origen y el
  método permitidos.
- Un origen no permitido no recibe la cabecera de permiso de origen.

No se usan mocks: se ejercita la app real a través del ``TestClient``.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

LOCAL_FRONTEND_ORIGIN = "http://localhost:5173"


def test_get_desde_origen_frontend_incluye_cabecera_cors(client: TestClient) -> None:
    """Un GET desde el origen local del frontend recibe allow-origin de CORS."""
    response = client.get("/ejes", headers={"Origin": LOCAL_FRONTEND_ORIGIN})

    assert response.status_code == 200
    assert (
        response.headers.get("access-control-allow-origin") == LOCAL_FRONTEND_ORIGIN
    )


def test_preflight_de_creacion_es_permitido(client: TestClient) -> None:
    """El preflight OPTIONS de un POST JSON desde el frontend es aceptado."""
    response = client.options(
        "/ejes",
        headers={
            "Origin": LOCAL_FRONTEND_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert (
        response.headers.get("access-control-allow-origin") == LOCAL_FRONTEND_ORIGIN
    )
    allow_methods = response.headers.get("access-control-allow-methods", "")
    assert "POST" in allow_methods


def test_origen_no_permitido_no_recibe_allow_origin(client: TestClient) -> None:
    """Un origen fuera de la lista no obtiene la cabecera de permiso de origen."""
    response = client.get(
        "/ejes", headers={"Origin": "http://malicious.example"}
    )

    # La petición en sí responde 200 (CORS lo aplica el navegador), pero el
    # backend no debe autorizar explícitamente ese origen.
    assert response.headers.get("access-control-allow-origin") != "http://malicious.example"
