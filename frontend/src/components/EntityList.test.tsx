// Pruebas de EntityList (tarea 23.1).
//
// Cubre:
//   - Req 7.1 / 7.3: renderiza la colección de entidades como una lista.
//   - Req 7.2 / 7.4: colección vacía → mensaje contextual (no lista en blanco).
//   - Req 7.5: cada elemento muestra sus campos confirmados (vía EntityDetail).
//   - Req 10.2: elementos con marcador [DEMO_DATA] muestran el DemoDataBadge.
//   - Drill-down: si se pasa `onSelect`, cada elemento es seleccionable.

import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { EntityList, type EntityListItem } from "./EntityList";
import { DEMO_DATA_MESSAGE } from "../utils/demoData";

interface Row {
  readonly id: number;
  readonly nombre: string;
}

function renderRow(row: Row): EntityListItem {
  return {
    key: row.id,
    title: row.nombre,
    fields: [{ label: "Nombre", value: row.nombre }],
    demoValues: [row.nombre],
  };
}

describe("EntityList", () => {
  it("renderiza cada entidad de la colección (Req 7.1 / 7.3)", () => {
    const items: Row[] = [
      { id: 1, nombre: "Eje Andino" },
      { id: 2, nombre: "Eje Caribe" },
    ];

    render(
      <EntityList items={items} emptyMessage="vacío" renderItem={renderRow} />,
    );

    // Cada entidad aparece como título y como valor del campo "Nombre".
    expect(screen.getAllByText("Eje Andino").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Eje Caribe").length).toBeGreaterThan(0);
    expect(screen.getAllByRole("listitem")).toHaveLength(2);
  });

  it("muestra el mensaje contextual cuando la colección está vacía (Req 7.2 / 7.4)", () => {
    render(
      <EntityList<Row>
        items={[]}
        emptyMessage="No hay Ejes disponibles."
        renderItem={renderRow}
      />,
    );

    expect(screen.getByText("No hay Ejes disponibles.")).toBeInTheDocument();
    expect(screen.queryAllByRole("listitem")).toHaveLength(0);
  });

  it("muestra el badge DEMO_DATA en elementos marcados (Req 10.2)", () => {
    const items: Row[] = [
      { id: 1, nombre: "[DEMO_DATA] Eje de ejemplo" },
      { id: 2, nombre: "Eje real" },
    ];

    render(
      <EntityList items={items} emptyMessage="vacío" renderItem={renderRow} />,
    );

    // Solo un elemento (el marcado) muestra el aviso de demostración.
    expect(screen.getAllByText(DEMO_DATA_MESSAGE)).toHaveLength(1);
  });

  it("ofrece drill-down cuando se pasa onSelect y lo invoca con el elemento", async () => {
    const onSelect = vi.fn();
    const items: Row[] = [{ id: 7, nombre: "Eje Andino" }];

    render(
      <EntityList
        items={items}
        emptyMessage="vacío"
        renderItem={renderRow}
        onSelect={onSelect}
        selectLabel="Ver Metas"
      />,
    );

    const row = screen.getByRole("listitem");
    await userEvent.click(within(row).getByRole("button", { name: /ver metas/i }));

    expect(onSelect).toHaveBeenCalledTimes(1);
    expect(onSelect).toHaveBeenCalledWith(items[0]);
  });

  it("no muestra botones de drill-down cuando se omite onSelect (nivel hoja)", () => {
    const items: Row[] = [{ id: 1, nombre: "Actividad" }];

    render(
      <EntityList items={items} emptyMessage="vacío" renderItem={renderRow} />,
    );

    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });
});
