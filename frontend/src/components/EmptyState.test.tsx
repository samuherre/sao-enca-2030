// Pruebas de EmptyState (tarea 23.1).
//
// Cubre Req 7.2 / 7.4: cuando una colección está vacía se muestra un mensaje
// contextual (no una lista en blanco sin contexto). El mensaje lo decide quien
// usa el componente, por lo que la prueba verifica que se renderiza tal cual y
// de forma accesible (`role="status"`).

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { EmptyState } from "./EmptyState";

describe("EmptyState", () => {
  it("muestra el mensaje contextual recibido (Req 7.2 / 7.4)", () => {
    render(<EmptyState message="No hay Ejes disponibles." />);

    expect(screen.getByText("No hay Ejes disponibles.")).toBeInTheDocument();
  });

  it("anuncia el estado vacío de forma accesible (role=status)", () => {
    render(<EmptyState message="Esta Meta no tiene Objetivos." />);

    const status = screen.getByRole("status");
    expect(status).toHaveTextContent("Esta Meta no tiene Objetivos.");
  });
});
