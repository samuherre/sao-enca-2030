// Hook de datos del dashboard bibliométrico (Componente B).
//
// Carga el resumen agregado de la fuente Boletín SAO a través del cliente API,
// reutilizando `useAsyncData` para `loading`/`data`/`error`/`reload`.

import { useCallback } from "react";

import { obtenerResumenBibliometrico, obtenerResumenConsolidado } from "../services";
import type { ResumenBibliometrico, ResumenConsolidado } from "../types";
import { useAsyncData, type AsyncDataState } from "./useAsyncData";

/** Carga el resumen bibliométrico de la fuente Boletín SAO. */
export function useResumenBibliometrico(): AsyncDataState<ResumenBibliometrico> {
  const loader = useCallback(
    ({ signal }: { signal: AbortSignal }) => obtenerResumenBibliometrico({ signal }),
    [],
  );
  return useAsyncData<ResumenBibliometrico>(loader);
}

/** Carga el resumen CONSOLIDADO de todas las fuentes procesadas. */
export function useResumenConsolidado(): AsyncDataState<ResumenConsolidado> {
  const loader = useCallback(
    ({ signal }: { signal: AbortSignal }) => obtenerResumenConsolidado({ signal }),
    [],
  );
  return useAsyncData<ResumenConsolidado>(loader);
}
