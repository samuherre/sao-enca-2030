// Tipos de la vista de biodiversidad — Datos de GBIF.
//
// Reflejan exactamente los schemas de respuesta del backend
// (`backend/src/schemas/biodiversidad.py`). Las cifras son registros de
// OCURRENCIA en GBIF, no individuos ni especies únicas.

/** Un publicador del ranking: organización que aporta registros a GBIF. */
export interface PublicadorGBIF {
  readonly rank: number;
  readonly org_key: string;
  /** Título resuelto; `null` si GBIF no lo devolvió (no se inventa). */
  readonly nombre: string | null;
  readonly registros_ocurrencia: number;
}

/** Un corte del histórico de cifras agregadas (snapshot con su fecha). */
export interface CorteHistoricoGBIF {
  readonly extraido_utc: string;
  readonly fecha: string | null;
  readonly estado: string;
  readonly total_registros_ocurrencia: number | null;
  readonly publicadores_en_ranking: number | null;
}

/** Metadatos de un CSV de exportación disponible en disco (para ArcGIS). */
export interface ArchivoExportacion {
  readonly nombre: string;
  readonly ruta_relativa: string;
  readonly filas: number;
  readonly modificado_utc: string;
}

/** Origen del dato mostrado: artefacto almacenado o consulta en vivo. */
export type OrigenGBIF = "almacenado" | "en_vivo";

/** Resumen de cifras de aves de GBIF (almacenado o en vivo). */
export interface ResumenGBIF {
  readonly fuente: string;
  readonly fuente_url: string;
  readonly grupo_taxonomico: string;
  readonly cobertura_geografica: string;
  readonly alcance: string;

  readonly origen: OrigenGBIF;
  readonly extraido_utc: string | null;
  readonly finalizado_utc: string | null;
  readonly estado: string;
  readonly errores: readonly string[];
  readonly nota: string | null;

  readonly total_registros_ocurrencia: number | null;
  readonly publicadores: readonly PublicadorGBIF[];

  readonly cortes_historicos: number;
  readonly historico: readonly CorteHistoricoGBIF[];
  readonly exportaciones: readonly ArchivoExportacion[];
}
