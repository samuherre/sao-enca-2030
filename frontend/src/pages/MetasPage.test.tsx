// Pruebas de MetasPage (tarea 23.1), vista hija de un Eje.
//
// Cubre:
//   - Req 7.3: lista las Metas del Eje (drill-down desde Ejes) y permite
//     profundizar al nivel inferior (Objetivos) con `onSelectMeta`.
//   - Req 7.4: si el Eje no tiene Metas, muestra un mensaje contextual.
//
// La vista es de SOLO VISUALIZACIÓN (decisión de SAO): ya no hay formulario de
// creación, por lo que no se prueba ese flujo.
//
// La capa de servicios se sustituye por dobles deterministas (vi.mock).

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { MetasPage } from "./MetasPage";
import * as api from "../services";
import type { Eje, Meta } from "../types";

vi.mock("../services", async () => {
  const actual = await vi.importActual<typeof import("../services")>("../services");
  return {
    ...actual,
    listarMetas: vi.fn(),
  };
});

const listarMetas = vi.mocked(api.listarMetas);

const EJE: Eje = { id: 3, nombre: "Eje Andino", descripcion: null };

describe("MetasPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("lista las Metas del Eje seleccionado (Req 7.3)", async () => {
    const metas: Meta[] = [
      { id: 1, descripcion: "Meta A", eje_id: 3 },
      { id: 2, descripcion: "Meta B", eje_id: 3 },
    ];
    listarMetas.mockResolvedValue(metas);

    render(<MetasPage eje={EJE} onSelectMeta={vi.fn()} />);

    // La descripción se usa como título y como valor del campo "Descripción".
    expect((await screen.findAllByText("Meta A")).length).toBeGreaterThan(0);
    expect(screen.getAllByText("Meta B").length).toBeGreaterThan(0);
    expect(listarMetas).toHaveBeenCalledWith(3, expect.anything());
  });

  it("muestra un mensaje contextual cuando el Eje no tiene Metas (Req 7.4)", async () => {
    listarMetas.mockResolvedValue([]);

    render(<MetasPage eje={EJE} onSelectMeta={vi.fn()} />);

    expect(await screen.findByText(/este eje no tiene metas/i)).toBeInTheDocument();
  });

  it("invoca el drill-down con la Meta seleccionada (Req 7.3)", async () => {
    const meta: Meta = { id: 1, descripcion: "Meta A", eje_id: 3 };
    listarMetas.mockResolvedValue([meta]);
    const onSelectMeta = vi.fn();

    render(<MetasPage eje={EJE} onSelectMeta={onSelectMeta} />);
    await screen.findByRole("button", { name: /ver objetivos/i });

    await userEvent.click(screen.getByRole("button", { name: /ver objetivos/i }));
    expect(onSelectMeta).toHaveBeenCalledWith(meta);
  });

  it("no muestra formulario de creación (vista de solo lectura)", async () => {
    listarMetas.mockResolvedValue([]);

    render(<MetasPage eje={EJE} onSelectMeta={vi.fn()} />);
    await screen.findByText(/este eje no tiene metas/i);

    expect(screen.queryByRole("button", { name: /^crear$/i })).not.toBeInTheDocument();
  });
});
