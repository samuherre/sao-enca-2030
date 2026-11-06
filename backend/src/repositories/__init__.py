"""Capa `repositories` del backend — acceso a datos vía SQLAlchemy.

Esta capa es el **único** punto del backend que conoce consultas y sesiones de
SQLAlchemy (design.md "Architecture"; tech.md §28, §9). Cada repositorio recibe
una ``Session`` de SQLAlchemy y expone operaciones de persistencia y consulta
para una entidad de la jerarquía ENCA, devolviendo y aceptando **entidades de
dominio** (``backend.src.domain.entities``), no modelos ORM.

Patrón común (design.md "Components and Interfaces"):

- ``crear(entidad) -> entidad``: persiste la entidad y devuelve la entidad de
  dominio con su ``id`` generado.
- ``obtener_por_id(id) -> entidad | None``: recupera por clave primaria, o
  ``None`` si no existe.
- ``listar_por_padre(padre_id) -> list[entidad]``: colección de hijos de un
  padre (``[]`` si no hay).

El ``EjeRepository`` (raíz) añade ``listar_todos() -> list[Eje]``. Los
repositorios de entidades hijas añaden ``padre_existe(padre_id) -> bool``.

Los repositorios mapean entre modelos ORM (``backend.src.models``) y entidades
de dominio en ambas direcciones, preservando la independencia del dominio
respecto del ORM.
"""

from backend.src.repositories.actividad_repository import ActividadRepository
from backend.src.repositories.eje_repository import EjeRepository
from backend.src.repositories.indicador_repository import IndicadorRepository
from backend.src.repositories.meta_repository import MetaRepository
from backend.src.repositories.objetivo_repository import ObjetivoRepository

__all__ = [
    "EjeRepository",
    "MetaRepository",
    "ObjetivoRepository",
    "IndicadorRepository",
    "ActividadRepository",
]
