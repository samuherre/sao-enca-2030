"""Contratos Pydantic de la Meta (tarea 10.3).

Define los schemas de **entrada** (``MetaCreate``) y de **salida**
(``MetaResponse``) del segundo nivel de la jerarquía ENCA, conforme a
``design.md`` ("Contratos Pydantic") y a los requisitos 2.1, 2.6 y 6.2.

Reglas aplicadas:

- Ambos contratos heredan de :class:`backend.src.schemas.base.SchemaBase`
  (``extra="forbid"``; Req 9.4).
- ``MetaCreate.descripcion`` es obligatorio: usa :data:`TextoRequerido` (Req 2.3).
  La referencia al padre (``eje_id``) **no** viaja en el cuerpo: se toma de la
  ruta anidada ``/ejes/{eje_id}/metas`` (design.md "Contratos Pydantic", notas).
  Como ``SchemaBase`` prohíbe campos extra, enviar ``eje_id`` en el cuerpo
  produce 422.
- ``MetaResponse`` expone ``id``, ``descripcion`` y ``eje_id`` (referencia al
  padre inmediato para la navegación hija→padre, Req 6.2). Se habilita
  ``from_attributes=True`` para serializar desde el ORM/dominio.

No contiene atributos PENDING_VALIDATION.
"""

from __future__ import annotations

from pydantic import ConfigDict

from backend.src.schemas.base import SchemaBase, TextoRequerido


class MetaCreate(SchemaBase):
    """Contrato de entrada para crear una Meta bajo un Eje.

    :ivar descripcion: Descripción de la Meta. Obligatoria (no nula, no vacía
        tras ``strip``). El ``eje_id`` se toma de la ruta, no del cuerpo.
    """

    descripcion: TextoRequerido


class MetaResponse(SchemaBase):
    """Contrato de salida de una Meta.

    :ivar id: Identificador único de la Meta.
    :ivar descripcion: Descripción de la Meta.
    :ivar eje_id: Identificador del Eje padre (navegación hija→padre, Req 6.2).
    """

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: int
    descripcion: str
    eje_id: int
