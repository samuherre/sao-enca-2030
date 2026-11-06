// Vista inicial: lista de Ejes estratégicos (tarea 21.1).
//
// Al abrir, solicita la lista de Ejes a la API y los muestra en una lista
// (Req 7.1). Si la API no devuelve ningún Eje, muestra un mensaje contextual en
// lugar de una lista vacía sin contexto (Req 7.2). Incluye un formulario para
// crear un Eje (Req 7.6). Al seleccionar un Eje se profundiza a sus Metas
// (drill-down, Req 7.3), delegado en `onSelectEje`.
//
// Es el nivel raíz: no tiene regreso a un nivel superior.

import { useEjes } from "../hooks";
import { crearEje } from "../services";
import type { Eje } from "../types";
import type { CreateFormField, CreateFormValues } from "../components";
import { LevelView } from "./LevelView";

interface EjesPageProps {
  /** Drill-down: navega a las Metas del Eje seleccionado (Req 7.3). */
  readonly onSelectEje: (eje: Eje) => void;
}

/** Campos del formulario de creación de Eje: `nombre` obligatorio, `descripcion` opcional. */
const CREATE_FIELDS: readonly CreateFormField[] = [
  { name: "nombre", label: "Nombre", required: true },
  { name: "descripcion", label: "Descripción", required: false, multiline: true },
];

export function EjesPage({ onSelectEje }: EjesPageProps) {
  const state = useEjes();

  async function handleCreate(values: CreateFormValues) {
    await crearEje({
      nombre: values.nombre,
      // `descripcion` es opcional: solo se envía si el usuario la escribió.
      ...(values.descripcion ? { descripcion: values.descripcion } : {}),
    });
  }

  return (
    <LevelView<Eje>
      title="Ejes estratégicos"
      subtitle="Nivel superior de la estructura de seguimiento ENCA."
      state={state}
      emptyMessage="No hay Ejes disponibles. Crea el primero con el formulario."
      renderItem={(eje) => ({
        key: eje.id,
        title: eje.nombre,
        fields: [
          { label: "Nombre", value: eje.nombre },
          { label: "Descripción", value: eje.descripcion },
        ],
        demoValues: [eje.nombre, eje.descripcion],
      })}
      onSelect={onSelectEje}
      selectLabel="Ver Metas"
      createTitle="Crear Eje"
      createFields={CREATE_FIELDS}
      onCreate={handleCreate}
    />
  );
}
