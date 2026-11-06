// Detalle de una entidad y sus campos confirmados (tarea 20.1).
//
// Muestra los campos CONFIRMADOS de una entidad obtenidos desde la API y, para
// cada campo cuyo valor sea nulo o vacío, muestra la indicación "Sin información"
// (Req 7.5). No incluye ni infiere atributos PENDING_VALIDATION: quien usa el
// componente decide qué campos confirmados pasar (p. ej. Indicador y Actividad
// nunca incluyen atributos pendientes de validación).
//
// Principio de no invención (Steering): un valor ausente se comunica
// explícitamente como "Sin información", nunca con un valor inventado.

/** Texto mostrado cuando un campo confirmado no tiene valor (Req 7.5). */
export const NO_INFO_LABEL = "Sin información";

/** Un campo confirmado a mostrar: su etiqueta legible y su valor. */
export interface EntityField {
  /** Etiqueta legible del campo (p. ej. "Nombre", "Descripción"). */
  readonly label: string;
  /**
   * Valor del campo. Un valor nulo, indefinido o cadena vacía/solo espacios se
   * considera "sin información".
   */
  readonly value: string | number | null | undefined;
}

interface EntityDetailProps {
  /** Lista de campos confirmados a mostrar, en orden. */
  readonly fields: readonly EntityField[];
}

/**
 * Determina si el valor de un campo debe tratarse como "sin información".
 * Son vacíos: `null`, `undefined` y las cadenas que tras recortar quedan vacías.
 * Los números (incluido `0`) se consideran valores presentes.
 */
function isEmptyValue(value: EntityField["value"]): boolean {
  if (value === null || value === undefined) {
    return true;
  }
  if (typeof value === "string") {
    return value.trim().length === 0;
  }
  return false;
}

/**
 * Lista de definición (`<dl>`) con los campos confirmados de la entidad.
 *
 * Cada campo vacío se renderiza con la indicación "Sin información" en un tono
 * atenuado, para distinguirlo claramente de un dato real (Req 7.5).
 */
export function EntityDetail({ fields }: EntityDetailProps) {
  return (
    <dl
      style={{
        margin: "0.5rem 0",
        display: "grid",
        gridTemplateColumns: "max-content 1fr",
        gap: "0.35rem 1rem",
      }}
    >
      {fields.map((field) => {
        const empty = isEmptyValue(field.value);
        return (
          <div key={field.label} style={{ display: "contents" }}>
            <dt style={{ fontWeight: 600, color: "#333" }}>{field.label}</dt>
            <dd
              style={{
                margin: 0,
                color: empty ? "#888" : "#1a1a1a",
                fontStyle: empty ? "italic" : "normal",
              }}
            >
              {empty ? NO_INFO_LABEL : String(field.value)}
            </dd>
          </div>
        );
      })}
    </dl>
  );
}
