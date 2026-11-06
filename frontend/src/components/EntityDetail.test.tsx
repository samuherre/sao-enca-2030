// Pruebas de EntityDetail (tarea 23.1).
//
// Cubre Req 7.5: se muestran los campos confirmados de la entidad y, para cada
// campo cuyo valor sea nulo o vacío (o solo espacios), se muestra la indicación
// "Sin información" en lugar de un valor inventado (principio de no invención).

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { EntityDetail, NO_INFO_LABEL } from "./EntityDetail";

describe("EntityDetail", () => {
  it("muestra los valores de los campos confirmados presentes", () => {
    render(
      <EntityDetail
        fields={[
          { label: "Nombre", value: "Eje Andino" },
          { label: "Descripción", value: "Conservación de aves de montaña" },
        ]}
      />,
    );

    expect(screen.getByText("Eje Andino")).toBeInTheDocument();
    expect(screen.getByText("Conservación de aves de montaña")).toBeInTheDocument();
    expect(screen.queryByText(NO_INFO_LABEL)).not.toBeInTheDocument();
  });

  it('muestra "Sin información" para valores nulos, vacíos o solo espacios (Req 7.5)', () => {
    render(
      <EntityDetail
        fields={[
          { label: "Nulo", value: null },
          { label: "Indefinido", value: undefined },
          { label: "Vacío", value: "" },
          { label: "Espacios", value: "   " },
        ]}
      />,
    );

    expect(screen.getAllByText(NO_INFO_LABEL)).toHaveLength(4);
  });

  it("trata el número 0 como un valor presente, no como vacío", () => {
    render(<EntityDetail fields={[{ label: "Conteo", value: 0 }]} />);

    expect(screen.getByText("0")).toBeInTheDocument();
    expect(screen.queryByText(NO_INFO_LABEL)).not.toBeInTheDocument();
  });
});
