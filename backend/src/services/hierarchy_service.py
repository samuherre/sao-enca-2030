"""Servicio de aplicación de la navegación de la jerarquía (árbol anidado).

Tarea 9.6 (tasks.md): implementa el ``HierarchyService``, que ensambla el árbol
anidado completo de un Eje a lo largo de los cinco niveles confirmados
(Eje → Meta → Objetivo SMART → Indicador → Actividad). Pertenece a la capa de
servicios (``design.md`` "Architecture"): **reutiliza los repositorios** de cada
entidad y aplica reglas de aplicación, **sin conocer FastAPI ni HTTP**. Lanza
**excepciones de dominio** (``NotFoundError``); la traducción a HTTP corresponde
a la capa de rutas.

Comportamiento (Req 6.1–6.5):

- Si el Eje ``eje_id`` no existe, lanza ``NotFoundError`` (Req 6.5).
- Si existe, consulta sus Metas, los Objetivos de cada Meta, los Indicadores de
  cada Objetivo y las Actividades de cada Indicador, reutilizando los
  repositorios por padre (Req 6.1).
- Los nodos sin hijos exponen una colección vacía ``[]`` (Req 6.4).
- El Eje raíz **no** incluye referencia a un padre (Req 6.3); en el árbol las
  referencias hija→padre son implícitas por el anidamiento (Req 6.2), por lo que
  los nodos anidados no replican el ``*_id`` del padre.

Formato de salida (``TECHNICAL_DECISION`` de esta capa): se devuelve una
estructura anidada de diccionarios con los campos confirmados de cada nivel y la
lista de hijos del nivel inmediatamente inferior. Esta estructura es
independiente de framework; la capa de rutas (tarea 11.7) la serializa al
contrato ``EjeArbolResponse`` (``backend/src/schemas/arbol.py``). No se exponen
atributos PENDING_VALIDATION de Indicador ni de Actividad (Req 4.7, 5.8, 9).
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from backend.src.domain.exceptions import NotFoundError
from backend.src.repositories.actividad_repository import ActividadRepository
from backend.src.repositories.eje_repository import EjeRepository
from backend.src.repositories.indicador_repository import IndicadorRepository
from backend.src.repositories.meta_repository import MetaRepository
from backend.src.repositories.objetivo_repository import ObjetivoRepository


class HierarchyService:
    """Ensambla el árbol anidado de un Eje reutilizando los repositorios.

    Recibe una ``Session`` de SQLAlchemy y construye sobre ella un repositorio
    por nivel de la jerarquía. No gestiona el ciclo de vida de la sesión
    (corresponde a la capa superior).
    """

    def __init__(self, session: Session) -> None:
        self._session = session
        self._eje_repositorio = EjeRepository(session)
        self._meta_repositorio = MetaRepository(session)
        self._objetivo_repositorio = ObjetivoRepository(session)
        self._indicador_repositorio = IndicadorRepository(session)
        self._actividad_repositorio = ActividadRepository(session)

    def obtener_arbol(self, eje_id: int) -> dict[str, Any]:
        """Devuelve el árbol anidado de cinco niveles del Eje ``eje_id``.

        Req 6.1: ensambla Eje → Metas → Objetivos → Indicadores → Actividades.
        Req 6.4: cada nivel expone ``[]`` cuando no tiene hijos. Req 6.3: el Eje
        raíz no incluye referencia a un padre.

        :raises NotFoundError: si no existe ningún Eje con ese ``id`` (Req 6.5).
        """
        eje = self._eje_repositorio.obtener_por_id(eje_id)
        if eje is None:
            raise NotFoundError(f"No existe un Eje con id {eje_id}.")

        return {
            "id": eje.id,
            "nombre": eje.nombre,
            "descripcion": eje.descripcion,
            "metas": [self._construir_meta(meta) for meta in
                      self._meta_repositorio.listar_por_padre(eje_id)],
        }

    def _construir_meta(self, meta: Any) -> dict[str, Any]:
        """Construye el subárbol de una Meta con sus Objetivos anidados."""
        return {
            "id": meta.id,
            "descripcion": meta.descripcion,
            "objetivos": [
                self._construir_objetivo(objetivo)
                for objetivo in self._objetivo_repositorio.listar_por_padre(
                    meta.id
                )
            ],
        }

    def _construir_objetivo(self, objetivo: Any) -> dict[str, Any]:
        """Construye el subárbol de un Objetivo con sus Indicadores anidados."""
        return {
            "id": objetivo.id,
            "descripcion": objetivo.descripcion,
            "indicadores": [
                self._construir_indicador(indicador)
                for indicador in self._indicador_repositorio.listar_por_padre(
                    objetivo.id
                )
            ],
        }

    def _construir_indicador(self, indicador: Any) -> dict[str, Any]:
        """Construye el subárbol de un Indicador con sus Actividades anidadas.

        Solo incluye atributos confirmados (``nombre``, ``descripcion``); no se
        exponen atributos PENDING_VALIDATION (Req 4.7, 9.1).
        """
        return {
            "id": indicador.id,
            "nombre": indicador.nombre,
            "descripcion": indicador.descripcion,
            "actividades": [
                self._construir_actividad(actividad)
                for actividad in self._actividad_repositorio.listar_por_padre(
                    indicador.id
                )
            ],
        }

    def _construir_actividad(self, actividad: Any) -> dict[str, Any]:
        """Construye el nodo hoja de una Actividad.

        Solo incluye el atributo confirmado (``descripcion``); no se exponen
        atributos PENDING_VALIDATION (Req 5.8, 9.2).
        """
        return {
            "id": actividad.id,
            "descripcion": actividad.descripcion,
        }
