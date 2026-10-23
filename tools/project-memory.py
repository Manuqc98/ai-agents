#!/usr/bin/env python3
"""Gestor de memoria persistente en SQLite para ai-agents (sin dependencias externas).

Permite que cualquier LLM o cliente recupere el estado del proyecto aunque se compacte
la ventana de contexto o se cambie de modelo a mitad de sesión.

Comandos principales:
  init        Inicializa .agents/memory.sqlite3 aplicando .agents/schema.sql
  status      Muestra el resumen de tareas activas, iteraciones, decisiones y uso de modelos
  task set    Crea o actualiza una tarea y su contrato de handoff
  task iter   Suma 1 vuelta a una tarea (sale con código 3 al llegar al límite de 3 vueltas)
  note add    Añade una nota de trazabilidad (handoff, replanteo, devolucion, qa, observacion)
  decision    Registra una decisión de arquitectura (ADR resumido)
  usage       Registra qué <proveedor>/<modelo> ejecutó un paso y por qué
"""
import argparse
import sqlite3
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
SCHEMA_PATH = RAIZ / ".agents" / "schema.sql"
DEFAULT_DB = RAIZ / ".agents" / "memory.sqlite3"
LIMITE_ITERACIONES = 3


def conectar(db_path):
    if not db_path.exists():
        sys.stderr.write(
            f"No existe {db_path}. Inicializa primero con: python3 tools/project-memory.py init\n"
        )
        sys.exit(1)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def cmd_init(args):
    db_path = Path(args.db)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    conn.commit()
    conn.close()
    print(f"✓ Memoria inicializada en {db_path}")


def cmd_task_set(args):
    conn = conectar(Path(args.db))
    existente = conn.execute("SELECT * FROM tasks WHERE id = ?", (args.id,)).fetchone()
    if existente is None:
        titulo = args.title or args.id
        conn.execute(
            """
            INSERT INTO tasks (id, title, kind, severity, circuit, status, agent_name,
                               input_ref, acceptance, return_if, assumptions, debt_size, debt_notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                args.id,
                titulo,
                args.kind or "Tarea",
                args.severity or "atencion",
                args.circuit or "conciso",
                args.status or "TODO",
                args.agent,
                args.input_ref,
                args.acceptance or "Pendiente de definir",
                args.return_if,
                args.assumptions,
                args.debt_size,
                args.debt_notes,
            ),
        )
        print(f"✓ Tarea creada: {args.id} [{args.status or 'TODO'}]")
    else:
        campos = {
            "title": args.title,
            "kind": args.kind,
            "severity": args.severity,
            "circuit": args.circuit,
            "status": args.status,
            "agent_name": args.agent,
            "input_ref": args.input_ref,
            "acceptance": args.acceptance,
            "return_if": args.return_if,
            "assumptions": args.assumptions,
            "debt_size": args.debt_size,
            "debt_notes": args.debt_notes,
        }
        actualizaciones = {k: v for k, v in campos.items() if v is not None}
        if actualizaciones:
            sets = ", ".join(f"{k} = ?" for k in actualizaciones)
            valores = list(actualizaciones.values()) + [args.id]
            conn.execute(
                f"UPDATE tasks SET {sets}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                valores,
            )
        print(f"✓ Tarea actualizada: {args.id}")
    conn.commit()
    conn.close()


def cmd_task_iterate(args):
    conn = conectar(Path(args.db))
    fila = conn.execute("SELECT iterations, status FROM tasks WHERE id = ?", (args.id,)).fetchone()
    if fila is None:
        sys.stderr.write(f"Error: No existe la tarea '{args.id}'\n")
        sys.exit(1)
    nuevas = fila["iterations"] + 1
    conn.execute(
        "UPDATE tasks SET iterations = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (nuevas, args.id),
    )
    conn.commit()
    conn.close()
    if nuevas >= LIMITE_ITERACIONES:
        print(
            f"⚠ LÍMITE ALCANZADO: '{args.id}' lleva {nuevas}/{LIMITE_ITERACIONES} iteraciones. "
            "DETÉN EL BUCLE y escala a la persona (Regla 10 de AGENTS.md)."
        )
        sys.exit(3)
    print(f"✓ Iteración {nuevas}/{LIMITE_ITERACIONES} registrada para '{args.id}'")


def cmd_note_add(args):
    conn = conectar(Path(args.db))
    conn.execute(
        """
        INSERT INTO task_notes (task_id, agent_name, kind, text, evidence_ref)
        VALUES (?, ?, ?, ?, ?)
        """,
        (args.task, args.agent, args.kind, args.text, args.evidence),
    )
    conn.commit()
    conn.close()
    print(f"✓ Nota ({args.kind}) añadida a '{args.task}' por {args.agent}")


def cmd_decision_add(args):
    conn = conectar(Path(args.db))
    conn.execute(
        """
        INSERT INTO decisions (task_id, title, chosen, alternatives, why)
        VALUES (?, ?, ?, ?, ?)
        """,
        (args.task, args.title, args.chosen, args.alternatives, args.why),
    )
    conn.commit()
    conn.close()
    print(f"✓ Decisión registrada: {args.title}")


def cmd_usage_add(args):
    conn = conectar(Path(args.db))
    conn.execute(
        """
        INSERT INTO model_usage (task_id, agent_name, provider, model, complexity, tokens_in, tokens_out, reason)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            args.task,
            args.agent,
            args.provider,
            args.model,
            args.complexity,
            args.tokens_in,
            args.tokens_out,
            args.reason,
        ),
    )
    conn.commit()
    conn.close()
    print(f"✓ Uso registrado: {args.agent} -> {args.provider}/{args.model} ({args.complexity})")


def cmd_status(args):
    conn = conectar(Path(args.db))
    tareas = conn.execute(
        "SELECT id, title, kind, severity, circuit, status, agent_name, iterations, debt_size "
        "FROM tasks ORDER BY updated_at DESC"
    ).fetchall()
    decisiones = conn.execute(
        "SELECT title, chosen, created_at FROM decisions ORDER BY id DESC LIMIT 5"
    ).fetchall()
    usos = conn.execute(
        "SELECT provider, model, complexity, COUNT(*) AS pasos, "
        "SUM(tokens_in) AS t_in, SUM(tokens_out) AS t_out "
        "FROM model_usage GROUP BY provider, model, complexity"
    ).fetchall()

    print("=== ESTADO DE MEMORIA (.agents/memory.sqlite3) ===")
    if not tareas:
        print("\nTareas: (ninguna registrada)")
    else:
        print(f"\nTareas ({len(tareas)}):")
        for t in tareas:
            agente = t["agent_name"] or "-"
            deuda = f" · deuda:{t['debt_size']}" if t["debt_size"] else ""
            alerta = " [¡ESCALAR!]" if t["iterations"] >= LIMITE_ITERACIONES else ""
            print(
                f"  - [{t['status']}] {t['id']} ({t['kind']}/{t['severity']} · {t['circuit']}) "
                f"agente:{agente} · vueltas:{t['iterations']}/{LIMITE_ITERACIONES}{deuda}{alerta}"
            )
            notas = conn.execute(
                "SELECT agent_name, kind, text FROM task_notes WHERE task_id = ? ORDER BY id DESC LIMIT 2",
                (t["id"],),
            ).fetchall()
            for n in notas:
                print(f"      ↳ ({n['kind']} @ {n['agent_name']}): {n['text']}")

    if decisiones:
        print(f"\nÚltimas decisiones (ADRs):")
        for d in decisiones:
            print(f"  - {d['title']} -> Elegido: {d['chosen']} ({d['created_at']})")

    if usos:
        print("\nUso por proveedor/modelo:")
        for u in usos:
            print(
                f"  - {u['provider']}/{u['model']} ({u['complexity']}): "
                f"{u['pasos']} paso(s) · in:{u['t_in'] or 0} / out:{u['t_out'] or 0} tokens"
            )
    conn.close()


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--db", default=str(DEFAULT_DB), help="Ruta a la base SQLite (.agents/memory.sqlite3)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="Inicializa la base de datos SQLite")
    p_init.set_defaults(func=cmd_init)

    p_status = sub.add_parser("status", help="Muestra el resumen del estado actual")
    p_status.set_defaults(func=cmd_status)

    p_task = sub.add_parser("task", help="Gestiona tareas del plan")
    sub_task = p_task.add_subparsers(dest="task_cmd", required=True)

    p_tset = sub_task.add_parser("set", help="Crea o actualiza una tarea")
    p_tset.add_argument("id", help="Fingerprint estable (sistema:modulo:sintoma)")
    p_tset.add_argument("--title", help="Título descriptivo")
    p_tset.add_argument("--kind", help="Tipo de petición (Incidencia, Historia, Tarea...)")
    p_tset.add_argument("--severity", choices=["bloqueante", "atencion", "observacion"])
    p_tset.add_argument("--circuit", choices=["quirurgico", "conciso", "completo"])
    p_tset.add_argument(
        "--status",
        choices=["BACKLOG", "TODO", "WIP", "INWAIT", "REVIEW", "DONE", "CANCELLED"],
    )
    p_tset.add_argument("--agent", help="Agente asignado actualmente")
    p_tset.add_argument("--input-ref", help="Punteros de entrada (rutas:líneas)")
    p_tset.add_argument("--acceptance", help="Criterio verificable de aceptación")
    p_tset.add_argument("--return-if", help="Condición explícita de rechazo (devuelve-si)")
    p_tset.add_argument("--assumptions", help="Supuestos etiquetados")
    p_tset.add_argument("--debt-size", choices=["sencilla", "media", "complicada"])
    p_tset.add_argument("--debt-notes", help="Detalle de deuda pendiente")
    p_tset.set_defaults(func=cmd_task_set)

    p_titer = sub_task.add_parser("iterate", help="Incrementa el contador de vueltas (código 3 a la 3.ª vuelta)")
    p_titer.add_argument("id", help="Fingerprint de la tarea")
    p_titer.set_defaults(func=cmd_task_iterate)

    p_note = sub.add_parser("note", help="Añade una observación o evidencia a una tarea")
    p_note.add_argument("--task", required=True, help="ID de la tarea")
    p_note.add_argument("--agent", required=True, help="Agente que deja la nota")
    p_note.add_argument(
        "--kind",
        required=True,
        choices=["handoff", "replanteo", "devolucion", "qa", "observacion"],
    )
    p_note.add_argument("--text", required=True, help="Contenido conciso de la nota")
    p_note.add_argument("--evidence", help="Ruta a fichero, test o commit de evidencia")
    p_note.set_defaults(func=cmd_note_add)

    p_dec = sub.add_parser("decision", help="Registra una decisión de diseño (ADR)")
    p_dec.add_argument("--task", help="ID de la tarea asociada (opcional)")
    p_dec.add_argument("--title", required=True, help="Qué se decidió")
    p_dec.add_argument("--chosen", required=True, help="Opción elegida")
    p_dec.add_argument("--alternatives", required=True, help="Alternativas descartadas")
    p_dec.add_argument("--why", required=True, help="Motivo y trade-offs asumidos")
    p_dec.set_defaults(func=cmd_decision_add)

    p_use = sub.add_parser("usage", help="Registra el modelo utilizado en una tarea")
    p_use.add_argument("--task", help="ID de la tarea")
    p_use.add_argument("--agent", required=True, help="Agente ejecutado")
    p_use.add_argument("--provider", required=True, help="Proveedor (google, anthropic, openai, local...)")
    p_use.add_argument("--model", required=True, help="Identificador del modelo")
    p_use.add_argument("--complexity", required=True, choices=["sencilla", "media", "complicada"])
    p_use.add_argument("--tokens-in", type=int, default=0)
    p_use.add_argument("--tokens-out", type=int, default=0)
    p_use.add_argument("--reason", default="nivel-modelo", help="Motivo de elección (manual, nivel-modelo, default)")
    p_use.set_defaults(func=cmd_usage_add)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
