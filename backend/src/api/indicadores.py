"""Router FastAPI del Indicador (tarea 11.5).

Expone los endpoints HTTP del cuarto nivel de la jerarquía ENCA. Pertenece a la
capa de rutas (``design.md`` "Architecture"): valida el contrato de entrada,
invoca el ``IndicadorService`` y traduce el resultado al contrato de salida. No
contiene reglas de negocio ni captura excepciones de dominio (las traduce a HTTP
el manejador de ``backend/src/api/error_handlers.py``).

La referencia al padre (``objetivo_id``) proviene de la **ruta anidada**, no del
cuerpo (design.md "Contratos Pydantic"). Los contratos **no** exponen atributos
PENDING_VALIDATION del Indicador (Req 4.7, 9.1).

Endpoints (design.md "Endpoints de la API — Indicadores"):

======  =======================================  ====================================  ====================
Método  Ruta                                     Propósito                             Respuesta
======  =======================================  ====================================  ====================
POST    ``/objetivos/{objetivo_id}/indicadores`` Crear Indicador bajo un Objetivo      ``IndicadorResponse`` (201); 404 (Objetivo), 422
GET     ``/objetivos/{objetivo_id}/indicadores`` Listar Indicadores de un Objetivo     ``list[IndicadorResponse]`` (200, puede ser ``[]``); 404 (Objetivo)
GET     ``/indicadores/{id}``                    Obtener Indicador por id              ``IndicadorResponse`` (200/404)
======  =======================================  ====================================  ====================

Requisitos: 4.1–4.7, 8.2 (referencia a padre inexistente → 404), 8.3 (validación
de forma → 422).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.src.core.database import get_db
from backend.src.domain.entities import Indicador
from backend.src.schemas.indicador import IndicadorCreate, IndicadorResponse
from backend.src.services.indicador_service import IndicadorService

router = APIRouter(tags=["Indicadores"])


@router.post(
    "/objetivos/{objetivo_id}/indicadores",
    response_model=IndicadorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un Indicador bajo un Objetivo",
)
def crear_indicador(
    objetivo_id: int, datos: IndicadorCreate, db: Session = Depends(get_db)
) -> IndicadorResponse:
    """Crea un Indicador bajo el Objetivo ``objetivo_id`` y lo devuelve (201).

    Si el Objetivo padre no existe, el servicio lanza
    ``InvalidParentReferenceError`` → 404 (Req 4.2, 8.2). Un cuerpo inválido —o
    con atributos PENDING_VALIDATION— produce 422 (Req 4.3, 4.7, 9.1).
    """
    servicio = IndicadorService(db)
    indicador = servicio.crear(
        objetivo_id,
        Indicador(nombre=datos.nombre, descripcion=datos.descripcion),
    )
    db.commit()
    return IndicadorResponse.model_validate(indicador)


@router.get(
    "/objetivos/{objetivo_id}/indicadores",
    response_model=list[IndicadorResponse],
    summary="Listar los Indicadores de un Objetivo",
)
def listar_indicadores(
    objetivo_id: int, db: Session = Depends(get_db)
) -> list[IndicadorResponse]:
    """Devuelve los Indicadores del Objetivo ``objetivo_id``; puede ser ``[]``.

    Req 4.4. Si el Objetivo no existe, el servicio lanza ``NotFoundError`` → 404.
    """
    servicio = IndicadorService(db)
    return [
        IndicadorResponse.model_validate(i)
        for i in servicio.listar_por_objetivo(objetivo_id)
    ]


@router.get(
    "/indicadores/{indicador_id}",
    response_model=IndicadorResponse,
    summary="Obtener un Indicador por id",
)
def obtener_indicador(
    indicador_id: int, db: Session = Depends(get_db)
) -> IndicadorResponse:
    """Devuelve el Indicador con el ``id`` dado (Req 4.5).

    Si no existe, el servicio lanza ``NotFoundError`` → 404 (Req 4.6).
    """
    servicio = IndicadorService(db)
    return IndicadorResponse.model_validate(servicio.obtener(indicador_id))
