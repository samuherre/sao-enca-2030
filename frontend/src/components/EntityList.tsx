// Lista reutilizable de entidades (tarea 21).
//
// Renderiza una colección de entidades de cualquier nivel de la jerarquía
// (Ejes, Metas, Objetivos, Indicadores, Actividades). Si la colección está
// vacía muestra un mensaje contextual mediante `EmptyState`, en lugar de una
// lista en blanco sin contexto (Req 7.2 para Ejes; Req 7.4 para hijos).
//
// Cada elemento muestra sus CAMPOS CONFIRMADOS mediante `EntityDetail` (que
// indica "Sin información" para los valores nulos/vacíos, Req 7.5) y, cuando el
// contenido lleva el marcador `[DEMO_DATA]`, el `DemoDataBadge` (Req 10.2).
//
// Si quien usa el componente proporciona `onSelect`, cada elemento se vuelve
// seleccionable para profundizar al nivel inferior (drill-down, Req 7.3). El
// componente NO carga datos ni contiene lógica de negocio: recibe la colección
// ya cargada por los hooks.

import type { ReactNode } from "react";

import { DemoDataBadge } from "./DemoDataBadge";
import { EmptyState } from "./EmptyState";
import { EntityDetail, type EntityField } from "./EntityDetail";

/** Descripción visual de un elemento de la lista, derivada de una entidad `T`. */
export interface EntityListItem {
  /** Clave estable del elemento (normalmente el `id` de la entidad). */
  readonly key: number | string;
  /** Título principal del elemento (p. ej. el nombre o la descripción). */
  readonly title: string;
  /** Campos confirmados a mostrar bajo el título (se muestran con EntityDetail). */
  readonly fields: readonly EntityField[];
  /**
   * Valores a inspeccionar para detectar el marcador DEMO_DATA. Suele ser el
   * conjunto de campos de texto de la entidad.
   */
  readonly demoValues: readonly unknown[];
}

interface EntityListProps<T> {
  /** Colección de entidades a mostrar (puede ser `[]`). */
  readonly items: readonly T[];
  /** Mensaje contextual cuando la colección está vacía (Req 7.2 / 7.4). */
  readonly emptyMessage: string;
  /** Deriva la descripción visual de cada entidad. */
  readonly renderItem: (item: T) => EntityListItem;
  /**
   * Acción de drill-down opcional: si se proporciona, al seleccionar un
   * elemento se navega al nivel inferior (Req 7.3). Si se omite (nivel hoja,
   * Actividad), los elementos no son seleccionables.
   */
  readonly onSelect?: (item: T) => void;
  /** Etiqueta del botón de drill-down (por defecto "Ver detalle"). */
  readonly selectLabel?: string;
}

const cardStyle: React.CSSProperties = {
  padding: "0.75rem 1rem",
  border: "1px solid #e0e0e0",
  borderRadius: "0.375rem",
  marginBottom: "0.5rem",
  backgroundColor: "#fff",
};

/**
 * Lista accesible de entidades con detalle de campos confirmados y, opcionalmente,
 * drill-down al nivel inferior.
 */
export function EntityList<T>({
  items,
  emptyMessage,
  renderItem,
  onSelect,
  selectLabel = "Ver detalle",
}: EntityListProps<T>): ReactNode {
  if (items.length === 0) {
    return <EmptyState message={emptyMessage} />;
  }

  return (
    <ul style={{ listStyle: "none", padding: 0, margin: "0.5rem 0" }}>
      {items.map((item) => {
        const view = renderItem(item);
        return (
          <li key={view.key} style={cardStyle}>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                gap: "1rem",
                marginBottom: "0.25rem",
              }}
            >
              <span style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <strong>{view.title}</strong>
                <DemoDataBadge value={view.demoValues} />
              </span>
              {onSelect ? (
                <button
                  type="button"
                  onClick={() => onSelect(item)}
                  style={{
                    flexShrink: 0,
                    padding: "0.35rem 0.75rem",
                    border: "1px solid #2a6f4b",
                    borderRadius: "0.25rem",
                    backgroundColor: "#fff",
                    color: "#2a6f4b",
                    cursor: "pointer",
                  }}
                >
                  {selectLabel}
                </button>
              ) : null}
            </div>
            <EntityDetail fields={view.fields} />
          </li>
        );
      })}
    </ul>
  );
}
