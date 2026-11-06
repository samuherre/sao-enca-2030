# Despliegue de DEMO en Vercel (frontend estático)

Esta guía explica cómo está montada la **demo de solo lectura** que se publica
en Vercel para que SAO pueda revisar la interfaz y dar retroalimentación.

> **Importante:** esta demo NO es la aplicación definitiva. El destino final del
> producto es ArcGIS. La demo solo sirve para mostrar el aspecto y el contenido
> actuales (qué quitar, modificar o agregar) mediante un enlace compartible,
> sin necesidad de servidor ni base de datos.

## Cómo funciona

La aplicación real tiene tres piezas: frontend React, API FastAPI y PostgreSQL.
Para la demo se despliega **solo el frontend**, que lee un **snapshot** de la API
congelado como archivos JSON estáticos.

- El snapshot vive en `frontend/public/api-snapshot/` y replica las rutas de la
  API (p. ej. `/ejes` → `ejes.json`, `/ejes/1/metas` → `ejes/1/metas.json`).
- El "modo estático" se activa con la variable `VITE_STATIC_MODE=true`, definida
  en `frontend/.env.production`. Con ese flag, la capa HTTP del frontend
  (`src/services/http.ts`) lee del snapshot en vez de llamar a un backend.
- Las acciones de escritura (crear entidades, consulta en vivo a GBIF) quedan
  deshabilitadas en la demo, porque no hay servidor que las ejecute.

## Regenerar el snapshot (cuando cambien los datos)

Si actualizas los datos y quieres reflejarlos en la demo:

1. Levanta el backend local:

   ```powershell
   .\.venv\Scripts\python -m uvicorn backend.src.main:app --port 8000
   ```

2. Regenera el snapshot:

   ```powershell
   .\.venv\Scripts\python scripts\export_static_snapshot.py
   ```

3. Haz commit de los cambios en `frontend/public/api-snapshot/` y súbelos. Si el
   repo está conectado a Vercel, el redeploy es automático.

## Publicar en Vercel

El repositorio incluye `vercel.json` en la raíz, que indica a Vercel cómo
construir el frontend (que vive en la subcarpeta `frontend/`):

- `buildCommand`: `cd frontend && npm install && npm run build`
- `outputDirectory`: `frontend/dist`

Pasos (una sola vez):

1. Sube el repositorio a GitHub.
2. En https://vercel.com, inicia sesión con GitHub e **Import Project**.
3. Selecciona el repositorio. Vercel detecta `vercel.json` automáticamente; no
   hace falta configurar variables de entorno (el modo estático ya está en
   `.env.production`).
4. Deploy. Vercel entrega una URL pública (`https://<proyecto>.vercel.app`) que
   puedes compartir.

Cada push a la rama principal genera un nuevo despliegue automáticamente.

## Probar la demo en local (igual que en Vercel)

```powershell
cd frontend
npm run build
npm run preview
```

Abre la URL que imprime `preview` (por defecto http://localhost:4173). Debe
mostrar las tres secciones (Seguimiento ENCA, Bibliometría, Biodiversidad) con
el aviso de "versión de demostración" y sin formularios de creación.
