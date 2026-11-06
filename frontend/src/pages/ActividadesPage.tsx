// Vista de Actividades de un Indicador (tarea 21.5).
//
// Lista las Actividades del Indicador seleccionado (drill-down desde
// `IndicadoresPage`, Req 7.3). Si el Indicador no tiene Actividades, muestra un
// mensaje contextual (Req 7.4). Incluye un formulario para crear una Actividad
// bajo el Indicador (Req 7.6). Es el NIVEL HOJA: no hay nivel inferior, por lo
// que la lista no ofrece drill-down (no se pasa `onSelect`). El regreso al nivel
// superior lo gestiona el App shell.
//
// IMPORTANTE (Req 5.8, 9.2): la Actividad NO expone atributos PENDING_VALIDATION
// (responsable, fecha, estado, evidencia, región). Solo el campo confirmado
// `descripcion`.

import { useActividades } from "../hooks";
import { crearActividad } from "../services";
import type { Actividad, Indicador } from "../types";
import type { CreateFormField, CreateFormValues } from "../components";
import { LevelView } from "./LevelView";

interface ActividadesPageProps {
  /** Indicador padre cuyas Actividades se listan y bajo el que se crean nuevas. */
  readonly indicador: Indicador;
}

/** Campo del formulario de creación de Actividad: solo `descripcion` (sin PENDING_VALIDATION). */
const CREATE_FIELDS: readonly CreateFormField[] = [
  { name: "descripcion", label: "Descripción", required: true, multiline: true },
];

export function ActividadesPage({ indicador }: ActividadesPageProps) {
  const state = useActividades(indicador.id);

  async function handleCreate(values: CreateFormValues) {
    await crearActividad(indicador.id, { descripcion: values.descripcion });
  }

  return (
    <LevelView<Actividad>
      title="Actividades"
      subtitle={`Actividades del Indicador: ${indicador.nombre}`}
      state={state}
      emptyMessage="Este Indicador no tiene Actividades. Crea la primera con el formulario."
      renderItem={(actividad) => ({
        key: actividad.id,
        title: actividad.descripcion,
        // Solo campo confirmado: sin atributos PENDING_VALIDATION (Req 5.8).
        fields: [{ label: "Descripción", value: actividad.descripcion }],
        demoValues: [actividad.descripcion],
      })}
      // Nivel hoja: sin drill-down (no se pasa onSelect).
      createTitle="Crear Actividad"
      createFields={CREATE_FIELDS}
      onCreate={handleCreate}
    />
  );
}
