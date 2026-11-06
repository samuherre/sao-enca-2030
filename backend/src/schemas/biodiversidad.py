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

    # Contexto del histórico y de las exportaciones disponibles.
    cortes_historicos: int = 0
    historico: list[CorteHistoricoGBIF] = []
    exportaciones: list[ArchivoExportacion] = []
