---
name: solution-design-spec
description: "Guion interactivo por fases (SDD) para el circuito completo (Historias, Mejoras Funcionales y Epics). Conduce desde la definición del problema y requisitos (AS-IS/TO-BE) hasta la arquitectura con replanteo, registro de decisiones (ADR) y descomposición en tareas con contrato de traspaso en SQLite. Cárgala siempre que agent-routing asigne el circuito completo."
version: 1.0.0
license: MIT
tags: [spec, sdd, architecture, requirements, planning, adr]
related_skills: [agent-routing]
---

# Especificación Guiada de Diseño y Planificación (`solution-design-spec`)

Este guion evita el error más frecuente de los modelos de lenguaje en tareas grandes: **empezar a escribir código en el minuto uno asumiendo en silencio lo que la persona no dijo**.

Cuando [`agent-routing`](../../skills/agent-routing/SKILL.md) asigna el circuito **`completo`**, [`orchestrator`](../../agents/orchestrator.md) y [`architect`](../../agents/architect.md) conducen esta conversación en **4 fases cortas**. Ninguna fase avanza a la siguiente si falta un dato crítico: se pregunta antes de construir.

---

## Fase 0 — Puerta de contexto y proporcionalidad

Antes de pedir requisitos o diseñar tablas, calibra el rigor según la naturaleza del proyecto (máximo 3 preguntas):

1. **¿Qué tipo de iniciativa es?**
   - Experimento / [PoC](../../docs/glosario.md#mvp-y-poc) descartable.
   - Proyecto personal / herramienta interna.
   - Sistema en producción con usuarios reales o datos críticos.
2. **¿Aplica definir métricas de negocio ([KPI](../../docs/glosario.md#kpi)) o de servicio ([SLO](../../docs/glosario.md#slo-y-sla))?**
   - Si es una utilidad personal o cambio pequeño, **declara explícitamente que no aplican** y ahorra esa burocracia.
   - Si aplican, exige **línea base actual**, **objetivo numérico** y **cómo se va a medir**.
3. **¿Toca algún disparador de seguridad o cumplimiento?**
   - Datos personales → exige definir qué no puede ir a logs ni a entornos de prueba.
   - Pagos, cobros o envíos externos → exige [idempotencia](../../docs/glosario.md#idempotencia) y manejo de reintentos.

---

## Fase 1 — Problema y Alcance Funcional (`AS-IS` → `TO-BE`)

Define **qué** hay que resolver sin atarlo todavía a cómo programarlo:

1. **Problema en una frase:** qué ocurre hoy (`AS-IS`) y por qué duele.
2. **Comportamiento esperado (`TO-BE`):** qué podrá hacer el usuario o el sistema cuando terminemos.
3. **Frontera del alcance (imprescindible):**
   - **Entra hoy (*Must have*):** lo mínimo necesario para entregar valor ([MVP](../../docs/glosario.md#mvp-y-poc)).
   - **Queda fuera hoy (*Won't have*):** lo que **no** vamos a construir en esta iteración (evita que el alcance crezca sin control a mitad del desarrollo).

> **Puerta de salida de Fase 1:** confirma este resumen de 10 líneas con la persona antes de pasar al diseño técnico.

---

## Fase 2 — Replanteo, Opciones y Arquitectura

Con el alcance confirmado, [`architect`](../../agents/architect.md) diseña la solución:

1. **[Replanteo](../../docs/glosario.md#replanteo) de solo lectura:**
   - Inspecciona el repositorio real (lenguaje, versión, dependencias actuales, estructura de carpetas, esquema de base de datos, tests existentes).
   - **El material manda:** respeta las convenciones y herramientas que ya usa el proyecto.
2. **Comparativa de opciones (si hay decisión de diseño):**
   - Presenta **2 o 3 opciones reales** con ventajas, compromisos (*trade-offs*) y motivo de recomendación.
3. **Revisión de las 6 capas técnicas:**
   - Declara en una línea qué cambia en cada capa (y cuáles no aplican):
     `Datos/Esquema` · `Backend/Lógica` · `Frontend/UI` · `Integraciones` · `Seguridad/Permisos` · `Observabilidad/Logs`.
4. **[Plan de reversión](../../docs/glosario.md#plan-de-reversion):**
   - Si hay migración de datos, cambio de contrato o despliegue delicado, escribe cómo volver atrás sin perder datos.
5. **Registro de la decisión ([ADR](../../docs/glosario.md#adr)):**
   - Guarda la decisión tomada en la memoria del proyecto:
     ```bash
     python3 tools/project-memory.py decision \
       --task "<id>" --title "<qué se decidió>" \
       --chosen "<opción elegida>" --alternatives "<opciones descartadas>" \
       --why "<motivo técnico y de negocio>"
     ```

---

## Fase 3 — Desglose en Tareas y Contratos de Traspaso (*Handoff*)

Antes de que [`implementer`](../../agents/implementer.md) toque una sola línea de código, convierte el diseño aprobado en tareas verificables y regístralas en `.agents/memory.sqlite3`:

1. **Una tarea = un objetivo verificable:** si una tarea tarda horas en explicarse, pártela en subtareas ordenadas por dependencia.
2. **Registra cada tarea en la memoria persistente:**
   ```bash
   python3 tools/project-memory.py task set "<id>" \
     --title "<objetivo en una frase>" \
     --kind Historia --severity atencion --circuit completo --status TODO \
     --agent implementer \
     --input-ref "<rutas a ficheros reales>" \
     --acceptance "<comando o test que debe pasar>" \
     --return-if "<condición bajo la cual implementer debe rechazar>"
   ```
3. **Relevo a ejecución (Fases 3 y 4 del circuito):**
   - Pasa cada tarea a [`implementer`](../../agents/implementer.md) y, cuando entregue en estado `REVIEW`, pásala a [`qa`](../../agents/qa.md) para su validación independiente.
