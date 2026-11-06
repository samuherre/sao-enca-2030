"""Excepciones de dominio del backend del Sistema_ENCA.

Define los errores de dominio que las capas de servicios y repositorios pueden
lanzar al aplicar las reglas de negocio de la jerarquía confirmada
(Eje → Meta → Objetivo → Indicador → Actividad).

Estas excepciones son **independientes de HTTP y de cualquier framework**
(tech.md §28, §32; structure.md §28): no importan FastAPI, Pydantic ni
SQLAlchemy. La traducción de cada excepción a un código HTTP se realiza
exclusivamente en la capa de rutas (`backend/src/api/`), según el mapeo
definido en `design.md` (sección "Error Handling"):

====================================  ===========  ====================================
Excepción de dominio                  Código HTTP  Requisitos
====================================  ===========  ====================================
``NotFoundError``                     404          1.5, 2.7, 3.7, 4.6, 5.7, 6.5
``InvalidParentReferenceError``       404          2.2, 3.2, 4.2, 5.2, 8.2
``MissingParentReferenceError``       422          8.3
``ValidationError``                   422          1.2, 2.3, 3.3, 4.3, 5.3
====================================  ===========  ====================================

Cada excepción expone un atributo ``error_code`` (código estable y legible) que
la capa de rutas puede incluir en el cuerpo JSON uniforme de error
(``{"detail": ..., "error": ...}``) para que el frontend lo mapee a mensajes
amigables, sin exponer trazas ni detalles internos (Req 7.9; tech.md §32).
"""

from __future__ import annotations


class DomainError(Exception):
    """Excepción base de todos los errores de dominio del Sistema_ENCA.

    No debe lanzarse directamente; sirve como raíz común para que las capas
    superiores puedan capturar cualquier error de dominio de forma genérica.
    Define un ``error_code`` estable que la capa de rutas usa para construir el
    cuerpo de error uniforme (campo ``error``).
    """

    #: Código de error estable y legible asociado a la excepción.
    error_code: str = "domain_error"

    def __init__(self, detail: str | None = None) -> None:
        self.detail = detail or self.__class__.__doc__ or self.error_code
        super().__init__(self.detail)


class ValidationError(DomainError):
    """Un campo obligatorio es nulo, vacío o contiene solo espacios.

    Representa un fallo de validación de forma de los datos de entrada. En la
    práctica, la validación de los contratos se delega a Pydantic en la capa de
    rutas; esta excepción está disponible para validaciones de invariantes
    aplicadas en el dominio o los servicios cuando sea necesario.

    Mapeo HTTP: 422 (Req 1.2, 2.3, 3.3, 4.3, 5.3).
    """

    error_code = "validation_error"


class NotFoundError(DomainError):
    """Una entidad (o el Eje raíz de un árbol) no existe para el id solicitado.

    Se lanza al consultar por id una entidad inexistente o al pedir el árbol de
    un Eje que no existe.

    Mapeo HTTP: 404 (Req 1.5, 2.7, 3.7, 4.6, 5.7, 6.5).
    """

    error_code = "not_found"


class InvalidParentReferenceError(DomainError):
    """La entidad padre referenciada no existe.

    Se lanza al intentar crear una entidad hija cuyo padre inmediato
    (identificado por la ruta anidada, p. ej. ``/ejes/{eje_id}/metas``) no
    existe.

    Mapeo HTTP: 404 (Req 2.2, 3.2, 4.2, 5.2, 8.2).
    """

    error_code = "parent_not_found"


class MissingParentReferenceError(DomainError):
    """La referencia a la entidad padre es nula o está ausente.

    Se lanza cuando no se proporciona el identificador del padre requerido para
    crear una entidad hija (referencia obligatoria ausente), a diferencia de
    ``InvalidParentReferenceError``, donde la referencia existe pero apunta a un
    padre inexistente.

    Mapeo HTTP: 422 (Req 8.3).
    """

    error_code = "missing_parent_reference"


__all__ = [
    "DomainError",
    "ValidationError",
    "NotFoundError",
    "InvalidParentReferenceError",
    "MissingParentReferenceError",
]
