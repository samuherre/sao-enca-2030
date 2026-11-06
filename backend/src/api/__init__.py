"""Capa de rutas (API) del backend del Sistema_ENCA.

Este paquete contiene la capa de presentación HTTP (``design.md``: "Routes";
structure.md §6, §28). Es la **única** capa que conoce HTTP: traduce los
resultados de los servicios a respuestas y mapea las excepciones de dominio
(independientes de framework) a códigos y cuerpos HTTP uniformes.

Elementos expuestos por el paquete:

- :func:`register_exception_handlers`: registra en la app FastAPI los
  manejadores que traducen las excepciones de dominio y los errores de
  validación de Pydantic/FastAPI al cuerpo JSON uniforme de error
  ``{"detail": ..., "error": ...}`` sin exponer trazas (tech.md §32, Req 7.9).

Los routers concretos por entidad (Eje, Meta, Objetivo, Indicador, Actividad)
y del árbol jerárquico se definen en los módulos de las tareas 11.2–11.7 y se
registran en la app en la tarea 11.8.
"""

from backend.src.api.error_handlers import register_exception_handlers

__all__ = [
    "register_exception_handlers",
]
