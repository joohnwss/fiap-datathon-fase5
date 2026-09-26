"""Testes do módulo `src/graficos_publicos.py` (gráficos interativos do
painel "Panorama e resultados").

Cobre: (a) todas as 11 perguntas produzem ao menos uma figura Plotly válida
e serializável; (b) os valores plotados batem exatamente com os valores já
publicados em `pergunta["principais_numeros"]` — nenhum número é reescrito
manualmente no módulo de gráficos; (c) a paleta usada é exclusivamente a
paleta categórica/sequencial/status validada pela skill `dataviz`, nunca uma
cor arbitrária; (d) nenhuma dependência de dados privados ou históricos.
"""
from __future__ import annotations

import ast
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

import graficos_publicos as graficos  # noqa: E402
import narrativa_publica as narrativa  # noqa: E402

DATA_PATH = ROOT / "reports" / "public" / "perguntas_oficiais_v1.json"

_CORES_VALIDAS = frozenset(
    graficos.CATEGORICAL
    + graficos.SEQUENCIAL_AZUL
    + tuple(graficos.STATUS.values())
    + (graficos.GRID, graficos.INK_SECONDARY, graficos.INK_MUTED, graficos.SURFACE,
       "white", "#0b0b0b")
)


class GraficosPublicosTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
        cls.perguntas = {q["numero"]: q for q in cls.data["perguntas"]}

    def test_todas_as_onze_perguntas_produzem_figura_valida(self):
        for numero in range(1, 12):
            with self.subTest(numero=numero):
                figuras = graficos.graficos_interativos(numero, self.perguntas[numero])
                self.assertTrue(figuras)
                for figura in figuras:
                    # Levanta exceção se houver algo não serializável (NaN,
                    # tipo numpy não convertido, etc.) — mesmo princípio de
                    # "falha controlada" das demais camadas do projeto.
                    representacao = figura.to_json()
                    self.assertTrue(representacao)

    def test_q1_valores_plotados_batem_com_a_tabela_publicada(self):
        pergunta = self.perguntas[1]
        figura = graficos.graficos_interativos(1, pergunta)[0]
        # Para cada trace (uma por categoria), confere que cada par (ano,
        # contagem) plotado existe, com o MESMO valor, na tabela publicada.
        linhas_por_categoria: dict[str, dict[str, int]] = {}
        for linha in pergunta["principais_numeros"]:
            linhas_por_categoria.setdefault(linha["Categoria"], {})[linha["Ano"]] = linha["Contagem"]

        total_pontos_conferidos = 0
        for trace in figura.data:
            categoria = trace.name.casefold()
            tabela_da_categoria = {k.casefold(): v for k, v in linhas_por_categoria.get(
                next(c for c in linhas_por_categoria if c.casefold() == categoria), {}).items()}
            for ano, valor in zip(trace.x, trace.y):
                self.assertEqual(tabela_da_categoria[ano], valor,
                                 f"{categoria}/{ano}: gráfico={valor}, tabela={tabela_da_categoria[ano]}")
                total_pontos_conferidos += 1
        # 3+2+2+1 = 8 pontos publicados na tabela de Q1 (3 categorias em
        # 2022/2023 + 2 categorias agregadas em 2024).
        self.assertEqual(total_pontos_conferidos, len(pergunta["principais_numeros"]))

    def test_q9_tem_tres_graficos_incluindo_equidade_por_fase(self):
        pergunta = self.perguntas[9]
        figuras = graficos.graficos_interativos(9, pergunta)
        self.assertEqual(len(figuras), 3)
        grafico_equidade = figuras[2]
        linhas_esperadas = [r for r in pergunta["analises_complementares_numeros"]
                            if r.get("Recorte") == "Equidade por fase — teste temporal"
                            and isinstance(r.get("Recall"), (int, float))]
        self.assertEqual(len(grafico_equidade.data[0].y), len(linhas_esperadas))
        for valor_grafico, linha in zip(grafico_equidade.data[0].y, linhas_esperadas):
            self.assertAlmostEqual(valor_grafico, linha["Recall"])

    def test_q10_tem_dois_graficos_incluindo_ida_por_pedra_origem(self):
        pergunta = self.perguntas[10]
        figuras = graficos.graficos_interativos(10, pergunta)
        self.assertEqual(len(figuras), 2)
        grafico_pedra = figuras[1]
        total_pontos = sum(len(trace.y) for trace in grafico_pedra.data)
        linhas_esperadas = [r for r in pergunta["analises_complementares_numeros"]
                           if r.get("Recorte") == "Variação média de IDA por Pedra de origem"]
        self.assertEqual(total_pontos, len(linhas_esperadas))

    def test_q1_tem_tres_graficos_incluindo_media_ian_e_recorte_sexo(self):
        """Correção pós-auditoria comparativa (24/09/2026, rodada 3): Q1
        precisa de uma composição mínima de gráficos distintos — (1)
        composição anual já existente, (2) evolução da média anual do IAN
        nos três anos, (3) recorte por sexo (agregação binária
        sem/alguma defasagem, publicável nos três anos).

        Correção pontual (24/09/2026): a média de 2024 passou a ser
        publicada (arredondada a duas casas decimais), após auditoria de
        divulgação conjunta confirmar que o arredondamento não permite
        reconstruir de forma única a célula protegida (ver
        `test_auditoria_de_divulgacao_conjunta_entre_perguntas` e
        `test_q1_2024_publica_agregacao_sem_revelar_subcategorias` em
        `tests/test_privacidade_publicacao.py`)."""
        pergunta = self.perguntas[1]
        figuras = graficos.graficos_interativos(1, pergunta)
        self.assertEqual(len(figuras), 3)

        grafico_media = figuras[1]
        linhas_media = [r for r in pergunta["analises_complementares_numeros"]
                        if r.get("Recorte") == "Média anual do IAN"]
        self.assertEqual(len(grafico_media.data[0].x), len(linhas_media))
        # As três médias (2022, 2023, 2024) são publicadas; a de 2024 vem
        # arredondada a exatamente duas casas decimais.
        for linha in linhas_media:
            self.assertIsInstance(linha["Valor"], float)
        ano_2024 = next(r for r in linhas_media if r["Ano"] == "2024")
        self.assertEqual(ano_2024["Valor"], round(ano_2024["Valor"], 2))

        grafico_recorte = figuras[2]
        linhas_sexo = [r for r in pergunta["analises_complementares_numeros"]
                       if r.get("Recorte") == "Defasagem por sexo (sem/alguma defasagem)"]
        # As seis combinações sexo×ano (2022/2023/2024 × feminino/masculino)
        # devem estar todas publicadas, sem nenhuma suprimida.
        self.assertEqual(len(linhas_sexo), 6)
        self.assertEqual(len(grafico_recorte.data), 2)
        self.assertEqual(len(grafico_recorte.data[0].x), len(linhas_sexo))
        self.assertTrue(all("n=" in rotulo for rotulo in grafico_recorte.data[0].x))
        self.assertIn("Variação anual", grafico_recorte.data[0].hovertemplate)
        self.assertTrue(any("moderada e severa" in a.text for a in grafico_recorte.layout.annotations))
        self.assertEqual(grafico_recorte.layout.xaxis.tickangle, 0)
        self.assertGreaterEqual(grafico_recorte.layout.margin.b, 100)

    def test_evidencias_da_pergunta_1_correspondem_ao_grafico_no_mesmo_indice(self):
        """Regressão de um desalinhamento real encontrado por inspeção visual
        (correção pontual da média do IAN em 2024, 24/09/2026): a lista de
        evidências de `narrativa_publica` precisa estar na MESMA ordem que
        `graficos_publicos.graficos_interativos` — o título/leitura de cada
        bloco de evidência é exibido junto do gráfico de mesmo índice na
        interface, então um desalinhamento na lista mostra o texto errado ao
        lado do gráfico errado sem que nenhum teste estrutural (que só
        confere contagens) perceba. Aqui, cada evidência de Q1 precisa
        mencionar um número que só aparece no gráfico do mesmo índice."""
        pergunta = self.perguntas[1]
        figuras = graficos.graficos_interativos(1, pergunta)
        evidencias = narrativa.evidencias(1)
        self.assertEqual(len(figuras), len(evidencias))

        # Evidência 0 (composição anual): menciona "53,8%" (2024, sem
        # defasagem) — só aparece nos rótulos de texto do gráfico 0.
        textos_grafico_0 = [str(t) for trace in figuras[0].data for t in (trace.text or [])]
        self.assertTrue(any("53,8%" in t for t in textos_grafico_0))
        self.assertIn("53,8%", evidencias[0]["leitura"]["padrao"])

        # Evidência 1 (média anual do IAN): menciona "7,68" — só aparece no
        # gráfico 1 (média_ian), nunca no gráfico 0 (composição).
        textos_grafico_1 = [str(t) for trace in figuras[1].data for t in (trace.text or [])]
        self.assertTrue(any("7.68" in t or "7,68" in t for t in textos_grafico_1))
        self.assertFalse(any("7.68" in t or "7,68" in t for t in textos_grafico_0))
        self.assertIn("7,68", evidencias[1]["leitura"]["padrao"])

    def test_idade_nunca_aparece_como_exata_no_json_publico(self):
        """Correção pós-auditoria comparativa (24/09/2026, rodada 3, item 2):
        toda menção a idade/faixa etária calculada precisa vir qualificada
        como aproximada — nunca "faixa etária" sozinho, sem a qualificação."""
        import re
        texto = json.dumps(self.data, ensure_ascii=False)
        # Toda ocorrência de "faixa etária" deve ser seguida por "aproximada".
        for m in re.finditer(r"faixa etária(?! aproximada)", texto, flags=re.IGNORECASE):
            self.fail(f"'faixa etária' sem qualificação 'aproximada' em: ...{texto[max(0, m.start()-40):m.start()+60]}...")
        self.assertIn("faixa etária aproximada", texto)

    def test_q9_matriz_de_confusao_bate_com_eventos_e_falsos(self):
        pergunta = self.perguntas[9]
        figuras = graficos.graficos_interativos(9, pergunta)
        matriz = figuras[1]
        z = matriz.data[0].z
        linha_teste = next(r for r in pergunta["principais_numeros"]
                           if r["Avaliação"].startswith("Teste temporal"))
        total_esperado = linha_teste["n"]
        total_matriz = sum(sum(linha) for linha in z)
        self.assertEqual(total_matriz, total_esperado)
        self.assertEqual(z[0][1], linha_teste["Falsos positivos"])
        self.assertEqual(z[1][0], linha_teste["Falsos negativos"])

    def test_nenhum_numero_hardcoded_de_negocio_no_modulo_de_graficos(self):
        """Os `_grafico_qN` recebem `pergunta` como parâmetro e leem
        `principais_numeros`; nenhuma função pode conter um literal
        numérico de negócio (ex.: 0.492, 622, 46.2) diretamente no corpo —
        apenas os parâmetros de estilo (larguras, tamanhos de fonte, cores)
        são aceitáveis como literais."""
        codigo = (SRC / "graficos_publicos.py").read_text(encoding="utf-8")
        arvore = ast.parse(codigo)
        funcoes_de_grafico = [n for n in ast.walk(arvore)
                              if isinstance(n, ast.FunctionDef) and n.name.startswith("_grafico_q")]
        # 11 perguntas, mais funções extras para o segundo/terceiro gráfico:
        # Q1 (+2: média anual do IAN e recorte por sexo/faixa etária), Q6
        # (+1), Q7 (+1), Q9 (+2: matriz e equidade por fase), Q10 (+1: IDA
        # por Pedra de origem) -> 11 + 7 = 18 funções ao todo.
        self.assertEqual(len(funcoes_de_grafico), 18)
        for funcao in funcoes_de_grafico:
            argumentos = {a.arg for a in funcao.args.args}
            self.assertIn("pergunta", argumentos, f"{funcao.name} não recebe 'pergunta' como parâmetro")

    def test_cores_usadas_pertencem_a_paleta_validada(self):
        """Toda cor usada nos gráficos vem exclusivamente da paleta
        categórica/sequencial/status validada (skill `dataviz`) — nenhuma
        cor arbitrária foi introduzida linha a linha."""
        for numero in range(1, 12):
            figuras = graficos.graficos_interativos(numero, self.perguntas[numero])
            for figura in figuras:
                for trace in figura.data:
                    marker = getattr(trace, "marker", None)
                    cor = getattr(marker, "color", None) if marker else None
                    if cor is None:
                        continue
                    cores = cor if isinstance(cor, (list, tuple)) else [cor]
                    for c in cores:
                        with self.subTest(numero=numero, cor=c):
                            self.assertIn(c, _CORES_VALIDAS)

    def test_paleta_categorica_e_a_paleta_validada_da_skill_dataviz(self):
        """Regressão literal: a ordem e os hex da paleta categórica devem
        continuar exatamente os documentados em
        `references/palette.md` da skill `dataviz` (oito cores, ordem
        fixa) — nunca reordenados nem trocados por cores 'parecidas'."""
        self.assertEqual(graficos.CATEGORICAL, (
            "#2a78d6", "#eb6834", "#1baf7a", "#eda100",
            "#e87ba4", "#008300", "#4a3aa7", "#e34948",
        ))

    def test_nenhum_jargao_de_desenvolvimento_visivel_nos_graficos(self):
        """Refatoração editorial (24/09/2026): título, eixos, legendas,
        anotações e texto de cada trace são visíveis diretamente no gráfico
        (fora do alcance dos testes de texto do `AppTest`, que só veem o
        DOM do Streamlit, não o conteúdo interno de um `go.Figure` Plotly).
        Nenhum desses pontos pode conter jargão de desenvolvimento."""
        termos = ("célula", "partição", "payload", "artefato", "schema",
                 "caixa pequena", "implementado", "redundância com outra análise")
        for numero in range(1, 12):
            figuras = graficos.graficos_interativos(numero, self.perguntas[numero])
            for indice, figura in enumerate(figuras):
                textos_visiveis = [str(figura.layout.title.text or "")]
                if figura.layout.xaxis.title.text:
                    textos_visiveis.append(str(figura.layout.xaxis.title.text))
                if figura.layout.yaxis.title.text:
                    textos_visiveis.append(str(figura.layout.yaxis.title.text))
                for anotacao in figura.layout.annotations or ():
                    textos_visiveis.append(str(anotacao.text or ""))
                for trace in figura.data:
                    if getattr(trace, "name", None):
                        textos_visiveis.append(str(trace.name))
                    texto_trace = getattr(trace, "text", None)
                    if texto_trace is not None:
                        textos_visiveis.extend(str(t) for t in (texto_trace if isinstance(texto_trace, (list, tuple)) else [texto_trace]))
                texto_completo = " ".join(textos_visiveis).lower()
                for termo in termos:
                    with self.subTest(numero=numero, grafico=indice, termo=termo):
                        self.assertNotIn(termo.lower(), texto_completo)

    def test_modulo_nao_depende_de_dados_privados_ou_historicos(self):
        codigo = (SRC / "graficos_publicos.py").read_text(encoding="utf-8")
        for proibido in ("DATATHON", "local_data", "local_recovery",
                         "metricas_analises_negocio", "analises_negocio"):
            self.assertNotIn(proibido, codigo)
        arvore = ast.parse(codigo)
        importados = {n.names[0].name for n in ast.walk(arvore) if isinstance(n, ast.Import)}
        importados |= {n.module for n in ast.walk(arvore) if isinstance(n, ast.ImportFrom) and n.module}
        self.assertEqual(importados & {"streamlit", "requests", "httpx", "socket"}, set())


class AplicarTemaTests(unittest.TestCase):
    """`aplicar_tema` (revisão de identidade visual, 25/09/2026): fundo,
    grade e texto dos gráficos acompanham o modo claro/escuro — a paleta
    categórica (`CATEGORICAL`) nunca muda. Cada teste restaura o modo claro
    ao final (`addCleanup`): estas são variáveis de MÓDULO, compartilhadas
    com o resto do processo de testes (`_CORES_VALIDAS` acima é montado uma
    única vez, na importação, a partir dos valores em modo claro)."""

    def setUp(self):
        self.addCleanup(graficos.aplicar_tema, False)

    def test_modo_escuro_muda_fundo_grade_e_texto_sem_alterar_paleta_categorica(self):
        categorica_antes = graficos.CATEGORICAL
        superficie_clara = graficos.SURFACE
        graficos.aplicar_tema(True)
        self.assertNotEqual(graficos.SURFACE, superficie_clara)
        self.assertEqual(graficos._LAYOUT_BASE["paper_bgcolor"], graficos.SURFACE)
        self.assertEqual(graficos._LAYOUT_BASE["plot_bgcolor"], graficos.SURFACE)
        self.assertEqual(graficos.CATEGORICAL, categorica_antes)

    def test_modo_claro_restaura_valores_originais(self):
        superficie_clara = graficos.SURFACE
        grade_clara = graficos.GRID
        graficos.aplicar_tema(True)
        graficos.aplicar_tema(False)
        self.assertEqual(graficos.SURFACE, superficie_clara)
        self.assertEqual(graficos.GRID, grade_clara)

    def test_grafico_gerado_apos_aplicar_tema_escuro_usa_fundo_escuro(self):
        dados = json.loads(DATA_PATH.read_text(encoding="utf-8"))
        pergunta = next(p for p in dados["perguntas"] if p["numero"] == 1)
        graficos.aplicar_tema(True)
        fundo_escuro = graficos.SURFACE
        figuras = graficos.graficos_interativos(1, pergunta)
        self.assertTrue(figuras)
        self.assertEqual(figuras[0].layout.paper_bgcolor, fundo_escuro)


if __name__ == "__main__":
    unittest.main()
