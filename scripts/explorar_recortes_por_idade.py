"""Achados exploratórios complementares por faixa etária (correção
pós-auditoria comparativa, 24/09/2026).

O campo `idade_numerico` tem inconsistência documentada (399/1.014 registros
de 2023 trazem uma data, não um número — ver docs/mapa_campos.md). Em vez de
descartar idade integralmente, este script usa uma recuperação SEGURA e
DETERMINÍSTICA, já presente no pipeline aprovado: `ano_nascimento_padronizado`
tem cobertura de 100% (3.030/3.030 registros) porque, mesmo quando o campo
"idade" original trazia uma data (status "extraido_data_sem_inferir_dia_mes"),
o pipeline já extraiu SÓ o ano de nascimento dessa data — sem inferir dia ou
mês, sem inventar nada. `idade_aproximada = ano_referencia - ano_nascimento`
está, portanto, disponível para 100% dos registros, com valores no intervalo
plausível 7-28 anos (nenhum valor negativo ou absurdo).

IMPORTANTE: essa é uma SUBTRAÇÃO DE ANOS, não uma idade exata — dia e mês de
nascimento não estão disponíveis, então a idade real pode diferir em quase
um ano da "idade aproximada", e um estudante perto de uma fronteira de faixa
pode estar na faixa vizinha na idade real. A camada pública nunca chama o
resultado de "idade" sozinho, sempre de "idade aproximada" ou "faixa etária
aproximada" (correção pós-auditoria comparativa, rodada 3, 24/09/2026).

Reaproveita as MESMAS funções de privacidade já aprovadas e congeladas em
src/analises_negocio.py — não modifica esse arquivo nem o artefato interno
congelado. Resultado não é congelado; reportado como achado exploratório.

Uso: `python scripts/explorar_recortes_por_idade.py [caminho_saida.json]`
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from preparacao_coortes import load_prepared, origin_exclusion  # noqa: E402
from analises_negocio import summary, distribution, association  # noqa: E402
from auditoria_inicial import pair_records  # noqa: E402
from dados_pede import ROOT as DADOS_ROOT  # noqa: E402

FAIXAS = ("7 a 10 anos", "11 a 13 anos", "14 a 16 anos", "17 anos ou mais")


def _faixa(idade: int) -> str:
    if idade <= 10:
        return FAIXAS[0]
    if idade <= 13:
        return FAIXAS[1]
    if idade <= 16:
        return FAIXAS[2]
    return FAIXAS[3]


def _frame_com_idade(records: list[dict]) -> pd.DataFrame:
    linhas = []
    for r in records:
        idade_aprox = int(r["ano_referencia"]) - int(float(r["ano_nascimento_padronizado"]))
        linhas.append({
            "ano": r["ano_referencia"], "faixa": _faixa(idade_aprox),
            "idade_aproximada": idade_aprox, "categoria": r["categoria_defasagem"],
            "ida": r["ida_numerico"], "ieg": r["ieg_numerico"], "ipv": r["ipv_numerico"],
        })
    return pd.DataFrame(linhas)


def q3_associacoes_por_faixa(df: pd.DataFrame) -> dict:
    resultado = {}
    for faixa, h in df.groupby("faixa"):
        resultado[faixa] = {
            "ieg x ida": association(h.ida, h.ieg, h.ano),
            "ieg x ipv": association(h.ipv, h.ieg, h.ano),
        }
    return resultado


def q1_defasagem_por_faixa(df: pd.DataFrame) -> dict:
    resultado = {}
    for ano in (2022, 2023, 2024):
        g = df[df.ano == ano]
        por_faixa = {}
        for faixa, h in g.groupby("faixa"):
            entrada = distribution(
                h.categoria.fillna("Ausente").tolist(),
                ["sem_defasagem", "moderada", "severa", "Ausente"],
            )
            entrada["n_faixa"] = len(h)
            por_faixa[faixa] = entrada
        resultado[str(ano)] = por_faixa
    return resultado


def q2_ida_por_faixa(df: pd.DataFrame) -> dict:
    resultado = {}
    for ano in (2022, 2023, 2024):
        g = df[df.ano == ano]
        resultado[str(ano)] = {faixa: summary(h.ida) for faixa, h in g.groupby("faixa")}
    return resultado


def q10_ida_pareado_por_faixa(records: list[dict]) -> dict:
    resultado = {}
    for origin, target in ((2022, 2023), (2023, 2024)):
        pairs = pair_records(records, origin, target, how="inner")
        left = [records[int(i)] for i in pairs.record_index_origem]
        right = [records[int(i)] for i in pairs.record_index_destino]
        a = _frame_com_idade(left)
        b = _frame_com_idade(right)
        delta = b.ida - a.ida
        por_faixa = {}
        for faixa in a.faixa.unique():
            mascara = (a.faixa == faixa).values
            por_faixa[faixa] = summary(delta[mascara])
        resultado[f"{origin}→{target}"] = por_faixa
    return resultado


def q11_perdas_por_faixa(records: list[dict]) -> dict:
    resultado = {}
    for origin, target in ((2022, 2023), (2023, 2024)):
        joined = pair_records(records, origin, target, how="left")
        grupos: dict[str, list] = {}
        for row in joined.to_dict("records"):
            r = records[int(row["record_index_origem"])]
            if origin_exclusion(r) is not None:
                continue
            found = row["_merge"] == "both"
            idade_aprox = int(r["ano_referencia"]) - int(float(r["ano_nascimento_padronizado"]))
            chave = f"{_faixa(idade_aprox)}_{'encontrados' if found else 'nao_encontrados'}"
            grupos.setdefault(chave, []).append(r)
        resultado[f"{origin}→{target}"] = {
            chave: {"n": len(rows), "ida": summary([r["ida_numerico"] for r in rows])}
            for chave, rows in grupos.items()
        }
    return resultado


def main() -> None:
    records = load_prepared(DADOS_ROOT)
    df = _frame_com_idade(records)
    resultado = {
        "cobertura_idade_aproximada": {
            "total": len(df), "por_faixa": {f: int(n) for f, n in df.faixa.value_counts().items()},
            "min": int(df.idade_aproximada.min()), "max": int(df.idade_aproximada.max()),
        },
        "q1_defasagem_por_faixa": q1_defasagem_por_faixa(df),
        "q2_ida_por_faixa": q2_ida_por_faixa(df),
        "q3_associacoes_por_faixa": q3_associacoes_por_faixa(df),
        "q10_ida_pareado_por_faixa": q10_ida_pareado_por_faixa(records),
        "q11_perdas_por_faixa": q11_perdas_por_faixa(records),
    }
    saida = json.dumps(resultado, indent=2, ensure_ascii=False, default=str)
    if len(sys.argv) > 1:
        Path(sys.argv[1]).write_text(saida, encoding="utf-8")
    else:
        print(saida)


if __name__ == "__main__":
    main()
