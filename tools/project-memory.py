#!/usr/bin/env python3
"""Gestor de memoria persistente en SQLite para ai-agents (sin dependencias externas).

Permite que cualquier LLM o cliente recupere el estado del proyecto aunque se compacte
la ventana de contexto o se cambie de modelo a mitad de sesión.

Comandos principales:
  init        Inicializa .agents/memory.sqlite3 aplicando .agents/schema.sql
  status      Muestra el resumen de tareas activas, iteraciones, decisiones y uso de modelos
  task set    Crea o actualiza una tarea y su contrato de handoff
  task show   Muestra el detalle completo de una tarea (notas, decisiones y modelos usados)
  task iter   Suma 1 vuelta a una tarea (sale con código 3 al llegar al límite de 3 vueltas)
  note        Añade una nota de trazabilidad (handoff, replanteo, devolucion, qa, security, observacion)
  decision    Registra una decisión de arquitectura (ADR resumido)
  usage       Registra qué <proveedor>/<modelo> ejecutó un paso o lista el historial (--list)
"""
import argparse
import sqlite3
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
SCHEMA_PATH = RAIZ / ".agents" / "schema.sql"
DEFAULT_DB = RAIZ / ".agents" / "memory.sqlite3"
LIMITE_ITERACIONES = 3
TIPOS_NOTA = ["handoff", "replanteo", "devolucion", "qa", "security", "observacion"]


def resolver_db(args):
    if args.db is not None:
        if not args.db.strip():
            sys.stderr.write("Error: La ruta pasada a --db no puede estar vacía\n")
            sys.exit(1)
        return Path(args.db)
    if args.repo is not None:
        if not args.repo.strip() or not Path(args.repo).is_dir():
            sys.stderr.write(f"Error: No existe el directorio del repositorio '{args.repo}'\n")
            sys.exit(1)
        return Path(args.repo) / ".agents" / "memory.sqlite3"
    return DEFAULT_DB


def conectar(db_path):
    if not db_path.exists():
        sys.stderr.write(
            f"No existe {db_path}. Inicializa primero con: python3 tools/project-memory.py --db {db_path} init\n"
        )
        sys.exit(1)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def verificar_tarea(conn, task_id):
    fila = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if fila is None:
        sys.stderr.write(f"Error: No existe la tarea '{task_id}'\n")
        sys.exit(1)
    return fila


def _migrar_task_notes_si_falta_security(conn):
    fila = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'task_notes'"
    ).fetchone()
    if fila and fila[0] and "'security'" not in fila[0]:
        tipos = ", ".join(f"'{t}'" for t in TIPOS_NOTA)
        conn.execute("BEGIN IMMEDIATE")
        try:
            conn.execute("ALTER TABLE task_notes RENAME TO _task_notes_old")
            conn.execute(
                f"""
                CREATE TABLE task_notes (
                  id           INTEGER PRIMARY KEY AUTOINCREMENT,
                  task_id      TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
                  agent_name   TEXT NOT NULL,
                  kind         TEXT NOT NULL CHECK (kind IN ({tipos})),
                  text         TEXT NOT NULL,
                  evidence_ref TEXT,
                  created_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                "INSERT INTO task_notes (id, task_id, agent_name, kind, text, evidence_ref, created_at) "
                "SELECT id, task_id, agent_name, kind, text, evidence_ref, created_at FROM _task_notes_old"
            )
            conn.execute("DROP TABLE _task_notes_old")
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise


def cmd_init(args):
    db_path = resolver_db(args)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    # isolation_level=None permite transacciones explícitas que cubren también DDL en la migración
    conn = sqlite3.connect(db_path, isolation_level=None)
    try:
        _migrar_task_notes_si_falta_security(conn)
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    finally:
        conn.close()
    print(f"✓ Memoria inicializada en {db_path}")


def cmd_task_set(args):
    conn = conectar(resolver_db(args))
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


def cmd_task_show(args):
    conn = conectar(resolver_db(args))
    t = verificar_tarea(conn, args.id)
    print(f"=== TAREA: {t['id']} ===")
    print(f"Título:      {t['title']}")
    print(f"Clasif.:     {t['kind']} / {t['severity']} · circuito {t['circuit']}")
    print(f"Estado:      {t['status']} · agente: {t['agent_name'] or '-'} · vueltas: {t['iterations']}/{LIMITE_ITERACIONES}")
    print(f"Aceptación:  {t['acceptance']}")
    if t["input_ref"]:
        print(f"Entrada:     {t['input_ref']}")
    if t["return_if"]:
        print(f"Devuelve si: {t['return_if']}")
    if t["assumptions"]:
        print(f"Supuestos:   {t['assumptions']}")
    if t["debt_size"] or t["debt_notes"]:
        print(f"Deuda:       {t['debt_size'] or '-'} — {t['debt_notes'] or ''}")

    notas = conn.execute(
        "SELECT agent_name, kind, text, evidence_ref, created_at FROM task_notes WHERE task_id = ? ORDER BY id ASC",
        (t["id"],),
    ).fetchall()
    if notas:
        print("\nNotas:")
        for n in notas:
            ev = f" [evidencia: {n['evidence_ref']}]" if n["evidence_ref"] else ""
            print(f"  - [{n['created_at']}] ({n['kind']} @ {n['agent_name']}): {n['text']}{ev}")

    decisiones = conn.execute(
        "SELECT title, chosen, alternatives, why, created_at FROM decisions WHERE task_id = ? ORDER BY id ASC",
        (t["id"],),
    ).fetchall()
    if decisiones:
        print("\nDecisiones (ADRs):")
        for d in decisiones:
            print(f"  - [{d['created_at']}] {d['title']} -> Elegido: {d['chosen']} (descartado: {d['alternatives']}) · {d['why']}")

    usos = conn.execute(
        "SELECT agent_name, provider, model, complexity, tokens_in, tokens_out, reason, created_at "
        "FROM model_usage WHERE task_id = ? ORDER BY id ASC",
        (t["id"],),
    ).fetchall()
    if usos:
        print("\nUso de modelos:")
        for u in usos:
            print(
                f"  - [{u['created_at']}] {u['agent_name']} -> {u['provider']}/{u['model']} "
                f"({u['complexity']}) · in:{u['tokens_in'] or 0}/out:{u['tokens_out'] or 0} · {u['reason']}"
            )
    conn.close()


def cmd_task_iterate(args):
    conn = conectar(resolver_db(args))
    fila = verificar_tarea(conn, args.id)
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
    conn = conectar(resolver_db(args))
    verificar_tarea(conn, args.task)
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
    conn = conectar(resolver_db(args))
    if args.task:
        verificar_tarea(conn, args.task)
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


def cmd_usage(args):
    conn = conectar(resolver_db(args))
    if args.list:
        consulta = (
            "SELECT task_id, agent_name, provider, model, complexity, tokens_in, tokens_out, reason, created_at "
            "FROM model_usage"
        )
        params = []
        filtros = []
        if args.task:
            filtros.append("task_id = ?")
            params.append(args.task)
        if args.agent:
            filtros.append("agent_name = ?")
            params.append(args.agent)
        if filtros:
            consulta += " WHERE " + " AND ".join(filtros)
        consulta += " ORDER BY id ASC"
        filas = conn.execute(consulta, params).fetchall()
        conn.close()
        if not filas:
            print("(sin registros de uso)")
            return
        for u in filas:
            tarea = u["task_id"] or "-"
            print(
                f"  - [{u['created_at']}] tarea:{tarea} · {u['agent_name']} -> "
                f"{u['provider']}/{u['model']} ({u['complexity']}) · "
                f"in:{u['tokens_in'] or 0} / out:{u['tokens_out'] or 0} · {u['reason']}"
            )
        return

    if args.task:
        verificar_tarea(conn, args.task)
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
    db_path = resolver_db(args)
    conn = conectar(db_path)
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

    print(f"=== ESTADO DE MEMORIA ({db_path}) ===")
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
        print("\nÚltimas decisiones (ADRs):")
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
    origen = parser.add_mutually_exclusive_group()
    origen.add_argument("--repo", help="Repositorio objetivo (usa <repo>/.agents/memory.sqlite3)")
    origen.add_argument("--db", help=f"Ruta explícita a la base SQLite (por defecto, {DEFAULT_DB})")
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

    p_tshow = sub_task.add_parser("show", help="Muestra el detalle completo de una tarea")
    p_tshow.add_argument("id", help="Fingerprint de la tarea")
    p_tshow.set_defaults(func=cmd_task_show)

    p_titer = sub_task.add_parser("iterate", help="Incrementa el contador de vueltas (código 3 a la 3.ª vuelta)")
    p_titer.add_argument("id", help="Fingerprint de la tarea")
    p_titer.set_defaults(func=cmd_task_iterate)

    p_note = sub.add_parser("note", help="Añade una observación o evidencia a una tarea")
    p_note.add_argument("--task", required=True, help="ID de la tarea")
    p_note.add_argument("--agent", required=True, help="Agente que deja la nota")
    p_note.add_argument("--kind", required=True, choices=TIPOS_NOTA)
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

    p_use = sub.add_parser("usage", help="Registra o consulta el modelo utilizado")
    p_use.add_argument("--list", action="store_true", help="Lista registros de uso (filtrables con --task y --agent)")
    p_use.add_argument("--task", help="ID de la tarea")
    p_use.add_argument("--agent", help="Agente ejecutado")
    p_use.add_argument("--provider", help="Proveedor (google, anthropic, openai, local...)")
    p_use.add_argument("--model", help="Identificador del modelo")
    p_use.add_argument("--complexity", choices=["sencilla", "media", "complicada"])
    p_use.add_argument("--tokens-in", type=int, default=0)
    p_use.add_argument("--tokens-out", type=int, default=0)
    p_use.add_argument("--reason", default="nivel-modelo", help="Motivo de elección (manual, nivel-modelo, default)")
    p_use.set_defaults(func=cmd_usage, _parser=p_use)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    if args.cmd == "usage" and not args.list:
        faltan = [f"--{k}" for k in ("agent", "provider", "model", "complexity") if not getattr(args, k)]
        if faltan:
            args._parser.error(f"para registrar uso hacen falta: {', '.join(faltan)} (o pasa --list para consultar)")
    args.func(args)


if __name__ == "__main__":
    main()
