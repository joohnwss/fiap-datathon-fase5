"""Camada narrativa da aba "Panorama e resultados".

Este módulo NÃO recalcula nada: lê exclusivamente os campos já aprovados de
`reports/public/perguntas_oficiais_v1.json` (a mesma camada pública gerada
por `src/analises_publicas.py`) e os organiza em uma narrativa curta para um
público não técnico (professores, pedagogos, psicólogos, assistentes
sociais e gestores da ONG). Os números exibidos nos cartões vêm sempre de
`pergunta["principais_numeros"]`/`analises_complementares_numeros` — nenhum
valor novo é calculado aqui. Os textos de "leitura do resultado" e "fonte em
linguagem pública" são interpretações editoriais dos mesmos números já
aprovados, sem introduzir nenhum dado, conclusão causal ou número que não
esteja já na camada pública.

Não lê `DATATHON/`, `local_data/`, `local_recovery/` nem artefatos privados.
"""
from __future__ import annotations


def _pct(texto: str) -> float:
    """'30,1% (142)' ou '30,1%' -> 30.1. Usado só para ordenar/formatar
    valores já publicados, nunca para calcular um número novo."""
    parte = texto.split("(")[0].strip().rstrip("%")
    return float(parte.replace(",", "."))


def _fmt_pp(valor: float) -> str:
    sinal = "+" if valor >= 0 else ""
    numero = f"{sinal}{valor:.1f}".replace(".", ",")
    return f"{numero} p.p."


def _fmt_pt(valor: float) -> str:
    sinal = "+" if valor >= 0 else ""
    return f"{sinal}{valor:.2f}".replace(".", ",")


# --------------------------------------------------------------------------- #
# Cartões de números principais (2 a 4 por pergunta)                         #
# --------------------------------------------------------------------------- #

def _cartoes_q1(p: dict) -> list[dict]:
    linhas = {(r["Ano"], r["Categoria"]): r for r in p["principais_numeros"]}
    sem_2022 = linhas[("2022", "sem defasagem")]
    sem_2024 = linhas[("2024", "sem defasagem")]
    variacao = _pct(sem_2024["Percentual"]) - _pct(sem_2022["Percentual"])
    return [
        {"rotulo": "Sem defasagem em 2022", "valor": sem_2022["Percentual"], "nota": f"{sem_2022['Contagem']} de 860 registros"},
        {"rotulo": "Sem defasagem em 2024", "valor": sem_2024["Percentual"], "nota": f"{sem_2024['Contagem']} de 1.156 registros"},
        {"rotulo": "Variação acumulada (2022→2024)", "valor": _fmt_pp(variacao), "nota": "na parcela sem defasagem"},
        {"rotulo": "População analisada", "valor": "3.030 registros", "nota": "860 (2022) + 1.014 (2023) + 1.156 (2024)"},
    ]


def _cartoes_q2(p: dict) -> list[dict]:
    geral = next(r for r in p["principais_numeros"] if r["Recorte"] == "Todos os registros")
    variacao = geral["2024"] - geral["2022"]
    return [
        {"rotulo": "IDA médio em 2022", "valor": _fmt_pt(geral["2022"]).lstrip("+"), "nota": "escala de 0 a 10"},
        {"rotulo": "IDA médio em 2023", "valor": _fmt_pt(geral["2023"]).lstrip("+"), "nota": "pico do período"},
        {"rotulo": "IDA médio em 2024", "valor": _fmt_pt(geral["2024"]).lstrip("+"), "nota": "recuo em relação a 2023"},
        {"rotulo": "Variação 2022→2024", "valor": _fmt_pt(variacao), "nota": "pontos na escala de 0 a 10"},
    ]


def _cartoes_q3(p: dict) -> list[dict]:
    linhas = {r["Relação"]: r for r in p["principais_numeros"]}
    ida = linhas["IEG × IDA"]
    ipv = linhas["IEG × IPV"]
    return [
        {"rotulo": "Engajamento × Desempenho", "valor": ida["Intensidade"].capitalize(), "nota": f"n = {ida['n']:,}".replace(",", ".")},
        {"rotulo": "Engajamento × Ponto de virada", "valor": ipv["Intensidade"].capitalize(), "nota": f"n = {ipv['n']:,}".replace(",", ".")},
        {"rotulo": "Registros pareados analisados", "valor": f"{ida['n']:,}".replace(",", "."), "nota": "2022–2024, ajustado por ano"},
    ]


def _cartoes_q4(p: dict) -> list[dict]:
    linhas = {r["Relação"]: r for r in p["principais_numeros"]}
    ida = linhas["IAA × IDA"]
    ieg = linhas["IAA × IEG"]
    return [
        {"rotulo": "Autoavaliação × Desempenho", "valor": ida["Intensidade"].capitalize(), "nota": f"n = {ida['n']:,}".replace(",", ".")},
        {"rotulo": "Autoavaliação × Engajamento", "valor": ieg["Intensidade"].capitalize(), "nota": f"n = {ieg['n']:,}".replace(",", ".")},
        {"rotulo": "Registros pareados analisados", "valor": f"{ida['n']:,}".replace(",", "."), "nota": "2022–2024, ajustado por ano"},
    ]


def _cartoes_q5(p: dict) -> list[dict]:
    linhas = p["principais_numeros"]
    ida1 = next(r for r in linhas if r["Transição"] == "2022→2023" and r["Desfecho futuro"] == "ΔIDA")
    ida2 = next(r for r in linhas if r["Transição"] == "2023→2024" and r["Desfecho futuro"] == "ΔIDA")
    return [
        {"rotulo": "IPS de origem × queda futura de IDA (2022→2023)", "valor": "praticamente nula", "nota": f"n = {ida1['n']}"},
        {"rotulo": "IPS de origem × queda futura de IDA (2023→2024)", "valor": "praticamente nula", "nota": f"n = {ida2['n']}"},
        {"rotulo": "Padrão", "valor": "repetido nas 2 transições", "nota": "e em 3 formas de medir queda"},
    ]


def _cartoes_q6(p: dict) -> list[dict]:
    linhas = {(r["Ano"], r["Medida"]): r for r in p["principais_numeros"]}
    ipp_ian_23 = linhas[("2023", "IPP × IAN")]
    ipp_ian_24 = linhas[("2024", "IPP × IAN")]
    return [
        {"rotulo": "IPP × IAN em 2023", "valor": "fraca", "nota": f"n = {ipp_ian_23['n']}"},
        {"rotulo": "IPP × IAN em 2024", "valor": "fraca", "nota": f"n = {ipp_ian_24['n']}"},
        {"rotulo": "Cobertura do IPP", "valor": "a partir de 2023", "nota": "ausente estruturalmente em 2022"},
    ]


def _cartoes_q7(p: dict) -> list[dict]:
    linhas = p["principais_numeros"]
    mesmo_ano_2022 = next(r for r in linhas if r["Janela"] == "Mesmo ano — 2022")
    futuro_2223 = next(r for r in linhas if r["Janela"] == "2022→2023" and "IDA" in r["Indicador"])
    return [
        {"rotulo": "Indicador mais associado no mesmo ano", "valor": mesmo_ano_2022["Indicador"], "nota": "força moderada a forte"},
        {"rotulo": "Indicador de origem mais associado ao ano seguinte", "valor": futuro_2223["Indicador"], "nota": "força moderada"},
        {"rotulo": "Diferença", "valor": "associações futuras um pouco mais fracas", "nota": "que as do mesmo ano"},
    ]


def _cartoes_q8(p: dict) -> list[dict]:
    return [
        {"rotulo": f"Maior média de INDE em {r['Ano']}", "valor": f"{r['INDE médio']:.2f}".replace(".", ","), "nota": f"n = {r['n']} · {r['Perfil de indicadores']}"}
        for r in p["principais_numeros"]
    ]


def _cartoes_q9(p: dict) -> list[dict]:
    linhas = p["principais_numeros"]
    dev = next(r for r in linhas if r["Avaliação"].startswith("Desenvolvimento"))
    teste = next(r for r in linhas if r["Avaliação"].startswith("Teste temporal"))
    return [
        {"rotulo": "Casos de risco sinalizados (validação interna)", "valor": f"{dev['Recall']*100:.1f}%".replace(".", ","), "nota": f"{dev['Eventos']} casos reais avaliados"},
        {"rotulo": "Casos de risco sinalizados (teste temporal)", "valor": f"{teste['Recall']*100:.1f}%".replace(".", ","), "nota": f"{teste['Eventos']} casos reais avaliados"},
        {"rotulo": "Casos de risco não sinalizados (teste temporal)", "valor": str(teste["Falsos negativos"]), "nota": f"de {teste['Eventos']} casos reais"},
        {"rotulo": "Ponto de atenção do modelo", "valor": "≈ 27%", "nota": "probabilidade a partir da qual o caso é sinalizado"},
    ]


def _cartoes_q10(p: dict) -> list[dict]:
    linhas = p["principais_numeros"]
    t1 = linhas[0]
    t2 = linhas[1]
    return [
        {"rotulo": f"Melhoria de Pedra ({t1['Transição']})", "valor": t1["Melhoria"], "nota": f"n = {t1['n']} pares"},
        {"rotulo": f"Melhoria de Pedra ({t2['Transição']})", "valor": t2["Melhoria"], "nota": f"n = {t2['n']} pares"},
        {"rotulo": "Estabilidade nas duas transições", "valor": "≈ 50%", "nota": f"{t1['Estabilidade']} e {t2['Estabilidade']}"},
    ]


def _cartoes_q11(p: dict) -> list[dict]:
    linhas = p["principais_numeros"]
    return [
        {"rotulo": "Perda de acompanhamento (2022→2023)", "valor": "27,0%", "nota": linhas[0]["Evidência"].split(": ", 1)[-1]},
        {"rotulo": "Perda de acompanhamento (2023→2024)", "valor": "22,1%", "nota": linhas[1]["Evidência"].split(": ", 1)[-1]},
        {"rotulo": "Sensibilidade do modelo (teste temporal)", "valor": "40,5%", "nota": "ver pergunta 9"},
    ]


_CARTOES = {
    1: _cartoes_q1, 2: _cartoes_q2, 3: _cartoes_q3, 4: _cartoes_q4, 5: _cartoes_q5,
    6: _cartoes_q6, 7: _cartoes_q7, 8: _cartoes_q8, 9: _cartoes_q9, 10: _cartoes_q10,
    11: _cartoes_q11,
}


def cartoes_numeros(pergunta: dict) -> list[dict]:
    """Devolve de 2 a 4 cartões de números principais para a pergunta,
    extraídos de `principais_numeros` — nunca um valor inventado aqui."""
    return _CARTOES[pergunta["numero"]](pergunta)


# --------------------------------------------------------------------------- #
# Tabelas de "Ver dados da análise": uma tabela pequena e específica por tipo #
# de recorte, em vez de uma única tabela genérica que mistura sexo, faixa    #
# etária, fase etc. em muitas colunas parcialmente vazias. Cada função       #
# devolve uma lista de {"titulo": str, "nota": str opcional,                 #
# "linhas": list[dict]} — os nomes de coluna já em linguagem compreensível.  #
# Nenhum valor novo é calculado aqui; tudo vem de                           #
# `analises_complementares_numeros`/`principais_numeros`.                    #
# --------------------------------------------------------------------------- #

def _partes_pct(texto) -> tuple[str, int | None]:
    """'31,1% (142)' -> ('31,1%', 142). Strings sem esse formato (ex.: uma
    nota de supressão) voltam como estão, sem quantidade."""
    if not isinstance(texto, str) or "(" not in texto:
        return texto, None
    percentual, resto = texto.split("(", 1)
    try:
        quantidade = int(resto.rstrip(") "))
    except ValueError:
        quantidade = None
    return percentual.strip(), quantidade


def _grupo_sexo(valor: str) -> str:
    return {"feminino": "Meninas", "masculino": "Meninos"}.get(valor, valor.capitalize())


def _tabelas_q1(p: dict) -> list[dict]:
    comp = p["analises_complementares_numeros"]
    tabelas = []

    linhas_media = [r for r in comp if r.get("Recorte") == "Média anual do IAN"]
    tabelas.append({
        "titulo": "Média anual do indicador de adequação (IAN)",
        "linhas": [
            {"Ano": r["Ano"], "Média do IAN": r["Valor"] if isinstance(r["Valor"], float) else "Não divulgada",
             "Quantidade de estudantes": r["n"]}
            for r in linhas_media
        ],
    })

    linhas_sinal = [r for r in comp if r.get("Recorte", "").startswith("Sinal da defasagem")]
    tabelas.append({
        "titulo": "Situação da defasagem por ano",
        "nota": "Cada estudante entra em uma destas três situações a cada ano.",
        "linhas": [
            {"Ano": r["Ano"], "Abaixo do nível esperado": r["D<0"],
             "No nível esperado": r["D=0"], "Acima do nível esperado": r["D>0"]}
            for r in linhas_sinal
        ],
    })

    linhas_sexo_fino = [r for r in comp if r.get("Recorte") == "Defasagem por sexo"
                        and r.get("Sexo") in ("feminino", "masculino")]
    tabelas.append({
        "titulo": "Defasagem por grupo em 2022 (detalhamento completo)",
        "nota": "Em 2023 e 2024, este detalhamento não é apresentado porque o grupo se torna pequeno demais.",
        "linhas": [
            {"Grupo": _grupo_sexo(r["Sexo"]), "Quantidade de estudantes": r["n"],
             "Sem defasagem": r["sem defasagem"], "Moderada": r["moderada"], "Severa": r["severa"]}
            for r in linhas_sexo_fino
        ],
    })

    linhas_sexo_bin = [r for r in comp if r.get("Recorte") == "Defasagem por sexo (sem/alguma defasagem)"]
    tabelas.append({
        "titulo": "Diferenças entre meninas e meninos (2022 a 2024)",
        "linhas": [
            {"Ano": r["Ano"], "Grupo": _grupo_sexo(r["Sexo"]), "Quantidade de estudantes": r["n"],
             "Sem defasagem": r["sem defasagem"], "Com alguma defasagem": r["alguma defasagem"],
             "Mudança em relação ao ano anterior": r['Variação de "alguma defasagem" em p.p. vs. ano anterior']}
            for r in linhas_sexo_bin
        ],
    })

    linhas_idade = [r for r in comp if r.get("Recorte") == "Defasagem por faixa etária aproximada"]
    tabelas.append({
        "titulo": "Diferenças por faixa etária aproximada",
        "nota": "Só aparecem aqui as combinações de ano e faixa com dados suficientes para publicar com segurança.",
        "linhas": [
            {"Ano": r["Ano"], "Faixa etária aproximada": r["Faixa"], "Quantidade de estudantes": r["n"],
             "Sem defasagem": r["sem defasagem"], "Moderada": r["moderada"], "Severa": r["severa"]}
            for r in linhas_idade
        ],
    })

    linhas_fase = [r for r in comp if r.get("Recorte", "").startswith("Defasagem por fase")]
    tabelas.append({
        "titulo": "Defasagem por fase escolar (2022)",
        "nota": "Achado exploratório: só a fase 3 em 2022 teve dados suficientes para publicar com segurança.",
        "linhas": [
            {"Fase": r["Fase"], "Quantidade de estudantes": r["n_fase"],
             "Sem defasagem": r["sem defasagem"], "Moderada": r["moderada"], "Severa": r["severa"]}
            for r in linhas_fase
        ],
    })
    return tabelas


def _tabelas_q2(p: dict) -> list[dict]:
    comp = p["analises_complementares_numeros"]
    tabelas = []

    linhas_sexo = [r for r in comp if r.get("Recorte") == "IDA médio por sexo"]
    tabelas.append({
        "titulo": "Desempenho médio (IDA) por grupo",
        "linhas": [
            {"Grupo": _grupo_sexo(r["Sexo"]), "IDA médio em 2022": r["2022"], "IDA médio em 2023": r["2023"],
             "IDA médio em 2024": r["2024"], "Quantidade de estudantes (2022/2023/2024)": r["n (2022/23/24)"]}
            for r in linhas_sexo
        ],
    })

    linhas_idade = [r for r in comp if r.get("Recorte") == "IDA médio por faixa etária aproximada"]
    tabelas.append({
        "titulo": "Desempenho médio (IDA) por faixa etária aproximada",
        "linhas": [
            {"Faixa etária aproximada": r["Faixa"], "IDA médio em 2022": r["2022"], "IDA médio em 2023": r["2023"],
             "IDA médio em 2024": r["2024"], "Quantidade de estudantes (2022/2023/2024)": r["n (2022/23/24)"]}
            for r in linhas_idade
        ],
    })
    return tabelas


def _forca_associacao(rho: float) -> str:
    intensidade = "fraca" if abs(rho) < 0.3 else "moderada" if abs(rho) < 0.6 else "forte"
    return f"{intensidade} ({rho:.2f})".replace(".", ",")


def _tabelas_q3(p: dict) -> list[dict]:
    comp = p["analises_complementares_numeros"]
    tabelas = []

    linhas_sexo = [r for r in comp if "Sexo" in r]
    tabelas.append({
        "titulo": "Força da relação entre engajamento e os demais indicadores, por grupo",
        "linhas": [
            {"Relação": r["Relação"], "Grupo": _grupo_sexo(r["Sexo"]),
             "Força da relação": _forca_associacao(r["ρ ajustado por ano"]), "Quantidade de estudantes": r["n"]}
            for r in linhas_sexo
        ],
    })

    linhas_idade = [r for r in comp if "Faixa etária aproximada" in r]
    tabelas.append({
        "titulo": "Força da relação entre engajamento e desempenho, por faixa etária aproximada",
        "linhas": [
            {"Faixa etária aproximada": r["Faixa etária aproximada"],
             "Força da relação": _forca_associacao(r["ρ ajustado por ano"]), "Quantidade de estudantes": r["n"]}
            for r in linhas_idade
        ],
    })
    return tabelas


def _tabelas_q9(p: dict) -> list[dict]:
    comp = p["analises_complementares_numeros"]

    def _linha(r):
        return {
            "Quantidade de estudantes": r["n"],
            "Casos de risco real": r["Eventos"],
            "Casos sinalizados corretamente": r["Verdadeiros positivos"],
            "Casos de risco não sinalizados": r["Falsos negativos"],
            "Proporção de casos sinalizados": (f"{r['Recall']*100:.1f}%".replace(".", ",")
                                               if isinstance(r["Recall"], float) else "Não divulgada"),
        }

    linhas_fase = [r for r in comp if r.get("Recorte") == "Equidade por fase — teste temporal"
                  and isinstance(r.get("n"), int)]
    tabela_fase = {"titulo": "Desempenho do modelo por fase escolar",
                  "nota": "Só aparecem as fases com dados suficientes para publicar com segurança.",
                  "linhas": [{"Fase": r["Fase"], **_linha(r)} for r in linhas_fase]}

    linhas_sexo = [r for r in comp if r.get("Recorte") == "Equidade por gênero — teste temporal"]
    tabela_sexo = {"titulo": "Desempenho do modelo por grupo",
                  "linhas": [{"Grupo": _grupo_sexo(r["Grupo"]), **_linha(r)} for r in linhas_sexo]}

    linhas_idade = [r for r in comp if r.get("Recorte") == "Equidade por faixa etária aproximada — teste temporal"
                   and isinstance(r.get("n"), int)]
    tabela_idade = {"titulo": "Desempenho do modelo por faixa etária aproximada",
                    "nota": "A faixa de 17 anos ou mais não aparece aqui: não teve casos de risco suficientes para uma leitura confiável.",
                    "linhas": [{"Faixa etária aproximada": r["Grupo"], **_linha(r)} for r in linhas_idade]}

    return [tabela_fase, tabela_sexo, tabela_idade]


def _tabelas_q10(p: dict) -> list[dict]:
    comp = p["analises_complementares_numeros"]

    linhas_pedra = [r for r in comp if r.get("Recorte") == "Variação média de IDA por Pedra de origem"]
    tabela_pedra = {
        "titulo": "Mudança no desempenho (IDA) conforme a Pedra de origem",
        "linhas": [
            {"Transição": r["Transição"], "Pedra de origem": r["Pedra de origem"],
             "Mudança média no IDA": r["Δ IDA médio"], "Quantidade de estudantes": r["n"]}
            for r in linhas_pedra
        ],
    }

    linhas_sexo = [r for r in comp if r.get("Recorte") == "Variação média de IDA por sexo"]
    tabela_sexo = {
        "titulo": "Mudança no desempenho (IDA) por grupo",
        "linhas": [
            {"Transição": r["Transição"], "Grupo": _grupo_sexo(r["Sexo"]),
             "Mudança média no IDA": r["Δ IDA médio"], "Quantidade de estudantes": r["n"]}
            for r in linhas_sexo
        ],
    }

    linhas_idade = [r for r in comp if r.get("Recorte") == "Variação média de IDA por faixa etária aproximada"]
    tabela_idade = {
        "titulo": "Mudança no desempenho (IDA) por faixa etária aproximada",
        "linhas": [
            {"Transição": r["Transição"], "Faixa etária aproximada": r["Faixa"],
             "Mudança média no IDA": r["Δ IDA médio"], "Quantidade de estudantes": r["n"]}
            for r in linhas_idade
        ],
    }
    return [tabela_pedra, tabela_sexo, tabela_idade]


def _tabelas_q11(p: dict) -> list[dict]:
    comp = p["analises_complementares_numeros"]

    linhas_gerais = [r for r in comp if r.get("Recorte", "").endswith("encontrados no ano seguinte")]
    tabela_geral = {
        "titulo": "Indicadores de quem foi e de quem não foi reencontrado",
        "linhas": [
            {"Transição": r["Transição"],
             "Situação": "Reencontrado" if "NÃO" not in r["Recorte"] else "Não reencontrado",
             "Indicador": r["Recorte"].split(" médio")[0],
             "Média": r["Valor"], "Quantidade de estudantes": r["n"]}
            for r in linhas_gerais
        ],
    }

    linhas_sexo = [r for r in comp if r.get("Recorte", "").startswith("IDA médio por sexo")]
    tabela_sexo = {
        "titulo": "Desempenho (IDA) de quem foi e de quem não foi reencontrado, por grupo",
        "linhas": [
            {"Transição": r["Transição"],
             "Grupo": _grupo_sexo(r["Recorte"].split(" — ")[1].split()[0]),
             "Situação": "Reencontrado(a)" if "não" not in r["Recorte"] else "Não reencontrado(a)",
             "IDA médio": r["Valor"], "Quantidade de estudantes": r["n"]}
            for r in linhas_sexo
        ],
    }
    return [tabela_geral, tabela_sexo]


def _tabelas_q7(p: dict) -> list[dict]:
    comp = [r for r in p["analises_complementares_numeros"] if r.get("Recorte") == "IPV médio por fase"]
    # 2023 e 2024 não têm dado nesta linha (fase deixou de ser comparável
    # nesses anos) — a coluna inteira ficaria vazia, então não é incluída.
    return [{
        "titulo": "Ponto de virada médio por fase (2022)",
        "nota": "Este detalhamento existe apenas para 2022; nos demais anos, a fase não é comparável da mesma forma.",
        "linhas": [{"Fase": r["Fase"], "Ponto de virada médio": r["2022"]} for r in comp],
    }]


def _tabelas_q8(p: dict) -> list[dict]:
    comp = p["analises_complementares_numeros"]

    linhas_cobertura = [r for r in comp if r.get("Recorte") == "Cobertura de casos completos"]
    tabela_cobertura = {
        "titulo": "Quantidade de estudantes com todos os indicadores preenchidos",
        "linhas": [
            {"Ano": r["Ano"], "Quantidade de estudantes no ano": r["Total do ano"],
             "Com todos os indicadores preenchidos": r["Casos completos"], "Cobertura": r["Cobertura"]}
            for r in linhas_cobertura
        ],
    }

    linhas_medianas = [r for r in comp if r.get("Recorte") == "Medianas dos componentes"]
    tabela_medianas = {
        "titulo": "Valor típico (mediana) de cada indicador, por ano",
        "nota": "O IPP não existe em 2022 (ausência estrutural do instrumento nesse ano).",
        "linhas": [
            {"Ano": r["Ano"], "IDA": r["IDA"], "IEG": r["IEG"], "IPS": r["IPS"], "IPP": r["IPP"]}
            for r in linhas_medianas
        ],
    }
    return [tabela_cobertura, tabela_medianas]


_TABELAS_COMPLEMENTARES = {
    1: _tabelas_q1, 2: _tabelas_q2, 3: _tabelas_q3, 7: _tabelas_q7, 8: _tabelas_q8,
    9: _tabelas_q9, 10: _tabelas_q10, 11: _tabelas_q11,
}


def tabelas_complementares(pergunta: dict) -> list[dict]:
    """Tabelas específicas por tipo de recorte para "Ver dados da análise".
    Perguntas sem recorte por sexo/idade (4, 5, 6, 7, 8) continuam usando a
    tabela genérica de `analises_complementares_numeros` diretamente — ela
    já não mistura tipos de recorte incompatíveis nessas perguntas."""
    construtor = _TABELAS_COMPLEMENTARES.get(pergunta["numero"])
    return construtor(pergunta) if construtor else []


# --------------------------------------------------------------------------- #
# Evidências (título interpretativo + frase curta + leitura do resultado)    #
# por gráfico, na mesma ordem de `graficos_publicos.graficos_interativos`.   #
# --------------------------------------------------------------------------- #

_EVIDENCIAS: dict[int, list[dict]] = {
    1: [
        {
            "titulo": "Como a defasagem se distribuiu a cada ano",
            "frase": "Compare a fatia de estudantes sem defasagem, com defasagem moderada e com defasagem severa em cada ano.",
            "leitura": {
                "padrao": "A fatia sem defasagem cresceu a cada ano: 30,1% em 2022, 45,6% em 2023 e 53,8% em 2024.",
                "comparacao": "Em compensação, a fatia com alguma defasagem caiu de 69,9% para 46,2% no mesmo período.",
                "atencao": "Em 2024, moderada e severa aparecem somadas numa única fatia — não porque essa distinção deixou de existir, mas porque separá-las revelaria um grupo pequeno demais para publicar com segurança.",
                "cuidado": "Cada ano é uma fotografia de um grupo parcialmente diferente de estudantes; comparar anos não é o mesmo que acompanhar os mesmos estudantes ano a ano.",
            },
        },
        {
            "titulo": "Como a média geral do indicador de adequação evoluiu",
            "frase": "A média mostra a tendência geral, mas não substitui a composição por categoria (evidência anterior).",
            "leitura": {
                "padrao": "A média do indicador de adequação (IAN) subiu nos três anos: 6,42 em 2022, 7,24 em 2023 e 7,68 em 2024.",
                "comparacao": "A melhora foi maior entre 2022 e 2023 (+0,82 ponto) do que entre 2023 e 2024 (+0,44 ponto).",
                "atencao": "O IAN é formado por apenas três valores possíveis (10, 5 ou 2,5, conforme a categoria de defasagem de cada estudante) — a média descreve a composição do grupo inteiro em cada ano, não uma nota contínua individual. A média de 2024 é publicada arredondada a duas casas decimais; esse arredondamento foi auditado e confirmado seguro, sem permitir descobrir exatamente quantos dos 534 registros com defasagem são moderados e quantos são severos.",
                "cuidado": "Um aumento da média não comprova progresso individual nem impacto causal do programa — cada ano é uma fotografia de um grupo parcialmente diferente de estudantes.",
            },
        },
        {
            "titulo": "A queda da defasagem por sexo e por faixa etária aproximada",
            "frase": "Veja se a melhora observada foi parecida entre meninos e meninas, e entre faixas etárias aproximadas.",
            "leitura": {
                "padrao": "A parcela com alguma defasagem caiu nos dois sexos entre 2022 e 2024: de 68,9% para 44,0% entre as meninas, e de 71,0% para 48,8% entre os meninos.",
                "comparacao": "Em cada ano isolado, a diferença entre meninos e meninas é pequena (2 a 3 pontos percentuais) — a queda ao longo do tempo foi parecida nos dois grupos.",
                "atencao": "Por faixa etária aproximada, só algumas combinações têm dado suficiente para publicar com segurança; onde há dado, a faixa de 14 a 16 anos em 2022 mostra uma fatia de defasagem severa maior que a média do ano.",
                "cuidado": "A faixa etária é estimada a partir do ano de nascimento, não da data exata — um estudante perto da fronteira entre duas faixas pode, na idade real, pertencer à faixa vizinha.",
            },
        },
    ],
    2: [
        {
            "titulo": "Como o desempenho médio evoluiu por fase e por ano",
            "frase": "Compare a média do indicador de desempenho (IDA) entre fases e anos.",
            "leitura": {
                "padrao": "A média geral do IDA subiu de 6,09 em 2022 para 6,66 em 2023, e recuou para 6,35 em 2024.",
                "comparacao": "O padrão não é igual em todas as fases: algumas tiveram alta seguida de leve recuo ou estabilidade; outras, alta seguida de queda maior, ou queda gradual nos três anos.",
                "atencao": "Não existe uma tendência única válida para todas as fases — olhar só a média geral esconde essas diferenças.",
                "cuidado": "A comparação entre anos usa fotografias anuais de grupos parcialmente diferentes de estudantes, não a mesma turma acompanhada ano a ano.",
            },
        },
    ],
    3: [
        {
            "titulo": "Engajamento acompanha desempenho e ponto de virada?",
            "frase": "Veja a força da relação entre o indicador de engajamento (IEG) e os outros dois indicadores.",
            "leitura": {
                "padrao": "O engajamento tem uma relação moderada com o desempenho acadêmico e com o ponto de virada — nos dois casos, a força da relação é parecida.",
                "comparacao": "Nenhuma das duas relações é claramente mais forte que a outra.",
                "atencao": "Relação moderada não é relação forte: outros fatores, além do engajamento, também explicam boa parte da variação do desempenho e do ponto de virada.",
                "cuidado": "Essa é uma medida de quanto duas variáveis se movem juntas — não prova que uma causa a outra.",
            },
        },
    ],
    4: [
        {
            "titulo": "A autopercepção do estudante combina com o desempenho real?",
            "frase": "Veja a força da relação entre a autoavaliação (IAA) e o desempenho/engajamento reais.",
            "leitura": {
                "padrao": "A relação entre autoavaliação e desempenho é fraca; com engajamento, também é fraca.",
                "comparacao": "A autoavaliação se aproxima um pouco mais do engajamento do que do desempenho, mas a diferença é pequena.",
                "atencao": "Uma relação fraca não significa que a autoavaliação está \"errada\" — pode estar captando uma dimensão pessoal que as medidas externas não capturam.",
                "cuidado": "Divergências grandes entre autoavaliação e desempenho real são um tema para conversa individual qualificada, não um alerta automático.",
            },
        },
    ],
    5: [
        {
            "titulo": "O contexto psicossocial de hoje antecipa quedas futuras?",
            "frase": "Veja se um IPS mais alto ou mais baixo no início se relaciona com quedas de desempenho depois.",
            "leitura": {
                "padrao": "Não foi encontrada relação relevante entre o IPS de origem e quedas futuras de desempenho ou engajamento — as medidas de associação ficaram muito próximas de zero nas duas transições analisadas.",
                "comparacao": "Estudantes com IPS acima da mediana tiveram uma variação de desempenho um pouco melhor que os com IPS abaixo, mas a diferença é pequena diante da dispersão de cada grupo.",
                "atencao": "Esse resultado se repete em três formas diferentes de medir queda, o que reduz a chance de ser um efeito de uma escolha de corte específica.",
                "cuidado": "Não encontrar relação não é o mesmo que provar que ela não existe — só que ela não apareceu de forma clara com os dados e o método usados aqui.",
            },
        },
    ],
    6: [
        {
            "titulo": "A avaliação psicopedagógica confirma a defasagem medida pelo IAN?",
            "frase": "Veja a força da relação entre a avaliação psicopedagógica (IPP) e o indicador de adequação (IAN).",
            "leitura": {
                "padrao": "A relação entre IPP e IAN é fraca em 2023 e também fraca, um pouco mais forte, em 2024.",
                "comparacao": "A relação entre IPP e a categoria de defasagem é parecida: fraca a moderada nos dois anos.",
                "atencao": "Uma relação fraca significa que as duas avaliações concordam pouco entre si — não que uma delas esteja errada, mas que medem aspectos diferentes.",
                "cuidado": "O IPP não existe na base de 2022 (ausência estrutural do instrumento, não um dado suprimido) — a comparação começa em 2023.",
            },
        },
        {
            "titulo": "A média do IPP muda entre as categorias de defasagem?",
            "frase": "Compare a média do IPP entre quem está sem, com defasagem moderada ou severa.",
            "leitura": {
                "padrao": "Em 2023, a média do IPP caiu de quem está sem defasagem para quem está com defasagem moderada, e caiu ainda mais para quem está com defasagem severa — uma diferença pequena, mas na direção esperada.",
                "comparacao": "Essa é a mesma direção que o IAN indicaria: quem tem mais defasagem tende a ter IPP um pouco mais baixo.",
                "atencao": "Em 2024, essa quebra por categoria não pôde ser publicada (grupo pequeno demais para a regra de privacidade do projeto).",
                "cuidado": "Diferença pequena entre médias de grupo não substitui uma avaliação individual — o IPP de um estudante específico pode não seguir o padrão do grupo.",
            },
        },
    ],
    7: [
        {
            "titulo": "O que se relaciona com o ponto de virada no mesmo ano",
            "frase": "Veja quais indicadores acompanham mais de perto o ponto de virada (IPV) no mesmo ano.",
            "leitura": {
                "padrao": "No mesmo ano, o desempenho (IDA) tem relação moderada a forte com o ponto de virada, conforme o ano.",
                "comparacao": "Em 2024, a avaliação psicopedagógica (IPP) teve a relação mais forte com o ponto de virada entre os indicadores medidos naquele ano.",
                "atencao": "\"Mais relacionado\" não é o mesmo que \"mais importante\" ou \"causa\" — é só o indicador que mais acompanha o ponto de virada no mesmo período.",
                "cuidado": "Todas essas são medidas de associação, não de causa.",
            },
        },
        {
            "titulo": "O que no início do ano se relaciona com o ponto de virada seguinte",
            "frase": "Veja se os indicadores de um ano antecipam o ponto de virada do ano seguinte.",
            "leitura": {
                "padrao": "O desempenho (IDA) e o engajamento (IEG) de origem têm relação moderada com o ponto de virada seguinte, nas duas transições.",
                "comparacao": "O contexto psicossocial (IPS) de origem tem relação bem mais fraca com o ponto de virada seguinte.",
                "atencao": "As relações \"futuras\" são um pouco mais fracas que as relações \"no mesmo ano\" — esperado, já que há mais tempo e mais fatores entre a medição e o desfecho.",
                "cuidado": "De novo, associação não é causa: um indicador se mover junto com o ponto de virada não prova que ele o provoca.",
            },
        },
    ],
    8: [
        {
            "titulo": "Quais combinações de indicadores têm a maior nota global média",
            "frase": "Veja, em cada ano, qual combinação de indicadores altos teve a maior média de INDE.",
            "leitura": {
                "padrao": "Em 2022, a combinação com maior média de INDE foi desempenho + engajamento + contexto psicossocial altos.",
                "comparacao": "Em 2023 e 2024, a combinação com maior média incluiu também a avaliação psicopedagógica — o papel dessa quarta variável não foi o mesmo nos dois anos.",
                "atencao": "Só combinações com pelo menos dez estudantes em cada ano são mostradas — combinações menores ficam de fora por privacidade, mesmo que existam na base.",
                "cuidado": "Uma média mais alta na combinação não significa que combinar esses indicadores CAUSA uma nota melhor — os mesmos fatores de fundo podem explicar os dois.",
            },
        },
    ],
    9: [
        {
            "titulo": "Quanto o modelo consegue sinalizar, em dois tipos de teste",
            "frase": "Compare a sensibilidade do modelo na validação interna com o teste mais realista (temporal).",
            "leitura": {
                "padrao": "Na validação interna (mesma janela de tempo do treino), o modelo sinalizou 81,7% dos casos de risco reais. No teste temporal (janela seguinte, mais parecida com o uso futuro), essa proporção caiu para 40,5%.",
                "comparacao": "A queda de sensibilidade é grande — quase a metade do valor da validação interna — mesmo a capacidade geral de distinguir casos de risco tendo se mantido parecida.",
                "atencao": "No teste temporal, dos 84 casos de risco reais, 50 não foram sinalizados pelo modelo.",
                "cuidado": "O teste temporal é a avaliação mais parecida com o uso futuro do modelo; a validação interna tende a ser otimista demais.",
            },
        },
        {
            "titulo": "O que aconteceu com cada caso no teste temporal",
            "frase": "Veja, dos 311 casos avaliados, quantos foram classificados corretamente e quantos não.",
            "leitura": {
                "padrao": "Dos 311 casos do teste temporal, o modelo sinalizou corretamente 34 casos de risco reais e deixou de sinalizar 50.",
                "comparacao": "Entre os 227 casos sem risco real, 19 foram sinalizados por engano e 208 foram corretamente identificados como sem risco.",
                "atencao": "O número de casos de risco não sinalizados (50) é maior que o de casos sinalizados corretamente (34) — por isso a orientação é sempre complementar o modelo com revisão humana dos casos não sinalizados.",
                "cuidado": "Essas contagens vêm de um único teste temporal; não são uma garantia do que vai acontecer em novos dados.",
            },
        },
        {
            "titulo": "Se o modelo funciona igual para todos os grupos",
            "frase": "Veja se a proporção de casos sinalizados corretamente varia entre fases (e, na tabela completa, entre sexos e faixas etárias aproximadas).",
            "leitura": {
                "padrao": "Entre as fases com dado suficiente para publicar, a proporção sinalizada varia de 0% (fase 3) a 62,5% (fase 1).",
                "comparacao": "Por sexo, a proporção sinalizada foi de 33,3% entre meninas e 47,6% entre meninos; por faixa etária aproximada, variou de 11,1% a 46,4% (tabela completa em \"Ver dados da análise\", abaixo).",
                "atencao": "A fase 3 teve 0% de sinalização (nenhum dos 6 casos reais foi identificado) — a pior cobertura entre as fases mostradas aqui, e um padrão de atenção que já aparece em outras perguntas desta análise.",
                "cuidado": "Essas comparações vêm de um único teste temporal e, nas faixas etárias intermediárias, de poucos casos reais — o que torna essas estimativas mais instáveis do que as demais.",
            },
        },
    ],
    10: [
        {
            "titulo": "Quantos estudantes melhoraram, mantiveram ou pioraram de Pedra",
            "frase": "Veja a proporção de pares de estudantes que mudou de Pedra entre um ano e o seguinte.",
            "leitura": {
                "padrao": "Nas duas transições, a proporção de melhora ficou perto de 24%, e a de estabilidade ficou em torno da metade dos pares.",
                "comparacao": "A proporção de piora foi um pouco maior na segunda transição (2023→2024) que na primeira.",
                "atencao": "Esses números descrevem o que foi observado, não avaliam se o programa causou a evolução — não há grupo de comparação fora do programa.",
                "cuidado": "Pedra é uma categoria; pequenas variações de nota perto da fronteira entre duas Pedras podem mudar a classificação sem uma mudança real grande no desempenho.",
            },
        },
        {
            "titulo": "A evolução do desempenho variou pela Pedra de origem",
            "frase": "Compare a variação média do indicador de desempenho (IDA) conforme a Pedra de onde o estudante partiu.",
            "leitura": {
                "padrao": "Em 2022→2023, quem partiu de Quartzo teve o maior ganho médio de IDA; em 2023→2024, esse mesmo grupo de origem teve o único resultado ainda relativamente melhor que as demais Pedras, mas já negativo.",
                "comparacao": "Por sexo, a variação foi parecida entre meninos e meninas nas duas transições; por faixa etária aproximada, a faixa de 11 a 13 anos teve o maior recuo em 2023→2024.",
                "atencao": "O padrão observado em uma transição não se repetiu do mesmo jeito na seguinte — não dá para tratar nenhuma Pedra de origem como garantia de evolução.",
                "cuidado": "Sem um grupo de comparação fora do programa, não é possível atribuir essa evolução a uma ação específica do programa.",
            },
        },
    ],
    11: [
        {
            "titulo": "Quem se perde de vista entre um ano e o seguinte, e o que isso sugere",
            "frase": "Compare os indicadores de quem foi reencontrado no ano seguinte com os de quem não foi.",
            "leitura": {
                "padrao": "27,0% dos estudantes elegíveis de 2022 não foram reencontrados em 2023, e 22,1% dos de 2023 não foram reencontrados em 2024.",
                "comparacao": "Quem não foi reencontrado tinha, em média, indicadores de origem mais baixos — a diferença mais marcante é no desempenho (IDA) e no ponto de virada (IPV).",
                "atencao": "Isso indica indícios de viés de seleção principalmente na primeira transição (2022→2023): o padrão não se repete com a mesma força na segunda.",
                "cuidado": "\"Não reencontrado\" não é o mesmo que \"evadiu\" — pode ser mudança de instituição, erro de registro ou outros motivos não distinguíveis nos dados disponíveis.",
            },
        },
    ],
}


def evidencias(numero: int) -> list[dict]:
    """Lista de blocos de evidência (título, frase curta, leitura do
    resultado) na mesma ordem dos gráficos retornados por
    `graficos_publicos.graficos_interativos(numero, pergunta)`."""
    return _EVIDENCIAS[numero]


# --------------------------------------------------------------------------- #
# Fonte e metodologia, em linguagem pública (sem jargão de engenharia)       #
# --------------------------------------------------------------------------- #

_FONTE_PUBLICA = {
    1: "Contagens e proporções anuais aprovadas do indicador de adequação (IAN), com o mesmo critério de privacidade aplicado a todos os recortes.",
    2: "Médias anuais aprovadas do indicador de desempenho (IDA), por fase e por par de anos consecutivos.",
    3: "Medidas de associação (correlação) aprovadas entre os indicadores de engajamento, desempenho e ponto de virada, ajustadas por ano.",
    4: "Medidas de associação (correlação) aprovadas entre autoavaliação, desempenho e engajamento, ajustadas por ano.",
    5: "Medidas de associação aprovadas entre o contexto psicossocial de um ano e a variação de desempenho/engajamento no ano seguinte.",
    6: "Medidas de associação e médias aprovadas entre a avaliação psicopedagógica e o indicador de adequação/categoria de defasagem.",
    7: "Medidas de associação aprovadas entre indicadores contemporâneos e futuros, e o ponto de virada.",
    8: "Perfis de combinações de indicadores com média de nota global (INDE) aprovada, respeitando o tamanho mínimo de grupo.",
    9: "Métricas oficiais do modelo preditivo, avaliadas uma única vez em cada período (desenvolvimento e teste temporal), sem retreino.",
    10: "Transições observadas de Pedra entre pares de anos consecutivos, com o mesmo critério de privacidade aplicado a todos os recortes.",
    11: "Comparação aprovada entre estudantes reencontrados e não reencontrados de um ano para o seguinte, combinada com o resultado do modelo (pergunta 9).",
}


def fonte_publica(numero: int) -> str:
    return _FONTE_PUBLICA[numero]


# --------------------------------------------------------------------------- #
# Conclusões fluidas: reescrita editorial dos mesmos 6 campos já aprovados     #
# em `pergunta["conclusao"]` (constatação principal, diferenças entre         #
# grupos, ponto de atenção, limite da evidência, implicação prática, próximo  #
# acompanhamento) como 2 a 4 parágrafos contínuos, sem rótulos nem            #
# coeficientes — os achados de cada pergunta são os mesmos já aprovados; só   #
# a redação muda. `pergunta["conclusao"]` continua intacto (usado pelos       #
# testes de integridade da camada pública) e serve de referência interna.     #
# --------------------------------------------------------------------------- #

_CONCLUSOES_FLUIDAS: dict[int, list[str]] = {
    1: [
        "A parcela de estudantes com alguma defasagem caiu bastante entre 2022 e 2024 (de 69,9% para 46,2%), "
        "com a queda mais forte logo no primeiro intervalo. A mesma tendência de queda aparece tanto entre "
        "meninas quanto entre meninos, e a diferença entre os dois grupos, em cada ano isolado, é pequena.",

        "Isso é uma comparação entre fotografias anuais de grupos parcialmente diferentes de estudantes — não "
        "o acompanhamento dos mesmos estudantes ao longo do tempo. Por isso, a queda não pode ser lida como o "
        "progresso individual de quem já estava na Associação nos três anos, nem como prova de que uma ação "
        "específica causou essa melhora.",

        "Para a equipe pedagógica, esse resultado ajuda a dimensionar quantos estudantes, a cada ano, precisam "
        "de atenção prioritária — e mostra que a melhora observada foi ampla, não concentrada em um único "
        "grupo.",

        "Vale registrar medições ao longo do próprio ano (não só uma vez) para enxergar mudanças que essa "
        "fotografia anual não capta, e acompanhar se a fase 3 e a faixa de 14 a 16 anos — que mostraram mais "
        "defasagem severa em 2022 — continuam sendo pontos de atenção nos próximos ciclos.",
    ],
    2: [
        "O desempenho médio (IDA) não segue uma tendência única: em algumas fases ele subiu e depois se "
        "manteve estável, em outras subiu e recuou, e em outras caiu de forma gradual nos três anos. A média "
        "geral subiu entre 2022 e 2023 e recuou um pouco em 2024.",

        "Isso mostra que olhar só a média geral esconde diferenças importantes entre fases — uma fase pode "
        "estar melhorando enquanto outra recua, e a média sozinha não captura isso.",

        "A Associação pode usar esse retrato por fase para direcionar atenção pedagógica às fases que "
        "recuaram, em vez de tratar todas da mesma forma.",

        "A comparação usa fotografias anuais de grupos parcialmente diferentes de estudantes, então não "
        "indica o progresso dos mesmos estudantes nem prova que uma ação específica causou a mudança.",
    ],
    3: [
        "Estudantes mais engajados também costumam apresentar melhor desempenho acadêmico e maior pontuação "
        "no ponto de virada. Esse padrão aparece nos três anos analisados e é parecido entre meninas e "
        "meninos; ele fica mais nítido entre os estudantes mais velhos.",

        "Isso não significa que o engajamento, sozinho, provoque a melhora dos demais indicadores: outras "
        "condições da vida escolar, familiar e social também podem influenciar os resultados, e a relação "
        "pode não se repetir da mesma forma em cada caso individual.",

        "Para a Associação, o engajamento pode ajudar a identificar estudantes que precisam de maior "
        "aproximação e incentivo à participação.",

        "A recomendação é acompanhar esse indicador ao longo do tempo e observar se as mudanças também "
        "aparecem no desempenho e nos demais aspectos do desenvolvimento do estudante — com atenção especial "
        "aos estudantes mais velhos, onde a relação é mais forte.",
    ],
    4: [
        "A forma como os estudantes avaliam a si mesmos (IAA) tem relação fraca com o desempenho acadêmico e "
        "também fraca com o engajamento — ela se aproxima um pouco mais do engajamento do que do desempenho, "
        "mas a diferença é pequena.",

        "Uma relação fraca não quer dizer que a autoavaliação está errada: ela pode estar captando uma "
        "dimensão pessoal — como autoconfiança ou percepção do próprio esforço — que as medidas de desempenho "
        "e engajamento não capturam.",

        "Para a equipe, divergências grandes entre a autoavaliação de um estudante e seu desempenho real "
        "podem ser um bom ponto de partida para uma conversa individual, não um sinal de alerta automático.",

        "Vale tratar cada caso com cuidado pedagógico, sem transformar essa diferença, sozinha, em critério "
        "de decisão.",
    ],
    5: [
        "Não foi encontrada associação clara entre o contexto psicossocial de um ano (IPS) e quedas futuras "
        "no desempenho ou no engajamento. Estudantes com IPS mais alto no início tiveram uma variação de "
        "desempenho um pouco melhor que os com IPS mais baixo, mas a diferença é pequena diante da variação "
        "natural de cada grupo.",

        "Esse padrão se repete nas duas transições estudadas e em diferentes formas de medir queda, o que "
        "reduz a chance de ser um resultado passageiro ligado a uma única forma de olhar os dados.",

        "Isso sugere que o IPS, isoladamente, não é um bom sinal de alerta antecipado para quedas de "
        "desempenho — outros indicadores, como os já usados no modelo preditivo da pergunta 9, parecem mais "
        "úteis para essa finalidade.",

        "Não encontrar uma associação clara não é o mesmo que provar que ela não existe: com mais dados ou "
        "outra forma de medir, o resultado pode mudar, e vale reavaliar esse indicador em ciclos futuros.",
    ],
    6: [
        "A avaliação psicopedagógica (IPP) tem relação fraca com o indicador de adequação (IAN) e com a "
        "categoria de defasagem — ou seja, as duas avaliações concordam pouco entre si. Em 2023, a média do "
        "IPP foi um pouco mais baixa entre estudantes com defasagem moderada ou severa do que entre os sem "
        "defasagem, na direção esperada, mas com diferença pequena.",

        "Uma relação fraca não significa que uma das duas avaliações esteja errada — elas medem aspectos "
        "diferentes do desenvolvimento do estudante, e não seria esperado que concordassem completamente.",

        "Para a equipe, isso reforça que o indicador de adequação e a avaliação psicopedagógica devem ser "
        "lidos como informações complementares, não como confirmação uma da outra: um estudante pode aparecer "
        "bem em uma e pedir atenção na outra.",

        "A avaliação psicopedagógica não existe nos registros de 2022 e, em 2024, o detalhamento por "
        "categoria de defasagem não pôde ser mostrado (grupo pequeno demais) — então essa comparação, por "
        "enquanto, é mais robusta em 2023.",
    ],
    7: [
        "No mesmo ano, o desempenho acadêmico (IDA) é o indicador mais associado ao ponto de virada na maior "
        "parte dos anos; em 2024, a avaliação psicopedagógica teve a relação mais forte. Olhando de um ano "
        "para o seguinte, o desempenho e o engajamento de origem continuam sendo os mais associados ao ponto "
        "de virada futuro, com relação um pouco mais fraca do que a do mesmo ano — o que já era esperado, já "
        "que há mais tempo e mais fatores entre a medição e o resultado.",

        "Isso ajuda a entender quais indicadores acompanham de perto o ponto de virada, mas não prova que "
        "algum deles, isoladamente, provoque essa mudança — outros fatores da vida escolar e pessoal do "
        "estudante também podem estar envolvidos.",

        "A Associação pode priorizar o acompanhamento do desempenho e do engajamento como sinais mais "
        "próximos do ponto de virada, sem abandonar os demais indicadores.",

        "Vale reavaliar essas relações a cada novo ciclo, para verificar se elas se mantêm estáveis ou mudam "
        "conforme o perfil dos estudantes muda.",
    ],
    8: [
        "Em todos os três anos, as combinações de indicadores com maior nota global (INDE) sempre incluíram "
        "desempenho, engajamento e contexto psicossocial altos; a partir de 2023, a avaliação psicopedagógica "
        "também apareceu nessas combinações — baixa em 2023, alta em 2024.",

        "Isso sugere que a nota global tende a ser mais alta quando vários indicadores estão bem ao mesmo "
        "tempo, mas não prova que combinar esses indicadores, por si só, cause uma nota melhor — os mesmos "
        "fatores de fundo podem explicar tanto os indicadores quanto a nota.",

        "Para a Associação, esse retrato pode orientar quais combinações de indicadores merecem mais atenção "
        "ao acompanhar o desenvolvimento de um estudante, sem tratá-las como uma fórmula fixa de sucesso.",

        "Só combinações com pelo menos dez estudantes em cada ano são mostradas — combinações menores existem "
        "na base, mas não têm tamanho suficiente para uma leitura confiável.",
    ],
    9: [
        "O modelo consegue sinalizar boa parte dos casos de risco na validação interna (81,7%), mas essa "
        "proporção cai bastante no teste mais realista, feito no período seguinte (40,5%). Essa queda de "
        "sensibilidade não é igual entre todos os grupos: varia bastante entre fases escolares, é um pouco "
        "menor entre meninas do que entre meninos, e varia ainda mais entre faixas etárias aproximadas.",

        "Isso significa que, no uso real, o modelo deixa de sinalizar uma parte importante dos casos de "
        "risco verdadeiros — e deixa de sinalizar mais casos em alguns grupos do que em outros. A fase 3, em "
        "particular, teve o pior resultado: nenhum dos casos de risco reais foi sinalizado no teste mais "
        "realista.",

        "Por isso, o resultado do modelo deve ser sempre tratado como apoio à decisão da equipe pedagógica, "
        "nunca como decisão automática — e a revisão humana deve ser reforçada especialmente na fase 3, entre "
        "as meninas e nas faixas etárias com menor proporção de casos sinalizados.",

        "Esses resultados vêm de um único teste no tempo; vale reavaliar essas diferenças a cada novo ciclo, "
        "para ver se elas se mantêm, diminuem ou mudam de direção com mais dados.",
    ],
    10: [
        "As proporções de estudantes que melhoraram, mantiveram ou pioraram de Pedra ficaram parecidas nas "
        "duas transições estudadas — cerca de um quarto melhorou e metade manteve a mesma Pedra em cada "
        "período. Quem partiu da Pedra mais inicial (Quartzo) teve, em média, o maior ganho de desempenho na "
        "primeira transição, mas esse padrão não se repetiu do mesmo jeito na segunda.",

        "Isso descreve a evolução observada dos estudantes ao longo do programa, mas não prova que o "
        "programa, por si só, causou essas mudanças — não há um grupo de comparação fora do programa para "
        "isso.",

        "Para a Associação, esse retrato ajuda a acompanhar a evolução geral por Pedra de origem, sem "
        "estabelecer uma expectativa fixa de que um determinado ponto de partida sempre leva a um determinado "
        "resultado.",

        "Antes de qualquer afirmação sobre o impacto do programa, seria necessário um desenho de avaliação "
        "com grupo de comparação; enquanto isso, vale acompanhar se o recuo maior visto na faixa de 11 a 13 "
        "anos na segunda transição se repete em ciclos futuros.",
    ],
    11: [
        "Uma parte dos estudantes elegíveis de um ano não é reencontrada no ano seguinte — 27,0% entre 2022 e "
        "2023, e 22,1% entre 2023 e 2024. Quem não foi reencontrado tinha, em média, indicadores de "
        "desempenho e de ponto de virada mais baixos do que quem continuou, principalmente na primeira "
        "transição.",

        "Isso é um indício de que a perda de acompanhamento pode não ser aleatória: estudantes com "
        "indicadores mais baixos parecem sair ou deixar de ser registrados com mais frequência, ao menos na "
        "primeira transição — mas esse padrão não se repetiu com a mesma força na segunda, então não é uma "
        "conclusão definitiva.",

        "Para a Associação, isso reforça a importância de registrar o motivo e a data de saída ou "
        "transferência de cada estudante, e de considerar esse possível viés ao interpretar qualquer "
        "resultado que dependa de estudantes acompanhados em mais de um ano — incluindo o próprio modelo "
        "preditivo da pergunta 9.",

        "\"Não reencontrado\" não é o mesmo que \"evadiu\": mudança de instituição, erro de registro e "
        "outros motivos não podem ser distinguidos apenas com os dados disponíveis.",
    ],
}


def conclusao_fluida(numero: int) -> list[str]:
    """Lista de 2 a 4 parágrafos contínuos para a conclusão da pergunta —
    reescrita editorial dos mesmos achados já aprovados em
    `pergunta["conclusao"]`, sem rótulos nem coeficientes."""
    return _CONCLUSOES_FLUIDAS[numero]
