// Estado vacío contextual (tarea 20.1).
//
// Se muestra cuando una consulta a la API devuelve una colección vacía, en
// lugar de dejar una lista en blanco sin contexto (Req 7.2, 7.4). El mensaje lo
// decide quien lo usa, para que sea específico del nivel consultado
// (p. ej. "No hay Ejes disponibles" o "Esta Meta no tiene Objetivos").

interface EmptyStateProps {
  /** Mensaje contextual que explica por qué no hay elementos para mostrar. */
  readonly message: string;
}

/**
 * Mensaje de "sin elementos" accesible.
 *
 * Usa `role="status"` para que el cambio a un estado vacío sea anunciado por
 * las tecnologías de asistencia.
 */
export function EmptyState({ message }: EmptyStateProps) {
  return (
    <p
      role="status"
      style={{
        padding: "1rem",
        color: "#555",
        backgroundColor: "#f7f7f7",
        border: "1px solid #e5e5e5",
        borderRadius: "0.375rem",
        margin: "0.5rem 0",
      }}
    >
      {message}
    </p>
  );
}
