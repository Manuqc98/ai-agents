"""Pruebas de tools/risk-gate.py sobre repositorios git temporales (solo biblioteca estándar).

Uso:
  python3 -m unittest discover tests
"""
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "risk-gate.py"
# Sin la configuración git de quien ejecuta las pruebas ni sus variables GIT_*: un hook exporta GIT_DIR o
# GIT_INDEX_FILE, que ganan a `git -C` y harían que las pruebas escribieran en el repositorio exterior
ENTORNO = {
    **{clave: valor for clave, valor in os.environ.items() if not clave.startswith("GIT_")},
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
}


class PuertaDeRiesgo(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        self.git("init", "-q")
        self.escribir("src/app.py", "print('hola')\n")
        self.commit()

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args):
        subprocess.run(["git", "-C", str(self.repo), *args], check=True, capture_output=True, env=ENTORNO)

    def commit(self):
        self.git("add", ".")
        self.git(
            "-c", "user.name=test", "-c", "user.email=test@example.com", "-c", "commit.gpgsign=false",
            "commit", "-qm", "cambio",
        )

    def escribir(self, ruta, texto, raiz=None):
        destino = (raiz or self.repo) / ruta
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(texto, encoding="utf-8")
        return destino

    def puerta(self, *args, entorno=ENTORNO):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--repo", str(self.repo), *args], capture_output=True, text=True, env=entorno
        )

    def test_cambio_pequeno_en_fichero_normal_es_bajo(self):
        self.escribir("src/app.py", "print('adiós')\n")
        r = self.puerta()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("riesgo: bajo", r.stdout)

    def test_tocar_dependencias_es_alto(self):
        self.escribir("package.json", "{}\n")
        r = self.puerta()
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("package.json", r.stdout)

    def test_superar_el_umbral_de_lineas_es_alto(self):
        self.escribir("src/app.py", "x = 1\n" * 301)
        r = self.puerta()
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("líneas cambiadas", r.stdout)

    def test_fichero_nuevo_sin_seguimiento_en_auth_es_alto(self):
        self.escribir("src/auth/sesion.py", "TTL = 60\n")
        r = self.puerta()
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("src/auth/sesion.py", r.stdout)

    def test_los_patrones_ignoran_mayusculas(self):
        self.escribir("src/OAuthClient.ts", "export {}\n")
        self.assertEqual(self.puerta().returncode, 2)

    def test_nombres_en_espanol_son_rutas_sensibles(self):
        self.escribir("src/sesion.js", "export {}\n")
        r = self.puerta()
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("src/sesion.js", r.stdout)

    def test_palabra_sensible_en_linea_anadida_es_alto_sin_copiar_la_linea(self):
        self.escribir("src/app.py", "print('hola')\nlog.info('acceso', token_de_sesion)\n")
        r = self.puerta()
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("contenido sensible: src/app.py", r.stdout)
        self.assertNotIn("token_de_sesion", r.stdout)

    def test_patron_de_config_externa_es_alto(self):
        config = self.escribir("rutas.txt", "# pagos\nsrc/app.py\n", raiz=Path(self.tmp.name))
        self.escribir("src/app.py", "print('adiós')\n")
        r = self.puerta("--config", str(config))
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("src/app.py", r.stdout)

    def test_config_del_proyecto_se_aplica_por_defecto(self):
        self.escribir(".agents/rutas-sensibles.txt", "src/nominas/*\n")
        self.escribir("src/nominas/calculo.py", "IRPF = 0\n")
        self.commit()
        self.escribir("src/nominas/calculo.py", "IRPF = 1\n")
        r = self.puerta()
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("src/nominas/*", r.stdout)

    def test_probar_patrones_avisa_de_los_que_no_capturan_nada(self):
        config = self.escribir("rutas.txt", "src/app.py\n*broker*\n", raiz=Path(self.tmp.name))
        r = self.puerta("--config", str(config), "--probar-patrones")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("✓ «src/app.py»: 1 fichero(s)", r.stdout)
        self.assertIn("⚠ «*broker*»: ningún fichero", r.stdout)

    def test_base_inexistente_es_error(self):
        r = self.puerta("--base", "no-existe")
        self.assertEqual(r.returncode, 1)
        self.assertIn("no-existe", r.stderr)

    def test_error_de_uso_es_error_y_no_alto(self):
        self.assertEqual(self.puerta("--bse", "main").returncode, 1)

    def test_la_config_git_del_usuario_no_oculta_el_contenido(self):
        self.escribir("src/app.py", "print('hola')\npassword = 'x'\n")
        for clave in ("diff.noprefix", "diff.mnemonicPrefix"):
            entorno = {**ENTORNO, "GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": clave, "GIT_CONFIG_VALUE_0": "true"}
            r = self.puerta(entorno=entorno)
            self.assertEqual(r.returncode, 2, f"{clave}: {r.stdout}{r.stderr}")
            self.assertIn("contenido sensible: src/app.py", r.stdout)

    def test_clave_privada_es_alto(self):
        self.escribir("claves/servidor.txt", "-----BEGIN OPENSSH PRIVATE KEY-----\nAAAA\n-----END OPENSSH PRIVATE KEY-----\n")
        r = self.puerta()
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("private key", r.stdout)

    def test_migracion_de_rails_es_alto(self):
        self.escribir("db/migrate/20261105_quitar_columna.rb", "remove_column :pedidos, :nota\n")
        self.assertEqual(self.puerta().returncode, 2)

    def test_vaciar_la_config_del_proyecto_no_desactiva_sus_patrones(self):
        self.escribir(".agents/rutas-sensibles.txt", "src/nominas/*\n")
        self.escribir("src/nominas/calculo.py", "IRPF = 0\n")
        self.commit()
        self.escribir(".agents/rutas-sensibles.txt", "")
        self.escribir("src/nominas/calculo.py", "IRPF = 1\n")
        r = self.puerta()
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("src/nominas/*", r.stdout)
        self.assertIn("ruta sensible: .agents/rutas-sensibles.txt", r.stdout)

    def test_base_compara_contra_el_ancestro_comun(self):
        self.git("branch", "base")
        self.git("switch", "-q", "base")
        self.escribir("package.json", "{}\n")  # la base avanza con un cambio sensible ajeno a la rama
        self.commit()
        self.git("switch", "-q", "-")
        self.escribir("src/app.py", "print('adiós')\n")
        self.commit()
        r = self.puerta("--base", "base")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("resumen: 1 ficheros", r.stdout)

    def test_enlace_sin_seguimiento_no_rompe_la_puerta(self):
        (self.repo / "enlace").symlink_to(self.repo / "src")
        r = self.puerta()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_config_externa_se_suma_a_la_del_proyecto(self):
        self.escribir(".agents/rutas-sensibles.txt", "src/nominas/*\n")
        self.escribir("src/nominas/calculo.py", "IRPF = 0\n")
        self.commit()
        self.escribir("src/nominas/calculo.py", "IRPF = 1\n")
        config = self.escribir("extra.txt", "otro/*\n", raiz=Path(self.tmp.name))
        r = self.puerta("--config", str(config))
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("src/nominas/*", r.stdout)

    def test_patrones_que_la_base_anade_despues_tambien_cuentan(self):
        self.escribir("src/nominas/calculo.py", "IRPF = 0\n")
        self.commit()
        self.git("branch", "base")
        self.git("switch", "-q", "-c", "rama")
        self.escribir("src/nominas/calculo.py", "IRPF = 1\n")
        self.commit()
        self.git("switch", "-q", "base")
        self.escribir(".agents/rutas-sensibles.txt", "src/nominas/*\n")  # la base declara la ruta tras bifurcarse
        self.commit()
        self.git("switch", "-q", "rama")
        r = self.puerta("--base", "base")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("src/nominas/*", r.stdout)

    def test_config_con_bom_o_en_cp1252_no_pierde_patrones(self):
        config = self.repo / ".agents" / "rutas-sensibles.txt"
        config.parent.mkdir()
        config.write_bytes(b"\xef\xbb\xbfsrc/nominas/*\n# N\xf3minas\n")
        self.escribir("src/nominas/calculo.py", "IRPF = 0\n")
        self.commit()
        self.escribir("src/nominas/calculo.py", "IRPF = 1\n")
        r = self.puerta()
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("(patrón «src/nominas/*»)", r.stdout)

    def test_clon_superficial_explica_el_error(self):
        self.git("branch", "base")
        self.git("switch", "-q", "-c", "rama")
        self.escribir("src/app.py", "print('adiós')\n")
        self.commit()
        self.git("switch", "-q", "base")
        self.escribir("src/otro.py", "x = 1\n")
        self.commit()
        clon = Path(self.tmp.name) / "clon"
        self.git("clone", "-q", "--depth", "1", "--branch", "rama", self.repo.as_uri(), str(clon))
        self.repo = clon
        self.git("fetch", "-q", "--depth", "1", "origin", "base:refs/remotes/origin/base")
        r = self.puerta("--base", "origin/base")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("superficial", r.stderr)

    def test_ruta_entrecomillada_se_informa_con_su_nombre_real(self):
        self.escribir('src/año "2026".py', "x = 0\n")
        self.commit()
        self.escribir('src/año "2026".py', "x = 0\ntoken = 1\n")
        r = self.puerta()
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn('contenido sensible: src/año "2026".py', r.stdout)
        self.assertIn("resumen: 1 ficheros", r.stdout)

    def test_salto_de_pagina_no_oculta_una_linea_anadida(self):
        self.escribir("src/app.py", "print('hola')\nx = 1\fpassword = 2\n")
        r = self.puerta()
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("contenido sensible: src/app.py", r.stdout)

    def test_muchas_lineas_anadidas_se_evaluan_en_tiempo_lineal(self):
        self.escribir("src/datos.txt", "")
        self.commit()
        self.escribir("src/datos.txt", "una línea de datos sin nada especial\n" * 100_000)
        inicio = time.monotonic()
        r = self.puerta("--max-lineas", "1000000")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertLess(time.monotonic() - inicio, 10)  # con concatenación cuadrática tardaba minutos


if __name__ == "__main__":
    unittest.main()
