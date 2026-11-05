# Plantillas del brain (`codebase-onboarding`)

Plantillas de los cinco documentos que genera la [Fase 2](../SKILL.md#fase-2--redaccion-architect). Cópialas en `docs/` del repositorio objetivo y sustituye cada `<marcador>`.

Reglas comunes a todas:
- Cada afirmación lleva evidencia: un puntero `ruta:línea` relativo a la raíz del repositorio (por ejemplo, `src/pagos/cobro.ts:42`) o `commit <hash>`. Lo que se deduce sin ejecutar se marca como `inferido`; lo que no se puede señalar, como `supuesto`.
- Enlaces markdown solo entre documentos del brain, relativos a `docs/`. Nunca `file:///`.
- Las preguntas abiertas se citan por su identificador (`P-01`).
- Fechas absolutas (`AAAA-MM-DD`).

---

## 1. `docs/index.md`

```markdown
# Brain de <proyecto>

> Generado con codebase-onboarding el <AAAA-MM-DD>. Alcance: <repositorio entero | módulo>. Ubicación: <local sin versionar | versionado>.

| Documento | Qué contiene | Cuándo consultarlo |
| :--- | :--- | :--- |
| [architecture.md](architecture.md) | Propósito, stack con versiones, mapa de directorios y puntos de entrada | Al empezar cualquier tarea o planificar cambios estructurales |
| [flows.md](flows.md) | Flujos paso a paso de los casos de uso que se van a tocar | Al implementar, refactorizar o depurar lógica |
| [limitations-and-gotchas.md](limitations-and-gotchas.md) | Límites, comportamientos no evidentes, deuda y advertencias para agentes | **Siempre** antes de tocar lógica sensible, almacenamiento o integraciones |
| [decisions.md](decisions.md) | Decisiones de arquitectura (ADR), documentadas o inferidas | Al proponer dependencias, rediseños o cambios de persistencia |

Documentación existente del repositorio (contrastada con el código): <`AGENTS.md`, README, wiki... o «ninguna»>

## Datos sensibles

- <Qué no puede aparecer en el brain ni en la memoria: credenciales de X, datos personales de Y, valores reales de Z>

## Preguntas abiertas para el equipo

- **P-01** — <pregunta> — evidencia: `<ruta:línea>` — a quién: <rol, o «por determinar»>
```

---

## 2. `docs/architecture.md`

```markdown
# Arquitectura de <proyecto>

## 1. Propósito
<Qué problema resuelve y para quién, en tres líneas.> — `<README.md:línea>`

## 2. Stack y dependencias clave
| Pieza | Versión | Para qué | Fuente |
| --- | --- | --- | --- |
| <lenguaje o framework> | <x.y> | <uso> | `<package.json:línea>` |

## 3. Mapa de directorios
| Ruta | Responsabilidad |
| --- | --- |
| `<src/servicios/>` | <qué vive aquí> |

## 4. Puntos de entrada y arranque
- Arranque: <comando o fichero> — `<ruta:línea>`
- Tests: <cómo se ejecutan> — `<ruta>`
- Integración y despliegue: <qué valida y adónde despliega> — `<ruta>`
```

---

## 3. `docs/flows.md`

```markdown
# Flujos de <proyecto>

## 1. <Nombre del flujo, por ejemplo «Alta de pedido»>
**Disparador:** <petición HTTP, evento, tarea programada o acción de usuario> — `<ruta:línea>`
1. <Paso> — `<ruta:línea>`
2. <Paso> — `<ruta:línea>`

**Datos que toca:** <tablas, colas o ficheros>
**Errores y reintentos:** <cómo falla y qué hace, o `supuesto`>
```

---

## 4. `docs/limitations-and-gotchas.md`

```markdown
# Limitaciones, gotchas y deuda de <proyecto>

## 1. Limitaciones funcionales
- <Lo que el sistema no hace o hace con límites> — `<ruta:línea>`

## 2. Gotchas (comportamientos no evidentes)
### A. <Título corto>
<Qué pasa, por qué sorprende y cómo evitarlo.> — `<ruta:línea>`

## 3. Deuda técnica
- <Qué> — complejidad: <sencilla | media | complicada> — `<ruta:línea>`

## 4. Advertencias para agentes de IA
- <Regla concreta, por ejemplo «no cambies X sin actualizar Y» o «Z lo comparte el servicio W»>
```

---

## 5. `docs/decisions.md`

```markdown
# Decisiones de arquitectura (ADR) de <proyecto>

### ADR-001: <Decisión> — <documentada | inferida>
- **Contexto:** <qué problema había>
- **Decisión:** <qué se eligió> — evidencia: `<ruta:línea>`
- **Alternativas:** <las conocidas, o «desconocidas»>
- **Consecuencias:** <qué implica para quien toque el código>
- **Porqué:** <motivo documentado (`commit <hash>` o `ruta:línea`), o «pregunta abierta P-0X»>
```
