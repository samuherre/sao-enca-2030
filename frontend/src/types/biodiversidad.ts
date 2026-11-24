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

/** Conteo de registros de aves de un departamento de Colombia (stateProvince). */
export interface DepartamentoGBIF {
  readonly rank: number;
  readonly departamento: string;
  readonly registros_ocurrencia: number;
}

/** Conteo de registros de aves por grupo taxonómico (orden o familia). */
export interface TaxonGBIF {
  readonly rank: number;
  readonly taxon_key: string;
  /** Nombre científico resuelto; `null` si GBIF no lo devolvió (no se inventa). */
  readonly nombre: string | null;
  readonly registros_ocurrencia: number;
}

/** Un punto (año, conteo) de la serie temporal de una especie. */
export interface SerieAnioGBIF {
  readonly anio: number;
  readonly registros_ocurrencia: number;
}

/** Registros por categoría de la Lista Roja de la UICN. */
export interface CategoriaIUCN {
  readonly rank: number;
  readonly codigo: string;
  readonly etiqueta: string;
  readonly registros_ocurrencia: number;
}

/** Especie amenazada (UICN) con su serie de registros por año. */
export interface EspecieAmenazada {
  readonly rank: number;
  readonly species_key: string;
  readonly nombre_cientifico: string | null;
  readonly nombre_comun: string | null;
  readonly iucn_codigo: string;
  readonly iucn_etiqueta: string;
  readonly registros_ocurrencia: number;
  readonly por_anio: readonly SerieAnioGBIF[];
}

/** Conteo de registros por tipo (basisOfRecord de GBIF). */
export interface TipoRegistroGBIF {
  readonly rank: number;
  /** Código del vocabulario de GBIF (p. ej. "HUMAN_OBSERVATION"). */
  readonly codigo: string;
  /** Etiqueta en español; si el código no está contemplado, es el propio código. */
  readonly etiqueta: string;
  readonly registros_ocurrencia: number;
}

/** Conteo de registros de aves por año de evento (serie temporal). */
export interface AnioGBIF {
  readonly anio: number;
  readonly registros_ocurrencia: number;
}

/** Conteo de registros de aves de un municipio de Colombia (GADM nivel 2). */
export interface MunicipioGBIF {
  readonly rank: number;
  /** Identificador GADM nivel 2 (p. ej. "COL.8.9_2"); llave de join en ArcGIS. */
  readonly gadm_gid: string;
  /** Nombre resuelto por GBIF; `null` si no se resolvió (no se inventa). */
  readonly nombre: string | null;
  readonly registros_ocurrencia: number;
}

/** Conteo de registros de aves agrupado por región ENCA (predominante). */
export interface RegionGBIF {
  readonly rank: number;
  readonly region: string;
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
  readonly departamentos: readonly DepartamentoGBIF[];
  readonly municipios: readonly MunicipioGBIF[];
  readonly anios: readonly AnioGBIF[];
  readonly tipos_registro: readonly TipoRegistroGBIF[];
  readonly iucn_categorias: readonly CategoriaIUCN[];
  readonly especies_amenazadas: readonly EspecieAmenazada[];
  readonly regiones: readonly RegionGBIF[];
  readonly ordenes: readonly TaxonGBIF[];
  readonly familias: readonly TaxonGBIF[];
  readonly especies: readonly TaxonGBIF[];

  readonly cortes_historicos: number;
  readonly historico: readonly CorteHistoricoGBIF[];
  readonly exportaciones: readonly ArchivoExportacion[];
}
