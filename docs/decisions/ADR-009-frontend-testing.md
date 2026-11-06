# ADR-009 — Librería de testing del frontend

- **Estado:** Aceptada
- **Fecha:** 2026-10-01
- **Ámbito:** Pruebas automatizadas de la interfaz (React + TypeScript) del
  proyecto SAO ENCA 2030.
- **Relación:** Resuelve el punto que quedaba `PENDING_VALIDATION` en `tech.md`
  §22 y en ADR-001 ("Testing de frontend: librería/framework concreto"). No
  modifica el resto del stack definido en ADR-001.

---

## Contexto

El stack de frontend está definido (React + TypeScript sobre Vite; ADR-001,
`tech.md` §6, §39), pero la librería/framework concreto de **testing del
frontend** permanecía `PENDING_VALIDATION` (`tech.md` §22). Al implementar las
pruebas de las vistas y componentes (Req 7.x del spec `enca-strategy-tracking`,
tarea 23.1) era necesario fijar esa decisión. El equipo la aprobó
explícitamente, por lo que deja de ser una suposición.

---

## Problema

Se necesita una herramienta de pruebas que:

- Se integre de forma natural con el toolchain existente (Vite + TypeScript),
  evitando una cadena de build de pruebas separada.
- Permita probar componentes y vistas React centrándose en el comportamiento
  observable por el usuario (no en detalles internos de implementación).
- Sea deterministas y ejecutable localmente, sin depender de un backend real.

---

## Opciones consideradas

- **Vitest + React Testing Library** (elegida): runner nativo del ecosistema
  Vite; reutiliza la misma configuración/transformaciones del build; API de
  aserciones compatible con el estilo de Jest; integra `@testing-library/*` para
  pruebas centradas en el usuario.
- **Jest + React Testing Library:** maduro y muy extendido, pero requiere
  configuración y transformadores adicionales para alinearse con Vite/ESM y TS,
  duplicando parte del toolchain ya resuelto por Vite.
- **Playwright / Cypress (E2E):** valiosos para flujos end-to-end en navegador
  real, pero fuera del alcance de las pruebas de componentes/vistas de esta
  tarea; podrán considerarse más adelante como complemento, no sustituto.

---

## Decisión

Se adopta para las pruebas de componentes y vistas del frontend:

| Pieza                         | Herramienta                     |
| ----------------------------- | ------------------------------- |
| Test runner                   | Vitest                          |
| Entorno DOM                   | jsdom                           |
| Utilidades de pruebas de UI   | @testing-library/react          |
| Matchers de DOM               | @testing-library/jest-dom       |
| Simulación de interacción     | @testing-library/user-event     |

Configuración: bloque `test` en `vite.config.ts` (`environment: "jsdom"`,
`globals: true`, `setupFiles: ["./src/test/setup.ts"]`); archivos `*.test.ts(x)`
co-ubicados junto al código; scripts `npm test` (`vitest run`) y
`npm run test:watch`.

Las pruebas **mockean la capa de servicios** (`src/services`) con los dobles de
Vitest, de modo que son deterministas y no consultan un backend real.

---

## Justificación

- **Integración con Vite:** Vitest reutiliza el pipeline y las transformaciones
  del propio Vite, evitando mantener una configuración de pruebas paralela
  (coherente con "la tecnología debe servir al problema", `tech.md` §40, y con
  evitar sobreingeniería, `tech.md` §33).
- **Pruebas centradas en el usuario:** React Testing Library favorece consultas
  por rol y texto accesible, lo que hace las pruebas robustas frente a cambios
  internos y refuerza la accesibilidad.
- **Simetría con backend:** el backend ya usa pytest (ADR-001); fijar un runner
  estándar también en frontend completa la estrategia de pruebas del proyecto.

---

## Consecuencias

### Positivas

- Las vistas y componentes quedan cubiertos por pruebas automatizadas de los
  Req 7.x (listas, carga/vacío/error, timeout de 30 s, "Sin información",
  `DemoDataBadge`, drill-down y regreso).
- `npm test` y `npm run build` se ejecutan localmente sin servicios externos.

### Negativas / limitaciones

- Añade dependencias de desarrollo (Vitest, jsdom, `@testing-library/*`) que
  deben mantenerse (versiones, seguridad).
- Las pruebas de componentes no sustituyen pruebas end-to-end en navegador real;
  si se requieren, se evaluará una herramienta E2E en una decisión posterior.

---

## Actualización del Steering

`tech.md` §22 debe dejar de marcar el testing de frontend como
`PENDING_VALIDATION` y reflejar esta decisión. La modificación del archivo de
Steering requiere indicación explícita (`tech.md` §36.6), por lo que se deja
anotada aquí para su actualización por quien corresponda.
