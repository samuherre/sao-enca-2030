// Vista de Indicadores de un Objetivo (tarea 21.4).
//
// Lista los Indicadores del Objetivo seleccionado (drill-down desde
// `ObjetivosPage`, Req 7.3). Si el Objetivo no tiene Indicadores, muestra un
// mensaje contextual (Req 7.4). Incluye un formulario para crear un Indicador
// bajo el Objetivo (Req 7.6). Al seleccionar un Indicador se profundiza a sus
// Actividades (`onSelectIndicador`). El regreso lo gestiona el App shell.
//
// IMPORTANTE (Req 4.7, 9.1): el Indicador NO expone atributos PENDING_VALIDATION
// (unidad de medida, valor objetivo/actual, fecha, fuente, estado). Solo se
// muestran y capturan los campos confirmados: `nombre` y `descripcion`.

import { useIndicadores } from "../hooks";
import { crearIndicador } from "../services";
import type { Indicador, Objetivo } from "../types";
import type { CreateFormField, CreateFormValues } from "../components";
import { LevelView } from "./LevelView";

interface IndicadoresPageProps {
  /** Objetivo padre cuyos Indicadores se listan y bajo el que se crean nuevos. */
  readonly objetivo: Objetivo;
  /** Drill-down: navega a las Actividades del Indicador seleccionado (Req 7.3). */
  readonly onSelectIndicador: (indicador: Indicador) => void;
}

/**
 * Campos del formulario de creación de Indicador: `nombre` y `descripcion`
 * obligatorios. Sin atributos PENDING_VALIDATION (Req 4.7).
 */
const CREATE_FIELDS: readonly CreateFormField[] = [
  { name: "nombre", label: "Nombre", required: true },
  { name: "descripcion", label: "Descripción", required: true, multiline: true },
];

export function IndicadoresPage({ objetivo, onSelectIndicador }: IndicadoresPageProps) {
  const state = useIndicadores(objetivo.id);

  async function handleCreate(values: CreateFormValues) {
    await crearIndicador(objetivo.id, {
      nombre: values.nombre,
      descripcion: values.descripcion,
    });
  }

  return (
    <LevelView<Indicador>
      title="Indicadores"
      subtitle={`Indicadores del Objetivo: ${objetivo.descripcion}`}
      state={state}
      emptyMessage="Este Objetivo no tiene Indicadores. Crea el primero con el formulario."
      renderItem={(indicador) => ({
        key: indicador.id,
        title: indicador.nombre,
        // Solo campos confirmados: sin atributos PENDING_VALIDATION (Req 4.7).
        fields: [
          { label: "Nombre", value: indicador.nombre },
          { label: "Descripción", value: indicador.descripcion },
        ],
        demoValues: [indicador.nombre, indicador.descripcion],
      })}
      onSelect={onSelectIndicador}
      selectLabel="Ver Actividades"
      createTitle="Crear Indicador"
      createFields={CREATE_FIELDS}
      onCreate={handleCreate}
    />
  );
}
