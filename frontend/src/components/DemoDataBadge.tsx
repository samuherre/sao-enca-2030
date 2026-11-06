// Badge de datos de demostración (tarea 20.2, Req 10.2 y 10.3).
//
// Cuando el frontend detecta el marcador `[DEMO_DATA]` en uno o varios campos
// de una entidad, este componente muestra una indicación visible de que el
// dato es de demostración y NO información oficial de SAO. De este modo los
// datos de desarrollo nunca se presentan como oficiales (design.md §DEMO_DATA).

import { DEMO_DATA_MESSAGE, isDemoData } from "../utils/demoData";

export interface DemoDataBadgeProps {
  /**
   * Valor o conjunto de valores a inspeccionar (p. ej. el nombre y la
   * descripción de una entidad). Si alguno contiene el marcador `[DEMO_DATA]`
   * se muestra el badge; en caso contrario no se renderiza nada.
   */
  value: unknown | readonly unknown[];
}

const badgeStyle: React.CSSProperties = {
  display: "inline-block",
  padding: "0.1rem 0.5rem",
  borderRadius: "0.25rem",
  backgroundColor: "#fff4e5",
  border: "1px solid #d9822b",
  color: "#8a4b08",
  fontSize: "0.8rem",
  fontWeight: 600,
};

/**
 * Muestra "Datos de demostración — no es información oficial de SAO" cuando el
 * valor recibido contiene el marcador DEMO_DATA; de lo contrario no renderiza
 * nada.
 */
export function DemoDataBadge({ value }: DemoDataBadgeProps) {
  if (!isDemoData(value)) {
    return null;
  }

  return (
    <span className="demo-data-badge" role="note" style={badgeStyle}>
      {DEMO_DATA_MESSAGE}
    </span>
  );
}
