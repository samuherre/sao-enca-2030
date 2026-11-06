// Tipos del árbol jerárquico anidado (tarea 19.1).
//
// Reflejan el contrato `EjeArbolResponse` del backend (`backend/src/schemas/arbol.py`,
// design.md "Schema del árbol jerárquico"), devuelto por `GET /ejes/{id}/arbol`.
//
// En el árbol la referencia al padre es IMPLÍCITA por el anidamiento, por lo que
// los nodos anidados OMITEN el `*_id` del padre para evitar redundancia. Cada
// lista de hijos puede ser vacía (`[]`) cuando el nodo no tiene hijos (Req 6.4).
// Indicador y Actividad no incluyen atributos PENDING_VALIDATION.

/** Nodo hoja del árbol: Actividad (nivel 5). */
export interface ActividadArbol {
  readonly id: number;
  readonly descripcion: string;
}

/** Nodo del árbol: Indicador (nivel 4) con sus Actividades. */
export interface IndicadorArbol {
  readonly id: number;
  readonly nombre: string;
  readonly descripcion: string;
  readonly actividades: ActividadArbol[];
}

/** Nodo del árbol: Objetivo SMART (nivel 3) con sus Indicadores. */
export interface ObjetivoArbol {
  readonly id: number;
  readonly descripcion: string;
  readonly indicadores: IndicadorArbol[];
}

/** Nodo del árbol: Meta (nivel 2) con sus Objetivos. */
export interface MetaArbol {
  readonly id: number;
  readonly descripcion: string;
  readonly objetivos: ObjetivoArbol[];
}

/**
 * Nodo raíz del árbol: Eje (nivel 1) con sus Metas.
 *
 * No incluye referencia a padre (el Eje es la raíz, Req 6.3). `descripcion`
 * puede ser nula.
 */
export interface EjeArbol {
  readonly id: number;
  readonly nombre: string;
  readonly descripcion: string | null;
  readonly metas: MetaArbol[];
}
