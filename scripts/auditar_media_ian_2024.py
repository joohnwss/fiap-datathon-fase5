"""Auditoria de divulgação conjunta — média anual do IAN em 2024.

Uma primeira análise suprimiu integralmente a média anual do IAN em 2024,
com o argumento de que publicá-la, combinada com as contagens
já públicas de "sem defasagem" (622) e "com defasagem" (534), permitiria
isolar algebricamente a divisão exata entre moderada e severa dentro dos
534 registros com defasagem — já que o IAN só assume três valores fixos por
construção (10 = sem defasagem, 5 = moderada, 2,5 = severa; ver
docs/contrato_metodologico.md).

Uma reavaliação encontrou essa supressão total excessiva: o risco real é
sobre a MÉDIA EXATA (com mais de duas casas decimais), não sobre o valor
arredondado a duas casas decimais — o mesmo padrão já aplicado a 2022 e
2023. Este script prova, por busca exaustiva sobre todas as divisões
inteiras possíveis de moderada/severa dentro do total conhecido (534),
que o valor arredondado a duas casas decimais é consistente com MAIS DE UMA
divisão exata — ou seja, não permite reconstrução única da célula
protegida — e por isso pode ser publicado.

Este script não lê nenhum dado privado: usa exclusivamente os totais já
aprovados e públicos (622, 534, 1156) e a regra de três valores fixos do
IAN, já documentada. Não altera o artefato interno congelado nem
`src/analises_negocio.py`.

Uso: `python scripts/auditar_media_ian_2024.py [caminho_saida.json]`
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

N_SEM_DEFASAGEM = 622
N_COM_DEFASAGEM = 534
N_TOTAL = N_SEM_DEFASAGEM + N_COM_DEFASAGEM

VALOR_SEM_DEFASAGEM = 10.0
VALOR_MODERADA = 5.0
VALOR_SEVERA = 2.5

MEDIA_PUBLICADA_2024 = 7.68


def divisoes_consistentes_com_media_arredondada(media_publicada: float, casas_decimais: int = 2) -> list[dict]:
    """Busca exaustiva: para cada divisão inteira possível de moderada/severa
    dentro de N_COM_DEFASAGEM, calcula a média exata resultante e verifica
    se ela arredonda para o valor publicado."""
    resultado = []
    for severa in range(0, N_COM_DEFASAGEM + 1):
        moderada = N_COM_DEFASAGEM - severa
        soma = (N_SEM_DEFASAGEM * VALOR_SEM_DEFASAGEM
                + moderada * VALOR_MODERADA
                + severa * VALOR_SEVERA)
        media_exata = soma / N_TOTAL
        if round(media_exata, casas_decimais) == media_publicada:
            resultado.append({"severa": severa, "moderada": moderada, "media_exata": media_exata})
    return resultado


def main() -> None:
    divisoes = divisoes_consistentes_com_media_arredondada(MEDIA_PUBLICADA_2024)
    saida = {
        "n_sem_defasagem": N_SEM_DEFASAGEM,
        "n_com_defasagem": N_COM_DEFASAGEM,
        "media_publicada_2024_arredondada": MEDIA_PUBLICADA_2024,
        "divisoes_moderada_severa_consistentes_com_a_media_publicada": divisoes,
        "quantidade_de_divisoes_consistentes": len(divisoes),
        "reconstrucao_unica_possivel": len(divisoes) <= 1,
        "conclusao": (
            "reconstrução única NÃO é possível: mais de uma divisão inteira de "
            "moderada/severa produz a mesma média arredondada publicada"
            if len(divisoes) > 1 else
            "ATENÇÃO: reconstrução única É possível — a média arredondada NÃO deveria ser publicada"
        ),
    }
    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    texto = json.dumps(saida, indent=2, ensure_ascii=False)
    if out_path:
        out_path.write_text(texto, encoding="utf-8")
    else:
        print(texto)


if __name__ == "__main__":
    main()
