// Punto de entrada de los tipos del dominio del frontend (tarea 19.1).
//
// Reexporta los contratos de la API (entidades confirmadas), los nodos del
// árbol jerárquico y las cargas útiles de creación. Permite importar desde
// `@/types` (o rutas relativas) sin conocer el archivo concreto.

export type {
  Eje,
  Meta,
  Objetivo,
  Indicador,
  Actividad,
} from "./entities";

export type {
  EjeArbol,
  MetaArbol,
  ObjetivoArbol,
  IndicadorArbol,
  ActividadArbol,
} from "./tree";

export type {
  EjeCreate,
  MetaCreate,
  ObjetivoCreate,
  IndicadorCreate,
  ActividadCreate,
} from "./payloads";

export type {
  ConteoPorClave,
  CompletitudCampo,
  ConteoOFC,
  ResumenBibliometrico,
  AporteFuente,
  ResumenConsolidado,
} from "./bibliometria";

export type {
  PublicadorGBIF,
  CorteHistoricoGBIF,
  ArchivoExportacion,
  OrigenGBIF,
  ResumenGBIF,
} from "./biodiversidad";
