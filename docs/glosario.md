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

### Puerta de riesgo
Cálculo determinista del nivel de riesgo de un cambio (`bajo` | `alto`) a partir de su diff: rutas sensibles tocadas (secretos, autenticación, pagos, migraciones, dependencias, CI e infraestructura), líneas añadidas que mencionan tokens, contraseñas o credenciales, y tamaño. Lo calcula [`tools/risk-gate.py`](../tools/risk-gate.py), no el criterio de un modelo, y decide si [`security-reviewer`](../agents/security-reviewer.md) se suma a la revisión. El LLM puede subir el nivel con un motivo, nunca bajarlo.

### Memoria Operativa
Seguimiento estructurado y determinista del plan de trabajo (tareas, estados `TODO`/`WIP`/`DONE`, corte a las 3 vueltas y consumo de modelos por proveedor), persistido en SQLite mediante [`tools/project-memory.py`](../tools/project-memory.py).

### Memoria Episódica
Memoria histórica y acumulativa que preserva aprendizajes, convenciones no escritas, decisiones de diseño y soluciones a bugs entre sesiones y modelos, persistida mediante [Engram](#engram).

### Brain del proyecto
Contexto persistente de un repositorio objetivo que los agentes leen antes de actuar: la documentación viva de `docs/` (índice, arquitectura, flujos, limitaciones y decisiones) más sus aprendizajes en [Engram](#engram). Se genera al llegar a un repositorio nuevo con [`specs/codebase-onboarding`](../specs/codebase-onboarding/SKILL.md) y se actualiza cuando un cambio altera flujos, limitaciones o decisiones.

### Engram
Sistema de memoria persistente entre sesiones para agentes de programación creado por Alan Buscaglia (Gentleman Programming). Funciona como un binario en Go con SQLite y [FTS5 / BM25](#fts5--bm25) expuesto mediante el protocolo [MCP](#mcp) y CLI.

### MCP
**Model Context Protocol** — Protocolo abierto estándar para conectar modelos de lenguaje con herramientas locales, bases de datos y servidores de memoria externa (como Engram) de forma independiente del fabricante.

### FTS5 / BM25
Motor de búsqueda de texto completo (*Full-Text Search*) integrado en SQLite que utiliza el algoritmo de clasificación probabilístico BM25 (*Best Matching 25*) para ordenar resultados por relevancia.

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

### PII
**Personally Identifiable Information** — Información de identificación personal (nombres, correos, documentos de identidad, números de tarjeta). Nunca debe registrarse en memorias persistentes, logs ni tests sin anonimizar.

### Ponytail
Filosofía del *desarrollador senior pragmático* («el mejor código es el que no hace falta escribir») creada por Dietrich Gebert ([repositorio original](https://github.com/DietrichGebert/ponytail), licencia MIT) y adaptada en [`skills/ponytail`](../skills/ponytail/SKILL.md). Aplica la [escalera de simplicidad](#escalera-de-simplicidad) para evitar la sobreingeniería, capas de abstracción innecesarias y dependencias superfluas generadas por modelos de lenguaje.

### Escalera de Simplicidad
Orden de prioridades de [Ponytail](#ponytail) (*Ladder of Laziness*): se toma la primera opción que resuelva la tarea completa: 1) cuestionar si tiene que existir ([YAGNI](#yagni)), 2) reutilizar lo que ya tiene el proyecto, 3) usar la biblioteca estándar o la plataforma, 4) usar dependencias ya instaladas, 5) dejarlo en una línea legible de un vistazo y 6) escribir el mínimo código nuevo que funcione.

### YAGNI
**You Aren't Gonna Need It** — «No lo vas a necesitar».
Principio que descarta construir funcionalidades, opciones o abstracciones para necesidades hipotéticas: se implementa solo lo que hace falta hoy.

---

## 3. Métricas y fiabilidad

### KPI
**Key Performance Indicator** — Indicador clave de rendimiento.
Métrica continua que mide la salud de un proceso o producto. Para ser válido necesita cuatro elementos: **línea base** (valor actual), **objetivo**, **plazo** y **fuente de medida**. Sin línea base no es un KPI, es un deseo.

### SLO y SLA
- **SLO (*Service Level Objective*, objetivo de nivel de servicio):** meta interna medible de fiabilidad o rendimiento (por ejemplo, disponibilidad del 99,9 % o latencia `p95 < 200 ms`).
- **SLA (*Service Level Agreement*, acuerdo de nivel de servicio):** contrato externo con el cliente que incluye consecuencias o penalizaciones si se incumple. El SLO interno debe ser siempre más estricto que el SLA.

### p50 / p95 / p99
**Percentiles de latencia.** Medida del tiempo de respuesta que experimenta el 50 %, el 95 % o el 99 % de las peticiones. Se usa en lugar de la media aritmética porque la media oculta los casos lentos que sufren los usuarios reales.
