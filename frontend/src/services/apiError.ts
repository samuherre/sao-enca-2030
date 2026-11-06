// Modelo de error de la capa de servicios (tarea 19.2).
//
// Unifica en una sola estructura manejable por la UI los distintos modos de
// fallo de una petición a la API:
//   - "timeout": la petición superó el límite de 30 s y fue abortada (Req 7.8).
//   - "network": fallo de red/transporte (sin respuesta HTTP del backend).
//   - "http":    el backend respondió con un código de error (4xx/5xx) y, en
//                general, el cuerpo uniforme `{ detail, error }` (design.md
//                "Formato de respuesta de error").
//
// El campo `error` del backend es un código estable y legible (p. ej.
// `parent_not_found`, `validation_error`, `not_found`) que la UI puede mapear a
// mensajes amigables. NUNCA se exponen trazas de pila ni detalles internos
// (Req 7.9).

/** Clase de fallo de una petición, para que la UI reaccione sin leer códigos HTTP. */
export type ApiErrorKind = "timeout" | "network" | "http";

/**
 * Error normalizado de la API, manejable por la interfaz.
 *
 * Es una subclase de `Error` para integrarse con los flujos estándar de
 * `try/catch` y para que los hooks puedan almacenarla directamente en su estado.
 */
export class ApiError extends Error {
  /** Clase de fallo (timeout / network / http). */
  readonly kind: ApiErrorKind;
  /**
   * Código HTTP de la respuesta cuando `kind === "http"`; `undefined` para
   * timeout o errores de red.
   */
  readonly status?: number;
  /**
   * Código de error estable del backend (campo `error` del cuerpo uniforme),
   * cuando está disponible. La UI puede mapearlo a un mensaje amigable.
   */
  readonly code?: string;
  /**
   * Causa original del fallo (p. ej. el `AbortError` de `fetch`), conservada
   * para diagnóstico. No se expone al usuario (Req 7.9). Se almacena en la
   * instancia porque la opción `cause` del constructor de `Error` requiere un
   * `lib` ES2022, mientras el proyecto compila contra ES2020.
   */
  readonly cause?: unknown;

  constructor(
    kind: ApiErrorKind,
    message: string,
    options?: { status?: number; code?: string; cause?: unknown },
  ) {
    super(message);
    this.name = "ApiError";
    this.kind = kind;
    this.status = options?.status;
    this.code = options?.code;
    this.cause = options?.cause;
  }

  /** `true` si el fallo se debió al límite de tiempo de 30 s (Req 7.8). */
  get isTimeout(): boolean {
    return this.kind === "timeout";
  }

  /** `true` si el recurso referenciado no existe (HTTP 404). */
  get isNotFound(): boolean {
    return this.kind === "http" && this.status === 404;
  }

  /** `true` si el backend rechazó la entrada por validación (HTTP 422). */
  get isValidation(): boolean {
    return this.kind === "http" && this.status === 422;
  }
}

/**
 * Forma del cuerpo de error uniforme del backend
 * (`design.md` "Formato de respuesta de error"): `{ "detail", "error" }`.
 */
export interface ApiErrorBody {
  readonly detail?: string;
  readonly error?: string;
}
