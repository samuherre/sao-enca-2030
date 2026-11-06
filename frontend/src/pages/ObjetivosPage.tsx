// Vista de Objetivos SMART de una Meta (tarea 21.3).
//
// Lista los Objetivos de la Meta seleccionada (drill-down desde `MetasPage`,
// Req 7.3). Si la Meta no tiene Objetivos, muestra un mensaje contextual
// (Req 7.4). Incluye un formulario para crear un Objetivo bajo la Meta
// (Req 7.6). Al seleccionar un Objetivo se profundiza a sus Indicadores
// (`onSelectObjetivo`). El regreso al nivel superior lo gestiona el App shell.

import { useObjetivos } from "../hooks";
import { crearObjetivo } from "../services";
import type { Meta, Objetivo } from "../types";
import type { CreateFormField, CreateFormValues } from "../components";
import { LevelView } from "./LevelView";

interface ObjetivosPageProps {
  /** Meta padre cuyos Objetivos se listan y bajo la que se crean nuevos. */
  readonly meta: Meta;
  /** Drill-down: navega a los Indicadores del Objetivo seleccionado (Req 7.3). */
  readonly onSelectObjetivo: (objetivo: Objetivo) => void;
}

/** Campo del formulario de creación de Objetivo: solo `descripcion`. */
const CREATE_FIELDS: readonly CreateFormField[] = [
  { name: "descripcion", label: "Descripción", required: true, multiline: true },
];

export function ObjetivosPage({ meta, onSelectObjetivo }: ObjetivosPageProps) {
  const state = useObjetivos(meta.id);

  async function handleCreate(values: CreateFormValues) {
    await crearObjetivo(meta.id, { descripcion: values.descripcion });
  }

  return (
    <LevelView<Objetivo>
      title="Objetivos SMART"
      subtitle={`Objetivos de la Meta: ${meta.descripcion}`}
      state={state}
      emptyMessage="Esta Meta no tiene Objetivos. Crea el primero con el formulario."
      renderItem={(objetivo) => ({
        key: objetivo.id,
        title: objetivo.descripcion,
        fields: [{ label: "Descripción", value: objetivo.descripcion }],
        demoValues: [objetivo.descripcion],
      })}
      onSelect={onSelectObjetivo}
      selectLabel="Ver Indicadores"
      createTitle="Crear Objetivo"
      createFields={CREATE_FIELDS}
      onCreate={handleCreate}
    />
  );
}
