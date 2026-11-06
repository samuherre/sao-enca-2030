// Banner de error comprensible (tarea 20.1).
//
// Muestra que una operación falló usando un mensaje claro para el usuario, SIN
// exponer trazas de pila, identificadores internos ni detalles técnicos de
// implementación (Req 7.9). El caso de timeout recibe un mensaje específico que
// aclara que se conserva la última vista válida mostrada (Req 7.8), coherente
// con que la UI no reemplaza los datos previos cuando la recarga falla.
//
// Las causas internas (`ApiError.cause`, códigos HTTP, `code` del backend) NO
// se renderizan: solo se usan para elegir el mensaje amigable adecuado.

import { ApiError } from "../services";

interface ErrorBannerProps {
  /**
   * Error a comunicar. Puede ser un `ApiError` normalizado (de los hooks de
   * datos) o un mensaje de texto ya resuelto por quien llama.
   */
  readonly error: ApiError | string;
  /**
   * Acción opcional de reintento. Si se proporciona, se muestra un botón
   * "Reintentar" que la invoca (p. ej. el `reload` de un hook).
   */
  readonly onRetry?: () => void;
}

/** Mensaje genérico cuando no se puede determinar una causa más específica. */
const DEFAULT_MESSAGE = "La operación no pudo completarse. Inténtalo de nuevo.";

/** Mensaje para el caso de timeout (Req 7.8): conserva la última vista válida. */
const TIMEOUT_MESSAGE =
  "La consulta tardó demasiado y no pudo completarse. Se conserva la última " +
  "información mostrada; puedes intentarlo de nuevo.";

/** Mensaje para fallos de red/conexión, sin detalles técnicos (Req 7.9). */
const NETWORK_MESSAGE =
  "No se pudo conectar con el servidor. Revisa tu conexión e inténtalo de nuevo.";

/** Mensaje para recurso no encontrado (HTTP 404), en lenguaje de usuario. */
const NOT_FOUND_MESSAGE = "No se encontró la información solicitada.";

/** Mensaje para errores de validación (HTTP 422), sin exponer el detalle crudo. */
const VALIDATION_MESSAGE =
  "Los datos enviados no son válidos. Revisa la información e inténtalo de nuevo.";

/**
 * Traduce un `ApiError` a un mensaje comprensible, sin exponer detalles
 * técnicos. Un mensaje de texto recibido directamente se usa tal cual, bajo la
 * responsabilidad de quien llama de no incluir detalles internos.
 */
function toUserMessage(error: ApiError | string): string {
  if (typeof error === "string") {
    return error.trim().length > 0 ? error : DEFAULT_MESSAGE;
  }

  if (error.isTimeout) {
    return TIMEOUT_MESSAGE;
  }
  if (error.kind === "network") {
    return NETWORK_MESSAGE;
  }
  if (error.isNotFound) {
    return NOT_FOUND_MESSAGE;
  }
  if (error.isValidation) {
    return VALIDATION_MESSAGE;
  }
  // Cualquier otro error HTTP: mensaje genérico, nunca el cuerpo crudo.
  return DEFAULT_MESSAGE;
}

/**
 * Banner de error accesible.
 *
 * Usa `role="alert"` para que el error se anuncie de inmediato. Solo renderiza
 * el mensaje amigable y, opcionalmente, un botón de reintento.
 */
export function ErrorBanner({ error, onRetry }: ErrorBannerProps) {
  const message = toUserMessage(error);

  return (
    <div
      role="alert"
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: "1rem",
        padding: "0.75rem 1rem",
        color: "#8a1f1f",
        backgroundColor: "#fdecec",
        border: "1px solid #f5c2c2",
        borderRadius: "0.375rem",
        margin: "0.5rem 0",
      }}
    >
      <span>{message}</span>
      {onRetry ? (
        <button
          type="button"
          onClick={onRetry}
          style={{
            flexShrink: 0,
            padding: "0.35rem 0.75rem",
            border: "1px solid #d99",
            borderRadius: "0.25rem",
            backgroundColor: "#fff",
            color: "#8a1f1f",
            cursor: "pointer",
          }}
        >
          Reintentar
        </button>
      ) : null}
    </div>
  );
}
