// Punto de entrada de los hooks de datos del frontend (tarea 19.3).
//
// Reexporta los hooks por nivel y el estado común, para que las vistas importen
// desde `../hooks` sin conocer el archivo concreto.

export {
  useEjes,
  useMetas,
  useObjetivos,
  useIndicadores,
  useActividades,
  useArbol,
} from "./useEntities";

export { useAsyncData, type AsyncDataState, type Loader } from "./useAsyncData";

export { useResumenBibliometrico, useResumenConsolidado } from "./useBibliometria";

export {
  useResumenGbif,
  useConsultaGbifEnVivo,
  type ConsultaEnVivoState,
} from "./useBiodiversidad";
