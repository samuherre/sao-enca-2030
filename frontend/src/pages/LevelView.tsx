// Vista genérica de un nivel de la jerarquía (tarea 21).
//
// Las cinco vistas por nivel (Ejes, Metas, Objetivos, Indicadores, Actividades)
// comparten exactamente la misma estructura: título del nivel, estado de carga,
// estado de error (con reintento) y lista de hijos (o mensaje contextual si
// está vacía). `LevelView` encapsula ese patrón para implementar las cinco
// páginas de forma CONSISTENTE sin duplicar la lógica de estados (Req 7.2,
// 7.4, 7.5, 7.7, 7.8, 7.9).
//
// SOLO VISUALIZACIÓN (decisión de SAO): la vista de Seguimiento ENCA muestra la
// estructura oficial de la ENCA para el público; NO se edita desde la web. Por
// eso este componente ya NO renderiza formulario de creación. Los datos se
// cargan desde el Excel oficial de SAO con el script
// `scripts/data/importar_enca_excel.py`. Las props de creación se conservan como
// OPCIONALES y OBSOLETAS solo para no romper las páginas que todavía las pasan;
// se ignoran y pueden retirarse cuando se limpien las 5 páginas.
//
// `LevelView` NO carga datos: recibe el estado del hook
// (`loading`/`data`/`error`/`reload`) y la configuración de lista, y delega la
// navegación de regreso en quien la usa (el App shell).

import type { AsyncDataState } from "../hooks";
import {
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
  /** @deprecated Solo visualización: ya no se usa. Se conserva por compatibilidad. */
  readonly createTitle?: string;
  /** @deprecated Solo visualización: ya no se usa. Se conserva por compatibilidad. */
  readonly createFields?: readonly CreateFormField[];
  /** @deprecated Solo visualización: ya no se usa. Se conserva por compatibilidad. */
  readonly onCreate?: (values: CreateFormValues) => Promise<void>;
}

/**
 * Renderiza un nivel completo de SOLO LECTURA: encabezado, estados (carga/error)
 * y lista de hijos (con drill-down).
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
}: LevelViewProps<T>) {
  const { loading, data, error, reload } = state;

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
    </section>
  );
}
