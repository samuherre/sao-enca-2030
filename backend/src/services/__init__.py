"""Capa `services` del backend — casos de uso y orquestación.

Esta capa contiene la **lógica de aplicación** del Sistema_ENCA (design.md
"Architecture"; tech.md §28, §4). Cada servicio coordina validaciones que
requieren acceso a datos (p. ej. "el padre debe existir" antes de crear una
entidad hija), invoca los repositorios (``backend.src.repositories``) y aplica
reglas de dominio, devolviendo **entidades de dominio**
(``backend.src.domain.entities``) y lanzando **excepciones de dominio**
(``backend.src.domain.exceptions``).

Los servicios **no conocen FastAPI ni HTTP**: la traducción de excepciones de
dominio a códigos HTTP corresponde exclusivamente a la capa de rutas
(``backend.src.api``). Cada servicio recibe una ``Session`` de SQLAlchemy y
construye sobre ella sus repositorios; no gestiona el ciclo de vida de la sesión
(apertura, commit o cierre), que corresponde a la capa superior.

Patrón común (design.md "Components and Interfaces"):

- Servicios de entidad (``EjeService``, ``MetaService``, ``ObjetivoService``,
  ``IndicadorService``, ``ActividadService``): ``crear`` (verificando el padre
  en las entidades hijas), ``obtener`` (lanza ``NotFoundError`` si el id no
  existe) y el listado por padre o por colección.
- ``HierarchyService``: ensambla el árbol anidado de cinco niveles de un Eje
  reutilizando los repositorios de cada nivel.
"""

from backend.src.services.actividad_service import ActividadService
from backend.src.services.eje_service import EjeService
from backend.src.services.hierarchy_service import HierarchyService
from backend.src.services.indicador_service import IndicadorService
from backend.src.services.meta_service import MetaService
from backend.src.services.objetivo_service import ObjetivoService

__all__ = [
    "EjeService",
    "MetaService",
    "ObjetivoService",
    "IndicadorService",
    "ActividadService",
    "HierarchyService",
]
