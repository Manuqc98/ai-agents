#!/usr/bin/env python3
"""Puerta de riesgo determinista para el repositorio objetivo (sin red y sin dependencias externas).

Calcula el nivel de riesgo de un cambio con hechos comprobables del diff, no con el criterio de un LLM:
  rutas sensibles      ¿Toca secretos, autenticación, pagos, migraciones, dependencias, CI o infraestructura?
                       Patrones por defecto + los del proyecto en .agents/rutas-sensibles.txt, tomados de la
                       punta de la base, del ancestro común y del árbol de trabajo, más los de --config:
                       el cambio puede añadir patrones, nunca quitarlos.
  contenido sensible   ¿Alguna línea añadida menciona tokens, contraseñas, claves o credenciales?
                       El informe cita el fichero y la palabra, nunca la línea (podría contener el secreto).
  tamaño               ¿Supera el umbral de líneas cambiadas o de ficheros tocados?

El cambio es el árbol de trabajo (incluidos los ficheros sin seguimiento) frente al ancestro común
de la base y HEAD, como `git diff --merge-base <base>`: lo que la base avanzó después no cuenta.

Niveles y códigos de salida:
  0  bajo   Basta la verificación de qa.
  2  alto   Se suma security-reviewer y el PR pide revisión humana explícita de los motivos.
  1  error  No es un repositorio git, la base no existe, argumentos inválidos u otro fallo de ejecución.

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
MAX_BYTES_LEIDOS = 1 << 20

PATRONES_POR_DEFECTO = (
    # Secretos y credenciales
    ".env*", "*secret*", "*credential*", "*.pem", "*.key", "*.p12", "*.pfx", "*.jks", "*.keystore",
    "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519", ".npmrc", ".pypirc", ".netrc",
    # Autenticación, sesiones y pagos (nombres en inglés y en español)
    "*auth*", "*login*", "*session*", "*sesion*", "*password*", "*permission*", "*permiso*",
    "*payment*", "*pago*", "*billing*", "*factura*",
    # Datos y migraciones
    "*migrations/*", "*migration/*", "*migrate/*", "*alembic/*", "*.sql",
    # Dependencias
    "package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "requirements*.txt", "pyproject.toml", "poetry.lock", "uv.lock", "Pipfile*",
    "pom.xml", "build.gradle*", "go.mod", "go.sum", "Cargo.toml", "Cargo.lock",
    "composer.json", "composer.lock", "Gemfile*", "*.csproj",
    # Integración y despliegue continuos (CI/CD)
    ".github/workflows/*", ".github/actions/*", ".gitlab-ci.yml", ".circleci/*", ".travis.yml",
    "Jenkinsfile", "azure-pipelines.yml", "bitbucket-pipelines.yml",
    # Infraestructura
    "Dockerfile*", "docker-compose*", "*.tf", "*.tfvars", "*k8s/*", "*kubernetes/*", "*helm/*",
    "Chart.yaml", "serverless.yml",
    # La propia configuración de la puerta
    CONFIG_DEL_PROYECTO.as_posix(),
)

PALABRAS_SENSIBLES = re.compile(
    r"password|passwd|contraseña|secret|token|api[_-]?key|private[\s_-]?key|credential|authorization|clave",
    re.I,
)

# Fijas para que la configuración git de cada persona (prefijos, diff externo, textconv) no cambie la salida
OPCIONES_DIFF = ("--no-color", "--no-ext-diff", "--no-textconv", "--no-renames", "--src-prefix=a/", "--dst-prefix=b/")


class ErrorPuerta(Exception):
    """Fallo de ejecución que impide calcular el nivel (sale con código 1)."""


def git(repo, *args):
    resultado = subprocess.run(["git", "-C", str(repo), *args], capture_output=True)
    if resultado.returncode != 0:
        error = resultado.stderr.decode("utf-8", "replace").strip()
        raise ErrorPuerta(error or f"`git {' '.join(args)}` terminó con código {resultado.returncode}")
    return resultado.stdout


def patrones_de(datos):
    # utf-8-sig quita el BOM que añaden algunos editores de Windows (pegado al primer patrón, lo anularía)
    lineas = (linea.strip() for linea in datos.decode("utf-8-sig", "replace").splitlines())
    return [linea for linea in lineas if linea and not linea.startswith("#")]


def patrones_del_proyecto(repo, refs, extra=None):
    """Une la config versionada en cada referencia, la del árbol de trabajo y la de --config.

    Así el cambio no puede quitar patrones. Si la config es local (sin versionar), vale la del árbol de trabajo.
    """
    patrones = []
    for ref in dict.fromkeys(refs):
        try:
            patrones += patrones_de(git(repo, "show", f"{ref}:{CONFIG_DEL_PROYECTO.as_posix()}"))
        except ErrorPuerta:
            pass  # esa referencia no la tiene versionada
    for fichero in (repo / CONFIG_DEL_PROYECTO, extra):
        if fichero and fichero.is_file():
            patrones += patrones_de(fichero.read_bytes())
    return list(dict.fromkeys(patrones))


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


def ancestro_comun(repo, base):
    """Commit contra el que se compara: el ancestro común de la base y HEAD."""
    try:
        git(repo, "rev-parse", "--verify", "--quiet", f"{base}^{{commit}}")
    except ErrorPuerta:
        raise ErrorPuerta(f"la base «{base}» no existe en {repo}") from None
    try:
        return git(repo, "merge-base", base, "HEAD").decode("utf-8").strip()
    except ErrorPuerta:
        motivo = f"«{base}» y HEAD no tienen ancestro común en {repo}"
        if git(repo, "rev-parse", "--is-shallow-repository").strip() == b"true":
            motivo += "; el clon es superficial: trae la historia con `git fetch --unshallow` (o `fetch-depth: 0` en CI)"
        raise ErrorPuerta(motivo) from None


def ruta_de_cabecera(cabecera):
    """Ruta de una línea `+++ b/<ruta>` del diff, o None si es un borrado (`+++ /dev/null`).

    git añade un tabulador final si la ruta tiene espacios, y entrecomilla con escapes de C (`\\"`, `\\303\\261`)
    las que tienen comillas, barras invertidas, caracteres de control o caracteres no ASCII.
    """
    nombre = cabecera[4:].rstrip(b"\t")
    if nombre.startswith(b'"') and nombre.endswith(b'"'):
        # unicode_escape deshace los escapes; latin-1 devuelve los bytes originales para decodificarlos como UTF-8
        nombre = nombre[1:-1].decode("unicode_escape").encode("latin-1")
    return nombre[2:].decode("utf-8", "replace") if nombre.startswith(b"b/") else None


def cambios(repo, ancestro):
    """Compara el árbol de trabajo con el ancestro común, incluidos los ficheros sin seguimiento.

    Devuelve dos diccionarios por ruta: líneas cambiadas y la primera palabra sensible de sus líneas añadidas.
    """
    lineas, palabras = {}, {}
    for entrada in git(repo, "diff", "--numstat", "-z", *OPCIONES_DIFF, ancestro).split(b"\0"):
        if entrada:
            anadidas, borradas, ruta = entrada.decode("utf-8", "replace").split("\t", 2)
            # Los binarios aparecen como «-»: cuentan como fichero tocado, no como líneas
            lineas[ruta] = sum(int(n) for n in (anadidas, borradas) if n.isdigit())

    ruta, en_cabecera = None, False
    # Solo se parte por «\n»: splitlines() también parte por \r, \f o \x1c y separaría una línea de su «+»
    for linea in git(repo, "diff", "-U0", *OPCIONES_DIFF, ancestro).split(b"\n"):
        if linea.startswith(b"diff --git "):
            ruta, en_cabecera = None, True
        elif linea.startswith(b"@@"):
            en_cabecera = False
        elif en_cabecera and linea.startswith(b"+++ "):
            ruta = ruta_de_cabecera(linea)
        elif not en_cabecera and ruta and ruta not in palabras and linea.startswith(b"+"):
            encontrada = PALABRAS_SENSIBLES.search(linea[1:].decode("utf-8", "replace"))
            if encontrada:
                palabras[ruta] = encontrada.group(0).lower()

    for cruda in git(repo, "ls-files", "--others", "--exclude-standard", "-z").split(b"\0"):
        if not cruda:
            continue
        ruta = cruda.decode("utf-8", "replace")
        fichero = repo / ruta
        if fichero.is_symlink() or not fichero.is_file():
            lineas[ruta] = 0  # enlace, repositorio anidado o fichero especial: cuenta como tocado, no se lee
            continue
        with fichero.open("rb") as f:
            # shortcut: solo se lee el primer MiB de cada fichero sin seguimiento, subir MAX_BYTES_LEIDOS si hiciera falta escanear ficheros mayores, sencilla
            contenido = f.read(MAX_BYTES_LEIDOS)
        texto = "" if b"\0" in contenido else contenido.decode("utf-8", "replace")  # binario: tocado, sin líneas
        lineas[ruta] = texto.count("\n") + (bool(texto) and not texto.endswith("\n"))
        encontrada = PALABRAS_SENSIBLES.search(texto)
        if encontrada:
            palabras[ruta] = encontrada.group(0).lower()
    return lineas, palabras


def evaluar(lineas, palabras, patrones, max_lineas, max_ficheros):
    motivos = []
    for ruta in sorted(lineas.keys() | palabras.keys()):
        patron = patron_que_coincide(ruta, patrones)
        if patron:
            motivos.append(f"ruta sensible: {ruta} (patrón «{patron}»)")
        elif ruta in palabras:
            motivos.append(f"contenido sensible: {ruta} (una línea añadida menciona «{palabras[ruta]}»)")
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
        help=f"Fichero de patrones adicional: se suma a los del proyecto (<repo>/{CONFIG_DEL_PROYECTO.as_posix()}), nunca los sustituye",
    )
    parser.add_argument("--max-lineas", type=int, default=300, help="Umbral de líneas cambiadas (por defecto, 300)")
    parser.add_argument("--max-ficheros", type=int, default=20, help="Umbral de ficheros tocados (por defecto, 20)")
    parser.add_argument(
        "--probar-patrones",
        action="store_true",
        help="Lista qué ficheros versionados captura cada patrón del proyecto, sin evaluar el diff",
    )
    try:
        args = parser.parse_args()
    except SystemExit as e:
        # argparse sale con 2 ante un error de uso, que aquí significaría «alto»
        raise SystemExit(SALIDA_ERROR if e.code else SALIDA_BAJO)

    try:
        repo = Path(git(Path(args.repo), "rev-parse", "--show-toplevel").decode("utf-8").strip())
        if args.config and not Path(args.config).is_file():
            raise ErrorPuerta(f"no existe el fichero de patrones {args.config}")
        ancestro = "HEAD" if args.probar_patrones else ancestro_comun(repo, args.base)
        proyecto = patrones_del_proyecto(repo, (args.base, ancestro), Path(args.config) if args.config else None)
        if args.probar_patrones:
            probar_patrones(repo, proyecto)
            sys.exit(SALIDA_BAJO)
        lineas, palabras = cambios(repo, ancestro)
    except (ErrorPuerta, OSError) as e:
        print(f"✗ error: {e}", file=sys.stderr)
        sys.exit(SALIDA_ERROR)

    motivos = evaluar(lineas, palabras, list(PATRONES_POR_DEFECTO) + proyecto, args.max_lineas, args.max_ficheros)
    print(f"riesgo: {'alto' if motivos else 'bajo'}")
    print("motivos:" if motivos else "motivos: ninguno")
    for motivo in motivos:
        print(f"  - {motivo}")
    print(f"resumen: {len(lineas)} ficheros, {sum(lineas.values())} líneas, base {args.base} (ancestro común {ancestro[:12]})")
    sys.exit(SALIDA_ALTO if motivos else SALIDA_BAJO)


if __name__ == "__main__":
    main()
