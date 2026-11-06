// Tipos de las cargas útiles de creación (Create) — tarea 19.1.
//
// Reflejan los contratos `*Create` del backend (`backend/src/schemas/`,
// design.md "Contratos Pydantic (schemas)"). Reglas:
//   - La referencia al padre NO viaja en el cuerpo del Create: se toma de la
//     ruta anidada (p. ej. `POST /ejes/{eje_id}/metas`). Por eso ningún payload
//     de creación de entidad hija incluye el `*_id` del padre.
//   - Los campos obligatorios de texto no pueden ser vacíos (el backend los
//     rechaza con 422 tras recortar espacios).
//   - El backend prohíbe campos extra (enviar atributos no reconocidos → 422),
//     por lo que estos tipos declaran únicamente los campos aceptados.

/** Cuerpo para crear un Eje: `nombre` obligatorio, `descripcion` opcional. */
export interface EjeCreate {
  readonly nombre: string;
  readonly descripcion?: string;
}

/** Cuerpo para crear una Meta bajo un Eje: solo `descripcion` (padre en la ruta). */
export interface MetaCreate {
  readonly descripcion: string;
}

/** Cuerpo para crear un Objetivo bajo una Meta: solo `descripcion`. */
export interface ObjetivoCreate {
  readonly descripcion: string;
}

/**
 * Cuerpo para crear un Indicador bajo un Objetivo: `nombre` y `descripcion`
 * obligatorios. Sin atributos PENDING_VALIDATION.
 */
export interface IndicadorCreate {
  readonly nombre: string;
  readonly descripcion: string;
}

/**
 * Cuerpo para crear una Actividad bajo un Indicador: solo `descripcion`.
 * Sin atributos PENDING_VALIDATION.
 */
export interface ActividadCreate {
  readonly descripcion: string;
}
