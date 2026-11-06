// Detección del marcador DEMO_DATA en campos del frontend (tarea 20.2).
//
// Estrategia proporcional (design.md §DEMO_DATA, Req 10): el backend siembra
// datos de desarrollo prefijando los campos de texto con un marcador legible
// `"[DEMO_DATA] "`. El frontend NO genera datos sintéticos; únicamente detecta
// ese marcador para avisar que un dato es de demostración y no información
// oficial de SAO (Req 10.2, 10.3).

/** Marcador textual legible que el seed de desarrollo antepone a los campos. */
export const DEMO_DATA_MARKER = "[DEMO_DATA]";

/** Mensaje visible cuando un dato está marcado como de demostración (Req 10.2). */
export const DEMO_DATA_MESSAGE =
  "Datos de demostración — no es información oficial de SAO";

/**
 * Indica si un valor contiene el marcador DEMO_DATA.
 *
 * Acepta un único valor o una lista de valores (p. ej. varios campos de una
 * entidad); devuelve `true` si cualquiera de ellos contiene el marcador.
 * Los valores que no son cadenas (null, undefined, números) se ignoran, de
 * modo que la función nunca lanza y no inventa información.
 */
export function isDemoData(value: unknown | readonly unknown[]): boolean {
  const values = Array.isArray(value) ? value : [value];
  return values.some(
    (candidate) =>
      typeof candidate === "string" && candidate.includes(DEMO_DATA_MARKER),
  );
}
