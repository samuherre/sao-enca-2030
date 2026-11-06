// Vista genérica de un nivel de la jerarquía (tarea 21).
//
// Las cinco vistas por nivel (Ejes, Metas, Objetivos, Indicadores, Actividades)
// comparten exactamente la misma estructura: título del nivel, estado de carga,
// estado de error (con reintento), lista de hijos (o mensaje contextual si está
// vacía) y un formulario de creación. `LevelView` encapsula ese patrón para
// implementar las cinco páginas de forma CONSISTENTE sin duplicar la lógica de
// estados (Req 7.2, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9).
//
// `LevelView` NO carga datos ni crea entidades: recibe el estado del hook
// (`loading`/`data`/`error`/`reload`) y la configuración de lista y formulario,
// y delega la navegación de regreso en quien la usa (el App shell).

import { STATIC_MODE } from "../config";
import type { AsyncDataState } from "../hooks";
import {
  CreateEntityForm,
  EntityList,
  LoadingIndicator,
  ErrorBanner,
  type CreateFormField,
  type CreateFormValues,
  type EntityListItem,
} from "../components";

interface LevelViewProps<T> {
  /** Título del nivel (p. ej. "Ejes estratégicos" o "Metas de …"). */
  readonly title: string;
  /** Subtítulo opcional de contexto (p. ej. el nombre del padre seleccionado). */
  readonly subtitle?: string;
  /** Estado de carga de la colección de este nivel (de un hook `useAsyncData`). */
  readonly state: AsyncDataState<T[]>;
  /** Mensaje contextual cuando la colección está vacía (Req 7.2 / 7.4). */
  readonly emptyMessage: string;
  /** Deriva la descripción visual de cada entidad para la lista. */
  readonly renderItem: (item: T) => EntityListItem;
  /**
   * Acción de drill-down al nivel inferior (Req 7.3). Se omite en el nivel hoja
   * (Actividades), donde no hay nivel inferior al que navegar.
   */
  readonly onSelect?: (item: T) => void;
  /** Etiqueta del botón de drill-down (por defecto definido por `EntityList`). */
  readonly selectLabel?: string;
  /** Título del formulario de creación (p. ej. "Crear Eje"). */
  readonly createTitle: string;
  /** Campos del formulario de creación. */
  readonly createFields: readonly CreateFormField[];
  /**
   * Acción de creación: llama al cliente API. Al resolverse, se recarga la
   * colección para reflejar el nuevo elemento.
   */
  readonly onCreate: (values: CreateFormValues) => Promise<void>;
}

/**
 * Renderiza un nivel completo: encabezado, estados (carga/error), lista de hijos
 * y formulario de creación.
 *
 * El error NO reemplaza la última vista válida: si ya hay datos cargados, se
 * siguen mostrando y el banner de error aparece encima (coherente con Req 7.8,
 * que exige conservar la última vista válida ante un timeout).
 */
export function LevelView<T>({
  title,
  subtitle,
  state,
  emptyMessage,
  renderItem,
  onSelect,
  selectLabel,
  createTitle,
  createFields,
  onCreate,
}: LevelViewProps<T>) {
  const { loading, data, error, reload } = state;

  // Tras crear una entidad con éxito, recarga la colección del nivel.
  async function handleCreate(values: CreateFormValues) {
    await onCreate(values);
    reload();
  }

  return (
    <section>
      <header style={{ marginBottom: "0.5rem" }}>
        <h2 style={{ margin: 0 }}>{title}</h2>
        {subtitle ? (
          <p style={{ margin: "0.25rem 0 0", color: "#555" }}>{subtitle}</p>
        ) : null}
      </header>

      {/* Error: se muestra sin descartar los datos previos (última vista válida). */}
      {error ? <ErrorBanner error={error} onRetry={reload} /> : null}

      {/* Carga: solo cuando aún no hay datos que mostrar (Req 7.7). */}
      {loading && data === null ? (
        <LoadingIndicator />
      ) : data !== null ? (
        <EntityList<T>
          items={data}
          emptyMessage={emptyMessage}
          renderItem={renderItem}
          onSelect={onSelect}
          selectLabel={selectLabel}
        />
      ) : null}

      {/* En la demo estática (solo lectura) no se muestra el formulario de
          creación: no hay backend que persista los datos (STATIC_MODE). */}
      {STATIC_MODE ? null : (
        <CreateEntityForm
          title={createTitle}
          fields={createFields}
          onSubmit={handleCreate}
        />
      )}
    </section>
  );
}
