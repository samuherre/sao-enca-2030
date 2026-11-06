// Pruebas de LoadingIndicator (tarea 23.1).
//
// Cubre Req 7.7: mientras la interfaz espera la respuesta de la API se muestra
// un indicador de carga. El indicador es accesible (`role="status"`,
// `aria-live="polite"`) y admite un mensaje comprensible personalizado.

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { LoadingIndicator } from "./LoadingIndicator";

describe("LoadingIndicator", () => {
  it("muestra un mensaje de carga por defecto comprensible (Req 7.7)", () => {
    render(<LoadingIndicator />);

    const status = screen.getByRole("status");
    expect(status).toHaveTextContent(/cargando/i);
    expect(status).toHaveAttribute("aria-live", "polite");
  });

  it("admite un mensaje de carga personalizado", () => {
    render(<LoadingIndicator message="Cargando Metas…" />);

    expect(screen.getByRole("status")).toHaveTextContent("Cargando Metas…");
  });
});
