# Servidores MCP del Proyecto (`docs/mcp/`)

Este directorio contiene configuraciones estándar de servidores [MCP](../../docs/glosario.md#mcp) (*Model Context Protocol*) para dotar a los agentes de capacidades externas de forma agnóstica al cliente.

---

## 1. Engram (`engram.json`)

[Engram](../../docs/glosario.md#engram) proporciona memoria persistente episódica y búsqueda semántica indexada ([FTS5 / BM25](../../docs/glosario.md#fts5--bm25)) entre sesiones.

### Prerrequisito
Tener instalado el binario de `engram`:
```bash
./tools/install-engram.sh
```

---

## 2. Cómo cargarlo según tu cliente (*Harness*)

### A. Antigravity / Gemini CLI
Añade la sección a tu archivo de configuración `~/.gemini/config/mcp_config.json`:
```json
{
  "mcpServers": {
    "engram": {
      "type": "stdio",
      "command": "engram",
      "args": ["mcp", "--tools=agent"]
    }
  }
}
```

### B. Claude Code
Ejecuta en tu terminal:
```bash
claude mcp add engram -- engram mcp --tools=agent
```

### C. Cursor
En `Settings > Features > MCP > Add New MCP Server`:
- **Name:** `engram`
- **Type:** `command`
- **Command:** `engram mcp --tools=agent`

### D. OpenCode / Codex
Añade a tu archivo `opencode.json` o configuración de agentes:
```json
{
  "mcp": {
    "engram": {
      "type": "stdio",
      "command": "engram",
      "args": ["mcp", "--tools=agent"]
    }
  }
}
```

---

## 3. Herramientas MCP expuestas por Engram

Una vez conectado, cualquier modelo tiene acceso a:
- **`engram_search`:** busca recuerdos por texto libre o palabras clave en SQLite FTS5.
- **`engram_save`:** guarda un recuerdo (`title` y `content`) en la base de datos local del proyecto.
- **`engram_context`:** recupera el contexto relevante de sesiones anteriores.
