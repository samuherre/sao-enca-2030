// Hook interno reutilizable para carga de datos asíncrona (tarea 19.3).
//
// Encapsula el patrón común de todos los hooks de datos: ejecutar una llamada a
// la API y exponer `loading`, `data` y `error`, además de permitir recargar.
// Cada petición se cancela al desmontar o al cambiar las dependencias, para
// evitar actualizaciones de estado sobre un componente ya desmontado.
//
// El `error` expuesto es siempre un `ApiError` (timeout / network / http), de
// modo que la UI pueda reaccionar sin inspeccionar códigos HTTP crudos (Req 7.7,
// 7.8, 7.9). `data` es `null` mientras no haya un resultado válido.

import { useCallback, useEffect, useState } from "react";

import { ApiError } from "../services";

/** Estado expuesto por los hooks de carga de datos. */
export interface AsyncDataState<T> {
  /** `true` mientras la petición está en curso (Req 7.7). */
  readonly loading: boolean;
  /** Datos cargados, o `null` si aún no hay resultado válido. */
  readonly data: T | null;
  /** Error normalizado de la última petición fallida, o `null`. */
  readonly error: ApiError | null;
  /** Relanza la petición manualmente (p. ej. tras crear una entidad). */
  readonly reload: () => void;
}

/**
 * Firma de la función de carga: recibe la señal de cancelación y devuelve los
 * datos. Debe aceptar `{ signal }` para integrarse con el cliente API.
 */
export type Loader<T> = (opts: { signal: AbortSignal }) => Promise<T>;

/**
 * Normaliza cualquier valor capturado a `ApiError`. El cliente API ya lanza
 * `ApiError`, pero esto protege ante fallos inesperados sin exponer detalles
 * técnicos a la UI (Req 7.9).
 */
function toApiError(cause: unknown): ApiError {
  if (cause instanceof ApiError) {
    return cause;
  }
  return new ApiError("network", "Ocurrió un error inesperado.", { cause });
}

/**
 * Ejecuta `loader` y gestiona el ciclo de vida de la petición.
 *
 * @typeParam T Tipo de los datos cargados.
 * @param loader Función de carga; debe ser estable (memoizada con `useCallback`
 *   por quien llama, usando sus propias dependencias como `ejeId`).
 * @param enabled Si es `false`, no se dispara la carga (útil cuando falta un id
 *   de padre). En ese caso el estado queda en reposo: `loading=false`,
 *   `data=null`, `error=null`.
 */
export function useAsyncData<T>(
  loader: Loader<T>,
  enabled: boolean = true,
): AsyncDataState<T> {
  const [loading, setLoading] = useState<boolean>(enabled);
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  // Contador para forzar recargas manuales a través de `reload()`.
  const [reloadToken, setReloadToken] = useState(0);

  const reload = useCallback(() => {
    setReloadToken((token) => token + 1);
  }, []);

  useEffect(() => {
    if (!enabled) {
      setLoading(false);
      setData(null);
      setError(null);
      return;
    }

    const controller = new AbortController();
    let active = true;

    setLoading(true);
    setError(null);

    loader({ signal: controller.signal })
      .then((result) => {
        if (!active) return;
        setData(result);
      })
      .catch((cause: unknown) => {
        if (!active || controller.signal.aborted) return;
        setError(toApiError(cause));
      })
      .finally(() => {
        if (!active) return;
        setLoading(false);
      });

    return () => {
      active = false;
      controller.abort();
    };
  }, [loader, enabled, reloadToken]);

  return { loading, data, error, reload };
}
