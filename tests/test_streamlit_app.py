"""Regressão da TASK 010 (interface pública), da subetapa de aprimoramento
anterior à TASK 011 (cinco áreas, linguagem para professores e profissionais
da ONG, apoio ao acompanhamento educacional), da ETAPA B (storytelling e
painel "Panorama e resultados") e da revisão editorial de 25/09/2026 (ficha
de acompanhamento em "Avaliar um caso", com calculadoras de indicadores e
relatório individual — a aplicação voltou a cinco áreas após a remoção da
antiga aba independente "Plano de acompanhamento", integrada ao resultado).

Usa `streamlit.testing.v1.AppTest` para exercitar a aplicação sem abrir um
navegador nem um servidor de verdade (nenhuma rede, nenhum processo externo).
Cobre comportamento da interface, privacidade/segurança (por análise AST e
textual do próprio código-fonte, agora também sobre `src/textos_aplicacao.py`)
e portabilidade.

Nenhum teste aqui altera `artifacts/`, `reports/`, `docs/` ou qualquer
arquivo do repositório; os testes de portabilidade que usam diretórios
temporários limpam tudo via `addCleanup`, mesmo em caso de falha. Nenhum
dado privado é lido ou necessário.
"""
from __future__ import annotations

import ast
import importlib.util
import json
import math
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import tomllib
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))
import graficos_publicos as graficos  # noqa: E402
import inferencia as inf  # noqa: E402
import narrativa_publica as narrativa  # noqa: E402
import textos_aplicacao as textos  # noqa: E402

# Import plano entre testes irmãos (mesmo padrão já usado em
# tests/test_analises_negocio.py -> test_coortes_regressao.py); garante que
# funcione tanto com `unittest discover -s tests` quanto com
# `python -m unittest tests.test_streamlit_app` isoladamente.
TESTS_DIR = Path(__file__).resolve().parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))
from test_inferencia_aplicacao import official_threshold, operational_threshold  # noqa: E402
# Reaproveita os helpers que leem os limiares dos artefatos/configuração, em
# vez de duplicar os números aqui. O equivalente para métricas
# (`official_metrics`, abaixo) é definido localmente, seguindo o mesmo
# padrão de leitura direta dos artefatos.

import modelagem as _modelagem  # noqa: E402


def official_metrics() -> dict:
    """Lê `reports/metricas_modelagem.json` diretamente do artefato oficial
    — nunca duplica nenhum valor numérico neste arquivo de teste."""
    return _modelagem.read_json(ROOT / _modelagem.METRICS)

APP_PATH = ROOT / "streamlit_app.py"
TEXTOS_PATH = SRC / "textos_aplicacao.py"
CONFIG_PATH = ROOT / ".streamlit" / "config.toml"

# Decisão de gestão de 25/09/2026 (ponto de atenção operacional): a
# probabilidade deste payload (~7,4%) precisou ficar seguramente ABAIXO do
# novo ponto operacional (~15,1%) — um payload que só ficasse abaixo do
# antigo ponto (~26,7%) mudaria de classificação sob a regra atual. Ver
# PAYLOAD_ZONA_ENTRE_PONTOS abaixo para o caso intermediário proposital.
PAYLOAD_BAIXO_RISCO = {"ida": "9.5", "ieg": "9.9", "iaa": "9.8", "ips": "9.5", "ipv": "9.8",
                       "fase_origem": "5", "defasagem_origem": "0"}
PAYLOAD_ALTO_RISCO = {"ida": "2.0", "ieg": "2.0", "iaa": "2.0", "ips": "2.0", "ipv": "2.0",
                      "fase_origem": "3", "defasagem_origem": "-3"}
# Fica ENTRE os dois pontos de atenção (probabilidade ~16,4%: acima do novo
# ponto operacional ~15,1%, abaixo do ponto metodológico original ~26,7%) —
# o único caso em que a classificação muda dependendo de qual ponto é
# usado. Era o valor original de PAYLOAD_BAIXO_RISCO antes desta rodada;
# preservado aqui com esse papel, agora explícito.
PAYLOAD_ZONA_ENTRE_PONTOS = {"ida": "6.5", "ieg": "8.0", "iaa": "7.0", "ips": "5.0", "ipv": "7.5",
                             "fase_origem": "2", "defasagem_origem": "0"}

# Revisão de identidade visual (25/09/2026): os avisos de privacidade/uso
# responsável da Início deixaram de ser caixas `st.success`/`st.warning"
# permanentes — viraram texto discreto no formulário de "Avaliar um caso" e
# um resumo no rodapé (Etapa 1, item 4). A única `st.info` permanente é a de
# "Modelo e limitações" (`AVISO_FINALIDADE_EDUCACIONAL`), que não conta aqui
# porque os testes abaixo olham só `warning`/`success`. Os testes de
# classificação por limiar comparam a contagem total de sucesso/aviso contra
# esta base (agora 0), em vez de assumir "exatamente 1" no app inteiro.
_BASE_WARNING = 0
_BASE_SUCCESS = 0


def _by_key(elementos, key):
    for elemento in elementos:
        if elemento.key == key:
            return elemento
    raise KeyError(f"widget com key={key!r} não encontrado")


def _button(at, rotulo):
    for botao in at.button:
        if botao.label == rotulo or (
            rotulo == "Gerar estimativa" and botao.label == "Gerar estimativa e relatório"
        ):
            return botao
    raise KeyError(f"botão {rotulo!r} não encontrado")


def _preencher_e_enviar(at, payload):
    _preencher_campos_sem_enviar(at, payload)
    at.run(timeout=30)
    _button(at, "Gerar estimativa").click()
    at.run(timeout=30)
    return at


def _preencher_campos_sem_enviar(at, payload):
    _by_key(at.text_input, "campo_identificacao_caso").set_value("caso-teste")
    _by_key(at.text_input, "campo_idade_contexto").set_value("14")
    _by_key(at.selectbox, "campo_sexo_contexto").select("Feminino")
    for campo in ("ida", "ieg", "iaa", "ips", "ipv"):
        _by_key(at.text_input, f"campo_{campo}").set_value(payload[campo])
    _by_key(at.selectbox, "campo_fase_origem").select(payload["fase_origem"])
    at.run(timeout=30)
    fase_ideal = str(int(payload["fase_origem"]) - int(float(payload["defasagem_origem"])))
    _by_key(at.selectbox, "campo_fase_ideal_calculo").select(fase_ideal)
    _by_key(at.text_input, "campo_ipp_contexto").set_value("7")
    return at


def _novo_app() -> AppTest:
    at = AppTest.from_file(str(APP_PATH))
    at.run(timeout=30)
    return at


def _texto_total(at) -> str:
    """Concatena todo o texto visível renderizado (markdown, caption, info,
    success, warning, error, title, subheader, métrica, aba, expander) em uma
    única string, para buscas textuais de conteúdo editorial. `st.tabs`
    renderiza o conteúdo de TODAS as abas no mesmo script run (a seleção da
    aba ativa é só uma escolha visual do cliente), então este texto cobre as
    cinco áreas da aplicação simultaneamente. Deliberadamente NÃO inclui
    `at.dataframe`/`at.table` (conteúdo de tabelas): tabelas têm seus
    próprios testes dedicados de conteúdo (ex.:
    `test_nenhuma_tabela_exibe_none_cru`), e incluir células de tabela aqui
    ampliaria esta varredura textual genérica para dentro de dados
    analíticos já aprovados, fora do escopo desta função."""
    partes = []
    for colecao in (at.markdown, at.caption, at.info, at.success, at.warning,
                    at.error, at.title, at.subheader, at.tabs):
        partes.extend(str(getattr(e, "value", getattr(e, "label", ""))) for e in colecao)
    for m in at.metric:
        partes.append(str(m.value))
    for exp in at.expander:
        partes.append(str(exp.label))
        for filho in exp.markdown:
            partes.append(str(filho.value))
        for filho in exp.caption:
            partes.append(str(filho.value))
    return "\n".join(partes)


# --------------------------------------------------------------------------- #
# Comportamento da interface (AppTest)                                       #
# --------------------------------------------------------------------------- #

class AppTestBehaviorTests(unittest.TestCase):
    # -- estrutura geral (itens 1, 2, 22) ---------------------------------- #

    def test_aplicacao_inicia_sem_excecao(self):
        at = _novo_app()
        self.assertEqual(list(at.exception), [])

    def test_titulo_presente(self):
        """Revisão de identidade visual (25/09/2026): o `st.title` do
        cabeçalho é o nome da instituição ("Passos Mágicos", nunca uma marca
        concorrente inventada); a finalidade da ferramenta continua descrita
        logo abaixo, no subtítulo do projeto."""
        at = _novo_app()
        self.assertTrue(any("passos mágicos" in t.value.lower() for t in at.title))
        self.assertIn(textos.SUBTITULO_PROJETO, _texto_total(at))

    def test_todas_as_areas_presentes(self):
        """Cobertura geral de estrutura de abas (a contagem exata e os
        rótulos das quatro áreas são conferidos em detalhe por
        `PanoramaTests.test_item1_cinco_abas_com_rotulos_exatos`).

        "Modelo e limitações" foi removida da navegação (decisão de
        produto, 25/09/2026) — o conteúdo agora vive em documento à parte,
        ver `tests/test_relatorio_modelo_e_limitacoes.py`."""
        at = _novo_app()
        self.assertEqual(len(at.tabs), 4)
        rotulos = [t.label for t in at.tabs]
        self.assertEqual(rotulos, ["Início", "Panorama e resultados", "Avaliar um caso",
                                   "Entenda os indicadores"])

    def test_item2_fluxo_inicial_compreensivel(self):
        """Revisão de identidade visual (25/09/2026, item 12): abertura
        editorial (título + texto de apoio), contexto institucional, questão
        central em destaque de citação, três caminhos numerados e equipe —
        sem repetir o antigo painel de cartões "O que este trabalho entrega"/
        "Como explorar a aplicação", retirado nesta rodada."""
        texto = _texto_total(_novo_app())
        for trecho in (
            textos.TITULO_EDITORIAL_INICIO,
            textos.TEXTO_APOIO_INICIO,
            textos.CONTEXTO_DESAFIO,
            "Questão central",
            textos.QUESTAO_CENTRAL,
            "Três caminhos",
            "Equipe",
        ):
            with self.subTest(trecho=trecho):
                self.assertIn(trecho, texto)

        for titulo, descricao in textos.CAMINHOS_APLICACAO:
            with self.subTest(caminho=titulo):
                self.assertIn(titulo, texto)
                self.assertIn(descricao, texto)

        marcacoes = [str(item.value) for item in _novo_app().markdown]
        posicoes = [
            marcacoes.index(f"**{indice}. {titulo}**")
            for indice, (titulo, _) in enumerate(textos.CAMINHOS_APLICACAO, start=1)
        ]
        self.assertEqual(posicoes, sorted(posicoes))

    def test_item2_equipe_exata_sem_email_cargo_ou_ferramenta(self):
        nomes_esperados = (
            "Lucas de Oliveira Schroeder",
            "Izadora Rayana Bento Araujo",
            "Laura Rossati de Oliveira",
            "Victor Thiago Farias Santos",
            "Jônatas Williams Santos Silva",
        )
        self.assertEqual(textos.EQUIPE, nomes_esperados)
        texto_renderizado = _texto_total(_novo_app())
        bloco_equipe = "\n".join(textos.EQUIPE)
        self.assertNotIn("@", bloco_equipe)
        for nome in nomes_esperados:
            self.assertIn(nome, texto_renderizado)
        for termo in ("github", "linkedin", "cientista", "desenvolvedor", "analista"):
            self.assertNotIn(termo, bloco_equipe.lower())

    def test_configuracao_da_pagina_e_primeira_chamada_streamlit(self):
        arvore = ast.parse(APP_PATH.read_text(encoding="utf-8"))
        chamadas_streamlit = sorted(
            (
                no for no in ast.walk(arvore)
                if isinstance(no, ast.Call)
                and isinstance(no.func, ast.Attribute)
                and isinstance(no.func.value, ast.Name)
                and no.func.value.id == "st"
            ),
            key=lambda no: (no.lineno, no.col_offset),
        )
        primeira = chamadas_streamlit[0]
        self.assertEqual(primeira.func.attr, "set_page_config")
        argumentos = {kw.arg: ast.literal_eval(kw.value) for kw in primeira.keywords}
        self.assertEqual(
            argumentos,
            {
                "page_title": "Apoio ao acompanhamento educacional",
                "page_icon": "🎓",
                "layout": "wide",
            },
        )

    def test_item22_layout_usa_componentes_nativos_e_responsivos(self):
        """Usa `st.tabs`/`st.columns` (empilham automaticamente em telas
        estreitas), sem nenhuma largura fixa em pixels codificada em
        `streamlit_app.py` (o CSS local em `assets/styles/app.css` pode usar
        px normalmente — é lá que vive todo dimensionamento, não aqui).
        `unsafe_allow_html` só pode aparecer para injetar esse CSS estático
        (ver `test_nenhum_unsafe_allow_html`)."""
        codigo = APP_PATH.read_text(encoding="utf-8")
        self.assertIn("st.tabs(", codigo)
        self.assertIn("st.columns(", codigo)
        self.assertNotRegex(codigo, r"\d+\s*px")
        self.assertIn('layout="wide"', codigo)

    # -- formulário (itens 3, 4, 5) ----------------------------------------- #

    def test_exatamente_sete_entradas_preditoras(self):
        """A partir da ETAPA B, `at.selectbox` também inclui o seletor de
        pergunta do painel "Panorama e resultados"; a partir da revisão
        editorial de 25/09/2026, "Avaliar um caso" também tem campos de
        identificação/contexto e da calculadora de defasagem (não
        preditores) — por isso a contagem restringe-se às sete chaves
        `campo_<preditor>` oficiais."""
        at = _novo_app()
        chaves_oficiais = {f"campo_{c}" for c in inf.FEATURES}
        text_inputs_oficiais = [ti for ti in at.text_input if ti.key in chaves_oficiais]
        selectboxes_oficiais = [sb for sb in at.selectbox if sb.key in chaves_oficiais]
        self.assertEqual(len(text_inputs_oficiais) + len(selectboxes_oficiais), 6)
        chaves = {ti.key for ti in text_inputs_oficiais} | {sb.key for sb in selectboxes_oficiais}
        self.assertEqual(chaves, chaves_oficiais - {"campo_defasagem_origem"})

    def test_campos_numericos_comecam_vazios_mas_bloqueiam_conclusao(self):
        at = _novo_app()
        for campo in ("ida", "ieg", "iaa", "ips", "ipv"):
            with self.subTest(campo=campo):
                self.assertEqual(_by_key(at.text_input, f"campo_{campo}").value, "")
        self.assertTrue(_button(at, "Gerar estimativa").disabled)

    def test_fase_domain_e_o_dominio_oficial_apesar_do_rotulo_amigavel(self):
        """`.options` do AppTest reflete o RÓTULO exibido (via `format_func`),
        não o valor bruto. E como o seletor vive dentro de um `st.form`, o
        valor só é efetivamente lido pelo script após o envio (comportamento
        de "batching" do Streamlit) — por isso a verificação de domínio
        submete um payload completo para cada fase bruta oficial e confirma
        que ela chega intacta à inferência (sem exceção, com resultado)."""
        at = _novo_app()
        sb = _by_key(at.selectbox, "campo_fase_origem")
        self.assertEqual(len(sb.options), len(inf.PHASE_CATEGORIES) + 1)  # + opção vazia
        for fase in inf.PHASE_CATEGORIES:
            with self.subTest(fase=fase):
                at = _preencher_e_enviar(_novo_app(), dict(PAYLOAD_BAIXO_RISCO, fase_origem=fase))
                self.assertEqual(list(at.exception), [])
                self.assertEqual(len(at.metric), 1)

    def test_item3_nenhum_campo_pessoal_no_formulario(self):
        at = _novo_app()
        chaves = {ti.key for ti in at.text_input} | {sb.key for sb in at.selectbox}
        for chave in chaves:
            self.assertNotRegex(chave, r"(?i)\b(ra|nome|cpf|email|telefone)\b")

    def test_item4_definicoes_tem_fonte_documental_indicada(self):
        self.assertTrue(textos.FONTES_DOCUMENTAIS)
        for campo in inf.FEATURES:
            with self.subTest(campo=campo):
                info = textos.INDICADORES[campo]
                for chave in ("sigla", "nome_extenso", "definicao", "o_que_informar", "ausencia"):
                    self.assertTrue(info[chave].strip(), f"{campo}.{chave} vazio")
        texto = _texto_total(_novo_app())
        self.assertIn("Fontes documentais", texto)
        for fonte in textos.FONTES_DOCUMENTAIS:
            self.assertIn(fonte, texto)

    def test_item5_e_item24_botao_de_exemplo_sintetico_funciona(self):
        at = _novo_app()
        _button(at, "Preencher exemplo sintético").click()
        at.run(timeout=30)
        for campo in ("ida", "ieg", "iaa", "ips", "ipv"):
            self.assertNotEqual(_by_key(at.text_input, f"campo_{campo}").value, "")
        self.assertNotEqual(_by_key(at.selectbox, "campo_fase_origem").value, "")
        _button(at, "Gerar estimativa").click()
        at.run(timeout=30)
        self.assertEqual(list(at.exception), [])
        self.assertEqual(len(at.metric), 1)

    def test_nenhuma_predicao_automatica_durante_a_digitacao(self):
        """Preencher um campo, sem clicar em enviar, não deve produzir
        nenhuma métrica de resultado (a inferência só ocorre no submit do
        `st.form`)."""
        at = _novo_app()
        _by_key(at.text_input, "campo_ida").set_value("6.5")
        at.run(timeout=30)
        self.assertEqual(len(at.metric), 0)

    def test_botao_de_estimativa_existe(self):
        at = _novo_app()
        _button(at, "Gerar estimativa")  # não levanta KeyError

    # -- resultado (itens 6, 7, 8, 9) ---------------------------------------- #

    def test_envio_valido_produz_probabilidade_em_percentual(self):
        at = _preencher_e_enviar(_novo_app(), PAYLOAD_BAIXO_RISCO)
        self.assertEqual(list(at.exception), [])
        self.assertEqual(len(at.metric), 1)
        self.assertRegex(at.metric[0].value, r"^\d+([.,]\d+)?%$")

    def test_item6_resultado_acima_do_limiar(self):
        at = _preencher_e_enviar(_novo_app(), PAYLOAD_ALTO_RISCO)
        self.assertEqual(list(at.exception), [])
        # +1 warning do resultado; a aba "Início" contribui sua própria base
        # em toda renderização, então a contagem total é a base + 1.
        self.assertEqual(len(at.warning), _BASE_WARNING + 1)
        self.assertEqual(len(at.success), _BASE_SUCCESS)
        texto = _texto_total(at)
        self.assertIn(textos.TITULO_ACIMA_DO_PONTO, texto)
        self.assertIn(textos.TEXTO_ACIMA_DO_PONTO, texto)

    def test_item7_resultado_abaixo_do_limiar(self):
        at = _preencher_e_enviar(_novo_app(), PAYLOAD_BAIXO_RISCO)
        self.assertEqual(list(at.exception), [])
        self.assertEqual(len(at.success), _BASE_SUCCESS + 1)
        self.assertEqual(len(at.warning), _BASE_WARNING)
        texto = _texto_total(at)
        self.assertIn(textos.TITULO_ABAIXO_DO_PONTO, texto)
        self.assertIn(textos.TEXTO_ABAIXO_DO_PONTO, texto)

    def test_item8_mensagem_abaixo_nao_elimina_risco(self):
        for payload in (PAYLOAD_BAIXO_RISCO, PAYLOAD_ALTO_RISCO):
            with self.subTest(payload=payload):
                at = _preencher_e_enviar(_novo_app(), payload)
                texto = _texto_total(at).lower()
                self.assertIn("não elimina o risco", texto)

    def test_item9_ponto_de_atencao_carregado_do_artefato(self):
        """Decisão de gestão de 25/09/2026: a mensagem exibida usa o ponto
        de atenção OPERACIONAL (config/ponto_atencao_operacional.json), não
        mais o limiar metodológico original — este último permanece
        preservado, mas só aparece no documento gerado por
        `scripts/gerar_relatorio_modelo_e_limitacoes.py`."""
        at = _preencher_e_enviar(_novo_app(), PAYLOAD_BAIXO_RISCO)
        texto = _texto_total(at)
        limiar_operacional = operational_threshold()
        self.assertIn(f"aproximadamente {round(limiar_operacional * 100)}%", texto)
        self.assertNotEqual(round(limiar_operacional * 100), round(official_threshold() * 100))
        # o valor EXATO só aparece na camada técnica (expander), nunca fora dele
        self.assertNotRegex(texto, r"threshold\s*=\s*0\.\d{4,}")
        self.assertNotRegex(texto, r"classe\s*=\s*1\b")

    def test_saida_crua_nao_aparece_fora_da_camada_tecnica(self):
        codigo = APP_PATH.read_text(encoding="utf-8")
        # os únicos usos de `predict_proba`/valores brutos ficam em `src/inferencia.py`,
        # nunca em `streamlit_app.py` (a interface só usa o resultado já interpretado)
        self.assertNotIn("predict_proba", codigo)

    def test_barra_visual_com_texto_e_numero_acessivel(self):
        """`AppTest` (nesta versão do Streamlit) não expõe uma coleção
        dedicada para `st.progress`; a presença do componente e do parâmetro
        `text=` (rótulo acessível sobre a própria barra) é confirmada no
        código-fonte, e a indicação numérica textual complementar via
        `st.metric` é confirmada pela execução real."""
        codigo = APP_PATH.read_text(encoding="utf-8")
        self.assertRegex(codigo, r"st\.progress\([^)]*text=")
        at = _preencher_e_enviar(_novo_app(), PAYLOAD_BAIXO_RISCO)
        self.assertEqual(len(at.metric), 1)  # indicação numérica textual, não só a barra

    def test_nao_afirma_qual_indicador_causou_o_resultado(self):
        at = _preencher_e_enviar(_novo_app(), PAYLOAD_ALTO_RISCO)
        texto = _texto_total(at).lower()
        self.assertIn("combinação dos sete indicadores", texto)
        self.assertIn("não aponta qual indicador", texto)

    # -- próximos passos (itens 12, 13) -------------------------------------- #
    # Integrados ao resultado de "Avaliar um caso" (revisão editorial,
    # 25/09/2026, Parte 7) — só aparecem depois de uma estimativa válida, não
    # mais numa aba própria sempre visível.

    def test_item12_proximos_passos_presentes_apos_estimativa(self):
        at_alto = _preencher_e_enviar(_novo_app(), PAYLOAD_ALTO_RISCO)
        texto_alto = _texto_total(at_alto)
        self.assertIn("Próximos passos sugeridos", texto_alto)
        for passo in textos.PROTOCOLO_PROXIMOS_PASSOS:
            with self.subTest(passo=passo):
                self.assertIn(passo, texto_alto)

        at_baixo = _preencher_e_enviar(_novo_app(), PAYLOAD_BAIXO_RISCO)
        texto_baixo = _texto_total(at_baixo)
        self.assertIn(textos.ORIENTACAO_PRIORIDADE_ABAIXO, texto_baixo)

    def test_item13_proximos_passos_sao_orientacao_geral(self):
        at = _preencher_e_enviar(_novo_app(), PAYLOAD_ALTO_RISCO)
        texto = _texto_total(at)
        self.assertIn(textos.AVISO_DECISAO_PROFISSIONAIS, texto)
        self.assertNotIn(textos.PROTOCOLO_PROXIMOS_PASSOS[0], _texto_total(_novo_app()))

    def test_ausencia_de_punicao_exclusao_ou_decisao_automatica(self):
        """"decisão automática" só pode aparecer na forma negada exigida
        pela revisão de identidade visual (25/09/2026, Etapa 1, item 4:
        `textos.AVISO_USO_RESPONSAVEL_CURTO`, "...não representa diagnóstico
        nem decisão automática.") — nunca endossando uma decisão automática
        de verdade. Por isso a ocorrência conhecida e seguramente negada é
        removida do texto antes da checagem de ausência."""
        texto = _texto_total(_novo_app()).lower()
        texto_sem_negacao_conhecida = texto.replace("nem decisão automática", "")
        for termo in ("punição", "punir", "excluir o aluno", "exclusão do aluno", "decisão automática"):
            self.assertNotIn(termo, texto_sem_negacao_conhecida)

    # -- indicadores (item 4 revisitado) ------------------------------------- #

    def test_dicionario_dos_indicadores_completo(self):
        at = _novo_app()
        rotulos_expander = {e.label for e in at.expander}
        for campo in inf.FEATURES:
            info = textos.INDICADORES[campo]
            with self.subTest(campo=campo):
                self.assertIn(f"{info['sigla']} — {info['nome_extenso']}", rotulos_expander)

    def test_explicacao_de_defasagem_presente(self):
        texto = _texto_total(_novo_app()).lower()
        self.assertIn("o que é \"defasagem\"", texto)

    # -- métricas e tradução (itens 10, 11) ----------------------------------- #

    def test_item11_traducao_correta_de_precisao_e_recall(self):
        """`frase_precisao`/`frase_recall` são funções puras — não dependem
        de nenhuma aba da aplicação. A verificação de que os números
        exibidos batem com os artefatos oficiais, a ausência de valores
        hardcoded e a separação de AP/ROC-AUC da visão simples migraram
        para `tests/test_relatorio_modelo_e_limitacoes.py` junto com o
        conteúdo (decisão de produto, 25/09/2026: "Modelo e limitações"
        saiu da navegação da aplicação)."""
        frase_p = textos.frase_precisao(0.64)
        frase_r = textos.frase_recall(0.40)
        self.assertIn("64%", frase_p)
        self.assertIn("cerca de 6", frase_p)
        self.assertIn("40%", frase_r)
        self.assertIn("aproximadamente 4", frase_r)

    # -- ausência de causalidade, diagnóstico e promessas (itens 14, 15) ----- #

    def test_linguagem_nao_causal(self):
        """O aviso de não causalidade acompanha o resultado (seção
        "Resultado" do enunciado); por isso o texto só existe após um envio
        — verificado aqui, em vez de na tela inicial sem interação."""
        at = _preencher_e_enviar(_novo_app(), PAYLOAD_BAIXO_RISCO)
        texto = _texto_total(at).lower()
        self.assertIn("causa e efeito", texto)
        self.assertIn("não é uma relação de causa e efeito", texto)

    def test_item15_ausencia_de_diagnostico_e_promessas(self):
        """A garantia de "não é diagnóstico" precisa estar sempre visível,
        sem precisar de nenhum envio — antes vinha da aba "Modelo e
        limitações" (removida, 25/09/2026); hoje é o rodapé
        (`AVISO_USO_RESPONSAVEL_CURTO`), com formulação equivalente
        ("não representa diagnóstico")."""
        texto = _texto_total(_novo_app()).lower()
        self.assertIn("não representa diagnóstico", texto)
        for termo in ("sem risco algum", "risco zero", "garantido", "garantia de",
                      "com certeza", "sempre vai", "nunca vai entrar em defasagem"):
            self.assertNotIn(termo, texto)

    def test_supervisao_humana_presente(self):
        at = _preencher_e_enviar(_novo_app(), PAYLOAD_BAIXO_RISCO)
        texto = _texto_total(at).lower()
        self.assertIn("revisado por uma equipe pedagógica", texto)

    # -- classificação binária, sem faixas arbitrárias (itens 12/13 do enunciado, restrições 12/13) #

    def test_ausencia_de_faixas_de_risco_baixo_medio_alto(self):
        codigo = APP_PATH.read_text(encoding="utf-8") + TEXTOS_PATH.read_text(encoding="utf-8")
        for termo in ("risco baixo", "risco médio", "risco alto", "baixo risco", "médio risco", "alto risco"):
            self.assertNotIn(termo.lower(), codigo.lower())

    def test_classificacao_permanece_binaria(self):
        """Exatamente UM novo alerta de resultado surge por envio (além da
        base fixa da aba "Início"): nunca uma terceira categoria/faixa."""
        base_total = _BASE_WARNING + _BASE_SUCCESS
        at_baixo = _preencher_e_enviar(_novo_app(), PAYLOAD_BAIXO_RISCO)
        at_alto = _preencher_e_enviar(_novo_app(), PAYLOAD_ALTO_RISCO)
        self.assertEqual(len(at_baixo.success) + len(at_baixo.warning), base_total + 1)
        self.assertEqual(len(at_alto.success) + len(at_alto.warning), base_total + 1)

    # -- item 25: classificação idêntica à inferência oficial ---------------- #

    def test_item25_classificacao_identica_a_inferencia_oficial(self):
        contexto = inf.prepare_application(root=ROOT)
        for payload in (PAYLOAD_BAIXO_RISCO, PAYLOAD_ALTO_RISCO):
            with self.subTest(payload=payload):
                esperado = inf.run_inference(contexto, payload)
                at = _preencher_e_enviar(_novo_app(), payload)
                metrica_exibida = at.metric[0].value  # ex.: "62.3%"
                percentual_exibido = float(metrica_exibida.rstrip("%").replace(",", "."))
                self.assertAlmostEqual(percentual_exibido, esperado.probability * 100, places=1)
                self.assertEqual(len(at.warning) == _BASE_WARNING + 1, esperado.is_risk)
                self.assertEqual(len(at.success) == _BASE_SUCCESS + 1, not esperado.is_risk)

    # -- erros de entrada (mantidos da TASK 010) ------------------------------ #

    def test_envio_com_campos_numericos_vazios_e_bloqueado(self):
        at = _novo_app()
        _by_key(at.selectbox, "campo_fase_origem").select("2")
        at.run(timeout=30)
        self.assertEqual(list(at.exception), [])
        self.assertTrue(_button(at, "Gerar estimativa").disabled)
        self.assertEqual(len(at.metric), 0)

    def test_texto_invalido_apresenta_mensagem_controlada(self):
        at = _novo_app()
        payload = dict(PAYLOAD_BAIXO_RISCO, ida="abc")
        _preencher_campos_sem_enviar(at, payload)
        at.run(timeout=30)
        self.assertEqual(list(at.exception), [])
        self.assertTrue(_button(at, "Gerar estimativa").disabled)

    def test_nan_apresenta_mensagem_controlada(self):
        at = _novo_app()
        _preencher_campos_sem_enviar(at, dict(PAYLOAD_BAIXO_RISCO, ida="NaN"))
        at.run(timeout=30)
        self.assertEqual(list(at.exception), [])
        self.assertTrue(_button(at, "Gerar estimativa").disabled)

    def test_infinito_apresenta_mensagem_controlada(self):
        at = _novo_app()
        _preencher_campos_sem_enviar(at, dict(PAYLOAD_BAIXO_RISCO, ida="inf"))
        at.run(timeout=30)
        self.assertEqual(list(at.exception), [])
        self.assertTrue(_button(at, "Gerar estimativa").disabled)

    def test_nenhuma_excecao_em_nenhum_dos_cenarios(self):
        cenarios = [
            PAYLOAD_BAIXO_RISCO,
            PAYLOAD_ALTO_RISCO,
            dict(PAYLOAD_BAIXO_RISCO, ida=""),
            dict(PAYLOAD_BAIXO_RISCO, ida="abc"),
            dict(PAYLOAD_BAIXO_RISCO, ida="NaN"),
            dict(PAYLOAD_BAIXO_RISCO, ida="inf"),
            dict(PAYLOAD_BAIXO_RISCO, ida="-inf"),
        ]
        for payload in cenarios:
            with self.subTest(payload=payload):
                at = _novo_app()
                _preencher_campos_sem_enviar(at, payload)
                at.run(timeout=30)
                self.assertEqual(list(at.exception), [])


# --------------------------------------------------------------------------- #
# Panorama e resultados (ETAPA B)                                            #
# --------------------------------------------------------------------------- #

def _selectbox_de_pergunta(at):
    candidatos = [sb for sb in at.selectbox if sb.key and sb.key.startswith("panorama_pergunta")]
    if not candidatos:
        raise KeyError("selectbox de pergunta do panorama não encontrado")
    return candidatos[0]


def _selecionar_pergunta(at, numero):
    sb = _selectbox_de_pergunta(at)
    sb.set_value(numero)
    at.run(timeout=30)
    return at


def _capitulo_exibido(at) -> str:
    capitulos = [str(item.value) for item in at.caption
                 if str(item.value).startswith("Capítulo: ")]
    if len(capitulos) != 1:
        raise AssertionError(f"esperado um capítulo atual, encontrados: {capitulos}")
    return capitulos[0]


def _contador_exibido(at, numero: int) -> bool:
    esperado = f"**Pergunta {numero} de 11**"
    return any(str(item.value) == esperado for item in at.markdown)


def _capitulo_esperado(numero: int) -> str:
    return next(capitulo for capitulo, numeros in textos.CAPITULOS if numero in numeros)


# --------------------------------------------------------------------------- #
# Execução da aplicação completa em processo isolado (correção item 3/6)    #
#                                                                             #
# `AppTest.from_file` roda no MESMO processo Python do restante da suíte;   #
# um teste anterior que redirecionava `inferencia.find_project_root` e      #
# limpava o cache `st.cache_resource` de `_carregar_aplicacao`/             #
# `_carregar_metricas_negocio` no meio da suíte corrompeu estado global do  #
# Streamlit e quebrou testes vizinhos. Os helpers abaixo, em vez disso,     #
# montam uma cópia pública isolada em disco (todo `src/`, `streamlit_app.py`#
# e os artefatos necessários) e a executam em um PROCESSO FILHO totalmente #
# separado — nenhum monkeypatch, nenhum cache compartilhado com os demais  #
# testes, e o código roda exatamente como em produção.                     #
# --------------------------------------------------------------------------- #

def _remover_mesmo_se_somente_leitura(funcao, caminho, exc_info):
    """`onerror` de `shutil.rmtree`: a causa raiz (identificada durante esta
    correção, via `icacls`/`Get-Item -Force`) de um diretório temporário
    residual é o atributo "somente leitura" do Windows presente em
    `src/` (dentro do OneDrive, raiz deste projeto) — `shutil.copytree`
    preserva atributos de arquivo por padrão (`copy2`), então a cópia em
    `tmp` herda esse atributo, e ele bloqueia a remoção normal (WinError 5:
    acesso negado). Remove o atributo e tenta de novo."""
    try:
        os.chmod(caminho, stat.S_IWRITE)
        funcao(caminho)
    except OSError:
        pass  # melhor esforço aqui; `_limpar_copia_publica_isolada_com_retentativas` decide se tenta de novo


def _limpar_copia_publica_isolada_com_retentativas(tmp: Path) -> None:
    """Remove `tmp` com novas tentativas, limpando o atributo somente
    leitura (ver `_remover_mesmo_se_somente_leitura`) a cada uma. Sem isso,
    o diretório temporário ficava residual (`WinError 5`) mesmo após o
    processo filho de `_rodar_driver_em_subprocesso` já ter terminado."""
    for _tentativa in range(10):
        shutil.rmtree(tmp, onerror=_remover_mesmo_se_somente_leitura)
        if not tmp.exists():
            return
        time.sleep(0.3)
    shutil.rmtree(tmp, ignore_errors=True)  # última tentativa, sem engolir eventual falha residual acima


def _montar_copia_publica_isolada(tmp: Path, *, grafico_a_corromper: str | None = None) -> None:
    """Monta em `tmp` uma cópia isolada e completa da aplicação pública:
    todo `src/`, `streamlit_app.py`, os artefatos exigidos por
    `inf.PUBLIC_REQUIRED_PATHS`, o painel de métricas de negócio e os dez
    gráficos oficiais, mais um marcador mínimo de `docs/TASKS.md` (único
    conteúdo de `docs/` exigido por `inferencia.find_project_root` quando a
    raiz não é passada explicitamente — o conteúdo real de `docs/TASKS.md`
    não é copiado nem necessário, só sua existência como marcador).

    Se `grafico_a_corromper` for informado (um dos caminhos de
    `textos.PERGUNTAS_NEGOCIO_GRAFICOS`), o conteúdo desse arquivo é
    substituído por bytes que não correspondem a nenhum hash oficial
    registrado, para exercitar o caminho real de erro controlado."""
    # `ignore=...__pycache__` evita copiar o cache de bytecode do `src/`
    # real (já populado pelas dezenas de outros testes desta suíte que
    # importam `inferencia`/`textos_aplicacao` normalmente) para dentro da
    # cópia isolada. `copy_function=shutil.copy` (em vez do padrão
    # `copy2`) evita propagar atributos de arquivo do Windows — a raiz do
    # projeto vive dentro do OneDrive, que por vezes marca arquivos como
    # "somente leitura"; herdar esse atributo na cópia temporária bloqueava
    # sua própria remoção depois (ver `_remover_mesmo_se_somente_leitura`,
    # mantido como segunda camada de proteção).
    shutil.copytree(SRC, tmp / "src", ignore=shutil.ignore_patterns("__pycache__"),
                    copy_function=shutil.copy)
    # `shutil.copy` (não `copy2`) em todos os arquivos abaixo, pelo mesmo
    # motivo: evitar herdar o atributo somente-leitura do OneDrive.
    shutil.copy(APP_PATH, tmp / "streamlit_app.py")
    for relativo in inf.PUBLIC_REQUIRED_PATHS:
        destino = tmp / relativo
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / relativo, destino)
    for relativo in (
        "reports/public/perguntas_oficiais_v1.json",
        "reports/public/manifesto_integridade_v1.json",
        "reports/curvas_modelagem.png",
        *textos.PERGUNTAS_NEGOCIO_GRAFICOS,
    ):
        destino = tmp / relativo
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / relativo, destino)
    (tmp / "docs").mkdir(parents=True, exist_ok=True)
    marcador = tmp / "docs" / "TASKS.md"
    if not marcador.exists():
        marcador.write_text(
            "Marcador mínimo para inferencia.find_project_root nesta cópia de teste "
            "isolada — não é o TASKS.md real do projeto.", encoding="utf-8")
    if grafico_a_corromper is not None:
        (tmp / grafico_a_corromper).write_bytes(
            b"conteudo adulterado, nao corresponde ao hash oficial registrado")


_DRIVER_ERRO_CONTROLADO = """
import json, sys
from streamlit.testing.v1 import AppTest

at = AppTest.from_file(sys.argv[1])
at.run(timeout=30)

textos_visiveis = []
for colecao in (at.markdown, at.caption, at.info, at.success, at.warning, at.error):
    textos_visiveis.extend(str(getattr(e, "value", "")) for e in colecao)

resultado = {
    "excecoes": [str(e) for e in at.exception],
    "erros": [e.value for e in at.error],
    "texto_total": textos_visiveis,
}
print(json.dumps(resultado))
"""

_DRIVER_APP_COMPLETA = """
import json, sys
from streamlit.testing.v1 import AppTest

at = AppTest.from_file(sys.argv[1])
at.run(timeout=30)

abas = [t.label for t in at.tabs]
# A partir da refatoração editorial (24/09/2026), o painel "Panorama e
# resultados" não exibe mais nenhum PNG histórico (só os gráficos Plotly
# interativos). A partir da revisão de identidade visual (25/09/2026), o
# logo oficial no cabeçalho é a única imagem permanente da aplicação — a
# curva agregada que antes vivia em "Modelo e limitações" > "Detalhes
# técnicos" saiu da aplicação junto com a aba (decisão de produto,
# 25/09/2026: ver reports/relatorio_modelo_e_limitacoes.html).
total_imagens = len(at.image)

for botao in at.button:
    if botao.label == "Preencher exemplo sintético":
        botao.click()
        break
at.run(timeout=30)
for botao in at.button:
    if botao.label == "Gerar estimativa e relatório":
        botao.click()
        break
at.run(timeout=30)

resultado = {
    "excecoes": [str(e) for e in at.exception],
    "abas": abas,
    "total_imagens": total_imagens,
    "metricas": [m.value for m in at.metric],
    "sucessos": len(at.success),
    "avisos": len(at.warning),
}
print(json.dumps(resultado))
"""

_DRIVER_CSS_E_TEMA = """
import json, sys
from streamlit.testing.v1 import AppTest

at = AppTest.from_file(sys.argv[1])
at.run(timeout=30)

textos_markdown = [str(e.value) for e in at.markdown]
css_presente = any("<style>" in t and "st-key-panorama_resumo_" in t for t in textos_markdown)
css_nao_vazio = any("<style>" in t and len(t) > len("<style></style>") + 200 for t in textos_markdown)

resultado = {
    "excecoes": [str(e) for e in at.exception],
    "css_presente": css_presente,
    "css_nao_vazio": css_nao_vazio,
}
print(json.dumps(resultado))
"""


def _rodar_driver_em_subprocesso(caso: unittest.TestCase, tmp: Path, conteudo_driver: str,
                                  *, cwd: Path | None = None) -> dict:
    """Grava `conteudo_driver` como um script em `tmp`, executa
    `streamlit_app.py` (copiado em `tmp` por `_montar_copia_publica_isolada`)
    em um processo Python filho totalmente separado (mesmo interpretador do
    venv usado para rodar os testes, via `sys.executable`) e devolve o
    resultado (JSON, sem `ensure_ascii=False`, imune a problemas de
    codificação do console) já decodificado. `cwd` permite rodar o processo
    filho a partir de um diretório de trabalho diferente da própria cópia
    (item 13 da correção) — a resolução da raiz depende só de `__file__`,
    nunca do diretório de trabalho atual.

    `PYTHONDONTWRITEBYTECODE=1` evita que o processo filho grave `.pyc` em
    `tmp/src/__pycache__/`: sem isso, o Windows por vezes mantém um lock
    breve nesses arquivos recém-criados (ex.: verificação de antivírus) e
    `shutil.rmtree(..., ignore_errors=True)` no `addCleanup` do teste falha
    silenciosamente, deixando diretório temporário residual — encontrado e
    corrigido durante esta própria correção."""
    driver = tmp / "_driver_apptest.py"
    driver.write_text(conteudo_driver, encoding="utf-8")
    ambiente = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    processo = subprocess.run(
        [sys.executable, str(driver), str(tmp / "streamlit_app.py")],
        cwd=str(cwd) if cwd is not None else str(tmp),
        capture_output=True, text=True, timeout=180, env=ambiente,
    )
    caso.assertEqual(processo.returncode, 0,
                     f"processo filho falhou (código {processo.returncode}):\n{processo.stderr}")
    ultima_linha = processo.stdout.strip().splitlines()[-1]
    return json.loads(ultima_linha)


class PanoramaTests(unittest.TestCase):
    """Cobre a aba "Panorama e resultados" (ETAPA B): quatro abas, quatro
    capítulos, onze perguntas, dez gráficos oficiais, carregamento a partir
    de `reports/metricas_analises_negocio.json` sem duplicação manual de
    número, navegação por capítulo/pergunta, e erro controlado para gráfico
    ausente ou divergente."""

    @classmethod
    def setUpClass(cls):
        cls.metricas_reais = json.loads(
            (ROOT / "reports" / "metricas_analises_negocio.json").read_text(encoding="utf-8"))
        cls.analises = cls.metricas_reais["analises"]
        cls.modelo = cls.metricas_reais["modelo"]
        cls.publico = json.loads(
            (ROOT / "reports" / "public" / "perguntas_oficiais_v1.json").read_text(
                encoding="utf-8"
            )
        )
        cls.perguntas_publicas = {
            int(item["numero"]): item for item in cls.publico["perguntas"]
        }

    # -- item 1: quatro abas ---------------------------------------------------

    def test_item1_cinco_abas_com_rotulos_exatos(self):
        """Nome do teste preservado por rastreabilidade histórica (a
        contagem real é quatro desde a remoção de "Modelo e limitações" da
        navegação, 25/09/2026)."""
        at = _novo_app()
        self.assertEqual(
            [t.label for t in at.tabs],
            ["Início", "Panorama e resultados", "Avaliar um caso", "Entenda os indicadores"],
        )

    # -- itens 2, 3, 4: capítulos, perguntas e mapeamento --------------------

    def test_item2_quatro_capitulos(self):
        self.assertEqual(len(textos.CAPITULOS), 4)
        rotulos = [c for c, _ in textos.CAPITULOS]
        self.assertEqual(len(rotulos), len(set(rotulos)))  # sem duplicatas

    def test_item3_onze_perguntas(self):
        self.assertEqual(len(textos.PERGUNTAS_NEGOCIO), 11)
        numeros = sorted(item["numero"] for item in textos.PERGUNTAS_NEGOCIO)
        self.assertEqual(numeros, list(range(1, 12)))
        self.assertEqual(
            [item["numero"] for item in self.publico["perguntas"]],
            list(range(1, 12)),
        )

        relatorio = (ROOT / "reports" / "public" / "relatorio_perguntas_oficiais_v1.md").read_text(
            encoding="utf-8"
        )
        titulos_relatorio = []
        for numero in range(1, 12):
            prefixo = f"## Pergunta {numero} — "
            linhas = [linha for linha in relatorio.splitlines() if linha.startswith(prefixo)]
            self.assertEqual(len(linhas), 1, f"pergunta {numero} ausente ou duplicada no relatório")
            titulos_relatorio.append(linhas[0].removeprefix(prefixo))
        self.assertEqual(
            titulos_relatorio,
            [item["pergunta"] for item in textos.PERGUNTAS_NEGOCIO],
        )

    def test_item4_mapeamento_exato_perguntas_para_capitulos(self):
        esperado = {
            "Trajetória e defasagem": (1, 10, 11),
            "Aprendizagem e engajamento": (2, 3),
            "Dimensões psicossociais e psicopedagógicas": (4, 5, 6),
            "Indicadores globais, risco e prioridades": (7, 8, 9),
        }
        self.assertEqual(dict(textos.CAPITULOS), esperado)
        todos_os_numeros = sorted(n for _, numeros in textos.CAPITULOS for n in numeros)
        self.assertEqual(todos_os_numeros, list(range(1, 12)))

    # -- itens 5, 6: onze gráficos públicos, um por pergunta -----------------

    def test_item5_onze_graficos_publicos(self):
        self.assertEqual(len(textos.PERGUNTAS_NEGOCIO_GRAFICOS), 11)
        self.assertEqual(len(set(textos.PERGUNTAS_NEGOCIO_GRAFICOS)), 11)
        for caminho in textos.PERGUNTAS_NEGOCIO_GRAFICOS:
            with self.subTest(caminho=caminho):
                self.assertTrue((ROOT / caminho).is_file())
                self.assertTrue(caminho.startswith("reports/public/figures/"))

    def test_item6_cada_pergunta_tem_grafico_distinto(self):
        por_numero = {item["numero"]: item["grafico"] for item in textos.PERGUNTAS_NEGOCIO}
        self.assertEqual(len(por_numero), 11)
        self.assertEqual(len(set(por_numero.values())), 11)
        self.assertEqual(
            por_numero,
            {item["numero"]: item["grafico"] for item in self.publico["perguntas"]},
        )

    # -- itens 7, 8: números carregados dos artefatos, sem duplicação -------

    def test_item7_numeros_carregados_dos_artefatos(self):
        """As respostas mudam se os NÚMEROS de entrada mudam — prova que são
        calculadas em tempo de execução, não fixas no texto."""
        perguntas_reais = textos.construir_perguntas_com_respostas(self.analises, self.modelo)
        resposta_real_q1 = perguntas_reais[1]["resposta"]

        analises_sinteticas = json.loads(json.dumps(self.analises))  # cópia profunda
        analises_sinteticas["anuais"]["2022"]["categorias"]["proporcoes"]["moderada"] = 0.01
        analises_sinteticas["anuais"]["2022"]["categorias"]["proporcoes"]["severa"] = 0.01
        perguntas_sinteticas = textos.construir_perguntas_com_respostas(analises_sinteticas, self.modelo)
        resposta_sintetica_q1 = perguntas_sinteticas[1]["resposta"]

        self.assertNotEqual(resposta_real_q1, resposta_sintetica_q1)
        self.assertIn("1%", resposta_sintetica_q1)

    def test_item7b_cada_resposta_reage_a_alteracao_sintetica_da_sua_fonte(self):
        base = textos.construir_perguntas_com_respostas(
            self.analises, self.modelo, self.metricas_reais["privacidade"]
        )

        cenarios = {
            1: ("analises", ("anuais", "2022", "categorias", "proporcoes", "moderada")),
            2: ("analises", ("anuais", "2022", "indicadores", "ida", "media")),
            3: ("analises", ("associacoes", "ajustado_ano", "ieg x ida", "rho")),
            4: ("analises", ("associacoes", "ajustado_ano", "iaa x ida", "rho")),
            5: ("analises", ("longitudinal", "2022→2023", "ips", "ida", "associacao", "rho")),
            6: ("analises", ("ipp", "2023", "ipp x ian", "rho")),
            7: ("analises", ("ipv", "2022", "ida", "rho")),
            9: ("modelo", ("temporal", "recall")),
            10: ("analises", ("longitudinal", "2022→2023", "pedras_evolucao", "proporcoes", "melhoria")),
            11: ("analises", ("perdas", "2022→2023", "desfecho", "contagens", "destino_ausente")),
        }
        # Q7 usa a camada `associacoes` dentro do ano.
        cenarios[7] = ("analises", ("ipv", "2022", "associacoes", "ida", "rho"))

        for numero, (origem, caminho) in cenarios.items():
            with self.subTest(numero=numero):
                analises = json.loads(json.dumps(self.analises))
                modelo = json.loads(json.dumps(self.modelo))
                alvo = analises if origem == "analises" else modelo
                for chave in caminho[:-1]:
                    alvo = alvo[chave]
                alvo[caminho[-1]] = -0.987654321
                alterado = textos.construir_perguntas_com_respostas(
                    analises, modelo, self.metricas_reais["privacidade"]
                )
                self.assertNotEqual(base[numero], alterado[numero])

        analises = json.loads(json.dumps(self.analises))
        perfis = analises["inde"]["2022"]["perfis_publicados"]
        melhor = max(perfis, key=lambda perfil: perfis[perfil]["media"])
        perfis[melhor]["media"] = 99.0
        alterado = textos.construir_perguntas_com_respostas(
            analises, self.modelo, self.metricas_reais["privacidade"]
        )
        self.assertNotEqual(base[8], alterado[8])

    def test_item8_ausencia_de_duplicacao_manual_dos_resultados(self):
        """Os extratores recebem `analises`/`modelo` como PARÂMETRO — nenhuma
        função de pergunta lê uma constante de módulo com o número já
        pronto."""
        codigo_textos = TEXTOS_PATH.read_text(encoding="utf-8")
        arvore = ast.parse(codigo_textos)
        funcoes_pergunta = [n for n in ast.walk(arvore)
                            if isinstance(n, ast.FunctionDef) and n.name in
                            {f"_q{n}" for n in range(1, 12)}]
        self.assertEqual(len(funcoes_pergunta), 11)
        for funcao in funcoes_pergunta:
            argumentos = {a.arg for a in funcao.args.args}
            self.assertIn("analises", argumentos)
            self.assertIn("modelo", argumentos)

    # -- itens 9, 10, 11: índice completo e seleção direta -------------------

    def test_item9_indice_permite_acesso_direto_as_onze_perguntas(self):
        at = _novo_app()
        sb = _selectbox_de_pergunta(at)
        numeros_exibidos = [int(rotulo.split(".", 1)[0]) for rotulo in sb.options]
        self.assertEqual(numeros_exibidos, list(range(1, 12)))
        texto = _texto_total(at)
        self.assertIn("responde às 11 perguntas de negócio", texto)
        for numero, pergunta in enumerate(textos.PERGUNTAS_NEGOCIO, 1):
            self.assertIn(f"{numero}. {pergunta['pergunta']}", texto)

    def test_navegador_explicita_total_seletor_e_estado_inicial(self):
        """Revisão editorial (24/09/2026, Parte 2): o navegador não tem mais
        um título/subtítulo próprios (o seletor fica imediatamente acima do
        conteúdo da pergunta, sem nada entre eles) — o essencial a conferir
        é o próprio seletor e o estado inicial dos botões."""
        at = _novo_app()
        seletor = _selectbox_de_pergunta(at)
        self.assertEqual(seletor.label, "Escolha uma das 11 perguntas")
        self.assertEqual(len(seletor.options), 11)
        self.assertEqual(len(set(seletor.options)), 11)
        self.assertEqual(
            seletor.options,
            [f"{item['numero']}. {item['pergunta']}" for item in textos.PERGUNTAS_NEGOCIO],
        )
        self.assertEqual(seletor.value, 1)
        self.assertTrue(_contador_exibido(at, 1))
        self.assertEqual(_capitulo_exibido(at), "Capítulo: Trajetória e defasagem")
        self.assertTrue(_button(at, "← Pergunta anterior").disabled)
        self.assertFalse(_button(at, "Próxima pergunta →").disabled)

    def test_navegador_botoes_avancam_e_retornam_sem_circular(self):
        at = _novo_app()

        _button(at, "Próxima pergunta →").click()
        at.run(timeout=30)
        self.assertEqual(_selectbox_de_pergunta(at).value, 2)
        self.assertTrue(_contador_exibido(at, 2))
        self.assertEqual(_capitulo_exibido(at), "Capítulo: Aprendizagem e engajamento")
        self.assertFalse(_button(at, "← Pergunta anterior").disabled)
        self.assertFalse(_button(at, "Próxima pergunta →").disabled)
        self.assertIn("### Pergunta 2", _texto_total(at))
        self.assertIn(f"**{textos.PERGUNTAS_NEGOCIO[1]['pergunta']}**", _texto_total(at))

        _button(at, "← Pergunta anterior").click()
        at.run(timeout=30)
        self.assertEqual(_selectbox_de_pergunta(at).value, 1)
        self.assertTrue(_contador_exibido(at, 1))
        self.assertEqual(_capitulo_exibido(at), "Capítulo: Trajetória e defasagem")
        self.assertTrue(_button(at, "← Pergunta anterior").disabled)
        self.assertIn("### Pergunta 1", _texto_total(at))
        self.assertIn(f"**{textos.PERGUNTAS_NEGOCIO[0]['pergunta']}**", _texto_total(at))

    def test_navegador_selecao_direta_da_pergunta_11_e_limite_final(self):
        at = _selecionar_pergunta(_novo_app(), 11)
        self.assertEqual(_selectbox_de_pergunta(at).value, 11)
        self.assertTrue(_contador_exibido(at, 11))
        self.assertEqual(_capitulo_exibido(at), "Capítulo: Trajetória e defasagem")
        self.assertFalse(_button(at, "← Pergunta anterior").disabled)
        self.assertTrue(_button(at, "Próxima pergunta →").disabled)
        self.assertIn("### Pergunta 11", _texto_total(at))
        self.assertIn(
            f"**{textos.PERGUNTAS_NEGOCIO[10]['pergunta']}**", _texto_total(at)
        )

    def test_navegador_sincroniza_resposta_tabela_grafico_e_capitulo(self):
        perguntas = self.perguntas_publicas
        at = _novo_app()
        for numero in (1, 2, 6, 9, 11):
            with self.subTest(numero=numero):
                _selecionar_pergunta(at, numero)
                pergunta = perguntas[numero]

                self.assertEqual(_selectbox_de_pergunta(at).value, numero)
                self.assertTrue(_contador_exibido(at, numero))
                self.assertEqual(
                    _capitulo_exibido(at),
                    f"Capítulo: {_capitulo_esperado(numero)}",
                )
                self.assertIn(pergunta["resposta"], _texto_total(at))
                tabela = at.dataframe[0].value.to_dict(orient="records")
                # A interface substitui `None` por um travessão antes de
                # exibir (item da correção pós-auditoria comparativa: uma
                # célula "None" crua se lia como erro do sistema) — a mesma
                # convenção já usada por `render_report()` no relatório em
                # markdown. Colunas que misturam números com o travessão
                # viram `object`/string ao passar pela serialização Arrow do
                # Streamlit (comportamento real, verificado empiricamente),
                # então a comparação abaixo é tolerante a tipo: compara como
                # número quando os dois lados são numéricos, senão como
                # texto — nunca compara dtype exato.
                def _celula_comparavel(valor):
                    if valor is None or (isinstance(valor, float) and math.isnan(valor)):
                        return "—"
                    try:
                        return round(float(valor), 6)
                    except (TypeError, ValueError):
                        return str(valor)

                # A interface renomeia algumas colunas para nomes compreensíveis
                # (revisão editorial, 24/09/2026, Parte 3 — ex.: "n" vira
                # "Quantidade de estudantes"); a comparação aplica o mesmo
                # mapeamento aos dados brutos antes de comparar.
                renomeia = {"n": "Quantidade de estudantes", "Sexo": "Grupo"}
                tabela_normalizada = [
                    {chave: _celula_comparavel(valor) for chave, valor in linha.items()}
                    for linha in tabela
                ]
                esperado = [
                    {renomeia.get(chave, chave): _celula_comparavel(valor) for chave, valor in linha.items()}
                    for linha in pergunta["principais_numeros"]
                ]
                self.assertEqual(tabela_normalizada, esperado)

    # -- navegador imediatamente antes do conteúdo da pergunta (revisão editorial, Parte 2) --

    def test_navegador_fica_imediatamente_antes_do_conteudo_da_pergunta(self):
        """Revisão editorial (24/09/2026, Parte 2): resumo executivo, índice
        e capítulos ficam recolhidos e ANTES do navegador — sem nada entre o
        navegador e o conteúdo da pergunta selecionada. Verificado por
        posição no código-fonte (a mesma técnica já usada por
        `test_item23_curvas_apenas_na_camada_tecnica`), já que os tipos de
        elemento do `AppTest` não preservam ordem visual entre si."""
        codigo = APP_PATH.read_text(encoding="utf-8")
        indice_expander_resumo = codigo.index('st.expander("Resumo executivo")')
        indice_expander_indice = codigo.index('st.expander("Índice completo das 11 perguntas"')
        indice_expander_capitulos = codigo.index('st.expander("Organização por capítulos")')
        indice_navegador = codigo.index('key="panorama_navegador_"')
        indice_conteudo_pergunta = codigo.index('st.markdown(f"### Pergunta {numero} de {len(perguntas)}")')
        self.assertLess(indice_expander_resumo, indice_navegador)
        self.assertLess(indice_expander_indice, indice_navegador)
        self.assertLess(indice_expander_capitulos, indice_navegador)
        self.assertLess(indice_navegador, indice_conteudo_pergunta)

    def test_indice_completo_e_organizacao_por_capitulos_ficam_recolhiveis(self):
        at = _novo_app()
        rotulos_expander = {e.label for e in at.expander}
        self.assertIn("Resumo executivo", rotulos_expander)
        self.assertIn("Índice completo das 11 perguntas", rotulos_expander)
        self.assertIn("Organização por capítulos", rotulos_expander)

    # -- storytelling, conclusão e recortes (correção pós-auditoria comparativa, 24/09/2026) --

    def test_cada_pergunta_exibe_por_que_importa_e_em_resumo(self):
        """Refatoração editorial (24/09/2026): "por que importa" continua
        visível logo no cabeçalho da pergunta; "como foi analisada" (texto
        mais técnico) deixou de aparecer literalmente na camada principal —
        a metodologia em linguagem pública agora vive em "Fonte e
        metodologia" (`test_expander_fonte_e_metodologia_em_linguagem_publica`)."""
        at = _novo_app()
        for numero in range(1, 12):
            with self.subTest(numero=numero):
                _selecionar_pergunta(at, numero)
                pergunta = self.perguntas_publicas[numero]
                texto = _texto_total(at)
                self.assertIn(pergunta["por_que_importa"], texto)
                self.assertIn("Em resumo", texto)
                self.assertIn(pergunta["resposta"], texto)

    # Duas expressões de jargão sobrevivem em dois campos de conclusão já
    # aprovados (pergunta 1 e 10); a interface traduz só essas duas na
    # apresentação, sem alterar a análise em si — ver `_texto_publico` em
    # `streamlit_app.py`. O teste aplica a mesma tradução antes de comparar.
    _TRADUCOES_JARGAO_ESPERADAS = {
        "caixa pequena": "grupo pequeno demais para publicar com segurança",
        "artefato interno": "registro interno da análise",
        "artefato congelado": "registro congelado do modelo",
        "células pequenas": "grupos pequenos",
        "células maiores": "grupos maiores",
        "partição de 2024": "recorte de 2024",
    }

    def _texto_publico_esperado(self, texto: str) -> str:
        for termo, traducao in self._TRADUCOES_JARGAO_ESPERADAS.items():
            texto = texto.replace(termo, traducao)
        return texto

    def test_cada_pergunta_exibe_bloco_de_conclusao_completo(self):
        """Revisão editorial (24/09/2026, Parte 4): a conclusão não é mais
        5 linhas com rótulos técnicos — é um texto contínuo de 2 a 4
        parágrafos (`narrativa.conclusao_fluida`). Verifica estrutura
        (quantidade de parágrafos, ausência dos rótulos antigos) e que cada
        parágrafo efetivamente aparece na interface renderizada."""
        at = _novo_app()
        for numero in range(1, 12):
            with self.subTest(numero=numero):
                _selecionar_pergunta(at, numero)
                paragrafos = narrativa.conclusao_fluida(numero)
                self.assertGreaterEqual(len(paragrafos), 2)
                self.assertLessEqual(len(paragrafos), 4)
                texto = _texto_total(at)
                self.assertIn("O que isso significa", texto)
                for paragrafo in paragrafos:
                    self.assertIn(self._texto_publico_esperado(paragrafo), texto)
                for rotulo_antigo in ("Principal resultado.", "Ponto de atenção.", "Limite da análise.",
                                     "Implicação para a ONG.", "Próximo acompanhamento sugerido."):
                    self.assertNotIn(rotulo_antigo, texto)

    def test_recortes_tecnicos_nao_aparecem_na_interface_publica(self):
        """Refatoração editorial (24/09/2026, item 1): o inventário de
        recortes (sexo/idade/fase/.../"implementado"/"não implementado") é
        conteúdo interno de desenvolvimento — não pode mais aparecer na
        interface pública. Os dados continuam no JSON público (ver
        `test_recortes_documentados_para_as_oito_dimensoes_em_todas_as_perguntas`
        em `tests/test_analises_publicas.py`), só não são mais renderizados."""
        at = _novo_app()
        for numero in range(1, 12):
            with self.subTest(numero=numero):
                _selecionar_pergunta(at, numero)
                rotulos_expander = {e.label for e in at.expander}
                self.assertFalse(any("Recortes considerados" in r for r in rotulos_expander))
                texto = _texto_total(at)
                for termo in ("implementado", "não implementado", "célula", "partição",
                             "payload", "artefato", "schema", "caixa pequena",
                             "redundância com outra análise", "publicável",
                             "agregado sanitizado", "supressão por divulgação conjunta",
                             "agregado ajustado", "gradiente", "correlação ordinal",
                             "terceiro fator comum", "coorte"):
                    self.assertNotIn(termo, texto, f"pergunta {numero}: termo interno {termo!r} vazou para a interface")

    def test_analises_complementares_aparecem_dentro_de_ver_dados_da_analise(self):
        """Todas as 11 perguntas têm análises complementares; a partir da
        refatoração editorial (24/09/2026) elas ficam dentro do expander
        "Ver dados da análise", não mais num expander próprio com o número
        da pergunta e a palavra "recortes" no rótulo (linguagem interna)."""
        at = _novo_app()
        for numero in range(1, 12):
            with self.subTest(numero=numero):
                pergunta = self.perguntas_publicas[numero]
                self.assertTrue(pergunta["analises_complementares_numeros"],
                                f"pergunta {numero} sem análises complementares")
                _selecionar_pergunta(at, numero)
                rotulos_expander = {e.label for e in at.expander}
                self.assertIn("Ver dados da análise", rotulos_expander)
                self.assertIn("Outros recortes", _texto_total(at))

    def test_sexo_e_idade_implementados_apenas_no_minimo_exigido_pela_correcao(self):
        """Regressão do escopo aprovado na correção pós-auditoria comparativa
        (24/09/2026, item 1/2): sexo e idade só podem aparecer marcados como
        implementados nas perguntas 1, 2, 3, 9, 10 e 11 (mínimo exigido);
        nas demais, continuam explicitamente não implementados."""
        at = _novo_app()
        minimo_exigido = {1, 2, 3, 9, 10, 11}
        for numero in range(1, 12):
            with self.subTest(numero=numero):
                _selecionar_pergunta(at, numero)
                pergunta = self.perguntas_publicas[numero]
                esperado = numero in minimo_exigido
                self.assertEqual(pergunta["recortes"]["sexo"]["implementado"], esperado)
                self.assertEqual(pergunta["recortes"]["idade"]["implementado"], esperado)

    # -- gráficos interativos (auditoria comparativa, Seção 9) ---------------

    def test_cada_pergunta_tem_pelo_menos_um_grafico_interativo(self):
        at = _novo_app()
        for numero in range(1, 12):
            with self.subTest(numero=numero):
                _selecionar_pergunta(at, numero)
                chaves = [el.key for el in at.get("plotly_chart")
                         if el.key and el.key.startswith(f"panorama_grafico_{numero}_")]
                self.assertGreaterEqual(len(chaves), 1)

    def test_quantidade_de_graficos_interativos_por_pergunta(self):
        """Q1 (composição anual + média anual do IAN + recorte por sexo/
        faixa etária, adicionados na correção pós-auditoria comparativa)
        tem três gráficos; Q6 (associações + médias por categoria) e Q10
        (transições + IDA por Pedra de origem) têm dois; Q7 (contemporâneas
        + futuras) tem dois; Q9 (recall + matriz de confusão + equidade por
        fase) tem três — consistente com
        `graficos_publicos._GRAFICOS_SECUNDARIOS`/`_GRAFICOS_TERCIARIOS`."""
        at = _novo_app()
        esperado = {1: 3, 6: 2, 7: 2, 9: 3, 10: 2}
        for numero, quantidade in esperado.items():
            with self.subTest(numero=numero):
                _selecionar_pergunta(at, numero)
                chaves = [el.key for el in at.get("plotly_chart")
                         if el.key and el.key.startswith(f"panorama_grafico_{numero}_")]
                self.assertEqual(len(chaves), quantidade)

    def test_nenhuma_tabela_exibe_none_cru(self):
        """Regressão do achado da auditoria comparativa independente
        (24/09/2026): uma célula suprimida por privacidade (ex.: pergunta 6,
        2024, "IPP por categoria") não pode aparecer como o texto literal
        "None" na tabela renderizada — deve ser compreensível sozinha, sem
        depender só da nota abaixo. Cobre as 11 perguntas, não apenas as
        que têm supressão conhecida hoje."""
        at = _novo_app()
        for numero in range(1, 12):
            with self.subTest(numero=numero):
                _selecionar_pergunta(at, numero)
                for tabela in at.dataframe:
                    for linha in tabela.value.to_dict(orient="records"):
                        for valor in linha.values():
                            texto_valor = str(valor).strip().casefold()
                            self.assertNotIn(texto_valor, ("none", "nan", "null", "<na>", "nat"),
                                             f"pergunta {numero}: valor interno de ausência exibido cru ({valor!r})")

    def test_nenhuma_tabela_tem_coluna_inteiramente_vazia(self):
        """Revisão editorial (24/09/2026, Parte 3, item 3): uma tabela não
        pode ter uma coluna onde toda linha é vazia/travessão — sinal de que
        um recorte que não se aplica àquela linha foi incluído mesmo assim.
        O resumo de indicadores de "Avaliar um caso" usa `st.table` (não
        `st.dataframe`), então nem aparece na varredura `at.dataframe`
        abaixo — de propósito, já que numa aplicação recém-aberta, sem
        nenhum indicador preenchido, sua coluna "Valor utilizado" é
        legitimamente toda "—", o que não é o mesmo defeito estrutural que
        este teste (específico das tabelas de recorte do Panorama) procura."""
        at = _novo_app()
        for numero in range(1, 12):
            with self.subTest(numero=numero):
                _selecionar_pergunta(at, numero)
                for tabela in at.dataframe:
                    linhas = tabela.value.to_dict(orient="records")
                    if not linhas:
                        continue
                    for coluna in linhas[0]:
                        valores = {str(linha.get(coluna, "—")).strip() for linha in linhas}
                        self.assertFalse(
                            valores <= {"—", "", "nan", "none"},
                            f"pergunta {numero}: coluna {coluna!r} inteiramente vazia",
                        )

    def test_tabelas_de_recorte_tem_apenas_colunas_pertinentes(self):
        """Revisão editorial (24/09/2026, Parte 3, item 4): a tabela de sexo
        de uma pergunta não pode ter coluna de faixa etária, e vice-versa —
        cada tipo de recorte tem sua própria tabela, sem campos cruzados."""
        d = json.loads((ROOT / "reports" / "public" / "perguntas_oficiais_v1.json").read_text(encoding="utf-8"))
        perguntas = {p["numero"]: p for p in d["perguntas"]}
        for numero in (1, 2, 3, 9, 10, 11):
            with self.subTest(numero=numero):
                tabelas = narrativa.tabelas_complementares(perguntas[numero])
                self.assertTrue(tabelas, f"pergunta {numero} deveria ter tabelas específicas por recorte")
                for tabela in tabelas:
                    colunas = set(tabela["linhas"][0]) if tabela["linhas"] else set()
                    # Uma tabela de faixa etária não pode ter coluna "Grupo"
                    # (sexo), e uma tabela de sexo não pode ter "Faixa etária
                    # aproximada" — são recortes diferentes.
                    tem_faixa = any("faixa" in c.casefold() for c in colunas)
                    tem_grupo_sexo = "Grupo" in colunas
                    self.assertFalse(tem_faixa and tem_grupo_sexo,
                                     f"pergunta {numero}, tabela {tabela['titulo']!r}: mistura sexo e faixa etária")

    def test_grafico_oficial_png_nao_aparece_mais_na_interface_publica(self):
        """Refatoração editorial (24/09/2026, item 2): o PNG oficial
        (verificado por hash) deixou de ser exibido na interface pública —
        o gráfico interativo em Plotly é a única evidência visual mostrada
        ao usuário. O arquivo, o hash e a verificação continuam intactos em
        disco e cobertos por `test_manifesto_confere`
        (`tests/test_analises_publicas.py`); só não aparecem mais aqui."""
        at = _selecionar_pergunta(_novo_app(), 1)
        rotulos_expander = {e.label for e in at.expander}
        self.assertNotIn("Detalhes técnicos: gráfico oficial, população e fonte exata", rotulos_expander)
        self.assertFalse(any("verificado por hash" in (e.label or "") for e in at.expander))
        texto = _texto_total(at)
        self.assertNotIn("verificado por hash", texto)
        self.assertNotIn("Gráfico oficial", texto)

    def test_item10_troca_de_pergunta_muda_o_conteudo_exibido(self):
        at = _novo_app()
        _selecionar_pergunta(at, 2)
        texto_q2 = _texto_total(at)
        self.assertIn(textos.PERGUNTAS_NEGOCIO[1]["pergunta"], texto_q2)
        _selecionar_pergunta(at, 3)
        texto_q3 = _texto_total(at)
        self.assertIn(textos.PERGUNTAS_NEGOCIO[2]["pergunta"], texto_q3)

    def test_item11_todas_as_perguntas_sao_acessiveis_sem_trocar_capitulo(self):
        at = _novo_app()
        contagem_inicial = len(at.image)
        for numero in range(1, 12):
            _selecionar_pergunta(at, numero)
            self.assertIn(textos.PERGUNTAS_NEGOCIO[numero - 1]["pergunta"], _texto_total(at))
            self.assertEqual(len(at.image), contagem_inicial)

    # -- item 12: gráfico corresponde à pergunta selecionada ------------------

    def test_item12_grafico_corresponde_a_pergunta_selecionada(self):
        """A partir da refatoração editorial (24/09/2026), a correspondência
        entre pergunta selecionada e gráfico é verificada pela CHAVE do
        `st.plotly_chart` (`panorama_grafico_{numero}_...`, única por
        pergunta) — não mais por legenda de imagem estática, removida da
        interface pública (item 2)."""
        at = _novo_app()
        _selecionar_pergunta(at, 6)
        chaves = [el.key for el in at.get("plotly_chart") if el.key]
        self.assertTrue(chaves, "nenhum gráfico interativo renderizado para a pergunta 6")
        self.assertTrue(all(chave.startswith("panorama_grafico_6_") for chave in chaves))

    # -- itens 13-17: estrutura uniforme do cartão ----------------------------

    def test_itens13a17_estrutura_uniforme_do_cartao(self):
        """Refatoração editorial (24/09/2026): a estrutura narrativa
        (identificação → Em resumo → números principais → evidências →
        conclusão → conteúdo secundário recolhido) precisa se repetir em
        todas as 11 perguntas."""
        at = _novo_app()
        for numero in range(1, 12):
            with self.subTest(numero=numero):
                _selecionar_pergunta(at, numero)
                texto = _texto_total(at)
                for rotulo in (
                    f"### Pergunta {numero} de 11", "Em resumo", "Números principais",
                    "Evidências", "O que isso significa",
                ):
                    self.assertIn(rotulo, texto, f"pergunta {numero}: {rotulo!r} ausente")
                rotulos_expander = {e.label for e in at.expander}
                self.assertIn("Ver dados da análise", rotulos_expander)
                self.assertIn("Fonte e metodologia", rotulos_expander)

    def test_cartao_numera_a_pergunta_sem_numerar_as_secoes(self):
        at = _novo_app()
        marcacoes = [str(item.value) for item in at.markdown]
        self.assertIn("### Pergunta 1 de 11", marcacoes)
        self.assertNotIn("##### 1. Pergunta oficial", marcacoes)
        self.assertIn("##### Em resumo", marcacoes)
        self.assertIn("##### Números principais", marcacoes)

        _selecionar_pergunta(at, 2)
        marcacoes = [str(item.value) for item in at.markdown]
        self.assertIn("### Pergunta 2 de 11", marcacoes)
        self.assertNotIn("### Pergunta 1 de 11", marcacoes)
        self.assertNotIn("##### 2. Em resumo", marcacoes)

    def test_item17b_pergunta_8_inclui_os_tres_anos(self):
        perguntas = textos.construir_perguntas_com_respostas(
            self.analises, self.modelo, self.metricas_reais["privacidade"]
        )
        anos = [linha["Ano"] for linha in perguntas[8]["principais_numeros"]]
        self.assertEqual(anos, ["2022", "2023", "2024"])

    def test_item17c_supressao_tem_regra_objetiva_sem_expor_contagem(self):
        perguntas = textos.construir_perguntas_com_respostas(
            self.analises, self.modelo, self.metricas_reais["privacidade"]
        )
        q1 = perguntas[1]
        self.assertIn(str(self.metricas_reais["privacidade"]["minimo_perfil"]), q1["resposta"])
        linha_2024 = q1["principais_numeros"][-1]
        self.assertEqual(linha_2024["Categoria"], "partição protegida")
        self.assertIsNone(linha_2024["Contagem"])

    # -- itens 18, 19, 20: idade e notas ---------------------------------------

    def test_item18_explicacao_correta_sobre_idade(self):
        texto = _texto_total(_novo_app())
        self.assertIn("idade", texto.lower())
        self.assertIn("fase ideal", texto.lower())
        self.assertIn("suger", texto.lower())

    def test_item19_explicacao_correta_sobre_notas_e_ida(self):
        texto = _texto_total(_novo_app())
        self.assertIn("matemática, português e inglês", texto.lower())
        self.assertIn("(matemática + português + inglês) / 3", texto.lower())

    def test_item20_idade_e_notas_disponiveis_na_ficha(self):
        at = _novo_app()
        chaves = {ti.key for ti in at.text_input} | {sb.key for sb in at.selectbox if sb.key and sb.key.startswith("campo_")}
        self.assertIn("campo_idade_contexto", chaves)
        _by_key(at.radio, "modo_ida").set_value(textos.ROTULO_MODO_IDA_CALCULADO)
        at.run(timeout=30)
        chaves = {ti.key for ti in at.text_input}
        self.assertTrue({"campo_nota_matematica", "campo_nota_portugues", "campo_nota_ingles"} <= chaves)

    # -- itens 21, 22: preservação do formulário e da inferência --------------

    def test_item21_sete_preditores_preservados(self):
        at = _novo_app()
        chaves_oficiais = {f"campo_{c}" for c in inf.FEATURES}
        todas_chaves = {ti.key for ti in at.text_input} | {
            sb.key for sb in at.selectbox if sb.key and sb.key.startswith("campo_")}
        self.assertTrue(chaves_oficiais - {"campo_defasagem_origem"} <= todas_chaves)

    def test_item22_predicao_sintetica_preservada(self):
        contexto = inf.prepare_application(root=ROOT)
        at = _novo_app()
        _button(at, "Preencher exemplo sintético").click()
        at.run(timeout=30)
        valores_exemplo = {campo: _by_key(at.text_input, f"campo_{campo}").value
                           for campo in ("ida", "ieg", "iaa", "ips", "ipv")}
        valores_exemplo["fase_origem"] = _by_key(at.selectbox, "campo_fase_origem").value
        valores_exemplo["defasagem_origem"] = "0"
        esperado = inf.run_inference(contexto, valores_exemplo)

        _button(at, "Gerar estimativa").click()
        at.run(timeout=30)
        percentual_exibido = float(at.metric[0].value.rstrip("%").replace(",", "."))
        self.assertAlmostEqual(percentual_exibido, esperado.probability * 100, places=1)

    # Item 23 (curvas só na camada técnica) migrou para
    # `tests/test_relatorio_modelo_e_limitacoes.py`: `curvas_modelagem.png`
    # não é mais referenciada em `streamlit_app.py` (decisão de produto,
    # 25/09/2026: "Modelo e limitações" saiu da navegação da aplicação).

    # -- item 27: ausência de treino/recalibração ------------------------------

    def test_item27_ausencia_de_treino_ou_recalibracao(self):
        proibidos = {"fit", "fit_transform", "partial_fit", "cross_val_score", "cross_validate", "GridSearchCV"}
        for nome, caminho in PUBLIC_PYTHON_MODULES:
            with self.subTest(modulo=nome):
                arvore = ast.parse(caminho.read_text(encoding="utf-8"))
                chamadas = {n.func.attr for n in ast.walk(arvore)
                           if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
                self.assertEqual(chamadas & proibidos, set())

    # -- item 28: caminhos relativos -------------------------------------------

    def test_item28_caminhos_dos_graficos_sao_relativos(self):
        for caminho in textos.PERGUNTAS_NEGOCIO_GRAFICOS:
            self.assertFalse(Path(caminho).is_absolute())
            self.assertFalse(caminho.startswith("C:"))

    # -- item 30 (extensão): cópia pública precisa dos novos artefatos --------

    def test_item30_panorama_funciona_em_copia_publica_minima(self):
        tmp = Path(tempfile.mkdtemp(prefix="panorama_portabilidade_"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        for relativo in inf.PUBLIC_REQUIRED_PATHS:
            destino = tmp / relativo
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relativo, destino)
        extras = [
            "reports/public/perguntas_oficiais_v1.json",
            "reports/public/manifesto_integridade_v1.json",
            "reports/curvas_modelagem.png",
            *textos.PERGUNTAS_NEGOCIO_GRAFICOS,
        ]
        for relativo in extras:
            destino = tmp / relativo
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relativo, destino)

        sys.path.insert(0, str(SRC))
        import streamlit_app as app_module  # noqa: F401 — só para checar import limpo se necessário

        metricas = app_module._carregar_metricas_negocio.__wrapped__(tmp)
        self.assertEqual(metricas["camada"], "publica_sanitizada")
        self.assertEqual(len(metricas["perguntas"]), 11)

    def test_tema_e_css_fazem_parte_dos_caminhos_publicos_obrigatorios(self):
        """Correção final pré-inspeção (24/09/2026): `.streamlit/config.toml`
        e `assets/styles/app.css` precisam ser exigidos pelo mesmo mecanismo
        que já protege os artefatos do modelo — para que a cópia pública
        mínima reproduza o mesmo tema e CSS do deploy final, nunca uma
        versão visualmente divergente."""
        self.assertIn(".streamlit/config.toml", inf.PUBLIC_REQUIRED_PATHS)
        self.assertIn("assets/styles/app.css", inf.PUBLIC_REQUIRED_PATHS)

    def test_copia_publica_minima_inclui_tema_e_css_carregaveis(self):
        """Estende `test_item30_panorama_funciona_em_copia_publica_minima`:
        confirma que a mesma cópia pública mínima (montada só a partir de
        `inf.PUBLIC_REQUIRED_PATHS` + os extras do painel) já contém
        `.streamlit/config.toml` e `assets/styles/app.css` — sem precisar
        de nenhuma cópia adicional — e que o caminho do CSS é resolvido a
        partir de `streamlit_app.py`, não do diretório de trabalho atual."""
        tmp = Path(tempfile.mkdtemp(prefix="panorama_tema_css_"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        for relativo in inf.PUBLIC_REQUIRED_PATHS:
            destino = tmp / relativo
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relativo, destino)
        shutil.copy2(APP_PATH, tmp / "streamlit_app.py")

        self.assertTrue((tmp / ".streamlit" / "config.toml").is_file())
        self.assertTrue((tmp / "assets" / "styles" / "app.css").is_file())
        config_copiado = tomllib.loads((tmp / ".streamlit" / "config.toml").read_text(encoding="utf-8"))
        config_original = tomllib.loads((ROOT / ".streamlit" / "config.toml").read_text(encoding="utf-8"))
        self.assertEqual(config_copiado, config_original)

        # Resolução do CSS depende só de `__file__` (streamlit_app.py dentro
        # de `tmp`), nunca do diretório de trabalho atual do processo.
        cwd_original = Path.cwd()
        outro_cwd = Path(tempfile.mkdtemp(prefix="cwd_alternativo_css_"))
        self.addCleanup(shutil.rmtree, outro_cwd, ignore_errors=True)
        try:
            os.chdir(outro_cwd)
            sys.path.insert(0, str(tmp))
            spec = importlib.util.spec_from_file_location("streamlit_app_copia_tema", tmp / "streamlit_app.py")
            modulo_copia = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(modulo_copia)
            self.assertEqual(modulo_copia.CSS_PATH, tmp / "assets" / "styles" / "app.css")
            css_carregado = modulo_copia._carregar_css.__wrapped__()
            css_original = (ROOT / "assets" / "styles" / "app.css").read_text(encoding="utf-8")
            self.assertEqual(css_carregado, css_original)
            self.assertTrue(css_carregado.strip())
        finally:
            os.chdir(cwd_original)

    def test_media_ian_2024_continua_7_68_e_eixo_continua_categorico(self):
        """Preserva a correção anterior (item 5 desta revisão editorial):
        a média de 2024 continua publicada como 7,68 (arredondada a duas
        casas decimais), e o gráfico correspondente continua com eixo
        categórico (2022/2023/2024), nunca numérico contínuo."""
        d = json.loads((ROOT / "reports" / "public" / "perguntas_oficiais_v1.json").read_text(encoding="utf-8"))
        q1 = next(p for p in d["perguntas"] if p["numero"] == 1)
        linha_2024 = next(r for r in q1["analises_complementares_numeros"]
                          if r.get("Recorte") == "Média anual do IAN" and r.get("Ano") == "2024")
        self.assertEqual(linha_2024["Valor"], 7.68)

        figuras = graficos.graficos_interativos(1, q1)
        self.assertEqual(figuras[1].layout.xaxis.type, "category")
        self.assertEqual(list(figuras[1].data[0].x), ["2022", "2023", "2024"])

    def test_controles_de_navegacao_existem_tambem_no_final_da_pergunta(self):
        """Revisão editorial (24/09/2026, Parte 2): ao final de cada
        pergunta, os mesmos três controles (anterior, voltar ao índice,
        próxima) precisam existir, com o mesmo estado habilitado/desabilitado
        da primeira e da última pergunta."""
        at = _selecionar_pergunta(_novo_app(), 1)
        self.assertTrue(_by_key(at.button, "panorama_pergunta_anterior_fim").disabled)
        self.assertTrue(any(b.label == "Voltar ao índice" for b in at.button))
        self.assertFalse(_by_key(at.button, "panorama_proxima_pergunta_fim").disabled)

        at = _selecionar_pergunta(at, 11)
        self.assertFalse(_by_key(at.button, "panorama_pergunta_anterior_fim").disabled)
        self.assertTrue(_by_key(at.button, "panorama_proxima_pergunta_fim").disabled)

    def test_ausencia_de_tema_ou_css_falha_com_erro_controlado_e_claro(self):
        """Reaproveita `_montar_copia_publica_isolada` (cópia pública
        completa e isolada) e remove, um de cada vez, `.streamlit/
        config.toml` e `assets/styles/app.css` — confirmando que a ausência
        de qualquer um interrompe a inicialização com uma mensagem clara
        (`PublicValidationError`, citando o caminho exato ausente), nunca
        silenciosamente com uma interface visualmente divergente."""
        for caminho_removido in (".streamlit/config.toml", "assets/styles/app.css"):
            with self.subTest(caminho=caminho_removido):
                tmp = Path(tempfile.mkdtemp(prefix="panorama_sem_tema_ou_css_"))
                self.addCleanup(_limpar_copia_publica_isolada_com_retentativas, tmp)
                _montar_copia_publica_isolada(tmp)
                (tmp / caminho_removido).unlink()
                with self.assertRaises(inf.PublicValidationError) as contexto:
                    inf.prepare_application(root=tmp)
                self.assertIn(caminho_removido, str(contexto.exception))

    # -- item 32: funcionamento sem os PDFs históricos -------------------------

    def test_item32_funcionamento_sem_pdfs_historicos(self):
        for nome, caminho in PUBLIC_PYTHON_MODULES:
            with self.subTest(modulo=nome):
                codigo = caminho.read_text(encoding="utf-8").lower()
                self.assertNotIn("import fitz", codigo)
                self.assertNotIn("import pypdf", codigo)
                arvore = ast.parse(caminho.read_text(encoding="utf-8"))
                literais = list(_non_docstring_string_literals(arvore))
                for termo in (".pdf", "pede2020", "pede2021", "pede2022"):
                    self.assertFalse(any(termo in literal.lower() for literal in literais),
                                     f"{nome} referencia {termo!r} fora de docstring")

    # -- item 33: erro controlado para gráfico ausente/divergente -------------

    def test_item33_erro_controlado_para_grafico_ausente(self):
        import streamlit_app as app_module

        tmp = Path(tempfile.mkdtemp(prefix="panorama_grafico_ausente_"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        destino_json = tmp / "reports" / "metricas_analises_negocio.json"
        destino_json.parent.mkdir(parents=True, exist_ok=True)
        conteudo = json.loads((ROOT / "reports" / "metricas_analises_negocio.json").read_text(encoding="utf-8"))
        destino_json.write_text(json.dumps(conteudo), encoding="utf-8")
        # nenhuma figura copiada -> deve falhar de forma controlada
        with self.assertRaises(app_module.PainelIndisponivelError) as contexto:
            app_module._carregar_metricas_negocio.__wrapped__(tmp)
        mensagem = str(contexto.exception)
        self.assertNotIn(str(tmp), mensagem)
        self.assertNotIn(str(destino_json), mensagem)
        self.assertNotRegex(mensagem, r"\b[0-9a-f]{64}\b")

    def test_item33_painel_indisponivel_apresenta_erro_controlado_na_interface(self):
        """Complementa `test_item33_erro_controlado_para_grafico_ausente`
        (que chama `_carregar_metricas_negocio.__wrapped__` diretamente,
        contornando o cache do Streamlit) exercitando o caminho REAL de
        produção: a aplicação completa, com um gráfico oficial corrompido
        (hash divergente, não apenas ausente) em uma cópia pública isolada,
        confirmando que a mensagem controlada chega até a interface
        renderizada.

        Roda em um PROCESSO PYTHON SEPARADO (não monkeypatcha nada no
        processo dos demais testes): uma tentativa anterior de redirecionar
        `inferencia.find_project_root` e limpar o cache de recurso
        (`st.cache_resource`) no mesmo processo corrompeu o estado
        compartilhado do Streamlit e quebrou testes vizinhos
        (`StreamlitInvalidFormCallbackError` em testes que rodam depois).
        Isolar em subprocesso elimina esse risco e, como bônus, exercita o
        código exatamente como ele roda em produção — sem nenhum stub."""
        tmp = Path(tempfile.mkdtemp(prefix="panorama_ui_grafico_corrompido_"))
        self.addCleanup(_limpar_copia_publica_isolada_com_retentativas, tmp)
        _montar_copia_publica_isolada(tmp, grafico_a_corromper=textos.PERGUNTAS_NEGOCIO_GRAFICOS[0])

        resultado = _rodar_driver_em_subprocesso(self, tmp, _DRIVER_ERRO_CONTROLADO)

        # Nenhum traceback não tratado chegou à interface.
        self.assertEqual(resultado["excecoes"], [])

        mensagens_de_erro = resultado["erros"]
        self.assertTrue(mensagens_de_erro, "nenhuma mensagem de erro controlada foi renderizada")
        texto_erros = "\n".join(mensagens_de_erro)
        self.assertIn("Não foi possível carregar o panorama de dados", texto_erros)

        texto_completo = "\n".join(resultado["texto_total"]) + texto_erros
        # Nunca o caminho do diretório temporário, nunca a mensagem interna
        # de PainelIndisponivelError, nunca um hash completo.
        self.assertNotIn(str(tmp), texto_completo)
        self.assertNotIn("Gráfico oficial", texto_completo)
        self.assertNotRegex(texto_completo, r"\b[0-9a-f]{64}\b")
        self.assertNotIn("Traceback", texto_completo)

    def test_aplicacao_completa_carrega_tema_e_css_na_copia_publica_isolada(self):
        """Correção final pré-inspeção (24/09/2026): executa a aplicação
        REAL (processo filho separado, mesmo padrão dos dois testes
        acima) numa cópia pública isolada e confirma que o CSS local foi
        efetivamente carregado e injetado (não apenas copiado) — a mesma
        cópia já inclui `.streamlit/config.toml` porque ambos os arquivos
        agora fazem parte de `inf.PUBLIC_REQUIRED_PATHS`
        (`_montar_copia_publica_isolada` os copia automaticamente)."""
        tmp = Path(tempfile.mkdtemp(prefix="panorama_tema_css_isolado_"))
        self.addCleanup(_limpar_copia_publica_isolada_com_retentativas, tmp)
        _montar_copia_publica_isolada(tmp)
        self.assertTrue((tmp / ".streamlit" / "config.toml").is_file())
        self.assertTrue((tmp / "assets" / "styles" / "app.css").is_file())

        resultado = _rodar_driver_em_subprocesso(self, tmp, _DRIVER_CSS_E_TEMA)

        self.assertEqual(resultado["excecoes"], [])
        self.assertTrue(resultado["css_presente"], "CSS local não foi injetado na interface renderizada")
        self.assertTrue(resultado["css_nao_vazio"], "CSS injetado ficou vazio (arquivo ausente ou leitura falhou)")

    # -- item 34: nenhuma métrica técnica na abertura -------------------------

    def test_item34_nenhuma_metrica_tecnica_na_abertura(self):
        codigo = APP_PATH.read_text(encoding="utf-8")
        arvore = ast.parse(codigo)
        funcao_inicio = next(
            no for no in arvore.body
            if isinstance(no, ast.FunctionDef) and no.name == "_tab_inicio"
        )
        texto_inicio = "\n".join((
            ast.get_source_segment(codigo, funcao_inicio) or "",
            textos.TITULO_EDITORIAL_INICIO,
            textos.TEXTO_APOIO_INICIO,
            textos.CONTEXTO_DESAFIO,
            textos.QUESTAO_CENTRAL,
            textos.OBJETIVO_TRABALHO,
            *(titulo + " " + descricao for titulo, descricao in textos.CAMINHOS_APLICACAO),
        ))
        for termo in ("ROC-AUC", "Brier", "average_precision", "matriz de confusão"):
            self.assertNotIn(termo.lower(), texto_inicio.lower())
        at = _novo_app()
        self.assertEqual(len(at.metric), 0)  # nenhuma métrica antes de qualquer envio

    # -- item 35: nenhuma referência textual a uma aba que não existe --------

    NOMES_DAS_ABAS_REAIS = (
        "Início", "Panorama e resultados", "Avaliar um caso", "Entenda os indicadores",
    )

    def test_item35_nenhuma_referencia_publica_a_sobre_o_modelo(self):
        """Regressão do defeito encontrado na revisão independente: a aba
        "Sobre o modelo" foi renomeada para "Modelo e limitações" durante a
        ETAPA B — nome que, por sua vez, foi removido da navegação (decisão
        de produto, 25/09/2026). Cobre duas frentes: (a) nenhum dos dois
        nomes antigos pode aparecer em nenhum lugar do código-fonte público;
        (b) toda referência textual entre aspas a uma aba, em qualquer um
        dos módulos públicos, precisa corresponder a uma das abas reais de
        `main()`."""
        for nome, caminho in PUBLIC_PYTHON_MODULES:
            with self.subTest(modulo=nome, verificacao="nomes antigos ausentes"):
                codigo = caminho.read_text(encoding="utf-8")
                self.assertNotIn("Sobre o modelo", codigo)

        padrao_referencia_a_aba = re.compile(r'ver \\?"([^"\\]+)\\?"')
        for nome, caminho in PUBLIC_PYTHON_MODULES:
            codigo = caminho.read_text(encoding="utf-8")
            for referencia in padrao_referencia_a_aba.findall(codigo):
                with self.subTest(modulo=nome, referencia=referencia):
                    self.assertIn(referencia, self.NOMES_DAS_ABAS_REAIS,
                                 f"{nome} referencia uma aba inexistente: {referencia!r}")

        at = _preencher_e_enviar(_novo_app(), PAYLOAD_BAIXO_RISCO)
        texto = _texto_total(at)
        self.assertNotIn("Sobre o modelo", texto)
        self.assertNotIn("Modelo e limitações", texto)

    # -- item 36: IPV — dois papéis (panorama exploratório e preditor) -------

    def test_item36_explicacao_do_ipv_informa_os_dois_papeis(self):
        """A explicação pública do Ponto de Virada precisa deixar claro que
        o IPV não é só uma variável do panorama exploratório: ele também é
        um dos sete preditores diretos usados pelo modelo em "Avaliar um
        caso". Cobre o texto da constante e sua presença na interface
        renderizada (aba "Entenda os indicadores")."""
        texto_constante = textos.EXPLICACAO_PONTO_DE_VIRADA
        self.assertIn("Panorama e resultados", texto_constante)
        self.assertIn("sete preditores diretos", texto_constante)
        self.assertIn("Avaliar um caso", texto_constante)
        self.assertNotIn("Sobre o modelo", texto_constante)

        texto = _texto_total(_novo_app())
        self.assertIn(textos.EXPLICACAO_PONTO_DE_VIRADA, texto)


# --------------------------------------------------------------------------- #
# Privacidade e segurança: análise AST/textual do próprio código-fonte       #
# --------------------------------------------------------------------------- #

_WIDGET_ATTRS = {"text_input", "number_input", "selectbox", "text_area", "date_input",
                 "multiselect", "radio", "checkbox", "file_uploader"}
_FORBIDDEN_FIELD_WORDS = re.compile(r"(?i)\b(ra|nome|cpf|matr[ií]cula|e-?mail|telefone|"
                                    r"endere[cç]o|identificador|identidade)\b")
_SECRET_PATTERN = re.compile(r'(?i)\b(api[_-]?key|secret|token|password|credential)\s*[:=]\s*["\']')
_ABSOLUTE_PATH_PATTERN = re.compile(
    r"(?i)(?:\bfile://)|(?:(?<![\w])[a-z]:[\\/])|(?:\\\\[a-z0-9_.-]+\\)"
    r"|(?:(?<![\w./])/(?:tmp|var|root|workspace|mnt|home|users|private|opt|usr)(?:/|\b))"
)
_WRITE_METHOD_ATTRS = {"write_text", "write_bytes", "write", "to_csv", "to_json", "dump"}

# Coleção explícita dos módulos Python públicos executáveis cobertos pelos
# testes de privacidade/segurança. `.streamlit/config.toml` é coberto à
# parte (não é Python) nos testes dedicados ao final da classe.
PUBLIC_PYTHON_MODULES: tuple[tuple[str, Path], ...] = (
    ("streamlit_app.py", APP_PATH),
    ("src/inferencia.py", SRC / "inferencia.py"),
    ("src/textos_aplicacao.py", TEXTOS_PATH),
    ("src/graficos_publicos.py", SRC / "graficos_publicos.py"),
    ("src/narrativa_publica.py", SRC / "narrativa_publica.py"),
    ("src/calculadoras_indicadores.py", SRC / "calculadoras_indicadores.py"),
)


def _parse(path: Path) -> tuple[str, ast.AST]:
    codigo = path.read_text(encoding="utf-8")
    return codigo, ast.parse(codigo)


def _iter_calls(tree, attrs):
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in attrs:
            yield node


def _iter_open_calls(tree):
    """Chamadas a `open(...)` (builtin) ou `<algo>.open(...)` (ex.:
    `Path.open`)."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name) and node.func.id == "open":
            yield node
        elif isinstance(node.func, ast.Attribute) and node.func.attr == "open":
            yield node


_READ_ONLY_MODES = frozenset({"r", "rt", "rb"})


def _open_call_is_unsafe(node) -> bool:
    """Classifica uma chamada `open()`/`<algo>.open()` como insegura sempre
    que não for possível comprovar estaticamente que é somente leitura.
    Não resolve fluxo de variáveis: qualquer argumento de modo que não seja
    uma string literal (constante) já é insegura.

    Regra conservadora:
    - sem argumento de modo: segura (o padrão do Python é `'r'`);
    - modo posicional **e** por keyword ao mesmo tempo, ou mais de um
      argumento `mode=`: inseguro (duplicado/ambíguo);
    - modo presente mas vindo de variável, expressão, chamada ou f-string
      (qualquer nó que não seja `ast.Constant` de `str`): inseguro;
    - modo é uma string constante: seguro apenas se for exatamente `'r'`,
      `'rt'` ou `'rb'`; qualquer outro valor (contendo `w`, `a`, `x` ou
      `+`, ou qualquer string não reconhecida) é inseguro.

    Para a forma de método (`<algo>.open(...)`, ex.: `Path.open`), o modo é
    o primeiro argumento posicional (índice 0, pois `self` é implícito);
    para o builtin `open(arquivo, modo, ...)`, é o segundo (índice 1)."""
    eh_metodo = isinstance(node.func, ast.Attribute)
    indice_modo_posicional = 0 if eh_metodo else 1

    modo_posicional = (node.args[indice_modo_posicional]
                       if len(node.args) > indice_modo_posicional else None)
    modos_keyword = [kw.value for kw in node.keywords if kw.arg == "mode"]

    if (modo_posicional is not None and modos_keyword) or len(modos_keyword) > 1:
        return True  # argumento de modo duplicado/ambíguo

    modo_node = modo_posicional if modo_posicional is not None else (
        modos_keyword[0] if modos_keyword else None)

    if modo_node is None:
        return False  # sem argumento de modo: leitura por padrão

    if not (isinstance(modo_node, ast.Constant) and isinstance(modo_node.value, str)):
        return True  # não é uma constante string comprovada (variável/expressão/chamada/f-string)

    return modo_node.value not in _READ_ONLY_MODES


# Casos adversariais sintéticos (item 1 da correção): cada trecho é
# analisado pelos MESMOS helpers usados sobre os módulos reais.
_OPEN_ADVERSARIAL_CASES = (
    ('open("arquivo.json")', False),
    ('open("arquivo.json", "r")', False),
    ('open("arquivo.json", mode="rb")', False),
    ('mode = "w"\nopen("saida.txt", mode)', True),
    ('mode = "r"\nopen("entrada.txt", mode)', True),  # não é constante comprovada, mesmo "parecendo" leitura
    ('open("saida.txt", "w")', True),
    ('open("saida.txt", mode="a")', True),
    ('open("saida.txt", "r+")', True),
    ('from pathlib import Path\nPath("saida.txt").open("x")', True),
)


def _dict_literal_string_values(tree, nome_variavel):
    for node in ast.walk(tree):
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name) and node.targets[0].id == nome_variavel
                and isinstance(node.value, ast.Dict)):
            return [v.value for v in node.value.values if isinstance(v, ast.Constant) and isinstance(v.value, str)]
    return []


def _nested_dict_literal_string_values(tree, nome_variavel):
    """Como `_dict_literal_string_values`, mas para um dicionário cujos
    VALORES são, por sua vez, dicionários literais (ex.:
    `textos_aplicacao.INDICADORES`) — devolve todas as strings literais de
    todos os sub-dicionários, achatado."""
    valores = []
    for node in ast.walk(tree):
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name) and node.targets[0].id == nome_variavel
                and isinstance(node.value, ast.Dict)):
            for sub in node.value.values:
                if isinstance(sub, ast.Dict):
                    valores.extend(v.value for v in sub.values
                                   if isinstance(v, ast.Constant) and isinstance(v.value, str))
            return valores
    return valores


def _call_string_args(node):
    for arg in list(node.args) + [kw.value for kw in node.keywords]:
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            yield arg.value


def _docstring_constant_ids(tree):
    """IDs (via `id()`) dos nós `Constant` que são docstrings (primeira
    instrução de módulo, classe ou função) — texto editorial, nunca
    executado como referência de caminho."""
    ids = set()
    alvos = [tree] + [n for n in ast.walk(tree)
                      if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
    for alvo in alvos:
        corpo = getattr(alvo, "body", None)
        if (corpo and isinstance(corpo[0], ast.Expr) and isinstance(corpo[0].value, ast.Constant)
                and isinstance(corpo[0].value.value, str)):
            ids.add(id(corpo[0].value))
    return ids


_FORBIDDEN_NETWORK_MODULES = frozenset({
    "requests", "httpx", "urllib", "urllib3", "socket", "aiohttp", "http.client",
})


def _imported_module_names(tree) -> set[str]:
    """Nomes de módulo importados via `ast.Import`/`ast.ImportFrom`,
    incluindo tanto o caminho completo (ex.: `urllib.request`) quanto o
    módulo raiz (ex.: `urllib`) — cobre alias, import direto, `from
    import` e submódulo, independentemente de como o módulo foi
    referenciado no código."""
    nomes: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                nomes.add(alias.name)
                nomes.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            nomes.add(node.module)
            nomes.add(node.module.split(".")[0])
    return nomes


def _forbidden_network_imports(tree) -> set[str]:
    """Interseção entre os módulos importados (caminho completo + raiz) e a
    lista mínima proibida de módulos de rede."""
    return _imported_module_names(tree) & _FORBIDDEN_NETWORK_MODULES


# Casos adversariais sintéticos (item 2 da correção).
_NETWORK_IMPORT_ADVERSARIAL_CASES = (
    ("import requests", True),
    ("import requests as req", True),
    ("from requests import post", True),
    ("from httpx import Client", True),
    ("import urllib.request", True),
    ("from urllib import request", True),
    ("import socket as s", True),
    ("from aiohttp import ClientSession", True),
    ("from http.client import HTTPSConnection", True),
    ("from pathlib import Path", False),
    ("import json", False),
    ("import math", False),
)


def _imports_logging(tree) -> bool:
    """Detecta `import logging`/`from logging import ...` (e submódulos)
    por AST, em vez de busca textual."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name == "logging" or alias.name.startswith("logging.") for alias in node.names):
                return True
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module == "logging" or node.module.startswith("logging."):
                return True
    return False


def _iter_print_calls(tree):
    """Chamadas executáveis a `print(...)`: nome `print` direto (builtin)
    ou `builtins.print(...)` explícito. Como opera sobre a AST, é
    indiferente a espaços, quebras de linha ou formatação — e não reprova
    comentários, strings explicativas nem funções cujo nome apenas contém
    a palavra 'print' (ex.: `printable_result()`), já que nenhum desses
    vira um nó `Call` cujo alvo seja exatamente `print`."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name) and node.func.id == "print":
            yield node
        elif (isinstance(node.func, ast.Attribute) and node.func.attr == "print"
              and isinstance(node.func.value, ast.Name) and node.func.value.id == "builtins"):
            yield node


# Casos adversariais sintéticos (item 3 da correção).
_PRINT_ADVERSARIAL_CASES = (
    ("print(payload)", True),
    ("print (payload)", True),
    ("print(\n    payload\n)", True),
    ("import builtins\nbuiltins.print(payload)", True),
    ("# print(payload)\nx = 1", False),
    ('texto = "print(payload)"', False),
    ("def printable_result():\n    return 1\nprintable_result()", False),
)


def _non_docstring_string_literals(tree):
    """Strings literais do código, excluindo docstrings — usado para
    diferenciar menção editorial (aceitável em docstring, ex.: 'nunca
    acessa DATATHON/') de uso executável real (literal em qualquer outro
    lugar, ex.: argumento de `Path`/`open`)."""
    docstrings = _docstring_constant_ids(tree)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstrings:
            yield node.value


class PrivacyAndSecurityTests(unittest.TestCase):
    """Cobre `streamlit_app.py`, `src/inferencia.py` e
    `src/textos_aplicacao.py` (`PUBLIC_PYTHON_MODULES`) e, separadamente,
    `.streamlit/config.toml`. Usa AST para comportamento executável
    (chamadas de escrita, rede, exceção) e restringe a análise textual a
    conteúdo editorial específico (rótulos de widgets, dicionários de
    texto) — nunca ao arquivo inteiro — para não confundir prosa legítima
    com um campo de entrada real."""

    @classmethod
    def setUpClass(cls):
        cls.modulos = [(nome, caminho, *_parse(caminho)) for nome, caminho in PUBLIC_PYTHON_MODULES]

    def test_nenhum_file_uploader(self):
        for nome, caminho, codigo, arvore in self.modulos:
            with self.subTest(modulo=nome):
                self.assertEqual(list(_iter_calls(arvore, {"file_uploader"})), [])
                self.assertNotIn("file_uploader", codigo)

    def test_nenhum_campo_de_entrada_pede_ra_nome_ou_identificador_pessoal(self):
        """Cobre os rótulos/ajudas efetivamente usados nos widgets: os
        literais passados diretamente a `st.text_input`/`st.selectbox` em
        `streamlit_app.py` e o dicionário `INDICADORES` (sigla/nome/definição/
        etc.) de `src/textos_aplicacao.py`, de onde os rótulos e ajudas do
        formulário são efetivamente montados."""
        codigo_app, arvore_app = _parse(APP_PATH)
        codigo_textos, arvore_textos = _parse(TEXTOS_PATH)
        rotulos = _nested_dict_literal_string_values(arvore_textos, "INDICADORES")
        for node in _iter_calls(arvore_app, _WIDGET_ATTRS):
            rotulos.extend(_call_string_args(node))
        self.assertTrue(rotulos, "nenhum rótulo de widget encontrado — verificação não é efetiva")
        for texto in rotulos:
            self.assertIsNone(_FORBIDDEN_FIELD_WORDS.search(texto),
                              f"campo de entrada com texto suspeito: {texto!r}")

    def test_contrato_de_campos_nunca_inclui_identificador_pessoal(self):
        """Mesma proibição, agora sobre o contrato de campos de
        `src/inferencia.py` (`FEATURES`), independente da interface —
        cobre o módulo que não tem widgets próprios."""
        for campo in inf.FEATURES:
            self.assertIsNone(_FORBIDDEN_FIELD_WORDS.search(campo), f"campo suspeito no contrato: {campo!r}")

    def test_nenhuma_referencia_executavel_a_pastas_privadas(self):
        """Menções editoriais em docstring são aceitas; qualquer referência
        **fora** de docstring — ou seja, um literal potencialmente usado
        para montar um caminho de verdade — reprova o teste. Cobre também
        `pesquisa_challenger_v2` (arquivada fora do repositório; a
        aplicação pública nunca deve depender dela)."""
        for nome, caminho, codigo, arvore in self.modulos:
            with self.subTest(modulo=nome):
                literais = list(_non_docstring_string_literals(arvore))
                for pasta in ("DATATHON", "local_data", "local_recovery", "pesquisa_challenger_v2"):
                    self.assertFalse(any(pasta in literal for literal in literais),
                                     f"{nome} referencia {pasta} fora de um docstring")

    def test_nenhuma_persistencia_de_entradas_em_arquivo(self):
        """Comportamento executável, via AST: qualquer chamada
        `.write_text(`/`.write_bytes(`/`.write(`/`.to_csv(`/`.to_json(`/
        `.dump(` é tratada como persistência proibida."""
        for nome, caminho, codigo, arvore in self.modulos:
            with self.subTest(modulo=nome):
                escritas = list(_iter_calls(arvore, _WRITE_METHOD_ATTRS))
                self.assertEqual(escritas, [], f"{nome} contém chamada(s) de escrita/persistência")

    def test_nenhum_open_em_modo_de_escrita_acrescimo_ou_atualizacao(self):
        for nome, caminho, codigo, arvore in self.modulos:
            with self.subTest(modulo=nome):
                for node in _iter_open_calls(arvore):
                    self.assertFalse(_open_call_is_unsafe(node), f"{nome}: open() inseguro detectado")

        for trecho, deve_ser_inseguro in _OPEN_ADVERSARIAL_CASES:
            with self.subTest(caso=trecho):
                arvore_sintetica = ast.parse(trecho)
                chamadas = list(_iter_open_calls(arvore_sintetica))
                self.assertTrue(chamadas, f"nenhuma chamada open() encontrada em: {trecho!r}")
                inseguro = any(_open_call_is_unsafe(no) for no in chamadas)
                self.assertEqual(inseguro, deve_ser_inseguro, f"classificação incorreta para: {trecho!r}")

    def test_nenhum_banco_de_dados(self):
        for nome, caminho, codigo, arvore in self.modulos:
            with self.subTest(modulo=nome):
                for termo in ("sqlite3", "sqlite", "sqlalchemy", "pymongo", "psycopg", "redis"):
                    self.assertNotIn(termo, codigo.lower())

    def test_nenhuma_chamada_http_ou_socket_externa(self):
        for nome, caminho, codigo, arvore in self.modulos:
            with self.subTest(modulo=nome):
                proibidos = _forbidden_network_imports(arvore)
                self.assertEqual(proibidos, set(), f"{nome} importa módulo(s) de rede: {proibidos}")

        for trecho, deve_ter_proibido in _NETWORK_IMPORT_ADVERSARIAL_CASES:
            with self.subTest(caso=trecho):
                arvore_sintetica = ast.parse(trecho)
                proibidos = _forbidden_network_imports(arvore_sintetica)
                if deve_ter_proibido:
                    self.assertTrue(proibidos, f"deveria detectar import de rede em: {trecho!r}")
                else:
                    self.assertEqual(proibidos, set(), f"falso positivo em: {trecho!r}")

    def test_nenhum_analytics(self):
        for nome, caminho, codigo, arvore in self.modulos:
            with self.subTest(modulo=nome):
                for termo in ("analytics", "gtag", "mixpanel", "segment.io", "google-analytics"):
                    self.assertNotIn(termo, codigo.lower())
        config = tomllib.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        self.assertFalse(config.get("browser", {}).get("gatherUsageStats", True))

    def test_nenhum_logging_ou_print_de_payload(self):
        for nome, caminho, codigo, arvore in self.modulos:
            with self.subTest(modulo=nome):
                self.assertEqual(list(_iter_print_calls(arvore)), [], f"{nome} chama print() executável")
                self.assertFalse(_imports_logging(arvore), f"{nome} importa logging")

        for trecho, deve_detectar in _PRINT_ADVERSARIAL_CASES:
            with self.subTest(caso=trecho):
                arvore_sintetica = ast.parse(trecho)
                achados = list(_iter_print_calls(arvore_sintetica))
                self.assertEqual(bool(achados), deve_detectar, f"classificação incorreta para: {trecho!r}")

    def test_nenhum_st_exception(self):
        codigo_app, arvore_app = _parse(APP_PATH)
        self.assertNotIn("st.exception", codigo_app)
        self.assertEqual(list(_iter_calls(arvore_app, {"exception"})), [])

    def test_item20_nenhum_unsafe_allow_html(self):
        """`unsafe_allow_html` só pode aparecer uma vez em toda a aplicação
        pública: para injetar o CSS local e estático de
        `assets/styles/app.css`, junto com o pequeno bloco de variáveis
        `:root` do modo claro/escuro (revisão de identidade visual,
        25/09/2026) — nunca conteúdo de formulário. Em qualquer outro
        módulo, ou mais de uma vez em `streamlit_app.py`, seria um sinal de
        HTML dinâmico — proibido."""
        for nome, caminho, codigo, arvore in self.modulos:
            with self.subTest(modulo=nome):
                ocorrencias = codigo.count("unsafe_allow_html")
                if nome == "streamlit_app.py":
                    self.assertEqual(ocorrencias, 1, "mais de um uso de unsafe_allow_html em streamlit_app.py")
                    self.assertIn(
                        r'st.markdown(f"<style>\n:root {{\n{variaveis}\n}}\n{_carregar_css()}</style>", '
                        r'unsafe_allow_html=True)',
                        codigo,
                    )
                else:
                    self.assertEqual(ocorrencias, 0)

    def test_nenhum_cache_de_dados_das_entradas(self):
        codigo_app, _ = _parse(APP_PATH)
        self.assertNotIn("cache_data", codigo_app)
        self.assertIn("cache_resource", codigo_app)

    def test_item21_nenhum_segredo_hardcoded(self):
        for nome, caminho, codigo, arvore in self.modulos:
            with self.subTest(modulo=nome):
                self.assertIsNone(_SECRET_PATTERN.search(codigo))

    def test_item21_nenhum_caminho_absoluto_local(self):
        for nome, caminho, codigo, arvore in self.modulos:
            with self.subTest(modulo=nome):
                self.assertIsNone(_ABSOLUTE_PATH_PATTERN.search(codigo))

    def test_nenhum_hash_completo_exposto(self):
        for nome, caminho, codigo, arvore in self.modulos:
            with self.subTest(modulo=nome):
                self.assertEqual(re.findall(r"\b[0-9a-f]{64}\b", codigo.lower()), [])

    def test_exemplo_e_rotulado_como_sintetico(self):
        codigo_app, _ = _parse(APP_PATH)
        self.assertIn("sintétic", codigo_app.lower())
        self.assertIn("não correspondem a nenhum(a) estudante real", codigo_app.lower())

    def test_nenhuma_referencia_a_ferramentas_assistentes_ou_llms(self):
        """Restrição adicional da subetapa: nenhum dos módulos públicos ou
        do `.streamlit/config.toml` pode mencionar ferramentas de IA,
        assistentes ou modelos de linguagem."""
        termos = ("claude", "anthropic", "chatgpt", "openai", "copilot", "gemini",
                 "llm", "large language model", "assistente de ia", "ia generativa")
        alvos = [(nome, codigo) for nome, caminho, codigo, arvore in self.modulos]
        alvos.append((".streamlit/config.toml", CONFIG_PATH.read_text(encoding="utf-8")))
        for nome, codigo in alvos:
            with self.subTest(modulo=nome):
                codigo_lower = codigo.lower()
                for termo in termos:
                    self.assertNotIn(termo, codigo_lower)

    def test_config_toml_sem_segredo_endpoint_externo_ou_caminho_absoluto(self):
        """`.streamlit/config.toml`: TOML válido, `gatherUsageStats`
        desabilitado, sem segredo, sem porta fixa, sem caminho absoluto e
        sem endpoint externo referenciado."""
        texto = CONFIG_PATH.read_text(encoding="utf-8")
        config = tomllib.loads(texto)  # levanta TOMLDecodeError se inválido
        self.assertIsInstance(config, dict)
        self.assertFalse(config.get("browser", {}).get("gatherUsageStats", True))
        self.assertNotIn("port", config.get("server", {}))
        self.assertIsNone(_SECRET_PATTERN.search(texto))
        self.assertIsNone(_ABSOLUTE_PATH_PATTERN.search(texto))
        self.assertIsNone(re.search(r"(?i)https?://", texto), "endpoint externo referenciado no config.toml")


# --------------------------------------------------------------------------- #
# Portabilidade                                                               #
# --------------------------------------------------------------------------- #

class PortabilityTests(unittest.TestCase):
    def test_usa_pathlib_e_nao_separador_hardcoded(self):
        for caminho in (APP_PATH, SRC / "inferencia.py", TEXTOS_PATH):
            codigo = caminho.read_text(encoding="utf-8")
            self.assertNotIn("\\\\", codigo)  # nenhum separador Windows hardcoded

    def test_localizacao_da_raiz_a_partir_de_pontos_diferentes(self):
        pontos_de_partida = [ROOT, SRC, ROOT / "tests", ROOT / "docs",
                             ROOT / "reports" / "figures"]
        for ponto in pontos_de_partida:
            with self.subTest(ponto=ponto.name or str(ponto)):
                self.assertEqual(inf.find_project_root(ponto), ROOT)

    def test_item23_execucao_com_copia_publica_minima_em_diretorio_temporario(self):
        """Confirma que a aplicação inicializa apenas com os arquivos
        públicos exigidos, sem nenhuma pasta privada — inclusive sem
        `pesquisa_challenger_v2`, que hoje nem existe mais dentro do
        repositório (arquivada externamente)."""
        tmp = Path(tempfile.mkdtemp(prefix="streamlit_portabilidade_"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        for relativo in inf.PUBLIC_REQUIRED_PATHS:
            destino = tmp / relativo
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relativo, destino)
        contexto = inf.prepare_application(root=tmp)
        self.assertAlmostEqual(contexto.validation.threshold, official_threshold(), places=12)
        for pasta in ("DATATHON", "local_data", "local_recovery", "pesquisa_challenger_v2"):
            self.assertFalse((tmp / pasta).exists())

    def test_item37_aplicacao_completa_funciona_em_copia_publica_isolada(self):
        """Amplia a cobertura de portabilidade: em vez de exercitar
        inferência (`test_item23...`) e painel (`PanoramaTests.
        test_item30...`) separadamente, roda a APLICAÇÃO COMPLETA (cinco
        abas, painel "Panorama e resultados" e "Avaliar um caso" com o
        exemplo sintético) dentro de uma ÚNICA cópia pública isolada —
        sem nenhuma pasta privada — e com o processo filho rodando a
        partir de um diretório de trabalho DIFERENTE da própria cópia
        (reaproveita `_montar_copia_publica_isolada`/
        `_rodar_driver_em_subprocesso`, definidos uma única vez para esta
        correção e usados também por
        `PanoramaTests.test_item33_painel_indisponivel_apresenta_erro_controlado_na_interface`)."""
        tmp = Path(tempfile.mkdtemp(prefix="app_completa_portabilidade_"))
        self.addCleanup(_limpar_copia_publica_isolada_com_retentativas, tmp)
        _montar_copia_publica_isolada(tmp)
        for pasta in ("DATATHON", "local_data", "local_recovery", "pesquisa_challenger_v2"):
            self.assertFalse((tmp / pasta).exists())

        outro_cwd = Path(tempfile.mkdtemp(prefix="app_completa_cwd_alternativo_"))
        self.addCleanup(shutil.rmtree, outro_cwd, ignore_errors=True)

        resultado = _rodar_driver_em_subprocesso(self, tmp, _DRIVER_APP_COMPLETA, cwd=outro_cwd)

        self.assertEqual(resultado["excecoes"], [])
        self.assertEqual(
            resultado["abas"],
            ["Início", "Panorama e resultados", "Avaliar um caso", "Entenda os indicadores"],
        )
        # Exatamente 1 imagem em toda a aplicação: o logo oficial no
        # cabeçalho (revisão de identidade visual, 25/09/2026) — o painel
        # "Panorama e resultados" não exibe mais nenhum PNG histórico
        # (refatoração editorial, item 2), e a curva agregada que antes
        # vivia em "Modelo e limitações" saiu junto com a aba (decisão de
        # produto, 25/09/2026).
        self.assertEqual(resultado["total_imagens"], 1)
        self.assertEqual(len(resultado["metricas"]), 1)
        self.assertRegex(resultado["metricas"][0], r"^\d+([.,]\d+)?%$")
        # Exatamente um alerta de resultado (sucesso ou aviso) além da base
        # fixa da aba "Início" (1 sucesso + 1 aviso, sempre presentes).
        self.assertEqual(resultado["sucessos"] + resultado["avisos"], _BASE_SUCCESS + _BASE_WARNING + 1)

    def test_independente_do_diretorio_de_trabalho_atual(self):
        outro_cwd = Path(tempfile.mkdtemp(prefix="cwd_alternativo_"))
        self.addCleanup(shutil.rmtree, outro_cwd, ignore_errors=True)
        cwd_original = Path.cwd()
        try:
            import os
            os.chdir(outro_cwd)
            contexto = inf.prepare_application(root=ROOT)
            self.assertAlmostEqual(contexto.validation.threshold, official_threshold(), places=12)
        finally:
            import os
            os.chdir(cwd_original)

    def test_configuracao_toml_e_valida_e_sem_porta_fixa(self):
        config = tomllib.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        self.assertIn("theme", config)
        self.assertIn("browser", config)
        self.assertNotIn("port", config.get("server", {}))

    def test_repositorio_nao_depende_da_pesquisa_arquivada(self):
        """`pesquisa_challenger_v2/` foi movida para fora do repositório;
        nenhum arquivo público pode assumir sua presença."""
        self.assertFalse((ROOT / "pesquisa_challenger_v2").exists())


# --------------------------------------------------------------------------- #
# "Avaliar um caso" — identificação/contexto, calculadoras e relatório       #
# (revisão editorial, 25/09/2026)                                           #
# --------------------------------------------------------------------------- #

def _estado_sintetico(**overrides) -> dict:
    """`estado` sintético no mesmo formato de `st.session_state["caso_resultado"]`
    (ver `streamlit_app._tab_avaliar`), para testar `_gerar_relatorio_html`
    diretamente, sem depender de introspecção de bytes de `st.download_button`
    no `AppTest` (não exposta de forma confiável pela API de testes)."""
    base = {
        "resultado": inf.InferenceResult(probability=0.42, threshold=0.30, is_risk=True),
        "entradas": dict(PAYLOAD_ALTO_RISCO),
        "contexto": {"identificacao": "", "idade": "", "sexo": "Não informado"},
        "modo_defasagem": textos.ROTULO_MODO_DEFASAGEM_DIRETO,
        "modo_ida": textos.ROTULO_MODO_IDA_DIRETO,
        "modo_iaa": textos.ROTULO_MODO_IAA_DIRETO,
        "notas_ida": {"matematica": "", "portugues": "", "ingles": ""},
        "ipp_contexto": "",
        "fase_ideal": "",
        "snapshot": {},
        "gerado_em": __import__("datetime").datetime(2026, 9, 25, 10, 30, 0),
    }
    base.update(overrides)
    return base


class AvaliarUmCasoIdentificacaoEContextoTests(unittest.TestCase):
    """Parte 4 + revisão de identidade visual (25/09/2026, Etapa 1): campos
    de identificação/idade/sexo — todos opcionais, nunca enviados ao
    modelo. `campo_identificacao_caso` usa o rótulo "Iniciais ou código
    interno" (não mais "Identificação do caso (opcional)")."""

    def test_campos_de_identificacao_idade_e_sexo_existem_e_comecam_pendentes(self):
        at = _novo_app()
        campo_id = _by_key(at.text_input, "campo_identificacao_caso")
        campo_idade = _by_key(at.text_input, "campo_idade_contexto")
        campo_sexo = _by_key(at.selectbox, "campo_sexo_contexto")
        self.assertEqual(campo_id.value, "")
        self.assertEqual(campo_idade.value, "")
        self.assertEqual(campo_sexo.value, "Selecione")
        self.assertTrue(_button(at, "Gerar estimativa").disabled)

    def test_rotulo_de_identificacao_e_iniciais_ou_codigo_interno(self):
        """Etapa 1, item 1: rótulo exato "Iniciais ou código interno" —
        nunca "identificação do caso" nem "nome completo"."""
        self.assertEqual(textos.ROTULO_IDENTIFICACAO_CASO, "Nome ou identificação interna *")
        at = _novo_app()
        campo = _by_key(at.text_input, "campo_identificacao_caso")
        self.assertEqual(campo.label, "Nome ou identificação interna *")

    def test_campo_de_idade_nao_e_um_preditor_oficial(self):
        chaves_oficiais = {f"campo_{c}" for c in inf.FEATURES}
        self.assertNotIn("campo_idade_contexto", chaves_oficiais)
        self.assertNotIn("idade", inf.FEATURES)

    def test_identificacao_idade_e_sexo_nao_alteram_a_estimativa(self):
        """Etapa 1, item 2: mantendo os sete indicadores iguais, variar
        identificação, idade e sexo não muda a estimativa."""
        contexto = inf.prepare_application(root=ROOT)
        esperado = inf.run_inference(contexto, PAYLOAD_BAIXO_RISCO)

        at = _novo_app()
        _by_key(at.text_input, "campo_identificacao_caso").set_value("caso-teste-001")
        _by_key(at.text_input, "campo_idade_contexto").set_value("15")
        _by_key(at.selectbox, "campo_sexo_contexto").select("Feminino")
        at = _preencher_e_enviar(at, PAYLOAD_BAIXO_RISCO)
        percentual = float(at.metric[0].value.rstrip("%").replace(",", "."))
        self.assertAlmostEqual(percentual, esperado.probability * 100, places=1)

    def test_idade_diferente_com_mesmos_sete_indicadores_produz_mesma_estimativa(self):
        at_a = _novo_app()
        _by_key(at_a.text_input, "campo_idade_contexto").set_value("9")
        at_a = _preencher_e_enviar(at_a, PAYLOAD_ALTO_RISCO)
        percentual_a = float(at_a.metric[0].value.rstrip("%").replace(",", "."))

        at_b = _novo_app()
        _by_key(at_b.text_input, "campo_idade_contexto").set_value("17")
        at_b = _preencher_e_enviar(at_b, PAYLOAD_ALTO_RISCO)
        percentual_b = float(at_b.metric[0].value.rstrip("%").replace(",", "."))

        self.assertAlmostEqual(percentual_a, percentual_b, places=6)

    def test_idade_sugere_mas_nao_confirma_fase_ideal(self):
        at = _novo_app()
        _by_key(at.text_input, "campo_idade_contexto").set_value("10")
        at.run(timeout=30)
        self.assertIn("Fase 2", _texto_total(at))
        self.assertEqual(_by_key(at.selectbox, "campo_fase_ideal_calculo").value, "")

    def test_avisos_de_privacidade_da_ficha_presentes(self):
        texto = _texto_total(_novo_app())
        self.assertIn(textos.AVISO_PRIVACIDADE_AVALIAR, texto)
        self.assertIn(textos.AVISO_USO_RESPONSAVEL_CURTO, texto)
        self.assertIn(textos.AVISO_IDADE_NAO_AUTOMATIZA_CALCULO, texto)

    def test_avisos_discretos_nao_sao_caixas_coloridas_no_formulario(self):
        """Etapa 1, item 4: os avisos de privacidade/uso responsável do
        formulário aparecem como `st.caption` discreto, não como
        `st.info`/`st.success`/`st.warning`."""
        codigo, _ = _parse(APP_PATH)
        trecho_tab_avaliar = codigo[codigo.index("def _tab_avaliar("):codigo.index("def _tab_indicadores(")]
        self.assertIn("st.caption(textos.AVISO_PRIVACIDADE_AVALIAR)", trecho_tab_avaliar)
        self.assertNotIn("st.info(", trecho_tab_avaliar)
        self.assertNotIn("st.success(", trecho_tab_avaliar)
        self.assertNotIn("st.warning(", trecho_tab_avaliar)


class AvaliarUmCasoCalculadorasTests(unittest.TestCase):
    """Calculadoras de defasagem/IAN/IDA/IAA/INDE com fórmula oficial
    confirmada (revisão de 25/09/2026 — releitura de `PEDE_ Pontos
    importantes.docx`, incluindo as imagens/tabelas incorporadas) e ausência
    de calculadora para os indicadores sem fórmula fechada (IEG/IPS/IPV)."""

    def test_notas_de_indicador_sem_calculadora_presentes(self):
        texto = _texto_total(_novo_app())
        self.assertIn(textos.NOTA_IEG_SEM_CALCULO, texto)
        self.assertIn(textos.NOTA_IPS_SEM_CALCULO, texto)
        self.assertIn(textos.NOTA_IPV_SEM_CALCULO, texto)

    def test_modo_calculado_deriva_defasagem_da_fase_e_fase_ideal(self):
        at = _novo_app()
        _by_key(at.selectbox, "campo_fase_origem").select("5")
        _by_key(at.radio, "modo_defasagem").set_value(textos.ROTULO_MODO_DEFASAGEM_CALCULADO)
        at.run(timeout=30)
        _by_key(at.selectbox, "campo_fase_ideal_calculo").select("2")
        at.run(timeout=30)
        self.assertIn("fase ideal:** 3", _texto_total(at))  # 5 - 2 = 3

    def test_modo_calculado_nao_envia_fase_ideal_ao_modelo(self):
        contexto = inf.prepare_application(root=ROOT)
        at = _novo_app()
        _by_key(at.selectbox, "campo_fase_origem").select("5")
        _by_key(at.radio, "modo_defasagem").set_value(textos.ROTULO_MODO_DEFASAGEM_CALCULADO)
        at.run(timeout=30)
        _by_key(at.selectbox, "campo_fase_ideal_calculo").select("2")
        for campo in ("ida", "ieg", "iaa", "ips", "ipv"):
            _by_key(at.text_input, f"campo_{campo}").set_value(PAYLOAD_ALTO_RISCO[campo])
        _by_key(at.text_input, "campo_identificacao_caso").set_value("caso-teste")
        _by_key(at.text_input, "campo_idade_contexto").set_value("14")
        _by_key(at.selectbox, "campo_sexo_contexto").select("Feminino")
        _by_key(at.text_input, "campo_ipp_contexto").set_value("7")
        at.run(timeout=30)
        _button(at, "Gerar estimativa").click()
        at.run(timeout=30)
        self.assertEqual(list(at.exception), [])
        esperado = inf.run_inference(contexto, dict(PAYLOAD_ALTO_RISCO, fase_origem="5", defasagem_origem="3"))
        percentual = float(at.metric[0].value.rstrip("%").replace(",", "."))
        self.assertAlmostEqual(percentual, esperado.probability * 100, places=1)

    def test_sugestao_de_fase_ideal_por_idade_aparece_no_modo_calculado(self):
        at = _novo_app()
        _by_key(at.text_input, "campo_idade_contexto").set_value("12")
        _by_key(at.radio, "modo_defasagem").set_value(textos.ROTULO_MODO_DEFASAGEM_CALCULADO)
        at.run(timeout=30)
        texto = _texto_total(at)
        self.assertIn("Fase 3", texto)
        self.assertIn(textos.AVISO_SUGESTAO_FASE_IDEAL, texto)

    def test_idade_ambigua_8_anos_mostra_as_duas_fases_candidatas(self):
        at = _novo_app()
        _by_key(at.text_input, "campo_idade_contexto").set_value("8")
        _by_key(at.radio, "modo_defasagem").set_value(textos.ROTULO_MODO_DEFASAGEM_CALCULADO)
        at.run(timeout=30)
        texto = _texto_total(at)
        self.assertIn("Alfa", texto)
        self.assertIn("Fase 1", texto)

    def test_sugestao_nunca_preenche_a_fase_ideal_automaticamente(self):
        """A fase ideal permanece em branco mesmo com sugestão exibida —
        exige seleção explícita (Parte 2, item 3: "usuário deverá confirmar
        ou selecionar")."""
        at = _novo_app()
        _by_key(at.text_input, "campo_idade_contexto").set_value("12")
        _by_key(at.radio, "modo_defasagem").set_value(textos.ROTULO_MODO_DEFASAGEM_CALCULADO)
        at.run(timeout=30)
        campo_fase_ideal = _by_key(at.selectbox, "campo_fase_ideal_calculo")
        self.assertEqual(campo_fase_ideal.value, "")

    def test_modo_calculado_ida_usa_media_das_tres_notas(self):
        at = _novo_app()
        _by_key(at.radio, "modo_ida").set_value(textos.ROTULO_MODO_IDA_CALCULADO)
        at.run(timeout=30)
        _by_key(at.text_input, "campo_nota_matematica").set_value("6")
        _by_key(at.text_input, "campo_nota_portugues").set_value("7")
        _by_key(at.text_input, "campo_nota_ingles").set_value("8")
        at.run(timeout=30)
        self.assertIn("IDA calculado:** 7.00", _texto_total(at))

    def test_modo_calculado_ida_produz_mesma_estimativa_que_ida_institucional_equivalente(self):
        contexto = inf.prepare_application(root=ROOT)
        at = _novo_app()
        _by_key(at.radio, "modo_ida").set_value(textos.ROTULO_MODO_IDA_CALCULADO)
        at.run(timeout=30)
        _by_key(at.text_input, "campo_nota_matematica").set_value("6")
        _by_key(at.text_input, "campo_nota_portugues").set_value("6")
        _by_key(at.text_input, "campo_nota_ingles").set_value("6")
        for campo in ("ieg", "iaa", "ips", "ipv"):
            _by_key(at.text_input, f"campo_{campo}").set_value(PAYLOAD_BAIXO_RISCO[campo])
        _by_key(at.selectbox, "campo_fase_origem").select(PAYLOAD_BAIXO_RISCO["fase_origem"])
        at.run(timeout=30)
        _by_key(at.selectbox, "campo_fase_ideal_calculo").select(PAYLOAD_BAIXO_RISCO["fase_origem"])
        _by_key(at.text_input, "campo_identificacao_caso").set_value("caso-teste")
        _by_key(at.text_input, "campo_idade_contexto").set_value("15")
        _by_key(at.selectbox, "campo_sexo_contexto").select("Feminino")
        _by_key(at.text_input, "campo_ipp_contexto").set_value("7")
        at.run(timeout=30)
        _button(at, "Gerar estimativa").click()
        at.run(timeout=30)
        self.assertEqual(list(at.exception), [])
        esperado = inf.run_inference(contexto, dict(PAYLOAD_BAIXO_RISCO, ida="6.0"))
        percentual = float(at.metric[0].value.rstrip("%").replace(",", "."))
        self.assertAlmostEqual(percentual, esperado.probability * 100, places=1)

    def test_ida_calculadora_nao_aceita_nota_ausente(self):
        at = _novo_app()
        _by_key(at.radio, "modo_ida").set_value(textos.ROTULO_MODO_IDA_CALCULADO)
        at.run(timeout=30)
        _by_key(at.text_input, "campo_nota_matematica").set_value("6")
        _by_key(at.text_input, "campo_nota_portugues").set_value("7")
        at.run(timeout=30)
        self.assertIn("IDA calculado:** —", _texto_total(at))

    def test_nota_cem_e_rejeitada_com_erro_proximo_ao_campo(self):
        """Regressão: uma nota bruta fora de 0–10 (ex.: 100) não pode ser
        aceita silenciosamente nem só bloquear via erro genérico do IDA
        resultante — precisa de mensagem própria, perto do campo."""
        at = _novo_app()
        _by_key(at.radio, "modo_ida").set_value(textos.ROTULO_MODO_IDA_CALCULADO)
        at.run(timeout=30)
        _by_key(at.text_input, "campo_nota_matematica").set_value("100")
        _by_key(at.text_input, "campo_nota_portugues").set_value("7")
        _by_key(at.text_input, "campo_nota_ingles").set_value("7")
        at.run(timeout=30)
        texto = _texto_total(at)
        self.assertIn("IDA calculado:** —", texto)
        self.assertIn("máximo é 10", texto)

    def test_nota_negativa_e_rejeitada(self):
        at = _novo_app()
        _by_key(at.radio, "modo_ida").set_value(textos.ROTULO_MODO_IDA_CALCULADO)
        at.run(timeout=30)
        _by_key(at.text_input, "campo_nota_matematica").set_value("-1")
        _by_key(at.text_input, "campo_nota_portugues").set_value("7")
        _by_key(at.text_input, "campo_nota_ingles").set_value("7")
        at.run(timeout=30)
        self.assertIn("IDA calculado:** —", _texto_total(at))

    def test_modo_calculado_iaa_soma_pontos_da_tabela_40(self):
        at = _novo_app()
        _by_key(at.selectbox, "campo_fase_origem").select("1")  # grupo 0-2
        _by_key(at.radio, "modo_iaa").set_value(textos.ROTULO_MODO_IAA_CALCULADO)
        at.run(timeout=30)
        for i in range(1, 7):
            _by_key(at.selectbox, f"campo_iaa_pergunta_{i}").select("A")
        at.run(timeout=30)
        self.assertIn("IAA calculado:** 10.00", _texto_total(at))

    def test_iaa_grupo_3_a_8_nao_oferece_opcao_d_para_fases_0_a_2(self):
        at = _novo_app()
        _by_key(at.selectbox, "campo_fase_origem").select("1")
        _by_key(at.radio, "modo_iaa").set_value(textos.ROTULO_MODO_IAA_CALCULADO)
        at.run(timeout=30)
        opcoes = _by_key(at.selectbox, "campo_iaa_pergunta_1").options
        self.assertEqual(opcoes, ["Selecione", "A", "B", "C"])

    def test_inde_calculado_quando_todos_os_componentes_disponiveis(self):
        at = _novo_app()
        _by_key(at.selectbox, "campo_fase_origem").select("3")
        at.run(timeout=30)  # o campo de IPP só existe depois que a fase está selecionada
        _by_key(at.selectbox, "campo_fase_ideal_calculo").select("3")  # IAN=10
        for campo, valor in (("ida", "7"), ("ieg", "8"), ("iaa", "9"), ("ips", "6"), ("ipv", "8")):
            _by_key(at.text_input, f"campo_{campo}").set_value(valor)
        _by_key(at.text_input, "campo_ipp_contexto").set_value("7")
        at.run(timeout=30)
        texto = _texto_total(at)
        esperado = 10 * .1 + 7 * .2 + 8 * .2 + 9 * .1 + 6 * .1 + 7 * .1 + 8 * .2
        self.assertIn(f"INDE calculado:** {esperado:.2f}", texto)

    def test_inde_nao_calculado_com_ipp_ausente(self):
        at = _novo_app()
        _by_key(at.selectbox, "campo_fase_origem").select("3")
        at.run(timeout=30)
        _by_key(at.selectbox, "campo_fase_ideal_calculo").select("3")
        for campo, valor in (("ida", "7"), ("ieg", "8"), ("iaa", "9"), ("ips", "6"), ("ipv", "8")):
            _by_key(at.text_input, f"campo_{campo}").set_value(valor)
        at.run(timeout=30)
        texto = _texto_total(at)
        self.assertIn("INDE não calculado", texto)
        self.assertIn("IPP", texto)

    def test_ipp_e_inde_nunca_sao_preditores_novos(self):
        chaves_oficiais = {f"campo_{c}" for c in inf.FEATURES}
        self.assertNotIn("campo_ipp_contexto", chaves_oficiais)
        self.assertNotIn("ipp", inf.FEATURES)
        self.assertNotIn("inde", inf.FEATURES)
        self.assertEqual(len(inf.FEATURES), 7)

    def test_campo_ipp_visivel_fora_do_expander_do_inde(self):
        """Regressão: o IPP é um campo obrigatório para concluir a ficha nas
        fases Alfa–7 — não pode ficar escondido dentro de um `st.expander`
        rotulado "informação complementar", que sugere ser dispensável e
        exige um clique extra para o usuário sequer ver o campo."""
        codigo = APP_PATH.read_text(encoding="utf-8")
        inicio_secao_ipp = codigo.index("def _secao_ipp(")
        fim_secao_ipp = codigo.index("\ndef ", inicio_secao_ipp + 1)
        corpo_secao_ipp = codigo[inicio_secao_ipp:fim_secao_ipp]
        self.assertIn("campo_ipp_contexto", corpo_secao_ipp)
        self.assertNotIn("st.expander", corpo_secao_ipp)

        inicio_secao_inde = codigo.index("def _secao_inde_complementar(")
        fim_secao_inde = codigo.index("\ndef ", inicio_secao_inde + 1)
        corpo_secao_inde = codigo[inicio_secao_inde:fim_secao_inde]
        self.assertNotIn("st.text_input", corpo_secao_inde)  # não recoleta o IPP ali dentro

        at = _novo_app()
        _by_key(at.selectbox, "campo_fase_origem").select("2")
        at.run(timeout=30)
        campo = _by_key(at.text_input, "campo_ipp_contexto")
        self.assertIn("Indicador Psicopedagógico", campo.label)

    def test_inde_nao_e_enviado_ao_modelo(self):
        contexto = inf.prepare_application(root=ROOT)
        esperado = inf.run_inference(contexto, PAYLOAD_BAIXO_RISCO)
        at = _novo_app()
        _by_key(at.selectbox, "campo_fase_origem").select(PAYLOAD_BAIXO_RISCO["fase_origem"])
        at.run(timeout=30)  # o campo de IPP só existe depois que a fase está selecionada
        _by_key(at.text_input, "campo_ipp_contexto").set_value("8")
        at = _preencher_e_enviar(at, PAYLOAD_BAIXO_RISCO)
        percentual = float(at.metric[0].value.rstrip("%").replace(",", "."))
        self.assertAlmostEqual(percentual, esperado.probability * 100, places=1)

    def test_ian_de_contexto_exibido_mas_nao_e_preditor(self):
        at = _preencher_e_enviar(_novo_app(), PAYLOAD_BAIXO_RISCO)  # defasagem_origem="0" -> IAN=10
        texto = _texto_total(at)
        self.assertIn("IAN", texto)
        self.assertIn(textos.EXPLICACAO_CALCULO_IAN, texto)
        self.assertEqual(len(inf.FEATURES), 7)
        self.assertNotIn("ian", inf.FEATURES)


class RelatorioDoCasoTests(unittest.TestCase):
    """Parte 8: relatório individual gerado somente em memória."""

    @classmethod
    def setUpClass(cls):
        import streamlit_app as app_module
        cls.app_module = app_module

    def test_relatorio_indisponivel_antes_de_qualquer_estimativa(self):
        at = _novo_app()
        self.assertEqual(len(at.download_button), 0)

    def test_relatorio_disponivel_apos_estimativa_valida(self):
        at = _preencher_e_enviar(_novo_app(), PAYLOAD_BAIXO_RISCO)
        self.assertEqual(len(at.download_button), 1)
        self.assertIn("Baixar relatório", at.download_button[0].label)

    def test_relatorio_e_html_autocontido_sem_javascript_ou_url_externa(self):
        html_gerado = self.app_module._gerar_relatorio_html(_estado_sintetico())
        self.assertTrue(html_gerado.strip().startswith("<!DOCTYPE html>"))
        self.assertNotIn("<script", html_gerado.lower())
        self.assertNotIn("http://", html_gerado)
        self.assertNotIn("https://", html_gerado)
        self.assertNotIn("javascript:", html_gerado.lower())

    def test_relatorio_escapa_identificacao_contra_injecao(self):
        estado = _estado_sintetico(contexto={"identificacao": "<script>alert(1)</script>", "sexo": "Não informado"})
        html_gerado = self.app_module._gerar_relatorio_html(estado)
        self.assertNotIn("<script>alert(1)</script>", html_gerado)
        self.assertIn("&lt;script&gt;", html_gerado)

    def test_nome_do_arquivo_nunca_usa_a_identificacao(self):
        self.assertNotIn("{identificacao", self.app_module.__dict__.get("RELATORIO_ARQUIVO_NOME", ""))
        self.assertEqual(textos.RELATORIO_ARQUIVO_NOME, "relatorio_acompanhamento.html")
        codigo_app, _ = _parse(APP_PATH)
        self.assertIn("RELATORIO_ARQUIVO_NOME", codigo_app)

    def test_relatorio_contem_estimativa_indicadores_e_orientacao_sem_valores_internos(self):
        html_gerado = self.app_module._gerar_relatorio_html(_estado_sintetico())
        self.assertIn("42.0%", html_gerado)
        self.assertIn(textos.TITULO_ACIMA_DO_PONTO, html_gerado)
        self.assertIn(textos.AVISO_DECISAO_PROFISSIONAIS, html_gerado)
        self.assertIn(textos.RELATORIO_AVISO_DIAGNOSTICO, html_gerado)
        # Palavra isolada (não substring de palavras comuns como
        # "determinante"): checagem por fronteira de palavra, não por
        # `in` cru, que dispararia falso positivo em prosa legítima.
        for termo in ("none", "nan", "null"):
            self.assertIsNone(re.search(rf"\b{termo}\b", html_gerado, re.IGNORECASE),
                              f"termo interno {termo!r} exposto cru no relatório")

    def test_relatorio_nao_afirma_que_sexo_influenciou_o_resultado(self):
        html_gerado = self.app_module._gerar_relatorio_html(
            _estado_sintetico(contexto={"identificacao": "", "sexo": "Feminino"}))
        self.assertNotIn("sexo influenciou", html_gerado.lower())
        self.assertNotIn("por ser do sexo", html_gerado.lower())

    def test_relatorio_gerado_somente_em_memoria(self):
        """Nenhuma chamada de escrita em disco em todo `streamlit_app.py`
        (mesma varredura AST de `test_nenhuma_persistencia_de_entradas_em_arquivo`,
        conferida aqui especificamente para o caminho do relatório)."""
        codigo_app, arvore_app = _parse(APP_PATH)
        self.assertNotIn("open(", codigo_app.replace("st.download_button", ""))
        for atributo in _WRITE_METHOD_ATTRS:
            self.assertEqual(list(_iter_calls(arvore_app, {atributo})), [],
                             f"streamlit_app.py chama .{atributo}(...) — proibido para o relatório em memória")

    def test_nenhum_dado_pessoal_em_mensagem_de_excecao(self):
        """Nenhuma f-string/`.format`/`%` de exceção em `streamlit_app.py`
        interpola `identificacao` ou `contexto_caso` — mensagens de erro
        nunca podem ecoar dado pessoal digitado pelo usuário."""
        codigo_app, arvore_app = _parse(APP_PATH)
        for node in ast.walk(arvore_app):
            if isinstance(node, ast.Raise) and node.exc is not None:
                sub = ast.dump(node.exc)
                self.assertNotIn("identificacao", sub)
                self.assertNotIn("contexto_caso", sub)


# --------------------------------------------------------------------------- #
# Identidade visual — logo, paleta, claro/escuro (revisão de identidade      #
# visual, 25/09/2026)                                                       #
# --------------------------------------------------------------------------- #

LOGO_PATH = ROOT / "assets" / "brand" / "passos-magicos-icon-cor.png"


def _luminancia_relativa(hex_cor: str) -> float:
    hex_cor = hex_cor.lstrip("#")
    r, g, b = (int(hex_cor[i:i + 2], 16) / 255 for i in (0, 2, 4))

    def linear(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * linear(r) + 0.7152 * linear(g) + 0.0722 * linear(b)


def _contraste(cor_a: str, cor_b: str) -> float:
    l1, l2 = sorted((_luminancia_relativa(cor_a), _luminancia_relativa(cor_b)), reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)


class IdentidadeVisualTests(unittest.TestCase):
    """Logo oficial, paleta clara/escura, alternador de aparência e ausência
    de dependências remotas (revisão de identidade visual, 25/09/2026)."""

    def test_logo_oficial_existe_localmente(self):
        self.assertTrue(LOGO_PATH.is_file(), f"logo ausente em {LOGO_PATH}")
        cabecalho = LOGO_PATH.read_bytes()[:8]
        self.assertEqual(cabecalho[:4], b"\x89PNG", "arquivo do logo não é um PNG válido")

    def test_logo_esta_nos_caminhos_publicos_obrigatorios(self):
        self.assertIn("assets/brand/passos-magicos-icon-cor.png", inf.PUBLIC_REQUIRED_PATHS)
        self.assertIn("assets/brand/passos-magicos-icon-cor.png", inf.VISUAL_ASSETS)

    def test_logo_referenciado_sem_hotlink(self):
        """O caminho do logo em `streamlit_app.py` é local (`assets/brand/...`),
        nunca uma URL remota."""
        codigo, _ = _parse(APP_PATH)
        self.assertIn('"assets" / "brand" / "passos-magicos-icon-cor.png"', codigo)
        self.assertNotRegex(codigo, r"passos-?magicos\.org\.br")

    def test_css_e_app_sem_dependencia_remota_de_fontes_ou_estilos(self):
        """A checagem ignora o bloco de comentário de cabeçalho do arquivo,
        que descreve em prosa o que NÃO está presente (ex.: "sem @import") —
        só o CSS efetivo (fora de comentários) precisa estar livre dessas
        dependências."""
        css_bruto = (ROOT / "assets" / "styles" / "app.css").read_text(encoding="utf-8")
        css_sem_comentarios = re.sub(r"/\*.*?\*/", "", css_bruto, flags=re.DOTALL)
        for termo in ("@import", "http://", "https://", "fonts.googleapis", "fonts.gstatic"):
            self.assertNotIn(termo, css_sem_comentarios,
                             f"{termo!r} encontrado em app.css fora de comentário (dependência remota proibida)")

    def test_preferencia_de_tema_nao_e_persistida_fora_da_sessao(self):
        """`st.session_state` apenas — nenhum `localStorage`, `sessionStorage`
        ou cookie custom para lembrar o modo claro/escuro entre sessões."""
        codigo, _ = _parse(APP_PATH)
        css = (ROOT / "assets" / "styles" / "app.css").read_text(encoding="utf-8")
        for termo in ("localStorage", "sessionStorage", "document.cookie"):
            self.assertNotIn(termo, codigo)
            self.assertNotIn(termo, css)

    def test_seletor_de_aparencia_e_nativo_com_duas_opcoes(self):
        at = _novo_app()
        controles = at.segmented_control
        self.assertEqual(len(controles), 1)
        self.assertEqual(set(controles[0].options), {"Claro", "Escuro"})

    def test_modo_claro_e_o_padrao(self):
        at = _novo_app()
        texto = _texto_total(at)
        self.assertIn("--pm-bg: #faf8f4", texto)

    def test_alternar_para_escuro_muda_as_variaveis_injetadas(self):
        at = _novo_app()
        at.segmented_control[0].set_value("Escuro")
        at.run(timeout=30)
        texto = _texto_total(at)
        self.assertIn("--pm-bg: #12211f", texto)
        self.assertNotIn("--pm-bg: #faf8f4", texto)

    def test_paleta_atende_contraste_wcag_aa_nos_dois_modos(self):
        import streamlit_app as app_module
        for nome_modo, variaveis in app_module._VARIAVEIS_TEMA.items():
            fundo = variaveis["pm-bg"]
            with self.subTest(modo=nome_modo, par="texto/fundo"):
                self.assertGreaterEqual(_contraste(variaveis["pm-texto"], fundo), 4.5)
            with self.subTest(modo=nome_modo, par="texto-suave/fundo"):
                self.assertGreaterEqual(_contraste(variaveis["pm-texto-suave"], fundo), 3.0)
            with self.subTest(modo=nome_modo, par="azul/fundo"):
                self.assertGreaterEqual(_contraste(variaveis["pm-azul"], fundo), 3.0)

    def test_componentes_nativos_seguem_a_cor_de_texto_do_tema(self):
        """Regressão: `st.table`, rótulos de widget (`stWidgetLabel`),
        `st.metric` e opções de rádio/selectbox fixam sua própria cor de
        texto a partir de `textColor` em `.streamlit/config.toml` — estático,
        só o modo "Claro". Sem uma regra explícita para cada um, ficavam
        ilegíveis no modo escuro (texto escuro sobre fundo escuro), mesmo com
        o restante da página já correto — encontrado por captura de tela
        real durante a validação visual desta rodada, não pelos testes
        automatizados anteriores."""
        css = (ROOT / "assets" / "styles" / "app.css").read_text(encoding="utf-8")
        for seletor in ('[data-testid="stWidgetLabel"]', '[data-testid="stTable"] td',
                        '[data-testid="stTable"] th', '[data-testid="stMetricLabel"]',
                        '[data-testid="stMetricValue"]', '[data-baseweb="select"] *'):
            self.assertIn(seletor, css, f"{seletor!r} não tem regra de cor de texto no tema")

    def test_cabecalho_tem_logo_titulo_e_seletor_antes_das_abas(self):
        codigo, _ = _parse(APP_PATH)
        pos_cabecalho = codigo.index("def _cabecalho(")
        pos_main = codigo.index("def main(")
        trecho_cabecalho = codigo[pos_cabecalho:pos_main]
        self.assertIn("st.image(", trecho_cabecalho)
        self.assertIn("st.segmented_control(", trecho_cabecalho)
        pos_chamada_cabecalho = codigo.index("_cabecalho()")
        pos_chamada_tabs = codigo.index("st.tabs(")
        self.assertLess(pos_chamada_cabecalho, pos_chamada_tabs)

    def test_nao_recria_aba_plano_de_acompanhamento(self):
        codigo, _ = _parse(APP_PATH)
        self.assertNotIn("Plano de acompanhamento", codigo)

    def test_nao_inventa_marca_concorrente(self):
        """O nome principal da instituição continua "Passos Mágicos" — sem
        uma marca de projeto inventada substituindo-o (ex.: "Trajetórias em
        foco" foi cogitado e descartado nesta rodada)."""
        texto = _texto_total(_novo_app())
        self.assertIn("Passos Mágicos", texto)
        self.assertNotIn("Trajetórias em foco", texto)


if __name__ == "__main__":
    unittest.main()
