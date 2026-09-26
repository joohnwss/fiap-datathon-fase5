"""Auditoria de equidade do modelo por gênero e por faixa etária aproximada:
tenta a ligação metodologicamente correta entre as predições do teste
temporal e o gênero/idade do estudante, com auditoria explícita da chave
de ligação.

O artefato oficial (reports/metricas_modelagem.json, robustez.equidade_genero)
registra "indisponível" porque as COORTES em formato tabular (CSV/X, y)
não retêm RA nem gênero. Porém `local_data/coortes_modelagem.jsonl` retém,
para cada linha, um bloco `chave_privada.ra` explicitamente destinado a
auditoria (ver docs do próprio pipeline) — o mesmo padrão que
`src/modelagem.py` usa internamente (`pd.DataFrame([r["X"] for r in rows],
columns=FEATURES)`) para reconstruir X a partir do JSONL.

CHAVE DE LIGAÇÃO — auditoria explícita:
um mesmo RA pode aparecer em mais de um ano em `local_data/
base_longitudinal.csv` (um registro por ano letivo por estudante), e uma
auditoria a essa própria base encontrou 12 RAs com `genero_padronizado`
inconsistente entre anos e 8 RAs com `ano_nascimento_padronizado`
inconsistente entre anos (INCONSISTÊNCIA CADASTRAL, não erro de ligação —
já esperada e documentada na auditoria de equidade por fase do artefato
oficial). Ligar apenas por RA (ignorando o ano) herdaria essa ambiguidade
sem necessidade. Por isso a chave de ligação usada aqui é a chave
COMPOSTA (RA, ano de referência dos preditores) — `(ra, ano_preditores)` —
que é a mesma convenção de identidade de registro já usada em todo o
projeto (ex.: `local_data/base_longitudinal.csv` tem exatamente uma linha
por par (ra, ano_referencia), confirmado abaixo). Isso reduz a zero as
ambiguidades: cada linha do teste temporal é ligada exatamente ao registro
do MESMO ano em que os preditores foram observados, nunca a um ano
diferente do mesmo estudante.

Este script: (1) carrega o MODELO CONGELADO sem retreinar; (2) reconstrói X
exatamente como o pipeline oficial faz a partir do JSONL; (3) confirma que
as métricas agregadas batem com as já publicadas (prova de que a
reconstrução é fiel, ANTES de qualquer quebra por subgrupo); (4) audita a
cardinalidade da ligação (ra, ano_preditores) -> base_longitudinal.csv
passo a passo (linhas antes, linhas depois, duplicação, correspondência
múltipla, linhas sem correspondência); (5) recalcula recall/precisão/AP/
ROC-AUC por gênero e por faixa etária aproximada, com a MESMA regra de supressão já
usada em `robustez.equidade_fase` (n>=30 e >=5 eventos/não eventos), e não
publica AP/ROC-AUC quando um grupo (mesmo que publicável pela regra acima)
não contém as duas classes — mostra "não estimável para este grupo" em
vez de um valor inventado.

Não retreina, não recalibra, não altera o modelo nem o limiar. Resultado
não é congelado; reportado como achado exploratório.

Uso: `python scripts/explorar_equidade_genero_modelo.py [caminho_saida.json]`
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from preparacao_coortes import FEATURES  # noqa: E402
import modelagem  # noqa: E402


def _metricas(y_true, proba, limiar) -> dict:
    """Métricas de subgrupo com supressão de privacidade (n>=30 e >=5
    eventos/não eventos) e sem publicar AP/ROC-AUC quando falta uma classe."""
    y_true = np.asarray(y_true)
    n = len(y_true)
    eventos = int(y_true.sum())
    nao_eventos = n - eventos
    duas_classes = len(set(y_true.tolist())) > 1
    if n < 30 or eventos < 5 or nao_eventos < 5:
        # A própria linha é potencialmente identificável. Portanto, nenhum
        # total, evento ou componente da matriz de confusão é devolvido. A
        # condição matemática de AP/ROC-AUC pode ser informada sem revelar a
        # célula protegida.
        return {
            "status": "suprimido por privacidade",
            "n": "suprimido", "positivos": "suprimido", "negativos": "suprimido",
            "alertas": "suprimido", "verdadeiros_positivos": "suprimido",
            "falsos_positivos": "suprimido", "falsos_negativos": "suprimido",
            "recall": "suprimido", "precisao": "suprimido",
            "average_precision": ("não estimável para este grupo" if not duas_classes else "suprimido"),
            "roc_auc": ("não estimável para este grupo" if not duas_classes else "suprimido"),
        }

    pred = (proba >= limiar).astype(int)
    tp = int(((pred == 1) & (y_true == 1)).sum())
    fp = int(((pred == 1) & (y_true == 0)).sum())
    fn = int(((pred == 0) & (y_true == 1)).sum())
    alertas = int((pred == 1).sum())
    recall = tp / eventos if eventos else None
    precisao = tp / (tp + fp) if (tp + fp) else None

    return {
        "status": "estimado",
        "n": n, "positivos": eventos, "negativos": nao_eventos,
        "alertas": alertas, "verdadeiros_positivos": tp,
        "falsos_positivos": fp, "falsos_negativos": fn,
        "recall": recall, "precisao": precisao,
        "average_precision": float(average_precision_score(y_true, proba)) if duas_classes else "não estimável para este grupo",
        "roc_auc": float(roc_auc_score(y_true, proba)) if duas_classes else "não estimável para este grupo",
    }


def _carregar_ligacao_base_longitudinal() -> tuple[dict, dict, dict]:
    """Carrega genero/ano_nascimento por (ra, ano_referencia) — chave
    composta, não apenas RA. Confirma, primeiro, que essa chave composta é
    de fato única na base (sem correspondência múltipla silenciosa)."""
    linhas = []
    with open(ROOT / "local_data/base_longitudinal.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            linhas.append(row)

    chaves = [(r["ra"], int(r["ano_referencia"])) for r in linhas]
    duplicadas = len(chaves) - len(set(chaves))
    if duplicadas:
        raise AssertionError(f"chave composta (ra, ano_referencia) tem {duplicadas} duplicatas — não é segura para ligação 1:1")

    genero_por_chave = {(r["ra"], int(r["ano_referencia"])): r["genero_padronizado"] for r in linhas}
    ano_nasc_por_chave = {(r["ra"], int(r["ano_referencia"])): int(float(r["ano_nascimento_padronizado"])) for r in linhas}
    estatisticas = {
        "total_linhas_base_longitudinal": len(linhas),
        "chaves_compostas_distintas_na_base": len(set(chaves)),
        "duplicatas_da_chave_composta_na_base": duplicadas,
        "ras_distintos_na_base": len({r["ra"] for r in linhas}),
    }
    return genero_por_chave, ano_nasc_por_chave, estatisticas


def _auditar_cardinalidade(linhas_teste: list[dict], genero_por_chave: dict, ano_nasc_por_chave: dict) -> dict:
    """Registra, passo a passo, a cardinalidade da ligação — para provar
    que não há duplicação nem correspondência múltipla introduzida por ela."""
    ras = [r["chave_privada"]["ra"] for r in linhas_teste]
    anos_preditores = [r["metadados"]["ano_preditores"] for r in linhas_teste]
    chaves_teste = list(zip(ras, anos_preditores))

    linhas_antes = len(linhas_teste)
    ras_distintos_antes = len(set(ras))
    chaves_distintas_antes = len(set(chaves_teste))
    duplicacao_ra_isolado = linhas_antes - ras_distintos_antes  # >0 confirma por que RA sozinho seria ambíguo
    duplicacao_chave_composta = linhas_antes - chaves_distintas_antes  # deve ser 0

    correspondencias = [chave in genero_por_chave for chave in chaves_teste]
    linhas_sem_correspondencia = correspondencias.count(False)
    linhas_depois = correspondencias.count(True)

    return {
        "chave_de_ligacao": "(ra, ano_preditores) — composta, não apenas RA",
        "linhas_antes_da_ligacao": linhas_antes,
        "ras_distintos": ras_distintos_antes,
        "linhas_com_ra_repetido_em_anos_diferentes": duplicacao_ra_isolado,
        "chaves_compostas_distintas": chaves_distintas_antes,
        "duplicacao_apos_chave_composta": duplicacao_chave_composta,
        "linhas_sem_correspondencia_na_base_longitudinal": linhas_sem_correspondencia,
        "linhas_com_correspondencia_apos_ligacao": linhas_depois,
        "correspondencia_multipla_detectada": False,  # garantido por _carregar_ligacao_base_longitudinal (chave composta única)
    }


def _digest_array(valores) -> str:
    """Fingerprint posicional: mesma ordem e mesmos valores produzem o
    mesmo hash; qualquer permutação muda o resultado."""
    arr = np.ascontiguousarray(np.asarray(valores))
    payload = f"{arr.dtype}|{arr.shape}|".encode("ascii") + arr.tobytes()
    return hashlib.sha256(payload).hexdigest()


def executar_auditoria() -> dict:
    """Executa a auditoria completa e devolve somente evidências agregadas.

    A função separada permite que os testes comprovem o comportamento real
    da ligação, em vez de procurar frases no código ou no relatório.
    """
    # 1) modelo congelado, sem retreinar
    frozen = modelagem.validate_frozen(ROOT)
    schema = modelagem.read_json(ROOT / "artifacts/schema_modelo.json")
    limiar = schema["limiar"]
    pipeline = joblib.load(ROOT / modelagem.MODEL)

    # 2) X, y e RA reconstruídos do JSONL exatamente como o pipeline oficial,
    # preservando a ordem original das linhas (X, y, proba e rótulos nunca
    # são reordenados de forma independente uns dos outros)
    linhas = []
    with open(ROOT / "local_data/coortes_modelagem.jsonl", encoding="utf-8") as f:
        for linha in f:
            r = json.loads(linha)
            if r["metadados"]["coorte"] == "teste_temporal" and r["y"] is not None:
                linhas.append(r)
    X = pd.DataFrame([r["X"] for r in linhas], columns=FEATURES)
    y = np.asarray([r["y"] for r in linhas], dtype=int)

    # A coorte tabular é a entrada efetivamente usada na avaliação oficial.
    # A igualdade posicional com a reconstrução do JSONL comprova que RA/ano
    # serão anexados à mesma linha de rótulo e probabilidade, sem merge que
    # possa reordenar ou multiplicar registros.
    X_oficial, y_oficial = modelagem.load_cohort(
        ROOT, "teste_temporal", frozen["configuracao"]["input_hashes"], frozen=frozen,
    )
    numericos_iguais = all(
        np.array_equal(
            X[coluna].to_numpy(dtype=float),
            X_oficial[coluna].to_numpy(dtype=float),
            equal_nan=True,
        )
        for coluna in FEATURES if coluna != "fase_origem"
    )
    fase_igual = X["fase_origem"].astype(str).tolist() == X_oficial["fase_origem"].astype(str).tolist()
    rotulos_iguais = np.array_equal(y, y_oficial)
    if not (numericos_iguais and fase_igual and rotulos_iguais):
        raise AssertionError("ordem da reconstrução JSONL diverge da coorte oficial")

    proba = pipeline.predict_proba(X)[:, 1]
    proba_oficial = pipeline.predict_proba(X_oficial)[:, 1]
    assert len(proba) == len(linhas) == len(y), "ordem de X/y/proba/linhas precisa permanecer alinhada 1:1"
    probabilidades_iguais = np.array_equal(proba, proba_oficial)
    if not probabilidades_iguais:
        raise AssertionError("probabilidades reconstruídas divergem da ordem da coorte oficial")

    auditoria_ordem = {
        "linhas": len(linhas),
        "preditores_na_ordem_oficial": numericos_iguais and fase_igual,
        "rotulos_na_ordem_oficial": rotulos_iguais,
        "probabilidades_na_ordem_oficial": probabilidades_iguais,
        "sha256_rotulos_posicionais": _digest_array(y),
        "sha256_probabilidades_posicionais": _digest_array(proba),
    }

    # 3) reproducao fiel: confirma contra o artefato oficial ja publicado,
    # ANTES de qualquer quebra por subgrupo
    oficial = modelagem.read_json(ROOT / "reports/metricas_modelagem.json")["temporal"]["metricas"]
    reproduzido = modelagem.metrics(y, proba, limiar)
    confere = reproduzido == oficial
    if not confere:
        raise AssertionError("métricas globais reconstruídas divergem do artefato oficial")

    # 4) ligação (ra, ano_preditores) -> genero/ano_nascimento — chave
    # composta, auditada explicitamente
    genero_por_chave, ano_nasc_por_chave, estatisticas_base = _carregar_ligacao_base_longitudinal()
    auditoria_cardinalidade = _auditar_cardinalidade(linhas, genero_por_chave, ano_nasc_por_chave)
    auditoria_cardinalidade.update(estatisticas_base)

    chaves = [(r["chave_privada"]["ra"], r["metadados"]["ano_preditores"]) for r in linhas]
    generos = [genero_por_chave.get(c) for c in chaves]
    sem_genero = sum(1 for g in generos if g is None)

    def _faixa(idade: int) -> str:
        if idade <= 10:
            return "7 a 10 anos"
        if idade <= 13:
            return "11 a 13 anos"
        if idade <= 16:
            return "14 a 16 anos"
        return "17 anos ou mais"

    idades_calc = [ano_o - ano_nasc_por_chave[c] if c in ano_nasc_por_chave else None
                   for ano_o, c in zip((r["metadados"]["ano_preditores"] for r in linhas), chaves)]
    faixas = [_faixa(idade) if idade is not None else None for idade in idades_calc]

    # 5) metricas por genero e por faixa etaria, mesma regra de supressao
    # de equidade_fase (n>=30 e >=5 eventos/nao eventos); AP/ROC-AUC nunca
    # publicados se faltar uma classe
    resultado_por_genero = {}
    for genero in ("feminino", "masculino"):
        mascara = np.asarray([g == genero for g in generos], dtype=bool)
        resultado_por_genero[genero] = _metricas(y[mascara], proba[mascara], limiar)

    resultado_por_faixa = {}
    for faixa in sorted({f for f in faixas if f is not None}):
        mascara = np.asarray([f == faixa for f in faixas], dtype=bool)
        resultado_por_faixa[faixa] = _metricas(y[mascara], proba[mascara], limiar)

    saida = {
        "auditoria_da_chave_de_ligacao": auditoria_cardinalidade,
        "auditoria_da_ordem": auditoria_ordem,
        "reproducao_fiel_do_artefato_oficial": confere,
        "reproduzido": reproduzido,
        "oficial_para_comparacao": oficial,
        "ras_sem_genero_encontrado": sem_genero,
        "equidade_por_genero": resultado_por_genero,
        "equidade_por_faixa_etaria": resultado_por_faixa,
    }
    return saida


def main() -> None:
    saida = executar_auditoria()
    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    texto = json.dumps(saida, indent=2, ensure_ascii=False, default=str)
    if out_path:
        out_path.write_text(texto, encoding="utf-8")
    else:
        print(texto)


if __name__ == "__main__":
    main()
