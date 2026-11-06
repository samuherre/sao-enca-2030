# config/

Configuración NO sensible del sistema (`structure.md` §21, `tech.md` §26).

## Estado

Stack definido (Python/FastAPI, `tech.md` §3–§5, ADR-001). El formato concreto
de los archivos de configuración (p. ej. settings de Pydantic) se concretará al
configurar el proyecto. Esta carpeta queda reservada; los secretos van en
variables de entorno, no aquí (`.env.example` en la raíz).

## Puede contener (conceptual)

- Rutas de datos.
- Parámetros de procesamiento.
- Parámetros de clasificación y umbrales (cuando se definan).
- Configuración de logging.
- Valores por defecto y configuración por entorno.

## No almacenar

Contraseñas, tokens, API keys ni credenciales. Los secretos van en variables de
entorno (ver `.env.example` en la raíz). Separar configuración de código
(`tech.md` §26): no codificar rutas absolutas de un equipo específico.
