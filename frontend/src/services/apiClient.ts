// Cliente API tipado (tarea 19.2).
//
// Expone una función por endpoint del backend, agrupadas por entidad, conforme a
// `design.md` ("Endpoints de la API"). Solo implementa CREAR y CONSULTAR
// (individual y por colección) y la navegación del árbol; no hay update/delete.
//
// Toda la comunicación pasa por `request()` (`http.ts`), que aplica el timeout
// de 30 s y normaliza los fallos a `ApiError`. Los tipos de entrada/salida
// provienen de `../types` y reflejan los contratos del backend.
//
// Mapa de rutas (design.md "Endpoints de la API"):
//   Ejes:        POST /ejes · GET /ejes · GET /ejes/{id}
//   Metas:       POST /ejes/{eje_id}/metas · GET /ejes/{eje_id}/metas · GET /metas/{id}
//   Objetivos:   POST /metas/{meta_id}/objetivos · GET /metas/{meta_id}/objetivos · GET /objetivos/{id}
//   Indicadores: POST /objetivos/{objetivo_id}/indicadores · GET /objetivos/{objetivo_id}/indicadores · GET /indicadores/{id}
//   Actividades: POST /indicadores/{indicador_id}/actividades · GET /indicadores/{indicador_id}/actividades · GET /actividades/{id}
//   Árbol:       GET /ejes/{eje_id}/arbol

import type {
  Actividad,
  ActividadCreate,
  Eje,
  EjeArbol,
  EjeCreate,
  Indicador,
  IndicadorCreate,
  Meta,
  MetaCreate,
  Objetivo,
  ObjetivoCreate,
  ResumenBibliometrico,
  ResumenConsolidado,
  ResumenGBIF,
} from "../types";
import { request } from "./http";

/** Opciones comunes de solo lectura para cualquier operación del cliente. */
interface CallOptions {
  /** Señal externa para cancelar la petición (p. ej. al desmontar un componente). */
  readonly signal?: AbortSignal;
}

// --- Ejes -------------------------------------------------------------------

/** Crea un Eje. `POST /ejes` → 201. */
export function crearEje(datos: EjeCreate, opts: CallOptions = {}): Promise<Eje> {
  return request<Eje>("/ejes", { method: "POST", body: datos, signal: opts.signal });
}

/** Lista todos los Ejes. `GET /ejes` → 200 (puede ser `[]`). */
export function listarEjes(opts: CallOptions = {}): Promise<Eje[]> {
  return request<Eje[]>("/ejes", { signal: opts.signal });
}

/** Obtiene un Eje por id. `GET /ejes/{id}` → 200 | 404. */
export function obtenerEje(id: number, opts: CallOptions = {}): Promise<Eje> {
  return request<Eje>(`/ejes/${id}`, { signal: opts.signal });
}

/** Obtiene el árbol anidado completo de un Eje. `GET /ejes/{id}/arbol` → 200 | 404. */
export function obtenerArbol(ejeId: number, opts: CallOptions = {}): Promise<EjeArbol> {
  return request<EjeArbol>(`/ejes/${ejeId}/arbol`, { signal: opts.signal });
}

// --- Metas ------------------------------------------------------------------

/** Crea una Meta bajo un Eje. `POST /ejes/{eje_id}/metas` → 201 | 404 | 422. */
export function crearMeta(
  ejeId: number,
  datos: MetaCreate,
  opts: CallOptions = {},
): Promise<Meta> {
  return request<Meta>(`/ejes/${ejeId}/metas`, {
    method: "POST",
    body: datos,
    signal: opts.signal,
  });
}

/** Lista las Metas de un Eje. `GET /ejes/{eje_id}/metas` → 200 (puede ser `[]`) | 404. */
export function listarMetas(ejeId: number, opts: CallOptions = {}): Promise<Meta[]> {
  return request<Meta[]>(`/ejes/${ejeId}/metas`, { signal: opts.signal });
}

/** Obtiene una Meta por id. `GET /metas/{id}` → 200 | 404. */
export function obtenerMeta(id: number, opts: CallOptions = {}): Promise<Meta> {
  return request<Meta>(`/metas/${id}`, { signal: opts.signal });
}

// --- Objetivos SMART --------------------------------------------------------

/** Crea un Objetivo bajo una Meta. `POST /metas/{meta_id}/objetivos` → 201 | 404 | 422. */
export function crearObjetivo(
  metaId: number,
  datos: ObjetivoCreate,
  opts: CallOptions = {},
): Promise<Objetivo> {
  return request<Objetivo>(`/metas/${metaId}/objetivos`, {
    method: "POST",
    body: datos,
    signal: opts.signal,
  });
}

/** Lista los Objetivos de una Meta. `GET /metas/{meta_id}/objetivos` → 200 (puede ser `[]`) | 404. */
export function listarObjetivos(
  metaId: number,
  opts: CallOptions = {},
): Promise<Objetivo[]> {
  return request<Objetivo[]>(`/metas/${metaId}/objetivos`, { signal: opts.signal });
}

/** Obtiene un Objetivo por id. `GET /objetivos/{id}` → 200 | 404. */
export function obtenerObjetivo(id: number, opts: CallOptions = {}): Promise<Objetivo> {
  return request<Objetivo>(`/objetivos/${id}`, { signal: opts.signal });
}

// --- Indicadores ------------------------------------------------------------

/** Crea un Indicador bajo un Objetivo. `POST /objetivos/{objetivo_id}/indicadores` → 201 | 404 | 422. */
export function crearIndicador(
  objetivoId: number,
  datos: IndicadorCreate,
  opts: CallOptions = {},
): Promise<Indicador> {
  return request<Indicador>(`/objetivos/${objetivoId}/indicadores`, {
    method: "POST",
    body: datos,
    signal: opts.signal,
  });
}

/** Lista los Indicadores de un Objetivo. `GET /objetivos/{objetivo_id}/indicadores` → 200 (puede ser `[]`) | 404. */
export function listarIndicadores(
  objetivoId: number,
  opts: CallOptions = {},
): Promise<Indicador[]> {
  return request<Indicador[]>(`/objetivos/${objetivoId}/indicadores`, {
    signal: opts.signal,
  });
}

/** Obtiene un Indicador por id. `GET /indicadores/{id}` → 200 | 404. */
export function obtenerIndicador(id: number, opts: CallOptions = {}): Promise<Indicador> {
  return request<Indicador>(`/indicadores/${id}`, { signal: opts.signal });
}

// --- Actividades ------------------------------------------------------------

/** Crea una Actividad bajo un Indicador. `POST /indicadores/{indicador_id}/actividades` → 201 | 404 | 422. */
export function crearActividad(
  indicadorId: number,
  datos: ActividadCreate,
  opts: CallOptions = {},
): Promise<Actividad> {
  return request<Actividad>(`/indicadores/${indicadorId}/actividades`, {
    method: "POST",
    body: datos,
    signal: opts.signal,
  });
}

/** Lista las Actividades de un Indicador. `GET /indicadores/{indicador_id}/actividades` → 200 (puede ser `[]`) | 404. */
export function listarActividades(
  indicadorId: number,
  opts: CallOptions = {},
): Promise<Actividad[]> {
  return request<Actividad[]>(`/indicadores/${indicadorId}/actividades`, {
    signal: opts.signal,
  });
}

/** Obtiene una Actividad por id. `GET /actividades/{id}` → 200 | 404. */
export function obtenerActividad(id: number, opts: CallOptions = {}): Promise<Actividad> {
  return request<Actividad>(`/actividades/${id}`, { signal: opts.signal });
}

// --- Bibliometría (Componente B) --------------------------------------------

/**
 * Obtiene el resumen agregado de la fuente Boletín SAO.
 * `GET /bibliometria/boletin-sao/resumen` → 200 | 404 (si no hay dataset).
 */
export function obtenerResumenBibliometrico(
  opts: CallOptions = {},
): Promise<ResumenBibliometrico> {
  return request<ResumenBibliometrico>("/bibliometria/boletin-sao/resumen", {
    signal: opts.signal,
  });
}

/**
 * Obtiene el resumen CONSOLIDADO de todas las fuentes procesadas
 * (unión sin exclusión, sin deduplicación entre fuentes).
 * `GET /bibliometria/resumen` → 200 | 404 (si no hay datasets).
 */
export function obtenerResumenConsolidado(
  opts: CallOptions = {},
): Promise<ResumenConsolidado> {
  return request<ResumenConsolidado>("/bibliometria/resumen", {
    signal: opts.signal,
  });
}

// --- Biodiversidad (Datos de GBIF) ------------------------------------------

/**
 * Obtiene el resumen del último corte GBIF ALMACENADO en disco.
 * `GET /biodiversidad/gbif/resumen` → 200 | 404 (si no hay artefactos).
 */
export function obtenerResumenGbif(opts: CallOptions = {}): Promise<ResumenGBIF> {
  return request<ResumenGBIF>("/biodiversidad/gbif/resumen", {
    signal: opts.signal,
  });
}

/**
 * Dispara una consulta EN VIVO a GBIF (no persiste archivos).
 * `POST /biodiversidad/gbif/consultar` → 200 | 422 (si GBIF no devolvió cifras).
 */
export function consultarGbifEnVivo(opts: CallOptions = {}): Promise<ResumenGBIF> {
  return request<ResumenGBIF>("/biodiversidad/gbif/consultar", {
    method: "POST",
    signal: opts.signal,
  });
}
