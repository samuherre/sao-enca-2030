// Indicador de estado de carga (tarea 20.1).
//
// Se muestra mientras la interfaz espera la respuesta de la API, hasta que la
// respuesta se reciba o se cumpla el tiempo límite de 30 s (Req 7.7). No
// contiene lógica de red: solo refleja visualmente el estado `loading` que los
// hooks de datos exponen (ver `useAsyncData`).

interface LoadingIndicatorProps {
  /**
   * Mensaje opcional mostrado junto al indicador. Por defecto comunica que la
   * información se está cargando, en lenguaje comprensible para el usuario.
   */
  readonly message?: string;
}

/** Mensaje por defecto del indicador de carga. */
const DEFAULT_MESSAGE = "Cargando información…";

/**
 * Indicador de carga accesible.
 *
 * Usa `role="status"` y `aria-live="polite"` para que las tecnologías de
 * asistencia anuncien el cambio de estado sin interrumpir al usuario.
 */
export function LoadingIndicator({ message = DEFAULT_MESSAGE }: LoadingIndicatorProps) {
  return (
    <div
      role="status"
      aria-live="polite"
      style={{
        display: "flex",
        alignItems: "center",
        gap: "0.5rem",
        padding: "1rem 0",
        color: "#444",
      }}
    >
      <span
        aria-hidden="true"
        style={{
          width: "1rem",
          height: "1rem",
          border: "0.15rem solid #ccc",
          borderTopColor: "#555",
          borderRadius: "50%",
          display: "inline-block",
        }}
      />
      <span>{message}</span>
    </div>
  );
}
