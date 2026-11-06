// Migas de pan de navegación (tarea 21).
//
// Muestra la ruta de niveles visitados (Eje → Meta → Objetivo → Indicador →
// Actividad) y permite REGRESAR a cualquier nivel superior previamente visitado
// (Req 7.6). Cada miga anterior al nivel actual es un botón que, al pulsarse,
// vuelve a ese nivel; la miga del nivel actual se muestra como texto no
// interactivo.
//
// No contiene lógica de navegación: solo invoca `onNavigate(index)` para que el
// App shell recorte la pila de niveles al índice elegido.

interface Crumb {
  /** Etiqueta visible de la miga (p. ej. "Ejes" o el nombre del padre). */
  readonly label: string;
}

interface BreadcrumbProps {
  /** Migas en orden, de la raíz al nivel actual. */
  readonly crumbs: readonly Crumb[];
  /** Regresa al nivel del índice indicado (0 = raíz). */
  readonly onNavigate: (index: number) => void;
}

/**
 * Barra de migas de pan accesible.
 *
 * Usa `<nav aria-label>` y una lista ordenada; el último elemento se marca con
 * `aria-current="page"` para las tecnologías de asistencia.
 */
export function Breadcrumb({ crumbs, onNavigate }: BreadcrumbProps) {
  return (
    <nav aria-label="Ruta de navegación" style={{ margin: "0 0 1rem" }}>
      <ol
        style={{
          display: "flex",
          flexWrap: "wrap",
          alignItems: "center",
          gap: "0.25rem",
          listStyle: "none",
          padding: 0,
          margin: 0,
        }}
      >
        {crumbs.map((crumb, index) => {
          const isLast = index === crumbs.length - 1;
          return (
            <li key={index} style={{ display: "flex", alignItems: "center", gap: "0.25rem" }}>
              {isLast ? (
                <span aria-current="page" style={{ fontWeight: 600, color: "#1a1a1a" }}>
                  {crumb.label}
                </span>
              ) : (
                <button
                  type="button"
                  onClick={() => onNavigate(index)}
                  style={{
                    border: "none",
                    background: "none",
                    padding: 0,
                    color: "#2a6f4b",
                    cursor: "pointer",
                    textDecoration: "underline",
                    font: "inherit",
                  }}
                >
                  {crumb.label}
                </button>
              )}
              {!isLast ? <span aria-hidden="true" style={{ color: "#999" }}>›</span> : null}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
