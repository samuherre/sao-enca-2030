// Pruebas de DemoDataBadge (tarea 23.1).
//
// Cubre Req 10.2 / 10.3: cuando un campo lleva el marcador textual legible
// "[DEMO_DATA]", el badge debe avisar que el dato es de demostración y NO
// información oficial de SAO; en caso contrario no debe renderizar nada.

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { DemoDataBadge } from "./DemoDataBadge";
import { DEMO_DATA_MESSAGE } from "../utils/demoData";

describe("DemoDataBadge", () => {
  it("muestra el aviso cuando un valor contiene el marcador [DEMO_DATA] (Req 10.2)", () => {
    render(<DemoDataBadge value="[DEMO_DATA] Eje de ejemplo" />);

    expect(screen.getByText(DEMO_DATA_MESSAGE)).toBeInTheDocument();
  });

  it("detecta el marcador en cualquiera de varios campos (lista de valores)", () => {
    render(<DemoDataBadge value={["Nombre real", "[DEMO_DATA] descripción"]} />);

    expect(screen.getByText(DEMO_DATA_MESSAGE)).toBeInTheDocument();
  });

  it("no renderiza nada cuando ningún valor lleva el marcador (dato oficial)", () => {
    const { container } = render(
      <DemoDataBadge value={["Eje Andino", "Conservación de aves"]} />,
    );

    expect(screen.queryByText(DEMO_DATA_MESSAGE)).not.toBeInTheDocument();
    expect(container).toBeEmptyDOMElement();
  });

  it("ignora valores no textuales (null, number) sin lanzar", () => {
    const { container } = render(<DemoDataBadge value={[null, 42, undefined]} />);

    expect(container).toBeEmptyDOMElement();
  });
});
