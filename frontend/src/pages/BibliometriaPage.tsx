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

import { useEffect, useState, type CSSProperties } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { EmptyState, ErrorBanner, LoadingIndicator } from "../components";
import { useResumenConsolidado } from "../hooks";
import {
  obtenerArticulosDeOfc,
  urlDescargaArticulosOfcCsv,
  urlDescargaConsolidadoCsv,
} from "../services";
import type {
  ArticulosOFC,
  IndicadoresColaboracion,
  ResumenConsolidado,
} from "../types";

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

/**
 * Tabla de indicadores de colaboración y autoría, bajo las métricas resumen.
 *
 * Incluye conteos (publicaciones, firmas, autores únicos) y los dos índices de
 * colaboración: Grado de Colaboración (Subramanyam 1983) y RCC (Egghe 1991).
 * Las filas de internacional/interinstitucional dependen de las afiliaciones
 * (país/institución por autor), que llegarán con la re-ingesta; mientras tanto
 * se muestran como "pendiente (requiere afiliaciones)". "Autores únicos" es
 * aproximado (no resuelve homónimos ni variantes del mismo nombre).
 */
function IndicadoresTable({ ind }: { ind: IndicadoresColaboracion }) {
  const td: CSSProperties = { padding: "0.35rem 0.6rem", borderBottom: "1px solid #eee" };
  const tdR: CSSProperties = { ...td, textAlign: "right", fontVariantNumeric: "tabular-nums" };
  const pendiente = "pendiente (requiere afiliaciones)";
  const fmt = (v: number | null) => (v == null ? "—" : v.toLocaleString("es-CO"));

  const filas: { etiqueta: string; valor: string; nota?: string }[] = [
    { etiqueta: "Total de publicaciones", valor: fmt(ind.total_publicaciones) },
    { etiqueta: "Publicaciones individuales", valor: fmt(ind.publicaciones_individuales) },
    { etiqueta: "Publicaciones de 2 o más autores", valor: fmt(ind.publicaciones_colaborativas) },
    { etiqueta: "Total de firmas de autor", valor: fmt(ind.total_firmas) },
    { etiqueta: "Autores únicos", valor: fmt(ind.autores_unicos), nota: "aproximado" },
    {
      etiqueta: "Publicaciones internacionales",
      valor: ind.publicaciones_internacionales == null ? pendiente : fmt(ind.publicaciones_internacionales),
    },
    {
      etiqueta: "Publicaciones interinstitucionales",
      valor: ind.publicaciones_interinstitucionales == null ? pendiente : fmt(ind.publicaciones_interinstitucionales),
    },
    {
      etiqueta: "Grado de Colaboración (Subramanyam, 1983)",
      valor: ind.grado_colaboracion == null ? "—" : ind.grado_colaboracion.toFixed(2),
    },
    {
      etiqueta: "RCC — Revised Collaborative Coefficient (Egghe, 1991)",
      valor: ind.rcc == null ? "—" : ind.rcc.toFixed(3),
    },
  ];

  return (
    <section style={{ marginTop: "1rem" }}>
      <h3 style={{ marginBottom: "0.25rem" }}>Indicadores de colaboración</h3>
      <p style={{ color: "#567", fontSize: "0.82rem", marginTop: 0 }}>
        Calculados sobre los artículos con autoría contable.{" "}
        {ind.articulos_sin_autoria > 0
          ? `${ind.articulos_sin_autoria.toLocaleString("es-CO")} artículo(s) sin autoría contable quedan fuera del cálculo.`
          : ""}
      </p>
      <table style={{ borderCollapse: "collapse", width: "100%", maxWidth: 520 }}>
        <tbody>
          {filas.map((f) => (
            <tr key={f.etiqueta}>
              <td style={td}>
                {f.etiqueta}
                {f.nota ? (
                  <span style={{ color: "#8a6d1f", fontSize: "0.78rem" }}> ({f.nota})</span>
                ) : null}
              </td>
              <td style={tdR}>{f.valor}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
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
 * Gráfico "Artículos por año" con barras (conteo anual) + línea de ACUMULADO.
 *
 * Las barras muestran los artículos de cada año y la línea la suma corrida
 * (2020, 2020+2021, …), en un segundo eje Y a la derecha para que ambas escalas
 * se lean bien. El acumulado se deriva de los mismos datos por año (orden
 * cronológico ascendente); no añade datos nuevos.
 *
 * Nota: con un año seleccionado en el filtro hay un solo punto, así que el
 * acumulado coincide con el conteo de ese año (la línea no aporta y se omite).
 */
function AnioAcumuladoCard({
  data,
}: {
  data: readonly { clave: string; conteo: number }[];
}) {
  // Orden cronológico ascendente por el año (clave numérica).
  const ordenado = [...data].sort((a, b) => Number(a.clave) - Number(b.clave));
  let suma = 0;
  const chart = ordenado.map((d) => {
    suma += d.conteo;
    return { clave: d.clave, conteo: d.conteo, acumulado: suma };
  });
  const mostrarAcumulado = chart.length > 1;
  return (
    <section style={{ marginTop: "1.5rem" }}>
      <h3 style={{ marginBottom: "0.5rem" }}>Artículos por año</h3>
      <div style={{ width: "100%", height: 280 }}>
        <ResponsiveContainer>
          <ComposedChart data={chart} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e3e8e5" />
            <XAxis dataKey="clave" />
            <YAxis yAxisId="left" allowDecimals={false} />
            {mostrarAcumulado && (
              <YAxis
                yAxisId="right"
                orientation="right"
                allowDecimals={false}
                stroke="#1f5c3a"
              />
            )}
            <Tooltip />
            <Legend />
            <Bar
              yAxisId="left"
              dataKey="conteo"
              name="Artículos del año"
              fill="#2f8f5b"
              radius={[4, 4, 0, 0]}
            />
            {mostrarAcumulado && (
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="acumulado"
                name="Acumulado"
                stroke="#1f5c3a"
                strokeWidth={2}
                dot={{ r: 3 }}
              />
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}

/** Ranking de instituciones (barras horizontales; nombres largos). */
function InstitucionesCard({
  titulo,
  descripcion,
  data,
}: {
  titulo: string;
  descripcion: string;
  data: readonly { clave: string; conteo: number }[];
}) {
  if (data.length === 0) return null;
  const chart = data.map((d) => ({ inst: d.clave, conteo: d.conteo }));
  const alto = Math.max(220, chart.length * 32);
  return (
    <section style={{ marginTop: "1.5rem" }}>
      <h3 style={{ marginBottom: "0.25rem" }}>{titulo}</h3>
      <p style={{ color: "#567", fontSize: "0.85rem", marginTop: 0 }}>{descripcion}</p>
      <div style={{ width: "100%", height: alto }}>
        <ResponsiveContainer>
          <BarChart layout="vertical" data={chart} margin={{ top: 8, right: 24, bottom: 8, left: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e3e8e5" />
            <XAxis type="number" allowDecimals={false} />
            <YAxis type="category" dataKey="inst" width={240} tick={{ fontSize: 11 }} />
            <Tooltip formatter={(v: number) => [`${v} artículos`, "Artículos"]} />
            <Bar dataKey="conteo" name="Artículos" fill="#2f8f5b" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}

/** Gráfico de barras apiladas de colaboración por año. */
function ColaboracionCard({
  data,
}: {
  data: ResumenConsolidado["colaboracion_por_anio"];
}) {
  if (data.length === 0) return null;
  const chart = data.map((d) => ({
    anio: String(d.anio),
    "Una institución": d.una_institucion,
    Nacional: d.nacional,
    Internacional: d.internacional,
  }));
  return (
    <section style={{ marginTop: "1.5rem" }}>
      <h3 style={{ marginBottom: "0.25rem" }}>Tipo de colaboración por año</h3>
      <p style={{ color: "#567", fontSize: "0.85rem", marginTop: 0 }}>
        Clasificación de cada artículo según las instituciones de sus autores: de una sola
        institución, colaboración nacional (varias instituciones colombianas) o internacional
        (instituciones de más de un país). Los artículos sin afiliación no se clasifican.
      </p>
      <div style={{ width: "100%", height: 300 }}>
        <ResponsiveContainer>
          <BarChart data={chart} margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e3e8e5" />
            <XAxis dataKey="anio" tick={{ fontSize: 10 }} />
            <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
            <Tooltip />
            <Legend />
            <Bar dataKey="Una institución" stackId="c" fill="#9ecfb4" />
            <Bar dataKey="Nacional" stackId="c" fill="#2f8f5b" />
            <Bar dataKey="Internacional" stackId="c" fill="#1f5c3a" />
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
        <h3 style={{ marginBottom: "0.5rem" }}>Artículos por fuente</h3>
        <p style={{ color: "#666" }}>No hay información de fuente en el conjunto actual.</p>
      </section>
    );
  }
  const chart = data.map((d) => ({ revista: d.clave, conteo: d.conteo }));
  const alto = Math.max(260, chart.length * 26);
  return (
    <section style={{ marginTop: "1.5rem" }}>
      <h3 style={{ marginBottom: "0.25rem" }}>Artículos por fuente</h3>
      <p style={{ color: "#567", fontSize: "0.85rem", marginTop: 0 }}>
        Fuentes con más publicaciones; el resto se agrupa en “Otros”. El nombre se muestra tal como
        viene del dato y puede ser una revista o un repositorio institucional (p. ej. repositorios
        universitarios, GBIF o Zenodo).
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
 * Explicación pública de bajo qué criterios se seleccionan los artículos.
 *
 * Julián (SAO) pidió que estos criterios estén siempre visibles para quien
 * consulte el dashboard, para evitar confusiones sobre qué incluye el análisis.
 * El dashboard NO filtra: solo consolida lo que ya se trajo en la ingesta; los
 * criterios son de esa etapa. Son una propuesta del equipo a validar con SAO
 * (no un criterio oficial de SAO), y así se declara.
 */
function CriteriosSeleccion() {
  return (
    <details
      style={{
        margin: "0.5rem 0 0",
        padding: "0.75rem 1rem",
        border: "1px solid #d7e3dc",
        borderRadius: "0.5rem",
        backgroundColor: "#f7faf8",
      }}
    >
      <summary style={{ cursor: "pointer", fontWeight: 600, color: "#1f5c3a" }}>
        ¿Bajo qué criterios se seleccionan los artículos?
      </summary>
      <p style={{ color: "#445", fontSize: "0.9rem", marginTop: "0.75rem", marginBottom: "0.5rem" }}>
        El dashboard no filtra: consolida todo lo recuperado en la ingesta. Los artículos se
        seleccionan por estos tres criterios:
      </p>
      <ol style={{ margin: 0, paddingLeft: "1.25rem", color: "#334", fontSize: "0.9rem" }}>
        <li style={{ marginBottom: "0.4rem" }}>
          <strong>Fuente:</strong> OpenAlex (API y Publish or Perish) y Boletín SAO.
        </li>
        <li style={{ marginBottom: "0.4rem" }}>
          <strong>Términos de búsqueda:</strong> ecuaciones booleanas multilingües (ES/EN/PT) que
          cruzan términos de aves (bird, aves, avifauna…) con conservación, amenazas y biodiversidad
          (conservation, habitat loss, threatened species, protected areas…). Alcance internacional,
          con énfasis —no exclusivo— en Colombia.
        </li>
        <li style={{ marginBottom: "0.4rem" }}>
          <strong>Período:</strong> 2020–2030.
        </li>
      </ol>
      <p style={{ color: "#8a6d1f", fontSize: "0.82rem", marginTop: "0.5rem", marginBottom: 0 }}>
        Estos criterios de búsqueda son una propuesta del equipo, pendiente de validación con SAO.
      </p>
    </details>
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
  // OFC seleccionado para ver sus artículos (null = ninguno).
  const [ofcSel, setOfcSel] = useState<string | null>(null);
  const onSeleccionarOfc = (ofc: string) =>
    setOfcSel((actual) => (actual === ofc ? null : ofc));

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
  // Barra adicional (decisión de Julián): los artículos de aves que NO encajan
  // en ningún OFC se muestran como una categoría propia, no se ocultan. Son
  // temas no focales (enfermedades, genética, metodología...).
  if (resumen.sin_ofc > 0) {
    data.push({
      ofc: "Otros",
      nombre: "Otros tópicos no incluidos (enfermedades, genética, metodología…)",
      conteo: resumen.sin_ofc,
    });
  }
  const alto = Math.max(220, data.length * 34);

  return (
    <section style={{ marginTop: "1.5rem" }}>
      <h3 style={{ marginBottom: "0.25rem" }}>Distribución por OFC</h3>
      <p style={{ color: "#8a6d1f", fontSize: "0.85rem", marginTop: 0 }}>
        Clasificación <strong>automática</strong> (reglas por palabras clave), sujeta a revisión
        humana. Los {resumen.sin_ofc} artículos que no encajan en ningún OFC se muestran como
        “Otros tópicos no incluidos” (temas no focales: enfermedades, genética, metodología…).
      </p>
      <ExplicacionOFC
        descripcion={resumen.ofc_descripcion}
        catalogo={resumen.catalogo_ofc}
      />
      <p style={{ color: "#567", fontSize: "0.82rem", margin: "0 0 0.25rem" }}>
        Haz clic en una barra para ver los artículos de ese OFC.
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
            <Bar
              dataKey="conteo"
              name="Artículos"
              fill="#2f8f5b"
              radius={[0, 4, 4, 0]}
              cursor="pointer"
              onClick={(payload: unknown) => {
                const ofc = (payload as { ofc?: string } | undefined)?.ofc;
                // "Otros" no es un OFC real (no tiene drill-down de artículos).
                if (ofc && ofc.startsWith("OFC-")) onSeleccionarOfc(ofc);
              }}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
      {ofcSel && <ArticulosOfcPanel ofcId={ofcSel} onCerrar={() => setOfcSel(null)} />}
      <GradoColaboracionTable por_ofc={resumen.por_ofc} />
    </section>
  );
}

/**
 * Panel con los artículos "detrás de" un OFC: lista acotada (título enlazado +
 * año/revista) y botón para descargar el CSV completo de ese OFC. Se carga al
 * hacer clic en la barra; mientras carga muestra un indicador. Pensado para
 * mapear al patrón de ArcGIS (pop-up con registros + descarga).
 */
function ArticulosOfcPanel({
  ofcId,
  onCerrar,
}: {
  ofcId: string;
  onCerrar: () => void;
}) {
  const [data, setData] = useState<ArticulosOFC | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let activo = true;
    setData(null);
    setError(null);
    obtenerArticulosDeOfc(ofcId)
      .then((res) => {
        if (activo) setData(res);
      })
      .catch(() => {
        if (activo) setError("No se pudieron cargar los artículos de este OFC.");
      });
    return () => {
      activo = false;
    };
  }, [ofcId]);

  return (
    <div
      style={{
        marginTop: "1rem",
        padding: "0.75rem 1rem",
        border: "1px solid #c5d6cb",
        borderRadius: "0.5rem",
        backgroundColor: "#fbfdfc",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", flexWrap: "wrap" }}>
        <h4 style={{ margin: 0 }}>
          Artículos de {data ? `${data.nombre} (${data.ofc_id})` : ofcId}
        </h4>
        <button
          type="button"
          onClick={onCerrar}
          style={{
            marginLeft: "auto",
            padding: "0.25rem 0.6rem",
            borderRadius: "0.4rem",
            border: "1px solid #c5d6cb",
            backgroundColor: "#fff",
            cursor: "pointer",
            fontSize: "0.8rem",
          }}
        >
          Cerrar ✕
        </button>
      </div>

      {error && <ErrorBanner error={error} />}
      {!data && !error && <LoadingIndicator message="Cargando artículos…" />}

      {data && (
        <>
          <p style={{ color: "#567", fontSize: "0.85rem", margin: "0.5rem 0" }}>
            {data.total} artículo(s) en este OFC.
            {data.mostrados < data.total
              ? ` Mostrando los primeros ${data.mostrados}; descarga el CSV para ver todos.`
              : ""}
            <a
              href={urlDescargaArticulosOfcCsv(data.ofc_id)}
              download
              style={{ marginLeft: "0.5rem", color: "#1f5c3a", fontWeight: 600 }}
            >
              ⬇ Descargar CSV de este OFC
            </a>
          </p>
          <ol style={{ margin: 0, paddingLeft: "1.25rem" }}>
            {data.items.map((a, i) => (
              <li key={i} style={{ marginBottom: "0.35rem", fontSize: "0.9rem" }}>
                {a.enlace ? (
                  <a href={a.enlace} target="_blank" rel="noopener noreferrer">
                    {a.titulo}
                  </a>
                ) : (
                  <span>{a.titulo}</span>
                )}
                <span style={{ color: "#789" }}>
                  {a.anio ? ` · ${a.anio}` : ""}
                  {a.revista ? ` · ${a.revista}` : ""}
                </span>
              </li>
            ))}
          </ol>
        </>
      )}
    </div>
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

      <CriteriosSeleccion />

      <div
        style={{
          margin: "0.75rem 0",
          display: "flex",
          alignItems: "center",
          gap: "0.75rem",
          flexWrap: "wrap",
        }}
      >
        <FiltroAnio anios={data.anios_disponibles} valor={anio} onChange={setAnio} />
        {anio != null && (
          <span style={{ fontSize: "0.85rem", color: "#567" }}>
            Mostrando resultados del año <strong>{anio}</strong>.
          </span>
        )}
        {data.total_articulos > 0 && (
          <a
            href={urlDescargaConsolidadoCsv(anio)}
            download
            style={{
              marginLeft: "auto",
              padding: "0.4rem 0.8rem",
              borderRadius: "0.4rem",
              border: "1px solid #2f8f5b",
              backgroundColor: "#2f8f5b",
              color: "#fff",
              fontSize: "0.85rem",
              textDecoration: "none",
              fontWeight: 600,
            }}
            title="Descarga un CSV con título, enlace y metadatos básicos de cada artículo"
          >
            ⬇ Descargar CSV {anio != null ? `(${anio})` : "(todos)"}
          </a>
        )}
      </div>

      {data.total_articulos === 0 ? (
        <EmptyState
          message={
            anio != null
              ? `No hay artículos del año ${anio} en ninguna fuente.`
              : "Aún no hay artículos procesados en ninguna fuente. Ejecuta los pipelines de ingesta para generar los datasets procesados."
          }
        />
      ) : (
        <>
          {/* Métricas resumen sobre el conjunto consolidado */}
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.75rem", marginTop: "1rem" }}>
            <MetricCard label="Artículos" value={data.total_articulos} />
            <MetricCard label="Fuentes" value={data.aporte_por_fuente.length} />
          </div>

          {data.indicadores && <IndicadoresTable ind={data.indicadores} />}

          <AnioAcumuladoCard data={data.por_anio} />
          <OFCCard resumen={data} />
          <RevistasCard data={data.por_revista} />
          <BarsCard title="Artículos por idioma" data={data.por_idioma} />
          <BarsCard title="Artículos por tipo de documento" data={data.por_tipo_documento} />
          <BarsCard title="Tipo de acceso (según GBIF/OpenAlex)" data={data.por_acceso_abierto} />
          <InstitucionesCard
            titulo="Instituciones — por primer autor (top 10)"
            descripcion="Instituciones del autor principal (posición 'first') con más artículos."
            data={data.instituciones_primer_autor}
          />
          <InstitucionesCard
            titulo="Instituciones — por presencia (top 10)"
            descripcion="Instituciones con más artículos en los que participa al menos uno de sus autores (cuenta 1 por artículo)."
            data={data.instituciones_presencia}
          />
          <ColaboracionCard data={data.colaboracion_por_anio} />
        </>
      )}
    </div>
  );
}
