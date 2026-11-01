---
name: engram-memory
description: "Gestión de memoria episódica y semántica persistente del proyecto con Engram (vía MCP o CLI). Cárgala para buscar aprendizajes previos sobre un módulo, recuperar soluciones a bugs recurrentes, consultar convenciones del repositorio o registrar nuevas lecciones aprendidas entre sesiones sin saturar el contexto."
version: 1.0.0
license: MIT
tags: [memory, engram, mcp, context, cross-session]
related_skills: [agent-routing]
---

# Memoria Episódica con Engram (`engram-memory`)

Esta *skill* define cómo los agentes consultan y alimentan la **memoria episódica** del proyecto utilizando [Engram](../../docs/glosario.md#engram) (de Gentleman Programming), ya sea mediante herramientas [MCP](../../docs/glosario.md#mcp) o mediante su interfaz de línea de comandos (CLI).

---

## 1. Las dos memorias del proyecto (no confundir)

| Dimensión | Memoria Operativa ([`tools/project-memory.py`](../../tools/project-memory.py)) | Memoria Episódica ([Engram](../../docs/glosario.md#engram)) |
|---|---|---|
| **Qué guarda** | Estado del plan: tareas, estado (`TODO`/`WIP`/`DONE`), iteraciones y consumo de tokens | Aprendizajes acumulados: decisiones técnicas, causas de bugs, convenciones y trucos del repositorio |
| **Naturaleza** | Estructurada, relacional y determinista | Textual, indexada con [FTS5 / BM25](../../docs/glosario.md#fts5--bm25) y semántica |
| **Acceso** | Script local en Python sobre SQLite (`.agents/memory.sqlite3`) | Servidor [MCP](../../docs/glosario.md#mcp), CLI (`engram`) o API HTTP |
| **Propósito** | Que el [`orchestrator`](../../agents/orchestrator.md) no pierda el plan ni el límite de 3 vueltas | Que ningún agente empiece de cero ni tropiece dos veces con la misma piedra |

---

## 2. Cuándo consultar Engram (`search`)

Los agentes deben realizar una búsqueda rápida antes de asumir o reinventar:

1. **Antes de diseñar o proponer arquitectura ([`architect`](../../agents/architect.md)):**
   - Buscar antecedentes de decisiones o alternativas descartadas:
     ```bash
     engram search "arquitectura OR base de datos OR auth"
     ```
2. **Antes de solucionar un bug complejo ([`implementer`](../../agents/implementer.md)):**
   - Comprobar si el síntoma o error ya ocurrió anteriormente en el proyecto:
     ```bash
     engram search "timeout OR race condition OR <nombre-de-libreria>"
     ```
3. **Antes de definir casos borde ([`qa`](../../agents/qa.md)):**
   - Consultar qué trampas o comportamientos inesperados se descubrieron en pruebas pasadas.

*(Si el entorno tiene configurado el servidor [MCP](../../docs/glosario.md#mcp), el agente utiliza directamente la herramienta `engram_search` sin necesidad de ejecutar comandos en terminal).*

---

## 3. Cuándo registrar un recuerdo (`save`)

No todo se guarda. Guardar demasiado genera ruido en las búsquedas; guardar poco provoca amnesia.

### ✅ Qué SÍ se guarda en Engram
- **Lecciones aprendidas:** *"La versión X de la librería Y produce fuga de memoria si no se cierra el canal manualmente"*.
- **Convenciones no evidentes:** *"En este proyecto los DTOs de respuesta siempre deben serializarse en snake_case"*.
- **Causas raíz de bugs resueltos:** *"El fallo en el login se debía a un desfase de reloj en el token JWT en entornos locales"*.
- **Compromisos asumidos en [ADRs](../../docs/glosario.md#adr):** resumen de por qué se eligió una solución sobre otra.

### ❌ Qué NUNCA se guarda en Engram
- **Secretos, tokens, contraseñas o claves privadas** (vulneración grave de seguridad).
- **Datos personales reales** ([PII](../../docs/glosario.md#pii)).
- **Estados temporales de tareas:** el estado `TODO`/`WIP`/`DONE` pertenece a [`tools/project-memory.py`](../../tools/project-memory.py).
- **Ficheros enteros copiados:** guarda la conclusión o el aprendizaje en 2 o 3 líneas, nunca volcados de código.

---

## 4. Comandos útiles de CLI

Si trabajas desde terminal o sin MCP:

```bash
# Inicializar Engram en el repositorio actual
engram init

# Guardar un aprendizaje (título y contenido)
engram save "SQLite WAL" "Al usar SQLite en entornos concurrentes activar siempre PRAGMA journal_mode=WAL"

# Buscar recuerdos por texto o palabras clave
engram search "sqlite wal"

# Ver contexto reciente de sesiones anteriores
engram context

# Ver estadísticas de la base de memoria
engram stats
```

---

## 5. Degradación elegante (Portabilidad Multi-LLM)

Engram es una capacidad **opcional y no bloqueante**:
- Si el entorno o el cliente cuenta con Engram instalado y configurado vía [MCP](../../docs/glosario.md#mcp), los agentes aprovechan la búsqueda semántica.
- Si Engram no está instalado en la máquina, los agentes continúan trabajando normalmente apoyándose en [`tools/project-memory.py`](../../tools/project-memory.py) y en [`docs/glosario.md`](../../docs/glosario.md) sin detener su flujo.
