"""Tarea 15.8 — Respuestas de error HTTP (404 y 422) sin trazas.

Consultar por id inexistente devuelve **404** en cada entidad y en el árbol; los
cuerpos inválidos devuelven **422**; y ninguna respuesta de error expone trazas
de pila, identificadores internos ni detalles técnicos.

Requisitos: 1.5, 2.7, 3.7, 4.6, 5.7, 6.5, 7.9, 8.3.
"""

from __future__ import annotations

import pytest

ID_INEXISTENTE = 999999

# Rutas GET por id que deben devolver 404 cuando el recurso no existe.
RUTAS_GET_POR_ID = [
    pytest.param(f"/ejes/{ID_INEXISTENTE}", id="eje"),
    pytest.param(f"/metas/{ID_INEXISTENTE}", id="meta"),
    pytest.param(f"/objetivos/{ID_INEXISTENTE}", id="objetivo"),
    pytest.param(f"/indicadores/{ID_INEXISTENTE}", id="indicador"),
    pytest.param(f"/actividades/{ID_INEXISTENTE}", id="actividad"),
    pytest.param(f"/ejes/{ID_INEXISTENTE}/arbol", id="arbol"),
]

# Fragmentos que delatarían una traza de pila o detalle interno filtrado.
FRAGMENTOS_PROHIBIDOS = [
    "Traceback",
    "File \"",
    "line ",
    "sqlalchemy",
    "psycopg",
    ".py",
    "Session",
    "SELECT",
]


def _sin_detalles_tecnicos(texto: str) -> bool:
    bajo = texto.lower()
    return not any(frag.lower() in bajo for frag in FRAGMENTOS_PROHIBIDOS)


class TestNotFound404:
    """Req 1.5, 2.7, 3.7, 4.6, 5.7, 6.5: id inexistente => 404 por entidad y árbol."""

    @pytest.mark.parametrize("ruta", RUTAS_GET_POR_ID)
    def test_get_por_id_inexistente_devuelve_404(self, client, ruta):
        resp = client.get(ruta)
        assert resp.status_code == 404
        cuerpo = resp.json()
        # Cuerpo de error uniforme {detail, error} (design.md "Error Handling").
        assert "detail" in cuerpo
        assert "error" in cuerpo


class TestValidacion422:
    """Req 8.3: cuerpos inválidos (sin campo obligatorio) => 422."""

    def test_crear_eje_sin_nombre_422(self, client):
        resp = client.post("/ejes", json={})
        assert resp.status_code == 422

    def test_crear_eje_con_campo_extra_422(self, client):
        resp = client.post("/ejes", json={"nombre": "X", "campo_desconocido": 1})
        assert resp.status_code == 422

    def test_json_malformado_no_rompe_el_servidor(self, client):
        # Cuerpo no-JSON: FastAPI responde 422 sin exponer trazas.
        resp = client.post(
            "/ejes", content="no es json", headers={"Content-Type": "application/json"}
        )
        assert resp.status_code == 422


class TestSinTrazasNiDetallesTecnicos:
    """Req 7.9: las respuestas de error no exponen trazas ni detalles internos."""

    @pytest.mark.parametrize("ruta", RUTAS_GET_POR_ID)
    def test_404_no_expone_detalles_tecnicos(self, client, ruta):
        resp = client.get(ruta)
        assert resp.status_code == 404
        assert _sin_detalles_tecnicos(resp.text), resp.text

    def test_422_no_expone_detalles_tecnicos(self, client):
        resp = client.post("/ejes", json={})
        assert resp.status_code == 422
        assert _sin_detalles_tecnicos(resp.text), resp.text

    def test_404_devuelve_json_y_no_html_de_traza(self, client):
        resp = client.get(f"/ejes/{ID_INEXISTENTE}")
        assert resp.headers["content-type"].startswith("application/json")
