"""Auditoria experimental do recall temporal (2023→2024).

Investiga se o recall de 40,48% no teste temporal pode ser melhorado sem
retreinar o modelo — por escolha de limiar e/ou recalibração — SEM alterar
o modelo congelado, o limiar oficial (0.26696679375725973) ou qualquer
artefato em `artifacts/`/`reports/` fora de `reports/experimental/`.

Regra metodológica inegociável: todo candidato de limiar é escolhido
EXCLUSIVAMENTE com as predições OOF do desenvolvimento (`selecionar_candidatos`
só aceita `(y_dev, p_dev)` — nunca recebe nada do teste temporal). Os
candidatos só são aplicados ao teste temporal DEPOIS de definidos, uma
única vez, por `avaliar_candidatos_no_temporal`.

Reprodução: as probabilidades OOF são recalculadas com o mesmo protocolo
congelado (StratifiedKFold 5 folds, shuffle=True, random_state=42,
`modelagem.make_pipeline("logistica")`) e as probabilidades do teste
temporal vêm do modelo já congelado (`artifacts/modelo_avaliado.joblib`,
somente `.predict_proba`, sem novo ajuste). As duas reproduções são
verificadas byte a byte contra `reports/metricas_modelagem.json` antes de
qualquer experimento prosseguir — se divergirem, o script interrompe a
execução com erro explícito e não produz nenhuma recomendação.

Uso: `python scripts/experimento_recall_temporal.py`
Saída: `reports/experimental/analise_recall_temporal.json`,
`reports/experimental/grafico_candidatos.png`,
`reports/experimental/relatorio_tecnico.md`,
`reports/experimental/relatorio_professores.md`.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

import modelagem  # noqa: E402
from scripts import explorar_equidade_genero_modelo as equidade_genero  # noqa: E402

OUT_DIR = ROOT / "reports/experimental"
SEED = modelagem.SEED  # 42 — mesma semente do protocolo congelado, reaproveitada por consistência.


# --------------------------------------------------------------------------- #
# 1) Reprodução exata dos artefatos oficiais (nada é aceito sem bater 1:1)   #
# --------------------------------------------------------------------------- #

def carregar_dados_oficiais():
    frozen = modelagem.validate_frozen(ROOT)
    schema = modelagem.read_json(ROOT / modelagem.SCHEMA)
    limiar_oficial = schema["limiar"]
    inputs = frozen["configuracao"]["input_hashes"]
    Xd, yd = modelagem.load_cohort(ROOT, "desenvolvimento", inputs)
    Xt, yt = modelagem.load_cohort(ROOT, "teste_temporal", inputs, frozen=frozen)
    pipeline = joblib.load(ROOT / modelagem.MODEL)
    return frozen, schema, limiar_oficial, Xd, yd, Xt, yt, pipeline


def reproduzir_oof(Xd, yd):
    """Recalcula as probabilidades OOF do vencedor ("logistica") com o
    protocolo exatamente congelado. Determinístico (semente fixa + splits
    fixos): reexecutar produz sempre o mesmo array `p`."""
    splits = list(StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED).split(Xd, yd))
    resultado, p_oof, fold_id = modelagem.evaluate_oof(modelagem.make_pipeline("logistica"), Xd, yd, splits)
    return p_oof, resultado["limiar"]


def verificar_reproducao(yd, p_oof, limiar_oof_recalculado, Xt, yt, p_temporal, limiar_oficial):
    oficial = modelagem.read_json(ROOT / modelagem.METRICS)
    oof_recalculado = modelagem.metrics(yd, p_oof, limiar_oficial)
    temporal_recalculado = modelagem.metrics(yt, p_temporal, limiar_oficial)
    ok_limiar = abs(limiar_oof_recalculado - limiar_oficial) < 1e-9
    ok_oof = oof_recalculado == oficial["oof"]["metricas"]
    ok_temporal = temporal_recalculado == oficial["temporal"]["metricas"]
    if not (ok_limiar and ok_oof and ok_temporal):
        raise AssertionError(
            f"Reprodução divergente dos artefatos oficiais: "
            f"limiar={ok_limiar} oof={ok_oof} temporal={ok_temporal}. "
            f"Nenhum experimento prossegue com uma reprodução que não bate 1:1.")
    return {
        "limiar_oficial": limiar_oficial,
        "oof": oof_recalculado,
        "temporal": temporal_recalculado,
        "reproducao_confere": True,
    }


# --------------------------------------------------------------------------- #
# 2) Tabela de métricas por limiar único (base para todos os critérios)     #
# --------------------------------------------------------------------------- #

def _linha_limiar(y, p, t):
    m = modelagem.metrics(y, p, t)
    tn, fp = m["matriz_confusao"][0]
    fn, tp = m["matriz_confusao"][1]
    especificidade = tn / (tn + fp) if (tn + fp) else None
    vpn = tn / (tn + fn) if (tn + fn) else None
    acuracia = (tp + tn) / len(y)
    acuracia_balanceada = (m["recall"] + especificidade) / 2 if (m["recall"] is not None and especificidade is not None) else None
    f2 = None
    if m["precisao"] is not None and m["recall"] is not None and (4 * m["precisao"] + m["recall"]) > 0:
        f2 = 5 * m["precisao"] * m["recall"] / (4 * m["precisao"] + m["recall"])
    youden_j = (m["recall"] + especificidade - 1) if (m["recall"] is not None and especificidade is not None) else None
    return {
        "limiar": float(t), "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "sinalizados": m["previstos_risco"], "percentual_sinalizado": m["proporcao_risco"],
        "recall": m["recall"], "precisao": m["precisao"], "especificidade": especificidade,
        "vpn": vpn, "acuracia": acuracia, "acuracia_balanceada": acuracia_balanceada,
        "f1": m["f1"], "f2": f2, "youden_j": youden_j,
    }


def tabela_por_limiar(y, p):
    y = np.asarray(y)
    p = np.asarray(p, dtype=float)
    return [_linha_limiar(y, p, t) for t in sorted(set(p.tolist()))]


# --------------------------------------------------------------------------- #
# 3) Candidatos de limiar — SOMENTE a partir do desenvolvimento (OOF)        #
# --------------------------------------------------------------------------- #

def _melhor(tabela, elegivel, chave_primaria):
    """Regra determinística e documentada de desempate: entre os elegíveis,
    maior `chave_primaria`; empate → maior recall; novo empate → maior
    limiar. Usada por todos os critérios deste experimento."""
    candidatos = [linha for linha in tabela if elegivel(linha)]
    if not candidatos:
        return None
    return max(candidatos, key=lambda linha: (
        chave_primaria(linha), linha["recall"] or -1, linha["limiar"]))


def selecionar_candidatos(y_dev, p_dev, *, incluir_oficial=True):
    """Só aceita dados de desenvolvimento. Nunca recebe nada do teste
    temporal — a ausência do parâmetro é a garantia estrutural exigida
    aqui (ver teste `test_selecao_nao_aceita_dados_temporais`).

    `incluir_oficial=False` é usado apenas ao reaplicar os mesmos sete
    critérios sobre probabilidades RECALIBRADAS (seção 5): o limiar bruto
    congelado não existe nessa outra escala de probabilidade, então essa
    entrada não se aplica e é omitida — os outros sete critérios continuam
    normalmente, pois são recalculados na própria escala recalibrada."""
    tabela = tabela_por_limiar(y_dev, p_dev)
    definicoes = {}
    if incluir_oficial:
        limiar_oficial = modelagem.read_json(ROOT / modelagem.SCHEMA)["limiar"]
        linha_oficial = next((l for l in tabela if abs(l["limiar"] - limiar_oficial) < 1e-9), None)
        if linha_oficial is None:
            raise ValueError("Limiar oficial não encontrado entre os valores únicos do OOF recalculado")
        definicoes["limiar_oficial"] = {
            "criterio": "limiar já congelado (recall OOF >= 80%, maior precisão, "
                        "empate: maior recall, depois maior limiar) — carregado do artefato, não re-derivado",
            "linha": linha_oficial,
        }
    definicoes.update({
        "recall_minimo_85": {
            "criterio": "recall OOF >= 85%; maior precisão; empate: maior recall, depois maior limiar",
            "linha": _melhor(tabela, lambda l: l["recall"] is not None and l["recall"] >= 0.85, lambda l: l["precisao"] or -1),
        },
        "recall_minimo_90": {
            "criterio": "recall OOF >= 90%; maior precisão; empate: maior recall, depois maior limiar",
            "linha": _melhor(tabela, lambda l: l["recall"] is not None and l["recall"] >= 0.90, lambda l: l["precisao"] or -1),
        },
        "recall_minimo_95": {
            "criterio": "recall OOF >= 95%; maior precisão; empate: maior recall, depois maior limiar",
            "linha": _melhor(tabela, lambda l: l["recall"] is not None and l["recall"] >= 0.95, lambda l: l["precisao"] or -1),
        },
        "maior_f2": {
            "criterio": "maior F2 OOF; empate: maior recall, depois maior limiar",
            "linha": _melhor(tabela, lambda l: l["f2"] is not None, lambda l: l["f2"]),
        },
        "maior_youden_j": {
            "criterio": "maior Youden J (recall + especificidade - 1) OOF; empate: maior recall, depois maior limiar",
            "linha": _melhor(tabela, lambda l: l["youden_j"] is not None, lambda l: l["youden_j"]),
        },
        "maior_recall_precisao_minima_50": {
            "criterio": "precisão OOF >= 50%; maior recall; empate: maior precisão, depois maior limiar",
            "linha": _melhor(tabela, lambda l: l["precisao"] is not None and l["precisao"] >= 0.50, lambda l: l["recall"] or -1),
        },
        "maior_recall_precisao_minima_40": {
            "criterio": "precisão OOF >= 40%; maior recall; empate: maior precisão, depois maior limiar",
            "linha": _melhor(tabela, lambda l: l["precisao"] is not None and l["precisao"] >= 0.40, lambda l: l["recall"] or -1),
        },
    })
    return {nome: {"criterio": d["criterio"], "limiar": d["linha"]["limiar"], "oof": d["linha"]}
            for nome, d in definicoes.items() if d["linha"] is not None}


def avaliar_candidatos_no_temporal(candidatos, y_temporal, p_temporal):
    """Aplica cada limiar já definido no OOF, uma única vez, ao teste
    temporal. Não busca, não otimiza, não escolhe nada aqui — só mede."""
    saida = {}
    for nome, dados in candidatos.items():
        saida[nome] = {**dados, "temporal": _linha_limiar(y_temporal, p_temporal, dados["limiar"])}
    return saida


# --------------------------------------------------------------------------- #
# 4) Baseline majoritário                                                    #
# --------------------------------------------------------------------------- #

def baseline_majoritario(y):
    y = np.asarray(y)
    n = len(y)
    prevalencia = float(y.mean())
    return {
        "n": n, "eventos": int(y.sum()), "prevalencia": prevalencia,
        "acuracia": 1.0 - prevalencia,
        "acuracia_balanceada": 0.5,
        "recall_classe_positiva": 0.0,
        "recall_classe_negativa": 1.0,
        "precisao_classe_positiva": None,
    }


# --------------------------------------------------------------------------- #
# 5) Recalibração experimental (ajustada só no OOF, aplicada 1x ao temporal)#
# --------------------------------------------------------------------------- #

def recalibrar(yd, p_oof, yt, p_temporal):
    platt = LogisticRegression().fit(p_oof.reshape(-1, 1), yd)
    p_oof_platt = platt.predict_proba(p_oof.reshape(-1, 1))[:, 1]
    p_temporal_platt = platt.predict_proba(p_temporal.reshape(-1, 1))[:, 1]

    iso = IsotonicRegression(out_of_bounds="clip").fit(p_oof, yd)
    p_oof_iso = iso.transform(p_oof)
    p_temporal_iso = iso.transform(p_temporal)

    from sklearn.metrics import brier_score_loss
    from scipy.stats import spearmanr

    def _brier(y, p):
        return float(brier_score_loss(y, p))

    ordenacao_preservada_platt = float(spearmanr(p_temporal, p_temporal_platt).correlation)
    ordenacao_preservada_iso = float(spearmanr(p_temporal, p_temporal_iso).correlation)

    return {
        "platt": {
            "brier_oof_antes": _brier(yd, p_oof), "brier_oof_depois": _brier(yd, p_oof_platt),
            "brier_temporal_antes": _brier(yt, p_temporal), "brier_temporal_depois": _brier(yt, p_temporal_platt),
            "correlacao_de_postos_com_original_temporal": ordenacao_preservada_platt,
            "calibracao_oof_depois": modelagem.calibration(yd, p_oof_platt),
            "calibracao_temporal_depois": modelagem.calibration(yt, p_temporal_platt),
            "p_oof": p_oof_platt, "p_temporal": p_temporal_platt,
        },
        "isotonica": {
            "brier_oof_antes": _brier(yd, p_oof), "brier_oof_depois": _brier(yd, p_oof_iso),
            "brier_temporal_antes": _brier(yt, p_temporal), "brier_temporal_depois": _brier(yt, p_temporal_iso),
            "correlacao_de_postos_com_original_temporal": ordenacao_preservada_iso,
            "calibracao_oof_depois": modelagem.calibration(yd, p_oof_iso),
            "calibracao_temporal_depois": modelagem.calibration(yt, p_temporal_iso),
            "aviso": "Isotônica ajustada com apenas 60 eventos no desenvolvimento: poucos degraus, alto risco de sobreajuste local.",
            "p_oof": p_oof_iso, "p_temporal": p_temporal_iso,
        },
    }


# --------------------------------------------------------------------------- #
# 6) Incerteza por bootstrap (nunca mistura desenvolvimento e teste)        #
# --------------------------------------------------------------------------- #

def bootstrap_temporal(y, p, limiar_a, limiar_b, n=2000, seed=SEED):
    """IC95 por bootstrap não-pareado (recall/precisão/acurácia balanceada
    em cada limiar) e diferença PAREADA (mesmo resample) entre limiar_a
    (oficial) e limiar_b (candidato) — nunca mistura desenvolvimento e
    teste; usa somente o teste temporal."""
    y = np.asarray(y)
    p = np.asarray(p, dtype=float)
    n_obs = len(y)
    rng = np.random.default_rng(seed)
    metricas = ("recall", "precisao", "acuracia_balanceada")
    valores = {"a": {m: [] for m in metricas}, "b": {m: [] for m in metricas},
               "diferenca_b_menos_a": {m: [] for m in metricas}}
    for _ in range(n):
        idx = rng.integers(0, n_obs, n_obs)
        ya, pa = y[idx], p[idx]
        if ya.sum() == 0 or ya.sum() == len(ya):
            continue
        la = _linha_limiar(ya, pa, limiar_a)
        lb = _linha_limiar(ya, pa, limiar_b)
        for m in metricas:
            if la[m] is not None:
                valores["a"][m].append(la[m])
            if lb[m] is not None:
                valores["b"][m].append(lb[m])
            if la[m] is not None and lb[m] is not None:
                valores["diferenca_b_menos_a"][m].append(lb[m] - la[m])
    def _ic(vs):
        return {"ic95": np.quantile(vs, [0.025, 0.975]).tolist() if vs else None, "validas": len(vs), "invalidas": n - len(vs)}
    return {grupo: {m: _ic(vs) for m, vs in scores.items()} for grupo, scores in valores.items()}


# --------------------------------------------------------------------------- #
# 7) Equidade (gênero, faixa etária aproximada, fase) por limiar            #
# --------------------------------------------------------------------------- #

def _faixa_etaria(idade: int) -> str:
    """Mesmo binning de `scripts/explorar_equidade_genero_modelo.py`
    (função local não importável): reproduzido aqui, não reinventado."""
    if idade <= 10:
        return "7 a 10 anos"
    if idade <= 13:
        return "11 a 13 anos"
    if idade <= 16:
        return "14 a 16 anos"
    return "17 anos ou mais"


def _linkagem_genero_idade_temporal():
    """Reconstrói (X, y, proba, genero, faixa_etaria) do teste temporal na
    mesma ordem/ligação já auditada em
    `scripts/explorar_equidade_genero_modelo.py` — reaproveitado em vez de
    duplicado, exceto pela troca do limiar, que aquele script fixa no
    valor oficial e este precisa variar por candidato."""
    frozen = modelagem.validate_frozen(ROOT)
    pipeline = joblib.load(ROOT / modelagem.MODEL)
    linhas = []
    with open(ROOT / "local_data/coortes_modelagem.jsonl", encoding="utf-8") as f:
        for linha in f:
            r = json.loads(linha)
            if r["metadados"]["coorte"] == "teste_temporal" and r["y"] is not None:
                linhas.append(r)
    import pandas as pd
    X = pd.DataFrame([r["X"] for r in linhas], columns=modelagem.FEATURES)
    y = np.asarray([r["y"] for r in linhas], dtype=int)
    proba = pipeline.predict_proba(X)[:, 1]

    genero_por_chave, ano_nasc_por_chave, _ = equidade_genero._carregar_ligacao_base_longitudinal()
    chaves = [(r["chave_privada"]["ra"], r["metadados"]["ano_preditores"]) for r in linhas]
    generos = [genero_por_chave.get(c) for c in chaves]
    idades = [ano_o - ano_nasc_por_chave[c] if c in ano_nasc_por_chave else None
              for ano_o, c in zip((r["metadados"]["ano_preditores"] for r in linhas), chaves)]
    faixas = [_faixa_etaria(idade) if idade is not None else None for idade in idades]
    return X, y, proba, generos, faixas


def equidade_para_limiar(y, proba, generos, faixas, Xt_fase, limiar):
    por_genero = {g: equidade_genero._metricas(
        y[np.asarray([x == g for x in generos])], proba[np.asarray([x == g for x in generos])], limiar)
        for g in ("feminino", "masculino")}
    por_faixa = {f: equidade_genero._metricas(
        y[np.asarray([x == f for x in faixas])], proba[np.asarray([x == f for x in faixas])], limiar)
        for f in sorted({x for x in faixas if x is not None})}
    por_fase = {fase: modelagem.subgroup(y[Xt_fase.eq(fase)], proba[Xt_fase.eq(fase)], limiar) for fase in modelagem.PHASES}
    return {"genero": por_genero, "faixa_etaria_aproximada": por_faixa, "fase": por_fase}


# --------------------------------------------------------------------------- #
# 8) Simulação de impacto pedagógico                                        #
# --------------------------------------------------------------------------- #

def simulacao_pedagogica(linha_temporal):
    return {
        "estudantes_encaminhados_para_observacao": linha_temporal["sinalizados"],
        "casos_reais_encontrados": linha_temporal["tp"],
        "casos_reais_ainda_perdidos": linha_temporal["fn"],
        "acompanhamentos_adicionais_que_sao_falsos_positivos": linha_temporal["fp"],
    }


# --------------------------------------------------------------------------- #
# 9) Classificação de decisão                                                #
# --------------------------------------------------------------------------- #

def classificar_candidato(nome, dados, oficial_temporal, prevalencia_temporal):
    t = dados["temporal"]
    if nome == "limiar_oficial" or abs(dados["limiar"] - oficial_temporal["limiar"]) < 1e-9:
        # Limiar numericamente idêntico ao oficial (ex.: "maior_youden_j" pode
        # coincidir com o limiar já congelado) — não é "rejeitado", é o mesmo
        # ponto de operação por outro critério; documentado como coincidência.
        return "Manter o limiar oficial"
    ganho_recall = (t["recall"] or 0) - (oficial_temporal["recall"] or 0)
    perda_precisao = (oficial_temporal["precisao"] or 0) - (t["precisao"] or 0)
    if ganho_recall <= 0:
        return "Rejeitado"
    if t["precisao"] is None or t["precisao"] < prevalencia_temporal:
        # Pior que sinalizar por prevalência-base já é pior que um palpite informado.
        return "Rejeitado"
    if t["sinalizados"] > 3 * oficial_temporal["sinalizados"] and perda_precisao > 0.25:
        return "Somente experimental"
    if ganho_recall >= 0.15 and perda_precisao <= 0.20:
        return "Candidato operacional promissor"
    return "Somente experimental"


# --------------------------------------------------------------------------- #
# 10) Gráfico                                                                 #
# --------------------------------------------------------------------------- #

def gerar_grafico(candidatos_temporais, caminho):
    nomes = list(candidatos_temporais.keys())
    recalls = [candidatos_temporais[n]["temporal"]["recall"] or 0 for n in nomes]
    precisoes = [candidatos_temporais[n]["temporal"]["precisao"] or 0 for n in nomes]
    percentuais = [candidatos_temporais[n]["temporal"]["percentual_sinalizado"] for n in nomes]

    fig, ax = plt.subplots(figsize=(11, 6))
    x = np.arange(len(nomes))
    largura = 0.27
    ax.bar(x - largura, recalls, largura, label="Recall (teste temporal)", color="#1E5AA8")
    ax.bar(x, precisoes, largura, label="Precisão (teste temporal)", color="#2E9E6C")
    ax.bar(x + largura, percentuais, largura, label="% estudantes sinalizados", color="#C97A2B")
    ax.set_xticks(x)
    ax.set_xticklabels(nomes, rotation=35, ha="right", fontsize=8)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Proporção")
    ax.set_title("Candidatos de limiar — recall × precisão × % sinalizado (teste temporal 2023→2024)")
    ax.legend()
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(caminho, dpi=150)
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Orquestração                                                                #
# --------------------------------------------------------------------------- #

def executar() -> dict:
    frozen, schema, limiar_oficial, Xd, yd, Xt, yt, pipeline = carregar_dados_oficiais()
    p_oof, limiar_oof_recalculado = reproduzir_oof(Xd, yd)
    p_temporal = pipeline.predict_proba(Xt)[:, 1]
    reproducao = verificar_reproducao(yd, p_oof, limiar_oof_recalculado, Xt, yt, p_temporal, limiar_oficial)

    candidatos = selecionar_candidatos(yd, p_oof)
    candidatos = avaliar_candidatos_no_temporal(candidatos, yt, p_temporal)

    baseline_dev = baseline_majoritario(yd)
    baseline_temp = baseline_majoritario(yt)

    recalibracao = recalibrar(yd, p_oof, yt, p_temporal)
    # Após recalibrar, repete a MESMA lógica de seleção (maior F2), agora nas
    # probabilidades calibradas — só para demonstrar que a curva de trade-off
    # (o par recall/precisão atingível) não muda sob transformação monótona.
    for metodo in ("platt", "isotonica"):
        p_oof_cal = recalibracao[metodo]["p_oof"]
        p_temporal_cal = recalibracao[metodo]["p_temporal"]
        cand_cal = selecionar_candidatos(yd, p_oof_cal, incluir_oficial=False)
        cand_cal_avaliado = avaliar_candidatos_no_temporal(
            {"maior_f2": cand_cal["maior_f2"]}, yt, p_temporal_cal)
        recalibracao[metodo]["candidato_maior_f2_recalibrado_temporal"] = cand_cal_avaliado["maior_f2"]["temporal"]
        del recalibracao[metodo]["p_oof"], recalibracao[metodo]["p_temporal"]

    # Bootstrap: oficial vs. os dois candidatos mais promissores (decididos abaixo).
    classificacoes = {nome: classificar_candidato(nome, dados, candidatos["limiar_oficial"]["temporal"],
                       reproducao["temporal"]["prevalencia"])
                       for nome, dados in candidatos.items()}
    promissores = [n for n, c in classificacoes.items() if c == "Candidato operacional promissor" and n != "limiar_oficial"]
    promissores = sorted(promissores, key=lambda n: candidatos[n]["temporal"]["recall"] or 0, reverse=True)[:2]
    if not promissores:
        promissores = sorted(
            (n for n in candidatos if n != "limiar_oficial"),
            key=lambda n: (candidatos[n]["temporal"]["recall"] or 0), reverse=True)[:2]

    bootstrap = {nome: bootstrap_temporal(yt, p_temporal, limiar_oficial, candidatos[nome]["limiar"])
                 for nome in promissores}

    generos_idades = _linkagem_genero_idade_temporal()
    _, y_link, proba_link, generos_link, faixas_link = generos_idades
    np.testing.assert_array_equal(y_link, yt)
    np.testing.assert_allclose(proba_link, p_temporal)
    equidade = {"limiar_oficial": equidade_para_limiar(yt, p_temporal, generos_link, faixas_link, Xt.fase_origem, limiar_oficial)}
    for nome in promissores:
        equidade[nome] = equidade_para_limiar(yt, p_temporal, generos_link, faixas_link, Xt.fase_origem, candidatos[nome]["limiar"])

    impacto = {nome: simulacao_pedagogica(dados["temporal"]) for nome, dados in candidatos.items()}

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    gerar_grafico(candidatos, OUT_DIR / "grafico_candidatos.png")

    resultado = {
        "aviso": "Análise experimental — não congelada, não usada para decisão automática, "
                 "não substitui o modelo/limiar oficiais.",
        "reproducao": reproducao,
        "baseline_majoritario": {"desenvolvimento": baseline_dev, "temporal": baseline_temp},
        "candidatos": candidatos,
        "classificacoes": classificacoes,
        "candidatos_promissores_para_bootstrap_e_equidade": promissores,
        "impacto_pedagogico": impacto,
        "recalibracao": recalibracao,
        "bootstrap_temporal": bootstrap,
        "equidade": equidade,
    }
    (OUT_DIR / "analise_recall_temporal.json").write_text(
        json.dumps(resultado, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return resultado


if __name__ == "__main__":
    r = executar()
    print(json.dumps({"reproducao_confere": r["reproducao"]["reproducao_confere"],
                       "classificacoes": r["classificacoes"],
                       "promissores": r["candidatos_promissores_para_bootstrap_e_equidade"]}, ensure_ascii=False))
