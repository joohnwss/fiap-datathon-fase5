"""Gera `config/ponto_atencao_operacional.json` a partir do candidato já
selecionado e testado em `reports/experimental/analise_recall_temporal.json`
("maior recall mantendo precisão mínima de 40%").

Nunca digita o valor do limiar manualmente — recupera-o programaticamente
do JSON experimental e falha explicitamente se a matriz de confusão do
teste temporal não bater exatamente com 49 VP, 38 FP, 189 VN e 35 FN, ou
se o candidato não tiver sido definido exclusivamente com as predições OOF
do desenvolvimento.

Não retreina, não recalibra e não toca em nenhum artefato oficial
(`artifacts/`, `reports/metricas_modelagem.json`) — só lê o limiar
metodológico original do schema já congelado, para registro cruzado.

Uso: `python scripts/gerar_configuracao_operacional.py`
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import modelagem  # noqa: E402

FONTE = ROOT / "reports/experimental/analise_recall_temporal.json"
DESTINO = ROOT / "config/ponto_atencao_operacional.json"
NOME_CRITERIO = "maior_recall_precisao_minima_40"
MATRIZ_TEMPORAL_ESPERADA = {"tp": 49, "fp": 38, "tn": 189, "fn": 35}


def recuperar_candidato() -> dict:
    """Recupera o candidato do JSON experimental e confere, programaticamente,
    que ele foi definido só com o desenvolvimento (OOF) e que a matriz de
    confusão do teste temporal é exatamente a esperada."""
    if not FONTE.is_file():
        raise FileNotFoundError(
            f"Arquivo de origem ausente: {FONTE} — a análise experimental precisa "
            "ter sido executada antes desta geração.")
    dados = json.loads(FONTE.read_text(encoding="utf-8"))
    candidatos = dados.get("candidatos", {})
    if NOME_CRITERIO not in candidatos:
        raise AssertionError(f"Critério '{NOME_CRITERIO}' não encontrado em {FONTE}")
    candidato = candidatos[NOME_CRITERIO]

    if "oof" not in candidato or not isinstance(candidato["oof"], dict) or "criterio" not in candidato:
        raise AssertionError(
            "Candidato sem registro de métricas OOF/critério — não há garantia de "
            "que foi definido exclusivamente com o desenvolvimento")
    descricao = candidato["criterio"].lower()
    if "oof" not in descricao:
        raise AssertionError(f"Descrição do critério não confirma origem no OOF: {candidato['criterio']!r}")

    temporal = candidato["temporal"]
    obtido = {k: temporal[k] for k in MATRIZ_TEMPORAL_ESPERADA}
    if obtido != MATRIZ_TEMPORAL_ESPERADA:
        raise AssertionError(
            f"Matriz de confusão do teste temporal divergente do esperado: "
            f"obtido={obtido}, esperado={MATRIZ_TEMPORAL_ESPERADA}")

    return candidato


def _linha_metricas(linha: dict) -> dict:
    """Extrai só os campos públicos relevantes de uma linha de métricas do
    JSON experimental (mesma estrutura para o ponto original e o
    operacional) — nunca digitados manualmente."""
    return {
        "n": linha["tp"] + linha["fp"] + linha["tn"] + linha["fn"],
        "positivos_reais": linha["tp"] + linha["fn"],
        "sinalizados": linha["sinalizados"],
        "verdadeiros_positivos": linha["tp"],
        "falsos_positivos": linha["fp"],
        "falsos_negativos": linha["fn"],
        "verdadeiros_negativos": linha["tn"],
        "recall": linha["recall"],
        "precisao": linha["precisao"],
        "acuracia": linha["acuracia"],
        "acuracia_balanceada": linha["acuracia_balanceada"],
    }


def gerar() -> dict:
    dados = json.loads(FONTE.read_text(encoding="utf-8"))
    candidato = recuperar_candidato()
    if "limiar_oficial" not in dados["candidatos"]:
        raise AssertionError("Candidato 'limiar_oficial' ausente no JSON experimental")
    ponto_original_temporal = dados["candidatos"]["limiar_oficial"]["temporal"]

    schema = modelagem.read_json(ROOT / modelagem.SCHEMA)
    limiar_metodologico_original = schema["limiar"]
    if abs(limiar_metodologico_original - ponto_original_temporal["limiar"]) > 1e-9:
        raise AssertionError(
            "Limiar metodológico original do schema divergente do candidato "
            f"'limiar_oficial' no JSON experimental: {limiar_metodologico_original!r} != "
            f"{ponto_original_temporal['limiar']!r}")
    limiar_operacional = candidato["limiar"]
    origem_hash = hashlib.sha256(FONTE.read_bytes()).hexdigest()

    config = {
        "versao": 1,
        "finalidade": (
            "Ponto de atenção operacional usado pela aplicação pública para decidir "
            "se um caso fica acima ou abaixo do ponto de atenção — separado do "
            "artefato metodológico original, que permanece intacto e é usado só "
            "para rastreabilidade em \"Modelo e limitações\"."
        ),
        "modelo": (
            "Mesmo modelo oficial congelado (artifacts/modelo_avaliado.joblib), "
            "sem retreino e sem recalibração. Esta configuração altera apenas a "
            "regra de comparação da probabilidade já calculada pelo modelo, nunca "
            "a probabilidade em si."
        ),
        "limiar_metodologico_original": limiar_metodologico_original,
        "ponto_atencao_operacional": {
            "limiar": limiar_operacional,
            "nome_criterio": NOME_CRITERIO,
            "criterio": candidato["criterio"],
        },
        "criterio_selecao": (
            "Maior recall mantendo precisão mínima de 40%, definido exclusivamente "
            "com as predições OOF do desenvolvimento (nunca olhando o teste "
            "temporal na escolha) e aplicado uma única vez ao teste temporal — "
            "ver reports/experimental/relatorio_tecnico.md, seção 4."
        ),
        "data_da_decisao": "2026-09-25",
        "metricas_temporais": {
            "ponto_metodologico_original": _linha_metricas(ponto_original_temporal),
            "ponto_operacional_adotado": _linha_metricas(candidato["temporal"]),
        },
        "avisos": {
            "altera_somente_a_classificacao": (
                "Este ajuste muda somente o valor com que a probabilidade já "
                "calculada pelo modelo é comparada para decidir a sinalização. A "
                "probabilidade individual de cada caso não muda."
            ),
            "supervisao_humana": (
                "Toda sinalização é apoio à priorização e deve ser sempre revisada "
                "por uma equipe pedagógica ou profissional responsável."
            ),
            "abaixo_do_ponto_nao_elimina_risco": (
                "Um resultado abaixo do ponto de atenção operacional não elimina o "
                "risco: parte dos casos reais permanece sem sinalização, mesmo com "
                "este ajuste."
            ),
        },
        "origem": {
            "arquivo": "reports/experimental/analise_recall_temporal.json",
            "sha256_no_momento_da_decisao": origem_hash,
            "criterio_definido_somente_com_oof_do_desenvolvimento": True,
            "aplicado_uma_unica_vez_ao_teste_temporal": True,
        },
    }
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return config


if __name__ == "__main__":
    config = gerar()
    print(json.dumps({
        "limiar_metodologico_original": config["limiar_metodologico_original"],
        "limiar_operacional": config["ponto_atencao_operacional"]["limiar"],
        "destino": str(DESTINO),
    }, ensure_ascii=False))
