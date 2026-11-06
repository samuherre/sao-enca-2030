"""Contratos Pydantic del Indicador (tarea 10.5).

Define los schemas de **entrada** (``IndicadorCreate``) y de **salida**
(``IndicadorResponse``) del cuarto nivel de la jerarquía ENCA, conforme a
``design.md`` ("Contratos Pydantic") y a los requisitos 4.1, 4.5, 4.7, 9.1 y 6.2.

Reglas aplicadas:

- Ambos contratos heredan de :class:`backend.src.schemas.base.SchemaBase`
  (``extra="forbid"``; Req 9.4).
- ``IndicadorCreate`` exige ``nombre`` y ``descripcion`` obligatorios mediante
  :data:`TextoRequerido` (Req 4.3). El ``objetivo_id`` se toma de la ruta
  ``/objetivos/{objetivo_id}/indicadores``, no del cuerpo.
- ``IndicadorResponse`` expone ``id``, ``nombre``, ``descripcion`` y
  ``objetivo_id`` (navegación hija→padre, Req 6.2). Se habilita
  ``from_attributes=True``.

**No** incluye ningún atributo PENDING_VALIDATION (unidad de medida, valor
objetivo, valor actual, fecha de medición, fuente/evidencia, estado) ni en el
Create ni en el Response (Req 4.7, 9.1; design.md "Columnas futuras no
implementadas").
"""

from __future__ import annotations

from pydantic import ConfigDict

from backend.src.schemas.base import SchemaBase, TextoRequerido


class IndicadorCreate(SchemaBase):
    """Contrato de entrada para crear un Indicador bajo un Objetivo.

    :ivar nombre: Nombre del Indicador. Obligatorio (no nulo, no vacío tras
        ``strip``).
    :ivar descripcion: Descripción del Indicador. Obligatoria. El ``objetivo_id``
        se toma de la ruta, no del cuerpo.
    """

    nombre: TextoRequerido
    descripcion: TextoRequerido


class IndicadorResponse(SchemaBase):
    """Contrato de salida de un Indicador.

    No expone atributos PENDING_VALIDATION (Req 4.7, 9.1).

    :ivar id: Identificador único del Indicador.
    :ivar nombre: Nombre del Indicador.
    :ivar descripcion: Descripción del Indicador.
    :ivar objetivo_id: Identificador del Objetivo padre (navegación hija→padre,
        Req 6.2).
    """

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: int
    nombre: str
    descripcion: str
    objetivo_id: int
