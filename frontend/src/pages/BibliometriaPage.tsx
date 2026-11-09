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

/** Gráfico de barras horizontales para la distribución por OFC. */
function OFCCard({ resumen }: { resumen: ResumenConsolidado }) {
  if (!resumen.clasificacion_disponible) {
    return (
      <section style={{ marginTop: "1.5rem" }}>
        <h3 style={{ marginBottom: "0.5rem" }}>Distribución por OFC</h3>
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
    </section>
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
  const { loading, data, error, reload } = useResumenConsolidado();

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

      {data.total_articulos === 0 ? (
        <>
          <EmptyState message="Aún no hay artículos procesados en ninguna fuente. Ejecuta los pipelines de ingesta para generar los datasets procesados." />
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
          <BarsCard title="Artículos por volumen" data={data.por_volumen} />
          <CompletitudTable completitud={data.completitud} />
          <AportePorFuenteSection aporte={data.aporte_por_fuente} />
        </>
      )}
    </div>
  );
}
