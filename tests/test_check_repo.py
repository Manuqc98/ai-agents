"""Pruebas de tools/check-repo.py (solo biblioteca estándar).

Uso:
  python3 -m unittest discover tests
"""
import importlib.util
import unittest
from pathlib import Path

# El guion tiene un guion en el nombre: se carga por ruta en lugar de con import
_spec = importlib.util.spec_from_file_location("check_repo", Path(__file__).resolve().parents[1] / "tools" / "check-repo.py")
check_repo = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check_repo)

CONFIG = """default: google/gemini-3.1-pro

complejidad:
  media:      google/gemini-3.1-pro
  "complicada": "anthropic/claude-opus-5-5"

agentes:   # vacío = sin overrides
  # implementer: local/qwen3-coder-32b
  "security-reviewer": 'openai/gpt-6-astra'
"""


class ProveedorEfectivo(unittest.TestCase):
    def test_override_con_clave_y_valor_entrecomillados(self):
        self.assertEqual(check_repo.proveedor_efectivo(CONFIG, "security-reviewer", "complicada"), "openai")

    def test_override_comentado_no_cuenta(self):
        self.assertEqual(check_repo.proveedor_efectivo(CONFIG, "implementer", "media"), "google")

    def test_nivel_entrecomillado(self):
        self.assertEqual(check_repo.proveedor_efectivo(CONFIG, "architect", "complicada"), "anthropic")

    def test_sin_nivel_se_usa_default(self):
        self.assertEqual(check_repo.proveedor_efectivo(CONFIG, "architect", None), "google")


if __name__ == "__main__":
    unittest.main()
