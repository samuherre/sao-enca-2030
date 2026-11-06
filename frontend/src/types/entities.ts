// Tipos de los contratos de la API — entidades confirmadas (tarea 19.1).
//
// Estos tipos reflejan EXACTAMENTE los contratos `Response` del backend
// (FastAPI + Pydantic) definidos en `backend/src/schemas/` y en
// `design.md` ("Contratos Pydantic (schemas)"). La jerarquía confirmada es:
//
//     Eje → Meta → Objetivo SMART → Indicador → Actividad
//
// Reglas respetadas (design.md, Req 4.7, 5.8, 9.1, 9.2):
//   - Indicador y Actividad NO incluyen atributos PENDING_VALIDATION
//     (unidad de medida, valor objetivo/actual, fecha, fuente, estado,
//     responsable, evidencia, región). Esos campos no existen en esta versión.
//   - La referencia al padre viaja como `*_id` en cada Response de las entidades
//     hijas; el Eje (raíz) NO incluye referencia a padre (Req 6.3).
//   - El `id` es un entero autoincremental (clave técnica generada por
//     PostgreSQL), expuesto como identificador único de la entidad (Req 8.4).

/**
 * Eje estratégico (nivel 1 / raíz de la jerarquía).
 *
 * Refleja `EjeResponse`. No incluye referencia a padre: el Eje es la raíz.
 * `descripcion` es opcional en el dominio y puede ser nula.
 */
export interface Eje {
  readonly id: number;
  readonly nombre: string;
  readonly descripcion: string | null;
}

/** Meta (nivel 2). Refleja `MetaResponse`; `eje_id` referencia al Eje padre. */
export interface Meta {
  readonly id: number;
  readonly descripcion: string;
  readonly eje_id: number;
}

/**
 * Objetivo SMART (nivel 3). Refleja `ObjetivoResponse`; `meta_id` referencia
 * a la Meta padre.
 */
export interface Objetivo {
  readonly id: number;
  readonly descripcion: string;
  readonly meta_id: number;
}

/**
 * Indicador (nivel 4). Refleja `IndicadorResponse`; `objetivo_id` referencia
 * al Objetivo padre. SIN atributos PENDING_VALIDATION (Req 4.7, 9.1).
 */
export interface Indicador {
  readonly id: number;
  readonly nombre: string;
  readonly descripcion: string;
  readonly objetivo_id: number;
}

/**
 * Actividad (nivel 5 / hoja). Refleja `ActividadResponse`; `indicador_id`
 * referencia al Indicador padre. SIN atributos PENDING_VALIDATION (Req 5.8, 9.2).
 */
export interface Actividad {
  readonly id: number;
  readonly descripcion: string;
  readonly indicador_id: number;
}
