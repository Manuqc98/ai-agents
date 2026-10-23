# Política de Modelos (`LLM.md`) — Agnóstica de Proveedor

En este repositorio **ningún agente ni *skill* está acoplado a un modelo o fabricante concreto**.

Los agentes declaran únicamente **qué nivel de capacidad cognitiva requiere su rol** (`sencilla`, `media` o `complicada`), y este fichero traduce cada nivel al `<proveedor>/<modelo>` activo en tu entorno. Así puedes cambiar de Google Gemini a Anthropic Claude, OpenAI, OpenRouter o modelos locales (Ollama / vLLM) tocando solo este fichero.

---

## 1. Configuración activa por defecto

Edita este bloque según las suscripciones, claves de API o modelos locales que tengas disponibles:

```yaml
# Formato estandarizado: <proveedor>/<identificador-modelo>
# Proveedores soportados: google | anthropic | openai | openrouter | local

default: google/gemini-3.1-pro

complejidad:
  sencilla:   google/gemini-3-flash          # Tareas rápidas: formato, documentación, consultas con fuente
  media:      google/gemini-3.1-pro          # Tareas acotadas: implementación, tests, coordinación
  complicada: anthropic/claude-opus-5-5      # Decisiones críticas: arquitectura, auditoría, triaje complejo

# Opcional: forzar un modelo concreto para un rol específico en este proyecto
agentes: {}
  # orchestrator: google/gemini-3.1-pro
  # docs-writer:  local/qwen3-coder-32b
```

---

## 2. Qué significa cada nivel de capacidad

| Nivel | Tipo de trabajo | Criterio para elegir el modelo | Roles típicos |
|---|---|---|---|
| `sencilla` | Resumir, formatear, buscar en documentación con fuente citada, actualizar glosarios | Modelo rápido y económico (baja latencia y bajo coste por millón de tokens). El error es fácil de detectar leyendo. | Documentación, soporte con fuente, memoria |
| `media` | Programar funcionalidades acotadas, escribir tests, planificar tareas, coordinar pasos | Modelo equilibrado en código y seguimiento de instrucciones (*instruction following*), con criterio de aceptación verificable. | Coordinador, implementador, QA, planificador |
| `complicada` | Diseñar arquitectura, tomar decisiones con *trade-offs* (compromisos técnicos), auditar requisitos o diagnosticar incidencias críticas | Modelo de máximo razonamiento disponible. Un error aquí se propaga a todas las fases siguientes y sale más caro que los tokens ahorrados. | Arquitecto, analista de negocio, auditor, respuesta a incidentes |

---

## 3. Matriz de equivalencia multi-proveedor (Referencia)

Cuando quieras cambiar de proveedor o combinar varios, usa esta correspondencia por nivel:

| Nivel | Google (Gemini) | Anthropic (Claude) | OpenAI (GPT) | Local / Open-Weights (Ollama / vLLM) |
|---|---|---|---|---|
| `sencilla` | `google/gemini-3-flash` | `anthropic/claude-haiku-5-5` | `openai/gpt-6-luna` | `local/llama-3.3-8b` / `local/qwen3-14b` |
| `media` | `google/gemini-3.1-pro` | `anthropic/claude-sonnet-5-5` | `openai/gpt-6.1-sol` | `local/qwen3-coder-32b` / `local/deepseek-v3` |
| `complicada` | `google/gemini-4-argon` / `gemini-3.1-pro` | `anthropic/claude-opus-5-5` | `openai/gpt-6-astra` | `local/deepseek-r1` / `local/qwen3-235b` |

> **Nota sobre identificadores:** los nombres de modelos cambian con frecuencia. Verifica siempre el ID exacto en la documentación oficial de tu proveedor o CLI antes de fijarlo en producción.

---

## 4. Orden de resolución

Cuando se ejecuta una tarea o se invoca a un subagente, el modelo efectivo se decide en este orden (de más específico a más general):

1. **Manual:** indicación explícita de la persona en la conversación (*«ejecuta esto con el modelo X»*). Gana siempre.
2. **Override de agente en `LLM.md`:** si el agente figura en el bloque `agentes:` de este fichero.
3. **Nivel del agente (`nivel-modelo`):** el nivel declarado en el frontmatter del agente (`sencilla` | `media` | `complicada`), traducido mediante el bloque `complejidad:` de este fichero.
4. **Complejidad de la tarea:** el nivel asignado a la tarea concreta si no interviene un agente específico.
5. **`default`:** el modelo por defecto si ninguna regla anterior aplica.

**Regla de conflicto:** si el agente tiene nivel `sencilla` pero la tarea se ha clasificado como `complicada`, no se asume en silencio: **se pregunta a la persona** o se eleva al nivel superior de la tarea.
