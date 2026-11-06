// Configuración de entorno del frontend (SAO ENCA 2030).
//
// La URL base de la API se obtiene EXCLUSIVAMENTE de una variable de entorno,
// nunca de una ruta absoluta de máquina ni de un valor hardcodeado
// (structure.md §26, tech.md §19).
//
// Vite solo expone al cliente las variables con prefijo `VITE_`, por lo que la
// variable conceptual `API_URL` (structure.md/tech.md) se define como
// `VITE_API_URL`. Documentada en `frontend/.env.example`.

/** URL base de la API del backend (p. ej. http://localhost:8000). */
export const API_URL: string = import.meta.env.VITE_API_URL ?? "";

// --- Modo estático (DEMO sin backend) ---------------------------------------
//
// Para el despliegue de DEMOSTRACIÓN en Vercel no hay backend ni base de datos:
// el frontend lee un "snapshot" de la API congelado como archivos JSON en
// `public/api-snapshot/` (generado con `scripts/export_static_snapshot.py`).
//
// Se activa definiendo `VITE_STATIC_MODE=true` al compilar (así se hace en el
// build de Vercel, ver `frontend/.env.production`). En desarrollo local normal
// queda desactivado y la app consume la API real como siempre.
//
// Nota: este modo es solo para la demo de retroalimentación; la aplicación
// definitiva migrará a ArcGIS. En modo estático las acciones de ESCRITURA
// (crear entidades) se deshabilitan porque no hay servidor que las persista.
export const STATIC_MODE: boolean =
  (import.meta.env.VITE_STATIC_MODE ?? "").toString().toLowerCase() === "true";

/** Ruta base (relativa) del snapshot estático de la API dentro de `public/`. */
export const STATIC_SNAPSHOT_BASE = "/api-snapshot";
