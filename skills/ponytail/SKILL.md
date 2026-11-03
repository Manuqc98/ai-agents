---
name: ponytail
description: "Simplicidad pragmática y anti-sobreingeniería con la escalera de simplicidad (YAGNI, You Aren't Gonna Need It: «no lo vas a necesitar»). Cárgala al implementar, refactorizar, elegir dependencias, comparar opciones de diseño o auditar un cambio, para lograr la solución más pequeña que resuelva la tarea completa sin wrappers, abstracciones ni dependencias superfluas."
version: 1.1.0
license: MIT
tags: [yagni, simplicity, clean-code, anti-overengineering, refactoring, quality]
related_skills: [design-patterns, agent-routing]
---

# Simplicidad Pragmática y Anti-Sobreingeniería (`ponytail`)

Resuelve el problema completo con el menor volumen de código nuevo: **«El mejor código es el que no hace falta escribir»**. Deja fuera la *patternitis* y la complejidad accidental, nunca la calidad (§2.3).

> **Origen y licencia:** adaptación al español de [Ponytail](https://github.com/DietrichGebert/ponytail) (a partir de la versión 5.3.3), © 2026 DietrichGebert, con licencia MIT ([`LICENSE`](LICENSE)). Si tu cliente carga también el plugin original, en este repositorio manda esta adaptación.

## Cuándo cargarla

- Vas a escribir, modificar o refactorizar código, configuración o migraciones.
- Hay que elegir entre añadir una dependencia, abstracción o patrón y algo más sencillo.
- Auditas un cambio ajeno (QA o revisión) para ver si sobra o falta algo.

---

## 1. Puerta de decisión (¿aplica aquí?)

- **¿El trabajo produce o cambia código?** Si es solo una consulta, una clasificación o un informe, no apliques el cierre de §3.
- **¿La persona pidió explícitamente la versión completa o flexible?** Lo pedido es alcance: la escalera recorta lo especulativo, nunca lo solicitado.

## 2. Procedimiento

### 2.1 Replanteo y alcance

Antes de escribir, haz el [replanteo](../../docs/glosario.md#replanteo) del código que vas a tocar y fija el alcance:
1. **Lista todos los puntos afectados:** llamadores directos e indirectos, tests, fixtures, configuración, exportaciones e interfaces. **Todos forman parte del cambio** y quedan actualizados: el diff mínimo no deja nada roto.
2. **Evalúa qué podría romperse:** datos expuestos o alterados, consumidores que queden desalineados.
3. **Fija el alcance:** resolver la necesidad respetando la estructura existente (capas, interfaces, convenciones). Las funcionalidades no pedidas y las abstracciones especulativas **no son alcance**.

### 2.2 Escalera de simplicidad

Toma la **primera opción que resuelva la tarea por completo** ([escalera de simplicidad](../../docs/glosario.md#escalera-de-simplicidad)):

1. **¿Tiene que existir? ([YAGNI](../../docs/glosario.md#yagni)):** descarta opciones, configuraciones y flexibilidad que nadie ha pedido, y nómbralas en una línea. Si la petición es vaga, construye la versión más pequeña que resuelva el núcleo.
2. **¿Ya existe en el proyecto?** Usa el helper, servicio, componente o convención tal como lo usa el código circundante.
3. **¿Lo cubre la biblioteca estándar o la plataforma?** Úsala antes de inventar utilidades caseras.
4. **¿Lo resuelve una dependencia ya instalada?** Úsala. **Prohibido añadir una dependencia nueva** para algo que se hace en pocas líneas.
5. **¿Cabe en una línea que se entiende de un vistazo?** Déjalo en una línea.
6. **Si no:** el mínimo código que funcione.

Desempates: gana la menor diferencia (*diff*) completa, pero una línea críptica no es concisión; entre opciones de tamaño parecido, elige la que es correcta en los casos borde.

### 2.3 Lo que NUNCA se recorta

La simplicidad no es descuido. Nunca se omite ni se simplifica a la baja:
- **Validación en fronteras de confianza:** entradas de usuario, servicios externos, deserialización y permisos.
- **Manejo de errores crítico:** pérdida de datos, transacciones y fallos silenciosos. El código que mueves o fusionas **conserva su validación y su manejo de errores**.
- **Seguridad:** criptografía, sanitización contra inyecciones y control de acceso.
- **Accesibilidad y cumplimiento normativo.**
- **Criterios de aceptación pedidos:** todo lo solicitado se cumple y se verifica.
- **Su comprobación:** la lógica nueva no trivial (una rama, un bucle, un parser, dinero o seguridad) deja al menos un test pequeño o una autocomprobación con aserciones. Los cambios triviales no la necesitan.

### 2.4 Atajos declarados (`shortcut:`)

Si tomas un atajo consciente con un límite conocido, márcalo en el código con un comentario en la sintaxis del lenguaje (`//`, `#`, `--`, `<!-- -->`, `"`…) y este contenido:

```text
shortcut: <límite exacto>, <cuándo o bajo qué condición actualizar>, <sencilla|media|complicada>
```

Es [deuda técnica](../../docs/glosario.md#deuda-tecnica) declarada: lista también cada `shortcut:` en el cierre del entregable.

---

## 3. Formato del entregable

Toda entrega que cambie código cierra con estas dos líneas:

```text
- **Omitido deliberadamente:** <qué se descartó (YAGNI) y por qué, o «nada»>
- **Riesgos o límites asumidos:** <supuestos, casos borde y deuda (cada `shortcut:`) con complejidad sencilla|media|complicada, o «ninguno»>
```

## 4. Errores frecuentes a evitar

- **Recortar calidad para encoger el diff:** quitar validación, manejo de errores o el test de la lógica nueva. Repasa §2.3 antes de entregar.
- **Diff mínimo pero incompleto:** cambiar una firma y dejar llamadores, fixtures o tests sin actualizar (§2.1).
- **Concisión críptica:** una línea que hay que descifrar no es simple; escribe la versión legible.
