"""Router FastAPI de la navegación de la jerarquía (tarea 11.7).

Expone el endpoint de navegación del árbol anidado completo de un Eje a lo largo
de los cinco niveles confirmados (Eje → Meta → Objetivo SMART → Indicador →
Actividad). Pertenece a la capa de rutas (``design.md`` "Architecture"): invoca
el ``HierarchyService`` y serializa su resultado al contrato de salida. No
contiene reglas de negocio ni captura excepciones de dominio (las traduce a HTTP
el manejador de ``backend/src/api/error_handlers.py``).

El ``HierarchyService`` devuelve una **estructura anidada de diccionarios** con
los campos confirmados de cada nivel y la lista de hijos (``[]`` cuando no hay
hijos); aquí se valida/serializa a ``EjeArbolResponse`` (Req 6.4). El Eje raíz no
incluye referencia a un padre (Req 6.3) y los nodos anidados omiten el ``*_id``
del padre (referencia implícita por anidamiento, Req 6.2).

Endpoint (design.md "Endpoints de la API — Navegación de la jerarquía"):

======  ========================  =============================================  ====================
Método  Ruta                      Propósito                                      Respuesta
======  ========================  =============================================  ====================
GET     ``/ejes/{eje_id}/arbol``  Árbol anidado completo de un Eje (5 niveles)   ``EjeArbolResponse`` (200/404)
======  ========================  =============================================  ====================

Requisitos: 6.1 (árbol de cinco niveles), 6.4 (``[]`` en nodos sin hijos),
6.5 (Eje inexistente → 404).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.src.core.database import get_db
from backend.src.schemas.arbol import EjeArbolResponse
from backend.src.services.hierarchy_service import HierarchyService

router = APIRouter(tags=["Jerarquía"])


@router.get(
    "/ejes/{eje_id}/arbol",
    response_model=EjeArbolResponse,
    summary="Obtener el árbol anidado completo de un Eje",
)
def obtener_arbol(eje_id: int, db: Session = Depends(get_db)) -> EjeArbolResponse:
    """Devuelve el árbol anidado de cinco niveles del Eje ``eje_id`` (Req 6.1).

    Si el Eje no existe, el ``HierarchyService`` lanza ``NotFoundError`` y el
    manejador de excepciones responde 404 (Req 6.5). Los nodos sin hijos exponen
    ``[]`` (Req 6.4).
    """
    servicio = HierarchyService(db)
    return EjeArbolResponse.model_validate(servicio.obtener_arbol(eje_id))
