"""Achado exploratório complementar da pergunta 1: defasagem (categoria)
por fase, por ano.

Reaproveita as MESMAS funções de privacidade já aprovadas e congeladas em
src/analises_negocio.py (analytic_frame/distribution) sobre os MESMOS campos
já permitidos na lista positiva daquele módulo (fase, categoria) — não
modifica esse arquivo nem o registro interno congelado da análise
(reports/metricas_analises_negocio.json). O resultado não é congelado nem
tem hash verificado; é reportado na camada pública explicitamente como
"achado exploratório", nunca misturado com os números oficiais.

Uso: `python scripts/explorar_defasagem_por_fase.py`
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from preparacao_coortes import load_prepared  # noqa: E402
from analises_negocio import analytic_frame, distribution  # noqa: E402
from dados_pede import ROOT as DADOS_ROOT  # noqa: E402


def compute() -> dict:
    records = load_prepared(DADOS_ROOT)
    df = analytic_frame(records)
    resultado: dict[str, dict] = {}
    for ano in (2022, 2023, 2024):
        g = df[df.ano == ano]
        por_fase = {}
        for fase, h in g.groupby("fase"):
            rotulo = str(int(fase))
            entrada = distribution(
                h.categoria.fillna("Ausente").tolist(),
                ["sem_defasagem", "moderada", "severa", "Ausente"],
            )
            entrada["n_fase"] = len(h)
            por_fase[rotulo] = entrada
        resultado[str(ano)] = por_fase
    return resultado


if __name__ == "__main__":
    print(json.dumps(compute(), indent=2, ensure_ascii=False))
