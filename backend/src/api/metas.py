"""Router FastAPI de la Meta (tarea 11.3).

Expone los endpoints HTTP del segundo nivel de la jerarquía ENCA. Pertenece a la
capa de rutas (``design.md`` "Architecture"): valida el contrato de entrada,
invoca el ``MetaService`` y traduce el resultado al contrato de salida. No
contiene reglas de negocio ni captura excepciones de dominio (las traduce a HTTP
el manejador de ``backend/src/api/error_handlers.py``).

La referencia al padre (``eje_id``) proviene de la **ruta anidada**, no del
cuerpo (design.md "Contratos Pydantic").

Endpoints (design.md "Endpoints de la API — Metas"):

======  =========================  ===============================  ====================
Método  Ruta                       Propósito                        Respuesta
======  =========================  ===============================  ====================
POST    ``/ejes/{eje_id}/metas``   Crear Meta bajo un Eje           ``MetaResponse`` (201); 404 (Eje), 422
GET     ``/ejes/{eje_id}/metas``   Listar Metas de un Eje           ``list[MetaResponse]`` (200, puede ser ``[]``); 404 (Eje)
GET     ``/metas/{id}``            Obtener Meta por id              ``MetaResponse`` (200/404)
======  =========================  ===============================  ====================

Requisitos: 2.1–2.7, 8.2 (referencia a padre inexistente → 404), 8.3 (validación
de forma → 422).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.src.core.database import get_db
from backend.src.domain.entities import Meta
from backend.src.schemas.meta import MetaCreate, MetaResponse
from backend.src.services.meta_service import MetaService

router = APIRouter(tags=["Metas"])


@router.post(
    "/ejes/{eje_id}/metas",
    response_model=MetaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una Meta bajo un Eje",
)
def crear_meta(
    eje_id: int, datos: MetaCreate, db: Session = Depends(get_db)
) -> MetaResponse:
    """Crea una Meta bajo el Eje ``eje_id`` y la devuelve (201).

    Si el Eje padre no existe, el servicio lanza ``InvalidParentReferenceError``
    → 404 (Req 2.2, 8.2). Un cuerpo inválido produce 422 (Req 2.3, 8.3).
    """
    servicio = MetaService(db)
    meta = servicio.crear(eje_id, Meta(descripcion=datos.descripcion))
    db.commit()
    return MetaResponse.model_validate(meta)


@router.get(
    "/ejes/{eje_id}/metas",
    response_model=list[MetaResponse],
    summary="Listar las Metas de un Eje",
)
def listar_metas(eje_id: int, db: Session = Depends(get_db)) -> list[MetaResponse]:
    """Devuelve las Metas del Eje ``eje_id``; puede ser ``[]`` (Req 2.4/2.5).

    Si el Eje no existe, el servicio lanza ``NotFoundError`` → 404.
    """
    servicio = MetaService(db)
    return [MetaResponse.model_validate(m) for m in servicio.listar_por_eje(eje_id)]


@router.get(
    "/metas/{meta_id}",
    response_model=MetaResponse,
    summary="Obtener una Meta por id",
)
def obtener_meta(meta_id: int, db: Session = Depends(get_db)) -> MetaResponse:
    """Devuelve la Meta con el ``id`` dado (Req 2.6).

    Si no existe, el servicio lanza ``NotFoundError`` → 404 (Req 2.7).
    """
    servicio = MetaService(db)
    return MetaResponse.model_validate(servicio.obtener(meta_id))
