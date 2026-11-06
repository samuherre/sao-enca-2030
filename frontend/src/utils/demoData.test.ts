// Pruebas de la utilidad de detección DEMO_DATA (tarea 23.1).
//
// Cubre la lógica que respalda Req 10.2 / 10.3: detectar el marcador textual
// legible "[DEMO_DATA]" en uno o varios campos, ignorando valores no textuales
// sin lanzar.

import { describe, expect, it } from "vitest";

import { DEMO_DATA_MARKER, isDemoData } from "./demoData";

describe("isDemoData", () => {
  it("detecta el marcador en una cadena simple", () => {
    expect(isDemoData(`${DEMO_DATA_MARKER} Eje`)).toBe(true);
  });

  it("detecta el marcador en cualquiera de varios valores", () => {
    expect(isDemoData(["real", `${DEMO_DATA_MARKER} desc`])).toBe(true);
  });

  it("devuelve false cuando ningún valor lleva el marcador", () => {
    expect(isDemoData(["Eje real", "Descripción oficial"])).toBe(false);
  });

  it("ignora valores no textuales sin lanzar", () => {
    expect(isDemoData([null, undefined, 123, {}])).toBe(false);
    expect(isDemoData(null)).toBe(false);
  });
});
