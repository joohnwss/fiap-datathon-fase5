"""Calculadoras de indicadores com fórmula institucional confirmada.

Ver `docs/auditoria_calculadoras_indicadores.md` para a auditoria completa
(revisada em 25/09/2026 — releitura de `DATATHON/PEDE_ Pontos
importantes.docx`, incluindo as 10 imagens/tabelas incorporadas ao
documento, não só o texto plano). Fórmulas confirmadas e implementadas
nesta rodada: defasagem, IAN, sugestão de fase ideal por idade (nunca
automática), IDA (fases 0–7, três notas), IAA (Tabela 40, 6 perguntas) e
INDE (informação complementar, nunca enviado ao modelo). IEG, IPS, IPP e
IPV continuam sem calculadora — os questionários/registros que os compõem
não têm escala ou lista de componentes fechada em nenhuma fonte
disponível.

Módulo puro (sem `streamlit`, sem leitura de dados privados): só as regras
aritméticas/de tabela documentadas, testável isoladamente.
"""
from __future__ import annotations

import math

FASES_VALIDAS: tuple[str, ...] = tuple(str(n) for n in range(8))  # contrato congelado do modelo: "0".."7"
FASES_FICHA: tuple[str, ...] = tuple(str(n) for n in range(9))  # domínio documental da ficha: Alfa..Fase 8


class EntradaInvalidaError(ValueError):
    """Entrada fora do domínio documentado para uma calculadora de indicador."""


def calcular_defasagem(fase_efetiva: int, fase_ideal: int) -> int:
    """D = fase efetiva − fase ideal (`PEDE_ Pontos importantes.docx`,
    parágrafo da seção "Defasagem", exemplo da linha 280/2024: fase efetiva
    2, fase ideal 3 → D = −1).

    Ambas as fases devem estar no domínio documentado 0–8 da ficha."""
    for nome, valor in (("fase efetiva", fase_efetiva), ("fase ideal", fase_ideal)):
        if isinstance(valor, bool) or not isinstance(valor, int):
            raise EntradaInvalidaError(f"A {nome} deve ser um número inteiro entre 0 e 8.")
        if valor < 0 or valor > 8:
            raise EntradaInvalidaError(f"A {nome} deve estar entre 0 e 8.")
    return fase_efetiva - fase_ideal


def ian_pela_defasagem(defasagem: float | int) -> float:
    """IAN a partir de D: D≥0→10; −2≤D<0→5; D<−2→2,5.

    (`PEDE_ Pontos importantes.docx`, Tabela 41 — mesma regra já usada em
    `src/dados_pede.py:expected_ian_value` para as análises descritivas.)
    """
    if defasagem is None or isinstance(defasagem, bool):
        raise EntradaInvalidaError("A defasagem é obrigatória para calcular o IAN.")
    try:
        d = float(defasagem)
    except (TypeError, ValueError):
        raise EntradaInvalidaError("A defasagem deve ser um número.") from None
    if not math.isfinite(d):
        raise EntradaInvalidaError("A defasagem deve ser um número finito.")
    if d >= 0:
        return 10.0
    if d >= -2:
        return 5.0
    return 2.5


def categoria_defasagem(defasagem: float | int) -> str:
    """Rótulo em linguagem simples da situação de defasagem (Tabela 41)."""
    if defasagem is None or isinstance(defasagem, bool):
        raise EntradaInvalidaError("A defasagem é obrigatória.")
    try:
        d = float(defasagem)
    except (TypeError, ValueError):
        raise EntradaInvalidaError("A defasagem deve ser um número.") from None
    if not math.isfinite(d):
        raise EntradaInvalidaError("A defasagem deve ser um número finito.")
    if d >= 0:
        return "Em fase"
    if d >= -2:
        return "Defasagem moderada"
    return "Defasagem severa"


# ---------------------------------------------------------------------------
# Idade → sugestão de fase ideal (Tabela 4, `PEDE_ Pontos importantes.docx`).
# Nunca aplicada automaticamente: a própria tabela tem faixas etárias que se
# sobrepõem na fronteira (ex.: 8 anos cabe em Alfa "7–8" e em Fase 1 "8–9"),
# então idades de fronteira retornam mais de uma candidata e a interface
# exige confirmação humana sempre — mesmo quando há uma única candidata.
# ---------------------------------------------------------------------------
_FAIXAS_IDADE_FASE: tuple[tuple[str, str, int, int | None], ...] = (
    ("Alfa (1º/2º ano)", "0", 7, 8),
    ("Fase 1 (3º/4º ano)", "1", 8, 9),
    ("Fase 2 (5º/6º ano)", "2", 10, 11),
    ("Fase 3 (7º/8º ano)", "3", 12, 13),
    ("Fase 4 (9º ano)", "4", 14, 14),
    ("Fase 5 (1º EM)", "5", 15, 15),
    ("Fase 6 (2º EM)", "6", 16, 16),
    ("Fase 7 (3º EM)", "7", 17, 17),
    ("Fase 8 (universidade)", "8", 18, None),
)


def sugerir_fase_ideal_por_idade(idade: int) -> dict:
    """Sugestão de fase ideal a partir da idade (Tabela 4) — nunca um valor
    final. Retorna um dicionário com as fases candidatas (rótulo + código),
    nunca só um código, para que a interface sempre peça confirmação
    explícita, mesmo quando há uma única candidata.

    `{"candidatas": [(rótulo, código), ...], "ambigua": bool}` —
    `candidatas` vem vazio quando a idade não bate com nenhuma faixa
    documentada (ex.: menor que 7 anos)."""
    if isinstance(idade, bool) or not isinstance(idade, int):
        raise EntradaInvalidaError("A idade deve ser um número inteiro de anos completos.")
    if idade < 0 or idade > 100:
        raise EntradaInvalidaError("A idade deve estar entre 0 e 100 anos.")
    candidatas = [
        (rotulo, codigo) for rotulo, codigo, minimo, maximo in _FAIXAS_IDADE_FASE
        if idade >= minimo and (maximo is None or idade <= maximo)
    ]
    return {"candidatas": candidatas, "ambigua": len(candidatas) > 1}


# ---------------------------------------------------------------------------
# IDA — Indicador de Desempenho Acadêmico (fases 0–7 apenas; a Fase 8 usa a
# média das disciplinas cursadas no ensino superior, não documentada em
# detalhe, e está fora do domínio de `fase_origem` nesta ficha).
# ---------------------------------------------------------------------------

def calcular_ida(nota_matematica: float, nota_portugues: float, nota_ingles: float) -> float:
    """IDA = (Matemática + Português + Inglês) / 3 (`PEDE_ Pontos
    importantes.docx`, seção "IDA"). As três notas são obrigatórias — nunca
    substitui uma nota ausente por zero, média ou qualquer valor estimado."""
    notas = {"Matemática": nota_matematica, "Português": nota_portugues, "Inglês": nota_ingles}
    valores = []
    for nome, valor in notas.items():
        if valor is None or isinstance(valor, bool):
            raise EntradaInvalidaError(f"A nota de {nome} é obrigatória para calcular o IDA.")
        try:
            numero = float(valor)
        except (TypeError, ValueError):
            raise EntradaInvalidaError(f"A nota de {nome} deve ser um número.") from None
        if not math.isfinite(numero):
            raise EntradaInvalidaError(f"A nota de {nome} deve ser um número finito.")
        if numero < 0 or numero > 10:
            raise EntradaInvalidaError(f"A nota de {nome} deve estar entre 0 e 10.")
        valores.append(numero)
    return sum(valores) / 3


# ---------------------------------------------------------------------------
# IAA — Indicador de Autoavaliação (Tabela 40, seis perguntas fixas, quatro
# alternativas A/B/C/D, valor em pontos por alternativa conforme o grupo de
# fases). Fase 8 não ocorre no domínio de `fase_origem` desta ficha.
# ---------------------------------------------------------------------------

PERGUNTAS_IAA: tuple[str, ...] = (
    "Como se sente consigo mesmo?",
    "Como se sente sobre os estudos?",
    "Como se sente sobre sua vida familiar?",
    "Como se sente sobre sua relação com os amigos?",
    "Como se sente sobre a Associação Passos Mágicos?",
    "Como se sente sobre seus professores na Passos Mágicos?",
)

_PONTOS_IAA_0_A_2: dict[str, float] = {"A": 10 / 6, "B": 7 / 6, "C": 3.5 / 6}
_PONTOS_IAA_3_A_8: dict[str, float] = {"A": 10 / 6, "B": 7.5 / 6, "C": 5 / 6, "D": 2.5 / 6}


def grupo_fase_iaa(fase_origem: str) -> str:
    """"0-2" ou "3-8", conforme a Tabela 40 usa uma coluna de pontuação
    diferente para cada grupo de fases."""
    if fase_origem not in FASES_FICHA:
        raise EntradaInvalidaError(f"Fase {fase_origem!r} fora do domínio 0–8.")
    return "0-2" if fase_origem in ("0", "1", "2") else "3-8"


def calcular_iaa(fase_origem: str, respostas: dict[int, str]) -> float:
    """Soma os pontos das 6 perguntas da Tabela 40, conforme a alternativa
    (A/B/C/D) escolhida em cada uma e o grupo de fases do estudante. Exige
    resposta para as 6 perguntas — nunca completa pergunta sem resposta."""
    grupo = grupo_fase_iaa(fase_origem)
    tabela = _PONTOS_IAA_0_A_2 if grupo == "0-2" else _PONTOS_IAA_3_A_8
    total = 0.0
    for numero in range(1, 7):
        resposta = respostas.get(numero)
        if resposta is None:
            raise EntradaInvalidaError(f"Falta a resposta da pergunta {numero} de 6.")
        resposta = str(resposta).strip().upper()
        if resposta not in tabela:
            opcoes = "/".join(sorted(tabela))
            raise EntradaInvalidaError(f"Resposta da pergunta {numero} deve ser uma de: {opcoes}.")
        total += tabela[resposta]
    return total


# ---------------------------------------------------------------------------
# INDE — Índice de Desenvolvimento Educacional (informação complementar;
# nunca enviado ao modelo, nunca confundido com a probabilidade da
# estimativa). Calculado só quando TODOS os componentes exigidos pela fase
# estão disponíveis — nunca com substituição por zero nem parcial.
# ---------------------------------------------------------------------------

_PESOS_INDE_0_A_7: dict[str, float] = {
    "ian": 0.1, "ida": 0.2, "ieg": 0.2, "iaa": 0.1, "ips": 0.1, "ipp": 0.1, "ipv": 0.2,
}
_PESOS_INDE_FASE_8: dict[str, float] = {
    "ian": 0.1, "ida": 0.4, "ieg": 0.2, "iaa": 0.1, "ips": 0.2,
}


def pesos_inde(fase_origem: str) -> dict[str, float]:
    """Pesos oficiais do INDE por componente, conforme a fase (Quadro
    "Composição do INDE"). Fase 8 nunca ocorre no domínio de `fase_origem`
    desta ficha, mas a função aceita "8" para fins de documentação/teste."""
    if fase_origem == "8":
        return dict(_PESOS_INDE_FASE_8)
    if fase_origem in FASES_VALIDAS:
        return dict(_PESOS_INDE_0_A_7)
    raise EntradaInvalidaError(f"Fase {fase_origem!r} fora do domínio 0–8.")


def calcular_inde(fase_origem: str, componentes: dict[str, float | None]) -> tuple[float | None, list[str]]:
    """`(valor, faltantes)`. `valor` é `None` (e `faltantes` lista as chaves
    ausentes) quando nem todos os componentes exigidos pela fase estão
    disponíveis — nunca calcula um INDE parcial nem substitui componente
    ausente por zero."""
    pesos = pesos_inde(fase_origem)
    faltantes = [chave for chave in pesos if componentes.get(chave) is None]
    if faltantes:
        return None, faltantes
    total = 0.0
    for chave, peso in pesos.items():
        valor = componentes[chave]
        try:
            numero = float(valor)
        except (TypeError, ValueError):
            raise EntradaInvalidaError(f"O componente {chave!r} do INDE deve ser um número.") from None
        if not math.isfinite(numero):
            raise EntradaInvalidaError(f"O componente {chave!r} do INDE deve ser um número finito.")
        total += numero * peso
    return total, []
