"""Manejadores de excepciones: dominio → HTTP (tarea 11.1).

Esta es la **única** capa que conoce HTTP (``design.md``: "Error Handling";
tech.md §32). Traduce las excepciones de dominio —independientes de framework
(``backend/src/domain/exceptions.py``)— y los errores de validación de forma de
Pydantic/FastAPI a respuestas HTTP con un **cuerpo JSON uniforme**:

.. code-block:: json

    { "detail": "Mensaje comprensible", "error": "codigo_de_error" }

Mapeo (``design.md`` sección "Error Handling"):

====================================  ===========  ================================
Excepción / situación                 Código HTTP  Requisitos
====================================  ===========  ================================
``NotFoundError``                     404          1.5, 2.7, 3.7, 4.6, 5.7, 6.5
``InvalidParentReferenceError``       404          2.2, 3.2, 4.2, 5.2, 8.2
``MissingParentReferenceError``       422          8.3
``ValidationError`` (dominio)         422          1.2, 2.3, 3.3, 4.3, 5.3
Validación Pydantic/FastAPI           422          1.2, 2.3, 3.3, 4.3, 5.3, 9.4
====================================  ===========  ================================

Garantías (tech.md §32, Req 7.9):

- La respuesta al cliente **nunca** incluye trazas de pila ni detalles internos.
- Los errores de dominio se **registran** en el log del backend con contexto
  suficiente para diagnóstico, sin secretos (tech.md §20, §31). La respuesta al
  cliente conserva únicamente el mensaje de alto nivel.
- Todas las respuestas de error comparten la misma forma de cuerpo, de modo que
  el frontend pueda mapear el campo ``error`` a mensajes amigables.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.src.domain.exceptions import (
    DomainError,
    InvalidParentReferenceError,
    MissingParentReferenceError,
    NotFoundError,
    ValidationError,
)

logger = logging.getLogger(__name__)

#: Código estable que acompaña a los errores de validación de forma producidos
#: por Pydantic/FastAPI (coherente con ``ValidationError.error_code`` de dominio).
VALIDATION_ERROR_CODE = "validation_error"

#: Mensaje de alto nivel para errores de validación de forma. No incluye detalles
#: internos ni trazas; el frontend puede mapear el ``error`` a un texto propio.
VALIDATION_ERROR_DETAIL = "Los datos enviados no son válidos."

#: Mapeo de cada tipo de excepción de dominio a su código HTTP.
#: El orden importa: los subtipos deben consultarse antes que ``DomainError``.
_DOMAIN_STATUS_BY_EXCEPTION: tuple[tuple[type[DomainError], int], ...] = (
    (NotFoundError, status.HTTP_404_NOT_FOUND),
    (InvalidParentReferenceError, status.HTTP_404_NOT_FOUND),
    (MissingParentReferenceError, status.HTTP_422_UNPROCESSABLE_ENTITY),
    (ValidationError, status.HTTP_422_UNPROCESSABLE_ENTITY),
)

#: Código HTTP por defecto para una ``DomainError`` genérica no mapeada
#: explícitamente. 422 evita exponer el error como un 500 con traza.
_DEFAULT_DOMAIN_STATUS = status.HTTP_422_UNPROCESSABLE_ENTITY


def _error_body(detail: str, error_code: str) -> dict[str, str]:
    """Construye el cuerpo JSON uniforme de error.

    Devuelve siempre la misma forma ``{"detail", "error"}`` sin trazas ni
    detalles internos (Req 7.9; tech.md §32).
    """
    return {"detail": detail, "error": error_code}


def _status_for_domain_error(exc: DomainError) -> int:
    """Resuelve el código HTTP de una excepción de dominio según el mapeo.

    Recorre el mapeo en orden para respetar la jerarquía de excepciones y
    aplica un valor por defecto seguro para errores de dominio no mapeados.
    """
    for exc_type, http_status in _DOMAIN_STATUS_BY_EXCEPTION:
        if isinstance(exc, exc_type):
            return http_status
    return _DEFAULT_DOMAIN_STATUS


async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    """Traduce cualquier :class:`DomainError` al cuerpo HTTP uniforme.

    Registra el error en el log del backend (sin secretos ni traza enviada al
    cliente) y responde con ``{"detail", "error"}`` y el código HTTP mapeado.
    """
    http_status = _status_for_domain_error(exc)
    # Log de diagnóstico: incluye método y ruta, nunca secretos ni cuerpo.
    logger.warning(
        "Error de dominio %s (%s) en %s %s -> HTTP %s",
        exc.__class__.__name__,
        exc.error_code,
        request.method,
        request.url.path,
        http_status,
    )
    return JSONResponse(
        status_code=http_status,
        content=_error_body(exc.detail, exc.error_code),
    )


async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Traduce los errores de validación de Pydantic/FastAPI a 422 uniforme.

    FastAPI usa 422 para los fallos de validación del cuerpo/parámetros. Aquí se
    normaliza la respuesta al mismo cuerpo ``{"detail", "error"}`` que el resto
    de errores. Un cuerpo con campos extra (prohibidos por los schemas) o con
    campos obligatorios ausentes/vacíos cae en este manejador (Req 9.4, 1.2,
    2.3, 3.3, 4.3, 5.3).

    No se exponen trazas al cliente; el detalle estructurado de Pydantic se
    registra en el log para diagnóstico.
    """
    # jsonable_encoder asegura que los errores de Pydantic sean serializables
    # en el log (contienen, p. ej., objetos de tipo). No se envían al cliente.
    logger.info(
        "Error de validación en %s %s: %s",
        request.method,
        request.url.path,
        jsonable_encoder(exc.errors()),
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=_error_body(VALIDATION_ERROR_DETAIL, VALIDATION_ERROR_CODE),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Registra en la app FastAPI los manejadores de excepciones de la API.

    Se registra un único manejador para la raíz :class:`DomainError`, de modo
    que todas sus subclases (``NotFoundError``, ``InvalidParentReferenceError``,
    ``MissingParentReferenceError``, ``ValidationError``) se capturen y mapeen
    al código HTTP correspondiente. Además se sobreescribe el manejador de
    :class:`RequestValidationError` para unificar el cuerpo de error.

    Esta función la invoca la tarea 11.8 al construir la app en
    ``backend/src/main.py``.
    """
    app.add_exception_handler(DomainError, domain_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)


__all__ = [
    "register_exception_handlers",
    "domain_error_handler",
    "validation_error_handler",
    "VALIDATION_ERROR_CODE",
    "VALIDATION_ERROR_DETAIL",
]
