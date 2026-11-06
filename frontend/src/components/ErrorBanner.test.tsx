// Pruebas de ErrorBanner (tarea 23.1).
//
// Cubre:
//   - Req 7.9: muestra un mensaje comprensible SIN exponer trazas de pila,
//     identificadores internos (status HTTP, `code` del backend) ni detalles
//     técnicos de implementación.
//   - Req 7.8: ante un timeout muestra un mensaje específico que aclara que se
//     conserva la última información mostrada.

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ErrorBanner } from "./ErrorBanner";
import { ApiError } from "../services";

describe("ErrorBanner", () => {
  it("muestra un mensaje específico de timeout que conserva la última vista (Req 7.8)", () => {
    const error = new ApiError("timeout", "La consulta no pudo completarse en el tiempo esperado.", {
      cause: new Error("AbortError"),
    });

    render(<ErrorBanner error={error} />);

    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent(/tardó demasiado/i);
    expect(alert).toHaveTextContent(/se conserva la última/i);
  });

  it("muestra mensaje de red para fallos de conexión", () => {
    const error = new ApiError("network", "No se pudo conectar con el servidor.");

    render(<ErrorBanner error={error} />);

    expect(screen.getByRole("alert")).toHaveTextContent(/no se pudo conectar/i);
  });

  it("muestra mensaje amigable de 'no encontrado' para HTTP 404", () => {
    const error = new ApiError("http", "El Eje 999 no existe en la base de datos", {
      status: 404,
      code: "not_found",
    });

    render(<ErrorBanner error={error} />);

    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent(/no se encontró la información/i);
  });

  it("NO expone trazas, códigos HTTP ni ids internos del error (Req 7.9)", () => {
    const error = new ApiError(
      "http",
      "Traceback: NullPointer at eje_service.py:42 (internal_id=abc-123)",
      { status: 500, code: "internal_error_xyz" },
    );

    render(<ErrorBanner error={error} />);

    const alert = screen.getByRole("alert");
    // El mensaje crudo del backend y los detalles técnicos nunca se renderizan.
    expect(alert).not.toHaveTextContent(/traceback/i);
    expect(alert).not.toHaveTextContent(/eje_service\.py/i);
    expect(alert).not.toHaveTextContent(/internal_id/i);
    expect(alert).not.toHaveTextContent(/500/);
    expect(alert).not.toHaveTextContent(/internal_error_xyz/);
    // En su lugar muestra el mensaje genérico comprensible.
    expect(alert).toHaveTextContent(/no pudo completarse/i);
  });

  it("invoca onRetry al pulsar 'Reintentar'", async () => {
    const onRetry = vi.fn();
    const error = new ApiError("network", "No se pudo conectar.");

    render(<ErrorBanner error={error} onRetry={onRetry} />);

    await userEvent.click(screen.getByRole("button", { name: /reintentar/i }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });
});
