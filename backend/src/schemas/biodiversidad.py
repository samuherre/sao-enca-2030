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

    # Desglose taxonómico: top órdenes y top familias. Pueden venir vacíos en
    # cortes anteriores a esta funcionalidad.
    ordenes: list[TaxonGBIF] = []
    familias: list[TaxonGBIF] = []

    # Contexto del histórico y de las exportaciones disponibles.
    cortes_historicos: int = 0
    historico: list[CorteHistoricoGBIF] = []
    exportaciones: list[ArchivoExportacion] = []
