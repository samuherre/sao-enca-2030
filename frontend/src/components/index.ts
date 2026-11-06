// Punto de entrada de los componentes reutilizables del frontend (tarea 20.1).
//
// Reexporta los componentes de estado (carga, vacío, error) y el detalle de
// entidad, para que las vistas importen desde `../components` sin conocer el
// archivo concreto.

export { LoadingIndicator } from "./LoadingIndicator";
export { EmptyState } from "./EmptyState";
export { ErrorBanner } from "./ErrorBanner";
export {
  EntityDetail,
  NO_INFO_LABEL,
  type EntityField,
} from "./EntityDetail";
export { DemoDataBadge } from "./DemoDataBadge";
export type { DemoDataBadgeProps } from "./DemoDataBadge";
export { CreateEntityForm } from "./CreateEntityForm";
export type {
  CreateFormField,
  CreateFormValues,
} from "./CreateEntityForm";
export { EntityList } from "./EntityList";
export type { EntityListItem } from "./EntityList";
