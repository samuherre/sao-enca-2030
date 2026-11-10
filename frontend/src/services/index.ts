// Punto de entrada de la capa de servicios del frontend (tarea 19.2).
//
// Reexporta el cliente API tipado, el modelo de error normalizado y la
// constante del timeout, para que las vistas y hooks importen desde
// `../services` sin conocer el archivo concreto.

export {
  // Ejes
  crearEje,
  listarEjes,
  obtenerEje,
  obtenerArbol,
  // Metas
  crearMeta,
  listarMetas,
  obtenerMeta,
  // Objetivos
  crearObjetivo,
  listarObjetivos,
  obtenerObjetivo,
  // Indicadores
  crearIndicador,
  listarIndicadores,
  obtenerIndicador,
  // Actividades
  crearActividad,
  listarActividades,
  obtenerActividad,
  // Bibliometría (Componente B)
  obtenerResumenBibliometrico,
  obtenerResumenConsolidado,
  obtenerArticulosDeOfc,
  urlDescargaConsolidadoCsv,
  urlDescargaArticulosOfcCsv,
  // Biodiversidad (Datos de GBIF)
  obtenerResumenGbif,
  consultarGbifEnVivo,
} from "./apiClient";

export { ApiError, type ApiErrorKind, type ApiErrorBody } from "./apiError";
export { REQUEST_TIMEOUT_MS } from "./http";
