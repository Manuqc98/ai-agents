# Casos de regresión de clasificación (`clasificacion.md`)

Batería de pruebas para la [Regla 2 de `AGENTS.md`](../AGENTS.md#2-lo-primero-clasifica-la-peticion): toda petición se clasifica en dos ejes (`Tipo × Severidad`) antes de actuar.

- **Qué comprueba el script (`python3 tools/check-repo.py --solo clasificacion`):** lee la tabla canónica de [`skills/agent-routing/SKILL.md`](../skills/agent-routing/SKILL.md#2-elegir-el-circuito) y verifica que el circuito de cada caso de esta tabla coincida con la especificación.
- **Qué comprueba la persona (o evaluación de LLM):** pasarle la columna `Petición` al [`orchestrator`](../agents/orchestrator.md) en cualquier modelo y verificar que elige el `Tipo`, `Severidad` y `Circuito` esperados.

| # | Petición | Tipo | Severidad | Circuito | Por qué |
|---|---|---|---|---|---|
| 1 | «La pasarela de pagos devuelve error 500 desde las 10:15 y nadie puede finalizar compra» | `Incidencia` | `bloqueante` | `quirurgico` | Flujo crítico (cobros) caído en producción ahora mismo |
| 2 | «El login falla para el 20 % de los usuarios tras el último despliegue» | `Incidencia` | `bloqueante` | `quirurgico` | Afecta a autenticación y supera el umbral del 5 % de peticiones |
| 3 | «El listado de facturas tarda a veces 7 segundos en cargar, pero acaba saliendo» | `Incidencia` | `atencion` | `conciso` | Degradación local recurrente sin caída global del servicio |
| 4 | «¿Por qué el job nocturno de exportación dejó de generar el CSV desde el martes?» | `Incidencia` | `atencion` | `conciso` | Viene formulado como pregunta, pero algo que funcionaba se ha roto (desempate 1) |
| 5 | «En los logs de consola se está imprimiendo el token de sesión en claro» | `Incidencia` | `atencion` | `conciso` | Fuga de datos sensibles activa en logs: requiere corrección acotada inmediata |
| 6 | «El nivel de log en producción se ha quedado en DEBUG y mete bastante ruido» | `Incidencia` | `observacion` | `conciso` | Ruido operativo sin degradación funcional |
| 7 | «¿Dónde se configuran las variables de entorno para el entorno de staging?» | `Soporte` | `observacion` | `conciso` | El entregable esperado es información con fuente citada, no tocar código (desempate 2) |
| 8 | «Analiza este repositorio y dime qué partes están acopladas a un proveedor» | `Soporte` | `observacion` | `conciso` | Consulta de análisis técnico sin modificar el sistema |
| 9 | «Hay que actualizar la librería de validación porque la versión actual está deprecada» | `Mejora Técnica` | `atencion` | `conciso` | Cambio interno sin alterar el comportamiento visible para el usuario (desempate 3) |
| 10 | «Extrae la lógica repetida de formateo de fechas a un módulo común» | `Mejora Técnica` | `observacion` | `conciso` | Refactor interno para reducir deuda técnica |
| 11 | «Renombra el campo `user_id` a `account_id` en el esquema de respuesta» | `Tarea` | `observacion` | `conciso` | Trabajo mecánico y acotado sin decisiones de diseño |
| 12 | «¿Qué arquitectura y base de datos nos conviene para añadir búsqueda semántica?» | `Diseño y prototipado` | `observacion` | `conciso` | Explorar opciones y registrar un [ADR](../docs/glosario.md#adr) antes de decidir si se construye |
| 13 | «Que el buscador actual permita además filtrar resultados por rango de fechas» | `Mejora Funcional` | `atencion` | `completo` | Amplía lo que el usuario puede hacer sobre una funcionalidad existente |
| 14 | «Como usuario quiero recibir alertas por Telegram cuando baje el precio de un producto» | `Historia` | `atencion` | `completo` | Funcionalidad nueva completa con actor y valor de negocio claros |
| 15 | «Queremos migrar todo el sistema de autenticación a arquitectura multi-tenant» | `Epic` | `atencion` | `completo` | Objetivo amplio que no cabe en una sola entrega; primero hay que descomponerlo (desempate 4) |
