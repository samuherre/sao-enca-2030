// Panel de resumen de la vista de Seguimiento ENCA.
//
// Muestra los totales de cada nivel de la jerarquía (ejes, metas, objetivos,
// indicadores, actividades) como tarjetas compactas. Es un adorno informativo
// que da contexto de la magnitud de la estructura; las cifras se calculan a
// partir del dato real (no se inventan) mediante `useTotalesEnca`.
//
// Mientras cargan, no muestra nada (evita parpadeo de ceros). Si falla la carga
// de los totales, tampoco se muestra: es un resumen complementario, no debe
// romper la vista principal.

import type { CSSProperties } from "react";

import { useTotalesEnca } from "../hooks";

const VERDE_OSCURO = "#1f5c3a";
const BORDE = "#d7e3dc";
const FONDO_SUAVE = "#f3f8f5";

const tarjeta: CSSProperties = {
  flex: "1 1 120px",
  minWidth: 110,
  padding: "0.6rem 0.9rem",
  border: `1px solid ${BORDE}`,
  borderRadius: "0.5rem",
  backgroundColor: FONDO_SUAVE,
  textAlign: "center",
};

/** Un dato del resumen: número grande + etiqueta. */
function Tarjeta({ valor, etiqueta }: { valor: number; etiqueta: string }) {
  return (
    <div style={tarjeta}>
      <div style={{ fontSize: "1.6rem", fontWeight: 700, color: VERDE_OSCURO }}>
        {new Intl.NumberFormat("es-CO").format(valor)}
      </div>
      <div style={{ fontSize: "0.8rem", color: "#456" }}>{etiqueta}</div>
    </div>
  );
}

/**
 * Tarjetas con los totales de la jerarquía ENCA. No muestra nada mientras carga
 * o si la carga falla (resumen complementario, no crítico).
 */
export function ResumenEnca() {
  const { data } = useTotalesEnca();
  if (data === null) {
    return null;
  }
  return (
    <section
      aria-label="Totales de la estructura ENCA"
      style={{
        display: "flex",
        flexWrap: "wrap",
        gap: "0.6rem",
        margin: "0 0 1rem",
      }}
    >
      <Tarjeta valor={data.ejes} etiqueta="Ejes" />
      <Tarjeta valor={data.metas} etiqueta="Metas" />
      <Tarjeta valor={data.objetivos} etiqueta="Objetivos" />
      <Tarjeta valor={data.indicadores} etiqueta="Indicadores" />
      <Tarjeta valor={data.actividades} etiqueta="Actividades" />
    </section>
  );
}
