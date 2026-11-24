"""Pruebas de tools/project-memory.py sobre repositorios temporales (solo biblioteca estándar).

Uso:
  python3 -m unittest discover tests
"""
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "project-memory.py"


class MemoriaDeProyecto(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "proyecto"
        self.repo.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def ejecutar(self, *args, usar_repo=True):
        cmd = [sys.executable, str(SCRIPT)]
        if usar_repo:
            cmd += ["--repo", str(self.repo)]
        cmd += list(args)
        return subprocess.run(cmd, capture_output=True, text=True)

    def test_init_y_status_con_repo(self):
        r = self.ejecutar("init")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((self.repo / ".agents" / "memory.sqlite3").is_file())

        r = self.ejecutar("status")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Tareas: (ninguna registrada)", r.stdout)

    def test_repo_inexistente_o_vacio_da_error(self):
        for flag, valor in (("--repo", str(self.repo / "no-existe")), ("--repo", ""), ("--db", "")):
            r = self.ejecutar(flag, valor, "init", usar_repo=False)
            self.assertEqual(r.returncode, 1, f"{flag}={valor!r} debería fallar")
            self.assertTrue(r.stderr.strip())

    def test_db_y_repo_mutuamente_excluyentes(self):
        r = self.ejecutar("--repo", str(self.repo), "--db", str(self.repo / "x.db"), "status", usar_repo=False)
        self.assertEqual(r.returncode, 2)

    def test_ciclo_tarea_show_y_corte_a_las_3_vueltas(self):
        self.ejecutar("init")
        r = self.ejecutar(
            "task", "set", "alfred:auth:login",
            "--title", "Validar token",
            "--kind", "Historia",
            "--severity", "atencion",
            "--circuit", "completo",
            "--status", "WIP",
            "--agent", "implementer",
            "--acceptance", "uv run pytest -k login",
            "--return-if", "Falta esquema",
        )
        self.assertEqual(r.returncode, 0, r.stderr)

        for vuelta in (1, 2):
            r = self.ejecutar("task", "iterate", "alfred:auth:login")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn(f"{vuelta}/3", r.stdout)

        r = self.ejecutar("task", "iterate", "alfred:auth:login")
        self.assertEqual(r.returncode, 3)
        self.assertIn("LÍMITE ALCANZADO", r.stdout)

        r_dec = self.ejecutar(
            "decision",
            "--task", "alfred:auth:login",
            "--title", "Formato de token",
            "--chosen", "JWT",
            "--alternatives", "Sesión opaca",
            "--why", "Sin estado compartido",
        )
        self.assertEqual(r_dec.returncode, 0, r_dec.stderr)

        r = self.ejecutar("task", "show", "alfred:auth:login")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Validar token", r.stdout)
        self.assertIn("uv run pytest -k login", r.stdout)
        self.assertIn("Formato de token", r.stdout)

    def test_nota_security_y_error_en_tarea_inexistente(self):
        self.ejecutar("init")
        self.ejecutar("task", "set", "app:api:pago", "--acceptance", "test pago")

        r = self.ejecutar(
            "note",
            "--task", "app:api:pago",
            "--agent", "security-reviewer",
            "--kind", "security",
            "--text", "Validar firma webhook",
            "--evidence", "src/pay.py:42",
        )
        self.assertEqual(r.returncode, 0, r.stderr)

        r = self.ejecutar(
            "note",
            "--task", "tarea-fantasma",
            "--agent", "qa",
            "--kind", "qa",
            "--text", "No debería lanzar traceback",
        )
        self.assertEqual(r.returncode, 1)
        self.assertNotIn("Traceback", r.stderr)
        self.assertIn("No existe la tarea 'tarea-fantasma'", r.stderr)

    def test_usage_registro_y_consulta_por_tarea(self):
        self.ejecutar("init")
        self.ejecutar("task", "set", "app:ui:form", "--acceptance", "ok")
        self.ejecutar("task", "set", "app:db:mig", "--acceptance", "ok")

        r = self.ejecutar(
            "usage",
            "--task", "app:ui:form",
            "--agent", "implementer",
            "--provider", "google",
            "--model", "gemini-3.1-pro",
            "--complexity", "media",
            "--tokens-in", "1200",
            "--tokens-out", "350",
        )
        self.assertEqual(r.returncode, 0, r.stderr)

        r2 = self.ejecutar(
            "usage",
            "--task", "app:db:mig",
            "--agent", "security-reviewer",
            "--provider", "anthropic",
            "--model", "claude-opus-5-5",
            "--complexity", "complicada",
        )
        self.assertEqual(r2.returncode, 0, r2.stderr)

        r = self.ejecutar("usage", "--list", "--task", "app:ui:form")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("google/gemini-3.1-pro", r.stdout)
        self.assertNotIn("anthropic/claude-opus-5-5", r.stdout)

        r_ag = self.ejecutar("usage", "--list", "--agent", "security-reviewer")
        self.assertEqual(r_ag.returncode, 0, r_ag.stderr)
        self.assertIn("anthropic/claude-opus-5-5", r_ag.stdout)
        self.assertNotIn("google/gemini-3.1-pro", r_ag.stdout)

        r_bad = self.ejecutar("usage", "--task", "app:ui:form")
        self.assertEqual(r_bad.returncode, 2)

    def test_init_migra_esquema_antiguo_sin_perder_notas_ni_indices(self):
        db = self.repo / ".agents" / "memory.sqlite3"
        db.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(db)
        conn.executescript(
            """
            CREATE TABLE tasks (
              id TEXT PRIMARY KEY, title TEXT NOT NULL, kind TEXT NOT NULL DEFAULT 'Tarea',
              severity TEXT NOT NULL DEFAULT 'atencion', circuit TEXT NOT NULL DEFAULT 'conciso',
              status TEXT NOT NULL DEFAULT 'TODO', agent_name TEXT, input_ref TEXT,
              acceptance TEXT NOT NULL DEFAULT 'Pendiente', return_if TEXT, assumptions TEXT,
              iterations INTEGER NOT NULL DEFAULT 0, debt_size TEXT, debt_notes TEXT,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE task_notes (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
              agent_name TEXT NOT NULL,
              kind TEXT NOT NULL CHECK (kind IN ('handoff','replanteo','devolucion','qa','observacion')),
              text TEXT NOT NULL, evidence_ref TEXT,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX idx_task_notes_task ON task_notes(task_id, created_at);
            INSERT INTO tasks (id, title) VALUES ('t1', 'Prueba');
            INSERT INTO task_notes (task_id, agent_name, kind, text) VALUES ('t1', 'qa', 'qa', 'Nota previa');
            """
        )
        conn.close()

        r = self.ejecutar("init")
        self.assertEqual(r.returncode, 0, r.stderr)

        conn = sqlite3.connect(db)
        indices = {fila[0] for fila in conn.execute("SELECT name FROM sqlite_master WHERE type = 'index'")}
        conn.close()
        self.assertIn("idx_task_notes_task", indices)

        r = self.ejecutar("note", "--task", "t1", "--agent", "security-reviewer", "--kind", "security", "--text", "OK")
        self.assertEqual(r.returncode, 0, r.stderr)

        r = self.ejecutar("task", "show", "t1")
        self.assertIn("Nota previa", r.stdout)
        self.assertIn("(security @ security-reviewer): OK", r.stdout)


if __name__ == "__main__":
    unittest.main()
