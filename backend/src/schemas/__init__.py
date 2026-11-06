"""Contratos Pydantic (Create / Response) de la API del Sistema_ENCA.

Este paquete agrupa los **schemas** de la capa de contrato (``design.md``:
"Contratos Pydantic"; structure.md §6). Los contratos de entrada (Create) y de
salida (Response) están separados del modelo de persistencia ORM (tech.md §5).

Elementos comunes expuestos por el paquete (tarea 10.1):

- :class:`SchemaBase`: base con ``extra="forbid"`` que prohíbe campos extra en
  todos los contratos (enviar atributos no declarados produce 422, Req 9.4).
- :data:`TextoRequerido`: tipo anotado reutilizable para campos de texto
  obligatorios (no nulo, no vacío tras ``strip``; Req 1.2, 2.3, 3.3, 4.3, 5.3).

Los contratos concretos por entidad (Eje, Meta, Objetivo, Indicador, Actividad)
y del árbol jerárquico se definen en los módulos de las tareas 10.2–10.7 y
heredan de :class:`SchemaBase`.
"""

from backend.src.schemas.actividad import ActividadCreate, ActividadResponse
from backend.src.schemas.arbol import (
    ActividadArbol,
    EjeArbolResponse,
    IndicadorArbol,
    MetaArbol,
    ObjetivoArbol,
)
from backend.src.schemas.base import SchemaBase, TextoRequerido
from backend.src.schemas.eje import EjeCreate, EjeResponse
from backend.src.schemas.indicador import IndicadorCreate, IndicadorResponse
from backend.src.schemas.meta import MetaCreate, MetaResponse
from backend.src.schemas.objetivo import ObjetivoCreate, ObjetivoResponse

__all__ = [
    # Base / utilidades comunes (tarea 10.1)
    "SchemaBase",
    "TextoRequerido",
    # Eje (tarea 10.2)
    "EjeCreate",
    "EjeResponse",
    # Meta (tarea 10.3)
    "MetaCreate",
    "MetaResponse",
    # Objetivo (tarea 10.4)
    "ObjetivoCreate",
    "ObjetivoResponse",
    # Indicador (tarea 10.5)
    "IndicadorCreate",
    "IndicadorResponse",
    # Actividad (tarea 10.6)
    "ActividadCreate",
    "ActividadResponse",
    # Árbol jerárquico (tarea 10.7)
    "EjeArbolResponse",
    "MetaArbol",
    "ObjetivoArbol",
    "IndicadorArbol",
    "ActividadArbol",
]
