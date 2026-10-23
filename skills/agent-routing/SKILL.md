---
name: agent-routing
description: Clasifica cualquier petición entrante (Tipo × Severidad), decide el circuito de trabajo (quirurgico, conciso o completo), define el contrato de traspaso (handoff) entre agentes y regula las condiciones de rechazo y el límite de 3 iteraciones. Cárgala SIEMPRE al recibir una petición nueva, al cambiar la naturaleza de una tarea en curso o antes de delegar en otro agente.
version: 1.0.0
license: MIT
tags: [routing, orchestration, triage, handoff, workflow]
related_skills: []
---

# Enrutado de peticiones y contrato entre agentes (`agent-routing`)

Esta *skill* resuelve únicamente dos decisiones:

1. **¿Qué camino recorre esta petición y quién interviene?** → Clasificación y circuito.
2. **¿Con qué contrato pasa el testigo de un paso al siguiente?** → Contrato de traspaso (*handoff*).

---

## 1. Clasificar en dos ejes (en este orden)

### Eje 1 — Tipo

Taxonomía independiente de cualquier herramienta de tickets (Jira, Linear, GitHub Issues):

| Tipo | Qué es | Señal típica en la petición |
|---|---|---|
| `Incidencia` | Algo que funcionaba ha dejado de funcionar o se degrada en producción | "da error", "se ha caído", "falla desde..." |
| `Soporte` | Consulta, duda, análisis o explicación que no requiere cambiar el sistema | "¿por qué pasa...?", "analiza esto", "¿dónde está...?" |
| `Mejora Técnica` | Cambio interno sin efecto funcional visible (refactor, actualización, rendimiento, deuda) | "limpiar", "actualizar librería", "optimizar consulta" |
| `Mejora Funcional` | Amplía o modifica lo que el usuario puede hacer sobre algo ya existente | "añadir filtro", "que además permita..." |
| `Historia` | Funcionalidad nueva acotada, con actor y valor claros | "crear módulo de...", "como X quiero Y para Z" |
| `Epic` | Iniciativa grande que abarca varias historias y requiere descomposición previa | Un objetivo amplio, no un entregable único |
| `Tarea` | Acción mecánica y acotada sin decisiones de diseño | "renombrar", "crear carpeta", "ajustar configuración" |
| `Diseño y prototipado` | Explorar arquitectura, comparar alternativas o hacer una [PoC](../../docs/glosario.md#mvp-y-poc) antes de construir | "¿cómo plantearíamos...?", "propón una arquitectura" |

**Reglas de desempate (por prioridad):**
1. Si hay impacto activo en producción ahora mismo → `Incidencia` (aunque esté formulado como pregunta).
2. Si el entregable esperado es información/análisis y no cambios en el sistema → `Soporte`.
3. Si no cambia el comportamiento percibido por el usuario final → `Mejora Técnica`.
4. Si no cabe en un entregable verificable único → `Epic` (el primer paso es partirlo).

---

### Eje 2 — Severidad

Basada en criterios objetivos, no en sensaciones:

| Severidad | Criterio objetivo |
|---|---|
| `bloqueante` | Afecta a un flujo crítico (autenticación, cobros, pérdida de datos), cae el servicio global **o** falla más del **5 %** de las peticiones. |
| `atencion` | Degradación parcial, error intermitente o fallo acotado a un módulo no crítico. *(Si faltan datos para medir el impacto, se clasifica como `atencion` por defecto y se declara).* |
| `observacion` | Sin impacto operativo inmediato: dudas, análisis, mejoras planificadas, deuda técnica o ruido en logs. |

---

## 2. Elegir el circuito

| Tipo | Severidad | Circuito | Recorrido de roles |
|---|---|---|---|
| `Incidencia` | `bloqueante` | **quirurgico** | Diagnóstico → Mitigación reversible (`implementer`) → Mini-verificación (`qa`) → Documentación |
| `Incidencia` | `atencion` / `observacion` | **conciso** | Diagnóstico → `implementer` → `qa` |
| `Soporte` | cualquiera | **conciso** | Respuesta con fuente verificada (+ documentación si es recurrente) |
| `Mejora Técnica` | cualquiera | **conciso** | `architect` → `implementer` → `qa` |
| `Tarea` | cualquiera | **conciso** | `implementer` → `qa` |
| `Diseño y prototipado` | cualquiera | **conciso / acotado** | `architect` (análisis, opciones y [ADR](../../docs/glosario.md#adr), sin fase de implementación) |
| `Mejora Funcional` | cualquiera | **completo** | Requisitos → `architect` → Plan → `implementer` → `qa` |
| `Historia` | cualquiera | **completo** | Requisitos → `architect` → Plan → `implementer` → `qa` |
| `Epic` | cualquiera | **completo** | Descomposición en historias → un ciclo por historia |

### Formato de salida al clasificar

Toda petición nueva o reclasificada comienza mostrando este bloque:

```text
Clasificación
  id:        <sistema:modulo:sintoma>
  tipo:      <Tipo> — <motivo en media línea>
  severidad: <Severidad> — <criterio que cumple>
  circuito:  <quirurgico | conciso | completo>
  ruta:      <rol 1> → <rol 2> → ...
Lo que falta por aclarar: <preguntas concretas, o "nada, procedo">
```

---

## 3. El contrato de traspaso (*Handoff*)

Cada vez que un agente o fase pasa trabajo al siguiente, entrega esta ficha completa:

```yaml
id:          <fingerprint estable: "sistema:modulo:sintoma">
de:          <rol emisor>
a:           <rol receptor>
tipo:        Incidencia | Soporte | Mejora Funcional | Mejora Técnica | Historia | Epic | Tarea | Diseño y prototipado
severidad:   bloqueante | atencion | observacion
circuito:    completo | conciso | quirurgico
estado:      TODO | WIP | INWAIT | REVIEW | DONE
objetivo:    <una sola frase; si necesitas dos frases, son dos tareas distintas>
entrada:     <rutas a ficheros y líneas — punteros, NUNCA contenido copiado>
aceptacion:  <criterio verificable para darlo por válido>
supuestos:   <asunciones hechas y su origen>
devuelve-si: <condición explícita bajo la cual el receptor DEBE rechazar el trabajo>
```

### Por qué tres campos son críticos en cualquier LLM

1. **`id` estable:** si el mismo fallo vuelve a ocurrir mañana, conserva el mismo `id`. Permite detectar problemas repetidos en lugar de tratarlos como nuevos.
2. **`entrada` por punteros:** pasar rutas (`src/auth/login.ts:42`) en vez de pegar código evita contaminar la ventana de contexto del receptor y garantiza que lea la versión real del fichero.
3. **`devuelve-si` (permiso para decir «no»):** los LLM tienden por defecto a complacer e inventar lo que falta. Definir explícitamente cuándo debe rechazar la tarea evita alucinaciones en cadena.

---

## 4. Realimentación, corte de bucles y escalado

### Adónde vuelve un fallo

| Qué ha fallado | Vuelve a | Motivo |
|---|---|---|
| Los tests fallan o el código no cumple lo especificado | `implementer` | Defecto de implementación |
| La realidad del código/entorno contradice el diseño ([replanteo](../../docs/glosario.md#replanteo)) | `architect` | El plan asumía algo que no existe en el repositorio |
| El código funciona pero no resuelve el problema real del usuario | Fase de requisitos / Persona | Defecto de definición funcional |

### Regla de las 3 vueltas (Corte de bucle)

Si dos roles intercambian el mismo `id` **tres veces** sin converger:
1. **Se detiene el bucle inmediatamente** (prohibida una cuarta iteración automática).
2. Se escala a la persona en máximo 10 líneas con:
   - Qué se intentó en las 3 vueltas.
   - Qué hipótesis se descartaron y con qué evidencia.
   - Qué decisión humana se necesita para desbloquear.
