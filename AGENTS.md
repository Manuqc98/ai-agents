# AI Agents — Punto de entrada (`AGENTS.md`)

> **Fuente canónica única.** Este fichero sigue el estándar abierto [agents.md](https://agents.md/) y es el punto de entrada para **cualquier LLM y cualquier entorno** (Antigravity, Claude Code, OpenCode, Cursor, Codex o API).
> `CLAUDE.md` es un enlace simbólico a este fichero: **nunca mantengas dos copias separadas**.

Léelo completo antes de actuar.

---

## 1. Qué es este repositorio y cómo se organiza

Un sistema modular de agentes, *skills* (habilidades) y *specs* (especificaciones) para resolver problemas de software de principio a fin, en español y de forma **agnóstica al modelo de lenguaje (LLM)**.

| Carpeta | Qué contiene | Propósito |
|---|---|---|
| `agents/` | **Quién actúa**: roles con responsabilidades y límites claros | Separar quién diseña, quién implementa y quién verifica |
| `skills/` | **Qué saber**: metodologías y formatos que se cargan solo cuando hacen falta | Ahorrar ventana de contexto en cualquier modelo |
| `specs/` | **El itinerario**: guiones paso a paso para definir negocio o arquitectura | No programar a ciegas en tareas grandes |
| `docs/` | **La memoria estática**: [`glosario.md`](docs/glosario.md), [`LLM.md`](docs/LLM.md) y [`plantillas/`](docs/plantillas/) | Vocabulario común y configuración multi-modelo |
| `tools/` | **El control determinista**: scripts que validan y persisten el estado | No fiar a la memoria del LLM lo que puede comprobar un script |

### El equipo base (`agents/`)

| Agente | Rol | Nivel (`LLM.md`) | ¿Escribe código de producción? |
|---|---|---|---|
| [`orchestrator`](agents/orchestrator.md) | **Coordinador**: clasifica, elige circuito, delega con contrato, controla las 3 vueltas y reporta desviación | `media` | No |
| [`architect`](agents/architect.md) | **Arquitecto**: traduce requisitos ambiguos, hace [replanteo](docs/glosario.md#replanteo), compara opciones y escribe [ADRs](docs/glosario.md#adr) | `complicada` | No |
| [`implementer`](agents/implementer.md) | **Implementador**: escribe código y migraciones respetando el proyecto y con [plan de reversión](docs/glosario.md#plan-de-reversion) | `media` | Sí |
| [`qa`](agents/qa.md) | **Verificador independiente**: comprueba criterios de aceptación con evidencia real, añade tests y emite dictamen | `media` | Solo tests |

---

## 2. Lo primero: clasifica la petición

**Nunca empieces a trabajar sin clasificar.** El error más caro trabajando con agentes es meter una tarea de 10 minutos por una cadena de 6 fases, o intentar arreglar a ciegas un fallo crítico de producción.

Carga siempre [`skills/agent-routing/SKILL.md`](skills/agent-routing/SKILL.md) al recibir trabajo nuevo. Allí está la tabla canónica que cruza dos ejes:

1. **Eje 1 — Tipo:** `Incidencia` · `Soporte` · `Mejora Técnica` · `Mejora Funcional` · `Historia` · `Epic` · `Tarea` · `Diseño y prototipado`.
2. **Eje 2 — Severidad:**
   - `bloqueante`: caída de funcionalidad crítica (autenticación, pagos, datos principales), servicio global caído o fallo en **> 5 %** de las peticiones.
   - `atencion`: degradación local o fallo recurrente que aún no tumba el sistema global. *(Valor por defecto si faltan datos de impacto, declarándolo explícitamente).*
   - `observacion`: consulta, deuda técnica o mejora sin urgencia operativa.
3. **Resultado — Circuito:**
   - `quirurgico`: para incidencias bloqueantes (primero mitigar y restablecer con plan de reversión; luego verificar y documentar).
   - `conciso`: para tareas acotadas, soporte o mejoras con una única decisión de diseño.
   - `completo`: para construir algo nuevo que requiere alinear requisitos, arquitectura, plan, código y pruebas.

> **Regla de oro de selección:** ante la duda entre dos circuitos, **elige siempre el más ligero** y escala si se queda corto.

**Estados de una petición** (definidos en [`docs/glosario.md#estados`](docs/glosario.md#estados)):
`BACKLOG` → `TODO` → `WIP` → `REVIEW` → `DONE` (con `INWAIT` para bloqueos externos y `CANCELLED` para descartes).

---

## 3. Reglas de oro (innegociables para cualquier LLM)

1. **Español siempre.** Responde, documenta y razona en español, aunque el código, los logs o la documentación técnica estén en inglés. Cita en inglés solo términos literales de código o estándares.
2. **Clasifica antes de actuar (§2).** Tu primera respuesta ante un trabajo nuevo incluye siempre su bloque de clasificación.
3. **Portabilidad total (Multi-LLM y Multi-Cliente).**
   - Nunca escribas instrucciones que dependan de un único modelo o proveedor.
   - Usa niveles de capacidad (`sencilla` | `media` | `complicada`) definidos en [`docs/LLM.md`](docs/LLM.md).
   - Toda restricción de herramientas de un agente debe figurar tanto en su frontmatter YAML como **escrita en texto claro** en el cuerpo del fichero, para que funcione igual aunque el cliente no parsee permisos YAML.
4. **Un traspaso (*handoff*) sin contrato se rechaza.** Si recibes o delegas una tarea sin los campos de §4 (especialmente `aceptacion` y `devuelve-si`), devuélvela pidiendo el dato que falta. **Nunca rellenes huecos inventando.**
5. **Replanteo antes de tocar código.** Antes de ejecutar un plan, contrástalo con los ficheros reales, versiones y entorno del proyecto ([replanteo](docs/glosario.md#replanteo)). Si la realidad contradice el plan, para y avisa.
6. **Lectura libre; escritura externa o destructiva con confirmación.** Leer, buscar y analizar es libre. Borrar datos, hacer acciones irreversibles o escribir en sistemas externos (tickets, wikis, despliegues) requiere **confirmación explícita de la persona** y un [plan de reversión](docs/glosario.md#plan-de-reversion).
7. **El índice orienta; la fuente manda.** No afirmes datos concretos (versiones, rutas, precios, comportamientos) de memoria si puedes leer el fichero o la fuente viva. Si algo no está verificado, etiquétalo como supuesto.
8. **Fechas absolutas.** Escribe siempre `2026-10-23` en lugar de «hoy» o «ayer».
9. **Nadie valida su propio trabajo.** Quien implementa el código no da el visto bueno final de calidad (QA), y quien define métricas no las audita en solitario.
10. **Límite de tres iteraciones.** Si un mismo problema da **3 vueltas** de corrección sin resolverse, **para y escala a la persona** resumiendo qué se ha probado, qué se ha descartado con evidencia y qué opciones quedan.
11. **Conciso y con el porqué.** Explica el motivo antes que el detalle. Usa enlaces a [`docs/glosario.md`](docs/glosario.md) y expande cualquier acrónimo la primera vez que aparezca.

---

## 4. Contrato de traspaso (*Handoff*)

Todo relevo entre agentes (o entre fases de trabajo) utiliza esta estructura YAML. Funciona en cualquier LLM porque es texto estructurado y autoexplicativo:

```yaml
id:          <identificador estable estilo "sistema:modulo:sintoma">
de:          <agente o fase emisora>
a:           <agente o fase receptora>
tipo:        Incidencia | Soporte | Mejora Funcional | Mejora Técnica | Historia | Epic | Tarea | Diseño y prototipado
severidad:   bloqueante | atencion | observacion
circuito:    completo | conciso | quirurgico
estado:      TODO | WIP | INWAIT | REVIEW | DONE
objetivo:    <una sola frase clara; si hay dos objetivos, sepáralo en dos tareas>
entrada:     <rutas a ficheros y líneas — punteros, NUNCA bloques de código copiados>
aceptacion:  <criterio verificable para dar la tarea por terminada>
supuestos:   <asunciones realizadas, indicando su origen>
devuelve-si: <condición explícita bajo la cual el receptor DEBE rechazar el trabajo>
```

---

## 5. Convenciones al crear ficheros en este repositorio

- **Nombres en `kebab-case`** y descriptivos.
- **Agentes y *skills* en Markdown con frontmatter YAML neutro:** sigue siempre las plantillas de [`docs/plantillas/agent-template.md`](docs/plantillas/agent-template.md) y [`docs/plantillas/skill-template.md`](docs/plantillas/skill-template.md).
- **`description` orientada al disparador:** en cualquier *skill* o agente, el campo `description` debe explicar **cuándo activarlo**, no solo qué contiene.
- **Skills grandes divididas en dos capas:** el método principal va en `SKILL.md` (ligero para no saturar el contexto de modelos pequeños) y las plantillas o catálogos extensos van en una subcarpeta `references/`.
- **Commits en español e imperativo** con prefijo semántico: `agent:`, `skill:`, `spec:`, `docs:`, `tool:`, `chore:`.
