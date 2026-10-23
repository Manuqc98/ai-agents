---
name: nombre-de-la-skill
description: "Explica CUÁNDO activar esta skill (qué palabras del usuario o qué situación técnica la disparan) y qué entregable produce. Este campo decide si el LLM la carga en su contexto."
version: 1.0.0
license: MIT
tags: [etiqueta-1, etiqueta-2]
related_skills: []
---

<!--
  NOTA DE PORTABILIDAD MULTI-LLM:
  1. Mantén el frontmatter YAML limpio y estándar (sin bloques propietarios atados a un único cliente).
  2. Mantén este fichero por debajo de ~200 líneas para no saturar la ventana de contexto en modelos pequeños o locales.
  3. Si necesitas plantillas largas, ejemplos extensos o scripts, guárdalos en una subcarpeta `references/` o `scripts/` dentro de esta misma skill y enlázalos desde aquí.
-->

# Título de la Skill (`nombre-de-la-skill`)

Explica en dos líneas qué problema resuelve esta *skill* y qué deja fuera.

## Cuándo cargarla

- Situación o disparador 1.
- Situación o disparador 2.

---

## 1. Puerta de decisión (¿aplica aquí?)

Antes de aplicar una metodología por inercia, haz las preguntas mínimas para confirmar si de verdad hace falta en este caso.

## 2. Procedimiento paso a paso

1. **Paso 1:** qué comprobar y por qué.
2. **Paso 2:** cómo estructurar el análisis o la acción.
3. **Paso 3:** cómo verificar que el resultado es válido.

## 3. Formato del entregable

```text
<Plantilla concisa de salida que cualquier LLM pueda rellenar sin ambigüedad>
```

## 4. Errores frecuentes a evitar

- **Error típico 1:** por qué ocurre y cómo corregirlo.
- **Error típico 2:** por qué ocurre y cómo corregirlo.
