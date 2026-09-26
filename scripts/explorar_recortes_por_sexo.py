"""Achados exploratórios complementares por sexo (correção pós-auditoria
comparativa, 24/09/2026): Q1 (defasagem por sexo), Q2 (IDA por sexo), Q3
(IEG×IDA/IPV por sexo), Q10 (IDA por sexo entre pares longitudinais) e Q11
(perda de correspondência por sexo).

Reaproveita as MESMAS funções de privacidade já aprovadas e congeladas em
src/analises_negocio.py (summary/distribution/association/pair_records) —
não modifica esse arquivo nem o artefato interno congelado
(reports/metricas_analises_negocio.json). O campo `genero_padronizado` (não
incluído na lista positiva de `analytic_frame()` daquele módulo) é lido
diretamente de `local_data/base_longitudinal.csv`/`.jsonl` aqui, apenas para
esta exploração.

O resultado não é congelado nem tem hash verificado; é reportado na camada
pública explicitamente como "achado exploratório", nunca misturado com os
números oficiais.

Uso: `python scripts/explorar_recortes_por_sexo.py`
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from preparacao_coortes import load_prepared, origin_exclusion  # noqa: E402
from analises_negocio import summary, distribution, association, MIN_PROFILE  # noqa: E402
from auditoria_inicial import pair_records  # noqa: E402
from dados_pede import ROOT as DADOS_ROOT  # noqa: E402


def _frame_com_genero(records: list[dict]) -> pd.DataFrame:
    """Como analytic_frame() de src/analises_negocio.py, mas incluindo
    genero_padronizado — usado só nesta exploração, nunca no artefato
    congelado."""
    return pd.DataFrame([{
        "ano": r["ano_referencia"], "genero": r["genero_padronizado"],
        "fase": r["fase_extraida"], "categoria": r["categoria_defasagem"],
        "ida": r["ida_numerico"], "ieg": r["ieg_numerico"], "ipv": r["ipv_numerico"],
    } for r in records])


def q1_defasagem_por_sexo(df: pd.DataFrame) -> dict:
    resultado = {}
    for ano in (2022, 2023, 2024):
        g = df[df.ano == ano]
        por_genero = {}
        for genero, h in g.groupby("genero"):
            entrada = distribution(
                h.categoria.fillna("Ausente").tolist(),
                ["sem_defasagem", "moderada", "severa", "Ausente"],
            )
            entrada["n_genero"] = len(h)
            por_genero[genero] = entrada
        resultado[str(ano)] = por_genero
    return resultado


_BINARIO = {"sem_defasagem": "sem_defasagem", "moderada": "alguma_defasagem", "severa": "alguma_defasagem"}


def q1_defasagem_binaria_por_sexo(df: pd.DataFrame) -> dict:
    """Agregação binária (sem defasagem vs. alguma defasagem = moderada +
    severa reunidas) por sexo e ano — mesma agregação já usada para publicar
    2024 na pergunta 1, aplicada aqui às três combinações sexo×ano, célula a
    célula, via a MESMA função de supressão (distribution) já aprovada."""
    resultado = {}
    for ano in (2022, 2023, 2024):
        g = df[df.ano == ano]
        por_genero = {}
        for genero, h in g.groupby("genero"):
            binario = h.categoria.map(_BINARIO).fillna("Ausente").tolist()
            entrada = distribution(binario, ["sem_defasagem", "alguma_defasagem", "Ausente"])
            entrada["n_genero"] = len(h)
            por_genero[genero] = entrada
        resultado[str(ano)] = por_genero
    return resultado


def q2_ida_por_sexo(df: pd.DataFrame) -> dict:
    resultado = {}
    for ano in (2022, 2023, 2024):
        g = df[df.ano == ano]
        resultado[str(ano)] = {genero: summary(h.ida) for genero, h in g.groupby("genero")}
    return resultado


def q3_associacoes_por_sexo(df: pd.DataFrame) -> dict:
    resultado = {}
    for genero, h in df.groupby("genero"):
        resultado[genero] = {
            "ieg x ida": association(h.ida, h.ieg, h.ano),
            "ieg x ipv": association(h.ipv, h.ieg, h.ano),
        }
    return resultado


def q10_ida_pareado_por_sexo(records: list[dict]) -> dict:
    resultado = {}
    for origin, target in ((2022, 2023), (2023, 2024)):
        pairs = pair_records(records, origin, target, how="inner")
        left = [records[int(i)] for i in pairs.record_index_origem]
        right = [records[int(i)] for i in pairs.record_index_destino]
        a = _frame_com_genero(left)
        b = _frame_com_genero(right)
        delta = b.ida - a.ida
        por_genero = {}
        for genero in a.genero.unique():
            mascara = (a.genero == genero).values
            por_genero[genero] = summary(delta[mascara])
        resultado[f"{origin}→{target}"] = por_genero
    return resultado


def q11_perdas_por_sexo(records: list[dict]) -> dict:
    resultado = {}
    for origin, target in ((2022, 2023), (2023, 2024)):
        joined = pair_records(records, origin, target, how="left")
        grupos: dict[str, list] = {}
        for row in joined.to_dict("records"):
            r = records[int(row["record_index_origem"])]
            if origin_exclusion(r) is not None:
                continue
            found = row["_merge"] == "both"
            chave = f"{r['genero_padronizado']}_{'encontrados' if found else 'nao_encontrados'}"
            grupos.setdefault(chave, []).append(r)
        resultado[f"{origin}→{target}"] = {
            chave: {"n": len(rows), "ida": summary([r["ida_numerico"] for r in rows])}
            for chave, rows in grupos.items()
        }
    return resultado


def main() -> None:
    records = load_prepared(DADOS_ROOT)
    df = _frame_com_genero(records)
    resultado = {
        "cobertura_genero": {
            "total": len(df),
            "por_genero": {g: int(n) for g, n in df.genero.value_counts().items()},
            "ausentes": int(df.genero.isna().sum()),
        },
        "q1_defasagem_por_sexo": q1_defasagem_por_sexo(df),
        "q1_defasagem_binaria_por_sexo": q1_defasagem_binaria_por_sexo(df),
        "q2_ida_por_sexo": q2_ida_por_sexo(df),
        "q3_associacoes_por_sexo": q3_associacoes_por_sexo(df),
        "q10_ida_pareado_por_sexo": q10_ida_pareado_por_sexo(records),
        "q11_perdas_por_sexo": q11_perdas_por_sexo(records),
    }
    saida = json.dumps(resultado, indent=2, ensure_ascii=False, default=str)
    if len(sys.argv) > 1:
        Path(sys.argv[1]).write_text(saida, encoding="utf-8")
    else:
        print(saida)


if __name__ == "__main__":
    main()
