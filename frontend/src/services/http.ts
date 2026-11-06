// Capa HTTP de bajo nivel con timeout de 30 s (tarea 19.2).
//
// Envuelve `fetch` con un `AbortController` que aborta la petición al cumplirse
// el límite de 30 segundos (Req 7.8, design.md "Timeout de 30 s"). Normaliza
// todos los modos de fallo a `ApiError`:
//   - aborto por timeout        → ApiError("timeout")
//   - fallo de red/transporte   → ApiError("network")
//   - respuesta HTTP de error   → ApiError("http", status, code del cuerpo)
//
// El backend responde JSON con el cuerpo uniforme `{ detail, error }` en los
// errores; las respuestas correctas pueden ser JSON o `204 No Content`.

import { API_URL, STATIC_MODE, STATIC_SNAPSHOT_BASE } from "../config";
import { ApiError, type ApiErrorBody } from "./apiError";

/** Límite de tiempo por petición, en milisegundos (30 segundos, Req 7.8). */
export const REQUEST_TIMEOUT_MS = 30_000;

/** Métodos HTTP utilizados por la API (solo crear y consultar, no update/delete). */
type HttpMethod = "GET" | "POST";

interface RequestOptions {
  /** Método HTTP; por defecto `GET`. */
  readonly method?: HttpMethod;
  /** Cuerpo JSON para peticiones de creación (serializado automáticamente). */
  readonly body?: unknown;
  /**
   * Señal externa opcional para que quien llama pueda cancelar la petición
   * (p. ej. al desmontar un componente). Se combina con el timeout interno.
   */
  readonly signal?: AbortSignal;
}

/** Une la ruta con la URL base evitando barras duplicadas o ausentes. */
function buildUrl(path: string): string {
  const base = API_URL.replace(/\/+$/, "");
  const suffix = path.startsWith("/") ? path : `/${path}`;
  return `${base}${suffix}`;
}

/**
 * Traduce una ruta de la API a la ruta del archivo del snapshot estático.
 *
 * El snapshot (ver `scripts/export_static_snapshot.py`) replica la estructura
 * de rutas de la API y guarda cada respuesta GET como un `.json`. Ejemplos:
 *   /ejes                         -> /api-snapshot/ejes.json
 *   /ejes/1/metas                 -> /api-snapshot/ejes/1/metas.json
 *   /bibliometria/resumen         -> /api-snapshot/bibliometria/resumen.json
 */
function buildSnapshotUrl(path: string): string {
  const clean = path.replace(/^\/+/, "").replace(/\/+$/, "");
  return `${STATIC_SNAPSHOT_BASE}/${clean}.json`;
}

/**
 * Atiende una petición en MODO ESTÁTICO (demo sin backend).
 *
 * - Las lecturas (`GET`) se sirven desde los archivos JSON del snapshot. Un
 *   archivo ausente (404 del hosting estático) se traduce a un `ApiError` 404,
 *   igual que haría el backend real.
 * - Las escrituras (`POST`) no se persisten: se rechazan con un `ApiError`
 *   claro, porque esta demo es de solo lectura (no hay servidor).
 */
async function requestStatic<T>(path: string, method: HttpMethod): Promise<T> {
  if (method !== "GET") {
    throw new ApiError(
      "http",
      "Esta es una versión de demostración de solo lectura: la creación de " +
        "datos no está disponible aquí.",
      { status: 405, code: "static_demo_read_only" },
    );
  }

  let response: Response;
  try {
    response = await fetch(buildSnapshotUrl(path), { method: "GET" });
  } catch (cause) {
    throw new ApiError("network", "No se pudieron cargar los datos de la demo.", {
      cause,
    });
  }

  if (!response.ok) {
    // En hosting estático, un recurso inexistente responde 404: se mapea a
    // "no encontrado", el mismo significado que en la API real.
    throw new ApiError("http", "Recurso no encontrado en la demo.", {
      status: response.status === 404 ? 404 : response.status,
      code: response.status === 404 ? "not_found" : undefined,
    });
  }

  return (await response.json()) as T;
}

/**
 * Extrae el código de error estable (`error`) y el mensaje (`detail`) del cuerpo
 * uniforme del backend. Si el cuerpo no es el esperado, degrada con seguridad.
 */
async function readErrorBody(
  response: Response,
): Promise<{ detail?: string; code?: string }> {
  try {
    const data = (await response.json()) as ApiErrorBody;
    return { detail: data.detail, code: data.error };
  } catch {
    // Cuerpo ausente o no-JSON: no se exponen detalles internos (Req 7.9).
    return {};
  }
}

/**
 * Realiza una petición a la API y devuelve el cuerpo deserializado como `T`.
 *
 * Aplica el timeout de 30 s mediante `AbortController`. Lanza `ApiError` para
 * cualquier modo de fallo, de forma que la UI pueda reaccionar sin inspeccionar
 * códigos HTTP crudos.
 *
 * @typeParam T Tipo esperado del cuerpo de respuesta.
 * @throws {ApiError} timeout | network | http.
 */
export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, signal } = options;

  // Modo estático (demo sin backend): sirve desde el snapshot JSON y bloquea
  // las escrituras. No aplica timeout ni cabeceras de red reales.
  if (STATIC_MODE) {
    return requestStatic<T>(path, method);
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  // Propaga una cancelación externa (si la hay) al controlador interno.
  const onExternalAbort = () => controller.abort();
  if (signal) {
    if (signal.aborted) {
      controller.abort();
    } else {
      signal.addEventListener("abort", onExternalAbort, { once: true });
    }
  }

  let response: Response;
  try {
    response = await fetch(buildUrl(path), {
      method,
      headers: body !== undefined ? { "Content-Type": "application/json" } : undefined,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });
  } catch (cause) {
    // `fetch` lanza `AbortError` tanto por timeout como por cancelación externa.
    // Si fue el timeout interno (y no una señal externa ya abortada), lo tratamos
    // como timeout manejable; en otro caso, como fallo de red/transporte.
    if (controller.signal.aborted && !(signal?.aborted ?? false)) {
      throw new ApiError(
        "timeout",
        "La consulta no pudo completarse en el tiempo esperado.",
        { cause },
      );
    }
    throw new ApiError(
      "network",
      "No se pudo conectar con el servidor.",
      { cause },
    );
  } finally {
    clearTimeout(timeoutId);
    if (signal) {
      signal.removeEventListener("abort", onExternalAbort);
    }
  }

  if (!response.ok) {
    const { detail, code } = await readErrorBody(response);
    throw new ApiError(
      "http",
      detail ?? "La solicitud no pudo completarse.",
      { status: response.status, code },
    );
  }

  // 204 No Content (u otras respuestas sin cuerpo): devuelve `undefined` como T.
  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}
