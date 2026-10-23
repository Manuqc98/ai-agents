# AI Agents — Sistema de Agentes Agnóstico de LLM

Equipo modular de agentes, *skills* (habilidades) y *specs* (especificaciones guiadas) para llevar software **desde el problema hasta el código verificado**, en español y **sin atarse a ningún modelo ni herramienta concreta**.

---

## 1. Principio rector: Agnóstico de LLM y de cliente (*Harness*)

Este repositorio está diseñado bajo dos reglas de portabilidad:

1. **Independencia de modelo (LLM-Agnostic):** ningún agente ni *skill* está atado a Claude, Gemini, GPT o Llama. Los agentes declaran **qué nivel de capacidad necesitan** (`sencilla`, `media`, `complicada`), y [`docs/LLM.md`](docs/LLM.md) traduce ese nivel al `<proveedor>/<modelo>` que decidas usar en cada momento.
2. **Independencia de herramienta (Harness-Agnostic):** funciona igual en Antigravity, Claude Code, OpenCode, Cursor, Codex o mediante llamadas directas por API.
   - **[`AGENTS.md`](AGENTS.md) es la única fuente de verdad** (estándar abierto [agents.md](https://agents.md/)).
   - `CLAUDE.md` es un enlace simbólico (*symlink*) a `AGENTS.md`, evitando duplicar y desincronizar ficheros.
   - Los permisos y límites de cada agente se declaran tanto en el frontmatter YAML (para clientes que lo soportan en frío) como en **instrucciones explícitas en el cuerpo del Markdown** (para que cualquier LLM los respete por comprensión lectora).

---

## 2. Estructura del repositorio

```text
.
├── AGENTS.md                  # Punto de entrada único: reglas de oro, circuitos y contrato de handoff
├── CLAUDE.md -> AGENTS.md     # Enlace simbólico para compatibilidad automática con Claude Code
├── README.md                  # Visión general, principios de portabilidad y hoja de ruta
├── agents/                    # Equipo mínimo viable de 4 roles (Iteración 2)
│   ├── orchestrator.md        # Coordinador: clasifica, delega, controla bucles y reporta
│   ├── architect.md           # Arquitecto: requisitos medibles, opciones, replanteo y ADRs
│   ├── implementer.md         # Implementador: código limpio, cambio mínimo y plan de reversión
│   └── qa.md                  # Verificador independiente: pruebas, evidencias y dictamen
├── skills/                    # Conocimiento modular cargado bajo demanda
│   └── agent-routing/         # Clasificación de peticiones, circuitos y contrato de traspaso
├── specs/                     # Guiones interactivos por fases (se poblará en la Iteración 4)
├── docs/
│   ├── LLM.md                 # Política de modelos multi-proveedor por nivel de complejidad
│   ├── glosario.md            # Vocabulario canónico compartido
│   └── plantillas/            # Plantillas neutras para crear nuevos agentes y skills
├── tests/
│   └── clasificacion.md       # Batería de 15 casos de regresión del enrutado (Tipo × Severidad)
└── tools/
    └── check-repo.py          # Validador determinista: enlaces+#anclas, frontmatter, portabilidad multi-LLM y clasificación
```

---

## 3. El equipo base (`agents/`)

| Agente | Rol | Nivel (`LLM.md`) | ¿Escribe código de producción? |
|---|---|---|---|
| [`orchestrator`](agents/orchestrator.md) | Clasifica, elige circuito, delega con contrato, corta bucles a la 3.ª vuelta y reporta desviación | `media` | **No** (`edit`/`write` denegados) |
| [`architect`](agents/architect.md) | Aterriza requisitos, hace [replanteo](docs/glosario.md#replanteo), compara opciones y redacta [ADRs](docs/glosario.md#adr) | `complicada` | **No** (`edit`/`write` denegados) |
| [`implementer`](agents/implementer.md) | Implementa cambios acotados, migraciones y correcciones con comprobación local | `media` | **Sí** (no firma su propio QA) |
| [`qa`](agents/qa.md) | Verifica criterios de aceptación con evidencias reales, añade tests y emite dictamen | `media` | **Solo tests** (prohibido tocar código de producción) |

---

## 4. Flujo de trabajo

Toda petición pasa primero por [`skills/agent-routing/SKILL.md`](skills/agent-routing/SKILL.md) para elegir el camino más ligero posible:

```text
[Petición] ──► Clasificar (Tipo × Severidad)
                  │
                  ├─► Quirúrgico : Incidencia bloqueante (mitigar → verificar → documentar)
                  ├─► Conciso    : Cambio acotado o consulta (ejecutar → verificar)
                  └─► Completo   : Diseño nuevo (Negocio → Arquitectura → Plan → Código → QA)
```

---

## 5. Hoja de ruta de construcción incremental

- [x] **Iteración 1 — El esqueleto agnóstico:** [`AGENTS.md`](AGENTS.md) único, política multi-modelo [`docs/LLM.md`](docs/LLM.md), enrutador [`skills/agent-routing/SKILL.md`](skills/agent-routing/SKILL.md), [`docs/glosario.md`](docs/glosario.md) base y plantillas universales en [`docs/plantillas/`](docs/plantillas/).
- [x] **Iteración 2 — El equipo mínimo viable (4 agentes):** [`orchestrator`](agents/orchestrator.md), [`architect`](agents/architect.md), [`implementer`](agents/implementer.md) y [`qa`](agents/qa.md).
- [x] **Iteración 3 — Guardarraíles deterministas:** validador en Python ([`tools/check-repo.py`](tools/check-repo.py)) y batería de regresión ([`tests/clasificacion.md`](tests/clasificacion.md)) para verificar enlaces, anclas, frontmatter y **portabilidad multi-LLM** sin consumir tokens.
- [ ] **Iteración 4 — Memoria persistente y specs:** estado en SQLite y guiones multifase bajo demanda.
