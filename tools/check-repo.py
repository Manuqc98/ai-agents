#!/usr/bin/env python3
"""Validador determinista del repositorio ai-agents (sin red y sin dependencias externas).

Ejecuta cuatro baterías de comprobación:
  enlaces       Verifica que todo enlace relativo en ficheros .md exista (incluyendo #anclas).
  frontmatter   Verifica que agentes, skills y specs cumplan el esquema de metadatos.
  portabilidad  Verifica las reglas Multi-LLM y Multi-Harness:
                  1. CLAUDE.md apunta a AGENTS.md (fuente canónica única).
                  2. Todos los agentes incluyen las directivas IMPORTANTE en texto plano.
                  3. Ningún agente ni skill tiene modelos concretos clavados ni bloques propietarios.
  clasificacion Verifica que los casos de tests/clasificacion.md concuerden con la tabla
                canónica de skills/agent-routing/SKILL.md.

Uso:
  python3 tools/check-repo.py
  python3 tools/check-repo.py --solo portabilidad
"""
import argparse
import re
import sys
import unicodedata
import urllib.parse
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
NIVELES = {"sencilla", "media", "complicada"}
MODOS = {"primary", "subagent"}
FASES = {"Transversal", "Fase 1", "Fase 2", "Fase 3", "Fase 4"}
IGNORADOS = {".git", "node_modules", "__pycache__", ".venv", "venv"}

# Patrones de acoplamiento prohibidos fuera de docs/LLM.md y plantillas
MODELOS_HARDCODEADOS = re.compile(
    r"\b(claude-(?:opus|sonnet|haiku)|gpt-[456]|gemini-[1234]|llama-3|qwen3-|deepseek-(?:r1|v3))\b",
    re.I,
)
BLOQUES_PROPIETARIOS = re.compile(r"^\s*hermes\s*:", re.M)


def ficheros_md():
    """Devuelve todos los ficheros .md reales (excluyendo symlinks para no validar dos veces)."""
    encontrados = [p for p in RAIZ.glob("*.md") if not p.is_symlink()]
    for carpeta in sorted(d for d in RAIZ.iterdir() if d.is_dir() and d.name not in IGNORADOS):
        for ruta in carpeta.rglob("*.md"):
            if not ruta.is_symlink() and not any(parte in IGNORADOS for parte in ruta.parts):
                encontrados.append(ruta)
    return sorted(set(encontrados))


def frontmatter(ruta):
    texto = ruta.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
    if not texto.startswith("---\n"):
        return None, texto
    fin = texto.find("\n---\n", 3)
    if fin == -1:
        return None, texto
    return texto[4:fin], texto[fin + 5:]


def campo(cabecera, nombre):
    if cabecera is None:
        return None
    m = re.search(rf"^{re.escape(nombre)}:[ \t]*(.+)$", cabecera, re.M)
    if not m:
        return None
    valor = m.group(1).split("#")[0].strip().strip("\"'")
    return valor


def plano(texto):
    limpio = texto.replace("`", "").replace("*", "")
    sin_tildes = unicodedata.normalize("NFKD", limpio)
    return "".join(c for c in sin_tildes if not unicodedata.combining(c)).strip().lower()


def slug_encabezado(titulo):
    """Convierte un encabezado Markdown al slug de ancla exacto de GitHub."""
    limpio = re.sub(r"[`*_~]", "", titulo).strip().lower()
    sin_tildes = "".join(
        c for c in unicodedata.normalize("NFKD", limpio) if not unicodedata.combining(c)
    )
    # GitHub elimina puntuación y convierte cada espacio individual en un guion
    slug = re.sub(r"[^\w\s-]", "", sin_tildes)
    slug = slug.strip().replace(" ", "-")
    return slug


def anclas_de(ruta):
    """Extrae el conjunto de slugs de encabezados de un fichero Markdown."""
    anclas = set()
    en_codigo = False
    for linea in ruta.read_text(encoding="utf-8", errors="replace").splitlines():
        if linea.strip().startswith("```"):
            en_codigo = not en_codigo
            continue
        if en_codigo:
            continue
        m = re.match(r"^#{1,6}\s+(.+)$", linea)
        if m:
            anclas.add(slug_encabezado(m.group(1)))
    return anclas


# --- 1. Enlaces y anclas -----------------------------------------------------

def comprobar_enlaces():
    fallos = []
    patron = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
    cache_anclas = {}

    for ruta in ficheros_md():
        en_codigo = False
        for numero, linea in enumerate(ruta.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if linea.strip().startswith("```"):
                en_codigo = not en_codigo
                continue
            if en_codigo:
                continue
            for destino in patron.findall(linea):
                if destino.startswith(("http://", "https://", "mailto:")):
                    continue
                if "<" in destino or ">" in destino:
                    continue
                partes = destino.split("#", 1)
                ruta_rel = partes[0]
                ancla = partes[1] if len(partes) > 1 else None

                objetivo = (ruta.parent / urllib.parse.unquote(ruta_rel)).resolve() if ruta_rel else ruta
                if not objetivo.exists():
                    fallos.append(f"{ruta.relative_to(RAIZ)}:{numero}: enlace roto -> {destino}")
                    continue
                if ancla and objetivo.is_file() and objetivo.suffix == ".md":
                    if objetivo not in cache_anclas:
                        cache_anclas[objetivo] = anclas_de(objetivo)
                    ancla_normalizada = slug_encabezado(urllib.parse.unquote(ancla))
                    if ancla_normalizada not in cache_anclas[objetivo]:
                        fallos.append(
                            f"{ruta.relative_to(RAIZ)}:{numero}: ancla #{ancla} no encontrada en {objetivo.relative_to(RAIZ)}"
                        )
    return fallos


# --- 2. Frontmatter ----------------------------------------------------------

def comprobar_frontmatter():
    fallos = []
    for ruta in sorted((RAIZ / "agents").glob("*.md")):
        rel = ruta.relative_to(RAIZ)
        cabecera, _ = frontmatter(ruta)
        if cabecera is None:
            fallos.append(f"{rel}: sin frontmatter YAML")
            continue
        nombre = campo(cabecera, "name")
        if nombre != ruta.stem:
            fallos.append(f"{rel}: `name` ({nombre!r}) no coincide con el fichero ({ruta.stem!r})")
        if not campo(cabecera, "description"):
            fallos.append(f"{rel}: falta `description`")
        modo = campo(cabecera, "mode")
        if modo not in MODOS:
            fallos.append(f"{rel}: `mode` ({modo!r}) debe estar en {sorted(MODOS)}")
        temp = campo(cabecera, "temperature")
        try:
            float(temp)
        except (TypeError, ValueError):
            fallos.append(f"{rel}: `temperature` ({temp!r}) debe ser un número")
        nivel = campo(cabecera, "nivel-modelo")
        if nivel not in NIVELES:
            fallos.append(f"{rel}: `nivel-modelo` ({nivel!r}) debe estar en {sorted(NIVELES)}")
        fase = campo(cabecera, "fase")
        if fase not in FASES:
            fallos.append(f"{rel}: `fase` ({fase!r}) debe estar en {sorted(FASES)}")
        if not campo(cabecera, "etiqueta"):
            fallos.append(f"{rel}: falta `etiqueta`")

    for patron in ("skills/*/SKILL.md", "specs/*/SKILL.md"):
        for ruta in sorted(RAIZ.glob(patron)):
            rel = ruta.relative_to(RAIZ)
            cabecera, _ = frontmatter(ruta)
            if cabecera is None:
                fallos.append(f"{rel}: sin frontmatter YAML")
                continue
            nombre = campo(cabecera, "name")
            if nombre != ruta.parent.name:
                fallos.append(f"{rel}: `name` ({nombre!r}) no coincide con la carpeta ({ruta.parent.name!r})")
            if not campo(cabecera, "description"):
                fallos.append(f"{rel}: falta `description`")
            if not campo(cabecera, "version"):
                fallos.append(f"{rel}: falta `version`")
    return fallos


# --- 3. Portabilidad Multi-LLM y Multi-Harness -------------------------------

def comprobar_portabilidad():
    fallos = []

    # 3.1 Fuente canónica única: AGENTS.md y CLAUDE.md
    agents_md = RAIZ / "AGENTS.md"
    claude_md = RAIZ / "CLAUDE.md"
    if not agents_md.exists():
        fallos.append("Falta AGENTS.md en la raíz del repositorio")
    if not claude_md.exists():
        fallos.append("Falta CLAUDE.md (debe ser symlink a AGENTS.md para compatibilidad multi-cliente)")
    elif not claude_md.is_symlink() and claude_md.read_bytes() != agents_md.read_bytes():
        fallos.append("CLAUDE.md no es symlink ni coincide con AGENTS.md: usa `ln -sf AGENTS.md CLAUDE.md`")

    # 3.2 Directivas en lenguaje natural obligatorias en cada agente
    directivas_obligatorias = (
        "IMPORTANTE — IDIOMA:",
        "IMPORTANTE — VOCABULARIO:",
        "IMPORTANTE — ROL Y LÍMITES",
    )
    for ruta in sorted((RAIZ / "agents").glob("*.md")):
        rel = ruta.relative_to(RAIZ)
        cabecera, cuerpo = frontmatter(ruta)
        for directiva in directivas_obligatorias:
            if directiva not in cuerpo:
                fallos.append(
                    f"{rel}: falta la directiva en texto plano '{directiva}' (necesaria para clientes que ignoran permisos YAML)"
                )
        if MODELOS_HARDCODEADOS.search( ruta.read_text(encoding="utf-8") ):
            fallos.append(
                f"{rel}: contiene un ID de modelo concreto hardcodeado; usa `nivel-modelo` y delega en docs/LLM.md"
            )
        if cabecera and BLOQUES_PROPIETARIOS.search(cabecera):
            fallos.append(f"{rel}: contiene bloque propietario en frontmatter (p. ej. `hermes:`)")

    # 3.3 Skills y specs libres de modelos hardcodeados y metadatos propietarios
    for patron in ("skills/*/SKILL.md", "specs/*/SKILL.md"):
        for ruta in sorted(RAIZ.glob(patron)):
            rel = ruta.relative_to(RAIZ)
            cabecera, _ = frontmatter(ruta)
            texto = ruta.read_text(encoding="utf-8")
            if MODELOS_HARDCODEADOS.search(texto):
                fallos.append(
                    f"{rel}: contiene un ID de modelo concreto hardcodeado; los modelos solo se definen en docs/LLM.md"
                )
            if cabecera and BLOQUES_PROPIETARIOS.search(cabecera):
                fallos.append(f"{rel}: contiene bloque propietario en frontmatter (p. ej. `hermes:`)")

    return fallos


# --- 4. Clasificación --------------------------------------------------------

def filas_tabla(texto, cabecera_contiene):
    filas, dentro = [], False
    for linea in texto.splitlines():
        if linea.startswith("|") and cabecera_contiene in linea:
            dentro = True
            continue
        if dentro:
            if not linea.startswith("|"):
                break
            celdas = [c.strip() for c in linea.strip("|").split("|")]
            if all(set(c) <= set("-: ") for c in celdas):
                continue
            filas.append(celdas)
    return filas


def tabla_de_circuitos():
    ruta_skill = RAIZ / "skills" / "agent-routing" / "SKILL.md"
    texto = ruta_skill.read_text(encoding="utf-8").replace("\r\n", "\n")
    severidades = {plano(f[0]) for f in filas_tabla(texto, "| Severidad |")}
    tipos, mapa = set(), {}
    for celdas in filas_tabla(texto, "| Tipo | Severidad | Circuito |"):
        tipo = plano(celdas[0])
        tipos.add(tipo)
        crudo = plano(celdas[1])
        cuales = severidades if crudo in ("cualquiera", "—", "-", "") else {
            s.strip() for s in crudo.split("/")
        }
        circuito = plano(celdas[2])
        for sev in cuales:
            mapa[(tipo, sev)] = circuito
    return tipos, severidades, mapa


def comprobar_clasificacion():
    casos = RAIZ / "tests" / "clasificacion.md"
    if not casos.exists():
        return ["Falta tests/clasificacion.md con la batería de regresión de enrutado"]
    tipos, severidades, mapa = tabla_de_circuitos()
    if not mapa:
        return ["No se pudo leer la tabla de circuitos de skills/agent-routing/SKILL.md"]
    fallos = []
    filas = filas_tabla(casos.read_text(encoding="utf-8"), "| Tipo | Severidad | Circuito |")
    if len(filas) < 10:
        fallos.append(f"tests/clasificacion.md: tiene {len(filas)} casos; el mínimo requerido es 10")
    for celdas in filas:
        ident, _peticion, tipo, severidad, circuito = celdas[:5]
        t_p, s_p, c_p = plano(tipo), plano(severidad), plano(circuito)
        if t_p not in tipos:
            fallos.append(f"caso #{ident}: tipo {tipo!r} no existe en agent-routing")
            continue
        if s_p not in severidades:
            fallos.append(f"caso #{ident}: severidad {severidad!r} no existe en agent-routing")
            continue
        esperado = mapa.get((t_p, s_p))
        if esperado and c_p != esperado:
            fallos.append(
                f"caso #{ident}: para {tipo}/{severidad} agent-routing exige '{esperado}' pero el test dice '{c_p}'"
            )
    return fallos


COMPROBACIONES = {
    "enlaces": comprobar_enlaces,
    "frontmatter": comprobar_frontmatter,
    "portabilidad": comprobar_portabilidad,
    "clasificacion": comprobar_clasificacion,
}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--solo",
        choices=sorted(COMPROBACIONES),
        action="append",
        help="ejecuta únicamente las comprobaciones indicadas (por defecto, todas)",
    )
    args = parser.parse_args()
    nombres = args.solo or list(COMPROBACIONES)

    total_fallos = 0
    for nombre in nombres:
        fallos = COMPROBACIONES[nombre]()
        if fallos:
            print(f"✗ {nombre}: {len(fallos)} fallo(s)")
            for f in fallos:
                print(f"  - {f}")
            total_fallos += len(fallos)
        else:
            print(f"✓ {nombre}: OK")

    sys.exit(1 if total_fallos else 0)


if __name__ == "__main__":
    main()
