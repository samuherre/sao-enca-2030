// Pruebas de la capa HTTP de bajo nivel (tarea 23.1).
//
// Cubre el comportamiento del cliente que respalda las vistas:
//   - Req 7.8: una petición que supera el límite de 30 s se aborta y propaga un
//     ApiError de tipo "timeout" (manejable por la UI, que conserva la vista).
//   - Req 7.9: un error HTTP se normaliza a ApiError sin exponer el cuerpo crudo
//     fuera del campo controlado; un fallo de red se normaliza a "network".
//
// `fetch` se sustituye por un doble determinista; se usan timers falsos para
// disparar el timeout sin esperar 30 s reales.

import { afterEach, describe, expect, it, vi } from "vitest";

import { request, REQUEST_TIMEOUT_MS } from "./http";
import { ApiError } from "./apiError";

describe("request (capa HTTP)", () => {
  const originalFetch = globalThis.fetch;

  afterEach(() => {
    globalThis.fetch = originalFetch;
    vi.useRealTimers();
  });

  it("deserializa el cuerpo JSON en una respuesta correcta", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify([{ id: 1, nombre: "Eje" }]), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    ) as unknown as typeof fetch;

    const data = await request<Array<{ id: number }>>("/ejes");
    expect(data).toEqual([{ id: 1, nombre: "Eje" }]);
  });

  it("aborta y lanza ApiError('timeout') al superar los 30 s (Req 7.8)", async () => {
    vi.useFakeTimers();

    // `fetch` que solo rechaza cuando su señal se aborta (simula el navegador).
    globalThis.fetch = vi.fn(
      (_url: string, init?: RequestInit) =>
        new Promise((_resolve, reject) => {
          const signal = init?.signal;
          signal?.addEventListener("abort", () => {
            const err = new Error("The operation was aborted.");
            err.name = "AbortError";
            reject(err);
          });
        }),
    ) as unknown as typeof fetch;

    const promise = request("/ejes");
    // Evita un unhandled rejection mientras avanzamos el reloj.
    const assertion = expect(promise).rejects.toMatchObject({
      name: "ApiError",
      kind: "timeout",
    });

    // Dispara el temporizador de timeout de 30 s.
    await vi.advanceTimersByTimeAsync(REQUEST_TIMEOUT_MS);
    await assertion;
  });

  it("normaliza una respuesta HTTP de error a ApiError('http') con status y code (Req 7.9)", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ detail: "no existe", error: "not_found" }), {
        status: 404,
        headers: { "Content-Type": "application/json" },
      }),
    ) as unknown as typeof fetch;

    await expect(request("/ejes/999")).rejects.toMatchObject({
      kind: "http",
      status: 404,
      code: "not_found",
    });
  });

  it("normaliza un fallo de red a ApiError('network')", async () => {
    globalThis.fetch = vi
      .fn()
      .mockRejectedValue(new TypeError("Failed to fetch")) as unknown as typeof fetch;

    await expect(request("/ejes")).rejects.toBeInstanceOf(ApiError);
    await expect(request("/ejes")).rejects.toMatchObject({ kind: "network" });
  });
});
