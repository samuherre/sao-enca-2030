/// <reference types="vitest/config" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Configuración de Vite para el frontend de SAO ENCA 2030 (React + TypeScript).
// La URL base de la API se consume en tiempo de ejecución mediante la variable
// de entorno VITE_API_URL (ver src/config.ts y .env.example). No se incluyen
// rutas absolutas de máquina (structure.md §26).
//
// Testing (tarea 23.1): framework seleccionado por el equipo (user-approved,
// actualiza el anterior PENDING_VALIDATION de tech.md §22):
//   - Vitest como runner (integrado con Vite, mismo pipeline de build).
//   - jsdom como entorno DOM para las pruebas de componentes/vistas React.
//   - @testing-library/react + jest-dom para pruebas centradas en el usuario.
// El archivo `src/test/setup.ts` registra los matchers de jest-dom y limpia el
// DOM entre pruebas.
export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    css: false,
    include: ["src/**/*.{test,spec}.{ts,tsx}"],
    restoreMocks: true,
    clearMocks: true,
  },
});
