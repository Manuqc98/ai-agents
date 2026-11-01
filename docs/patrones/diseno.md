# Patrones de Diseño (GoF) — Refactoring Guru

> **Fuente canónica en español:** [Refactoring Guru — Patrones de diseño](https://refactoring.guru/es/design-patterns).
> Catálogo general: [`catalog`](https://refactoring.guru/es/design-patterns/catalog) ·
> Creacionales: [`creational-patterns`](https://refactoring.guru/es/design-patterns/creational-patterns) ·
> Estructurales: [`structural-patterns`](https://refactoring.guru/es/design-patterns/structural-patterns) ·
> Conductuales: [`behavioral-patterns`](https://refactoring.guru/es/design-patterns/behavioral-patterns).

---

## 1. Patrones Creacionales (Cómo se crean los objetos)

Mecanismos de creación de objetos que incrementan la flexibilidad y la reutilización del código existente evitando acoplarse a clases concretas.

| Patrón | Propósito en una línea | Capa habitual | Enlace canónico |
|---|---|---|---|
| **Factory Method** | Define una interfaz para crear objetos en una superclase, permitiendo a las subclases decidir la clase exacta a instanciar | Backend / Servicios | [factory-method](https://refactoring.guru/es/design-patterns/factory-method) |
| **Abstract Factory** | Permite producir familias de objetos relacionados o dependientes sin especificar sus clases concretas | Backend / Servicios | [abstract-factory](https://refactoring.guru/es/design-patterns/abstract-factory) |
| **Builder** | Permite construir objetos complejos paso a paso; facilita producir distintas representaciones de un objeto usando el mismo código | Backend / Servicios | [builder](https://refactoring.guru/es/design-patterns/builder) |
| **Prototype** | Permite copiar o clonar objetos existentes sin que el código dependa de sus clases concretas | Backend / Servicios | [prototype](https://refactoring.guru/es/design-patterns/prototype) |
| **Singleton** | Garantiza que una clase tenga una única instancia y proporciona un punto de acceso global a ella *(⚠️ Usar con cautela: suele actuar como antipatrón de estado global compartido)* | Transversal | [singleton](https://refactoring.guru/es/design-patterns/singleton) |

---

## 2. Patrones Estructurales (Cómo se componen y relacionan objetos)

Explican cómo ensamblar objetos y clases en estructuras más grandes a la vez que se mantiene la flexibilidad y eficiencia de la arquitectura.

| Patrón | Propósito en una línea | Capa habitual | Enlace canónico |
|---|---|---|---|
| **Adapter** | Permite que objetos con interfaces incompatibles puedan colaborar envolviendo uno de ellos | Backend / Integración | [adapter](https://refactoring.guru/es/design-patterns/adapter) |
| **Bridge** | Desacopla una abstracción de su implementación para que ambas puedan evolucionar de forma independiente | Backend / Servicios | [bridge](https://refactoring.guru/es/design-patterns/bridge) |
| **Composite** | Permite componer objetos en estructuras de árbol para representar jerarquías de parte-todo y tratarlos de forma homogénea | Backend / UI | [composite](https://refactoring.guru/es/design-patterns/composite) |
| **Decorator** | Añade dinámicamente nuevas responsabilidades a un objeto envolviéndolo sin alterar el comportamiento de otros objetos de la misma clase | Backend / Middleware | [decorator](https://refactoring.guru/es/design-patterns/decorator) |
| **Facade** | Proporciona una interfaz simplificada hacia una biblioteca, un framework o un conjunto complejo de clases | Backend / Integración | [facade](https://refactoring.guru/es/design-patterns/facade) |
| **Flyweight** | Permite mantener más objetos en la memoria compartiendo partes comunes del estado entre varios objetos en lugar de almacenar todo en cada uno | Sistemas / Rendimiento | [flyweight](https://refactoring.guru/es/design-patterns/flyweight) |
| **Proxy** | Proporciona un sustituto o intermediario de otro objeto para controlar el acceso a él (caché, autenticación, carga diferida) | Red / Backend | [proxy](https://refactoring.guru/es/design-patterns/proxy) |

---

## 3. Patrones Conductuales (Cómo colaboran y reparten responsabilidades)

Se centran en la asignación efectiva de responsabilidades y en los algoritmos de comunicación entre objetos.

| Patrón | Propósito en una línea | Capa habitual | Enlace canónico |
|---|---|---|---|
| **Chain of Responsibility** | Pasa solicitudes a lo largo de una cadena de manejadores; cada uno decide procesar o pasar la solicitud al siguiente | Backend / Seguridad | [chain-of-responsibility](https://refactoring.guru/es/design-patterns/chain-of-responsibility) |
| **Command** | Convierte una solicitud en un objeto independiente que contiene toda la información de la acción (útil para encolar, deshacer o diferir) | Backend / Tareas | [command](https://refactoring.guru/es/design-patterns/command) |
| **Iterator** | Permite recorrer secuencialmente elementos de una colección sin exponer su representación subyacente (lista, árbol, grafo) | Backend / Datos | [iterator](https://refactoring.guru/es/design-patterns/iterator) |
| **Mediator** | Restringe la comunicación directa entre objetos y los fuerza a colaborar únicamente a través de un objeto mediador central | Backend / UI | [mediator](https://refactoring.guru/es/design-patterns/mediator) |
| **Memento** | Permite guardar y restaurar el estado previo de un objeto sin revelar los detalles de su implementación | Backend / Estado | [memento](https://refactoring.guru/es/design-patterns/memento) |
| **Observer** | Define un mecanismo de suscripción para notificar a múltiples objetos sobre cualquier evento que le suceda al objeto que están observando | Integración / Eventos | [observer](https://refactoring.guru/es/design-patterns/observer) |
| **State** | Permite a un objeto alterar su comportamiento cuando su estado interno cambia, simulando el cambio de su clase sin bloques condicionales enormes | Backend / Lógica | [state](https://refactoring.guru/es/design-patterns/state) |
| **Strategy** | Define una familia de algoritmos, coloca cada uno en una clase separada y hace sus objetos intercambiables en tiempo de ejecución | Backend / Servicios | [strategy](https://refactoring.guru/es/design-patterns/strategy) |
| **Template Method** | Define el esqueleto de un algoritmo en la superclase pero permite que las subclases sobrescriban pasos específicos sin cambiar la estructura | Backend / Frameworks | [template-method](https://refactoring.guru/es/design-patterns/template-method) |
| **Visitor** | Permite separar algoritmos de los objetos sobre los que operan, añadiendo nuevas operaciones sin modificar las clases de los elementos | Backend / Compiladores | [visitor](https://refactoring.guru/es/design-patterns/visitor) |

---

## 4. Ejemplos por lenguaje en Refactoring Guru

Cuando el proyecto objetivo esté desarrollado en un lenguaje específico, consulta la implementación idiomática recomendada en la fuente oficial:
- [TypeScript](https://refactoring.guru/es/design-patterns/typescript)
- [Python](https://refactoring.guru/es/design-patterns/python)
- [Java](https://refactoring.guru/es/design-patterns/java)
- [C#](https://refactoring.guru/es/design-patterns/csharp)
- [Go](https://refactoring.guru/es/design-patterns/go)
- [Rust](https://refactoring.guru/es/design-patterns/rust)
