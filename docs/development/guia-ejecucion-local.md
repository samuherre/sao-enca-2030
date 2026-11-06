# Guía de ejecución local — SAO ENCA 2030

Esta guía explica cómo dejar el proyecto corriendo en tu máquina (Windows) y qué
hacer cada vez que vuelvas a abrir el proyecto. Cubre tres piezas:

1. Backend — API FastAPI (backend/src/main.py).
2. Frontend — React + TypeScript con Vite (frontend/).
3. Bibliometría — pipelines que generan datasets en data/processed/ (entre ellos
   el conector de OpenAlex por API).

> El dashboard de bibliometría (pestaña Bibliometría) NO necesita base de datos:
> el backend lee los datasets ya procesados de data/processed/. PostgreSQL solo
> hace falta para los endpoints de la estructura ENCA
> (Eje -> Meta -> Objetivo -> Indicador -> Actividad).

---

## 0. Requisitos (solo la primera vez)

- Python 3.12+ (ya existe el entorno virtual del proyecto en .venv/).
- Node.js 18+ y npm (para el frontend; verificado con Node 24 / npm 11).
- PostgreSQL en local SOLO si vas a usar los endpoints de estructura ENCA. Para
  ver bibliometría no es necesario.

---

## 1. Primera vez / tras clonar o actualizar dependencias

Desde la raíz del repo, en PowerShell:

    .\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
    .\.venv\Scripts\python.exe -m pip install -r bibliometrics\requirements.txt

    cd frontend
    npm install
    cd ..

Variables de entorno (si aún no tienes los .env locales): copia los ejemplos y
complétalos (NO se versionan):

    copy .env.example .env
    copy frontend\.env.example frontend\.env

Valores presentes en este equipo:

- Raíz .env: DATABASE_URL de PostgreSQL, ENVIRONMENT, LOG_LEVEL,
  CORS_ALLOW_ORIGINS (vacío = orígenes de Vite por defecto). OPENALEX_MAILTO es
  OPCIONAL y NO es un secreto (polite pool de OpenAlex); si no la defines, el
  conector funciona igual.
- Frontend .env: VITE_API_URL=http://localhost:8000
---
## 2. Cada vez que abres el proyecto (arranque normal)

Necesitas DOS terminales abiertas en la raiz del repo.

### Terminal A - Backend (API)

    .\.venv\Scripts\python.exe -m uvicorn backend.src.main:app --reload --port 8000

- API: http://localhost:8000
- Swagger (docs interactivos): http://localhost:8000/docs
- Resumen bibliometrico: http://localhost:8000/bibliometria/resumen

### Terminal B - Frontend (dashboard)

    cd frontend
    npm run dev

- App: http://localhost:5173  (abre esta URL en el navegador)

Para detener cualquiera de los dos: Ctrl + C en su terminal.

---
## 3. Actualizar / regenerar datos de bibliometria (opcional)

Los pipelines corren SIN UI y escriben en data/processed/. El dashboard solo lee
esos resultados; no procesa nada al abrir una pagina.

### OpenAlex por API (consulta directa, un solo comando)

    .\.venv\Scripts\python.exe bibliometrics\pipelines\process_openalex_api.py --term "birds conservation"

- Varios terminos en una corrida: repite --term.
- Salida: data/processed/openalex/openalex_dataset_YYYY-MM-DD.(json|csv)
- Guia detallada: docs/user-guide/consultar-openalex-api.md
- Los terminos de busqueda son PROPUESTA del equipo a validar con SAO; el periodo
  2020-2030 y la carpeta de salida si estan definidos por el proyecto.

Tras regenerar un dataset, recarga la pestana Bibliometria del frontend (o vuelve
a pedir GET /bibliometria/resumen) para ver los cambios.

---
## 4. Ejecutar las pruebas

    .\.venv\Scripts\python.exe -m pytest tests -q
    .\.venv\Scripts\python.exe -m pytest tests -k openalex_api -q

Frontend:

    cd frontend
    npm test
    cd ..

Las pruebas de la capa HTTP usan un cliente simulado: ninguna toca la red real.

---
## 5. Problemas frecuentes

- ModuleNotFoundError (p. ej. requests): falto instalar los requirements. Repite el paso 1.
- El frontend no muestra datos / error de CORS: confirma que el backend esta en el
  puerto 8000 y que frontend/.env apunta a VITE_API_URL=http://localhost:8000
- Error de conexion a PostgreSQL: solo afecta a los endpoints de estructura ENCA.
  La pestana Bibliometria funciona sin base de datos.
- El dashboard no muestra OpenAlex: confirma que existe un .json en
  data/processed/openalex/ y recarga la pagina.
