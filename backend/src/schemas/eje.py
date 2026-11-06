"""Contratos Pydantic del Eje estratégico (tarea 10.2).

Define los schemas de **entrada** (``EjeCreate``) y de **salida** (``EjeResponse``)
del nivel raíz de la jerarquía ENCA (D-001), conforme a ``design.md``
("Contratos Pydantic") y a los requisitos 1.1 y 6.3.

Reglas aplicadas:

- Ambos contratos heredan de :class:`backend.src.schemas.base.SchemaBase`, que
  fija ``extra="forbid"`` (enviar campos no declarados → 422, Req 9.4).
- ``EjeCreate.nombre`` es obligatorio: usa :data:`TextoRequerido` (no nulo, no
  vacío tras ``strip``; Req 1.2). ``descripcion`` es opcional.
- ``EjeResponse`` expone únicamente ``id``, ``nombre`` y ``descripcion``. El Eje
  es la raíz de la jerarquía, por lo que **no** incluye referencia a un padre
  (Req 6.3). Se habilita ``from_attributes=True`` para poder serializar desde el
  modelo ORM (``EjeModel``) o la entidad de dominio.

No contiene atributos PENDING_VALIDATION.
"""

from __future__ import annotations

from pydantic import ConfigDict

from backend.src.schemas.base import SchemaBase, TextoRequerido


class EjeCreate(SchemaBase):
    """Contrato de entrada para crear un Eje.

    :ivar nombre: Nombre del Eje. Obligatorio (no nulo, no vacío tras ``strip``).
    :ivar descripcion: Descripción opcional del Eje.
    """

    nombre: TextoRequerido
    descripcion: str | None = None


class EjeResponse(SchemaBase):
    """Contrato de salida de un Eje.

    No incluye referencia a padre: el Eje es la raíz de la jerarquía (Req 6.3).

    :ivar id: Identificador único del Eje.
    :ivar nombre: Nombre del Eje.
    :ivar descripcion: Descripción del Eje (puede ser nula).
    """

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: int
    nombre: str
    descripcion: str | None = None
