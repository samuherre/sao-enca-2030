// Pruebas de navegación del App shell (tarea 23.1).
//
// Cubre el flujo completo de drill-down con regreso entre niveles de la
// jerarquía (Req 7.3 y 7.6):
//   Eje → Meta → Objetivo (drill-down), y regreso a un nivel superior mediante
//   las migas de pan.
//
// La capa de servicios se sustituye por dobles deterministas (vi.mock), de modo
// que la navegación no depende de un backend real.

import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";
import * as api from "./services";
import type { Eje, Meta, Objetivo } from "./types";

vi.mock("./services", async () => {
  const actual = await vi.importActual<typeof import("./services")>("./services");
  return {
    ...actual,
    listarEjes: vi.fn(),
    listarMetas: vi.fn(),
    listarObjetivos: vi.fn(),
    listarIndicadores: vi.fn(),
    listarActividades: vi.fn(),
  };
});

const listarEjes = vi.mocked(api.listarEjes);
const listarMetas = vi.mocked(api.listarMetas);
const listarObjetivos = vi.mocked(api.listarObjetivos);
const listarIndicadores = vi.mocked(api.listarIndicadores);
const listarActividades = vi.mocked(api.listarActividades);

const EJE: Eje = { id: 1, nombre: "Eje Andino", descripcion: null };
const META: Meta = { id: 10, descripcion: "Meta A", eje_id: 1 };
const OBJETIVO: Objetivo = { id: 100, descripcion: "Objetivo X", meta_id: 10 };

describe("App — navegación de la jerarquía", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    listarEjes.mockResolvedValue([EJE]);
    listarMetas.mockResolvedValue([META]);
    listarObjetivos.mockResolvedValue([OBJETIVO]);
    // Niveles inferiores: colecciones vacías (no se profundiza más en la prueba).
    listarIndicadores.mockResolvedValue([]);
    listarActividades.mockResolvedValue([]);
  });

  it("hace drill-down Eje → Meta → Objetivo y regresa con las migas de pan (Req 7.3, 7.6)", async () => {
    render(<App />);

    // Nivel raíz: lista de Ejes (botón de drill-down a Metas).
    await userEvent.click(await screen.findByRole("button", { name: /ver metas/i }));

    // Drill-down a Metas del Eje → botón de drill-down a Objetivos.
    await userEvent.click(await screen.findByRole("button", { name: /ver objetivos/i }));
    expect(listarMetas).toHaveBeenCalledWith(1, expect.anything());

    // Drill-down a Objetivos de la Meta → botón de drill-down a Indicadores.
    await userEvent.click(await screen.findByRole("button", { name: /ver indicadores/i }));
    expect(listarObjetivos).toHaveBeenCalledWith(10, expect.anything());

    // Las migas de pan reflejan la ruta completa visitada y el nivel actual.
    const breadcrumb = screen.getByRole("navigation", { name: /ruta de navegación/i });
    expect(within(breadcrumb).getByText("Ejes")).toBeInTheDocument();
    expect(within(breadcrumb).getByText("Eje Andino")).toBeInTheDocument();
    expect(within(breadcrumb).getByText("Meta A")).toBeInTheDocument();

    // Regreso al nivel superior "Ejes" pulsando su miga (Req 7.6).
    await userEvent.click(within(breadcrumb).getByRole("button", { name: "Ejes" }));

    // Vuelve a mostrarse el nivel raíz de Ejes…
    expect(await screen.findByText("Ejes estratégicos")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /ver metas/i })).toBeInTheDocument();
    // …y ya no se ve el nivel de Objetivos (su botón de drill-down desaparece).
    expect(screen.queryByRole("button", { name: /ver indicadores/i })).not.toBeInTheDocument();
  });
});
