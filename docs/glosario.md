# Glosario Canónico (`glosario.md`)

> **Fuente única de vocabulario.** Ningún agente, *skill* ni documento redefine términos por su cuenta: enlaza siempre a las entradas de este fichero. La primera vez que aparezca un acrónimo en un documento, escríbela completa seguida de su explicación breve y su enlace.

---

## 1. Conceptos del sistema de agentes

### Agente
Rol especializado con un propósito acotado, un nivel de capacidad asignado (`nivel-modelo`) y límites explícitos sobre qué puede y qué no puede hacer (por ejemplo, diseñar sin tocar código o auditar sin implementar).

### Skill (Habilidad)
Módulo de conocimiento reutilizable (`skills/<nombre>/SKILL.md`) que explica **cómo** realizar un procedimiento concreto (clasificar una petición, escribir un test, redactar una decisión de arquitectura). Se carga bajo demanda para no saturar la ventana de contexto del LLM.

### Spec (Especificación guiada)
Guion interactivo por fases (`specs/<nombre>/SKILL.md`) que conduce una conversación desde una idea abierta hasta un entregable estructurado y verificado, sin asumir requisitos en silencio.

### Harness (Cliente o entorno de ejecución)
La herramienta o interfaz que ejecuta al modelo de lenguaje y le proporciona acceso a ficheros y terminal (por ejemplo: Antigravity, Claude Code, OpenCode, Cursor, Codex o un script propio vía API). Este repositorio se diseña para no depender de un *harness* único.

### Handoff (Contrato de traspaso)
Bloque estructurado de metadatos que acompaña cualquier delegación entre agentes o fases. Incluye objetivo único, punteros de entrada (nunca texto copiado), criterio de aceptación verificable, supuestos y condición de rechazo (`devuelve-si`).

### Circuito
El camino que recorre una petición según su tipo y severidad (definido en [`skills/agent-routing/SKILL.md`](../skills/agent-routing/SKILL.md)):
- **`quirurgico`**: para incidencias críticas; prioriza restablecer el servicio con cambio mínimo reversible antes de pasar por el ciclo completo.
- **`conciso`**: para tareas acotadas, consultas o mejoras con una única decisión de diseño.
- **`completo`**: ciclo integral de negocio, arquitectura, planificación, implementación y verificación.

### Estados
Ciclo de vida estándar de cualquier petición o tarea:
- `BACKLOG`: identificada pero aún no priorizada.
- `TODO`: lista para empezar, con contrato de aceptación claro.
- `WIP` (*Work In Progress*): en ejecución activa.
- `INWAIT`: pausada esperando respuesta de la persona o de un tercero.
- `REVIEW`: implementada y pendiente de validación independiente (QA o revisión).
- `DONE`: verificada y documentada.
- `CANCELLED`: descartada explícitamente (dejando anotado el motivo).

### Replanteo
Comprobación de solo lectura que contrasta un plan o diseño contra la realidad del proyecto (ficheros existentes, versiones instaladas, esquema de datos real) **antes** de empezar a modificar código.

### Plan de reversión
Procedimiento concreto y verificado para deshacer un cambio destructivo, migración o mitigación en caso de fallo, escrito **antes** de aplicar la acción.

---

## 2. Ingeniería de software y arquitectura

### SDD
**Spec-Driven Development** — Desarrollo guiado por especificación.
Metodología en la que primero se acuerda el comportamiento esperado, las restricciones y los criterios de aceptación en una especificación escrita, y después se genera y valida el código contra ella.

### ADR
**Architecture Decision Record** — Registro de decisión de arquitectura.
Documento breve que captura una decisión técnica importante: el contexto, las opciones evaluadas (mínimo dos), la opción elegida y sus consecuencias (*trade-offs*). Evita volver a discutir lo mismo seis meses después.

### Deuda técnica
Trabajo pendiente o solución subóptima asumida conscientemente para cumplir un plazo o mitigar una incidencia. En este sistema toda deuda declarada debe llevar **qué queda pendiente** y **su complejidad estimada** (`sencilla` | `media` | `complicada`).

### Idempotencia
Propiedad de una operación por la cual ejecutarla una vez o varias veces con los mismos datos produce exactamente el mismo resultado (imprescindible en pagos, envíos de mensajes y migraciones).

### MVP y PoC
- **MVP (*Minimum Viable Product*, producto mínimo viable):** la versión más pequeña de una solución que entrega valor real en producción con calidad, seguridad y tests suficientes.
- **PoC (*Proof of Concept*, prueba de concepto):** experimento técnico acotado y descartable para validar si una idea es viable. **Nunca se pasa una PoC directamente a producción.**

---

## 3. Métricas y fiabilidad

### KPI
**Key Performance Indicator** — Indicador clave de rendimiento.
Métrica continua que mide la salud de un proceso o producto. Para ser válido necesita cuatro elementos: **línea base** (valor actual), **objetivo**, **plazo** y **fuente de medida**. Sin línea base no es un KPI, es un deseo.

### SLO y SLA
- **SLO (*Service Level Objective*, objetivo de nivel de servicio):** meta interna medible de fiabilidad o rendimiento (por ejemplo, disponibilidad del 99,9 % o latencia `p95 < 200 ms`).
- **SLA (*Service Level Agreement*, acuerdo de nivel de servicio):** contrato externo con el cliente que incluye consecuencias o penalizaciones si se incumple. El SLO interno debe ser siempre más estricto que el SLA.

### p50 / p95 / p99 (Percentiles de latencia)
Medida del tiempo de respuesta que experimenta el 50 %, el 95 % o el 99 % de las peticiones. Se usa en lugar de la media aritmética porque la media oculta los casos lentos que sufren los usuarios reales.
