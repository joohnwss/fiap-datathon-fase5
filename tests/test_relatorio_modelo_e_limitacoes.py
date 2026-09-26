"""Testes do documento autônomo "Modelo e limitações" (HTML/PDF).

A aba homônima saiu da navegação da aplicação (decisão de produto,
25/09/2026) — o conteúdo técnico não precisa ficar em primeiro plano na
ficha do dia a dia, mas continua útil como material de apoio para a
equipe (ex.: vídeo de apresentação do modelo). Este arquivo cobre a
cobertura que antes vivia em `tests/test_streamlit_app.py` para essa aba,
agora aplicada ao documento gerado por
`scripts/gerar_relatorio_modelo_e_limitacoes.py`.
"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import modelagem  # noqa: E402
import textos_aplicacao as textos  # noqa: E402
import scripts.gerar_relatorio_modelo_e_limitacoes as gerador  # noqa: E402


def _official_metrics() -> dict:
    return modelagem.read_json(ROOT / modelagem.METRICS)


class RelatorioModeloELimitacoesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contexto = gerador.inferencia.prepare_application(root=ROOT)
        cls.html = gerador.montar_html(cls.contexto)

    def test_ponto_operacional_e_o_numero_em_destaque_na_visao_simples(self):
        """A "Visão simples" precisa mostrar o recall/precisão do ponto
        OPERACIONAL (o que a aplicação realmente usa hoje), não os números
        do ponto original desatualizados — a confusão que motivou esta
        correção (25/09/2026)."""
        ponto_operacional = self.contexto.operational["metricas_temporais"]["ponto_operacional_adotado"]
        inicio = self.html.index("Visão simples")
        fim = self.html.index("Pontos de atenção: original e operacional")
        regiao = self.html[inicio:fim]
        self.assertIn(f"{round(ponto_operacional['precisao'] * 100)}%", regiao)
        self.assertIn(f"{round(ponto_operacional['recall'] * 100)}%", regiao)

    def test_metricas_batem_com_o_artefato_oficial_sem_hardcode(self):
        metricas = _official_metrics()
        precisao_original = metricas["temporal"]["metricas"]["precisao"]
        recall_original = metricas["temporal"]["metricas"]["recall"]
        self.assertIn(f"{precisao_original:.4f}", self.html)
        self.assertIn(f"{recall_original:.4f}", self.html)
        codigo_textos = (SRC / "textos_aplicacao.py").read_text(encoding="utf-8")
        self.assertNotIn(f"{precisao_original:.4f}", codigo_textos)
        self.assertNotIn(f"{recall_original:.4f}", codigo_textos)

    def test_ap_e_roc_auc_nao_tem_destaque_na_visao_principal(self):
        """AP/ROC-AUC só podem aparecer na seção "Detalhes técnicos", nunca
        na "Visão simples" nem na comparação dos dois pontos."""
        inicio = self.html.index("Visão simples")
        abertura_detalhes = self.html.index("<h2>Detalhes técnicos</h2>")
        regiao_antes = self.html[inicio:abertura_detalhes]
        self.assertNotIn("ROC-AUC", regiao_antes)
        self.assertNotRegex(regiao_antes, r"\bAP\b")

        regiao_depois = self.html[abertura_detalhes:]
        self.assertIn("ROC-AUC", regiao_depois)

    def test_tabela_de_traducao_de_termos_presente(self):
        for tecnico, simples in textos.TRADUCOES:
            with self.subTest(tecnico=tecnico):
                self.assertIn(simples, self.html)
                self.assertIn(tecnico, self.html)

    def test_ambos_os_pontos_de_atencao_presentes_com_valores_exatos(self):
        self.assertIn(f"{self.contexto.validation.threshold:.12f}", self.html)
        self.assertIn(
            f"{self.contexto.operational['ponto_atencao_operacional']['limiar']:.12f}", self.html)

    def test_sete_preditores_na_ordem_oficial(self):
        self.assertIn(", ".join(gerador.inferencia.FEATURES), self.html)

    def test_limitacoes_presentes(self):
        for limitacao in textos.LIMITACOES_MODELO:
            with self.subTest(limitacao=limitacao[:40]):
                self.assertIn(limitacao, self.html)

    def test_negrito_markdown_convertido_para_html(self):
        """`**texto**` nos textos internos precisa virar `<strong>`, não
        aparecer como asteriscos literais no documento renderizado."""
        self.assertNotIn("**", self.html)
        self.assertIn("<strong>", self.html)

    def test_documento_autocontido_sem_javascript_ou_url_externa(self):
        self.assertNotIn("<script", self.html.lower())
        self.assertNotRegex(self.html, r'src="https?://')
        self.assertNotRegex(self.html, r'href="https?://')

    def test_imagem_das_curvas_embutida_em_base64(self):
        if (ROOT / "reports" / "curvas_modelagem.png").is_file():
            self.assertIn("data:image/png;base64,", self.html)

    def test_gerar_produz_html_e_tenta_pdf_sem_lancar_excecao(self):
        gerador.gerar()
        self.assertTrue(gerador.OUT_HTML.is_file())

    def test_nao_altera_nenhum_artefato_oficial(self):
        import hashlib
        arquivos = (
            "artifacts/configuracao_congelada.json", "artifacts/schema_modelo.json",
            "artifacts/modelo_avaliado.joblib", "artifacts/avaliacao_temporal.json",
            "reports/metricas_modelagem.json", "config/ponto_atencao_operacional.json",
        )
        antes = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in arquivos}
        gerador.gerar()
        depois = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in arquivos}
        self.assertEqual(antes, depois)


class AbaRemovidaDaAplicacaoTests(unittest.TestCase):
    """Confirma que a remoção da aba foi completa e consistente."""

    def test_streamlit_app_nao_referencia_mais_a_funcao_removida(self):
        """A FUNÇÃO e a criação da aba (`st.tabs`) não podem mais existir —
        comentários explicativos que citam o nome histórico entre aspas
        (mesmo padrão já usado para documentar a renomeação anterior de
        "Sobre o modelo") são aceitáveis e não são o alvo desta checagem."""
        codigo = (ROOT / "streamlit_app.py").read_text(encoding="utf-8")
        self.assertNotIn("_tab_modelo_e_limitacoes", codigo)
        self.assertNotIn('tab_modelo', codigo)

    def test_main_cria_exatamente_quatro_abas(self):
        codigo = (ROOT / "streamlit_app.py").read_text(encoding="utf-8")
        match = re.search(r"st\.tabs\(\s*\[([^\]]+)\]", codigo)
        self.assertIsNotNone(match)
        rotulos = re.findall(r'"([^"]+)"', match.group(1))
        self.assertEqual(
            rotulos, ["Início", "Panorama e resultados", "Avaliar um caso", "Entenda os indicadores"])


if __name__ == "__main__":
    unittest.main()
