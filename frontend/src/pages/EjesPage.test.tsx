// Pruebas de EjesPage (tarea 23.1), la vista inicial.
//
// Cubre:
//   - Req 7.1: al abrir, solicita la lista de Ejes y la muestra.
//   - Req 7.7: muestra el indicador de carga mientras espera la respuesta.
//   - Req 7.2: colección vacía → mensaje contextual (no lista en blanco).
//   - Req 7.9: ante un error de la API, muestra un mensaje comprensible sin
//     exponer detalles técnicos.
//   - Req 7.6 (crear): el formulario de creación llama al cliente API y recarga.
//
// La capa de servicios se sustituye por dobles deterministas (vi.mock), de modo
// que las pruebas no dependen de un backend real.

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { EjesPage } from "./EjesPage";
import { ApiError } from "../services";
import * as api from "../services";
import type { Eje } from "../types";

vi.mock("../services", async () => {
  const actual = await vi.importActual<typeof import("../services")>("../services");
  return {
    ...actual,
    listarEjes: vi.fn(),
    crearEje: vi.fn(),
  };
});

const listarEjes = vi.mocked(api.listarEjes);
const crearEje = vi.mocked(api.crearEje);

describe("EjesPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("solicita y muestra la lista de Ejes al abrir (Req 7.1)", async () => {
    const ejes: Eje[] = [
      { id: 1, nombre: "Eje Andino", descripcion: "Montañas" },
      { id: 2, nombre: "Eje Caribe", descripcion: null },
    ];
    listarEjes.mockResolvedValue(ejes);

    render(<EjesPage onSelectEje={vi.fn()} />);

    // "Eje Andino" aparece como título y como valor del campo "Nombre": basta
    // con que esté presente al menos una vez.
    expect((await screen.findAllByText("Eje Andino")).length).toBeGreaterThan(0);
    expect(screen.getAllByText("Eje Caribe").length).toBeGreaterThan(0);
    expect(listarEjes).toHaveBeenCalledTimes(1);
  });

  it("muestra el indicador de carga mientras espera la respuesta (Req 7.7)", async () => {
    // Promesa que no se resuelve de inmediato para capturar el estado de carga.
    let resolve!: (value: Eje[]) => void;
    listarEjes.mockReturnValue(
      new Promise<Eje[]>((r) => {
        resolve = r;
      }),
    );

    render(<EjesPage onSelectEje={vi.fn()} />);

    expect(screen.getByRole("status")).toHaveTextContent(/cargando/i);

    resolve([]);
    await waitFor(() => expect(screen.queryByText(/cargando/i)).not.toBeInTheDocument());
  });

  it("muestra un mensaje contextual cuando la API no devuelve Ejes (Req 7.2)", async () => {
    listarEjes.mockResolvedValue([]);

    render(<EjesPage onSelectEje={vi.fn()} />);

    expect(await screen.findByText(/no hay ejes disponibles/i)).toBeInTheDocument();
  });

  it("muestra un error comprensible sin detalles técnicos cuando la API falla (Req 7.9)", async () => {
    listarEjes.mockRejectedValue(
      new ApiError("http", "Traceback internal_id=abc en eje_service.py", {
        status: 500,
        code: "boom_internal",
      }),
    );

    render(<EjesPage onSelectEje={vi.fn()} />);

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent(/no pudo completarse/i);
    expect(alert).not.toHaveTextContent(/traceback/i);
    expect(alert).not.toHaveTextContent(/eje_service/i);
    expect(alert).not.toHaveTextContent(/boom_internal/i);
  });

  it("crea un Eje a través del formulario y recarga la lista (Req 7.6)", async () => {
    listarEjes.mockResolvedValue([]);
    crearEje.mockResolvedValue({ id: 10, nombre: "Nuevo Eje", descripcion: null });

    render(<EjesPage onSelectEje={vi.fn()} />);
    await screen.findByText(/no hay ejes disponibles/i);

    // Con la colección vacía no hay botones de drill-down: el único botón es
    // "Crear" del formulario de creación.
    await userEvent.type(screen.getByLabelText(/nombre/i), "Nuevo Eje");
    await userEvent.click(screen.getByRole("button", { name: /^crear$/i }));

    await waitFor(() =>
      expect(crearEje).toHaveBeenCalledWith({ nombre: "Nuevo Eje" }),
    );
    // Tras crear, se recarga la colección (segunda llamada a listarEjes).
    await waitFor(() => expect(listarEjes).toHaveBeenCalledTimes(2));
  });
});
