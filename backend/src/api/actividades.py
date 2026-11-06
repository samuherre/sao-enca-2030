"""Router FastAPI de la Actividad (tarea 11.6).

Expone los endpoints HTTP del quinto y último nivel de la jerarquía ENCA.
Pertenece a la capa de rutas (``design.md`` "Architecture"): valida el contrato
de entrada, invoca el ``ActividadService`` y traduce el resultado al contrato de
salida. No contiene reglas de negocio ni captura excepciones de dominio (las
traduce a HTTP el manejador de ``backend/src/api/error_handlers.py``).

La referencia al padre (``indicador_id``) proviene de la **ruta anidada**, no
del cuerpo (design.md "Contratos Pydantic"). Los contratos **no** exponen
atributos PENDING_VALIDATION de la Actividad (Req 5.8, 9.2).

Endpoints (design.md "Endpoints de la API — Actividades"):

======  ==========================================  =====================================  ====================
Método  Ruta                                        Propósito                              Respuesta
======  ==========================================  =====================================  ====================
POST    ``/indicadores/{indicador_id}/actividades`` Crear Actividad bajo un Indicador      ``ActividadResponse`` (201); 404 (Indicador), 422
GET     ``/indicadores/{indicador_id}/actividades`` Listar Actividades de un Indicador     ``list[ActividadResponse]`` (200, puede ser ``[]``); 404 (Indicador)
GET     ``/actividades/{id}``                       Obtener Actividad por id               ``ActividadResponse`` (200/404)
======  ==========================================  =====================================  ====================

Requisitos: 5.1–5.8, 8.2 (referencia a padre inexistente → 404), 8.3 (validación
de forma → 422).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.src.core.database import get_db
from backend.src.domain.entities import Actividad
from backend.src.schemas.actividad import ActividadCreate, ActividadResponse
from backend.src.services.actividad_service import ActividadService

router = APIRouter(tags=["Actividades"])


@router.post(
    "/indicadores/{indicador_id}/actividades",
    response_model=ActividadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una Actividad bajo un Indicador",
)
def crear_actividad(
    indicador_id: int, datos: ActividadCreate, db: Session = Depends(get_db)
) -> ActividadResponse:
    """Crea una Actividad bajo el Indicador ``indicador_id`` y la devuelve (201).

    Si el Indicador padre no existe, el servicio lanza
    ``InvalidParentReferenceError`` → 404 (Req 5.2, 8.2). Un cuerpo inválido —o
    con atributos PENDING_VALIDATION— produce 422 (Req 5.3, 5.8, 9.2).
    """
    servicio = ActividadService(db)
    actividad = servicio.crear(
        indicador_id, Actividad(descripcion=datos.descripcion)
    )
    db.commit()
    return ActividadResponse.model_validate(actividad)


@router.get(
    "/indicadores/{indicador_id}/actividades",
    response_model=list[ActividadResponse],
    summary="Listar las Actividades de un Indicador",
)
def listar_actividades(
    indicador_id: int, db: Session = Depends(get_db)
) -> list[ActividadResponse]:
    """Devuelve las Actividades del Indicador ``indicador_id``; puede ser ``[]``.

    Req 5.4/5.5. Si el Indicador no existe, el servicio lanza ``NotFoundError``
    → 404.
    """
    servicio = ActividadService(db)
    return [
        ActividadResponse.model_validate(a)
        for a in servicio.listar_por_indicador(indicador_id)
    ]


@router.get(
    "/actividades/{actividad_id}",
    response_model=ActividadResponse,
    summary="Obtener una Actividad por id",
)
def obtener_actividad(
    actividad_id: int, db: Session = Depends(get_db)
) -> ActividadResponse:
    """Devuelve la Actividad con el ``id`` dado (Req 5.6).

    Si no existe, el servicio lanza ``NotFoundError`` → 404 (Req 5.7).
    """
    servicio = ActividadService(db)
    return ActividadResponse.model_validate(servicio.obtener(actividad_id))
