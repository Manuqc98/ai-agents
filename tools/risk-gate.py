#!/usr/bin/env python3
"""Puerta de riesgo determinista para el repositorio objetivo (sin red y sin dependencias externas).

Calcula el nivel de riesgo de un cambio con hechos comprobables del diff, no con el criterio de un LLM:
  rutas sensibles      ¿Toca secretos, autenticación, pagos, migraciones, dependencias, CI o infraestructura?
                       Patrones por defecto + los que añada el proyecto en .agents/rutas-sensibles.txt.
  contenido sensible   ¿Alguna línea añadida menciona tokens, contraseñas, claves o credenciales?
                       El informe cita el fichero y la palabra, nunca la línea (podría contener el secreto).
  tamaño               ¿Supera el umbral de líneas cambiadas o de ficheros tocados?

Niveles y códigos de salida:
  0  bajo   Basta la verificación de qa.
  2  alto   Se suma security-reviewer y el PR pide revisión humana explícita de los motivos.
  1  error  No es un repositorio git, la base no existe u otro fallo de ejecución.

El LLM puede subir el nivel con un motivo, nunca bajarlo. Ante la duda los patrones se equivocan
hacia «alto» (por ejemplo, `*auth*` también captura `author.ts`).

Formato de los patrones (uno por línea, `#` para comentarios):
  sin «/»  se compara con cada componente de la ruta (fichero o carpeta), como en .gitignore.
  con «/»  se compara con la ruta completa desde la raíz del repositorio («*» también cruza «/»).
  Las mayúsculas no cuentan: `*auth*` captura `src/OAuthClient.ts`.

Uso:
  python3 tools/risk-gate.py                                  # cambios sin commitear del directorio actual
  python3 tools/risk-gate.py --repo ../mi-proyecto --base main
  python3 tools/risk-gate.py --config /ruta/rutas-sensibles.txt --max-lineas 500
  python3 tools/risk-gate.py --repo ../mi-proyecto --probar-patrones   # qué captura cada patrón del proyecto
"""
import argparse
import fnmatch
import re
import subprocess
import sys
from pathlib import Path

SALIDA_BAJO = 0
SALIDA_ERROR = 1
SALIDA_ALTO = 2
CONFIG_DEL_PROYECTO = Path(".agents") / "rutas-sensibles.txt"

PATRONES_POR_DEFECTO = (
    # Secretos y credenciales
    ".env*", "*secret*", "*credential*", "*.pem", "*.key",
    # Autenticación, sesiones y pagos (nombres en inglés y en español)
    "*auth*", "*login*", "*session*", "*sesion*", "*password*", "*permission*", "*permiso*",
    "*payment*", "*pago*", "*billing*", "*factura*",
    # Datos y migraciones
    "*migrations/*", "*.sql",
    # Dependencias
    "package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "requirements*.txt", "pyproject.toml", "poetry.lock", "uv.lock", "Pipfile*",
    "pom.xml", "build.gradle*", "go.mod", "go.sum", "Cargo.toml", "Cargo.lock",
    "composer.json", "composer.lock", "Gemfile*", "*.csproj",
    # Integración y despliegue continuos (CI/CD)
    ".github/workflows/*", ".gitlab-ci.yml", "Jenkinsfile", "azure-pipelines.yml", "bitbucket-pipelines.yml",
    # Infraestructura
    "Dockerfile*", "docker-compose*", "*.tf", "*.tfvars",
)

PALABRAS_SENSIBLES = re.compile(
    r"password|passwd|contraseña|secret|token|api[_-]?key|private[_-]?key|credential|authorization|clave",
    re.I,
)


class ErrorPuerta(Exception):
    """Fallo de ejecución que impide calcular el nivel (sale con código 1)."""


def git(repo, *args):
    resultado = subprocess.run(["git", "-C", str(repo), *args], capture_output=True)
    if resultado.returncode != 0:
        error = resultado.stderr.decode("utf-8", "replace").strip()
        raise ErrorPuerta(error or f"`git {' '.join(args)}` terminó con código {resultado.returncode}")
    return resultado.stdout


def leer_patrones(config):
    if not config.exists():
        return []
    lineas = (linea.strip() for linea in config.read_text(encoding="utf-8").splitlines())
    return [linea for linea in lineas if linea and not linea.startswith("#")]


def patron_que_coincide(ruta, patrones):
    """Devuelve el primer patrón que captura la ruta, o None."""
    ruta = ruta.lower()
    componentes = ruta.split("/")
    for patron in patrones:
        p = patron.lower()
        if "/" in p:
            if fnmatch.fnmatchcase(ruta, p.lstrip("/")):
                return patron
        elif any(fnmatch.fnmatchcase(c, p) for c in componentes):
            return patron
    return None


def cambios(repo, base):
    """Compara el árbol de trabajo con la base, incluidos los ficheros sin seguimiento.

    Devuelve dos diccionarios por ruta: líneas cambiadas y texto añadido.
    """
    try:
        git(repo, "rev-parse", "--verify", "--quiet", f"{base}^{{commit}}")
    except ErrorPuerta:
        raise ErrorPuerta(f"la base «{base}» no existe en {repo}") from None

    lineas, anadido = {}, {}
    for entrada in git(repo, "diff", "--numstat", "--no-renames", "-z", base).split(b"\0"):
        if entrada:
            anadidas, borradas, ruta = entrada.decode("utf-8", "replace").split("\t", 2)
            # Los binarios aparecen como «-»: cuentan como fichero tocado, no como líneas
            lineas[ruta] = sum(int(n) for n in (anadidas, borradas) if n.isdigit())

    diff = git(repo, "-c", "core.quotepath=false", "diff", "-U0", "--no-color", "--no-renames", base)
    ruta, en_cabecera = None, False
    for linea in diff.decode("utf-8", "replace").splitlines():
        if linea.startswith("diff --git "):
            ruta, en_cabecera = None, True
        elif linea.startswith("@@"):
            en_cabecera = False
        elif en_cabecera and linea.startswith("+++ "):
            # git añade un tabulador final si la ruta tiene espacios; /dev/null es un borrado
            ruta = linea[6:].rstrip("\t") if linea.startswith("+++ b/") else None
        elif not en_cabecera and ruta and linea.startswith("+"):
            anadido[ruta] = anadido.get(ruta, "") + linea[1:] + "\n"

    for cruda in git(repo, "ls-files", "--others", "--exclude-standard", "-z").split(b"\0"):
        if cruda:
            ruta = cruda.decode("utf-8", "replace")
            contenido = (repo / ruta).read_bytes()
            binario = b"\0" in contenido
            lineas[ruta] = 0 if binario else contenido.count(b"\n")
            anadido[ruta] = "" if binario else contenido.decode("utf-8", "replace")
    return lineas, anadido


def evaluar(lineas, anadido, patrones, max_lineas, max_ficheros):
    motivos = []
    for ruta in sorted(lineas):
        patron = patron_que_coincide(ruta, patrones)
        palabra = PALABRAS_SENSIBLES.search(anadido.get(ruta, ""))
        if patron:
            motivos.append(f"ruta sensible: {ruta} (patrón «{patron}»)")
        elif palabra:
            motivos.append(f"contenido sensible: {ruta} (una línea añadida menciona «{palabra.group(0).lower()}»)")
    total = sum(lineas.values())
    if total > max_lineas:
        motivos.append(f"tamaño: {total} líneas cambiadas (umbral {max_lineas})")
    if len(lineas) > max_ficheros:
        motivos.append(f"tamaño: {len(lineas)} ficheros tocados (umbral {max_ficheros})")
    return motivos


def probar_patrones(repo, patrones):
    """Muestra cuántos ficheros versionados captura cada patrón del proyecto (no evalúa el diff)."""
    ficheros = [r.decode("utf-8", "replace") for r in git(repo, "ls-files", "-z").split(b"\0") if r]
    if not patrones:
        print("sin patrones del proyecto: solo se aplican los patrones por defecto")
    for patron in patrones:
        capturados = [f for f in ficheros if patron_que_coincide(f, [patron])]
        if capturados:
            print(f"✓ «{patron}»: {len(capturados)} fichero(s), p. ej. {capturados[0]}")
        else:
            print(f"⚠ «{patron}»: ningún fichero (preventivo o errata)")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", default=".", help="Repositorio objetivo (por defecto, el directorio actual)")
    parser.add_argument("--base", default="HEAD", help="Referencia contra la que se compara (por defecto, HEAD)")
    parser.add_argument(
        "--config",
        help=f"Patrones extra del proyecto (por defecto, <repo>/{CONFIG_DEL_PROYECTO.as_posix()} si existe)",
    )
    parser.add_argument("--max-lineas", type=int, default=300, help="Umbral de líneas cambiadas (por defecto, 300)")
    parser.add_argument("--max-ficheros", type=int, default=20, help="Umbral de ficheros tocados (por defecto, 20)")
    parser.add_argument(
        "--probar-patrones",
        action="store_true",
        help="Lista qué ficheros versionados captura cada patrón del proyecto, sin evaluar el diff",
    )
    args = parser.parse_args()

    try:
        repo = Path(git(Path(args.repo), "rev-parse", "--show-toplevel").decode("utf-8").strip())
        config = Path(args.config) if args.config else repo / CONFIG_DEL_PROYECTO
        if args.config and not config.is_file():
            raise ErrorPuerta(f"no existe el fichero de patrones {config}")
        if args.probar_patrones:
            probar_patrones(repo, leer_patrones(config))
            sys.exit(SALIDA_BAJO)
        patrones = list(PATRONES_POR_DEFECTO) + leer_patrones(config)
        lineas, anadido = cambios(repo, args.base)
    except (ErrorPuerta, OSError) as e:
        print(f"✗ error: {e}", file=sys.stderr)
        sys.exit(SALIDA_ERROR)

    motivos = evaluar(lineas, anadido, patrones, args.max_lineas, args.max_ficheros)
    print(f"riesgo: {'alto' if motivos else 'bajo'}")
    print("motivos:" if motivos else "motivos: ninguno")
    for motivo in motivos:
        print(f"  - {motivo}")
    print(f"resumen: {len(lineas)} ficheros, {sum(lineas.values())} líneas, base {args.base}")
    sys.exit(SALIDA_ALTO if motivos else SALIDA_BAJO)


if __name__ == "__main__":
    main()
