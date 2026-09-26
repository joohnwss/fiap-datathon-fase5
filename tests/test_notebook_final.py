"""Contrato do notebook público sanitizado."""
from __future__ import annotations

import ast
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks" / "datathon_fase5.ipynb"
PUBLIC_JSON = ROOT / "reports" / "public" / "perguntas_oficiais_v1.json"


def _notebook() -> dict:
    return json.loads(NOTEBOOK.read_text(encoding="utf-8"))


def _fontes_codigo() -> list[str]:
    return [
        "".join(cell.get("source", []))
        for cell in _notebook()["cells"]
        if cell.get("cell_type") == "code"
    ]


def _texto_total() -> str:
    return json.dumps(_notebook(), ensure_ascii=False)


class NotebookPublicoTests(unittest.TestCase):
    def test_notebook_valido_e_sem_saidas_salvas(self):
        nb = _notebook()
        self.assertEqual(nb["nbformat"], 4)
        for cell in nb["cells"]:
            if cell.get("cell_type") == "code":
                self.assertEqual(cell.get("outputs", []), [])
                self.assertIsNone(cell.get("execution_count"))

    def test_le_exclusivamente_a_camada_publica(self):
        fontes = "\n".join(_fontes_codigo()).replace("\\", "/").lower()
        self.assertIn("reports/public", fontes.replace("' / '", "/"))
        self.assertIn("perguntas_oficiais_v1.json", fontes)
        self.assertIn("manifesto_integridade_v1.json", fontes)
        for proibido in (
            "metricas_analises_negocio.json",
            "relatorio_analises_negocio.md",
            "artifacts_meta.json",
            "data/processed",
            "datathon/",
            "local_data/",
            "local_recovery/",
        ):
            self.assertNotIn(proibido, fontes)

    def test_nao_treina_nem_recalibra_modelo(self):
        proibidos = {"fit", "fit_transform", "partial_fit", "cross_validate", "cross_val_score"}
        for fonte in _fontes_codigo():
            arvore = ast.parse(fonte)
            chamadas = {
                node.func.attr
                for node in ast.walk(arvore)
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            }
            self.assertEqual(chamadas & proibidos, set())

    def test_exibe_as_onze_perguntas_a_partir_do_json(self):
        payload = json.loads(PUBLIC_JSON.read_text(encoding="utf-8"))
        self.assertEqual(len(payload["perguntas"]), 11)
        self.assertEqual([q["numero"] for q in payload["perguntas"]], list(range(1, 12)))
        fontes = "\n".join(_fontes_codigo())
        self.assertIn("for q in DATA['perguntas']", fontes)
        self.assertIn("q['principais_numeros']", fontes)
        self.assertIn("q['grafico']", fontes)

    def test_verifica_todos_os_hashes_do_manifesto(self):
        fontes = "\n".join(_fontes_codigo())
        self.assertIn("MANIFEST['output_hashes'].items()", fontes)
        self.assertIn("assert all(checks.values())", fontes)

    def test_documenta_modelo_congelado_e_privacidade(self):
        texto = _texto_total().lower()
        self.assertIn("modelo permanece congelado", texto)
        self.assertIn("supressão complementar", texto)
        self.assertIn("não é exigência do enunciado", texto)

    def test_sem_identificadores_pessoais_ou_caminhos_absolutos(self):
        texto = _texto_total()
        self.assertNotRegex(texto, r"(?i)\b(?:ra|cpf|e-?mail|telefone)\b")
        self.assertNotRegex(texto, r"(?i)(?:[a-z]:[\\/]|/users/|/home/)")

    def test_sem_imagens_binarias_embutidas(self):
        texto = _texto_total()
        self.assertNotIn('"image/png"', texto)
        self.assertNotIn('"image/jpeg"', texto)


if __name__ == "__main__":
    unittest.main()
