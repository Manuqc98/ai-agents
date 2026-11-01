# Catálogo Canónico de Patrones (`docs/patrones/`)

> **Regla de uso:** Antes de diseñar o proponer una solución técnica, consulta este catálogo. Cita el patrón con su enlace canónico y justifica por qué aplica a ese problema específico. Prohibido inventar patrones o proponerlos de memoria.

---

## 1. Fuente canónica única

La fuente de referencia para los patrones de diseño del equipo es **[Refactoring Guru (en español)](https://refactoring.guru/es/design-patterns)**:
- Vocabulario compartido y estandarizado en español.
- Enfoque pragmático: explica el problema, la solución, pros, contras y relaciones con otros patrones.
- Ejemplos políglotas en los lenguajes principales (TypeScript, Python, Java, Go, C#, Rust).

---

## 2. Índices disponibles

| Catálogo | Qué cubre | Documento |
|---|---|---|
| **Patrones de Diseño (GoF)** | Los 22 patrones creacionales, estructurales y conductuales clásicos | [`diseno.md`](diseno.md) |

---

## 3. Regla contra la sobreingeniería

> **«El mejor patrón es el que no hace falta en tu caso.»**

No utilices un patrón si una función simple o una estructura de datos estándar resuelve el problema con claridad. Si se introduce un patrón, debe justificarse en el diseño ([ADR](../../docs/glosario.md#adr)) qué flexibilidad aporta y qué coste de complejidad añade.
