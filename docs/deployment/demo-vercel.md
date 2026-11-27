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

2. Regenera el snapshot **completo** con el orquestador:

   ```powershell
   .\.venv\Scripts\python scripts\regenerar_snapshot_demo.py
   ```

3. Haz commit de los cambios en `frontend/public/api-snapshot/` y súbelos. Si el
   repo está conectado a Vercel, el redeploy es automático.

> **Importante — no uses `export_static_snapshot.py` a secas.** Ese script
> congela lo que devuelve el backend, pero la vista de biodiversidad tiene dos
> conjuntos de campos que el backend NO conoce y que se resuelven por API externa
> (GBIF/GADM) en post-proceso sobre el propio snapshot:
> `gbif_portal_key` (enlaces a GBIF por especie/familia/orden) y `gadm_gid`
> (enlaces por departamento). Ejecutar solo el export los deja en `null` y rompe
> esos enlaces en la demo. El orquestador `regenerar_snapshot_demo.py` hace el
> export y vuelve a añadir ambos campos en el orden correcto
> (`export_static_snapshot.py` → `data/resolver_claves_gbif_portal.py` →
> `data/resolver_gadm_departamentos.py`). Los pasos de GBIF/GADM requieren
> internet.

### Reflejar una re-ingesta de bibliometría en la demo

La distribución por OFC del dashboard se calcula a partir de los datasets
`data/processed/<fuente>_clasificado/`. Si re-ingieres una fuente, **antes** de
regenerar el snapshot hay que (re)clasificarla, o el gráfico de OFC quedará
desfasado o incompleto:

```powershell
.\.venv\Scripts\python bibliometrics\pipelines\classify_dataset.py --source <fuente>
```

(una vez por fuente con dataset nuevo o sin clasificar; p. ej. `openalex`,
`scielo`, `boletin_sao`, `google_scholar`). Luego ya sí regenera el snapshot con
el orquestador del paso anterior.

## Publicar en Vercel

**Clave:** se despliega SOLO la subcarpeta `frontend/`. El repo tiene varias
carpetas (`backend/`, `bibliometrics/`, `frontend/`); si se apunta Vercel a la
raíz, su detección automática intenta un despliegue "multiservicio" (backend +
frontend) que NO queremos para la demo. Por eso el `vercel.json` vive dentro de
`frontend/` y se configura el *Root Directory* en `frontend`.

Pasos (una sola vez):

1. Sube el repositorio a GitHub.
2. En https://vercel.com, inicia sesión con GitHub e **Import Project**.
3. Selecciona el repositorio.
4. En **Root Directory**, pulsa **Edit** y elige la carpeta **`frontend`**.
   Esto hace que Vercel trate el proyecto como una app Vite normal (no
   multiservicio).
5. El resto de ajustes (framework Vite, build `npm run build`, output `dist`) se
   detectan solos por el `vercel.json` de `frontend/`. No hace falta configurar
   variables de entorno (el modo estático ya está en `.env.production`).
6. **Deploy**. Vercel entrega una URL pública (`https://<proyecto>.vercel.app`).

> Si Vercel muestra un asistente de "proyecto multiservicio" y propone un
> `vercel.json` con una sección `services`, **no lo aceptes**: significa que está
> apuntando a la raíz. Vuelve atrás y fija el *Root Directory* en `frontend`.

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
