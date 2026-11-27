// Pruebas de navegación del App shell (tarea 23.1).
//
// Cubre el flujo completo de drill-down con regreso entre niveles de la
// jerarquía (Req 7.3 y 7.6):
//   Eje → Meta → Objetivo (drill-down), y regreso a un nivel superior mediante
//   el botón "Volver".
//
// La capa de servicios se sustituye por dobles deterministas (vi.mock), de modo
// que la navegación no depende de un backend real.

import { render, screen } from "@testing-library/react";
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

  it("hace drill-down Eje → Meta → Objetivo y regresa con el botón Volver (Req 7.3, 7.6)", async () => {
    render(<App />);

    // Nivel raíz: lista de Ejes (botón de drill-down a Metas). Aquí NO debe
    // existir el botón "Volver" (se está en la raíz).
    expect(screen.queryByRole("button", { name: /volver/i })).not.toBeInTheDocument();
    await userEvent.click(await screen.findByRole("button", { name: /ver metas/i }));

    // Drill-down a Metas del Eje → botón de drill-down a Objetivos.
    await userEvent.click(await screen.findByRole("button", { name: /ver objetivos/i }));
    expect(listarMetas).toHaveBeenCalledWith(1, expect.anything());

    // Drill-down a Objetivos de la Meta → botón de drill-down a Indicadores.
    await userEvent.click(await screen.findByRole("button", { name: /ver indicadores/i }));
    expect(listarObjetivos).toHaveBeenCalledWith(10, expect.anything());

    // Ahora se está en el nivel de Indicadores (nivel 4). Cada "Volver" sube un
    // nivel: Indicadores → Objetivos → Metas → Ejes.

    // Volver 1: de Indicadores a Objetivos (reaparece "Ver indicadores").
    await userEvent.click(await screen.findByRole("button", { name: /volver/i }));
    expect(await screen.findByRole("button", { name: /ver indicadores/i })).toBeInTheDocument();

    // Volver 2: de Objetivos a Metas (reaparece "Ver objetivos").
    await userEvent.click(await screen.findByRole("button", { name: /volver/i }));
    expect(await screen.findByRole("button", { name: /ver objetivos/i })).toBeInTheDocument();

    // Volver 3: de Metas a la raíz de Ejes.
    await userEvent.click(await screen.findByRole("button", { name: /volver/i }));
    expect(await screen.findByText("Ejes estratégicos")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /ver metas/i })).toBeInTheDocument();
    // En la raíz ya no hay botón "Volver" ni niveles inferiores.
    expect(screen.queryByRole("button", { name: /volver/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /ver objetivos/i })).not.toBeInTheDocument();
  });
});
