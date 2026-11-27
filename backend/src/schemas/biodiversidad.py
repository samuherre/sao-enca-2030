"""Contratos Pydantic de la vista de biodiversidad — Datos de GBIF.

Estos schemas describen lo que el frontend consume para la sección
"Biodiversidad → Datos de GBIF". El backend expone datos obtenidos del piloto
GBIF (``scripts/biodiversity_pilot/``):

- Lectura de los ARTEFACTOS YA GENERADOS en ``outputs/biodiversity_pilot/gbif/``
  (resultado almacenado del último corte).
- Opcionalmente, una consulta EN VIVO que reutiliza ``gbif_bird_counts.run`` sin
  escribir archivos (no corrompe el histórico ni mezcla cortes).

Principios aplicados (product.md §15 no invención, tech.md §12 bibliometría
desacoplada, §32 manejo de errores):
- Los valores reflejan SOLO lo que los artefactos/consulta contienen. Un dato
  ausente viaja como ``None`` (no se inventa ni se sustituye por 0).
- Un registro de GBIF es una OCURRENCIA en la fuente, no un individuo ni una
  especie única: el contrato lo nombra explícitamente (``total_registros_ocurrencia``).

Todos heredan de ``SchemaBase`` (``extra="forbid"``) por coherencia con el resto
de la API.
"""

from __future__ import annotations

from backend.src.schemas.base import SchemaBase


class PublicadorGBIF(SchemaBase):
    """Un publicador del ranking: organización que aporta registros a GBIF.

    ``org_key`` es el identificador estable (orgKey de GBIF). ``nombre`` es el
    título resuelto; puede ser ``None`` si GBIF no lo devolvió (no se inventa).
    """

    rank: int
    org_key: str
    nombre: str | None
    registros_ocurrencia: int


class DepartamentoGBIF(SchemaBase):
    """Conteo de registros de aves de un departamento de Colombia.

    El nombre procede del campo ``stateProvince`` de GBIF (texto libre), ya
    canonizado para unir variantes del mismo departamento. Los registros sin
    departamento no se cuentan aquí, de modo que la suma por departamento puede
    ser inferior al total nacional (no se inventa una asignación).
    """

    rank: int
    departamento: str
    registros_ocurrencia: int


class TaxonGBIF(SchemaBase):
    """Conteo de registros de aves por grupo taxonómico (orden o familia).

    ``taxon_key`` es la clave del backbone de GBIF. ``nombre`` es el nombre
    científico resuelto (canonicalName); puede ser ``None`` si GBIF no lo
    devolvió (no se inventa).
    """

    rank: int
    taxon_key: str
    nombre: str | None
    registros_ocurrencia: int


class SerieAnioGBIF(SchemaBase):
    """Un punto (año, conteo) de la serie temporal de una especie."""

    anio: int
    registros_ocurrencia: int


class CategoriaIUCN(SchemaBase):
    """Registros por categoría de la Lista Roja de la UICN.

    ``codigo`` es el valor de GBIF (p. ej. ``VU``); ``etiqueta`` su traducción.
    """

    rank: int
    codigo: str
    etiqueta: str
    registros_ocurrencia: int


class EspecieAmenazada(SchemaBase):
    """Especie de ave amenazada (UICN CR/EN/VU) con su serie de registros/año.

    ``species_key`` es la clave del backbone de GBIF. Los nombres pueden ser
    ``None`` si GBIF no los devolvió (no se inventan). ``por_anio`` es la serie
    temporal de esa especie, para el selector "registros por especie por año".
    """

    rank: int
    species_key: str
    # Clave del taxón en el backbone ACTUAL del portal web de GBIF (Catalogue of
    # Life Extended Release), alfanumérica y corta (p. ej. "6YJKF"). Es la que el
    # enlace del portal usa como taxonKey; las claves numéricas del backbone
    # antiguo (species_key) el portal nuevo no las reconoce. None si GBIF no
    # resolvió el nombre (no se inventa).
    gbif_portal_key: str | None = None
    nombre_cientifico: str | None
    nombre_comun: str | None
    iucn_codigo: str
    iucn_etiqueta: str
    registros_ocurrencia: int
    por_anio: list[SerieAnioGBIF] = []
    # True si la especie es endémica de Colombia según el listado oficial CCRO
    # (cruce por nombre científico). False si no lo es o no se pudo cruzar; el
    # endemismo no se infiere (se toma solo de la lista oficial).
    endemica: bool = False


class TipoRegistroGBIF(SchemaBase):
    """Conteo de registros por TIPO (basisOfRecord de GBIF).

    ``codigo`` es el valor del vocabulario controlado de GBIF (p. ej.
    ``HUMAN_OBSERVATION``); ``etiqueta`` es su traducción a español. Ninguno se
    inventa: si GBIF trae un código no contemplado, la etiqueta es el propio
    código.
    """

    rank: int
    codigo: str
    etiqueta: str
    registros_ocurrencia: int


class AnioGBIF(SchemaBase):
    """Conteo de registros de aves por año de evento (serie temporal).

    El año es el año de EVENTO del registro en GBIF (cuándo se observó/recolectó
    la ocurrencia), no la fecha de extracción. Los registros sin año no se
    cuentan aquí.
    """

    anio: int
    registros_ocurrencia: int


class MunicipioGBIF(SchemaBase):
    """Conteo de registros de aves de un municipio de Colombia.

    ``gadm_gid`` es el identificador GADM de nivel 2 (p. ej. ``COL.8.9_2``), que
    sirve como llave para unir con una capa de municipios en ArcGIS. ``nombre``
    es el nombre resuelto por GBIF; puede ser ``None`` si no se resolvió (no se
    inventa). Los registros sin municipio no se cuentan aquí.
    """

    rank: int
    gadm_gid: str
    nombre: str | None
    registros_ocurrencia: int


class RiquezaDepartamentoGBIF(SchemaBase):
    """Riqueza de especies: nº de especies de aves DISTINTAS por departamento.

    A diferencia de ``DepartamentoGBIF`` (que cuenta registros de ocurrencia),
    aquí ``especies`` es cuántas especies distintas tienen al menos un registro
    en ese departamento (unión de especies sobre las variantes del nombre).
    """

    rank: int
    departamento: str
    especies: int


class RegionGBIF(SchemaBase):
    """Conteo de registros de aves agrupado por región geográfica de la ENCA.

    La región se obtiene agregando los departamentos según su región ENCA
    PREDOMINANTE. Es una propuesta del equipo (una región por departamento),
    pendiente de confirmación por SAO; no es un mapeo oficial. Los departamentos
    sin región asignada no se cuentan aquí (no se inventa su pertenencia).
    """

    rank: int
    region: str
    registros_ocurrencia: int


class CorteHistoricoGBIF(SchemaBase):
    """Un corte del histórico de cifras agregadas (snapshot con su fecha).

    Representa una ejecución registrada en el histórico consolidado. La fecha es
    la de EXTRACCIÓN (cuándo se consultó GBIF), NO la fecha de observación
    biológica de las aves.
    """

    extraido_utc: str
    fecha: str | None
    estado: str
    total_registros_ocurrencia: int | None
    publicadores_en_ranking: int | None


class ArchivoExportacion(SchemaBase):
    """Metadatos de un CSV de exportación disponible en disco (para ArcGIS)."""

    nombre: str
    ruta_relativa: str
    filas: int
    modificado_utc: str


class ResumenGBIF(SchemaBase):
    """Resumen de la última consulta de cifras de aves de GBIF (almacenada).

    ``origen`` distingue el modo de obtención del dato:
    - ``"almacenado"``: leído de los artefactos del último corte en disco.
    - ``"en_vivo"``: calculado ahora mismo consultando GBIF (sin persistir).

    Si no existe ningún artefacto todavía, el servicio lanza ``NotFoundError``;
    aquí no se representa el caso vacío con ceros inventados.
    """

    # Identificación de la fuente y el alcance (constantes del piloto).
    fuente: str
    fuente_url: str
    grupo_taxonomico: str
    cobertura_geografica: str
    alcance: str

    # Trazabilidad / estado de los datos.
    origen: str  # "almacenado" | "en_vivo"
    extraido_utc: str | None
    finalizado_utc: str | None
    estado: str  # "completed" | "completed_with_errors" | ...
    errores: list[str] = []
    nota: str | None = None

    # Cifras (registros de OCURRENCIA, no individuos ni especies únicas).
    total_registros_ocurrencia: int | None
    publicadores: list[PublicadorGBIF] = []

    # Desglose por departamento (campo stateProvince de GBIF, canonizado). Puede
    # venir vacío si el corte almacenado es anterior a esta funcionalidad.
    departamentos: list[DepartamentoGBIF] = []
    # Riqueza de especies (nº de especies distintas) por departamento. Puede
    # venir vacía en cortes anteriores a esta funcionalidad.
    riqueza_departamentos: list[RiquezaDepartamentoGBIF] = []

    # Agrupación por región ENCA (predominante). Propuesta del equipo, pendiente
    # de confirmación por SAO. Puede venir vacía en cortes antiguos.
    regiones: list[RegionGBIF] = []

    # Top municipios (GADM nivel 2). Puede venir vacío en cortes antiguos.
    municipios: list[MunicipioGBIF] = []

    # Serie temporal: registros por año de evento. Puede venir vacía en cortes
    # anteriores a esta funcionalidad.
    anios: list[AnioGBIF] = []

    # Registros por tipo (basisOfRecord). Puede venir vacío en cortes antiguos.
    tipos_registro: list[TipoRegistroGBIF] = []

    # Módulo de amenazadas: categorías UICN + especies amenazadas con serie anual.
    # Pueden venir vacíos en cortes anteriores a esta funcionalidad.
    iucn_categorias: list[CategoriaIUCN] = []
    especies_amenazadas: list[EspecieAmenazada] = []

    # Desglose taxonómico: órdenes, familias y especies. Pueden venir vacíos en
    # cortes anteriores a esta funcionalidad. ``especies`` es la lista completa
    # (todas las especies con registros) para el buscador del dashboard.
    ordenes: list[TaxonGBIF] = []
    familias: list[TaxonGBIF] = []
    especies: list[TaxonGBIF] = []

    # Contexto del histórico y de las exportaciones disponibles.
    cortes_historicos: int = 0
    historico: list[CorteHistoricoGBIF] = []
    exportaciones: list[ArchivoExportacion] = []
