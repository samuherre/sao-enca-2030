# frontend/

Interfaz de usuario del proyecto SAO ENCA 2030.

## Estado

Proyecto **inicializado** con **React + TypeScript** sobre **Vite** (ver
`tech.md` §6, §7, §39 y `docs/decisions/ADR-001-stack-tecnologico.md`).

- **React + TypeScript** (stack DEFINIDO).
- **Vite** como herramienta de build/dev server (decisión técnica estándar para
  React + TS; sustituible si el equipo lo justifica).
- **Lovable** puede usarse como acelerador de UI (prototipado/componentes), NO
  como fuente de verdad de la arquitectura. Todo código generado con Lovable
  debe revisarse antes de integrarse (`tech.md` §7).

**Testing del frontend (decisión tomada):** **Vitest + React Testing Library**
(aprobado por el equipo). Actualiza el anterior `PENDING_VALIDATION` de
`tech.md` §22. Ver la sección "Testing" más abajo y
`docs/decisions/ADR-009-frontend-testing.md`.

## Estructura (structure.md §5)

```text
frontend/
├── index.html
├── package.json
├── tsconfig*.json
├── vite.config.ts
├── .env.example
└── src/
    ├── main.tsx          # Punto de entrada
    ├── App.tsx           # Página base
    ├── config.ts         # Lectura de VITE_API_URL (API_URL)
    ├── index.css
    ├── components/
    ├── pages/
    ├── layouts/
    ├── services/
    ├── hooks/
    ├── types/
    └── utils/
```

## Configuración (variable de entorno de la API)

La URL base de la API se consume **exclusivamente** desde una variable de
entorno; no se hardcodea ni se usan rutas absolutas de máquina
(structure.md §26, tech.md §19).

Vite solo expone al cliente las variables con prefijo `VITE_`, así que la
variable conceptual `API_URL` se define como **`VITE_API_URL`**:

1. Copiar `.env.example` a `.env`.
2. Completar `VITE_API_URL` con la URL del backend local (p. ej.
   `http://localhost:8000`).

## Comandos

```bash
npm install        # instala dependencias
npm run dev        # servidor de desarrollo (Vite)
npm run build      # type-check (tsc) + build de producción
npm run preview    # sirve el build de producción
npm run typecheck  # solo verificación de tipos (tsc --noEmit)
npm test           # ejecuta las pruebas una vez (vitest run)
npm run test:watch # ejecuta las pruebas en modo watch (vitest)
```

## Testing

El framework de testing del frontend está **DEFINIDO** (decisión aprobada por el
equipo, que actualiza el anterior `PENDING_VALIDATION` de `tech.md` §22):

- **Vitest** como test runner (se integra con Vite y reutiliza el mismo
  pipeline/transformaciones del build; evita una herramienta de bundling de
  pruebas separada).
- **jsdom** como entorno DOM para las pruebas de componentes y vistas React.
- **@testing-library/react** + **@testing-library/jest-dom** +
  **@testing-library/user-event** para pruebas centradas en el comportamiento
  del usuario (consultas por rol/texto accesible, no por detalles internos).

Configuración:

- Bloque `test` en `vite.config.ts` (`environment: "jsdom"`, `globals: true`,
  `setupFiles: ["./src/test/setup.ts"]`).
- `src/test/setup.ts` registra los matchers de `jest-dom` y limpia el DOM entre
  pruebas.
- Convención de nombres: `*.test.ts` / `*.test.tsx` **co-ubicados** junto al
  código que prueban (`structure.md` §19 permite co-ubicación por cercanía).

Las pruebas **mockean la capa de servicios** (`src/services`) con los dobles de
Vitest, de modo que son deterministas y **no** consultan un backend real.
Cubren Req 7.x: listas, estados de carga/vacío/error, timeout de 30 s,
"Sin información", `DemoDataBadge` y la navegación drill-down con regreso.

## Ejecución local integrada (frontend + backend)

El frontend consume la API del backend desde el navegador (Req 7.1). Para una
sesión local completa (navegar Eje → … → Actividad, crear entidades y ver los
estados de carga/vacío/error, el timeout de 30 s y el `DemoDataBadge`):

1. **Backend** (desde la raíz del repositorio, con el entorno virtual activo y
   `DATABASE_URL` configurada en `.env`):
   - Aplicar migraciones: `alembic upgrade head`.
   - (Opcional, recomendado) Cargar datos de demostración:
     `python scripts/data/seed_demo_data.py` — inserta una jerarquía marcada con
     el prefijo `[DEMO_DATA]`, que activa el `DemoDataBadge` en la interfaz.
   - Arrancar la API: `uvicorn backend.src.main:app --reload` (por defecto en
     `http://localhost:8000`).

2. **CORS** (ya configurado): el backend permite por defecto el origen local de
   Vite (`http://localhost:5173` y `http://127.0.0.1:5173`), de modo que el
   navegador no bloquee las peticiones. Si el frontend se sirve en otro origen,
   definir `CORS_ALLOW_ORIGINS` en el `.env` del backend (lista separada por
   comas, sin secretos; ver `.env.example` raíz).

3. **Frontend** (desde `frontend/`):
   - Copiar `.env.example` a `.env` y fijar `VITE_API_URL=http://localhost:8000`
     (debe coincidir con el host/puerto donde corre uvicorn).
   - `npm install` y luego `npm run dev` (Vite en `http://localhost:5173`).

4. Abrir `http://localhost:5173`: la vista inicial solicita los Ejes a la API.
   Con el seed cargado se verá la jerarquía DEMO_DATA con su badge; sin datos, el
   mensaje contextual de colección vacía.

> Nota: si `VITE_API_URL` queda vacía, la app muestra un aviso y no consulta
> datos. Si el backend no responde en 30 s, la petición se aborta y se muestra un
> mensaje de error conservando la última vista válida (Req 7.7, 7.8).

## Navegación (drill-down con regreso)

Las cinco vistas por nivel (Ejes → Metas → Objetivos → Indicadores →
Actividades) se conectan en un flujo de drill-down con regreso (Req 7.3, 7.6).

**Decisión técnica:** la navegación se implementa por **estado en memoria**
(una pila de niveles en `App.tsx`) con **migas de pan** para regresar; **no** se
añade `react-router-dom`. El drill-down es estrictamente lineal y cada nivel
necesita la entidad padre ya seleccionada (disponible en memoria), por lo que un
router sería sobreingeniería en el alcance actual (`tech.md` §33, §40). Si en el
futuro se requieren enlaces profundos o URLs compartibles, podrá incorporarse un
router con versión fijada sin cambiar las vistas.

## Responsabilidades (conceptuales, según structure.md §5)

- Presentación de información.
- Navegación.
- Formularios, filtros, tablas, gráficos, dashboard.
- Estados de carga y mensajes de error.
- Interacción con la API.

## No debe contener

- Consultas directas a la base de datos.
- Lógica de clasificación.
- Procesamiento masivo de artículos.
- Reglas críticas de negocio que deban mantenerse en el backend.

## Pendiente antes de ampliar

- Definir herramientas de visualización concretas.
- Validar con SAO los requisitos de interfaz y las dimensiones del dashboard.
