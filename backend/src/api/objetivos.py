"""Router FastAPI del Objetivo SMART (tarea 11.4).

Expone los endpoints HTTP del tercer nivel de la jerarquía ENCA. Pertenece a la
capa de rutas (``design.md`` "Architecture"): valida el contrato de entrada,
invoca el ``ObjetivoService`` y traduce el resultado al contrato de salida. No
contiene reglas de negocio ni captura excepciones de dominio (las traduce a HTTP
el manejador de ``backend/src/api/error_handlers.py``).

La referencia al padre (``meta_id``) proviene de la **ruta anidada**, no del
cuerpo (design.md "Contratos Pydantic").

Endpoints (design.md "Endpoints de la API — Objetivos SMART"):

======  ==============================  ==================================  ====================
Método  Ruta                            Propósito                           Respuesta
======  ==============================  ==================================  ====================
POST    ``/metas/{meta_id}/objetivos``  Crear Objetivo bajo una Meta        ``ObjetivoResponse`` (201); 404 (Meta), 422
GET     ``/metas/{meta_id}/objetivos``  Listar Objetivos de una Meta        ``list[ObjetivoResponse]`` (200, puede ser ``[]``); 404 (Meta)
GET     ``/objetivos/{id}``             Obtener Objetivo por id             ``ObjetivoResponse`` (200/404)
======  ==============================  ==================================  ====================

Requisitos: 3.1–3.7, 8.2 (referencia a padre inexistente → 404), 8.3 (validación
de forma → 422).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.src.core.database import get_db
from backend.src.domain.entities import Objetivo
from backend.src.schemas.objetivo import ObjetivoCreate, ObjetivoResponse
from backend.src.services.objetivo_service import ObjetivoService

router = APIRouter(tags=["Objetivos"])


@router.post(
    "/metas/{meta_id}/objetivos",
    response_model=ObjetivoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un Objetivo bajo una Meta",
)
def crear_objetivo(
    meta_id: int, datos: ObjetivoCreate, db: Session = Depends(get_db)
) -> ObjetivoResponse:
    """Crea un Objetivo bajo la Meta ``meta_id`` y lo devuelve (201).

    Si la Meta padre no existe, el servicio lanza
    ``InvalidParentReferenceError`` → 404 (Req 3.2, 8.2). Un cuerpo inválido
    produce 422 (Req 3.3, 8.3).
    """
    servicio = ObjetivoService(db)
    objetivo = servicio.crear(meta_id, Objetivo(descripcion=datos.descripcion))
    db.commit()
    return ObjetivoResponse.model_validate(objetivo)


@router.get(
    "/metas/{meta_id}/objetivos",
    response_model=list[ObjetivoResponse],
    summary="Listar los Objetivos de una Meta",
)
def listar_objetivos(
    meta_id: int, db: Session = Depends(get_db)
) -> list[ObjetivoResponse]:
    """Devuelve los Objetivos de la Meta ``meta_id``; puede ser ``[]`` (Req 3.4).

    Si la Meta no existe, el servicio lanza ``NotFoundError`` → 404 (Req 3.5).
    """
    servicio = ObjetivoService(db)
    return [
        ObjetivoResponse.model_validate(o)
        for o in servicio.listar_por_meta(meta_id)
    ]


@router.get(
    "/objetivos/{objetivo_id}",
    response_model=ObjetivoResponse,
    summary="Obtener un Objetivo por id",
)
def obtener_objetivo(
    objetivo_id: int, db: Session = Depends(get_db)
) -> ObjetivoResponse:
    """Devuelve el Objetivo con el ``id`` dado (Req 3.6).

    Si no existe, el servicio lanza ``NotFoundError`` → 404 (Req 3.7).
    """
    servicio = ObjetivoService(db)
    return ObjetivoResponse.model_validate(servicio.obtener(objetivo_id))
