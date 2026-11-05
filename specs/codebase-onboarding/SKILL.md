---
name: codebase-onboarding
description: "Guion por fases para generar el brain de un repositorio que no conoces: inventario con comandos, documentación viva en docs/ (índice, arquitectura, flujos, limitaciones y decisiones) con punteros verificables, preguntas abiertas para el equipo y siembra de Engram y de las rutas sensibles de la puerta de riesgo. Cárgala al llegar a un repositorio sin docs/index.md o cuando la petición sea «analiza este repositorio» o «genera su documentación de contexto»."
version: 1.0.0
license: MIT
tags: [onboarding, brain, docs, analysis, context, engram]
related_skills: [agent-routing, engram-memory]
---

# Generar el brain de un repositorio (`codebase-onboarding`)

Sin contexto persistente, cada agente redescubre el proyecto en cada sesión y decide sobre supuestos distintos. Este guion produce el [brain del proyecto](../../docs/glosario.md#brain-del-proyecto) de un repositorio desconocido **sin modificar su código**. No sustituye a [`solution-design-spec`](../solution-design-spec/SKILL.md): aquí se describe lo que hay, no se diseña lo que vendrá.

- **Clasificación:** `Soporte` · `observacion` · circuito `conciso` (caso 16 de [`tests/clasificacion.md`](../../tests/clasificacion.md)).
- **Ruta:** [`architect`](../../agents/architect.md) analiza y redacta → [`implementer`](../../agents/implementer.md) escribe los ficheros (solo documentación, nunca código) → [`qa`](../../agents/qa.md) verifica.

## Cuándo cargarla

- Llegas a un repositorio sin `docs/index.md`, o con documentación que nadie mantiene.
- La persona pide «analiza este repositorio», «explícame cómo está montado» o «genera su documentación de contexto».
- Antes de la primera tarea de circuito `completo` en un repositorio sin brain.

---

## Fase 0 — Puerta (máximo 3 preguntas)

1. **Alcance:** ¿repositorio entero o un módulo concreto? En repositorios grandes, empieza por el módulo de la primera tarea.
2. **Dónde vive el brain:**
   - **Local sin versionar (por defecto):** `docs/` del repositorio, añadido a `.git/info/exclude`. No toca `.gitignore` ni el historial del equipo. Acuerda con la persona cómo lo cargará su cliente (por ejemplo, un fichero de instrucciones local, también excluido, que apunte a `docs/index.md`): si nada lo enlaza, ningún agente lo encontrará.
   - **Versionado:** solo si el equipo lo acepta de forma explícita. En un equipo nuevo, no lo des por hecho.
3. **Disparadores sensibles:** ¿maneja datos personales ([PII](../../docs/glosario.md#pii)), pagos, credenciales de terceros o lógica que decide precios, órdenes o importes? Anota en la sección «Datos sensibles» de `index.md` qué no puede aparecer ni en el brain ni en Engram.

## Fase 1 — Inventario con comandos (solo lectura)

La fuente manda (regla 7 de [`AGENTS.md`](../../AGENTS.md)): cada dato sale de un comando o de un fichero leído, nunca de la memoria del modelo.

| Qué averiguar | Cómo |
|---|---|
| Lenguajes y tamaño | `git ls-files \| sed 's/.*\.//' \| sort \| uniq -c \| sort -rn \| head` |
| Dependencias y versiones | Ficheros de dependencias (`package.json`, `pyproject.toml`, `pom.xml`, `go.mod`...) |
| Puntos de entrada | Scripts de arranque, rutas, `Dockerfile` y comandos del README |
| Integración y despliegue continuos | `.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile`... |
| Tests y cómo se ejecutan | Carpetas de tests, configuración del ejecutor y scripts |
| Zonas que más cambian | `git log --since=1.year --format= --name-only \| sort \| uniq -c \| sort -rn \| head -20` |
| Configuración esperada | `.env.example` y ficheros de configuración (nunca leas ni copies valores reales) |
| Documentación existente | `AGENTS.md`, `CLAUDE.md`, README y `docs/`: es evidencia de intención, no de comportamiento. Contrasta sus afirmaciones con el código y enlázala desde el índice en lugar de repetirla |

No recojas autores ni correos, ni del historial ni de los metadatos de ficheros versionados (por ejemplo, `authors` en `pyproject.toml` o firmas del README): son PII y no aportan nada al brain.

## Fase 2 — Redacción (`architect`)

Rellena las plantillas de [`references/plantillas.md`](references/plantillas.md) en este orden: `architecture.md` → `flows.md` → `limitations-and-gotchas.md` → `decisions.md` → `index.md`. El índice va al final, cuando ya sabes qué contiene cada documento.

1. **Cada afirmación con evidencia:** un puntero `` `ruta:línea` `` relativo a la raíz del repositorio (o `` `ruta` `` si es el fichero entero), o `` `commit <hash>` `` cuando el porqué solo está en un mensaje de commit.
2. **Tres niveles de certeza:** con puntero directo (no se marca); `inferido` si se deduce de varios punteros sin haberlo ejecutado (cita de cuáles sale); `supuesto` si no hay puntero.
3. **Enlaces markdown solo entre documentos del brain**, relativos a `docs/`. Nunca `file:///`: las rutas absolutas de una máquina se rompen en todas las demás.
4. **Decisiones reconstruidas como `inferida`:** en código heredado se ve el *qué*, rara vez el *porqué*. Un [ADR](../../docs/glosario.md#adr) inferido describe la evidencia y deja el motivo como pregunta.
5. **Preguntas abiertas para el equipo:** todo lo que el código no responde (por qué existe algo, si un comportamiento raro es intencionado, quién se encarga de un módulo). Asígnales un identificador estable (`P-01`, `P-02`...) en cuanto surjan, desde la Fase 1; los documentos citan el identificador y `index.md` las recoge al final. Es el entregable más útil de las primeras semanas.
6. **Proporcionalidad ([Ponytail](../../skills/ponytail/SKILL.md)):** documenta los flujos que alguien va a tocar, no todos. Sin una primera tarea concreta, elige por puntos de entrada y zonas que más cambian. Cinco flujos bien señalados valen más que veinte vagos.

## Fase 3 — Verificación por otro rol (`qa`)

Nadie valida su propio trabajo (regla 9). [`qa`](../../agents/qa.md) emite su dictamen habitual sobre los documentos:

- [ ] Todos los punteros `ruta:línea` y `commit <hash>` existen y apuntan a lo que dicen.
- [ ] Al menos 5 afirmaciones de `flows.md` y `limitations-and-gotchas.md` se contrastan con el código.
- [ ] No hay enlaces `file:///`, secretos, valores reales de configuración ni PII.
- [ ] Cada `inferido`, `supuesto` y decisión `inferida` está marcado como tal, y cada `inferido` cita de qué punteros sale.

## Fase 4 — Siembra

1. **Memoria episódica:** guarda en [Engram](../../docs/glosario.md#engram) solo lo no evidente (gotchas, convenciones, causas de comportamientos raros), en 2 o 3 líneas cada uno y sin secretos ni PII ([`skills/engram-memory`](../../skills/engram-memory/SKILL.md)). Empieza cada título con el nombre del repositorio (`<repo>: ...`) para no mezclar proyectos. Si inicializar Engram crea ficheros en el repositorio y el brain es local, exclúyelos igual que `docs/`.
2. **Rutas sensibles de la [puerta de riesgo](../../docs/glosario.md#puerta-de-riesgo):** crea `.agents/rutas-sensibles.txt` en el repositorio objetivo con los módulos de autenticación, pagos, datos personales, configuración crítica o lógica que decide precios, órdenes o importes que hayas encontrado y que los patrones por defecto de [`tools/risk-gate.py`](../../tools/risk-gate.py) no capturan. Sigue el mismo criterio de versionado que el brain: si es local, añádelo también a `.git/info/exclude`.
3. **Comprobación:** ejecuta `python3 tools/risk-gate.py --repo <ruta-del-proyecto> --probar-patrones`. Lista cuántos ficheros versionados captura cada patrón; revisa los marcados con `⚠`, que no capturan ninguno (son preventivos o erratas).

## Formato del entregable

```text
Brain generado:  <repositorio o módulo> · ubicación: <docs/ local | versionado>
Documentos:      index · architecture · flows · limitations-and-gotchas · decisions
Punteros:        <n> escritos (implementer) · <n> verificados (qa) · inferidos: <n> · supuestos: <n> · decisiones inferidas: <n>
Engram:          <n> recuerdos guardados
Rutas sensibles: <n> patrones en .agents/rutas-sensibles.txt
Preguntas abiertas para el equipo: <n> (al final de docs/index.md)
```

## Errores frecuentes a evitar

- **Describir de memoria:** «usa Redis como caché» sin puntero suele ser una invención verosímil. Sin puntero, es un `supuesto`.
- **Documentarlo todo:** un brain de 40 páginas no lo lee nadie, tampoco un agente con contexto limitado.
- **Versionar sin preguntar:** en un equipo nuevo, añadir `docs/` al repositorio es una decisión del equipo, no tuya.
- **Inventar el porqué de una decisión:** si no está escrito en ningún sitio, es una pregunta abierta.
