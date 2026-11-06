# Registro de Decisiones de Arquitectura (ADR)

Registro de decisiones técnicas importantes del proyecto (`structure.md` §20.5).

No todas las decisiones requieren un ADR; sí las que afectan significativamente
la arquitectura o el funcionamiento del sistema.

## Índice

| ADR     | Título                                     | Estado                       |
| ------- | ------------------------------------------ | ---------------------------- |
| ADR-000 | Inicialización técnica neutral             | Aceptada (histórica)         |
| ADR-001 | Stack tecnológico inicial                  | Aceptada                     |
| ADR-009 | Librería de testing del frontend           | Aceptada                     |

Nota: la conclusión de ADR-000 sobre "stack completamente pendiente" quedó
superada por ADR-001.

## ADRs pendientes (previstos, aún no decididos)

Corresponden a decisiones que siguen `PENDING_VALIDATION` (`tech.md` §34). Se
crearán cuando cada decisión se evalúe y valide:

- ADR-002 — Metodología/modelo de clasificación bibliométrica (bloqueada por dataset P0)
- ADR-003 — Estrategia de deduplicación bibliográfica
- ADR-004 — Métricas y dimensiones del análisis bibliométrico
- ADR-005 — Estrategia de procesamiento de grandes volúmenes (si el volumen lo exige)
- ADR-006 — Uso de Docker, estrategia de despliegue y distribución local
- ADR-007 — Estrategia de actualización anual / versionamiento
- ADR-008 — Autenticación, autorización y roles (si se requiere)

La numeración es orientativa y puede ajustarse al tomar cada decisión.

Nota: ADR-009 (librería de testing del frontend) ya fue decidida — ver el índice
anterior.
