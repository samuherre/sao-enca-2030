"""Router FastAPI del Eje estratégico (tarea 11.2).

Expone los endpoints HTTP del nivel raíz de la jerarquía ENCA (D-001). Pertenece
a la capa de rutas (``design.md`` "Architecture"): es la **única** capa que
conoce HTTP. Solo valida el contrato de entrada (Pydantic), invoca el
``EjeService`` y traduce el resultado al contrato de salida; **no** contiene
reglas de negocio ni captura excepciones de dominio (las traduce a HTTP el
manejador registrado en ``backend/src/api/error_handlers.py``).

Endpoints (design.md "Endpoints de la API — Ejes"):

======  ============  ========================================  ====================
Método  Ruta          Propósito                                 Respuesta
======  ============  ========================================  ====================
POST    ``/ejes``     Crear un Eje                              ``EjeResponse`` (201)
GET     ``/ejes``     Listar todos los Ejes                     ``list[EjeResponse]`` (200, puede ser ``[]``)
GET     ``/ejes/{id}``Obtener un Eje por id                     ``EjeResponse`` (200/404)
======  ============  ========================================  ====================

Requisitos: 1.1 (crear), 1.2 (validación → 422), 1.3 (listar), 1.4 (obtener),
1.5 (id inexistente → 404).

Convención de commit (consistente en todos los routers de la Spec): los
servicios y repositorios hacen ``flush`` pero **no** ``commit``; el router
confirma la transacción con ``db.commit()`` tras una creación correcta, de modo
que el control transaccional quede en el borde de la petición HTTP.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.src.core.database import get_db
from backend.src.domain.entities import Eje
from backend.src.schemas.eje import EjeCreate, EjeResponse
from backend.src.services.eje_service import EjeService

router = APIRouter(tags=["Ejes"])


@router.post(
    "/ejes",
    response_model=EjeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un Eje",
)
def crear_eje(datos: EjeCreate, db: Session = Depends(get_db)) -> EjeResponse:
    """Crea un Eje y lo devuelve con su ``id`` generado (201).

    Pydantic valida el cuerpo (``nombre`` obligatorio; campos extra prohibidos);
    un cuerpo inválido produce 422 antes de llegar aquí (Req 1.2). Tras crear se
    confirma la transacción.
    """
    servicio = EjeService(db)
    eje = servicio.crear(Eje(nombre=datos.nombre, descripcion=datos.descripcion))
    db.commit()
    return EjeResponse.model_validate(eje)


@router.get(
    "/ejes",
    response_model=list[EjeResponse],
    summary="Listar todos los Ejes",
)
def listar_ejes(db: Session = Depends(get_db)) -> list[EjeResponse]:
    """Devuelve la colección completa de Ejes; puede ser ``[]`` (Req 1.3)."""
    servicio = EjeService(db)
    return [EjeResponse.model_validate(eje) for eje in servicio.listar()]


@router.get(
    "/ejes/{eje_id}",
    response_model=EjeResponse,
    summary="Obtener un Eje por id",
)
def obtener_eje(eje_id: int, db: Session = Depends(get_db)) -> EjeResponse:
    """Devuelve el Eje con el ``id`` dado (Req 1.4).

    Si no existe, el ``EjeService`` lanza ``NotFoundError`` y el manejador de
    excepciones responde 404 (Req 1.5).
    """
    servicio = EjeService(db)
    return EjeResponse.model_validate(servicio.obtener(eje_id))
