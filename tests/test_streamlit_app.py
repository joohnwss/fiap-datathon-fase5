"""Regressão da TASK 010 para `streamlit_app.py` (interface pública).

Usa `streamlit.testing.v1.AppTest` para exercitar a aplicação sem abrir um
navegador nem um servidor de verdade (nenhuma rede, nenhum processo externo).
Cobre comportamento da interface, privacidade/segurança (por análise AST e
textual do próprio código-fonte) e portabilidade.

Nenhum teste aqui altera `artifacts/`, `reports/`, `docs/` ou qualquer
arquivo do repositório; os testes de portabilidade que usam diretórios
temporários limpam tudo via `addCleanup`, mesmo em caso de falha. Nenhum
dado privado é lido ou necessário.
"""
from __future__ import annotations

import ast
import re
import shutil
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))
import inferencia as inf  # noqa: E402

# Import plano entre testes irmãos (mesmo padrão já usado em
# tests/test_analises_negocio.py -> test_coortes_regressao.py); garante que
# funcione tanto com `unittest discover -s tests` quanto com
# `python -m unittest tests.test_streamlit_app` isoladamente.
TESTS_DIR = Path(__file__).resolve().parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))
from test_inferencia_aplicacao import official_threshold  # noqa: E402
# Reaproveita o helper que lê o limiar oficial dos artefatos, em vez de
# duplicar o número aqui.

APP_PATH = ROOT / "streamlit_app.py"
CONFIG_PATH = ROOT / ".streamlit" / "config.toml"

PAYLOAD_BAIXO_RISCO = {"ida": "6.5", "ieg": "8.0", "iaa": "7.0", "ips": "5.0", "ipv": "7.5",
                       "fase_origem": "2", "defasagem_origem": "0"}
PAYLOAD_ALTO_RISCO = {"ida": "2.0", "ieg": "2.0", "iaa": "2.0", "ips": "2.0", "ipv": "2.0",
                      "fase_origem": "3", "defasagem_origem": "-3"}


def _by_key(elementos, key):
    for elemento in elementos:
        if elemento.key == key:
            return elemento
    raise KeyError(f"widget com key={key!r} não encontrado")


def _button(at, rotulo):
    for botao in at.button:
        if botao.label == rotulo:
            return botao
    raise KeyError(f"botão {rotulo!r} não encontrado")


def _preencher_e_enviar(at, payload):
    for campo in inf.NUMERIC_FIELDS:
        _by_key(at.text_input, f"campo_{campo}").set_value(payload[campo])
    _by_key(at.selectbox, "campo_fase_origem").select(payload["fase_origem"])
    _button(at, "Gerar estimativa").click()
    at.run(timeout=30)
    return at


def _novo_app() -> AppTest:
    at = AppTest.from_file(str(APP_PATH))
    at.run(timeout=30)
    return at


def _texto_total(at) -> str:
    """Concatena todo o texto visível renderizado (markdown, caption, info,
    success, warning, error, expander) em uma única string, para buscas
    textuais de conteúdo editorial (avisos, limitações etc.)."""
    partes = []
    for colecao in (at.markdown, at.caption, at.info, at.success, at.warning,
                    at.error, at.title, at.subheader):
        partes.extend(str(e.value) for e in colecao)
    for exp in at.expander:
        partes.append(str(exp.label))
        for filho in exp.markdown:
            partes.append(str(filho.value))
    return "\n".join(partes)


# --------------------------------------------------------------------------- #
# Comportamento da interface (AppTest)                                       #
# --------------------------------------------------------------------------- #

class AppTestBehaviorTests(unittest.TestCase):
    def test_aplicacao_inicia_sem_excecao(self):
        at = _novo_app()
        self.assertEqual(list(at.exception), [])

    def test_titulo_presente(self):
        at = _novo_app()
        self.assertTrue(any("defasagem" in t.value.lower() for t in at.title))

    def test_aviso_educacional_presente(self):
        at = _novo_app()
        texto = _texto_total(at).lower()
        self.assertIn("educacional", texto)
        self.assertIn("demonstrativ", texto)

    def test_exatamente_sete_entradas_preditoras(self):
        at = _novo_app()
        self.assertEqual(len(at.text_input) + len(at.selectbox), 7)
        chaves = {ti.key for ti in at.text_input} | {sb.key for sb in at.selectbox}
        self.assertEqual(chaves, {f"campo_{c}" for c in inf.FEATURES})

    def test_seis_campos_numericos_permitem_vazio(self):
        at = _novo_app()
        for campo in inf.NUMERIC_FIELDS:
            with self.subTest(campo=campo):
                self.assertEqual(_by_key(at.text_input, f"campo_{campo}").value, "")

    def test_fase_contem_somente_0_a_7(self):
        at = _novo_app()
        opcoes = _by_key(at.selectbox, "campo_fase_origem").options
        self.assertEqual(tuple(opcoes), ("",) + inf.PHASE_CATEGORIES)

    def test_botao_de_exemplo_sintetico_funciona(self):
        at = _novo_app()
        _button(at, "Preencher exemplo sintético").click()
        at.run(timeout=30)
        for campo in inf.NUMERIC_FIELDS:
            self.assertNotEqual(_by_key(at.text_input, f"campo_{campo}").value, "")
        self.assertNotEqual(_by_key(at.selectbox, "campo_fase_origem").value, "")

    def test_botao_de_estimativa_existe(self):
        at = _novo_app()
        _button(at, "Gerar estimativa")  # não levanta KeyError

    def test_envio_valido_produz_probabilidade_em_percentual(self):
        at = _preencher_e_enviar(_novo_app(), PAYLOAD_BAIXO_RISCO)
        self.assertEqual(list(at.exception), [])
        self.assertEqual(len(at.metric), 1)
        self.assertRegex(at.metric[0].value, r"^\d+([.,]\d+)?%$")

    def test_classificacao_e_exibida_e_menciona_limiar_oficial(self):
        at = _preencher_e_enviar(_novo_app(), PAYLOAD_BAIXO_RISCO)
        self.assertEqual(len(at.success) + len(at.warning), 1)
        texto = _texto_total(at)
        self.assertIn(f"{official_threshold():.4f}", texto)

    def test_classificacao_acima_do_limiar_sinaliza_risco(self):
        at = _preencher_e_enviar(_novo_app(), PAYLOAD_ALTO_RISCO)
        self.assertEqual(list(at.exception), [])
        self.assertEqual(len(at.warning), 1)
        self.assertEqual(len(at.success), 0)

    def test_envio_com_campos_numericos_vazios_funciona(self):
        at = _novo_app()
        _by_key(at.selectbox, "campo_fase_origem").select("2")
        _button(at, "Gerar estimativa").click()
        at.run(timeout=30)
        self.assertEqual(list(at.exception), [])
        self.assertEqual(len(at.metric), 1)

    def test_texto_invalido_apresenta_mensagem_controlada(self):
        at = _novo_app()
        payload = dict(PAYLOAD_BAIXO_RISCO, ida="abc")
        at = _preencher_e_enviar(at, payload)
        self.assertEqual(list(at.exception), [])
        self.assertEqual(len(at.error), 1)
        self.assertIn("ida", at.error[0].value)

    def test_nan_apresenta_mensagem_controlada(self):
        at = _preencher_e_enviar(_novo_app(), dict(PAYLOAD_BAIXO_RISCO, ida="NaN"))
        self.assertEqual(list(at.exception), [])
        self.assertEqual(len(at.error), 1)

    def test_infinito_apresenta_mensagem_controlada(self):
        at = _preencher_e_enviar(_novo_app(), dict(PAYLOAD_BAIXO_RISCO, ida="inf"))
        self.assertEqual(list(at.exception), [])
        self.assertEqual(len(at.error), 1)

    def test_resultado_abaixo_do_limiar_nao_e_apresentado_como_ausencia_de_risco(self):
        at = _preencher_e_enviar(_novo_app(), PAYLOAD_BAIXO_RISCO)
        texto = _texto_total(at).lower()
        self.assertIn("não elimina o risco", texto)

    def test_limitacoes_presentes(self):
        at = _novo_app()
        rotulos_expander = [e.label for e in at.expander]
        self.assertTrue(any("limitaç" in r.lower() for r in rotulos_expander))

    def test_queda_do_recall_presente(self):
        texto = _texto_total(_novo_app()).lower()
        self.assertIn("recall", texto)
        self.assertTrue("caiu" in texto or "queda" in texto)

    def test_subestimacao_do_risco_presente(self):
        texto = _texto_total(_novo_app()).lower()
        self.assertIn("subestima", texto)

    def test_supervisao_humana_presente(self):
        texto = _texto_total(_novo_app()).lower()
        self.assertIn("supervisão humana", texto)

    def test_linguagem_nao_causal(self):
        texto = _texto_total(_novo_app()).lower()
        self.assertIn("causa e efeito", texto)
        self.assertIn("não é uma relação de causa e efeito", texto)

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
                at = _preencher_e_enviar(_novo_app(), payload)
                self.assertEqual(list(at.exception), [])


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
# testes de privacidade/segurança desta TASK. `.streamlit/config.toml` é
# coberto à parte (não é Python) nos testes dedicados ao final da classe.
PUBLIC_PYTHON_MODULES: tuple[tuple[str, Path], ...] = (
    ("streamlit_app.py", APP_PATH),
    ("src/inferencia.py", SRC / "inferencia.py"),
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
    """Cobre `streamlit_app.py` e `src/inferencia.py`
    (`PUBLIC_PYTHON_MODULES`) e, separadamente, `.streamlit/config.toml`.
    Usa AST para comportamento executável (chamadas de escrita, rede,
    exceção) e restringe a análise textual a conteúdo editorial específico
    (rótulos de widgets, dicionários de texto) — nunca ao arquivo inteiro —
    para não confundir prosa legítima (ex.: a docstring que diz 'Nenhum RA,
    nome... é solicitado', ou menções a 'classe positiva'/'nome do modelo')
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
        """Restrito aos textos de rótulo/ajuda efetivamente usados nos
        widgets de entrada do Streamlit (`CAMPO_ROTULO`/`CAMPO_AJUDA` e os
        argumentos literais das chamadas `st.text_input`/`st.selectbox`/
        etc.) — não ao arquivo inteiro, onde a mesma palavra pode aparecer
        legitimamente em prosa editorial."""
        codigo_app, arvore_app = _parse(APP_PATH)
        rotulos = (_dict_literal_string_values(arvore_app, "CAMPO_ROTULO")
                  + _dict_literal_string_values(arvore_app, "CAMPO_AJUDA"))
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
        """Menções editoriais em docstring são aceitas (ex.: a própria
        docstring de `src/inferencia.py` explica que o módulo 'nunca...
        acessa DATATHON/, local_data/ ou local_recovery/'); qualquer
        referência **fora** de docstring — ou seja, um literal
        potencialmente usado para montar um caminho de verdade — reprova o
        teste."""
        for nome, caminho, codigo, arvore in self.modulos:
            with self.subTest(modulo=nome):
                literais = list(_non_docstring_string_literals(arvore))
                for pasta in ("DATATHON", "local_data", "local_recovery"):
                    self.assertFalse(any(pasta in literal for literal in literais),
                                     f"{nome} referencia {pasta} fora de um docstring")

    def test_nenhuma_persistencia_de_entradas_em_arquivo(self):
        """Comportamento executável, via AST: qualquer chamada
        `.write_text(`/`.write_bytes(`/`.write(`/`.to_csv(`/`.to_json(`/
        `.dump(` é tratada como persistência proibida. A leitura legítima
        dos artefatos públicos usa apenas `read_text`/`read_json`/`load`
        (nunca métodos de escrita), então não é afetada por esta checagem."""
        for nome, caminho, codigo, arvore in self.modulos:
            with self.subTest(modulo=nome):
                escritas = list(_iter_calls(arvore, _WRITE_METHOD_ATTRS))
                self.assertEqual(escritas, [], f"{nome} contém chamada(s) de escrita/persistência")

    def test_nenhum_open_em_modo_de_escrita_acrescimo_ou_atualizacao(self):
        """Diferencia leitura comprovada estaticamente (`open(caminho)`,
        `open(caminho, 'r')`/`'rt'`/`'rb'`, permitidos) de qualquer coisa
        que não seja uma leitura comprovada: modo `'w'`/`'a'`/`'x'`/`'+'`,
        modo vindo de variável/expressão/chamada/f-string, ou argumento de
        modo duplicado/ambíguo (todos proibidos, regra conservadora — sem
        resolver fluxo de variáveis). Primeiro confere os módulos reais;
        depois exercita os mesmos helpers com os casos adversariais
        sintéticos do revisor."""
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
        """AST puro (`ast.Import`/`ast.ImportFrom`): considera módulo raiz e
        submódulo, independentemente de alias, import direto ou `from
        import`. Lista mínima proibida: requests, httpx, urllib, urllib3,
        socket, aiohttp, http.client."""
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
        """`print()` executável detectado por AST (indiferente a
        espaços/quebras de linha; não reprova comentário, string
        explicativa nem função como `printable_result()`); `logging`
        detectado por AST de import."""
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

    def test_nenhum_unsafe_allow_html(self):
        for nome, caminho, codigo, arvore in self.modulos:
            with self.subTest(modulo=nome):
                self.assertNotIn("unsafe_allow_html", codigo)

    def test_nenhum_cache_de_dados_das_entradas(self):
        codigo_app, _ = _parse(APP_PATH)
        self.assertNotIn("cache_data", codigo_app)
        self.assertIn("cache_resource", codigo_app)

    def test_nenhum_segredo_hardcoded(self):
        for nome, caminho, codigo, arvore in self.modulos:
            with self.subTest(modulo=nome):
                self.assertIsNone(_SECRET_PATTERN.search(codigo))

    def test_nenhum_caminho_absoluto_local(self):
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
        self.assertIn("não correspondem a nenhum aluno real", codigo_app.lower())

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
        for caminho in (APP_PATH, SRC / "inferencia.py"):
            codigo = caminho.read_text(encoding="utf-8")
            self.assertIn("from pathlib import Path", codigo)
            self.assertNotIn("\\\\", codigo)  # nenhum separador Windows hardcoded

    def test_localizacao_da_raiz_a_partir_de_pontos_diferentes(self):
        pontos_de_partida = [ROOT, SRC, ROOT / "tests", ROOT / "docs",
                             ROOT / "reports" / "figures"]
        for ponto in pontos_de_partida:
            with self.subTest(ponto=ponto.name or str(ponto)):
                self.assertEqual(inf.find_project_root(ponto), ROOT)

    def test_execucao_com_copia_publica_minima_em_diretorio_temporario(self):
        tmp = Path(tempfile.mkdtemp(prefix="streamlit_portabilidade_"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        for relativo in inf.PUBLIC_REQUIRED_PATHS:
            destino = tmp / relativo
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relativo, destino)
        contexto = inf.prepare_application(root=tmp)
        self.assertAlmostEqual(contexto.validation.threshold, official_threshold(), places=12)
        for pasta in ("DATATHON", "local_data", "local_recovery"):
            self.assertFalse((tmp / pasta).exists())

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


if __name__ == "__main__":
    unittest.main()
