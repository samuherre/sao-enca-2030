// Vista de Metas de un Eje (tarea 21.2).
//
// Lista las Metas del Eje seleccionado (drill-down desde `EjesPage`, Req 7.3).
// Si el Eje no tiene Metas, muestra un mensaje contextual (Req 7.4). Incluye un
// formulario para crear una Meta bajo el Eje (Req 7.6). Al seleccionar una Meta
// se profundiza a sus Objetivos (`onSelectMeta`). El regreso al nivel superior
// (Ejes) lo gestiona el App shell mediante las migas de pan.

import { useMetas } from "../hooks";
import { crearMeta } from "../services";
import type { Eje, Meta } from "../types";
import type { CreateFormField, CreateFormValues } from "../components";
import { LevelView } from "./LevelView";

interface MetasPageProps {
  /** Eje padre cuyas Metas se listan y bajo el que se crean nuevas Metas. */
  readonly eje: Eje;
  /** Drill-down: navega a los Objetivos de la Meta seleccionada (Req 7.3). */
  readonly onSelectMeta: (meta: Meta) => void;
}

/** Campo del formulario de creación de Meta: solo `descripcion` (el padre va en la ruta). */
const CREATE_FIELDS: readonly CreateFormField[] = [
  { name: "descripcion", label: "Descripción", required: true, multiline: true },
];

export function MetasPage({ eje, onSelectMeta }: MetasPageProps) {
  const state = useMetas(eje.id);

  async function handleCreate(values: CreateFormValues) {
    await crearMeta(eje.id, { descripcion: values.descripcion });
  }

  return (
    <LevelView<Meta>
      title="Metas"
      subtitle={`Metas del Eje: ${eje.nombre}`}
      state={state}
      emptyMessage="Este Eje no tiene Metas. Crea la primera con el formulario."
      renderItem={(meta) => ({
        key: meta.id,
        title: meta.descripcion,
        fields: [{ label: "Descripción", value: meta.descripcion }],
        demoValues: [meta.descripcion],
      })}
      onSelect={onSelectMeta}
      selectLabel="Ver Objetivos"
      createTitle="Crear Meta"
      createFields={CREATE_FIELDS}
      onCreate={handleCreate}
    />
  );
}
