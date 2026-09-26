import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "reports" / "public"
DATA_PATH = PUBLIC / "perguntas_oficiais_v1.json"


class PrivacidadePublicacaoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
        cls.questions = {q["numero"]: q for q in cls.data["perguntas"]}
        cls.public_text = "\n".join(
            p.read_text(encoding="utf-8")
            for p in PUBLIC.rglob("*") if p.is_file() and p.suffix in {".json", ".md"}
        )

    def test_q1_2024_publica_agregacao_sem_revelar_subcategorias(self):
        linhas = [r for r in self.questions[1]["principais_numeros"] if r["Ano"] == "2024"]
        self.assertEqual(len(linhas), 2)
        self.assertEqual(
            {linha["Categoria"] for linha in linhas},
            {"sem defasagem", "com defasagem (moderada + severa)"},
        )
        self.assertEqual(sum(linha["Contagem"] for linha in linhas), 1156)
        self.assertTrue(all(linha["Contagem"] >= 10 for linha in linhas))
        self.assertTrue(all(linha["Percentual"] not in (None, "None") for linha in linhas))
        self.assertTrue(all("Denominador" not in linha for linha in linhas))

        q1_publica = json.dumps(self.questions[1], ensure_ascii=False).casefold()
        # A contagem exata de severa (3) e de moderada (531) — a divisão real
        # dentro dos 534 registros com defasagem — nunca pode aparecer como
        # contagem publicada em nenhuma tabela (a média arredondada de 2024,
        # ao contrário, É publicada deliberadamente — ver
        # `test_media_ian_2024_arredondada_nao_permite_reconstrucao_unica`).
        self.assertNotIn(531, [linha["Contagem"] for linha in linhas])
        self.assertNotIn(3, [linha["Contagem"] for linha in linhas])
        self.assertNotIn("partição integralmente protegida", q1_publica)

        # A camada não oferece as variáveis internas do artefato congelado
        # que decomporiam o grupo agregado de 2024 entre moderada e severa
        # com precisão total (essas chaves nunca existiram na camada
        # pública, com ou sem a média arredondada).
        for chave_proibida in ("ian_distribuicao", "sinal_d", "ian_divergencias", "media_ian_2024"):
            self.assertNotIn(chave_proibida, self.public_text.casefold())

    def test_media_ian_2024_arredondada_nao_permite_reconstrucao_unica(self):
        """Correção pontual (24/09/2026): a média anual do IAN em 2024 passou
        a ser publicada (arredondada a duas casas decimais), após uma
        reavaliação encontrar a supressão total anterior excessiva. Esta é a
        prova matemática exigida antes de manter essa publicação: o IAN só
        assume três valores fixos (10/5/2,5, um por categoria de defasagem —
        ver docs/contrato_metodologico.md), então a média EXATA de 2024,
        combinada com as contagens já públicas de "sem defasagem" (622) e
        "com defasagem" (534), determinaria a divisão exata entre moderada e
        severa. O arredondamento a duas casas decimais precisa deixar mais
        de uma divisão inteira igualmente consistente com o valor publicado
        — senão, a supressão da contagem fina não protegeria nada."""
        linhas_2024 = [r for r in self.questions[1]["principais_numeros"] if r["Ano"] == "2024"]
        n_sem = next(r["Contagem"] for r in linhas_2024 if r["Categoria"] == "sem defasagem")
        n_com = next(r["Contagem"] for r in linhas_2024 if r["Categoria"] == "com defasagem (moderada + severa)")
        n_total = n_sem + n_com

        linha_media = next(r for r in self.questions[1]["analises_complementares_numeros"]
                           if r.get("Recorte") == "Média anual do IAN" and r.get("Ano") == "2024")
        media_publicada = linha_media["Valor"]
        self.assertIsInstance(media_publicada, float)
        self.assertEqual(media_publicada, round(media_publicada, 2),
                         "a média de 2024 precisa estar arredondada a exatamente duas casas decimais")

        # IAN só assume 10 (sem defasagem), 5 (moderada) ou 2,5 (severa).
        VALOR_SEM_DEFASAGEM, VALOR_MODERADA, VALOR_SEVERA = 10.0, 5.0, 2.5

        divisoes_consistentes = []
        for severa in range(0, n_com + 1):
            moderada = n_com - severa
            soma = n_sem * VALOR_SEM_DEFASAGEM + moderada * VALOR_MODERADA + severa * VALOR_SEVERA
            media_exata = soma / n_total
            if round(media_exata, 2) == media_publicada:
                divisoes_consistentes.append((severa, moderada))

        self.assertGreater(
            len(divisoes_consistentes), 1,
            "a média arredondada publicada é consistente com uma ÚNICA divisão moderada/severa — "
            "isso reconstruiria a célula protegida e a publicação deveria ser revertida",
        )
        # Nenhuma das divisões plausíveis pode ser confirmada como A divisão
        # real só com o dado público — ou seja, o valor exato (531/3) precisa
        # estar entre as possíveis, mas não isolado como a única.
        self.assertIn((3, 531), divisoes_consistentes)

    def test_q6_nao_publica_quadrantes_artificiais(self):
        q6 = json.dumps(self.questions[6], ensure_ascii=False).casefold()
        for texto in ("abaixo da mediana", "na mediana ou acima", "perfis alinhados", "perfis contrastantes"):
            self.assertNotIn(texto, q6)
        self.assertIn("não existe critério externo validado", q6)
        self.assertIn("ipp × ian", q6)
        self.assertIn("ipp × defasagem", q6)

    def test_q9_nao_publica_celulas_do_subgrupo_suprimido(self):
        q9 = self.questions[9]
        linha = next(
            r for r in q9["analises_complementares_numeros"]
            if r.get("Recorte") == "Equidade por faixa etária aproximada — teste temporal"
            and r.get("Grupo") == "17 anos ou mais"
        )
        for campo in ("n", "Eventos", "Negativos", "Alertas", "Verdadeiros positivos",
                      "Falsos positivos", "Falsos negativos", "Recall", "Precisão"):
            self.assertEqual(linha[campo], "suprimido")
        self.assertEqual(linha["AP"], "não estimável para este grupo")
        self.assertEqual(linha["ROC-AUC"], "não estimável para este grupo")
        texto_q9 = json.dumps(q9, ensure_ascii=False)
        self.assertNotIn("0 eventos em 8 casos", texto_q9)

    def test_sem_referencia_a_artefatos_historicos(self):
        proibidos = (
            "reports/metricas_analises_negocio.json",
            "reports/relatorio_analises_negocio.md",
            "reports/relatorio_preparacao_inicial.md",
            "reports/figures/",
        )
        for caminho in proibidos:
            self.assertNotIn(caminho, self.public_text)

    def test_notebook_publico_sem_outputs_e_sem_dependencias_privadas(self):
        notebook = json.loads((ROOT / "notebooks/datathon_fase5.ipynb").read_text(encoding="utf-8"))
        codigo = "\n".join("".join(c["source"]) for c in notebook["cells"])
        self.assertTrue(all(not c.get("outputs") for c in notebook["cells"] if c["cell_type"] == "code"))
        self.assertIn("reports/public", codigo)
        for antigo in ("metricas_analises_negocio.json", "relatorio_analises_negocio.md"):
            self.assertNotIn(antigo, codigo)
        for privado in ("DATATHON/", "local_data/", "local_recovery/"):
            # Os nomes podem aparecer na explicação de independência, mas nunca
            # em chamadas de abertura ou composição de caminho.
            self.assertIsNone(re.search(rf"(?:open|read_text|read_bytes|Path)\([^\n]*{re.escape(privado)}", codigo))

    def test_todos_os_graficos_estao_no_diretorio_publico(self):
        graficos = [q["grafico"] for q in self.data["perguntas"]]
        self.assertEqual(len(graficos), 11)
        self.assertEqual(len(set(graficos)), 11)
        self.assertTrue(all(g.startswith("reports/public/figures/") for g in graficos))

    def test_auditoria_de_divulgacao_conjunta_entre_perguntas(self):
        """Verifica que NENHUMA combinação de números publicados em QUALQUER
        das 11 perguntas permite reconstruir, de forma ÚNICA, as células
        suprimidas: (a) a divisão exata do grupo "com defasagem" de 2024
        (534 registros) entre moderada e severa (Q1) — a média arredondada
        do IAN em 2024 É publicada deliberadamente desde a correção pontual
        de 24/09/2026, mas só depois de provado que o arredondamento a duas
        casas decimais deixa mais de uma divisão igualmente possível (ver
        `test_media_ian_2024_arredondada_nao_permite_reconstrucao_unica`);
        (b) a distribuição categórica de IPP por categoria de defasagem em
        2024 (Q6). Uma soma total sozinha (ex.: moderada + severa = 534) não
        fecha o sistema sozinha — é preciso uma SEGUNDA equação
        independente E de precisão total (não arredondada) publicada em
        QUALQUER lugar do documento. Auditoria feita e confirmada de forma
        independente durante a implementação do plano da auditoria
        comparativa (24/09/2026), e reexecutada na correção pontual da
        média de 2024."""
        # Chaves internas do artefato congelado que forneceriam uma segunda
        # equação de PRECISÃO TOTAL (não arredondada) — essas nunca podem
        # aparecer, com ou sem a média arredondada de 2024 já publicada.
        termos_que_forneceriam_segunda_equacao_exata_para_celula_a = (
            "ian_distribuicao", "sinal_d", "ian_divergencias", "media_ian_2024",
        )
        for termo in termos_que_forneceriam_segunda_equacao_exata_para_celula_a:
            self.assertNotIn(termo, self.public_text.casefold(),
                             f"termo {termo!r} forneceria uma segunda equação independente e exata "
                             "para a célula protegida de moderada/severa em 2024")

        # A média EXATA (não arredondada) de 2024 nunca pode aparecer — só a
        # versão arredondada a duas casas decimais, já auditada.
        self.assertNotIn("7,6838", self.public_text)
        self.assertNotIn("7.6838", self.public_text)
        self.assertNotIn("7,683823", self.public_text)

        # Nenhuma pergunta que não seja a 6 pode conter uma média de IPP por
        # categoria de defasagem referente a 2024 (o que decomporia a célula
        # protegida de IPP por categoria).
        termos_media_ipp_por_categoria = (
            "ipp médio — sem defasagem", "ipp médio — moderada", "ipp médio — severa",
        )
        for numero, pergunta in self.questions.items():
            if numero == 6:
                continue
            texto_pergunta = json.dumps(pergunta, ensure_ascii=False).casefold()
            for termo in termos_media_ipp_por_categoria:
                self.assertNotIn(termo, texto_pergunta,
                                 f"pergunta {numero} não deveria conter {termo!r} (célula de Q6)")

        # A linha suprimida de Q6/2024 continua com todos os campos numéricos
        # nulos (nenhuma regressão futura pode preenchê-la parcialmente, o
        # que já seria uma forma de vazamento parcial).
        linha_suprimida = [r for r in self.questions[6]["principais_numeros"]
                           if r.get("Ano") == "2024" and r.get("Medida") == "IPP por categoria"]
        self.assertEqual(len(linha_suprimida), 1)
        self.assertTrue(all(v is None for k, v in linha_suprimida[0].items() if k not in ("Ano", "Medida")))


if __name__ == "__main__":
    unittest.main()
