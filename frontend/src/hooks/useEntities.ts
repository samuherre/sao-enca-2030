// Hooks de carga de datos por nivel de la jerarquía (tarea 19.3).
//
// Un hook por colección y uno para el árbol completo. Cada hook encapsula la
// llamada al cliente API y expone `loading`, `data` y `error` por nivel
// (Req 7.1, 7.3, 7.7), reutilizando `useAsyncData`.
//
// Convenciones:
//   - Los hooks de colecciones de hijos reciben el id del padre. Si el id es
//     `null`/`undefined`, el hook queda deshabilitado (no dispara la petición)
//     y expone `data=null`, `loading=false`, `error=null`.
//   - El estado de "colección vacía" se representa con `data = []` (no es un
//     error): la UI lo distingue de `data = null` (aún sin cargar).
//   - El `loader` se memoiza con `useCallback` sobre el id del padre, de modo
//     que la petición se repita automáticamente al cambiar de padre.

import { useCallback } from "react";

import {
  listarActividades,
  listarEjes,
  listarIndicadores,
  listarMetas,
  listarObjetivos,
  obtenerArbol,
} from "../services";
import type {
  Actividad,
  Eje,
  EjeArbol,
  Indicador,
  Meta,
  Objetivo,
} from "../types";
import { useAsyncData, type AsyncDataState } from "./useAsyncData";

/** Id de padre opcional: `null`/`undefined` deshabilita el hook. */
type ParentId = number | null | undefined;

/** Carga la lista completa de Ejes (vista inicial, Req 7.1). */
export function useEjes(): AsyncDataState<Eje[]> {
  const loader = useCallback(
    ({ signal }: { signal: AbortSignal }) => listarEjes({ signal }),
    [],
  );
  return useAsyncData<Eje[]>(loader);
}

/** Carga las Metas de un Eje. Deshabilitado si `ejeId` es nulo (Req 7.3). */
export function useMetas(ejeId: ParentId): AsyncDataState<Meta[]> {
  const enabled = ejeId != null;
  const loader = useCallback(
    ({ signal }: { signal: AbortSignal }) => listarMetas(ejeId as number, { signal }),
    [ejeId],
  );
  return useAsyncData<Meta[]>(loader, enabled);
}

/** Carga los Objetivos de una Meta. Deshabilitado si `metaId` es nulo (Req 7.3). */
export function useObjetivos(metaId: ParentId): AsyncDataState<Objetivo[]> {
  const enabled = metaId != null;
  const loader = useCallback(
    ({ signal }: { signal: AbortSignal }) =>
      listarObjetivos(metaId as number, { signal }),
    [metaId],
  );
  return useAsyncData<Objetivo[]>(loader, enabled);
}

/** Carga los Indicadores de un Objetivo. Deshabilitado si `objetivoId` es nulo (Req 7.3). */
export function useIndicadores(objetivoId: ParentId): AsyncDataState<Indicador[]> {
  const enabled = objetivoId != null;
  const loader = useCallback(
    ({ signal }: { signal: AbortSignal }) =>
      listarIndicadores(objetivoId as number, { signal }),
    [objetivoId],
  );
  return useAsyncData<Indicador[]>(loader, enabled);
}

/** Carga las Actividades de un Indicador. Deshabilitado si `indicadorId` es nulo (Req 7.3). */
export function useActividades(indicadorId: ParentId): AsyncDataState<Actividad[]> {
  const enabled = indicadorId != null;
  const loader = useCallback(
    ({ signal }: { signal: AbortSignal }) =>
      listarActividades(indicadorId as number, { signal }),
    [indicadorId],
  );
  return useAsyncData<Actividad[]>(loader, enabled);
}

/**
 * Carga el árbol anidado completo de un Eje (`GET /ejes/{id}/arbol`).
 * Deshabilitado si `ejeId` es nulo. El Eje inexistente propaga un `ApiError`
 * 404 en el estado `error`.
 */
export function useArbol(ejeId: ParentId): AsyncDataState<EjeArbol> {
  const enabled = ejeId != null;
  const loader = useCallback(
    ({ signal }: { signal: AbortSignal }) => obtenerArbol(ejeId as number, { signal }),
    [ejeId],
  );
  return useAsyncData<EjeArbol>(loader, enabled);
}
