// Formulario reutilizable de creación de entidades (tarea 21).
//
// Un único formulario sirve para crear cualquiera de las cinco entidades de la
// jerarquía (Eje, Meta, Objetivo, Indicador, Actividad). Quien lo usa declara
// los campos a capturar y una función `onSubmit` que llama al cliente API.
//
// Responsabilidades (design.md "CreateEntityForm", Req 7.6):
//   - Validar LOCALMENTE que los campos obligatorios no queden vacíos tras
//     recortar espacios (coherente con la validación del backend, que rechaza
//     nulo/vacío/solo espacios con 422). Así se evita una llamada innecesaria.
//   - Enviar solo los campos declarados (el backend prohíbe campos extra).
//   - Traducir los errores de la API a mensajes amigables mediante `ErrorBanner`
//     (sin exponer trazas ni detalles técnicos, Req 7.9).
//   - No contiene lógica de negocio: delega la creación en `onSubmit`.

import { useState, type FormEvent } from "react";

import { ApiError } from "../services";
import { ErrorBanner } from "./ErrorBanner";

/** Definición de un campo del formulario. */
export interface CreateFormField {
  /** Clave del campo en el objeto de valores (p. ej. "nombre", "descripcion"). */
  readonly name: string;
  /** Etiqueta legible mostrada al usuario. */
  readonly label: string;
  /** Si el campo es obligatorio (no puede quedar vacío tras recortar). */
  readonly required: boolean;
  /** Si se renderiza como área de texto multilínea (por defecto, campo simple). */
  readonly multiline?: boolean;
}

/** Mapa de valores del formulario por clave de campo. */
export type CreateFormValues = Record<string, string>;

interface CreateEntityFormProps {
  /** Título del formulario (p. ej. "Crear Eje"). */
  readonly title: string;
  /** Campos a capturar, en orden. */
  readonly fields: readonly CreateFormField[];
  /** Texto del botón de envío (por defecto "Crear"). */
  readonly submitLabel?: string;
  /**
   * Acción de creación: recibe los valores recortados y debe llamar al cliente
   * API. Si la promesa se rechaza con `ApiError`, se muestra un mensaje
   * amigable. Si se resuelve, el formulario se limpia.
   */
  readonly onSubmit: (values: CreateFormValues) => Promise<void>;
}

/** Construye el estado inicial (todos los campos vacíos). */
function initialValues(fields: readonly CreateFormField[]): CreateFormValues {
  const values: CreateFormValues = {};
  for (const field of fields) {
    values[field.name] = "";
  }
  return values;
}

/**
 * Formulario de creación controlado y accesible.
 *
 * Mantiene su propio estado de valores, de envío en curso y de error. La
 * validación local marca los campos obligatorios vacíos sin llamar a la API.
 */
export function CreateEntityForm({
  title,
  fields,
  submitLabel = "Crear",
  onSubmit,
}: CreateEntityFormProps) {
  const [values, setValues] = useState<CreateFormValues>(() => initialValues(fields));
  const [submitting, setSubmitting] = useState(false);
  // Error de validación local por campo (clave → mensaje).
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  // Error de la API (o mensaje) tras un envío fallido.
  const [apiError, setApiError] = useState<ApiError | string | null>(null);

  function handleChange(name: string, value: string) {
    setValues((prev) => ({ ...prev, [name]: value }));
    // Limpia el error del campo en cuanto el usuario escribe algo.
    if (fieldErrors[name]) {
      setFieldErrors((prev) => {
        const next = { ...prev };
        delete next[name];
        return next;
      });
    }
  }

  /** Valida localmente los campos obligatorios; devuelve `true` si todo es válido. */
  function validate(): boolean {
    const errors: Record<string, string> = {};
    for (const field of fields) {
      if (field.required && values[field.name].trim().length === 0) {
        errors[field.name] = `El campo ${field.label} es obligatorio.`;
      }
    }
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setApiError(null);

    if (!validate()) {
      return;
    }

    // Envía solo los campos declarados, recortados; omite los opcionales vacíos.
    const payload: CreateFormValues = {};
    for (const field of fields) {
      const trimmed = values[field.name].trim();
      if (field.required || trimmed.length > 0) {
        payload[field.name] = trimmed;
      }
    }

    setSubmitting(true);
    try {
      await onSubmit(payload);
      // Éxito: limpia el formulario para una nueva creación.
      setValues(initialValues(fields));
    } catch (cause) {
      setApiError(cause instanceof ApiError ? cause : "No se pudo crear el elemento.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="create-entity-form" noValidate>
      <h3 style={{ margin: "0 0 0.5rem" }}>{title}</h3>

      {fields.map((field) => {
        const fieldId = `create-${field.name}`;
        const error = fieldErrors[field.name];
        return (
          <div key={field.name} style={{ marginBottom: "0.75rem" }}>
            <label
              htmlFor={fieldId}
              style={{ display: "block", fontWeight: 600, marginBottom: "0.25rem" }}
            >
              {field.label}
              {field.required ? <span aria-hidden="true"> *</span> : null}
            </label>
            {field.multiline ? (
              <textarea
                id={fieldId}
                value={values[field.name]}
                onChange={(e) => handleChange(field.name, e.target.value)}
                aria-invalid={error ? true : undefined}
                aria-describedby={error ? `${fieldId}-error` : undefined}
                rows={3}
                style={{ width: "100%", boxSizing: "border-box", padding: "0.4rem" }}
              />
            ) : (
              <input
                id={fieldId}
                type="text"
                value={values[field.name]}
                onChange={(e) => handleChange(field.name, e.target.value)}
                aria-invalid={error ? true : undefined}
                aria-describedby={error ? `${fieldId}-error` : undefined}
                style={{ width: "100%", boxSizing: "border-box", padding: "0.4rem" }}
              />
            )}
            {error ? (
              <span
                id={`${fieldId}-error`}
                role="alert"
                style={{ color: "#8a1f1f", fontSize: "0.85rem" }}
              >
                {error}
              </span>
            ) : null}
          </div>
        );
      })}

      {apiError ? <ErrorBanner error={apiError} /> : null}

      <button
        type="submit"
        disabled={submitting}
        style={{
          padding: "0.45rem 1rem",
          border: "1px solid #2a6f4b",
          borderRadius: "0.25rem",
          backgroundColor: submitting ? "#9ec7ad" : "#2a6f4b",
          color: "#fff",
          cursor: submitting ? "default" : "pointer",
        }}
      >
        {submitting ? "Creando…" : submitLabel}
      </button>
    </form>
  );
}
