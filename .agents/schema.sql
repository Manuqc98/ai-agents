-- Esquema de memoria persistente agnóstica de LLM (.agents/schema.sql)
-- Diseñado para sostener el estado fuera de la ventana de contexto de cualquier modelo.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS tasks (
  id          TEXT PRIMARY KEY, -- Fingerprint estable: "sistema:modulo:sintoma"
  title       TEXT NOT NULL,
  kind        TEXT NOT NULL DEFAULT 'Tarea' CHECK (kind IN (
                'Incidencia','Soporte','Mejora Técnica','Mejora Funcional',
                'Historia','Epic','Tarea','Diseño y prototipado')),
  severity    TEXT NOT NULL DEFAULT 'atencion' CHECK (severity IN ('bloqueante','atencion','observacion')),
  circuit     TEXT NOT NULL DEFAULT 'conciso' CHECK (circuit IN ('quirurgico','conciso','completo')),
  status      TEXT NOT NULL DEFAULT 'TODO' CHECK (status IN (
                'BACKLOG','TODO','WIP','INWAIT','REVIEW','DONE','CANCELLED')),
  agent_name  TEXT,
  input_ref   TEXT,
  acceptance  TEXT NOT NULL DEFAULT 'Pendiente de definir',
  return_if   TEXT,
  assumptions TEXT,
  iterations  INTEGER NOT NULL DEFAULT 0,
  debt_size   TEXT CHECK (debt_size IN ('sencilla','media','complicada')),
  debt_notes  TEXT,
  created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS task_notes (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  task_id      TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
  agent_name   TEXT NOT NULL,
  kind         TEXT NOT NULL CHECK (kind IN ('handoff','replanteo','devolucion','qa','observacion')),
  text         TEXT NOT NULL,
  evidence_ref TEXT,
  created_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS decisions (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  task_id      TEXT REFERENCES tasks(id) ON DELETE SET NULL,
  title        TEXT NOT NULL,
  chosen       TEXT NOT NULL,
  alternatives TEXT NOT NULL,
  why          TEXT NOT NULL,
  created_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS model_usage (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  task_id     TEXT REFERENCES tasks(id) ON DELETE SET NULL,
  agent_name  TEXT NOT NULL,
  provider    TEXT NOT NULL, -- google | anthropic | openai | openrouter | local
  model       TEXT NOT NULL,
  complexity  TEXT NOT NULL CHECK (complexity IN ('sencilla','media','complicada')),
  tokens_in   INTEGER DEFAULT 0,
  tokens_out  INTEGER DEFAULT 0,
  reason      TEXT NOT NULL DEFAULT 'nivel-modelo',
  created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_task_notes_task ON task_notes(task_id, created_at);
CREATE INDEX IF NOT EXISTS idx_decisions_task ON decisions(task_id);
CREATE INDEX IF NOT EXISTS idx_usage_task ON model_usage(task_id, provider);
