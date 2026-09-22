"""Regressão da TASK 007 (notebook final reprodutível).

Este arquivo não executa nem altera `notebooks/datathon_fase5.ipynb`: ele lê o
notebook já executado e salvo, extrai todo o conteúdo textual de forma
recursiva (fontes, metadados e todos os tipos de saída) e verifica privacidade,
ausência de caminhos absolutos, ausência de treino/reavaliação (via AST),
coerência com os artefatos oficiais e integridade dos gráficos. A seção final
executa uma cópia pública temporária do notebook, fora do repositório, sem as
pastas privadas.
"""
from __future__ import annotations

import ast
import functools
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
NOTEBOOK = ROOT / "notebooks" / "datathon_fase5.ipynb"
sys.path.insert(0, str(SRC))
import rastreabilidade as rastro  # noqa: E402  (import após ajustar sys.path, como nos demais testes)


# --------------------------------------------------------------------------- #
# 1. Extração recursiva e segura de todo o conteúdo textual do notebook       #
# --------------------------------------------------------------------------- #

IMAGE_MIME_PREFIX = "image/"
BINARY_MIME_TYPES = frozenset({"application/pdf", "application/octet-stream", "application/zip"})
_TEXTUAL_APPLICATION_EXACT = frozenset({"application/json", "application/xml", "application/javascript"})
_TEXTUAL_APPLICATION_SUFFIXES = ("+json", "+xml")


def is_embedded_image_mime(mime: str) -> bool:
    """Imagens e binários equivalentes: nunca convertidos em texto."""
    return mime.startswith(IMAGE_MIME_PREFIX) or mime in BINARY_MIME_TYPES


def is_textual_mime(mime: str) -> bool:
    """Cobre text/* (inclusive text/javascript), application/json,
    application/*+json, application/xml, application/*+xml e
    application/javascript — sem nunca tratar image/* ou application/pdf
    como texto."""
    if is_embedded_image_mime(mime):
        return False
    if mime.startswith("text/"):
        return True
    if mime in _TEXTUAL_APPLICATION_EXACT:
        return True
    return mime.startswith("application/") and mime.endswith(_TEXTUAL_APPLICATION_SUFFIXES)


def iter_strings(node):
    """Percorre recursivamente estruturas JSON (dict/list/str) e emite as strings.

    Chaves de dicionário também são conteúdo textual (por exemplo, um JSON mal
    formado poderia esconder um RA ou um nome como chave em vez de valor) e por
    isso são percorridas da mesma forma que os valores.
    """
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for key, value in node.items():
            yield from iter_strings(key)
            yield from iter_strings(value)
    elif isinstance(node, (list, tuple)):
        for item in node:
            yield from iter_strings(item)
    # números, booleanos, None e bytes não carregam texto e são ignorados.


def extract_notebook_parts(nb: dict) -> tuple[str, list[tuple[int, str]]]:
    """Extrai todo o texto do notebook e relata imagens binárias embutidas.

    Cobre: metadados do notebook, fonte de todas as células, metadados de
    célula, metadados de saída, `stream`, `error` (ename/evalue/traceback) e
    todos os tipos MIME textuais de `data` (qualquer `text/*` — inclusive
    `text/javascript` —, `application/json`, `application/*+json`,
    `application/xml`, `application/*+xml` e `application/javascript`).
    Imagens (`image/*`) e binários equivalentes não são convertidos em texto,
    apenas contabilizados.
    """
    texts: list[str] = []
    embedded_images: list[tuple[int, str]] = []

    def add(value) -> None:
        texts.extend(iter_strings(value))

    add(nb.get("metadata", {}))
    for index, cell in enumerate(nb.get("cells", [])):
        add(cell.get("source", []))
        add(cell.get("metadata", {}))
        for output in cell.get("outputs", []) or []:
            add(output.get("metadata", {}))
            output_type = output.get("output_type")
            if output_type == "stream":
                add(output.get("text", []))
            elif output_type == "error":
                add(output.get("ename"))
                add(output.get("evalue"))
                add(output.get("traceback", []))
            else:  # display_data / execute_result
                for mime, content in (output.get("data", {}) or {}).items():
                    if is_embedded_image_mime(mime):
                        embedded_images.append((index, mime))
                        continue
                    if is_textual_mime(mime):
                        add(content)
                    # outros tipos binários não textuais são ignorados aqui, sem
                    # produzir texto e sem contar como imagem embutida.
    return "\n".join(texts), embedded_images


@functools.lru_cache(maxsize=1)
def load_notebook() -> dict:
    return json.loads(NOTEBOOK.read_text(encoding="utf-8"))


@functools.lru_cache(maxsize=1)
def extracted_notebook_text() -> str:
    text, _ = extract_notebook_parts(load_notebook())
    return text


class NotebookExtractionTests(unittest.TestCase):
    """Testa a função de extração com estruturas sintéticas, não com o notebook real."""

    def test_extrai_texto_de_todos_os_campos_relevantes(self):
        nb = {
            "metadata": {"kernelspec": {"display_name": "Python 3"}},
            "cells": [
                {
                    "cell_type": "markdown",
                    "metadata": {"tags": ["nota-metadado"]},
                    "source": ["# título\n", "corpo em markdown"],
                },
                {
                    "cell_type": "code",
                    "metadata": {"chave": "fonte-metadado-celula"},
                    "source": ["x = 1\n"],
                    "outputs": [
                        {"output_type": "stream", "name": "stdout", "text": ["saida-stream\n"]},
                        {
                            "output_type": "display_data",
                            "metadata": {"nota": "saida-metadado"},
                            "data": {
                                "text/plain": "saida-texto-plano",
                                "text/markdown": "saida-markdown",
                                "text/html": "<td>saida-html</td>",
                                "application/json": {"chave_json": ["valor-json-aninhado"]},
                                "text/x-custom": "saida-mime-textual-generico",
                            },
                        },
                        {
                            "output_type": "error",
                            "ename": "ValueError",
                            "evalue": "mensagem-erro",
                            "traceback": ["linha-traceback-1", "linha-traceback-2"],
                        },
                    ],
                },
            ],
        }
        text, images = extract_notebook_parts(nb)
        for esperado in (
            "corpo em markdown", "nota-metadado", "fonte-metadado-celula", "saida-stream",
            "saida-texto-plano", "saida-markdown", "saida-html", "valor-json-aninhado",
            "saida-mime-textual-generico", "saida-metadado", "ValueError", "mensagem-erro",
            "linha-traceback-1", "linha-traceback-2",
        ):
            self.assertIn(esperado, text, f"campo ausente na extração: {esperado}")
        self.assertEqual(images, [])

    def test_recursao_segura_em_estruturas_json_profundamente_aninhadas(self):
        nb = {
            "cells": [
                {
                    "cell_type": "code",
                    "source": [],
                    "metadata": {},
                    "outputs": [
                        {
                            "output_type": "execute_result",
                            "data": {
                                "application/json": {
                                    "nivel1": {"nivel2": [{"nivel3": ["texto-profundo", 123, None, True]}]}
                                }
                            },
                        }
                    ],
                }
            ]
        }
        text, _ = extract_notebook_parts(nb)
        self.assertIn("texto-profundo", text)

    def test_reprova_imagem_binaria_embutida_em_vez_de_referencia_relativa(self):
        nb = {
            "cells": [
                {
                    "cell_type": "code",
                    "source": [],
                    "metadata": {},
                    "outputs": [
                        {"output_type": "display_data", "data": {"image/png": "QkFTRTY0RkFLRQ=="}}
                    ],
                }
            ]
        }
        _, images = extract_notebook_parts(nb)
        self.assertEqual(images, [(0, "image/png")])

    def test_notebook_real_nao_possui_imagens_binarias_embutidas(self):
        _, images = extract_notebook_parts(load_notebook())
        self.assertEqual(images, [], "gráficos devem permanecer referenciados por caminho relativo")

    def test_chaves_de_dicionario_sao_percorridas_como_texto(self):
        nb = {
            "cells": [
                {
                    "cell_type": "code",
                    "source": [],
                    "metadata": {"chave-metadado-suspeita": True},
                    "outputs": [
                        {
                            "output_type": "execute_result",
                            "data": {"application/json": {"chave-de-saida-suspeita": {"status": "ativo"}}},
                        }
                    ],
                }
            ]
        }
        text, _ = extract_notebook_parts(nb)
        self.assertIn("chave-metadado-suspeita", text)
        self.assertIn("chave-de-saida-suspeita", text)

    def test_amplitude_de_mime_types_textuais(self):
        nb = {
            "cells": [
                {
                    "cell_type": "code",
                    "source": [],
                    "metadata": {},
                    "outputs": [
                        {
                            "output_type": "display_data",
                            "data": {
                                "application/xml": "<raiz>texto-xml</raiz>",
                                "application/vnd.api+json": {"dados": "texto-json-com-sufixo"},
                                "application/rdf+xml": "<raiz>texto-xml-com-sufixo</raiz>",
                                "application/javascript": "var texto = 'texto-javascript';",
                                "text/javascript": "var texto = 'texto-javascript-plano';",
                            },
                        }
                    ],
                }
            ]
        }
        text, images = extract_notebook_parts(nb)
        for esperado in ("texto-xml", "texto-json-com-sufixo", "texto-xml-com-sufixo",
                         "texto-javascript", "texto-javascript-plano"):
            self.assertIn(esperado, text, f"MIME textual não coberto: {esperado}")
        self.assertEqual(images, [])


# --------------------------------------------------------------------------- #
# 2. Privacidade: RA, nomes, estruturas de identificação e dados pessoais     #
# --------------------------------------------------------------------------- #

RA_VALUE = re.compile(r"(?i)\bra\b[\"']?\s*[:=]?\s*[\"']?\d{4,}\b")
NAME_LABELED = re.compile(
    r"(?i)\b(?:nome|aluno|estudante)\b\s*[:=]\s*[\"']?"
    r"[A-ZÀ-Þ][\wÀ-ÿ'-]*\s+[A-Za-zÀ-ÿ][\wÀ-ÿ'-]*"
)
STRUCT_KEYS = re.compile(
    r"(?i)[\"']?\b(?:ra|nome|aluno|estudante)[\"']?\s*[:=]\s*[\"'][^\"']{1,120}[\"']"
)


def privacy_issues(text: str) -> set[str]:
    """Detecta indícios de dados privados em texto livre; reutiliza `rastreabilidade`
    para caminhos absolutos e vocabulário editorial alheio ao relatório."""
    issues = set(rastro.public_text_issues(text))
    if RA_VALUE.search(text):
        issues.add("ra_valor")
    if NAME_LABELED.search(text):
        issues.add("nome_pessoa")
    if STRUCT_KEYS.search(text):
        issues.add("estrutura_identificadores")
    return issues


class NotebookPrivacyDetectionTests(unittest.TestCase):
    """Casos adversariais totalmente sintéticos: nenhum dado real do projeto."""

    def test_detecta_ra_ficticio(self):
        self.assertIn("ra_valor", privacy_issues('RA: 8827364'))
        self.assertIn("ra_valor", privacy_issues('"ra": "9911002"'))

    def test_detecta_nome_de_estudante(self):
        self.assertIn("nome_pessoa", privacy_issues("Nome: Maria da Silva"))

    def test_detecta_estrutura_com_chaves_de_identificacao(self):
        registro = json.dumps({"ra": "9911002", "nome": "Maria da Silva"}, ensure_ascii=False)
        issues = privacy_issues(registro)
        self.assertTrue({"ra_valor", "nome_pessoa", "estrutura_identificadores"} & issues)

    def test_detecta_registro_individual_em_texto_plano(self):
        linha = "RA 8827364 - Maria da Silva - fase 3 - IDA 7.2"
        issues = privacy_issues(linha)
        self.assertTrue(issues, "registro individual sintético não foi detectado")

    def test_detecta_dado_pessoal_em_metadados_de_celula(self):
        nb = {
            "cells": [
                {
                    "cell_type": "code",
                    "source": ["x = 1\n"],
                    "metadata": {"depuracao": {"aluno_ra": "RA: 8827364", "aluno_nome": "Nome: Maria da Silva"}},
                    "outputs": [],
                }
            ]
        }
        text, _ = extract_notebook_parts(nb)
        self.assertTrue(privacy_issues(text))

    def test_detecta_dado_pessoal_em_saida_text_html(self):
        nb = {
            "cells": [
                {
                    "cell_type": "code",
                    "source": [],
                    "metadata": {},
                    "outputs": [
                        {
                            "output_type": "display_data",
                            "data": {"text/html": "<tr><td>RA: 8827364</td><td>Nome: Maria da Silva</td></tr>"},
                        }
                    ],
                }
            ]
        }
        text, _ = extract_notebook_parts(nb)
        self.assertTrue(privacy_issues(text))

    def test_detecta_nome_como_chave_de_dicionario_em_saida(self):
        nb = {
            "cells": [{
                "cell_type": "code", "source": [], "metadata": {},
                "outputs": [{
                    "output_type": "execute_result",
                    "data": {"application/json": {"Nome: Maria da Silva": True}},
                }],
            }]
        }
        text, _ = extract_notebook_parts(nb)
        self.assertTrue(privacy_issues(text), "chave de dicionário 'Nome: Maria da Silva' não detectada")

    def test_detecta_ra_como_chave_de_dicionario_em_saida(self):
        nb = {
            "cells": [{
                "cell_type": "code", "source": [], "metadata": {},
                "outputs": [{
                    "output_type": "execute_result",
                    "data": {"application/json": {"RA: 8827364": {"status": "ativo"}}},
                }],
            }]
        }
        text, _ = extract_notebook_parts(nb)
        self.assertTrue(privacy_issues(text), "chave de dicionário 'RA: 8827364' não detectada")

    def test_detecta_dado_pessoal_como_chave_de_metadata(self):
        nb = {
            "cells": [{
                "cell_type": "code", "source": ["x = 1\n"],
                "metadata": {"RA: 8827364": {"status": "ativo"}},
                "outputs": [],
            }]
        }
        text, _ = extract_notebook_parts(nb)
        self.assertTrue(privacy_issues(text), "chave pessoal em metadata de célula não detectada")

    def test_detecta_dado_pessoal_como_chave_em_application_mais_json(self):
        nb = {
            "cells": [{
                "cell_type": "code", "source": [], "metadata": {},
                "outputs": [{
                    "output_type": "display_data",
                    "data": {"application/vnd.api+json": {"Nome: Maria da Silva": {"status": "ativo"}}},
                }],
            }]
        }
        text, _ = extract_notebook_parts(nb)
        self.assertTrue(privacy_issues(text), "chave pessoal em application/*+json não detectada")

    def test_detecta_caminho_absoluto_via_rastreabilidade(self):
        self.assertIn("caminho_absoluto", privacy_issues(r"C:\Users\alguem\segredo.csv"))

    def test_nao_reprova_texto_metodologico_legitimo(self):
        texto = (
            "O RA será utilizado exclusivamente para correspondência longitudinal e "
            "auditoria, sem integrar as variáveis preditoras. Nome e RA são identificadores "
            "excluídos do modelo. O aluno pode aparecer nas duas transições."
        )
        self.assertEqual(privacy_issues(texto), set())

    def test_notebook_real_sem_indicios_de_dados_privados(self):
        issues = privacy_issues(extracted_notebook_text())
        self.assertEqual(issues, set(), f"indícios de privacidade no notebook: {issues}")


# --------------------------------------------------------------------------- #
# 3. Caminhos absolutos (Windows e Unix/Linux)                                #
# --------------------------------------------------------------------------- #

ABSOLUTE_PATH = re.compile(
    r"(?i)"
    r"(?:\bfile://)"                                              # file://...
    r"|(?:(?<![\w])[a-z]:[\\/])"                                   # C:\..., C:/..., D:\..., D:/...
    r"|(?:\\\\[a-z0-9_.-]+\\)"                                     # \\servidor\compartilhamento\
    r"|(?:(?<![\w./])/(?:tmp|var|root|workspace|mnt|home|users|private|opt|usr)(?:/|\b))"
)


class NotebookAbsolutePathDetectionTests(unittest.TestCase):
    def test_detecta_variantes_windows(self):
        for caminho in (r"C:\Users\alguem\arquivo.csv", "C:/Users/alguem/arquivo.csv",
                        r"D:\dados\base.csv", "D:/dados/base.csv", r"\\servidor\compartilhado\pasta"):
            self.assertRegex(caminho, ABSOLUTE_PATH, f"não detectado: {caminho}")

    def test_detecta_variantes_unix_e_file_scheme(self):
        for caminho in ("/tmp/segredo.csv", "/var/dados/base.csv", "/root/base.csv",
                        "/workspace/dados/base.csv", "/mnt/dados/base.csv", "file:///tmp/base.csv"):
            self.assertRegex(caminho, ABSOLUTE_PATH, f"não detectado: {caminho}")

    def test_nao_reprova_caminhos_relativos_legitimos(self):
        for caminho in ("../reports/figures/01_defasagem.png", "reports/metricas_modelagem.json",
                        "src/modelagem.py", "docs/contrato_metodologico.md", "notebooks/datathon_fase5.ipynb"):
            self.assertNotRegex(caminho, ABSOLUTE_PATH, f"falso positivo em caminho relativo: {caminho}")

    def test_notebook_real_sem_caminhos_absolutos(self):
        achado = ABSOLUTE_PATH.search(extracted_notebook_text())
        self.assertIsNone(achado, f"caminho absoluto encontrado: {achado and achado.group(0)!r}")


# --------------------------------------------------------------------------- #
# 4. Treino e reavaliação: análise AST das células de código                  #
# --------------------------------------------------------------------------- #

FORBIDDEN_TRAIN_NAMES = frozenset({
    "fit", "fit_transform", "partial_fit", "predict", "predict_proba",
    "GridSearchCV", "RandomizedSearchCV", "cross_validate", "cross_val_score",
    "learning_curve", "validation_curve",
    "freeze_development", "select_development", "evaluate_temporal", "choose_threshold",
})
FORBIDDEN_METRIC_NAMES = frozenset({
    "accuracy_score", "average_precision_score", "roc_auc_score", "precision_score",
    "recall_score", "f1_score", "fbeta_score", "brier_score_loss", "precision_recall_curve",
    "roc_curve", "confusion_matrix", "classification_report", "log_loss",
})
FORBIDDEN_CALL_NAMES = FORBIDDEN_TRAIN_NAMES | FORBIDDEN_METRIC_NAMES
_GENERIC_METRIC_SUFFIX = re.compile(r"(?i)(?:_score|_loss|_curve)$")
_THRESHOLD_WORD = re.compile(r"(?i)threshold|limiar")


def classify_call_name(name: str) -> str | None:
    if name in FORBIDDEN_CALL_NAMES:
        return "chamada_proibida"
    if _THRESHOLD_WORD.search(name):
        return "otimizacao_de_limiar"
    if _GENERIC_METRIC_SUFFIX.search(name) or name in {"confusion_matrix", "classification_report"}:
        return "metrica_sklearn_equivalente"
    return None


def _import_alias_map(tree: ast.AST) -> dict[str, str]:
    alias_map: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                original = alias.name.rsplit(".", 1)[-1]
                local = alias.asname or alias.name.split(".")[0]
                alias_map[local] = original
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                alias_map[alias.asname or alias.name] = alias.name
    return alias_map


def _assignment_alias_map(tree: ast.AST) -> dict[str, str]:
    """Detecta alias por atribuição: `treinar = modelo.fit` ou `treinar = fit`.

    Só registra o alias quando o lado direito é uma simples referência
    (`Name` ou `Attribute`), nunca quando é uma chamada (`Call`) — assim
    `x = calcular_algo()` (o resultado de uma chamada comum e segura)
    jamais vira alias de `calcular_algo`.
    """
    alias_map: dict[str, str] = {}
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)):
            continue
        alvo = node.targets[0].id
        origem = node.value
        if isinstance(origem, ast.Attribute):
            alias_map[alvo] = origem.attr
        elif isinstance(origem, ast.Name):
            alias_map[alvo] = origem.id
        # Constant, Call, Subscript, BinOp etc. não criam alias.
    return alias_map


def _resolve_alias_chain(name: str, alias_map: dict[str, str]) -> str:
    """Segue a cadeia de aliases (import e atribuição combinados) até o nome
    final ou até detectar um ciclo, cobrindo casos como
    `a = modelo.fit; b = a; b(X, y)`."""
    seen: set[str] = set()
    while name in alias_map and name not in seen:
        seen.add(name)
        name = alias_map[name]
    return name


def _call_target_name(func: ast.AST) -> str | None:
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def find_forbidden_calls(source: str) -> list[tuple[str, str]]:
    """Analisa uma única fonte Python (célula ou trecho sintético) via AST.

    Diferencia chamadas executáveis reais de comentários (removidos pelo parser),
    strings explicativas (nós `Constant`, nunca `Call`) e texto em Markdown
    (não é código Python e não é analisado por esta função). Resolve aliases
    tanto de `import ... as` quanto de atribuição simples (`x = modelo.fit`),
    inclusive encadeados.
    """
    tree = ast.parse(source)
    alias_map = {**_import_alias_map(tree), **_assignment_alias_map(tree)}
    found: list[tuple[str, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _call_target_name(node.func)
        if name is None:
            continue
        resolved = _resolve_alias_chain(name, alias_map)
        classificacao = classify_call_name(resolved) or classify_call_name(name)
        if classificacao:
            found.append((resolved, classificacao))
    return found


def code_cells(nb: dict) -> list[str]:
    return ["".join(cell.get("source", [])) for cell in nb.get("cells", [])
            if cell.get("cell_type") == "code" and "".join(cell.get("source", [])).strip()]


def find_forbidden_calls_in_notebook(nb: dict) -> list[tuple[str, str]]:
    sources = code_cells(nb)
    trees = [ast.parse(source) for source in sources]
    alias_map: dict[str, str] = {}
    for tree in trees:
        alias_map.update(_import_alias_map(tree))
        alias_map.update(_assignment_alias_map(tree))
    found: list[tuple[str, str]] = []
    for tree in trees:
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = _call_target_name(node.func)
            if name is None:
                continue
            resolved = _resolve_alias_chain(name, alias_map)
            classificacao = classify_call_name(resolved) or classify_call_name(name)
            if classificacao:
                found.append((resolved, classificacao))
    return found


class NotebookForbiddenCallDetectionTests(unittest.TestCase):
    def test_detecta_fit_em_metodo_de_atributo(self):
        achados = find_forbidden_calls("modelo.fit(X, y)")
        self.assertTrue(any(nome == "fit" for nome, _ in achados))

    def test_detecta_fit_como_nome_isolado(self):
        achados = find_forbidden_calls("fit(X, y)")
        self.assertTrue(any(nome == "fit" for nome, _ in achados))

    def test_detecta_alias_de_cross_val_score(self):
        fonte = "from sklearn.model_selection import cross_val_score as cvs\ncvs(modelo, X, y)\n"
        achados = find_forbidden_calls(fonte)
        self.assertTrue(any(nome == "cross_val_score" for nome, _ in achados))

    def test_detecta_alias_de_metrica_sklearn(self):
        fonte = "from sklearn.metrics import roc_auc_score as auc2\nauc2(y, p)\n"
        achados = find_forbidden_calls(fonte)
        self.assertTrue(any(nome == "roc_auc_score" for nome, _ in achados))

    def test_detecta_grid_search_cv(self):
        fonte = "from sklearn.model_selection import GridSearchCV\nGridSearchCV(estimator=modelo, param_grid={})\n"
        achados = find_forbidden_calls(fonte)
        self.assertTrue(any(nome == "GridSearchCV" for nome, _ in achados))

    def test_detecta_randomized_search_cv(self):
        fonte = "from sklearn.model_selection import RandomizedSearchCV\nRandomizedSearchCV(modelo, {})\n"
        achados = find_forbidden_calls(fonte)
        self.assertTrue(any(nome == "RandomizedSearchCV" for nome, _ in achados))

    def test_detecta_otimizacao_de_limiar_por_nome_generico(self):
        achados = find_forbidden_calls("novo_limiar = otimizar_threshold(y, p)\n")
        self.assertTrue(any(classe == "otimizacao_de_limiar" for _, classe in achados))

    def test_nao_reprova_comentario(self):
        self.assertEqual(find_forbidden_calls("# modelo.fit(X, y) não deve ser chamado aqui\nx = 1\n"), [])

    def test_nao_reprova_string_explicativa(self):
        fonte = 'texto = "não chamamos modelo.fit(X, y) neste notebook"\n'
        self.assertEqual(find_forbidden_calls(fonte), [])

    def test_nao_reprova_celula_markdown_com_mesmo_texto(self):
        nb = {"cells": [{"cell_type": "markdown", "source": ["`modelo.fit(X, y)` não é executado aqui"],
                         "metadata": {}}]}
        self.assertEqual(find_forbidden_calls_in_notebook(nb), [])

    def test_detecta_alias_por_atribuicao_de_fit(self):
        fonte = "treinar = modelo.fit\ntreinar(X, y)\n"
        achados = find_forbidden_calls(fonte)
        self.assertTrue(any(nome == "fit" for nome, _ in achados))

    def test_detecta_alias_por_atribuicao_encadeado(self):
        fonte = "a = modelo.fit\nb = a\nb(X, y)\n"
        achados = find_forbidden_calls(fonte)
        self.assertTrue(any(nome == "fit" for nome, _ in achados), "alias encadeado não resolvido")

    def test_detecta_alias_por_atribuicao_de_metrica(self):
        fonte = "from sklearn.metrics import roc_auc_score\nmedir = roc_auc_score\nmedir(y, p)\n"
        achados = find_forbidden_calls(fonte)
        self.assertTrue(any(nome == "roc_auc_score" for nome, _ in achados))

    def test_detecta_alias_por_atribuicao_de_validacao_cruzada(self):
        fonte = "from sklearn.model_selection import cross_val_score\nvalidar = cross_val_score\nvalidar(modelo, X, y)\n"
        achados = find_forbidden_calls(fonte)
        self.assertTrue(any(nome == "cross_val_score" for nome, _ in achados))

    def test_detecta_alias_por_atribuicao_de_busca_de_hiperparametros(self):
        fonte = "from sklearn.model_selection import GridSearchCV\nBusca = GridSearchCV\nBusca(estimator=modelo, param_grid={})\n"
        achados = find_forbidden_calls(fonte)
        self.assertTrue(any(nome == "GridSearchCV" for nome, _ in achados))

    def test_detecta_alias_por_atribuicao_de_funcao_de_limiar(self):
        fonte = "ajustar = otimizar_limiar\najustar(y, p)\n"
        achados = find_forbidden_calls(fonte)
        self.assertTrue(any(classe == "otimizacao_de_limiar" for _, classe in achados))

    def test_alias_por_atribuicao_nao_gera_falso_positivo_com_padroes_comuns(self):
        fonte = (
            "modelo = LogisticRegression()\n"          # atribuição do resultado de uma chamada comum
            "media_ida = resultado.media\n"             # leitura de um atributo comum de dados
            "outra_variavel = calcular_media_local\n"   # alias de uma função local irrelevante
            "outra_variavel(1, 2)\n"
            "limiar_fixo = 0.5\n"                       # atribuição de constante, não de referência
        )
        self.assertEqual(find_forbidden_calls(fonte), [])

    def test_notebook_real_sem_chamadas_de_treino_ou_reavaliacao(self):
        achados = find_forbidden_calls_in_notebook(load_notebook())
        self.assertEqual(achados, [], f"chamadas proibidas encontradas no notebook: {achados}")


# --------------------------------------------------------------------------- #
# 5. Estrutura mínima e metadados de execução                                 #
# --------------------------------------------------------------------------- #

class NotebookStructureTests(unittest.TestCase):
    def test_estrutura_com_as_22_secoes(self):
        nb = load_notebook()
        self.assertEqual(nb["nbformat"], 4)
        titulos = [int(n) for c in nb["cells"] if c["cell_type"] == "markdown"
                   for n in re.findall(r"^## (\d+)\. ", "".join(c["source"]), flags=re.M)]
        self.assertEqual(titulos, list(range(1, 23)))

    def test_todas_as_celulas_de_codigo_foram_executadas_sem_erro_ou_stream(self):
        nb = load_notebook()
        codigo = [c for c in nb["cells"] if c["cell_type"] == "code"]
        self.assertTrue(codigo)
        for cell in codigo:
            self.assertIsNotNone(cell["execution_count"], "notebook sem execução registrada")
            for output in cell["outputs"]:
                self.assertNotEqual(output["output_type"], "error")
                self.assertNotEqual(output["output_type"], "stream")

    def test_dependencias_do_notebook_documentadas(self):
        nb = load_notebook()
        conteudo = (ROOT / "notebooks" / "requirements-notebook.txt").read_text(encoding="utf-8")
        self.assertIn("ipykernel==", conteudo)
        primeiras_celulas = "".join("".join(c["source"]) for c in nb["cells"][:2])
        self.assertIn("requirements-notebook.txt", primeiras_celulas)


# --------------------------------------------------------------------------- #
# 6. Resultados oficiais: conferência direta contra os artefatos              #
# --------------------------------------------------------------------------- #

@functools.lru_cache(maxsize=1)
def official_artifacts() -> dict:
    def load(path):
        return json.loads((ROOT / path).read_text(encoding="utf-8"))

    return {
        "metricas": load("reports/metricas_modelagem.json"),
        "schema": load("artifacts/schema_modelo.json"),
        "negocio": load("reports/metricas_analises_negocio.json"),
        "acesso": load("artifacts/avaliacao_temporal.json"),
    }


class NotebookOfficialResultsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = extracted_notebook_text()
        cls.artefatos = official_artifacts()

    def test_nome_do_modelo_oficial(self):
        modelo = self.artefatos["metricas"]["modelo"]
        self.assertEqual(modelo, "logistica")
        self.assertIn(modelo, self.text)
        self.assertRegex(self.text, r"(?i)regress\w*\s+log")

    def test_ordem_exata_dos_sete_preditores(self):
        oficiais = self.artefatos["schema"]["colunas"]
        self.assertEqual(oficiais, ["ida", "ieg", "iaa", "ips", "ipv", "fase_origem", "defasagem_origem"])
        encontrados_em_ordem = []
        for token in re.findall(r"`([a-z_]+)`", self.text):
            if token in oficiais and token not in encontrados_em_ordem:
                encontrados_em_ordem.append(token)
            if len(encontrados_em_ordem) == len(oficiais):
                break
        self.assertEqual(encontrados_em_ordem, oficiais)

    def test_limiar_oficial(self):
        limiar = self.artefatos["metricas"]["limiar"]
        self.assertIn(f"{limiar:.6f}", self.text)

    def test_metricas_temporais_e_recall_de_desenvolvimento(self):
        m = self.artefatos["metricas"]
        for chave in ("average_precision", "roc_auc", "precisao", "recall"):
            self.assertIn(f'{m["temporal"]["metricas"][chave]:.4f}', self.text)
        self.assertIn(f'{m["oof"]["metricas"]["recall"]:.4f}', self.text)

    def test_existencia_das_onze_respostas(self):
        for numero in range(1, 12):
            self.assertRegex(self.text, rf"(?i)Pergunta\s+{numero}\b")

    def test_existencia_dos_dez_graficos_oficiais(self):
        figuras = self.artefatos["negocio"]["figuras"]
        self.assertEqual(len(figuras), 10)
        for figura in figuras:
            self.assertIn(Path(figura).name, self.text)

    def test_mencao_a_conclusoes_e_limitacoes(self):
        self.assertRegex(self.text, r"(?i)limita[çc][õo]es")
        self.assertRegex(self.text, r"(?i)conclus[õo]es")

    def test_mencao_explicita_a_queda_do_recall(self):
        m = self.artefatos["metricas"]
        dev_recall = f'{100 * m["oof"]["metricas"]["recall"]:.1f}%'
        teste_recall = f'{100 * m["temporal"]["metricas"]["recall"]:.1f}%'
        self.assertIn(dev_recall, self.text)
        self.assertIn(teste_recall, self.text)
        self.assertTrue(
            re.search(r"(?i)recall[^\n]{0,80}(?:ca[ií][ud][ao]?s?|queda)", self.text)
            or re.search(r"(?i)(?:queda|ca[ií][ud][ao]?s?)[^\n]{0,80}recall", self.text),
            "menção à queda do recall não encontrada",
        )

    def test_mencao_a_subestimacao_do_risco(self):
        self.assertRegex(self.text, r"(?i)subestimou")


# --------------------------------------------------------------------------- #
# 7. Integridade dos gráficos referenciados                                   #
# --------------------------------------------------------------------------- #

class NotebookGraphicsHashTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = extracted_notebook_text()
        cls.artefatos = official_artifacts()

    def test_todos_os_graficos_referenciados_conferem_com_o_registro_oficial(self):
        registrados = dict(self.artefatos["negocio"]["output_hashes"])
        registrados.update(self.artefatos["acesso"]["output_hashes"])
        oficiais = set(self.artefatos["negocio"]["figuras"]) | {"reports/curvas_modelagem.png"}

        referenciados = {f"reports/{sufixo}" for sufixo in
                         re.findall(r"\.\./reports/((?:figures/)?[\w.]+\.png)", self.text)}

        self.assertEqual(len(oficiais), 11)
        self.assertEqual(referenciados, oficiais,
                          "o notebook deve referenciar exatamente os dez gráficos e as curvas oficiais")
        for caminho in referenciados:
            arquivo = ROOT / caminho
            self.assertTrue(arquivo.is_file(), f"gráfico ausente: {caminho}")
            self.assertIn(caminho, registrados, f"gráfico sem hash oficial registrado: {caminho}")
            self.assertTrue(rastro.file_matches_sha256(arquivo, registrados[caminho]),
                            f"hash divergente do registro oficial: {caminho}")

    def test_reprova_referencia_a_grafico_nao_registrado(self):
        registrados = dict(official_artifacts()["negocio"]["output_hashes"])
        registrados.update(official_artifacts()["acesso"]["output_hashes"])
        texto_com_grafico_estranho = "![figura estranha](../reports/figures/99_nao_oficial.png)"
        referenciado = {f"reports/{s}" for s in
                        re.findall(r"\.\./reports/((?:figures/)?[\w.]+\.png)", texto_com_grafico_estranho)}
        self.assertFalse(referenciado <= set(registrados), "figura sintética deveria ser não registrada")


# --------------------------------------------------------------------------- #
# 8. Execução pública automatizada (sem DATATHON/, local_data/, local_recovery/) #
# --------------------------------------------------------------------------- #

PRIVATE_DIR_NAMES = ("DATATHON", "local_data", "local_recovery")

# Únicos arquivos não rastreados autorizados enquanto a TASK 007 não foi
# commitada. Depois do commit, estes arquivos passam a aparecer em
# `git ls-files --cached` e simplesmente deixam de ser "não rastreados" —
# a regra abaixo continua válida sem qualquer alteração.
AUTHORIZED_UNTRACKED_FILES = frozenset({
    "notebooks/datathon_fase5.ipynb",
    "notebooks/requirements-notebook.txt",
    "tests/test_notebook_final.py",
})


def tracked_files(root: Path) -> list[str]:
    result = subprocess.run(["git", "ls-files", "--cached"], cwd=root,
                            capture_output=True, text=True, encoding="utf-8", check=True)
    return [linha for linha in result.stdout.splitlines() if linha]


def untracked_files(root: Path) -> list[str]:
    result = subprocess.run(["git", "ls-files", "--others", "--exclude-standard"], cwd=root,
                            capture_output=True, text=True, encoding="utf-8", check=True)
    return [linha for linha in result.stdout.splitlines() if linha]


def build_public_copy_manifest(tracked: list[str], untracked: list[str],
                                authorized_untracked=AUTHORIZED_UNTRACKED_FILES) -> list[str]:
    """Função pura (sem tocar em git ou disco): decide quais arquivos entram na
    cópia pública. Todo arquivo rastreado entra; um arquivo não rastreado só
    entra se estiver explicitamente autorizado. Qualquer outro arquivo não
    rastreado e não ignorado é tratado como inesperado e interrompe a cópia."""
    inesperados = sorted(set(untracked) - set(authorized_untracked))
    if inesperados:
        raise ValueError(
            "arquivos não rastreados inesperados encontrados (não são ignorados pelo "
            "Git nem estão na lista autorizada da TASK 007): " + ", ".join(inesperados)
            + ". Autorizados: " + ", ".join(sorted(authorized_untracked)))
    autorizados_presentes = [f for f in untracked if f in authorized_untracked]
    return tracked + autorizados_presentes


def public_copy_manifest(root: Path) -> list[str]:
    """Lista exata de arquivos a copiar para a execução pública, lendo o
    estado real do Git em `root` e aplicando `build_public_copy_manifest`."""
    return build_public_copy_manifest(tracked_files(root), untracked_files(root))


class PublicCopyManifestTests(unittest.TestCase):
    """Testa a regra de seleção de arquivos com listas sintéticas, sem git e
    sem criar nenhum arquivo inesperado dentro do repositório."""

    def test_rejeita_arquivo_nao_rastreado_inesperado(self):
        tracked = ["src/modelagem.py", "README.md"]
        untracked = ["notebooks/datathon_fase5.ipynb", "arquivo_suspeito.csv"]
        with self.assertRaises(ValueError) as contexto:
            build_public_copy_manifest(tracked, untracked)
        self.assertIn("arquivo_suspeito.csv", str(contexto.exception))

    def test_aceita_apenas_os_tres_arquivos_autorizados_ainda_nao_rastreados(self):
        tracked = ["src/modelagem.py"]
        untracked = sorted(AUTHORIZED_UNTRACKED_FILES)
        manifesto = build_public_copy_manifest(tracked, untracked)
        self.assertEqual(set(manifesto), set(tracked) | AUTHORIZED_UNTRACKED_FILES)

    def test_funciona_apos_o_commit_quando_os_tres_arquivos_ja_estao_rastreados(self):
        tracked = ["src/modelagem.py", *sorted(AUTHORIZED_UNTRACKED_FILES)]
        untracked: list[str] = []
        manifesto = build_public_copy_manifest(tracked, untracked)
        self.assertEqual(set(manifesto), set(tracked))

    def test_nenhum_diretorio_privado_e_aceito_mesmo_que_aparecesse_como_nao_rastreado(self):
        tracked = ["src/modelagem.py"]
        untracked = ["DATATHON/base.xlsx"]
        with self.assertRaises(ValueError):
            build_public_copy_manifest(tracked, untracked)

    def test_manifesto_real_do_repositorio_nao_levanta_erro(self):
        # Confirma no repositório real (sem criar arquivos) que hoje só os três
        # arquivos esperados estão fora do controle de versão.
        manifesto = public_copy_manifest(ROOT)
        for esperado in AUTHORIZED_UNTRACKED_FILES:
            self.assertIn(esperado, manifesto)


class NotebookPublicExecutionTests(unittest.TestCase):
    def test_notebook_executa_publicamente_sem_fontes_privadas(self):
        if not (ROOT / ".git").exists():
            self.fail("requer um repositório git local para montar a cópia pública")
        try:
            import nbformat
            from nbclient import NotebookClient
        except ImportError as erro:
            self.fail(
                f"dependência de execução ausente ({erro.name}). Este teste é obrigatório "
                "na suíte padrão: execute `python -m pip install -r requirements.txt` "
                "(que agora também instala notebooks/requirements-notebook.txt) antes de "
                "rodar os testes."
            )

        try:
            arquivos_publicos = public_copy_manifest(ROOT)
        except ValueError as erro:
            self.fail(str(erro))
        self.assertIn("notebooks/datathon_fase5.ipynb", arquivos_publicos)
        for pasta in PRIVATE_DIR_NAMES:
            self.assertFalse(any(a.startswith(pasta + "/") for a in arquivos_publicos),
                             f"{pasta}/ não deveria estar entre os arquivos públicos")

        tmp_root = Path(tempfile.mkdtemp(prefix="datathon_execucao_publica_"))
        self.assertFalse(str(tmp_root).startswith(str(ROOT)), "diretório temporário deve ficar fora do repositório")
        try:
            for relativo in arquivos_publicos:
                origem = ROOT / relativo
                if not origem.is_file():
                    continue
                destino = tmp_root / relativo
                destino.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(origem, destino)

            for pasta in PRIVATE_DIR_NAMES:
                self.assertFalse((tmp_root / pasta).exists(), f"{pasta}/ não deveria existir na cópia pública")

            notebook_copia = tmp_root / "notebooks" / "datathon_fase5.ipynb"
            self.assertTrue(notebook_copia.is_file())

            nb = nbformat.read(notebook_copia, as_version=4)
            client = NotebookClient(nb, timeout=600, kernel_name="python3",
                                    resources={"metadata": {"path": str(notebook_copia.parent)}})
            client.execute()

            for cell in nb["cells"]:
                if cell.get("cell_type") != "code":
                    continue
                for output in cell.get("outputs", []):
                    self.assertNotEqual(output.get("output_type"), "error",
                                        f"erro na execução pública: {output.get('evalue')}")

            texto_execucao, _ = extract_notebook_parts(nb)
            self.assertIn("Fonte privada não disponível neste ambiente", texto_execucao)

            for pasta in PRIVATE_DIR_NAMES:
                self.assertFalse((tmp_root / pasta).exists(),
                                 f"{pasta}/ não deveria ter sido criado durante a execução pública")

            # Os diretórios privados originais do repositório permanecem intocados.
            for pasta in PRIVATE_DIR_NAMES:
                caminho_original = ROOT / pasta
                if caminho_original.exists():
                    self.assertTrue(caminho_original.is_dir())
        finally:
            shutil.rmtree(tmp_root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
