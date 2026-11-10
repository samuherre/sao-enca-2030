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
    """Conteo de artículos asignados a un OFC (clasificación automática).

    Incluye el Grado de Colaboración (GC) de Subramanyam (1983) del OFC:
    ``GC = 1 - f1/N`` sobre los artículos con autoría contable de forma fiable
    (ver servicio). ``grado_colaboracion`` es ``None`` cuando no hay artículos
    con autoría contable en el OFC (no se inventa un valor).
    """

    ofc_id: str
    nombre: str
    conteo: int
    # Grado de Colaboración (Subramanyam 1983), en [0, 1]; None si no hay base.
    grado_colaboracion: float | None = None
    # Artículos del OFC con autoría contable (N usado en el GC) y los excluidos
    # por no tener autoría contable de forma fiable (transparencia del alcance).
    gc_articulos_contables: int = 0
    gc_articulos_sin_autoria: int = 0


class DescripcionOFC(SchemaBase):
    """Ficha descriptiva pública de un OFC (número, nombre y definición).

    Proviene del catálogo oficial ENCA 2030; sirve para explicar al público del
    dashboard qué representa cada Objeto Focal de Conservación. No incluye los
    términos internos del clasificador.
    """

    ofc_id: str
    numero: int | None = None
    nombre: str
    definicion: str = ""


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
    # Distribución por revista: las revistas con más artículos y el resto bajo
    # "Otros" (reemplaza la antigua distribución por volumen en el consolidado).
    por_revista: list[ConteoPorClave]
    completitud: list[CompletitudCampo]
    pendientes_revision: int
    posibles_duplicados: int
    # Una fecha por fuente que tenga dataset fechado; vacío si ninguna la aporta.
    fechas_dataset: list[str]
    # Filtro por año de publicación. ``anios_disponibles`` SIEMPRE lista todos
    # los años presentes en el conjunto completo (para poblar el desplegable),
    # con independencia del filtro aplicado. ``anio_seleccionado`` es el año por
    # el que se filtró el resto del resumen, o ``None`` cuando el resumen abarca
    # todos los años ("Todos").
    anios_disponibles: list[int] = []
    anio_seleccionado: int | None = None
    # Clasificación por OFC (automática, sujeta a revisión).
    clasificacion_disponible: bool = False
    por_ofc: list[ConteoOFC] = []
    sin_ofc: int = 0
    # Explicación pública de los OFC (texto oficial ENCA + catálogo de los 11).
    # Permite que el dashboard explique qué son los OFC a cualquier visitante.
    ofc_descripcion: str = ""
    catalogo_ofc: list[DescripcionOFC] = []
    # Desglose del aporte de cada fuente al consolidado.
    aporte_por_fuente: list[AporteFuente] = []
