// Setup global de las pruebas de frontend (tarea 23.1).
//
// Framework: Vitest + React Testing Library (decisión aprobada por el equipo,
// que actualiza el anterior PENDING_VALIDATION de tech.md §22).
//
// Responsabilidades:
//   - Registrar los matchers de `@testing-library/jest-dom` (p. ej.
//     `toBeInTheDocument`, `toHaveTextContent`) para expresar aserciones
//     centradas en el usuario sobre el DOM.
//   - Limpiar el DOM renderizado después de cada prueba, para que las pruebas
//     sean deterministas e independientes entre sí.

import "@testing-library/jest-dom/vitest";
import { afterEach } from "vitest";
import { cleanup } from "@testing-library/react";

afterEach(() => {
  cleanup();
});
