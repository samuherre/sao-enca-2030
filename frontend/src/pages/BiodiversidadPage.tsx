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

import { useState, type CSSProperties } from "react";
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

/**
 * Formato compacto para marcas de eje que abarcan varios órdenes de magnitud
 * (escala logarítmica): usa M para millones y K para miles. P. ej. 1 000 000 →
 * "1 M", 100 000 → "100 K". Evita el confuso "0,1 M" de la escala lineal.
 */
function formatoCompacto(valor: number | null | undefined): string {
  if (valor === null || valor === undefined) return "—";
  const abs = Math.abs(valor);
  const fmt = (n: number) =>
    new Intl.NumberFormat("es-CO", { maximumFractionDigits: 1 }).format(n);
  if (abs >= 1_000_000) return `${fmt(valor / 1_000_000)} M`;
  if (abs >= 1_000) return `${fmt(valor / 1_000)} K`;
  return fmt(valor);
}

/** Formatea un timestamp ISO UTC a fecha/hora legible, o "no disponible". */
function formatoFechaHora(iso: string | null | undefined): string {
  if (!iso) return "no disponible";
  const fecha = new Date(iso);
  if (Number.isNaN(fecha.getTime())) return iso;
  return `${fecha.toLocaleString("es-CO", { dateStyle: "medium", timeStyle: "short" })} (hora local)`;
}

/**
 * Enlace al portal web de GBIF con las ocurrencias de ESE publicador en
 * Colombia (country=CO + publishing_org=orgKey).
 *
 * NO se incluye el filtro de taxón: el portal web NO reconoce `taxon_key` en la
 * URL y lo interpreta como un término de búsqueda de nombre científico (p. ej.
 * "212"), lo que devolvía 0 resultados. Los filtros que el portal sí aplica
 * desde la URL son `country` y `publishing_org`; el usuario puede acotar a aves
 * con el selector de taxón del propio portal si lo necesita.
 */
function urlGbifPublicador(orgKey: string): string {
  const params = new URLSearchParams({
    country: "CO",
    publishing_org: orgKey,
  });
  return `https://www.gbif.org/occurrence/search?${params.toString()}`;
}

/**
 * Enlace a GBIF con TODAS las ocurrencias de Colombia (solo ``country=CO``),
 * usado por la fila/barra "Otros publicadores". El portal de GBIF no permite
 * filtrar por "todos los publicadores EXCEPTO estos", así que el enlace lleva al
 * conjunto nacional completo (que incluye a los no listados); así el usuario
 * llega al menos a los registros de Colombia, como pidió SAO. Se aclara en el
 * título del enlace para no dar a entender que filtra solo "los demás".
 */
function urlGbifColombia(): string {
  const params = new URLSearchParams({ country: "CO" });
  return `https://www.gbif.org/occurrence/search?${params.toString()}`;
}

/** Etiqueta de la barra/fila que agrupa a los publicadores fuera del ranking. */
const ETIQUETA_OTROS_PUBLICADORES = "Otros publicadores";

/**
 * Enlace a GBIF con las ocurrencias de un TIPO de registro (basisOfRecord) en
 * Colombia. El portal web SÍ aplica ``basis_of_record`` desde la URL (a
 * diferencia del taxón), así que el filtro funciona. ``codigo`` es el propio
 * valor de GBIF (p. ej. "HUMAN_OBSERVATION", "PRESERVED_SPECIMEN").
 */
function urlGbifTipoRegistro(codigo: string): string {
  const params = new URLSearchParams({
    country: "CO",
    basis_of_record: codigo,
  });
  return `https://www.gbif.org/occurrence/search?${params.toString()}`;
}

/**
 * Enlace a la VISTA DE MAPA de GBIF (mapa de calor de densidad de ocurrencias),
 * con los filtros que el portal aplica de forma fiable desde la URL: país y,
 * opcionalmente, publicador. La pestaña "MAP" del portal muestra el mapa de
 * calor hexagonal de GBIF.
 *
 * El filtro taxonómico NO se pone como `taxon_key` numérico: el portal lo
 * interpreta como nombre científico (bug conocido). Cuando se quiere acotar por
 * un orden/familia concreto se usa `urlGbifMapaTaxon` (página del taxón, que
 * trae su propio mapa).
 */
function urlGbifMapaPublicador(orgKey: string | null): string {
  const params = new URLSearchParams({ country: "CO" });
  if (orgKey) params.set("publishing_org", orgKey);
  return `https://www.gbif.org/occurrence/map?${params.toString()}`;
}

/**
 * Enlace al MAPA de un grupo taxonómico (orden o familia) en la página del
 * taxón de GBIF, que incluye su propio mapa de calor de ocurrencias. Se usa la
 * clave del backbone (taxonKey), que aquí SÍ es la vía correcta (no es el portal
 * de búsqueda por texto, sino la ficha del taxón).
 */
function urlGbifMapaTaxon(taxonKey: string): string {
  return `https://www.gbif.org/species/${encodeURIComponent(taxonKey)}`;
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

  const data = resumen.publicadores
    // En escala logarítmica un valor <= 0 no es representable; se excluye (no se
    // inventa un mínimo). En la práctica GBIF solo devuelve conteos positivos.
    .filter((p) => p.registros_ocurrencia > 0)
    .map((p) => ({
      etiqueta: p.nombre ?? p.org_key,
      registros: p.registros_ocurrencia,
    }));

  // "Otros publicadores" = total nacional − suma de los del ranking. Solo se
  // calcula si hay un total nacional fiable y queda remanente positivo; nunca
  // se inventa (si no hay total, no se añade la barra).
  const sumaTop = resumen.publicadores.reduce((acc, p) => acc + p.registros_ocurrencia, 0);
  const total = resumen.total_registros_ocurrencia;
  const otros = total !== null && total > sumaTop ? total - sumaTop : null;
  if (otros !== null) {
    data.push({ etiqueta: ETIQUETA_OTROS_PUBLICADORES, registros: otros });
  }

  const alto = Math.max(220, data.length * 40);

  // Dominio del eje logarítmico: de la menor potencia de 10 por debajo del
  // mínimo a la mayor por encima del máximo, para que cada barra sea visible
  // aunque un publicador concentre casi todos los registros.
  const valores = data.map((d) => d.registros);
  const minimo = valores.length > 0 ? Math.min(...valores) : 1;
  const maximo = valores.length > 0 ? Math.max(...valores) : 1;
  const dominioInferior = Math.pow(10, Math.floor(Math.log10(minimo)));
  const dominioSuperior = Math.pow(10, Math.ceil(Math.log10(maximo)));

  return (
    <section style={{ marginTop: "1.5rem" }}>
      <h3 style={{ marginBottom: "0.25rem" }}>Principales publicadores</h3>
      <p style={{ color: "#567", fontSize: "0.85rem", marginTop: 0 }}>
        Organizaciones que aportan más registros de ocurrencia de aves de Colombia a GBIF. El eje usa
        una <strong>escala logarítmica</strong>: cada marca representa diez veces más registros que la
        anterior, de modo que se aprecie la contribución de cada publicador aunque uno concentre la
        mayoría. Las cifras exactas están en la tabla inferior.
      </p>

      <div style={{ width: "100%", height: alto }}>
        <ResponsiveContainer>
          <BarChart
            layout="vertical"
            data={data}
            margin={{ top: 8, right: 32, bottom: 8, left: 8 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e3e8e5" />
            <XAxis
              type="number"
              scale="log"
              domain={[dominioInferior, dominioSuperior]}
              allowDataOverflow
              tickFormatter={(v: number) => formatoCompacto(v)}
            />
            <YAxis type="category" dataKey="etiqueta" width={200} tick={{ fontSize: 11 }} />
            <Tooltip
              formatter={(value: number) => [`${formatoEntero(value)} registros`, "Ocurrencias"]}
            />
            <Bar dataKey="registros" name="Registros" fill={VERDE} radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <p style={{ color: "#789", fontSize: "0.8rem", marginBottom: "0.25rem" }}>
        El nombre de cada publicador enlaza a sus registros en GBIF filtrados por publicador y
        Colombia (se abre en una pestaña nueva). "Otros publicadores" agrupa los registros fuera de
        este ranking; como GBIF no permite filtrar "todos excepto estos", su enlace lleva a todas las
        ocurrencias de aves de Colombia en GBIF.
      </p>

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
                <a
                  href={urlGbifPublicador(p.org_key)}
                  target="_blank"
                  rel="noopener noreferrer"
                  title="Ver en GBIF las ocurrencias de este publicador en Colombia"
                  style={{ color: VERDE_OSCURO, textDecoration: "underline" }}
                >
                  {p.nombre ?? (
                    <em style={{ color: "#888" }}>nombre no disponible ({p.org_key})</em>
                  )}
                </a>
              </td>
              <td style={{ padding: "0.4rem", textAlign: "right", borderBottom: "1px solid #eee" }}>
                {formatoEntero(p.registros_ocurrencia)}
              </td>
            </tr>
          ))}
          {otros !== null ? (
            <tr>
              <td style={{ padding: "0.4rem", borderBottom: "1px solid #eee", color: "#789" }}>—</td>
              <td style={{ padding: "0.4rem", borderBottom: "1px solid #eee" }}>
                <a
                  href={urlGbifColombia()}
                  target="_blank"
                  rel="noopener noreferrer"
                  title="GBIF no permite filtrar 'todos excepto estos'; este enlace lleva a todas las ocurrencias de aves de Colombia en GBIF"
                  style={{ color: VERDE_OSCURO, textDecoration: "underline" }}
                >
                  {ETIQUETA_OTROS_PUBLICADORES}
                </a>{" "}
                <span style={{ color: "#aaa", fontSize: "0.75rem" }}>
                  (resto no listado individualmente)
                </span>
              </td>
              <td style={{ padding: "0.4rem", textAlign: "right", borderBottom: "1px solid #eee" }}>
                {formatoEntero(otros)}
              </td>
            </tr>
          ) : null}
        </tbody>
      </table>
    </section>
  );
}

/** Gráfico + tabla de registros de aves por departamento de Colombia. */
function DepartamentosCard({ resumen }: { resumen: ResumenGBIF }) {
  const departamentos = resumen.departamentos;

  if (departamentos.length === 0) {
    return (
      <section style={{ marginTop: "1.5rem" }}>
        <h3 style={{ marginBottom: "0.5rem" }}>Registros por departamento</h3>
        <p style={{ color: "#666" }}>
          Este corte no incluye el desglose por departamento. Se generará en la próxima
          actualización de datos.
        </p>
      </section>
    );
  }

  // Suma por departamento vs. total nacional: parte de los registros de GBIF no
  // trae departamento, así que la suma será menor. Se informa con honestidad.
  const sumaDepartamentos = departamentos.reduce((acc, d) => acc + d.registros_ocurrencia, 0);
  const total = resumen.total_registros_ocurrencia;
  const sinDepartamento =
    total !== null && total >= sumaDepartamentos ? total - sumaDepartamentos : null;

  const data = departamentos.map((d) => ({
    etiqueta: d.departamento,
    registros: d.registros_ocurrencia,
  }));
  const alto = Math.max(260, data.length * 24);

  return (
    <section style={{ marginTop: "1.5rem" }}>
      <h3 style={{ marginBottom: "0.25rem" }}>Registros por departamento</h3>
      <p style={{ color: "#567", fontSize: "0.85rem", marginTop: 0 }}>
        Registros de ocurrencia de aves de Colombia por departamento, según el campo de ubicación de
        GBIF. Los registros que GBIF no asocia a ningún departamento no aparecen aquí, por lo que la
        suma por departamento es menor que el total nacional.
      </p>

      <div style={{ width: "100%", height: alto }}>
        <ResponsiveContainer>
          <BarChart
            layout="vertical"
            data={data}
            margin={{ top: 8, right: 32, bottom: 8, left: 8 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e3e8e5" />
            <XAxis type="number" tickFormatter={(v: number) => formatoCompacto(v)} />
            <YAxis type="category" dataKey="etiqueta" width={180} tick={{ fontSize: 11 }} />
            <Tooltip
              formatter={(value: number) => [`${formatoEntero(value)} registros`, "Ocurrencias"]}
            />
            <Bar dataKey="registros" name="Registros" fill={VERDE} radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {sinDepartamento !== null ? (
        <p style={{ color: "#789", fontSize: "0.8rem", marginTop: "0.25rem" }}>
          Registros sin departamento asignado en GBIF: {formatoEntero(sinDepartamento)} (no se
          reparten entre departamentos para no inventar una ubicación).
        </p>
      ) : null}

      <table style={{ borderCollapse: "collapse", width: "100%", marginTop: "0.5rem" }}>
        <thead>
          <tr>
            <th style={{ textAlign: "left", padding: "0.4rem", borderBottom: "2px solid #ccc" }}>#</th>
            <th style={{ textAlign: "left", padding: "0.4rem", borderBottom: "2px solid #ccc" }}>
              Departamento
            </th>
            <th style={{ textAlign: "right", padding: "0.4rem", borderBottom: "2px solid #ccc" }}>
              Registros de ocurrencia
            </th>
          </tr>
        </thead>
        <tbody>
          {departamentos.map((d) => (
            <tr key={d.departamento}>
              <td style={{ padding: "0.4rem", borderBottom: "1px solid #eee" }}>{d.rank}</td>
              <td style={{ padding: "0.4rem", borderBottom: "1px solid #eee" }}>{d.departamento}</td>
              <td style={{ padding: "0.4rem", textAlign: "right", borderBottom: "1px solid #eee" }}>
                {formatoEntero(d.registros_ocurrencia)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <RegionesBloque resumen={resumen} />
    </section>
  );
}

/**
 * Desglose por región geográfica de la ENCA, agregando los departamentos por su
 * región PREDOMINANTE. Es una propuesta del equipo (una región por
 * departamento), etiquetada como pendiente de confirmación de SAO: la geografía
 * de los departamentos fronterizos admite más de una región.
 */
function RegionesBloque({ resumen }: { resumen: ResumenGBIF }) {
  const regiones = resumen.regiones;

  return (
    <div style={{ marginTop: "1.25rem" }}>
      <h4 style={{ marginBottom: "0.25rem" }}>Por región geográfica de la ENCA</h4>
      <p
        style={{
          padding: "0.6rem 0.9rem",
          backgroundColor: "#faf3df",
          border: "1px solid #ecdcae",
          borderRadius: "0.375rem",
          color: "#5a4a1f",
          fontSize: "0.82rem",
          marginTop: 0,
        }}
      >
        <strong>Propuesta, pendiente de confirmación de SAO.</strong> Cada departamento se asigna a
        su región <strong>predominante</strong> (una región por departamento). Algunos departamentos
        son fronterizos y admiten más de una región; SAO puede ajustar la asignación.
      </p>

      {regiones.length === 0 ? (
        <p style={{ color: "#666", fontSize: "0.85rem" }}>
          Este corte no incluye la agrupación por región. Se generará en la próxima actualización.
        </p>
      ) : (
        <>
          <div style={{ width: "100%", height: Math.max(200, regiones.length * 40) }}>
            <ResponsiveContainer>
              <BarChart
                layout="vertical"
                data={regiones.map((r) => ({ etiqueta: r.region, registros: r.registros_ocurrencia }))}
                margin={{ top: 8, right: 32, bottom: 8, left: 8 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#e3e8e5" />
                <XAxis type="number" tickFormatter={(v: number) => formatoCompacto(v)} />
                <YAxis type="category" dataKey="etiqueta" width={120} tick={{ fontSize: 12 }} />
                <Tooltip
                  formatter={(value: number) => [`${formatoEntero(value)} registros`, "Ocurrencias"]}
                />
                <Bar dataKey="registros" name="Registros" fill={VERDE_OSCURO} radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <table style={{ borderCollapse: "collapse", width: "100%", marginTop: "0.5rem" }}>
            <thead>
              <tr>
                <th style={{ textAlign: "left", padding: "0.4rem", borderBottom: "2px solid #ccc" }}>#</th>
                <th style={{ textAlign: "left", padding: "0.4rem", borderBottom: "2px solid #ccc" }}>
                  Región ENCA
                </th>
                <th style={{ textAlign: "right", padding: "0.4rem", borderBottom: "2px solid #ccc" }}>
                  Registros de ocurrencia
                </th>
              </tr>
            </thead>
            <tbody>
              {regiones.map((r) => (
                <tr key={r.region}>
                  <td style={{ padding: "0.4rem", borderBottom: "1px solid #eee" }}>{r.rank}</td>
                  <td style={{ padding: "0.4rem", borderBottom: "1px solid #eee" }}>{r.region}</td>
                  <td style={{ padding: "0.4rem", textAlign: "right", borderBottom: "1px solid #eee" }}>
                    {formatoEntero(r.registros_ocurrencia)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </div>
  );
}

/** Gráfico + tabla de registros por tipo (basisOfRecord). */
function TipoRegistroCard({ resumen }: { resumen: ResumenGBIF }) {
  const tipos = resumen.tipos_registro;

  if (tipos.length === 0) {
    return (
      <section style={{ marginTop: "1.5rem" }}>
        <h3 style={{ marginBottom: "0.5rem" }}>Tipo de registro</h3>
        <p style={{ color: "#666" }}>
          Este corte no incluye el desglose por tipo de registro. Se generará en la próxima
          actualización.
        </p>
      </section>
    );
  }

  // Escala logarítmica (como en publicadores): "Observación humana" supera por
  // varios órdenes de magnitud al resto, así que en escala lineal las demás
  // barras son invisibles. En log cada tipo se aprecia. Un valor <= 0 no es
  // representable en log, por lo que se excluye del GRÁFICO (no de la tabla).
  const data = tipos
    .filter((t) => t.registros_ocurrencia > 0)
    .map((t) => ({ etiqueta: t.etiqueta, registros: t.registros_ocurrencia }));
  const alto = Math.max(200, data.length * 40);

  const valores = data.map((d) => d.registros);
  const minimo = valores.length > 0 ? Math.min(...valores) : 1;
  const maximo = valores.length > 0 ? Math.max(...valores) : 1;
  const dominioInferior = Math.pow(10, Math.floor(Math.log10(minimo)));
  const dominioSuperior = Math.pow(10, Math.ceil(Math.log10(maximo)));

  return (
    <section style={{ marginTop: "1.5rem" }}>
      <h3 style={{ marginBottom: "0.25rem" }}>Tipo de registro</h3>
      <p style={{ color: "#567", fontSize: "0.85rem", marginTop: 0 }}>
        Naturaleza del registro según GBIF: observación de una persona, observación automática
        (sensor/cámara), espécimen de museo preservado, etc. La inmensa mayoría son observaciones, no
        especímenes físicos. El eje usa una <strong>escala logarítmica</strong> (cada marca es diez
        veces la anterior) para que los tipos minoritarios sean visibles junto a la observación humana.
      </p>

      <div style={{ width: "100%", height: alto }}>
        <ResponsiveContainer>
          <BarChart
            layout="vertical"
            data={data}
            margin={{ top: 8, right: 32, bottom: 8, left: 8 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e3e8e5" />
            <XAxis
              type="number"
              scale="log"
              domain={[dominioInferior, dominioSuperior]}
              allowDataOverflow
              tickFormatter={(v: number) => formatoCompacto(v)}
            />
            <YAxis type="category" dataKey="etiqueta" width={220} tick={{ fontSize: 11 }} />
            <Tooltip
              formatter={(value: number) => [`${formatoEntero(value)} registros`, "Ocurrencias"]}
            />
            <Bar dataKey="registros" name="Registros" fill={VERDE} radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <p style={{ color: "#789", fontSize: "0.8rem", marginBottom: "0.25rem" }}>
        Cada tipo de registro enlaza a esas ocurrencias en GBIF, filtradas por Colombia (se abre en
        una pestaña nueva).
      </p>

      <table style={{ borderCollapse: "collapse", width: "100%", marginTop: "0.5rem" }}>
        <thead>
          <tr>
            <th style={{ textAlign: "left", padding: "0.4rem", borderBottom: "2px solid #ccc" }}>#</th>
            <th style={{ textAlign: "left", padding: "0.4rem", borderBottom: "2px solid #ccc" }}>
              Tipo de registro
            </th>
            <th style={{ textAlign: "right", padding: "0.4rem", borderBottom: "2px solid #ccc" }}>
              Registros de ocurrencia
            </th>
          </tr>
        </thead>
        <tbody>
          {tipos.map((t) => (
            <tr key={t.codigo}>
              <td style={{ padding: "0.4rem", borderBottom: "1px solid #eee" }}>{t.rank}</td>
              <td style={{ padding: "0.4rem", borderBottom: "1px solid #eee" }}>
                <a
                  href={urlGbifTipoRegistro(t.codigo)}
                  target="_blank"
                  rel="noopener noreferrer"
                  title="Ver en GBIF las ocurrencias de este tipo de registro en Colombia"
                  style={{ color: VERDE_OSCURO, textDecoration: "underline" }}
                >
                  {t.etiqueta}
                </a>{" "}
                <span style={{ color: "#aaa", fontSize: "0.75rem" }}>({t.codigo})</span>
              </td>
              <td style={{ padding: "0.4rem", textAlign: "right", borderBottom: "1px solid #eee" }}>
                {formatoEntero(t.registros_ocurrencia)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

/** Serie temporal de registros por año de evento. */
function AniosCard({ resumen }: { resumen: ResumenGBIF }) {
  // Año desde el cual mostrar: GBIF tiene registros desde el s. XVIII, pero con
  // cifras ínfimas; se muestra el periodo con datos significativos (>=1990) para
  // que la tendencia reciente sea legible. Los datos completos quedan en el dato
  // (y migran a ArcGIS); esto es solo el recorte de presentación.
  const ANIO_MINIMO = 1990;
  const serie = resumen.anios.filter((a) => a.anio >= ANIO_MINIMO);

  if (resumen.anios.length === 0) {
    return (
      <section style={{ marginTop: "1.5rem" }}>
        <h3 style={{ marginBottom: "0.5rem" }}>Registros por año</h3>
        <p style={{ color: "#666" }}>
          Este corte no incluye el desglose por año. Se generará en la próxima actualización.
        </p>
      </section>
    );
  }

  const data = serie.map((a) => ({ anio: String(a.anio), registros: a.registros_ocurrencia }));
  const primero = resumen.anios[0];
  const ultimo = resumen.anios[resumen.anios.length - 1];

  return (
    <section style={{ marginTop: "1.5rem" }}>
      <h3 style={{ marginBottom: "0.25rem" }}>Registros por año</h3>
      <p style={{ color: "#567", fontSize: "0.85rem", marginTop: 0 }}>
        Evolución del número de registros de ocurrencia de aves por <strong>año de observación</strong>{" "}
        (no de extracción). Se muestra desde {ANIO_MINIMO}; GBIF tiene registros más antiguos pero con
        cifras muy bajas. El año en curso suele verse incompleto.
      </p>

      <div style={{ width: "100%", height: 300 }}>
        <ResponsiveContainer>
          <BarChart data={data} margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e3e8e5" />
            <XAxis dataKey="anio" tick={{ fontSize: 10 }} interval="preserveStartEnd" />
            <YAxis tickFormatter={(v: number) => formatoCompacto(v)} tick={{ fontSize: 11 }} />
            <Tooltip
              formatter={(value: number) => [`${formatoEntero(value)} registros`, "Ocurrencias"]}
              labelFormatter={(label: string) => `Año ${label}`}
            />
            <Bar dataKey="registros" name="Registros" fill={VERDE} radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <p style={{ color: "#789", fontSize: "0.8rem", marginTop: "0.25rem" }}>
        Rango disponible en GBIF: {primero.anio}–{ultimo.anio}. El crecimiento reciente refleja sobre
        todo el auge de la ciencia ciudadana (observaciones en línea), no necesariamente cambios en las
        poblaciones de aves.
      </p>
    </section>
  );
}

/** Nº de municipios que se muestran en el gráfico (los demás, vía búsqueda). */
const MUNICIPIOS_EN_GRAFICO = 25;
/** Máximo de resultados que lista la búsqueda, para no volcar cientos. */
const MAX_RESULTADOS_BUSQUEDA = 50;

/** Normaliza para búsqueda: minúsculas y sin acentos. */
function normalizaBusqueda(texto: string): string {
  return texto
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
}

/** Gráfico + tabla de registros por municipio (top de GADM nivel 2). */
function MunicipiosCard({ resumen }: { resumen: ResumenGBIF }) {
  const municipios = resumen.municipios;
  const [consulta, setConsulta] = useState("");

  if (municipios.length === 0) {
    return (
      <section style={{ marginTop: "1.5rem" }}>
        <h3 style={{ marginBottom: "0.5rem" }}>Registros por municipio</h3>
        <p style={{ color: "#666" }}>
          Este corte no incluye el desglose por municipio. Se generará en la próxima actualización.
        </p>
      </section>
    );
  }

  // El gráfico muestra solo el top; la lista completa (todos los municipios con
  // registros) se explora con la búsqueda. Los datos ya vienen ordenados por
  // conteo descendente desde el pipeline.
  const top = municipios.slice(0, MUNICIPIOS_EN_GRAFICO);
  const data = top.map((m) => ({
    etiqueta: m.nombre ?? m.gadm_gid,
    registros: m.registros_ocurrencia,
  }));
  const alto = Math.max(260, data.length * 24);

  const conMas = municipios[0];

  // Búsqueda sobre TODOS los municipios (por nombre o código GADM).
  const q = normalizaBusqueda(consulta);
  const resultados = q
    ? municipios.filter(
        (m) =>
          normalizaBusqueda(m.nombre ?? "").includes(q) ||
          m.gadm_gid.toLowerCase().includes(q),
      )
    : [];

  return (
    <section style={{ marginTop: "1.5rem" }}>
      <h3 style={{ marginBottom: "0.25rem" }}>Registros por municipio</h3>
      <p style={{ color: "#567", fontSize: "0.85rem", marginTop: 0 }}>
        Registros de ocurrencia de aves por municipio de Colombia, según la ubicación GADM de GBIF.
        El gráfico muestra los {MUNICIPIOS_EN_GRAFICO} con más registros; el total disponible es de{" "}
        <strong>{formatoEntero(municipios.length)}</strong> municipios. Usa el buscador para
        encontrar cualquier municipio del país.
      </p>

      <p style={{ color: "#456", fontSize: "0.85rem", margin: "0 0 0.5rem" }}>
        El municipio con <strong>más</strong> registros es{" "}
        <strong>{conMas.nombre ?? conMas.gadm_gid}</strong> (
        {formatoEntero(conMas.registros_ocurrencia)}).
      </p>

      {/* Buscador entre todos los municipios */}
      <div style={{ margin: "0.5rem 0 0.75rem" }}>
        <input
          type="search"
          value={consulta}
          onChange={(e) => setConsulta(e.target.value)}
          placeholder="Buscar municipio (p. ej. Jericó, Leticia…)"
          aria-label="Buscar municipio"
          style={{
            width: "100%",
            maxWidth: 360,
            padding: "0.45rem 0.6rem",
            borderRadius: "0.4rem",
            border: `1px solid ${BORDE}`,
            fontSize: "0.9rem",
          }}
        />
        {q ? (
          resultados.length === 0 ? (
            <p style={{ color: "#789", fontSize: "0.85rem", marginTop: "0.4rem" }}>
              Sin coincidencias para “{consulta}”. (Solo aparecen municipios con al menos un registro
              de aves en GBIF.)
            </p>
          ) : (
            <table style={{ borderCollapse: "collapse", width: "100%", marginTop: "0.5rem" }}>
              <thead>
                <tr>
                  <th style={{ textAlign: "left", padding: "0.4rem", borderBottom: "2px solid #ccc" }}>
                    Municipio
                  </th>
                  <th style={{ textAlign: "right", padding: "0.4rem", borderBottom: "2px solid #ccc" }}>
                    Registros de ocurrencia
                  </th>
                </tr>
              </thead>
              <tbody>
                {resultados.slice(0, MAX_RESULTADOS_BUSQUEDA).map((m) => (
                  <tr key={m.gadm_gid}>
                    <td style={{ padding: "0.4rem", borderBottom: "1px solid #eee" }}>
                      {m.nombre ?? <em style={{ color: "#888" }}>sin nombre ({m.gadm_gid})</em>}
                    </td>
                    <td style={{ padding: "0.4rem", textAlign: "right", borderBottom: "1px solid #eee" }}>
                      {formatoEntero(m.registros_ocurrencia)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )
        ) : null}
        {q && resultados.length > MAX_RESULTADOS_BUSQUEDA ? (
          <p style={{ color: "#789", fontSize: "0.8rem", marginTop: "0.25rem" }}>
            Mostrando {MAX_RESULTADOS_BUSQUEDA} de {formatoEntero(resultados.length)} coincidencias;
            afina la búsqueda para ver menos.
          </p>
        ) : null}
      </div>

      <div style={{ width: "100%", height: alto }}>
        <ResponsiveContainer>
          <BarChart
            layout="vertical"
            data={data}
            margin={{ top: 8, right: 32, bottom: 8, left: 8 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e3e8e5" />
            <XAxis type="number" tickFormatter={(v: number) => formatoCompacto(v)} />
            <YAxis type="category" dataKey="etiqueta" width={160} tick={{ fontSize: 11 }} />
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
              Municipio
            </th>
            <th style={{ textAlign: "right", padding: "0.4rem", borderBottom: "2px solid #ccc" }}>
              Registros de ocurrencia
            </th>
          </tr>
        </thead>
        <tbody>
          {top.map((m) => (
            <tr key={m.gadm_gid}>
              <td style={{ padding: "0.4rem", borderBottom: "1px solid #eee" }}>{m.rank}</td>
              <td style={{ padding: "0.4rem", borderBottom: "1px solid #eee" }}>
                {m.nombre ?? <em style={{ color: "#888" }}>sin nombre ({m.gadm_gid})</em>}
              </td>
              <td style={{ padding: "0.4rem", textAlign: "right", borderBottom: "1px solid #eee" }}>
                {formatoEntero(m.registros_ocurrencia)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Nota de migración: el "cruce con el mapa de municipios" lo hace ArcGIS
          uniendo estos conteos con una capa de municipios por el código GADM
          (gadm_gid). No se dibuja aquí un mapa propio. */}
      <p
        style={{
          marginTop: "0.5rem",
          padding: "0.6rem 0.9rem",
          backgroundColor: FONDO_SUAVE,
          border: `1px solid ${BORDE}`,
          borderRadius: "0.375rem",
          color: "#456",
          fontSize: "0.8rem",
        }}
      >
        <strong>Nota (demo):</strong> el cruce con el mapa de municipios se hará en{" "}
        <strong>ArcGIS</strong>, uniendo estos conteos con una capa de municipios por su código GADM.
        Aquí se muestran las cifras; el mapa coroplético se monta con las herramientas de ArcGIS.
      </p>
    </section>
  );
}

/** Gráfico + tabla de registros por grupo taxonómico (orden o familia). */
function TaxonCard({
  titulo,
  descripcion,
  items,
  etiquetaColumna,
}: {
  titulo: string;
  descripcion: string;
  items: readonly import("../types").TaxonGBIF[];
  etiquetaColumna: string;
}) {
  if (items.length === 0) {
    return (
      <div style={{ marginTop: "1rem" }}>
        <h4 style={{ marginBottom: "0.25rem" }}>{titulo}</h4>
        <p style={{ color: "#666", fontSize: "0.85rem" }}>
          Este corte no incluye el desglose. Se generará en la próxima actualización.
        </p>
      </div>
    );
  }

  const data = items.map((t) => ({
    etiqueta: t.nombre ?? t.taxon_key,
    registros: t.registros_ocurrencia,
  }));

  return (
    <div style={{ marginTop: "1rem" }}>
      <h4 style={{ marginBottom: "0.25rem" }}>{titulo}</h4>
      <p style={{ color: "#567", fontSize: "0.85rem", marginTop: 0 }}>{descripcion}</p>

      <div style={{ width: "100%", height: Math.max(220, data.length * 28) }}>
        <ResponsiveContainer>
          <BarChart
            layout="vertical"
            data={data}
            margin={{ top: 8, right: 32, bottom: 8, left: 8 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e3e8e5" />
            <XAxis type="number" tickFormatter={(v: number) => formatoCompacto(v)} />
            <YAxis type="category" dataKey="etiqueta" width={160} tick={{ fontSize: 11 }} />
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
              {etiquetaColumna}
            </th>
            <th style={{ textAlign: "right", padding: "0.4rem", borderBottom: "2px solid #ccc" }}>
              Registros de ocurrencia
            </th>
          </tr>
        </thead>
        <tbody>
          {items.map((t) => (
            <tr key={t.taxon_key}>
              <td style={{ padding: "0.4rem", borderBottom: "1px solid #eee" }}>{t.rank}</td>
              <td style={{ padding: "0.4rem", borderBottom: "1px solid #eee" }}>
                {t.nombre ?? (
                  <em style={{ color: "#888" }}>nombre no disponible ({t.taxon_key})</em>
                )}
              </td>
              <td style={{ padding: "0.4rem", textAlign: "right", borderBottom: "1px solid #eee" }}>
                {formatoEntero(t.registros_ocurrencia)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/**
 * Mapa de calor de registros de GBIF (Opción B: enlace al mapa oficial de GBIF,
 * no un mapa embebido). Dos selectores: categoría taxonómica (todas las aves,
 * un orden o una familia) y procedencia/publicador (todos, eBird, iNaturalist…).
 *
 * Decisión de diseño (el destino del producto es ArcGIS): NO se construye un
 * mapa propio con Leaflet, que habría que rehacer en ArcGIS. Se enlaza al mapa
 * de calor que GBIF ya ofrece con esos filtros, y el mapa definitivo se montará
 * con las herramientas nativas de ArcGIS a partir de estos mismos filtros.
 */
function MapaCard({ resumen }: { resumen: ResumenGBIF }) {
  // Opciones taxonómicas: todas las aves + los órdenes y familias disponibles.
  const opcionesTaxon = [
    { clave: "212", etiqueta: "Todas las aves (Aves)" },
    ...resumen.ordenes.map((o) => ({
      clave: o.taxon_key,
      etiqueta: `Orden: ${o.nombre ?? o.taxon_key}`,
    })),
    ...resumen.familias.map((f) => ({
      clave: f.taxon_key,
      etiqueta: `Familia: ${f.nombre ?? f.taxon_key}`,
    })),
  ];

  const [taxonKey, setTaxonKey] = useState<string>("212");
  const [orgKey, setOrgKey] = useState<string>(""); // "" = todos los publicadores

  // Si hay un taxón concreto seleccionado (distinto de "todas las aves"), el
  // enlace fiable es la página del taxón (trae su mapa). Si es "todas las aves",
  // se usa el mapa del portal, que además puede filtrarse por publicador.
  const esTodasLasAves = taxonKey === "212";
  const enlace = esTodasLasAves
    ? urlGbifMapaPublicador(orgKey || null)
    : urlGbifMapaTaxon(taxonKey);

  const selectStyle: CSSProperties = {
    padding: "0.4rem 0.6rem",
    border: `1px solid ${BORDE}`,
    borderRadius: "0.375rem",
    fontSize: "0.9rem",
    minWidth: "220px",
  };

  return (
    <section style={{ marginTop: "1.5rem" }}>
      <h3 style={{ marginBottom: "0.25rem" }}>Mapa de registros (GBIF)</h3>
      <p style={{ color: "#567", fontSize: "0.85rem", marginTop: 0 }}>
        El mapa de calor de las ocurrencias de aves lo ofrece directamente GBIF. Elige la categoría
        taxonómica y la procedencia, y abre el mapa de GBIF ya filtrado (en una pestaña nueva).
      </p>

      <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap", alignItems: "flex-end" }}>
        <label style={{ display: "flex", flexDirection: "column", gap: "0.2rem", fontSize: "0.8rem", color: "#567" }}>
          Categoría taxonómica
          <select
            value={taxonKey}
            onChange={(e) => setTaxonKey(e.target.value)}
            style={selectStyle}
          >
            {opcionesTaxon.map((o) => (
              <option key={o.clave} value={o.clave}>
                {o.etiqueta}
              </option>
            ))}
          </select>
        </label>

        <label style={{ display: "flex", flexDirection: "column", gap: "0.2rem", fontSize: "0.8rem", color: "#567" }}>
          Procedencia (publicador)
          <select
            value={orgKey}
            onChange={(e) => setOrgKey(e.target.value)}
            disabled={!esTodasLasAves}
            title={
              esTodasLasAves
                ? undefined
                : "El filtro por publicador aplica al mapa general de aves; para un orden/familia concreto se abre la ficha del taxón en GBIF."
            }
            style={{ ...selectStyle, opacity: esTodasLasAves ? 1 : 0.5 }}
          >
            <option value="">Todas las fuentes</option>
            {resumen.publicadores.map((p) => (
              <option key={p.org_key} value={p.org_key}>
                {p.nombre ?? p.org_key}
              </option>
            ))}
          </select>
        </label>

        <a
          href={enlace}
          target="_blank"
          rel="noopener noreferrer"
          style={{
            padding: "0.5rem 1.1rem",
            borderRadius: "0.375rem",
            backgroundColor: VERDE,
            color: "#fff",
            fontWeight: 600,
            textDecoration: "none",
          }}
        >
          Abrir mapa en GBIF ↗
        </a>
      </div>

      <p style={{ color: "#789", fontSize: "0.78rem", marginTop: "0.5rem" }}>
        El filtro por procedencia se combina con el mapa de todas las aves; al elegir un orden o
        familia concretos se abre la ficha de ese taxón en GBIF, que incluye su propio mapa.
      </p>

      {/* Nota de migración a ArcGIS: el mapa de calor definitivo del sitio de
          SAO se montará con la capa nativa de ArcGIS Online, usando estos mismos
          filtros (taxón + publicador + país). No se construye un mapa propio que
          habría que rehacer. */}
      <p
        style={{
          marginTop: "0.5rem",
          padding: "0.6rem 0.9rem",
          backgroundColor: FONDO_SUAVE,
          border: `1px solid ${BORDE}`,
          borderRadius: "0.375rem",
          color: "#456",
          fontSize: "0.8rem",
        }}
      >
        <strong>Nota (demo):</strong> en el sitio definitivo de SAO el mapa de calor se integrará con
        las herramientas de mapas de <strong>ArcGIS</strong>, usando estos mismos filtros. Aquí se
        enlaza al mapa de GBIF para no duplicar trabajo que luego se rehace en ArcGIS.
      </p>
    </section>
  );
}

/** Sección de desglose taxonómico: órdenes y familias de aves. */
function TaxonomiaCard({ resumen }: { resumen: ResumenGBIF }) {
  if (resumen.ordenes.length === 0 && resumen.familias.length === 0) {
    return null;
  }
  return (
    <section style={{ marginTop: "1.5rem" }}>
      <h3 style={{ marginBottom: "0.25rem" }}>Por grupo taxonómico</h3>
      <p style={{ color: "#567", fontSize: "0.85rem", marginTop: 0 }}>
        Registros de ocurrencia de aves de Colombia por <strong>orden</strong> y por{" "}
        <strong>familia</strong> taxonómica (clasificación del backbone de GBIF). Se muestran los
        grupos con más registros.
      </p>
      <TaxonCard
        titulo="Órdenes con más registros"
        descripcion="Órdenes de aves ordenados por número de registros de ocurrencia."
        items={resumen.ordenes}
        etiquetaColumna="Orden"
      />
      <TaxonCard
        titulo="Familias con más registros"
        descripcion="Familias de aves ordenadas por número de registros de ocurrencia."
        items={resumen.familias}
        etiquetaColumna="Familia"
      />
    </section>
  );
}

/**
 * Módulo de especies amenazadas (UICN) + selector "registros por especie por
 * año". El endemismo NO se incluye: GBIF no marca especies endémicas de
 * Colombia y no existe una lista oficial validada por SAO (no se inventa).
 */
function AmenazadasCard({ resumen }: { resumen: ResumenGBIF }) {
  const categorias = resumen.iucn_categorias;
  const especies = resumen.especies_amenazadas;

  // Especie seleccionada en el desplegable (por species_key).
  const [seleccion, setSeleccion] = useState<string>(
    especies.length > 0 ? especies[0].species_key : "",
  );

  if (categorias.length === 0 && especies.length === 0) {
    return null;
  }

  const especie = especies.find((e) => e.species_key === seleccion) ?? especies[0];
  const serie = especie
    ? especie.por_anio.filter((p) => p.anio >= 1990).map((p) => ({
        anio: String(p.anio),
        registros: p.registros_ocurrencia,
      }))
    : [];

  function nombreEspecie(e: import("../types").EspecieAmenazada): string {
    if (e.nombre_comun && e.nombre_cientifico) return `${e.nombre_comun} (${e.nombre_cientifico})`;
    return e.nombre_cientifico ?? e.nombre_comun ?? e.species_key;
  }

  return (
    <section style={{ marginTop: "1.5rem" }}>
      <h3 style={{ marginBottom: "0.25rem" }}>Especies amenazadas</h3>
      <p style={{ color: "#567", fontSize: "0.85rem", marginTop: 0 }}>
        Registros de aves de Colombia según su categoría de amenaza en la{" "}
        <strong>Lista Roja de la UICN</strong> (dato de GBIF). "Amenazadas" agrupa las categorías
        Vulnerable (VU), En peligro (EN) y En peligro crítico (CR).
      </p>

      {/* Desglose por categoría UICN */}
      {categorias.length > 0 ? (
        <table style={{ borderCollapse: "collapse", width: "100%", marginBottom: "1rem" }}>
          <thead>
            <tr>
              <th style={{ textAlign: "left", padding: "0.4rem", borderBottom: "2px solid #ccc" }}>
                Categoría UICN
              </th>
              <th style={{ textAlign: "right", padding: "0.4rem", borderBottom: "2px solid #ccc" }}>
                Registros de ocurrencia
              </th>
            </tr>
          </thead>
          <tbody>
            {categorias.map((c) => (
              <tr key={c.codigo}>
                <td style={{ padding: "0.4rem", borderBottom: "1px solid #eee" }}>{c.etiqueta}</td>
                <td style={{ padding: "0.4rem", textAlign: "right", borderBottom: "1px solid #eee" }}>
                  {formatoEntero(c.registros_ocurrencia)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}

      {/* Selector de especie amenazada + serie por año */}
      {especies.length > 0 ? (
        <div>
          <h4 style={{ marginBottom: "0.25rem" }}>Registros por especie, por año</h4>
          <p style={{ color: "#567", fontSize: "0.85rem", marginTop: 0 }}>
            Elige una especie amenazada y mira la evolución de sus registros por año. Se listan las{" "}
            {especies.length} especies amenazadas con más registros.
          </p>

          <label
            style={{ display: "flex", flexDirection: "column", gap: "0.2rem", fontSize: "0.8rem", color: "#567", maxWidth: 480 }}
          >
            Especie amenazada
            <select
              value={seleccion}
              onChange={(e) => setSeleccion(e.target.value)}
              style={{
                padding: "0.4rem 0.6rem",
                border: `1px solid ${BORDE}`,
                borderRadius: "0.375rem",
                fontSize: "0.9rem",
              }}
            >
              {especies.map((e) => (
                <option key={e.species_key} value={e.species_key}>
                  {nombreEspecie(e)} — {e.iucn_etiqueta}
                </option>
              ))}
            </select>
          </label>

          {especie ? (
            <>
              <p style={{ color: "#456", fontSize: "0.85rem", margin: "0.5rem 0 0" }}>
                <strong>{nombreEspecie(especie)}</strong> — {especie.iucn_etiqueta}. Total de
                registros: {formatoEntero(especie.registros_ocurrencia)}.
              </p>

              {serie.length > 0 ? (
                <div style={{ width: "100%", height: 280, marginTop: "0.5rem" }}>
                  <ResponsiveContainer>
                    <BarChart data={serie} margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e3e8e5" />
                      <XAxis dataKey="anio" tick={{ fontSize: 10 }} interval="preserveStartEnd" />
                      <YAxis tickFormatter={(v: number) => formatoCompacto(v)} tick={{ fontSize: 11 }} />
                      <Tooltip
                        formatter={(value: number) => [`${formatoEntero(value)} registros`, "Ocurrencias"]}
                        labelFormatter={(label: string) => `Año ${label}`}
                      />
                      <Bar dataKey="registros" name="Registros" fill={VERDE_OSCURO} radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <p style={{ color: "#666", fontSize: "0.85rem" }}>
                  Sin registros con año asignado desde 1990 para esta especie.
                </p>
              )}
            </>
          ) : null}
        </div>
      ) : null}

      {/* Endemismo: pendiente de lista oficial de SAO (no se inventa). */}
      <p
        style={{
          marginTop: "0.75rem",
          padding: "0.6rem 0.9rem",
          backgroundColor: "#faf3df",
          border: "1px solid #ecdcae",
          borderRadius: "0.375rem",
          color: "#5a4a1f",
          fontSize: "0.82rem",
        }}
      >
        <strong>Especies endémicas: pendiente de validación.</strong> GBIF no marca qué especies son
        endémicas de Colombia; identificarlas requiere una lista oficial (p. ej. de SAO/ABO). Cuando
        SAO la proporcione, se cruza con estas especies por su nombre/clave. No se marca el endemismo
        de forma inventada.
      </p>
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
          <strong>Con desglose por departamento, municipio, región de la ENCA</strong> (la región es
          una propuesta por región predominante, pendiente de confirmación de SAO),{" "}
          <strong>por año</strong>, <strong>por grupo taxonómico</strong> (orden y familia) y{" "}
          <strong>por categoría de amenaza UICN</strong> (con serie por especie amenazada). El{" "}
          <strong>endemismo</strong> queda pendiente de una lista oficial de SAO. No se inventan
          datos ausentes.
        </li>
        <li>
          <strong>Es un borrador:</strong> esta vista muestra el contenido de forma preliminar; la
          versión definitiva de estos datos se publicará en ArcGIS.
        </li>
      </ul>
    </section>
  );
}

/**
 * Bloque colapsable con información de ADMINISTRACIÓN (no de usuario final):
 * histórico de ejecuciones de la consulta y archivos CSV preparados para ArcGIS.
 * Viene cerrado por defecto; el usuario de SAO no necesita verlo para entender
 * las cifras, pero se mantiene accesible por trazabilidad y uso interno.
 */
function DetallesTecnicos({ resumen }: { resumen: ResumenGBIF }) {
  return (
    <details
      style={{
        marginTop: "1.5rem",
        padding: "0.5rem 1rem",
        border: `1px solid ${BORDE}`,
        borderRadius: "0.5rem",
        backgroundColor: "#fbfdfc",
      }}
    >
      <summary style={{ cursor: "pointer", fontWeight: 600, color: "#567" }}>
        Detalles técnicos (uso interno)
      </summary>
      <p style={{ color: "#789", fontSize: "0.8rem", marginTop: "0.5rem" }}>
        Información de administración del piloto: no es necesaria para interpretar las cifras de
        arriba. Útil para el equipo que mantiene la actualización de datos.
      </p>

      {/* Estado de la última ejecución (antes en la cabecera; es dato operativo). */}
      <p style={{ color: "#567", fontSize: "0.85rem" }}>
        Estado de la última actualización: <strong>{resumen.estado}</strong>
        {resumen.errores.length > 0 ? (
          <span style={{ color: "#8a1f1f" }}> — avisos: {resumen.errores.join("; ")}</span>
        ) : null}
      </p>

      <HistoricoCard resumen={resumen} />
      <ExportacionesCard resumen={resumen} />
    </details>
  );
}

/**
 * Cabecera orientada al usuario de SAO: fuente, grupo taxonómico, cobertura y
 * fecha de actualización en lenguaje llano. Los detalles operativos (estado de
 * la ejecución, errores de la consulta, hora exacta de extracción) NO se
 * muestran aquí: son información de administración y viven en "Detalles
 * técnicos" al pie de la vista.
 */
function CabeceraResumen({ resumen }: { resumen: ResumenGBIF }) {
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
      <div style={{ fontSize: "0.8rem", color: "#789", textTransform: "uppercase", letterSpacing: "0.05em" }}>
        Fuente
      </div>
      <div style={{ fontWeight: 700, color: VERDE_OSCURO }}>{resumen.fuente}</div>

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
          <dt style={{ fontSize: "0.75rem", color: "#789" }}>Datos actualizados a</dt>
          <dd style={{ margin: 0 }}>{formatoFechaHora(resumen.extraido_utc)}</dd>
        </div>
      </dl>
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
        <MetricCard
          label="Publicadores principales"
          value={resumen.publicadores.length}
          hint="Organizaciones que más aportan (ver gráfico)"
        />
      </div>

      <PublicadoresCard resumen={resumen} />
      <TipoRegistroCard resumen={resumen} />
      <DepartamentosCard resumen={resumen} />
      <MunicipiosCard resumen={resumen} />
      <AniosCard resumen={resumen} />
      <TaxonomiaCard resumen={resumen} />
      <AmenazadasCard resumen={resumen} />
      <MapaCard resumen={resumen} />
      <LimitacionesCard />

      {/* Información de administración, no de valor para el usuario de SAO:
          el histórico de ejecuciones y los archivos CSV preparados para ArcGIS.
          Se oculta en un bloque colapsable para no saturar la vista, pero se
          conserva (trazabilidad) y queda a mano para uso interno. */}
      <DetallesTecnicos resumen={resumen} />
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
