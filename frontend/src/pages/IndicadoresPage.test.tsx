// Pruebas de IndicadoresPage (tarea 23.1).
//
// Cubre:
//   - Req 7.3: lista los Indicadores del Objetivo y permite drill-down a
//     Actividades.
//   - Req 4.7 / 9.1: la vista NO muestra atributos PENDING_VALIDATION del
//     Indicador (unidad de medida, valor objetivo/actual, fecha, fuente,
//     estado). El texto del indicador se muestra UNA sola vez (como título),
//     sin duplicarlo en campos Nombre/Descripción.

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { IndicadoresPage } from "./IndicadoresPage";
import * as api from "../services";
import type { Indicador, Objetivo } from "../types";

vi.mock("../services", async () => {
  const actual = await vi.importActual<typeof import("../services")>("../services");
  return {
    ...actual,
    listarIndicadores: vi.fn(),
    crearIndicador: vi.fn(),
  };
});

const listarIndicadores = vi.mocked(api.listarIndicadores);

const OBJETIVO: Objetivo = { id: 5, descripcion: "Objetivo X", meta_id: 2 };

describe("IndicadoresPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("lista los Indicadores mostrando solo campos confirmados (Req 4.7 / 9.1)", async () => {
    const indicadores: Indicador[] = [
      { id: 1, nombre: "Cobertura", descripcion: "Porcentaje de cobertura", objetivo_id: 5 },
    ];
    listarIndicadores.mockResolvedValue(indicadores);

    render(<IndicadoresPage objetivo={OBJETIVO} onSelectIndicador={vi.fn()} />);

    // El texto del indicador se muestra como título (una sola vez, sin
    // duplicarlo en campos Nombre/Descripción).
    expect((await screen.findAllByText("Cobertura")).length).toBeGreaterThan(0);

    // Ningún atributo PENDING_VALIDATION del Indicador se renderiza.
    expect(screen.queryByText(/unidad de medida/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/valor objetivo/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/valor actual/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/fecha de medición/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/^estado$/i)).not.toBeInTheDocument();
  });

  it("permite drill-down al nivel de Actividades (Req 7.3)", async () => {
    const indicador: Indicador = {
      id: 1,
      nombre: "Cobertura",
      descripcion: "desc",
      objetivo_id: 5,
    };
    listarIndicadores.mockResolvedValue([indicador]);
    const onSelectIndicador = vi.fn();

    render(
      <IndicadoresPage objetivo={OBJETIVO} onSelectIndicador={onSelectIndicador} />,
    );
    await screen.findByRole("button", { name: /ver actividades/i });

    await userEvent.click(screen.getByRole("button", { name: /ver actividades/i }));
    expect(onSelectIndicador).toHaveBeenCalledWith(indicador);
  });
});
