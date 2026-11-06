// Vista de biodiversidad — Datos de GBIF (cifras de registros de aves).
//
// Muestra las cifras AGREGADAS que el piloto GBIF obtiene para aves de Colombia:
// total nacional de registros de OCURRENCIA y ranking de publicadores. Los datos
// provienen de dos orígenes DIFERENCIADOS, siempre etiquetados:
//   - "almacenado": último corte guardado en disco (lectura, sin red).
//   - "en_vivo":    consulta a GBIF hecha al pulsar "Consultar GBIF" (no persiste).
//
// Principio de honestidad: un registro de GBIF es una ocurrencia en la fuente,
// NO un individuo ni una especie única; la fecha del histórico es la de
// EXTRACCIÓN, no la de observación biológica. La UI lo dice explícitamente y no
// inventa cifras ausentes.

import { useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { ErrorBanner, LoadingIndicator } from "../components";
import { STATIC_MODE } from "../config";
import { useConsultaGbifEnVivo, useResumenGbif } from "../hooks";
import type { ResumenGBIF } from "../types";

// --- Utilidades de formato (presentación pura) ------------------------------

/** Formatea un entero con separadores de miles (es-CO), o "—" si es nulo. */
function formatoEntero(valor: number | null | undefined): string {
  if (valor === null || valor === undefined) return "—";
  return new Intl.NumberFormat("es-CO").format(valor);
}

/** Convierte millones a texto corto (p. ej. 26 753 542 → "26,75 M"). */
function formatoMillones(valor: number | null | undefined): string {
  if (valor === null || valor === undefined) return "—";
  const millones = valor / 1_000_000;
  return `${new Intl.NumberFormat("es-CO", { maximumFractionDigits: 2 }).format(millones)} M`;
}

/** Formatea un timestamp ISO UTC a fecha/hora legible, o "no disponible". */
function formatoFechaHora(iso: string | null | undefined): string {
  if (!iso) return "no disponible";
  const fecha = new Date(iso);
  if (Number.isNaN(fecha.getTime())) return iso;
  return `${fecha.toLocaleString("es-CO", { dateStyle: "medium", timeStyle: "short" })} (hora local)`;
}

// --- Paleta coherente con el resto del frontend -----------------------------

const VERDE = "#2f8f5b";
const VERDE_OSCURO = "#1f5c3a";
const BORDE = "#d7e3dc";
const FONDO_SUAVE = "#f3f8f5";

// --- Subcomponentes ---------------------------------------------------------

/** Tarjeta de métrica individual (número grande + etiqueta + aclaración). */
function MetricCard({
  label,
  value,
  hint,
}: {
  label: string;
  value: string | number;
  hint?: string;
}) {
  return (
    <div
      style={{
        flex: "1 1 180px",
        padding: "1rem",
        border: `1px solid ${BORDE}`,
        borderRadius: "0.5rem",
        backgroundColor: FONDO_SUAVE,
      }}
    >
      <div style={{ fontSize: "1.8rem", fontWeight: 700, color: VERDE_OSCURO }}>{value}</div>
      <div style={{ fontSize: "0.85rem", color: "#456" }}>{label}</div>
      {hint ? (
        <div style={{ fontSize: "0.72rem", color: "#789", marginTop: "0.25rem" }}>{hint}</div>
      ) : null}
    </div>
  );
}

/** Etiqueta de origen del dato (almacenado vs en vivo), siempre visible. */
function OrigenBadge({ origen }: { origen: ResumenGBIF["origen"] }) {
  const enVivo = origen === "en_vivo";
  return (
    <span
      style={{
        display: "inline-block",
        padding: "0.15rem 0.6rem",
        borderRadius: "999px",
        fontSize: "0.75rem",
        fontWeight: 700,
        color: enVivo ? "#1f4e5c" : "#5a4a1f",
        backgroundColor: enVivo ? "#e2f0f4" : "#faf3df",
        border: `1px solid ${enVivo ? "#b9dbe4" : "#ecdcae"}`,
      }}
    >
      {enVivo ? "Consulta en vivo" : "Datos almacenados"}
    </span>
  );
}

/** Tabla + gráfico del ranking de publicadores. */
function PublicadoresCard({ resumen }: { resumen: ResumenGBIF }) {
  if (resumen.publicadores.length === 0) {
    return (
      <section style={{ marginTop: "1.5rem" }}>
        <h3 style={{ marginBottom: "0.5rem" }}>Principales publicadores</h3>
        <p style={{ color: "#666" }}>No hay ranking de publicadores en este resultado.</p>
      </section>
    );
  }

  const data = resumen.publicadores.map((p) => ({
    etiqueta: p.nombre ?? p.org_key,
    registros: p.registros_ocurrencia,
  }));
  const alto = Math.max(220, data.length * 46);

  return (
    <section style={{ marginTop: "1.5rem" }}>
      <h3 style={{ marginBottom: "0.25rem" }}>Principales publicadores</h3>
      <p style={{ color: "#567", fontSize: "0.85rem", marginTop: 0 }}>
        Organizaciones que aportan más registros de ocurrencia de aves de Colombia a GBIF.
      </p>

      <div style={{ width: "100%", height: alto }}>
        <ResponsiveContainer>
          <BarChart
            layout="vertical"
            data={data}
            margin={{ top: 8, right: 32, bottom: 8, left: 8 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e3e8e5" />
            <XAxis type="number" tickFormatter={(v: number) => formatoMillones(v)} />
            <YAxis type="category" dataKey="etiqueta" width={200} tick={{ fontSize: 12 }} />
            <Tooltip
              formatter={(value: number) => [`${formatoEntero(value)} registros`, "Ocurrencias"]}
            />
            <Bar dataKey="registros" name="Registros" fill={VERDE} radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <table style={{ borderCollapse: "collapse", width: "100%", marginTop: "0.5rem" }}>
        <thead>
          <tr>
            <th style={{ textAlign: "left", padding: "0.4rem", borderBottom: "2px solid #ccc" }}>#</th>
            <th style={{ textAlign: "left", padding: "0.4rem", borderBottom: "2px solid #ccc" }}>
              Publicador
            </th>
            <th style={{ textAlign: "right", padding: "0.4rem", borderBottom: "2px solid #ccc" }}>
              Registros de ocurrencia
            </th>
          </tr>
        </thead>
        <tbody>
          {resumen.publicadores.map((p) => (
            <tr key={p.org_key}>
              <td style={{ padding: "0.4rem", borderBottom: "1px solid #eee" }}>{p.rank}</td>
              <td style={{ padding: "0.4rem", borderBottom: "1px solid #eee" }}>
                {p.nombre ?? <em style={{ color: "#888" }}>nombre no disponible ({p.org_key})</em>}
              </td>
              <td style={{ padding: "0.4rem", textAlign: "right", borderBottom: "1px solid #eee" }}>
                {formatoEntero(p.registros_ocurrencia)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

/** Sección del histórico de cortes (con transparencia sobre su significado). */
function HistoricoCard({ resumen }: { resumen: ResumenGBIF }) {
  const cortes = resumen.historico;

  return (
    <section style={{ marginTop: "1.5rem" }}>
      <h3 style={{ marginBottom: "0.25rem" }}>Histórico de cortes</h3>
      <p style={{ color: "#567", fontSize: "0.85rem", marginTop: 0 }}>
        Cada corte es una ejecución de la consulta agregada, con su fecha de{" "}
        <strong>extracción</strong> (cuándo se consultó GBIF). No es la fecha de observación
        biológica de las aves, ni representa cambios de población: son variaciones del total que
        GBIF reporta en cada fecha.
      </p>

      {cortes.length < 2 ? (
        <p
          style={{
            padding: "0.75rem 1rem",
            backgroundColor: "#faf3df",
            border: "1px solid #ecdcae",
            borderRadius: "0.375rem",
            color: "#5a4a1f",
            fontSize: "0.9rem",
          }}
        >
          Todavía no hay suficientes cortes para una serie temporal comparable (se registran{" "}
          {cortes.length} corte{cortes.length === 1 ? "" : "s"}). La actualización está pensada para
          ser mensual; con una sola fecha no se puede mostrar una evolución honesta.
        </p>
      ) : (
        <table style={{ borderCollapse: "collapse", width: "100%" }}>
          <thead>
            <tr>
              <th style={{ textAlign: "left", padding: "0.4rem", borderBottom: "2px solid #ccc" }}>
                Fecha de extracción
              </th>
              <th style={{ textAlign: "right", padding: "0.4rem", borderBottom: "2px solid #ccc" }}>
                Total de registros
              </th>
              <th style={{ textAlign: "left", padding: "0.4rem", borderBottom: "2px solid #ccc" }}>
                Estado
              </th>
            </tr>
          </thead>
          <tbody>
            {cortes.map((c) => (
              <tr key={c.extraido_utc}>
                <td style={{ padding: "0.4rem", borderBottom: "1px solid #eee" }}>
                  {formatoFechaHora(c.extraido_utc)}
                </td>
                <td style={{ padding: "0.4rem", textAlign: "right", borderBottom: "1px solid #eee" }}>
                  {formatoEntero(c.total_registros_ocurrencia)}
                </td>
                <td style={{ padding: "0.4rem", borderBottom: "1px solid #eee" }}>{c.estado}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}

/** Sección de exportaciones CSV disponibles (para ArcGIS, sin publicar). */
function ExportacionesCard({ resumen }: { resumen: ResumenGBIF }) {
  return (
    <section style={{ marginTop: "1.5rem" }}>
      <h3 style={{ marginBottom: "0.25rem" }}>Exportaciones para ArcGIS</h3>
      <p style={{ color: "#567", fontSize: "0.85rem", marginTop: 0 }}>
        Archivos CSV generados localmente para una eventual publicación en ArcGIS Online. La
        publicación a la cuenta de SAO es un proceso aparte y <strong>no</strong> se ejecuta desde
        esta vista.
      </p>
      {resumen.exportaciones.length === 0 ? (
        <p style={{ color: "#666" }}>No hay archivos de exportación generados todavía.</p>
      ) : (
        <table style={{ borderCollapse: "collapse", width: "100%" }}>
          <thead>
            <tr>
              <th style={{ textAlign: "left", padding: "0.4rem", borderBottom: "2px solid #ccc" }}>
                Archivo
              </th>
              <th style={{ textAlign: "right", padding: "0.4rem", borderBottom: "2px solid #ccc" }}>
                Filas
              </th>
              <th style={{ textAlign: "left", padding: "0.4rem", borderBottom: "2px solid #ccc" }}>
                Generado
              </th>
            </tr>
          </thead>
          <tbody>
            {resumen.exportaciones.map((e) => (
              <tr key={e.ruta_relativa}>
                <td style={{ padding: "0.4rem", borderBottom: "1px solid #eee" }}>
                  <code>{e.nombre}</code>
                </td>
                <td style={{ padding: "0.4rem", textAlign: "right", borderBottom: "1px solid #eee" }}>
                  {formatoEntero(e.filas)}
                </td>
                <td style={{ padding: "0.4rem", borderBottom: "1px solid #eee" }}>
                  {formatoFechaHora(e.modificado_utc)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}

/** Sección de disponibilidad y limitaciones conocidas (transparencia). */
function LimitacionesCard() {
  return (
    <section
      style={{
        marginTop: "1.5rem",
        padding: "1rem",
        border: `1px solid ${BORDE}`,
        borderRadius: "0.5rem",
        backgroundColor: "#fbfdfc",
      }}
    >
      <h3 style={{ marginTop: 0, marginBottom: "0.5rem" }}>Qué muestra y qué no</h3>
      <ul style={{ margin: 0, paddingLeft: "1.2rem", color: "#445", fontSize: "0.9rem", lineHeight: 1.6 }}>
        <li>
          <strong>Disponible:</strong> total nacional de registros de ocurrencia de aves de Colombia
          y ranking de publicadores, tal como GBIF los reporta de forma agregada.
        </li>
        <li>
          <strong>Registros de ocurrencia</strong>, no individuos ni especies únicas. Un mismo
          individuo puede tener muchos registros.
        </li>
        <li>
          <strong>Sin desglose</strong> por departamento, especie ni año: el piloto actual no genera
          esos datos, y no se inventan.
        </li>
        <li>
          <strong>Histórico:</strong> requiere varios cortes (idealmente mensuales) para comparar; la
          serie refleja variaciones de lo reportado por GBIF, no cambios poblacionales.
        </li>
        <li>
          <strong>ArcGIS:</strong> solo se preparan CSV locales; la publicación a SAO está pendiente
          de permisos y configuración.
        </li>
      </ul>
    </section>
  );
}

/** Cabecera: fuente, alcance y estado de la última ejecución. */
function CabeceraResumen({ resumen }: { resumen: ResumenGBIF }) {
  const conErrores = resumen.estado !== "completed";
  return (
    <section
      style={{
        padding: "1rem",
        border: `1px solid ${BORDE}`,
        borderRadius: "0.5rem",
        backgroundColor: "#fff",
        marginTop: "1rem",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: "0.5rem" }}>
        <div>
          <div style={{ fontSize: "0.8rem", color: "#789", textTransform: "uppercase", letterSpacing: "0.05em" }}>
            Fuente
          </div>
          <div style={{ fontWeight: 700, color: VERDE_OSCURO }}>{resumen.fuente}</div>
        </div>
        <OrigenBadge origen={resumen.origen} />
      </div>

      <dl
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          gap: "0.5rem 1.5rem",
          margin: "0.75rem 0 0",
        }}
      >
        <div>
          <dt style={{ fontSize: "0.75rem", color: "#789" }}>Grupo taxonómico</dt>
          <dd style={{ margin: 0 }}>{resumen.grupo_taxonomico}</dd>
        </div>
        <div>
          <dt style={{ fontSize: "0.75rem", color: "#789" }}>Cobertura geográfica</dt>
          <dd style={{ margin: 0 }}>{resumen.cobertura_geografica}</dd>
        </div>
        <div>
          <dt style={{ fontSize: "0.75rem", color: "#789" }}>Última extracción</dt>
          <dd style={{ margin: 0 }}>{formatoFechaHora(resumen.extraido_utc)}</dd>
        </div>
        <div>
          <dt style={{ fontSize: "0.75rem", color: "#789" }}>Estado</dt>
          <dd style={{ margin: 0, color: conErrores ? "#8a1f1f" : "#1f5c3a", fontWeight: 600 }}>
            {resumen.estado}
          </dd>
        </div>
      </dl>

      {resumen.errores.length > 0 ? (
        <p style={{ marginTop: "0.5rem", color: "#8a1f1f", fontSize: "0.85rem" }}>
          Avisos de la consulta: {resumen.errores.join("; ")}
        </p>
      ) : null}
    </section>
  );
}

// --- Página ------------------------------------------------------------------

/** Vista principal de biodiversidad — Datos de GBIF. */
export function BiodiversidadPage() {
  const almacenado = useResumenGbif();
  const enVivo = useConsultaGbifEnVivo();

  // Se muestra el resultado en vivo si existe; si no, el almacenado. Así el
  // usuario ve de inmediato los datos guardados y, tras "Consultar GBIF", el
  // resultado fresco, siempre etiquetado con su origen.
  const resumen: ResumenGBIF | null = enVivo.data ?? almacenado.data;

  // Mensaje de estado de la acción en vivo (para el botón).
  const [ultimaAccion, setUltimaAccion] = useState<string | null>(null);

  function onConsultar() {
    setUltimaAccion(null);
    enVivo.consultar();
  }

  // Carga inicial del almacenado.
  if (almacenado.loading && !resumen) {
    return <LoadingIndicator message="Cargando cifras de GBIF almacenadas…" />;
  }

  // Si no hay almacenado NI resultado en vivo, se muestra el error del almacenado
  // (p. ej. 404 si aún no hay artefactos) con opción de reintentar.
  if (!resumen) {
    return (
      <div>
        <Encabezado />
        {almacenado.error ? (
          <ErrorBanner error={almacenado.error} onRetry={almacenado.reload} />
        ) : (
          <ErrorBanner
            error="No hay cifras de GBIF disponibles todavía."
            onRetry={almacenado.reload}
          />
        )}
        {/* La consulta en vivo (POST a GBIF) no está disponible en la demo
            estática: no hay backend que la ejecute (STATIC_MODE). */}
        {STATIC_MODE ? null : (
          <AccionConsultar
            loading={enVivo.loading}
            onConsultar={onConsultar}
            error={enVivo.error}
            mensaje={ultimaAccion}
          />
        )}
      </div>
    );
  }

  return (
    <div>
      <Encabezado />

      {/* La consulta en vivo (POST a GBIF) no está disponible en la demo
          estática: no hay backend que la ejecute (STATIC_MODE). */}
      {STATIC_MODE ? null : (
        <AccionConsultar
          loading={enVivo.loading}
          onConsultar={onConsultar}
          error={enVivo.error}
          mensaje={
            enVivo.data
              ? `Consulta en vivo completada (${formatoFechaHora(enVivo.data.extraido_utc)}).`
              : ultimaAccion
          }
        />
      )}

      <CabeceraResumen resumen={resumen} />

      {/* Métricas resumen */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: "0.75rem", marginTop: "1rem" }}>
        <MetricCard
          label="Registros de ocurrencia (aves, Colombia)"
          value={formatoEntero(resumen.total_registros_ocurrencia)}
          hint="Total agregado reportado por GBIF"
        />
        <MetricCard
          label="En millones"
          value={formatoMillones(resumen.total_registros_ocurrencia)}
          hint="Equivalente aproximado del total"
        />
        <MetricCard label="Publicadores en el ranking" value={resumen.publicadores.length} />
        <MetricCard label="Cortes históricos" value={resumen.cortes_historicos} />
      </div>

      <PublicadoresCard resumen={resumen} />
      <HistoricoCard resumen={resumen} />
      <ExportacionesCard resumen={resumen} />
      <LimitacionesCard />
    </div>
  );
}

/** Título y descripción de la vista. */
function Encabezado() {
  return (
    <div>
      <h2 style={{ marginBottom: "0.25rem" }}>Biodiversidad — Datos de GBIF</h2>
      <p style={{ color: "#567", marginTop: 0 }}>
        Cifras de <strong>registros de ocurrencia de aves</strong> en Colombia obtenidas de GBIF
        mediante consultas agregadas. Útil para dimensionar cuánta información de aves del país está
        documentada en la fuente y quién la aporta.
      </p>
    </div>
  );
}

/** Botón de consulta en vivo con su estado (carga / éxito / error). */
function AccionConsultar({
  loading,
  onConsultar,
  error,
  mensaje,
}: {
  loading: boolean;
  onConsultar: () => void;
  error: import("../services").ApiError | null;
  mensaje: string | null;
}) {
  return (
    <section style={{ margin: "1rem 0" }}>
      <div style={{ display: "flex", alignItems: "center", gap: "1rem", flexWrap: "wrap" }}>
        <button
          type="button"
          onClick={onConsultar}
          disabled={loading}
          style={{
            padding: "0.5rem 1.1rem",
            border: "none",
            borderRadius: "0.375rem",
            backgroundColor: loading ? "#9ac3ac" : VERDE,
            color: "#fff",
            fontWeight: 600,
            cursor: loading ? "default" : "pointer",
          }}
        >
          {loading ? "Consultando GBIF…" : "Consultar GBIF (en vivo)"}
        </button>
        {loading ? <LoadingIndicator message="Consultando GBIF en tiempo real…" /> : null}
        {!loading && mensaje ? (
          <span style={{ color: "#1f5c3a", fontSize: "0.9rem" }}>{mensaje}</span>
        ) : null}
      </div>
      {!loading && error ? <ErrorBanner error={error} onRetry={onConsultar} /> : null}
      <p style={{ color: "#789", fontSize: "0.78rem", marginTop: "0.4rem" }}>
        La consulta en vivo pregunta a GBIF en este momento y <strong>no</strong> sobrescribe los
        archivos almacenados. Puede tardar unos segundos.
      </p>
    </section>
  );
}
