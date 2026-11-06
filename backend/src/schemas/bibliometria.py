"""Contratos Pydantic del dashboard bibliométrico (Componente B).

Estos schemas describen las agregaciones que el frontend consume para el
dashboard de la fuente Boletín SAO. El backend expone datos YA PROCESADOS
(leídos de ``data/processed/boletin_sao/``); no ejecuta el pipeline ni toca la
base de datos (steering bibliometrics.md §4.5, tech.md §12, structure.md §30).

Todos heredan de ``SchemaBase`` (``extra="forbid"``) por coherencia con el resto
de la API.
"""

from __future__ import annotations

from backend.src.schemas.base import SchemaBase


class ConteoPorClave(SchemaBase):
    """Par (clave, conteo) para distribuciones simples (p. ej. por año)."""

    clave: str
    conteo: int


class CompletitudCampo(SchemaBase):
    """Completitud de un campo del contrato: cuántos registros lo tienen."""

    campo: str
    con_dato: int
    total: int


class ConteoOFC(SchemaBase):
    """Conteo de artículos asignados a un OFC (clasificación automática)."""

    ofc_id: str
    nombre: str
    conteo: int


class ResumenBibliometrico(SchemaBase):
    """Resumen agregado del dataset de la fuente Boletín SAO.

    Representa SOLO lo que el dataset procesado/clasificado contiene; no infiere
    ni inventa valores.

    La clasificación por OFC es AUTOMÁTICA (reglas-keywords-v1, ADR-010) y está
    sujeta a revisión humana: ``clasificacion_disponible`` indica si existe un
    dataset clasificado; ``por_ofc`` trae la distribución cuando lo hay.
    """

    fuente: str
    total_articulos: int
    por_anio: list[ConteoPorClave]
    por_volumen: list[ConteoPorClave]
    completitud: list[CompletitudCampo]
    pendientes_revision: int
    posibles_duplicados: int
    fecha_dataset: str | None
    # Clasificación por OFC (automática, sujeta a revisión).
    clasificacion_disponible: bool = False
    por_ofc: list[ConteoOFC] = []
    sin_ofc: int = 0


class AporteFuente(SchemaBase):
    """Aporte de una fuente concreta al resumen consolidado.

    Permite desglosar, por cada fuente descubierta bajo ``data/processed/``,
    cuántos artículos aporta al total y con qué completitud de campos, sin
    deduplicación entre fuentes (unión por inclusión). Reutiliza
    :class:`CompletitudCampo` para describir la completitud por campo.
    """

    fuente: str
    total_articulos: int
    completitud: list[CompletitudCampo]


class ResumenConsolidado(SchemaBase):
    """Resumen agregado de TODAS las fuentes procesadas (análisis consolidado).

    Generaliza :class:`ResumenBibliometrico` al conjunto de fuentes descubiertas
    bajo ``data/processed/``. El total es la suma por fuente (unión sin
    exclusión; sin deduplicación entre fuentes). Expone SOLO lo que los datasets
    procesados/clasificados contienen; no infiere ni inventa valores.

    ``alcance = "consolidado"`` es un identificador explícito del alcance del
    resumen (Req 6.4), que lo distingue del resumen de una sola fuente.

    La clasificación por OFC es AUTOMÁTICA (reglas-keywords-v1, ADR-010) y está
    sujeta a revisión humana: ``clasificacion_disponible`` indica si existe algún
    dataset clasificado; ``por_ofc`` trae la distribución agregada cuando lo hay.
    Los datasets ``*_clasificado`` aportan solo ``por_ofc`` y no cuentan al total.
    """

    alcance: str = "consolidado"
    total_articulos: int
    por_anio: list[ConteoPorClave]
    por_volumen: list[ConteoPorClave]
    completitud: list[CompletitudCampo]
    pendientes_revision: int
    posibles_duplicados: int
    # Una fecha por fuente que tenga dataset fechado; vacío si ninguna la aporta.
    fechas_dataset: list[str]
    # Clasificación por OFC (automática, sujeta a revisión).
    clasificacion_disponible: bool = False
    por_ofc: list[ConteoOFC] = []
    sin_ofc: int = 0
    # Desglose del aporte de cada fuente al consolidado.
    aporte_por_fuente: list[AporteFuente] = []
