"""Inferência pública do modelo oficialmente avaliado (TASK 009).

Reaproveita `modelagem.validate_frozen` como única fonte de verdade para as
verificações que ela realmente executa, e complementa apenas com as
verificações adicionais definidas no contrato aprovado na TASK 008
(`docs/decisao_modelo_operacional.md`, seção 7.1), que dependem
exclusivamente de artefatos públicos.

Este módulo **nunca** chama `modelagem.validate_artifacts` — essa função
exige hashes de arquivos privados em `local_data/` e não pode rodar num
deploy público. Este módulo também **nunca** treina, ajusta incrementalmente,
recalibra ou regenera nenhum artefato; ele apenas lê, valida e usa o que já
está congelado.

Não importa Streamlit: é utilizável e testável isoladamente (a TASK 010
adicionará os testes automatizados). `streamlit_app.py` é a única camada que
conhece a interface; este módulo só conhece dados e artefatos.
"""
from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

# Mesma convenção dos demais módulos de src/ (import plano entre irmãos):
# garante que `import modelagem` funcione mesmo se este arquivo for
# importado antes de qualquer outro ajuste de sys.path (ex.: diretamente por
# streamlit_app.py a partir da raiz do repositório).
_SRC_DIR = Path(__file__).resolve().parent
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

import modelagem  # noqa: E402
import rastreabilidade as rastro  # noqa: E402

# ---------------------------------------------------------------------------
# Contrato oficial (todos os valores lidos dos módulos existentes; nada
# duplicado ou reinventado aqui).
# ---------------------------------------------------------------------------

FEATURES: tuple[str, ...] = tuple(modelagem.FEATURES)
PHASE_FIELD = "fase_origem"
NUMERIC_FIELDS: tuple[str, ...] = tuple(f for f in FEATURES if f != PHASE_FIELD)
PHASE_CATEGORIES: tuple[str, ...] = tuple(modelagem.PHASES)
POSITIVE_LABEL = 1

CONTRACT_PATH = "docs/contrato_metodologico.md"
PUBLIC_INFERENCE_ARTIFACTS: tuple[str, ...] = (
    modelagem.MODEL, modelagem.SCHEMA, modelagem.FREEZE, modelagem.ACCESS, modelagem.METRICS,
)
PUBLIC_REQUIRED_PATHS: tuple[str, ...] = PUBLIC_INFERENCE_ARTIFACTS + (CONTRACT_PATH,)


class PublicValidationError(RuntimeError):
    """Artefato ausente, hash divergente ou schema incompatível.

    Sempre interrompe a aplicação de forma controlada; nunca é seguida de
    tentativa de correção, retreino ou regeneração automática."""


class InputValidationError(ValueError):
    """Entrada do usuário inválida. Nunca dispara inferência parcial."""


# ---------------------------------------------------------------------------
# Localização da raiz do projeto (portátil, sem caminho absoluto embutido).
# ---------------------------------------------------------------------------

def find_project_root(start: Path | str | None = None) -> Path:
    """Sobe diretórios a partir de `start` (por padrão, este arquivo)
    procurando os mesmos marcadores usados pelo notebook final:
    `src/modelagem.py` e `docs/TASKS.md`."""
    inicio = Path(start or __file__).resolve()
    for pasta in (inicio, *inicio.parents):
        if (pasta / "src" / "modelagem.py").is_file() and (pasta / "docs" / "TASKS.md").is_file():
            return pasta
    raise PublicValidationError(
        "Não foi possível localizar a raiz do repositório (procurando src/modelagem.py e docs/TASKS.md).")


# ---------------------------------------------------------------------------
# Validador público (contrato da TASK 008, seção 7.1 de
# docs/decisao_modelo_operacional.md).
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PublicValidationResult:
    """Resultado do validador público: artefatos já lidos e conferidos,
    prontos para carregar o modelo e realizar inferência."""
    frozen: dict
    schema: dict
    access: dict
    metrics: dict
    threshold: float


def check_public_paths_exist(root: Path) -> None:
    """Passo 1 do validador público: existência dos seis caminhos públicos
    (cinco artefatos de inferência + a dependência adicional de integridade
    `docs/contrato_metodologico.md`)."""
    ausentes = [caminho for caminho in PUBLIC_REQUIRED_PATHS if not (root / caminho).is_file()]
    if ausentes:
        raise PublicValidationError(
            "Artefato(s) público(s) ausente(s): " + ", ".join(ausentes))


def run_public_validator(root: Path) -> PublicValidationResult:
    """Executa o validador público completo, sem nunca chamar
    `modelagem.validate_artifacts` e sem nunca acessar `DATATHON/`,
    `local_data/` ou `local_recovery/`."""
    check_public_paths_exist(root)

    # Passos 2-... : reaproveita modelagem.validate_frozen por inteiro. Essa
    # função já confere (ver docs/decisao_modelo_operacional.md, seção 7.1):
    # hash canônico da configuração congelada, protocolo, hashes históricos
    # de código, hash de docs/contrato_metodologico.md, versões de pacotes,
    # e, ao ler o schema, schema["configuracao_sha256"], schema["colunas"]
    # (ordem dos sete preditores), schema["limiar"] e o hash do modelo
    # (schema["modelo_sha256"]) contra o arquivo .joblib real.
    try:
        frozen = modelagem.validate_frozen(root)
    except Exception as erro:  # noqa: BLE001 — qualquer falha aqui é de integridade, sem tentativa de correção.
        raise PublicValidationError(f"Configuração congelada ou schema inválidos: {erro}") from erro

    schema = modelagem.read_json(root / modelagem.SCHEMA)
    access = modelagem.read_json(root / modelagem.ACCESS)
    metrics = modelagem.read_json(root / modelagem.METRICS)

    # Redundância explícita da ordem dos sete preditores (já conferida dentro
    # de validate_frozen; repetida aqui apenas para tornar o validador
    # público autodescritivo, sem depender implicitamente de detalhes
    # internos de outra função).
    if list(schema.get("colunas", [])) != list(FEATURES):
        raise PublicValidationError("Ordem dos preditores do schema diverge do contrato oficial")

    # Hash portátil do arquivo do schema em si (distinto do modelo_sha256
    # que o schema carrega como conteúdo), contra o registro de
    # avaliacao_temporal.json.
    schema_hash_registrado = access.get("output_hashes", {}).get(modelagem.SCHEMA)
    if not schema_hash_registrado or not rastro.file_matches_sha256(root / modelagem.SCHEMA, schema_hash_registrado):
        raise PublicValidationError("Hash do arquivo schema_modelo.json divergente do registro oficial")

    # Hash binário exato do modelo, confirmado por duas fontes públicas
    # independentes (schema_modelo.json e avaliacao_temporal.json).
    hash_modelo_schema = schema.get("modelo_sha256")
    hash_modelo_access = access.get("output_hashes", {}).get(modelagem.MODEL)
    if not hash_modelo_schema or not hash_modelo_access or hash_modelo_schema != hash_modelo_access:
        raise PublicValidationError(
            "Hash do modelo divergente entre schema_modelo.json e avaliacao_temporal.json")
    if not rastro.file_matches_sha256(root / modelagem.MODEL, hash_modelo_schema):
        raise PublicValidationError("Hash do artefato modelo_avaliado.joblib divergente do registro oficial")

    # Igualdade dos três registros de configuracao_sha256 e do hash canônico
    # da configuração congelada.
    hash_canonico = frozen["sha256"]
    if modelagem.stable_hash(frozen["configuracao"]) != hash_canonico:
        raise PublicValidationError("Hash canônico da configuração congelada não confere")
    registros_configuracao_sha256 = {
        "schema_modelo.json.configuracao_sha256": schema.get("configuracao_sha256"),
        "avaliacao_temporal.json.configuracao_sha256": access.get("configuracao_sha256"),
        "metricas_modelagem.json.configuracao_sha256": metrics.get("configuracao_sha256"),
    }
    if any(valor != hash_canonico for valor in registros_configuracao_sha256.values()):
        raise PublicValidationError(
            "Registros de configuracao_sha256 divergentes do hash canônico: "
            f"{registros_configuracao_sha256} (canônico: {hash_canonico})")

    # Igualdade numérica (não textual) do limiar entre os três registros
    # públicos aplicáveis.
    limiar_config = frozen["configuracao"].get("limiar")
    limiar_schema = schema.get("limiar")
    limiar_metricas = metrics.get("limiar")
    limiares_validos = all(isinstance(v, (int, float)) and math.isfinite(v)
                           for v in (limiar_config, limiar_schema, limiar_metricas))
    if not limiares_validos or not (limiar_config == limiar_schema == limiar_metricas):
        raise PublicValidationError(
            f"Limiares divergentes entre artefatos públicos: configuracao={limiar_config}, "
            f"schema={limiar_schema}, metricas={limiar_metricas}")

    return PublicValidationResult(
        frozen=frozen, schema=schema, access=access, metrics=metrics, threshold=float(limiar_schema))


# ---------------------------------------------------------------------------
# Carregamento e compatibilidade do modelo (classes_, predict_proba).
# ---------------------------------------------------------------------------

def load_model(root: Path, schema: dict) -> Any:
    """Carrega o pipeline oficial (`joblib.load`, nunca `fit`) e confirma
    compatibilidade com o schema: `predict_proba` disponível, `classes_`
    igual a `[0, 1]` e classe positiva do schema presente em `classes_`."""
    try:
        pipeline = joblib.load(root / modelagem.MODEL)
    except Exception as erro:  # noqa: BLE001 — erro de carregamento é de integridade, não corrigível aqui.
        raise PublicValidationError(f"Falha ao carregar o artefato do modelo: {erro}") from erro

    if not hasattr(pipeline, "predict_proba"):
        raise PublicValidationError("Artefato carregado não expõe predict_proba")
    classes = getattr(pipeline, "classes_", None)
    if classes is None:
        raise PublicValidationError("Artefato carregado não expõe classes_")
    classes = [int(c) for c in classes]
    if classes != [0, 1]:
        raise PublicValidationError(f"Classes do modelo inesperadas: {classes} (esperado [0, 1])")

    # A classe positiva oficial (artifacts/schema_modelo.json.classe_positiva)
    # é o inteiro JSON `1` — nunca um booleano (`False`/`True` são o mesmo
    # que 0/1 em comparações numéricas do Python, mas não são o tipo
    # registrado no schema), nunca uma string ("1") e nunca um float (1.0,
    # que também não é o tipo registrado). A checagem de tipo é estrita
    # (`type(...) is int`, não `isinstance`) exatamente para excluir bool,
    # que é subtipo de int em Python.
    classe_positiva_schema = schema.get("classe_positiva")
    if type(classe_positiva_schema) is not int or classe_positiva_schema != POSITIVE_LABEL:
        raise PublicValidationError(
            f"Classe positiva do schema inválida: esperado o inteiro {POSITIVE_LABEL!r}, "
            f"obtido {classe_positiva_schema!r} (tipo {type(classe_positiva_schema).__name__})")
    return pipeline


def positive_class_index(pipeline: Any, positive_label: int = POSITIVE_LABEL) -> int:
    """Localiza a posição da classe positiva em `predict_proba` pelo valor
    real de `classes_` — nunca assume um índice fixo."""
    classes = list(pipeline.classes_)
    if positive_label not in classes:
        raise PublicValidationError(f"Classe positiva {positive_label} ausente em classes_={classes}")
    return classes.index(positive_label)


def _validate_probability_row(proba: Any, n_classes: int) -> np.ndarray:
    """Valida o retorno bruto de `predict_proba` antes de qualquer indexação.

    Confere, nesta ordem: conversão para estrutura numérica; exatamente duas
    dimensões; exatamente uma linha; pelo menos duas classes no modelo;
    número de colunas igual ao número de classes (`len(classes_)`); todos os
    valores da linha finitos; todos os valores em `[0, 1]`; e a soma da
    linha numericamente compatível com 1 (coerente com um classificador
    binário do scikit-learn). Qualquer divergência vira
    `PublicValidationError` — nunca `IndexError`, `TypeError` ou `ValueError`
    crus, nem a mensagem interna do modelo, chegam à interface."""
    try:
        matriz = np.asarray(proba, dtype=float)
    except (TypeError, ValueError) as erro:
        raise PublicValidationError("Retorno de predict_proba não é uma estrutura numérica válida") from erro

    if matriz.ndim != 2:
        raise PublicValidationError(f"Retorno de predict_proba com dimensão inesperada: {matriz.ndim} (esperado 2)")
    if matriz.shape[0] != 1:
        raise PublicValidationError(
            f"Retorno de predict_proba com número de linhas inesperado: {matriz.shape[0]} (esperado 1)")
    if n_classes < 2:
        raise PublicValidationError(f"Modelo com número de classes insuficiente: {n_classes} (esperado >= 2)")
    if matriz.shape[1] != n_classes:
        raise PublicValidationError(
            f"Retorno de predict_proba com {matriz.shape[1]} coluna(s); "
            f"esperado {n_classes} (tamanho de classes_ do modelo)")

    linha = matriz[0]
    if not np.all(np.isfinite(linha)):
        raise PublicValidationError("Retorno de predict_proba contém valores não finitos (NaN/±inf)")
    if bool(np.any(linha < 0.0) or np.any(linha > 1.0)):
        raise PublicValidationError("Retorno de predict_proba contém valores fora de [0, 1]")
    soma = float(np.sum(linha))
    if not math.isclose(soma, 1.0, rel_tol=1e-6, abs_tol=1e-6):
        raise PublicValidationError(f"Retorno de predict_proba não soma 1 (soma={soma})")
    return linha


# ---------------------------------------------------------------------------
# Validação e construção da entrada.
# ---------------------------------------------------------------------------

def _coerce_numeric_field(field: str, value: Any) -> float | None:
    """Converte um valor de formulário em `float` finito, ou `None` quando o
    campo foi deixado sem informação (ausência aceita e compatível com a
    imputação por mediana já embutida no pipeline). Rejeita texto não
    numérico, infinito e `NaN` digitados pelo usuário."""
    if value is None:
        return None
    if isinstance(value, str):
        texto = value.strip()
        if texto == "":
            return None
        valor_bruto: Any = texto
    else:
        valor_bruto = value
    if isinstance(valor_bruto, bool):  # bool é subtipo de int; nunca é uma entrada numérica válida.
        raise InputValidationError(f"Campo '{field}': valor inválido")
    try:
        numero = float(valor_bruto)
    except (TypeError, ValueError):
        raise InputValidationError(f"Campo '{field}': não é um número válido") from None
    if not math.isfinite(numero):
        raise InputValidationError(f"Campo '{field}': valor deve ser finito (não pode ser infinito ou 'NaN')")
    return numero


def validate_inputs(raw_inputs: dict) -> dict:
    """Valida os sete campos do contrato oficial e retorna um dicionário
    pronto para `build_feature_frame`.

    O payload precisa conter **exatamente** as sete chaves oficiais — nem
    uma a menos, nem uma a mais. Uma chave numérica presente pode valer
    `None` ou vazio (representa ausência do indicador); mas uma chave
    completamente ausente do payload é um erro de contrato, não uma
    ausência de indicador, e por isso nunca é preenchida silenciosamente.
    """
    if not isinstance(raw_inputs, dict):
        raise InputValidationError(
            f"Payload inválido: esperado um dicionário, obtido {type(raw_inputs).__name__}")

    chaves_informadas = set(raw_inputs)
    chaves_oficiais = set(FEATURES)
    ausentes = sorted(chaves_oficiais - chaves_informadas)
    extras = sorted(chaves_informadas - chaves_oficiais)
    if ausentes or extras:
        detalhes = []
        if ausentes:
            detalhes.append(f"ausente(s): {ausentes}")
        if extras:
            detalhes.append(f"fora do contrato oficial de sete preditores: {extras}")
        raise InputValidationError("Chave(s) inválida(s) no payload — " + "; ".join(detalhes))

    validado: dict[str, Any] = {}
    for campo in NUMERIC_FIELDS:
        validado[campo] = _coerce_numeric_field(campo, raw_inputs[campo])

    fase_bruta = raw_inputs[PHASE_FIELD]
    fase = "" if fase_bruta is None else str(fase_bruta).strip()
    if fase == "":
        raise InputValidationError(f"Campo '{PHASE_FIELD}': obrigatório, não pode ficar em branco")
    if fase not in PHASE_CATEGORIES:
        raise InputValidationError(
            f"Campo '{PHASE_FIELD}': valor '{fase}' fora do domínio oficial {PHASE_CATEGORIES}")
    validado[PHASE_FIELD] = fase
    return validado


def build_feature_frame(validado: dict) -> pd.DataFrame:
    """Monta o `DataFrame` de uma única observação, com as sete colunas
    exatamente na ordem oficial de `FEATURES`."""
    linha = {campo: validado[campo] for campo in FEATURES}
    frame = pd.DataFrame([linha], columns=list(FEATURES))
    frame[PHASE_FIELD] = frame[PHASE_FIELD].astype(str)
    return frame


# ---------------------------------------------------------------------------
# Inferência.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class InferenceResult:
    probability: float
    threshold: float
    is_risk: bool


def predict(pipeline: Any, frame: pd.DataFrame, threshold: float) -> InferenceResult:
    """Executa `predict_proba` (nunca `predict`, cujo limiar padrão seria
    0,5) e aplica o limiar congelado lido dos artefatos oficiais."""
    if list(frame.columns) != list(FEATURES):
        raise InputValidationError("Ordem das colunas de entrada diverge do contrato oficial")
    if len(frame) != 1:
        raise InputValidationError("A inferência pública aceita exatamente uma observação por vez")

    try:
        proba_bruta = pipeline.predict_proba(frame)
    except Exception as erro:  # noqa: BLE001 — nunca expor a mensagem interna do modelo à interface.
        raise PublicValidationError("Falha ao calcular a probabilidade com o modelo oficial") from erro

    linha = _validate_probability_row(proba_bruta, n_classes=len(pipeline.classes_))

    indice_positivo = positive_class_index(pipeline, positive_label=POSITIVE_LABEL)
    if not (0 <= indice_positivo < linha.shape[0]):
        raise PublicValidationError("Índice da classe positiva fora dos limites do retorno de predict_proba")
    probabilidade = float(linha[indice_positivo])

    if not (isinstance(threshold, (int, float)) and math.isfinite(threshold)):
        raise PublicValidationError("Limiar inválido para classificação")

    return InferenceResult(probability=probabilidade, threshold=float(threshold),
                           is_risk=probabilidade >= threshold)


# ---------------------------------------------------------------------------
# Orquestração de alto nível (usada por streamlit_app.py).
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ApplicationContext:
    """Estado carregado uma única vez por processo: raiz do projeto, modelo
    e resultado do validador público (inclui o limiar oficial)."""
    root: Path
    pipeline: Any
    validation: PublicValidationResult


def prepare_application(root: Path | str | None = None) -> ApplicationContext:
    """Ponto de entrada único de inicialização: localiza a raiz, executa o
    validador público e carrega o modelo. Levanta `PublicValidationError` em
    qualquer divergência — a interface deve capturar e interromper com
    `st.stop()`, sem tentar corrigir ou treinar nada."""
    raiz = find_project_root(root) if root is None else Path(root).resolve()
    resultado = run_public_validator(raiz)
    pipeline = load_model(raiz, resultado.schema)
    return ApplicationContext(root=raiz, pipeline=pipeline, validation=resultado)


def run_inference(context: ApplicationContext, raw_inputs: dict) -> InferenceResult:
    """Valida a entrada do usuário, monta o `DataFrame` oficial e executa a
    inferência com o limiar congelado do contexto já validado."""
    validado = validate_inputs(raw_inputs)
    frame = build_feature_frame(validado)
    return predict(context.pipeline, frame, context.validation.threshold)
