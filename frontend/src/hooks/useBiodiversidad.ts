// Hooks de datos de la vista de biodiversidad (Datos de GBIF).
//
// - `useResumenGbif`: carga el resumen ALMACENADO (último corte en disco) con el
//   patrón común de `useAsyncData` (loading/data/error/reload).
// - `useConsultaGbifEnVivo`: dispara una consulta EN VIVO de forma imperativa
//   (al pulsar un botón), con su propio estado de carga/error. No se ejecuta al
//   montar: solo cuando el usuario lo pide.

import { useCallback, useEffect, useRef, useState } from "react";

import { ApiError, consultarGbifEnVivo, obtenerResumenGbif } from "../services";
import type { ResumenGBIF } from "../types";
import { useAsyncData, type AsyncDataState } from "./useAsyncData";

/** Carga el resumen del último corte GBIF almacenado en disco. */
export function useResumenGbif(): AsyncDataState<ResumenGBIF> {
  const loader = useCallback(
    ({ signal }: { signal: AbortSignal }) => obtenerResumenGbif({ signal }),
    [],
  );
  return useAsyncData<ResumenGBIF>(loader);
}

/** Estado y disparador de la consulta en vivo a GBIF. */
export interface ConsultaEnVivoState {
  /** `true` mientras la consulta en vivo está en curso. */
  readonly loading: boolean;
  /** Resultado de la última consulta en vivo exitosa, o `null`. */
  readonly data: ResumenGBIF | null;
  /** Error normalizado de la última consulta fallida, o `null`. */
  readonly error: ApiError | null;
  /** Dispara una nueva consulta en vivo a GBIF. */
  readonly consultar: () => void;
}

/**
 * Gestiona una consulta EN VIVO a GBIF disparada por el usuario.
 *
 * No consulta al montar: solo cuando se invoca `consultar()`. Cancela la
 * petición en curso al desmontar y evita actualizar el estado tras el desmontaje.
 */
export function useConsultaGbifEnVivo(): ConsultaEnVivoState {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<ResumenGBIF | null>(null);
  const [error, setError] = useState<ApiError | null>(null);

  // Controlador de la petición en curso, para poder cancelarla al desmontar o
  // al lanzar una nueva consulta antes de que termine la anterior.
  const controllerRef = useRef<AbortController | null>(null);
  const activeRef = useRef(true);

  useEffect(() => {
    activeRef.current = true;
    return () => {
      activeRef.current = false;
      controllerRef.current?.abort();
    };
  }, []);

  const consultar = useCallback(() => {
    // Cancela una consulta anterior aún en curso.
    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;

    setLoading(true);
    setError(null);

    consultarGbifEnVivo({ signal: controller.signal })
      .then((result) => {
        if (!activeRef.current || controller.signal.aborted) return;
        setData(result);
      })
      .catch((cause: unknown) => {
        if (!activeRef.current || controller.signal.aborted) return;
        setError(
          cause instanceof ApiError
            ? cause
            : new ApiError("network", "Ocurrió un error inesperado.", { cause }),
        );
      })
      .finally(() => {
        if (!activeRef.current || controller.signal.aborted) return;
        setLoading(false);
      });
  }, []);

  return { loading, data, error, consultar };
}
