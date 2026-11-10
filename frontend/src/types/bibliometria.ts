// Tipos del dashboard bibliométrico (Componente B).
//
// Reflejan exactamente los schemas de respuesta del backend
// (`backend/src/schemas/bibliometria.py`). El backend expone datos YA
// PROCESADOS de la fuente Boletín SAO; no incluye clasificación OFC
// (PENDING_VALIDATION).

/** Par (clave, conteo) para distribuciones simples (p. ej. por año). */
export interface ConteoPorClave {
  readonly clave: string;
  readonly conteo: number;
}

/** Completitud de un campo del contrato: cuántos registros lo tienen. */
export interface CompletitudCampo {
  readonly campo: string;
  readonly con_dato: number;
  readonly total: number;
}

/** Conteo de artículos por OFC (clasificación automática). */
export interface ConteoOFC {
  readonly ofc_id: string;
  readonly nombre: string;
  readonly conteo: number;
}

/** Ficha descriptiva pública de un OFC (catálogo oficial ENCA 2030). */
export interface DescripcionOFC {
  readonly ofc_id: string;
  readonly numero: number | null;
  readonly nombre: string;
  readonly definicion: string;
}

/** Resumen agregado del dataset de la fuente Boletín SAO. */
export interface ResumenBibliometrico {
  readonly fuente: string;
  readonly total_articulos: number;
  readonly por_anio: readonly ConteoPorClave[];
  readonly por_volumen: readonly ConteoPorClave[];
  readonly completitud: readonly CompletitudCampo[];
  readonly pendientes_revision: number;
  readonly posibles_duplicados: number;
  readonly fecha_dataset: string | null;
  readonly clasificacion_disponible: boolean;
  readonly por_ofc: readonly ConteoOFC[];
  readonly sin_ofc: number;
}

/** Aporte de una fuente individual al resumen consolidado. */
export interface AporteFuente {
  readonly fuente: string;
  readonly total_articulos: number;
  readonly completitud: readonly CompletitudCampo[];
}

/**
 * Resumen agregado de TODAS las fuentes bajo `data/processed/`
 * (unión sin exclusión, sin deduplicación entre fuentes).
 */
export interface ResumenConsolidado {
  readonly alcance: string;
  readonly total_articulos: number;
  readonly por_anio: readonly ConteoPorClave[];
  readonly por_volumen: readonly ConteoPorClave[];
  readonly completitud: readonly CompletitudCampo[];
  readonly pendientes_revision: number;
  readonly posibles_duplicados: number;
  readonly fechas_dataset: readonly string[];
  // Años disponibles para el desplegable (siempre el conjunto completo) y el
  // año por el que se filtró el resumen (null = "Todos").
  readonly anios_disponibles: readonly number[];
  readonly anio_seleccionado: number | null;
  readonly clasificacion_disponible: boolean;
  readonly por_ofc: readonly ConteoOFC[];
  readonly sin_ofc: number;
  // Explicación pública de los OFC (texto oficial ENCA + catálogo de los 11).
  readonly ofc_descripcion: string;
  readonly catalogo_ofc: readonly DescripcionOFC[];
  readonly aporte_por_fuente: readonly AporteFuente[];
}
