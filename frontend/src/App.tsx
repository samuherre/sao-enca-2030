// App shell del frontend de SAO ENCA 2030 (tarea 21 — cableado de navegación).
//
// Conecta las cinco vistas por nivel (Ejes → Metas → Objetivos → Indicadores →
// Actividades) en un flujo de drill-down con REGRESO (Req 7.3, 7.6).
//
// DECISIÓN DE NAVEGACIÓN (TECHNICAL_DECISION, documentada aquí y en el README):
// se usa una navegación por ESTADO en memoria, SIN añadir `react-router-dom`.
// Justificación (coherente con tech.md §33 y §40, "evitar sobreingeniería"):
//   - El drill-down es estrictamente lineal: Eje → Meta → Objetivo → Indicador
//     → Actividad. No hay rutas transversales ni enlaces profundos requeridos.
//   - Cada nivel necesita la ENTIDAD PADRE (no solo su id) para mostrar su
//     contexto; esa entidad ya se tiene en memoria al seleccionarla en la lista
//     del nivel superior, por lo que una pila de niveles es suficiente y evita
//     volver a pedir el padre a la API.
//   - No añadir una dependencia de router mantiene el stack mínimo (React + TS)
//     mientras el alcance del MVP sea esta navegación lineal. Si en el futuro se
//     necesitan enlaces profundos o URLs compartibles, podrá incorporarse un
//     router (p. ej. react-router-dom con versión fijada) sin cambiar las vistas.
//
// La navegación es una PILA de niveles. El drill-down apila un nivel; las migas
// de pan permiten regresar recortando la pila al índice elegido (Req 7.6).

import type { CSSProperties } from "react";
import { useState } from "react";

import { Breadcrumb } from "./layouts";
import {
  ActividadesPage,
  BibliometriaPage,
  BiodiversidadPage,
  EjesPage,
  IndicadoresPage,
  MetasPage,
  ObjetivosPage,
} from "./pages";
import { API_URL, STATIC_MODE } from "./config";
import type { Eje, Indicador, Meta, Objetivo } from "./types";

/**
 * Un nivel de la pila de navegación. Cada nivel (salvo la raíz de Ejes) lleva la
 * entidad padre seleccionada, necesaria para listar sus hijos y crear nuevos.
 */
type NavLevel =
  | { readonly kind: "ejes" }
  | { readonly kind: "metas"; readonly eje: Eje }
  | { readonly kind: "objetivos"; readonly meta: Meta }
  | { readonly kind: "indicadores"; readonly objetivo: Objetivo }
  | { readonly kind: "actividades"; readonly indicador: Indicador };

/** Etiqueta de la miga de pan para cada nivel de la pila. */
function crumbLabel(level: NavLevel): string {
  switch (level.kind) {
    case "ejes":
      return "Ejes";
    case "metas":
      return level.eje.nombre;
    case "objetivos":
      return level.meta.descripcion;
    case "indicadores":
      return level.objetivo.descripcion;
    case "actividades":
      return level.indicador.nombre;
  }
}

/** Pestañas de nivel superior: Seguimiento ENCA, Bibliometría y Biodiversidad. */
type Tab = "enca" | "bibliometria" | "biodiversidad";

export function App() {
  // Pestaña activa de nivel superior. Por defecto, Seguimiento ENCA.
  const [tab, setTab] = useState<Tab>("enca");
  // La pila siempre empieza en el nivel raíz (Ejes), la vista inicial (Req 7.1).
  const [stack, setStack] = useState<readonly NavLevel[]>([{ kind: "ejes" }]);

  const current = stack[stack.length - 1];

  /** Apila un nuevo nivel (drill-down al nivel inferior). */
  function push(level: NavLevel) {
    setStack((prev) => [...prev, level]);
  }

  /** Regresa recortando la pila al índice indicado por las migas (Req 7.6). */
  function navigateTo(index: number) {
    setStack((prev) => prev.slice(0, index + 1));
  }

  function renderCurrent(level: NavLevel) {
    switch (level.kind) {
      case "ejes":
        return <EjesPage onSelectEje={(eje) => push({ kind: "metas", eje })} />;
      case "metas":
        return (
          <MetasPage
            eje={level.eje}
            onSelectMeta={(meta) => push({ kind: "objetivos", meta })}
          />
        );
      case "objetivos":
        return (
          <ObjetivosPage
            meta={level.meta}
            onSelectObjetivo={(objetivo) => push({ kind: "indicadores", objetivo })}
          />
        );
      case "indicadores":
        return (
          <IndicadoresPage
            objetivo={level.objetivo}
            onSelectIndicador={(indicador) => push({ kind: "actividades", indicador })}
          />
        );
      case "actividades":
        return <ActividadesPage indicador={level.indicador} />;
    }
  }

  // En modo estático (demo), los datos salen del snapshot JSON incluido en el
  // sitio, así que no se requiere VITE_API_URL. En modo normal sí.
  const apiConfigured = STATIC_MODE || API_URL.trim().length > 0;

  /** Estilo de un botón de pestaña según si está activa. */
  function tabStyle(active: boolean): CSSProperties {
    return {
      padding: "0.5rem 1rem",
      border: "none",
      borderBottom: active ? "3px solid #2f8f5b" : "3px solid transparent",
      background: "none",
      cursor: "pointer",
      fontSize: "1rem",
      fontWeight: active ? 700 : 400,
      color: active ? "#1f5c3a" : "#567",
    };
  }

  return (
    <main className="app">
      <h1>SAO ENCA 2030</h1>

      {/* Aviso de demo: deja claro que es un corte de solo lectura para
          retroalimentación, no la aplicación definitiva (destino: ArcGIS). */}
      {STATIC_MODE ? (
        <p
          style={{
            margin: "0 0 1rem",
            padding: "0.6rem 0.9rem",
            backgroundColor: "#faf3df",
            border: "1px solid #ecdcae",
            borderRadius: "0.375rem",
            color: "#5a4a1f",
            fontSize: "0.9rem",
          }}
        >
          <strong>Versión de demostración (solo lectura).</strong> Los datos son un
          corte tomado para revisión y retroalimentación; la creación de registros
          está deshabilitada. La aplicación definitiva se construirá sobre ArcGIS.
        </p>
      ) : null}

      {/* Navegación de nivel superior entre Componente A y Componente B. */}
      <nav
        role="tablist"
        aria-label="Secciones"
        style={{ display: "flex", gap: "0.5rem", borderBottom: "1px solid #dde", marginBottom: "1rem" }}
      >
        <button
          type="button"
          role="tab"
          aria-selected={tab === "enca"}
          onClick={() => setTab("enca")}
          style={tabStyle(tab === "enca")}
        >
          Seguimiento ENCA
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={tab === "bibliometria"}
          onClick={() => setTab("bibliometria")}
          style={tabStyle(tab === "bibliometria")}
        >
          Bibliometría
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={tab === "biodiversidad"}
          onClick={() => setTab("biodiversidad")}
          style={tabStyle(tab === "biodiversidad")}
        >
          Biodiversidad
        </button>
      </nav>

      {!apiConfigured ? (
        <p>
          <em>
            VITE_API_URL no configurada (defínela en <code>frontend/.env</code>). La
            interfaz no podrá consultar datos hasta configurarla.
          </em>
        </p>
      ) : null}

      {tab === "enca" ? (
        <>
          <p>
            Seguimiento de la Estructura ENCA — Eje → Meta → Objetivo → Indicador → Actividad.
          </p>
          <Breadcrumb
            crumbs={stack.map((level) => ({ label: crumbLabel(level) }))}
            onNavigate={navigateTo}
          />
          {renderCurrent(current)}
        </>
      ) : tab === "bibliometria" ? (
        <BibliometriaPage />
      ) : (
        <BiodiversidadPage />
      )}
    </main>
  );
}
