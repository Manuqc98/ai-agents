"""Pruebas de tools/risk-gate.py sobre repositorios git temporales (solo biblioteca estándar).

Uso:
  python3 -m unittest discover tests
"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "risk-gate.py"


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
        subprocess.run(["git", "-C", str(self.repo), *args], check=True, capture_output=True)

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

    def puerta(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--repo", str(self.repo), *args], capture_output=True, text=True
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


if __name__ == "__main__":
    unittest.main()
