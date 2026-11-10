// Dashboard bibliométrico — análisis CONSOLIDADO de todas las fuentes
// (Componente B).
//
// Muestra agregaciones del conjunto combinado de TODAS las fuentes ya
// procesadas bajo `data/processed/` (unión sin exclusión, sin deduplicación
// entre fuentes): total de artículos, distribución por año y por volumen,
// completitud de metadata y, cuando exista, distribución por OFC. Como
// información complementaria incluye el "Aporte por fuente" (cuánto aporta cada
// fuente al total), sin fragmentar el análisis por fuente.
//
// La clasificación por OFC es automática y está sujeta a revisión humana; así
// se comunica cuando hay un dataset clasificado disponible. Cuando el conjunto
// no tiene artículos se muestra un estado vacío honesto, sin inventar datos.
//
// Los gráficos usan Recharts. Los estados de carga/error/vacío reutilizan los
// componentes compartidos (LoadingIndicator, ErrorBanner, EmptyState).

import { useState, type CSSProperties } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { EmptyState, ErrorBanner, LoadingIndicator } from "../components";
import { useResumenConsolidado } from "../hooks";
import type { ResumenConsolidado } from "../types";

/** Valor del desplegable que representa "todos los años" (sin filtro). */
const TODOS_LOS_ANIOS = "todos";

/** Desplegable para filtrar el dashboard por año de publicación. */
function FiltroAnio({
  anios,
  valor,
  onChange,
}: {
  anios: readonly number[];
  valor: number | null;
  onChange: (anio: number | null) => void;
}) {
  if (anios.length === 0) {
    return null;
  }
  return (
    <label style={{ display: "inline-flex", alignItems: "center", gap: "0.5rem" }}>
      <span style={{ fontSize: "0.9rem", color: "#456" }}>Año:</span>
      <select
        value={valor == null ? TODOS_LOS_ANIOS : String(valor)}
        onChange={(e) =>
          onChange(e.target.value === TODOS_LOS_ANIOS ? null : Number(e.target.value))
        }
        style={{
          padding: "0.35rem 0.5rem",
          borderRadius: "0.4rem",
          border: "1px solid #c5d6cb",
          backgroundColor: "#fff",
          color: "#1f5c3a",
          fontSize: "0.9rem",
        }}
      >
        <option value={TODOS_LOS_ANIOS}>Todos</option>
        {anios.map((a) => (
          <option key={a} value={String(a)}>
            {a}
          </option>
        ))}
      </select>
    </label>
  );
}

/** Tarjeta de métrica individual (número grande + etiqueta). */
function MetricCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div
      style={{
        flex: "1 1 160px",
        padding: "1rem",
        border: "1px solid #d7e3dc",
        borderRadius: "0.5rem",
        backgroundColor: "#f3f8f5",
      }}
    >
      <div style={{ fontSize: "1.8rem", fontWeight: 700, color: "#1f5c3a" }}>{value}</div>
      <div style={{ fontSize: "0.85rem", color: "#456" }}>{label}</div>
    </div>
  );
}

/** Gráfico de barras simple para una distribución (clave → conteo). */
function BarsCard({
  title,
  data,
}: {
  title: string;
  data: readonly { clave: string; conteo: number }[];
}) {
  return (
    <section style={{ marginTop: "1.5rem" }}>
      <h3 style={{ marginBottom: "0.5rem" }}>{title}</h3>
      <div style={{ width: "100%", height: 260 }}>
        <ResponsiveContainer>
          <BarChart data={[...data]} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e3e8e5" />
            <XAxis dataKey="clave" />
            <YAxis allowDecimals={false} />
            <Tooltip />
            <Bar dataKey="conteo" name="Artículos" fill="#2f8f5b" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}

/**
 * Distribución por revista: barras HORIZONTALES con el nombre de la revista.
 *
 * Se usa layout horizontal (nombre en el eje Y) porque los nombres de revista
 * son largos y no caben legibles en el eje X. Muestra el top de revistas que
 * envía el backend y una barra final "Otros" que agrupa el resto. Los nombres
 * se muestran tal cual vienen del dato (pueden incluir repositorios).
 */
function RevistasCard({
  data,
}: {
  data: readonly { clave: string; conteo: number }[];
}) {
  if (data.length === 0) {
    return (
      <section style={{ marginTop: "1.5rem" }}>
        <h3 style={{ marginBottom: "0.5rem" }}>Artículos por revista</h3>
        <p style={{ color: "#666" }}>No hay información de revista en el conjunto actual.</p>
      </section>
    );
  }
  const chart = data.map((d) => ({ revista: d.clave, conteo: d.conteo }));
  const alto = Math.max(260, chart.length * 26);
  return (
    <section style={{ marginTop: "1.5rem" }}>
      <h3 style={{ marginBottom: "0.25rem" }}>Artículos por revista</h3>
      <p style={{ color: "#567", fontSize: "0.85rem", marginTop: 0 }}>
        Revistas con más publicaciones; el resto se agrupa en “Otros”. El nombre se muestra tal
        como viene de la fuente (puede incluir repositorios como GBIF, bioRxiv o Zenodo).
      </p>
      <div style={{ width: "100%", height: alto }}>
        <ResponsiveContainer>
          <BarChart
            layout="vertical"
            data={chart}
            margin={{ top: 8, right: 24, bottom: 8, left: 8 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e3e8e5" />
            <XAxis type="number" allowDecimals={false} />
            <YAxis type="category" dataKey="revista" width={240} tick={{ fontSize: 11 }} />
            <Tooltip formatter={(value: number) => [`${value} artículos`, "Conteo"]} />
            <Legend />
            <Bar dataKey="conteo" name="Artículos" fill="#2f8f5b" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}

/**
 * Explicación pública de qué son los OFC (Objetos Focales de Conservación).
 *
 * Muestra el texto oficial de la ENCA y la lista de los 11 OFC con su
 * definición, en un desplegable para no saturar la vista. Pensado para que
 * cualquier visitante del sitio público entienda el término sin conocerlo de
 * antemano. El contenido proviene del backend (catálogo oficial ENCA 2030);
 * si no viene, el componente no se renderiza.
 */
function ExplicacionOFC({
  descripcion,
  catalogo,
}: {
  descripcion: string;
  catalogo: ResumenConsolidado["catalogo_ofc"];
}) {
  if (!descripcion && catalogo.length === 0) {
    return null;
  }
  return (
    <details
      style={{
        margin: "0.5rem 0 1rem",
        padding: "0.75rem 1rem",
        border: "1px solid #d7e3dc",
        borderRadius: "0.5rem",
        backgroundColor: "#f7faf8",
      }}
    >
      <summary style={{ cursor: "pointer", fontWeight: 600, color: "#1f5c3a" }}>
        ¿Qué son los OFC (Objetos Focales de Conservación)?
      </summary>
      {descripcion && (
        <p style={{ color: "#445", fontSize: "0.9rem", marginTop: "0.75rem" }}>
          {descripcion}
        </p>
      )}
      {catalogo.length > 0 && (
        <ol style={{ margin: "0.5rem 0 0", paddingLeft: "1.25rem", color: "#334" }}>
          {catalogo.map((o) => (
            <li key={o.ofc_id} style={{ marginBottom: "0.4rem", fontSize: "0.9rem" }}>
              <strong>{o.nombre}</strong>
              {o.definicion ? (
                <span style={{ color: "#667" }}> — {o.definicion}</span>
              ) : null}
            </li>
          ))}
        </ol>
      )}
    </details>
  );
}

/** Gráfico de barras horizontales para la distribución por OFC. */
function OFCCard({ resumen }: { resumen: ResumenConsolidado }) {
  if (!resumen.clasificacion_disponible) {
    return (
      <section style={{ marginTop: "1.5rem" }}>
        <h3 style={{ marginBottom: "0.5rem" }}>Distribución por OFC</h3>
        <ExplicacionOFC
          descripcion={resumen.ofc_descripcion}
          catalogo={resumen.catalogo_ofc}
        />
        <p style={{ color: "#666" }}>
          Aún no hay un dataset clasificado. Ejecuta el pipeline de clasificación por OFC.
        </p>
      </section>
    );
  }

  // Usa el id como etiqueta corta del eje; el nombre va en el tooltip.
  const data = resumen.por_ofc.map((o) => ({
    ofc: o.ofc_id,
    nombre: o.nombre,
    conteo: o.conteo,
  }));
  const alto = Math.max(220, data.length * 34);

  return (
    <section style={{ marginTop: "1.5rem" }}>
      <h3 style={{ marginBottom: "0.25rem" }}>Distribución por OFC</h3>
      <p style={{ color: "#8a6d1f", fontSize: "0.85rem", marginTop: 0 }}>
        Clasificación <strong>automática</strong> (reglas por palabras clave), sujeta a revisión
        humana. {resumen.sin_ofc} artículo(s) sin OFC asignado.
      </p>
      <ExplicacionOFC
        descripcion={resumen.ofc_descripcion}
        catalogo={resumen.catalogo_ofc}
      />
      <div style={{ width: "100%", height: alto }}>
        <ResponsiveContainer>
          <BarChart
            layout="vertical"
            data={data}
            margin={{ top: 8, right: 24, bottom: 8, left: 8 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e3e8e5" />
            <XAxis type="number" allowDecimals={false} />
            <YAxis type="category" dataKey="ofc" width={64} />
            <Tooltip
              formatter={(value: number) => [`${value} artículos`, "Conteo"]}
              labelFormatter={(ofc: string) =>
                data.find((d) => d.ofc === ofc)?.nombre ?? ofc
              }
            />
            <Legend />
            <Bar dataKey="conteo" name="Artículos" fill="#2f8f5b" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <GradoColaboracionTable por_ofc={resumen.por_ofc} />
    </section>
  );
}

/**
 * Tabla del Grado de Colaboración (GC) de Subramanyam (1983) por OFC.
 *
 * GC = 1 − f1/N: proporción de la producción de cada OFC hecha en coautoría
 * (0 = todo de autor único; cercano a 1 = predomina la colaboración). Se calcula
 * solo sobre artículos con autoría contable de forma fiable; la columna "Base"
 * indica cuántos artículos entraron en el cálculo y, entre paréntesis, cuántos
 * quedaron fuera por no tener autoría contable. Un GC "—" significa que el OFC
 * no tiene artículos con autoría contable.
 */
function GradoColaboracionTable({
  por_ofc,
}: {
  por_ofc: ResumenConsolidado["por_ofc"];
}) {
  const th: CSSProperties = {
    textAlign: "left",
    padding: "0.4rem",
    borderBottom: "2px solid #ccc",
  };
  const thR: CSSProperties = { ...th, textAlign: "right" };
  const td: CSSProperties = { padding: "0.4rem", borderBottom: "1px solid #eee" };
  const tdR: CSSProperties = { ...td, textAlign: "right" };
  return (
    <div style={{ marginTop: "1rem" }}>
      <h4 style={{ margin: "0 0 0.25rem" }}>Grado de Colaboración por OFC</h4>
      <p style={{ color: "#567", fontSize: "0.85rem", marginTop: 0 }}>
        Índice de Subramanyam (1983): <code>GC = 1 − f₁/N</code>, donde f₁ son los artículos de
        un solo autor y N los artículos del OFC con autoría contable. 0 = producción individual;
        cerca de 1 = predomina la coautoría. Se calcula solo donde la autoría es contable de forma
        fiable (p. ej. OpenAlex); el paréntesis en “Base” son los artículos sin autoría contable.
      </p>
      <table style={{ borderCollapse: "collapse", width: "100%", maxWidth: 560 }}>
        <thead>
          <tr>
            <th style={th}>OFC</th>
            <th style={thR}>Artículos</th>
            <th style={thR}>GC</th>
            <th style={thR}>Base (N)</th>
          </tr>
        </thead>
        <tbody>
          {por_ofc.map((o) => (
            <tr key={o.ofc_id}>
              <td style={td} title={o.nombre}>
                {o.ofc_id}
              </td>
              <td style={tdR}>{o.conteo}</td>
              <td style={tdR}>
                {o.grado_colaboracion == null ? "—" : o.grado_colaboracion.toFixed(2)}
              </td>
              <td style={tdR}>
                {o.gc_articulos_contables}
                {o.gc_articulos_sin_autoria > 0 ? ` (+${o.gc_articulos_sin_autoria})` : ""}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/** Tabla de completitud de metadata (campo → con dato / total). */
function CompletitudTable({
  completitud,
}: {
  completitud: ResumenConsolidado["completitud"];
}) {
  return (
    <section style={{ marginTop: "1.5rem" }}>
      <h3 style={{ marginBottom: "0.5rem" }}>Completitud de metadata</h3>
      <table style={{ borderCollapse: "collapse", width: "100%", maxWidth: 480 }}>
        <thead>
          <tr>
            <th style={{ textAlign: "left", padding: "0.4rem", borderBottom: "2px solid #ccc" }}>
              Campo
            </th>
            <th style={{ textAlign: "right", padding: "0.4rem", borderBottom: "2px solid #ccc" }}>
              Con dato
            </th>
            <th style={{ textAlign: "right", padding: "0.4rem", borderBottom: "2px solid #ccc" }}>
              %
            </th>
          </tr>
        </thead>
        <tbody>
          {completitud.map((c) => {
            const pct = c.total > 0 ? Math.round((100 * c.con_dato) / c.total) : 0;
            return (
              <tr key={c.campo}>
                <td style={{ padding: "0.4rem", borderBottom: "1px solid #eee" }}>{c.campo}</td>
                <td style={{ padding: "0.4rem", textAlign: "right", borderBottom: "1px solid #eee" }}>
                  {c.con_dato} / {c.total}
                </td>
                <td style={{ padding: "0.4rem", textAlign: "right", borderBottom: "1px solid #eee" }}>
                  {pct}%
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </section>
  );
}

/**
 * Sección "Aporte por fuente" (información complementaria).
 *
 * Indica, por cada fuente con dataset procesado, cuántos artículos aporta al
 * total consolidado y su completitud global de metadata. NO fragmenta el
 * análisis por fuente: es un desglose complementario del conjunto.
 */
function AportePorFuenteSection({
  aporte,
}: {
  aporte: ResumenConsolidado["aporte_por_fuente"];
}) {
  return (
    <section style={{ marginTop: "1.5rem" }}>
      <h3 style={{ marginBottom: "0.25rem" }}>Aporte por fuente</h3>
      <p style={{ color: "#567", fontSize: "0.85rem", marginTop: 0 }}>
        Información complementaria: cuánto aporta cada fuente al conjunto consolidado. El análisis
        sigue siendo único; no se separa por fuente.
      </p>
      {aporte.length === 0 ? (
        <EmptyState message="Aún no hay fuentes con dataset procesado." />
      ) : (
        <table style={{ borderCollapse: "collapse", width: "100%", maxWidth: 480 }}>
          <thead>
            <tr>
              <th
                style={{ textAlign: "left", padding: "0.4rem", borderBottom: "2px solid #ccc" }}
              >
                Fuente
              </th>
              <th
                style={{ textAlign: "right", padding: "0.4rem", borderBottom: "2px solid #ccc" }}
              >
                Artículos
              </th>
              <th
                style={{ textAlign: "right", padding: "0.4rem", borderBottom: "2px solid #ccc" }}
              >
                Completitud
              </th>
            </tr>
          </thead>
          <tbody>
            {aporte.map((f) => {
              // Completitud global de la fuente: promedio de % por campo.
              const pct =
                f.completitud.length > 0
                  ? Math.round(
                      f.completitud.reduce(
                        (acc, c) => acc + (c.total > 0 ? (100 * c.con_dato) / c.total : 0),
                        0,
                      ) / f.completitud.length,
                    )
                  : 0;
              return (
                <tr key={f.fuente}>
                  <td style={{ padding: "0.4rem", borderBottom: "1px solid #eee" }}>{f.fuente}</td>
                  <td
                    style={{
                      padding: "0.4rem",
                      textAlign: "right",
                      borderBottom: "1px solid #eee",
                    }}
                  >
                    {f.total_articulos}
                  </td>
                  <td
                    style={{
                      padding: "0.4rem",
                      textAlign: "right",
                      borderBottom: "1px solid #eee",
                    }}
                  >
                    {pct}%
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </section>
  );
}

/** Página del dashboard bibliométrico consolidado. */
export function BibliometriaPage() {
  // Año seleccionado para el filtro (null = "Todos"). Al cambiarlo, el hook
  // recarga el resumen ya filtrado desde el backend/snapshot.
  const [anio, setAnio] = useState<number | null>(null);
  const { loading, data, error, reload } = useResumenConsolidado(anio);

  if (loading) {
    return <LoadingIndicator message="Cargando dashboard bibliométrico…" />;
  }
  if (error) {
    return <ErrorBanner error={error} onRetry={reload} />;
  }
  if (!data) {
    return <ErrorBanner error="No hay datos bibliométricos disponibles." onRetry={reload} />;
  }

  const fechas = data.fechas_dataset.filter((f) => f.length > 0);

  return (
    <div>
      <h2 style={{ marginBottom: "0.25rem" }}>Bibliometría — todas las fuentes</h2>
      <p style={{ color: "#567", marginTop: 0 }}>
        Análisis consolidado del conjunto combinado de todas las fuentes procesadas
        {fechas.length > 0 ? ` (datasets: ${fechas.join(", ")})` : ""}. La clasificación por OFC
        está pendiente de validación con SAO.
      </p>

      <div style={{ margin: "0.75rem 0" }}>
        <FiltroAnio anios={data.anios_disponibles} valor={anio} onChange={setAnio} />
        {anio != null && (
          <span style={{ marginLeft: "0.75rem", fontSize: "0.85rem", color: "#567" }}>
            Mostrando resultados del año <strong>{anio}</strong>.
          </span>
        )}
      </div>

      {data.total_articulos === 0 ? (
        <>
          <EmptyState
            message={
              anio != null
                ? `No hay artículos del año ${anio} en ninguna fuente.`
                : "Aún no hay artículos procesados en ninguna fuente. Ejecuta los pipelines de ingesta para generar los datasets procesados."
            }
          />
          <AportePorFuenteSection aporte={data.aporte_por_fuente} />
        </>
      ) : (
        <>
          {/* Métricas resumen sobre el conjunto consolidado */}
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.75rem", marginTop: "1rem" }}>
            <MetricCard label="Artículos" value={data.total_articulos} />
            <MetricCard label="Fuentes" value={data.aporte_por_fuente.length} />
          </div>

          <BarsCard title="Artículos por año" data={data.por_anio} />
          <OFCCard resumen={data} />
          <RevistasCard data={data.por_revista} />
          <CompletitudTable completitud={data.completitud} />
          <AportePorFuenteSection aporte={data.aporte_por_fuente} />
        </>
      )}
    </div>
  );
}
