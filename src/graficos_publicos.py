"""Gráficos interativos do painel "Panorama e resultados".

Módulo exclusivamente de apresentação: cada função `_grafico_qN` recebe o
dicionário de uma pergunta já carregado (e com hash conferido) de
`reports/public/perguntas_oficiais_v1.json` e constrói um `plotly.graph_objects.Figure`
lendo os números diretamente de `pergunta["principais_numeros"]` — nenhum
valor numérico oficial é duplicado como literal aqui. O gráfico estático
(`pergunta["grafico"]`, um PNG com hash verificado) continua a ser exibido
como o artefato "oficial" e reprodutível; o gráfico interativo desta camada
é complementar, construído em tempo de execução a partir dos MESMOS números
já validados.

Paleta categórica validada (`dataviz`, ordem fixa, nunca ciclada
arbitrariamente): azul, laranja, água, amarelo, magenta, verde, violeta,
vermelho. Cores de status (bom/atenção/sério/crítico) são reservadas e nunca
reaproveitadas como cor de série.
"""
from __future__ import annotations

import plotly.graph_objects as go

# ---------------------------------------------------------------------------
# Paleta validada (skill `dataviz`, references/palette.md) — ordem fixa.
# ---------------------------------------------------------------------------

CATEGORICAL = (
    "#2a78d6",  # 1 azul
    "#eb6834",  # 2 laranja
    "#1baf7a",  # 3 água
    "#eda100",  # 4 amarelo
    "#e87ba4",  # 5 magenta
    "#008300",  # 6 verde
    "#4a3aa7",  # 7 violeta
    "#e34948",  # 8 vermelho
)
SEQUENCIAL_AZUL = ("#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95")
STATUS = {"bom": "#0ca30c", "atencao": "#fab219", "serio": "#ec835a", "critico": "#d03b3b"}
GRID = "#e1e0d9"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
SURFACE = "#fcfcfb"

_LAYOUT_BASE = dict(
    paper_bgcolor=SURFACE,
    plot_bgcolor=SURFACE,
    font=dict(family="system-ui, -apple-system, 'Segoe UI', sans-serif", size=13, color="#0b0b0b"),
    margin=dict(l=48, r=24, t=56, b=48),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=12)),
    hoverlabel=dict(bgcolor="white", font_size=12),
)

_TEMA_CLARO = dict(surface="#fcfcfb", grid="#e1e0d9", ink_muted="#898781",
                    ink_secondary="#52514e", texto="#0b0b0b", hover_bg="white")
_TEMA_ESCURO = dict(surface="#16302c", grid="#2a423d", ink_muted="#9fb0ac",
                     ink_secondary="#cdd9d6", texto="#eef2f0", hover_bg="#1f3b37")


def aplicar_tema(escuro: bool) -> None:
    """Ajusta fundo/grade/texto dos gráficos para o modo claro ou escuro
    selecionado na interface (`st.session_state["tema_aparencia"]`).

    Os gráficos não são cacheados (`graficos_interativos()` é chamado direto
    a cada renderização de `streamlit_app.py`), então basta atualizar estas
    variáveis de módulo no início do script para que todo gráfico gerado no
    mesmo rerun já reflita o modo atual — nenhuma figura antiga fica presa
    ao tema anterior. A paleta categórica (`CATEGORICAL`) não muda: só o
    fundo, a grade e as cores de texto/eixo, para preservar a validação de
    acessibilidade já feita sobre as cores de série."""
    global SURFACE, GRID, INK_MUTED, INK_SECONDARY
    valores = _TEMA_ESCURO if escuro else _TEMA_CLARO
    SURFACE = valores["surface"]
    GRID = valores["grid"]
    INK_MUTED = valores["ink_muted"]
    INK_SECONDARY = valores["ink_secondary"]
    _LAYOUT_BASE["paper_bgcolor"] = SURFACE
    _LAYOUT_BASE["plot_bgcolor"] = SURFACE
    _LAYOUT_BASE["font"]["color"] = valores["texto"]
    _LAYOUT_BASE["hoverlabel"]["bgcolor"] = valores["hover_bg"]
    _LAYOUT_BASE["hoverlabel"]["font_color"] = valores["texto"] if escuro else "#0b0b0b"


def _aplicar_layout(fig: go.Figure, titulo: str, *, y_titulo: str = "", altura: int = 380) -> go.Figure:
    fig.update_layout(
        **_LAYOUT_BASE,
        title=dict(text=titulo, font=dict(size=15, weight="bold" if hasattr(go.layout.Title(), "font") else None)),
        height=altura,
        yaxis=dict(title=y_titulo, gridcolor=GRID, zerolinecolor=GRID, tickfont=dict(color=INK_MUTED)),
        xaxis=dict(gridcolor=SURFACE, tickfont=dict(color=INK_MUTED)),
        bargap=0.28,
    )
    return fig


def _numeros(pergunta: dict) -> list[dict]:
    return pergunta["principais_numeros"]


def _complementares(pergunta: dict) -> list[dict]:
    return pergunta.get("analises_complementares_numeros") or []


# ---------------------------------------------------------------------------
# Q1 — perfil de defasagem (barras 100% por ano)
# ---------------------------------------------------------------------------

def _grafico_q1(pergunta: dict) -> go.Figure:
    linhas = _numeros(pergunta)
    anos = sorted({r["Ano"] for r in linhas})
    categorias_ordem = ["sem defasagem", "moderada", "severa", "com defasagem (moderada + severa)"]
    cor_por_categoria = {
        "sem defasagem": CATEGORICAL[0],
        "moderada": CATEGORICAL[3],
        "severa": CATEGORICAL[7],
        "com defasagem (moderada + severa)": CATEGORICAL[3],
    }
    fig = go.Figure()
    for categoria in categorias_ordem:
        pontos = [r for r in linhas if r["Categoria"] == categoria]
        if not pontos:
            continue
        xs = [r["Ano"] for r in pontos]
        ys = [r["Contagem"] for r in pontos]
        textos = [r["Percentual"] for r in pontos]
        fig.add_bar(
            x=xs, y=ys, name=categoria.capitalize(), marker_color=cor_por_categoria[categoria],
            text=textos, textposition="inside", hovertemplate="%{x} — " + categoria + ": %{y} (%{text})<extra></extra>",
        )
    fig.update_layout(barmode="stack")
    fig = _aplicar_layout(fig, "Perfil anual de defasagem (contagens)", y_titulo="Registros")
    fig.update_xaxes(type="category")  # anos são categorias, nunca eixo numérico interpolável
    return fig


def _grafico_q1_media_ian(pergunta: dict) -> go.Figure:
    """Evolução da média anual do IAN nos três anos. A média de 2024 foi
    auditada (auditoria de divulgação conjunta, correção pontual de
    24/09/2026) e confirmada segura para publicação com arredondamento a
    duas casas decimais — o arredondamento deixa mais de uma divisão
    exata entre moderada/severa igualmente possível, então não permite
    reconstruir a célula protegida (ver nota de análises complementares)."""
    linhas = [r for r in _complementares(pergunta) if r.get("Recorte") == "Média anual do IAN"]
    anos = [r["Ano"] for r in linhas]
    valores = [r["Valor"] if isinstance(r["Valor"], (int, float)) else None for r in linhas]
    fig = go.Figure()
    fig.add_bar(
        x=anos, y=[v if v is not None else 0 for v in valores],
        marker_color=[CATEGORICAL[0] if v is not None else GRID for v in valores],
        text=[f"{v:.2f}" if v is not None else "não publicado" for v in valores], textposition="outside",
        hovertemplate="%{x}: %{text}<extra></extra>",
    )
    fig.update_layout(showlegend=False)
    fig = _aplicar_layout(fig, "Média anual do IAN", y_titulo="IAN médio (0–10)")
    # Sem isto, o Plotly detecta os rótulos "2022"/"2023"/"2024" como eixo
    # numérico contínuo e desenha ticks intermediários como "2.021,5" — os
    # anos são categorias, não uma escala numérica interpolável.
    fig.update_xaxes(type="category")
    return fig


def _grafico_q1_sexo_idade(pergunta: dict) -> go.Figure:
    """Comparação binária por sexo nos três anos.

    Mantém apenas as seis barras necessárias para que o recorte continue
    legível em telas estreitas. O denominador fica no próprio eixo; a
    variação anual em pontos percentuais fica no tooltip. A análise por faixa
    etária aproximada continua disponível na tabela complementar.
    """
    linhas = _complementares(pergunta)
    sexo = [r for r in linhas if r.get("Recorte") == "Defasagem por sexo (sem/alguma defasagem)"]

    fig = go.Figure()
    categorias = ("sem defasagem", "alguma defasagem")
    cores = {"sem defasagem": CATEGORICAL[0], "alguma defasagem": CATEGORICAL[4],
             "moderada": CATEGORICAL[3], "severa": CATEGORICAL[7]}

    def _valor(row, categoria):
        bruto = row.get(categoria, "0")
        if isinstance(bruto, str) and "(" in bruto:
            return float(bruto.split("(")[0].replace(",", ".").rstrip("% "))
        return 0.0

    rotulos = [f"{'F' if r['Sexo'] == 'feminino' else 'M'}<br>{r['Ano']}<br>n={r['n']}" for r in sexo]
    variacoes = [r['Variação de "alguma defasagem" em p.p. vs. ano anterior'] for r in sexo]
    descricoes = [f"{r['Sexo'].capitalize()} · {r['Ano']} · n={r['n']}" for r in sexo]
    for categoria in categorias:
        valores = [_valor(r, categoria) for r in sexo]
        nome_serie = "Sem defasagem" if categoria == "sem defasagem" else "Alguma defasagem"
        fig.add_bar(x=rotulos, y=valores, name=nome_serie, marker_color=cores[categoria],
                    text=[f"{v:.1f}%" for v in valores], textposition="inside",
                    customdata=list(zip(descricoes, variacoes)),
                    hovertemplate=("%{customdata[0]}<br>" + categoria + ": %{y:.1f}%"
                                   "<br>Variação anual de alguma defasagem: %{customdata[1]}<extra></extra>"))
    fig.update_layout(barmode="stack")
    fig.add_annotation(
        text=("F = feminino · M = masculino<br>‘Alguma defasagem’ reúne moderada e severa<br>"
              "para não expor grupos pequenos demais para publicar com segurança."),
        xref="paper", yref="paper", x=0.5, y=-0.34, showarrow=False,
        font=dict(size=11, color=INK_MUTED),
    )
    fig = _aplicar_layout(
        fig, "Defasagem por sexo (2022–2024)",
        y_titulo="% em cada sexo/ano", altura=500,
    )
    fig.update_layout(
        margin=dict(l=44, r=12, t=86, b=112),
        title=dict(x=0.5, xanchor="center", y=0.98, yanchor="top", font=dict(size=14)),
        legend=dict(orientation="h", yanchor="bottom", y=1.06, xanchor="center", x=0.5, font=dict(size=10)),
        xaxis=dict(tickangle=0, tickfont=dict(size=10, color=INK_MUTED)),
    )
    return fig


# ---------------------------------------------------------------------------
# Q2 — IDA médio por fase e ano (linhas) + pares longitudinais (barras)
# ---------------------------------------------------------------------------

def _grafico_q2(pergunta: dict) -> go.Figure:
    linhas = [r for r in _numeros(pergunta) if r["Recorte"].startswith("Fase") or r["Recorte"] == "Todos os registros"]
    fig = go.Figure()
    for indice, ano in enumerate(("2022", "2023", "2024")):
        fig.add_scatter(
            x=[r["Recorte"].replace("Fase ", "F") for r in linhas],
            y=[r[ano] for r in linhas],
            mode="lines+markers", name=ano, line=dict(width=2, color=CATEGORICAL[indice]),
            marker=dict(size=9),
            hovertemplate="%{x} em " + ano + ": %{y:.2f}<extra></extra>",
        )
    return _aplicar_layout(fig, "IDA médio por fase e ano", y_titulo="IDA médio")


# ---------------------------------------------------------------------------
# Q3, Q4 — associações (barras simples de ρ)
# ---------------------------------------------------------------------------

def _grafico_associacoes(pergunta: dict, titulo: str) -> go.Figure:
    linhas = _numeros(pergunta)
    fig = go.Figure()
    fig.add_bar(
        x=[r["Relação"] for r in linhas], y=[r["ρ ajustado por ano"] for r in linhas],
        marker_color=CATEGORICAL[:len(linhas)],
        text=[f"ρ={r['ρ ajustado por ano']:.3f} (n={r['n']})" for r in linhas], textposition="outside",
        hovertemplate="%{x}: ρ=%{y:.3f}<extra></extra>",
    )
    fig.update_layout(showlegend=False)
    return _aplicar_layout(fig, titulo, y_titulo="ρ de Spearman")


def _grafico_q3(pergunta: dict) -> go.Figure:
    return _grafico_associacoes(pergunta, "Associação de IEG com IDA e IPV (ajustada por ano)")


def _grafico_q4(pergunta: dict) -> go.Figure:
    return _grafico_associacoes(pergunta, "Coerência ordinal da autoavaliação (IAA)")


# ---------------------------------------------------------------------------
# Q5 — IPS de origem × variação futura (barras divergentes em torno de zero)
# ---------------------------------------------------------------------------

def _grafico_q5(pergunta: dict) -> go.Figure:
    linhas = _numeros(pergunta)
    fig = go.Figure()
    rotulos = [f"{r['Transição']}<br>{r['Desfecho futuro']}" for r in linhas]
    valores = [r["ρ"] for r in linhas]
    cores = [CATEGORICAL[0] if v >= 0 else CATEGORICAL[7] for v in valores]
    fig.add_bar(
        x=rotulos, y=valores, marker_color=cores,
        text=[f"ρ={v:.3f} (n={r['n']})" for v, r in zip(valores, linhas)], textposition="outside",
        hovertemplate="%{x}: ρ=%{y:.3f}<extra></extra>",
    )
    fig.add_hline(y=0, line_color=INK_MUTED, line_width=1)
    fig.update_layout(showlegend=False)
    return _aplicar_layout(fig, "IPS na origem × variação futura de IDA/IEG", y_titulo="ρ de Spearman")


# ---------------------------------------------------------------------------
# Q6 — IPP: associações (barras) + médias por categoria em 2023 (barras)
# ---------------------------------------------------------------------------

def _grafico_q6(pergunta: dict) -> go.Figure:
    linhas = _numeros(pergunta)
    associacoes = [r for r in linhas if r["Medida"] in ("IPP × IAN", "IPP × defasagem")]
    medias = [r for r in linhas if r["Medida"].startswith("IPP médio") and r["Valor"] is not None]

    fig = go.Figure()
    for indice, medida in enumerate(("IPP × IAN", "IPP × defasagem")):
        pontos = [r for r in associacoes if r["Medida"] == medida]
        fig.add_bar(
            x=[r["Ano"] for r in pontos], y=[r["Valor"] for r in pontos], name=medida,
            marker_color=CATEGORICAL[indice],
            hovertemplate=medida + " em %{x}: ρ=%{y:.3f}<extra></extra>",
        )
    fig.update_layout(barmode="group")
    fig = _aplicar_layout(fig, "IPP × IAN e IPP × defasagem, por ano", y_titulo="ρ de Spearman")
    fig.update_xaxes(type="category")
    return fig


def _grafico_q6_medias(pergunta: dict) -> go.Figure:
    """Segundo gráfico da pergunta 6: médias de IPP por categoria (2023,
    único ano com essa decomposição publicável)."""
    linhas = [r for r in _numeros(pergunta) if r["Medida"].startswith("IPP médio") and r["Valor"] is not None]
    fig = go.Figure()
    fig.add_bar(
        x=[r["Medida"].replace("IPP médio — ", "").capitalize() for r in linhas],
        y=[r["Valor"] for r in linhas], marker_color=CATEGORICAL[2],
        text=[f"n={r['n']}" for r in linhas], textposition="outside",
        hovertemplate="%{x}: IPP médio=%{y:.2f}<extra></extra>",
    )
    fig.update_layout(showlegend=False)
    return _aplicar_layout(fig, "IPP médio por categoria de defasagem — 2023", y_titulo="IPP médio (0–10)")


# ---------------------------------------------------------------------------
# Q7 — IPV: associações contemporâneas + associações futuras
# ---------------------------------------------------------------------------

def _grafico_q7(pergunta: dict) -> go.Figure:
    linhas = [r for r in _numeros(pergunta) if r["Janela"].startswith("Mesmo ano")]
    fig = go.Figure()
    fig.add_bar(
        x=[r["Janela"].replace("Mesmo ano — ", "") for r in linhas], y=[r["ρ"] for r in linhas],
        marker_color=CATEGORICAL[:len(linhas)],
        text=[f"{r['Indicador']}: ρ={r['ρ']:.3f}" for r in linhas], textposition="outside",
        hovertemplate="%{x}: ρ=%{y:.3f}<extra></extra>",
    )
    fig.update_layout(showlegend=False)
    return _aplicar_layout(fig, "Maior associação contemporânea com IPV, por ano", y_titulo="ρ de Spearman")


def _grafico_q7_futuro(pergunta: dict) -> go.Figure:
    linhas = [r for r in _numeros(pergunta) if "→" in r["Janela"]]
    fig = go.Figure()
    for indice, indicador in enumerate(("IDA de origem", "IEG de origem", "IPS de origem")):
        pontos = [r for r in linhas if r["Indicador"] == indicador]
        fig.add_bar(
            x=[r["Janela"] for r in pontos], y=[r["ρ"] for r in pontos], name=indicador,
            marker_color=CATEGORICAL[indice],
            hovertemplate=indicador + " em %{x}: ρ=%{y:.3f}<extra></extra>",
        )
    fig.update_layout(barmode="group")
    return _aplicar_layout(fig, "Indicador de origem × IPV do ano seguinte", y_titulo="ρ de Spearman")


# ---------------------------------------------------------------------------
# Q8 — INDE médio dos perfis líderes por ano
# ---------------------------------------------------------------------------

def _grafico_q8(pergunta: dict) -> go.Figure:
    linhas = _numeros(pergunta)
    fig = go.Figure()
    fig.add_bar(
        x=[r["Ano"] for r in linhas], y=[r["INDE médio"] for r in linhas],
        marker_color=CATEGORICAL[0],
        text=[f"n={r['n']}" for r in linhas], textposition="outside",
        hovertemplate="%{x}: INDE médio=%{y:.2f}<extra></extra>",
    )
    fig.update_layout(showlegend=False)
    fig.add_annotation(text="Associação esperada pela composição do INDE — não causal",
                       xref="paper", yref="paper", x=0.5, y=-0.22, showarrow=False,
                       font=dict(size=11, color=INK_MUTED))
    fig = _aplicar_layout(fig, "Combinação de indicadores com maior nota global, por ano",
                          y_titulo="INDE médio", altura=420)
    fig.update_xaxes(type="category")
    return fig


# ---------------------------------------------------------------------------
# Q9 — recall OOF vs teste temporal + matriz de confusão
# ---------------------------------------------------------------------------

def _grafico_q9(pergunta: dict) -> go.Figure:
    linhas = [r for r in _numeros(pergunta) if r["Recall"] is not None]
    fig = go.Figure()
    fig.add_bar(
        x=[r["Avaliação"].split(" — ")[0] for r in linhas], y=[r["Recall"] for r in linhas],
        marker_color=[STATUS["bom"], STATUS["critico"]],
        text=[f"{r['Recall'] * 100:.1f}%" for r in linhas], textposition="outside",
        hovertemplate="%{x}: recall=%{y:.1%}<extra></extra>",
    )
    fig.update_layout(showlegend=False, yaxis_tickformat=".0%")
    return _aplicar_layout(fig, "Recall: desenvolvimento (OOF) × teste temporal", y_titulo="Recall")


def _grafico_q9_equidade_fase(pergunta: dict) -> go.Figure:
    """Auditoria de equidade por fase (recall no teste temporal), a partir
    de analises_complementares_numeros — dado já congelado e aprovado em
    reports/metricas_modelagem.json (robustez.equidade_fase)."""
    linhas = [r for r in _complementares(pergunta)
             if r.get("Recorte") == "Equidade por fase — teste temporal" and isinstance(r.get("Recall"), (int, float))]
    fig = go.Figure()
    fig.add_bar(
        x=[f"Fase {r['Fase']}" for r in linhas], y=[r["Recall"] for r in linhas],
        marker_color=CATEGORICAL[:len(linhas)],
        text=[f"n={r['n']}, eventos={r['Eventos']}" for r in linhas], textposition="outside",
        hovertemplate="%{x}: recall=%{y:.1%}<extra></extra>",
    )
    fig.update_layout(showlegend=False, yaxis_tickformat=".0%")
    return _aplicar_layout(fig, "Equidade do modelo por fase — recall no teste temporal", y_titulo="Recall")


def _grafico_q9_matriz(pergunta: dict) -> go.Figure:
    linha_teste = next(r for r in _numeros(pergunta) if r["Avaliação"].startswith("Teste temporal"))
    verdadeiros_positivos = linha_teste["Eventos"] - linha_teste["Falsos negativos"]
    verdadeiros_negativos = linha_teste["n"] - linha_teste["Eventos"] - linha_teste["Falsos positivos"]
    z = [[verdadeiros_negativos, linha_teste["Falsos positivos"]],
         [linha_teste["Falsos negativos"], verdadeiros_positivos]]
    fig = go.Figure(data=go.Heatmap(
        z=z, x=["Previsto: sem risco", "Previsto: risco"], y=["Real: sem risco", "Real: risco"],
        colorscale=[[0, SEQUENCIAL_AZUL[0]], [1, SEQUENCIAL_AZUL[-1]]],
        text=z, texttemplate="%{text}", showscale=False,
        hovertemplate="%{y} / %{x}: %{z}<extra></extra>",
    ))
    fig.update_layout(**_LAYOUT_BASE, title=dict(text="Matriz de confusão — teste temporal (2023→2024)", font=dict(size=15)),
                      height=380, yaxis=dict(autorange="reversed"))
    return fig


# ---------------------------------------------------------------------------
# Q10 — transições de Pedra (barras 100% empilhadas)
# ---------------------------------------------------------------------------

def _grafico_q10(pergunta: dict) -> go.Figure:
    linhas = _numeros(pergunta)
    fig = go.Figure()
    for rotulo, cor in (("Melhoria", STATUS["bom"]), ("Estabilidade", INK_MUTED), ("Piora", STATUS["critico"])):
        fig.add_bar(
            x=[r["Transição"] for r in linhas],
            y=[float(r[rotulo].replace(",", ".").rstrip("%")) for r in linhas],
            name=rotulo, marker_color=cor,
            hovertemplate=rotulo + " em %{x}: %{y:.1f}%<extra></extra>",
        )
    fig.update_layout(barmode="stack")
    return _aplicar_layout(fig, "Transições observadas entre Pedras", y_titulo="% dos pares")


def _grafico_q10_ida_por_pedra(pergunta: dict) -> go.Figure:
    """Variação média de IDA por Pedra de origem, nas duas transições —
    a partir de analises_complementares_numeros."""
    linhas = [r for r in _complementares(pergunta) if r.get("Recorte") == "Variação média de IDA por Pedra de origem"]
    fig = go.Figure()
    for indice, transicao in enumerate(("2022→2023", "2023→2024")):
        pontos = [r for r in linhas if r["Transição"] == transicao]
        fig.add_bar(
            x=[r["Pedra de origem"] for r in pontos], y=[r["Δ IDA médio"] for r in pontos],
            name=transicao, marker_color=CATEGORICAL[indice],
            hovertemplate=transicao + " — %{x}: Δ IDA=%{y:.2f}<extra></extra>",
        )
    fig.add_hline(y=0, line_color=INK_MUTED, line_width=1)
    fig.update_layout(barmode="group")
    return _aplicar_layout(fig, "Variação média de IDA por Pedra de origem", y_titulo="Δ IDA médio")


# ---------------------------------------------------------------------------
# Q11 — perdas de correspondência por transição
# ---------------------------------------------------------------------------

def _grafico_q11(pergunta: dict) -> go.Figure:
    import re
    linhas = [r for r in _numeros(pergunta) if r["Evidência"].startswith("Perda de correspondência")]
    transicoes, percentuais, brutos = [], [], []
    for r in linhas:
        m = re.search(r"(\d{4}→\d{4}): (\d+) de (\d+) \(([\d,]+)%\)", r["Evidência"])
        if not m:
            continue
        transicoes.append(m.group(1))
        percentuais.append(float(m.group(4).replace(",", ".")))
        brutos.append(f"{m.group(2)} de {m.group(3)}")
    fig = go.Figure()
    fig.add_bar(
        x=transicoes, y=percentuais, marker_color=CATEGORICAL[3],
        text=brutos, textposition="outside",
        hovertemplate="%{x}: %{y:.1f}%% (%{text})<extra></extra>",
    )
    fig.update_layout(showlegend=False)
    return _aplicar_layout(fig, "Estudantes elegíveis sem correspondência no ano seguinte", y_titulo="% dos elegíveis")


_GRAFICOS_PRINCIPAIS = {
    1: _grafico_q1, 2: _grafico_q2, 3: _grafico_q3, 4: _grafico_q4, 5: _grafico_q5,
    6: _grafico_q6, 7: _grafico_q7, 8: _grafico_q8, 9: _grafico_q9, 10: _grafico_q10,
    11: _grafico_q11,
}
# Gráficos adicionais por pergunta. A partir da correção pós-auditoria
# comparativa (24/09/2026): Q1 ganhou um segundo gráfico (evolução da média
# do IAN, só nos anos publicáveis) e um terceiro (defasagem por sexo e por
# faixa etária APROXIMADA — nunca idade exata); Q9 ganhou um segundo (matriz
# de confusão) e um terceiro (equidade por fase/gênero/faixa etária
# aproximada); Q10 ganhou um segundo (IDA por Pedra de origem).
_GRAFICOS_SECUNDARIOS = {1: _grafico_q1_media_ian, 6: _grafico_q6_medias, 7: _grafico_q7_futuro, 9: _grafico_q9_matriz}
_GRAFICOS_TERCIARIOS = {1: _grafico_q1_sexo_idade, 9: _grafico_q9_equidade_fase, 10: _grafico_q10_ida_por_pedra}


def graficos_interativos(numero: int, pergunta: dict) -> list[go.Figure]:
    """Devolve a lista de gráficos interativos (1 a 3) para a pergunta
    `numero`, construídos a partir de `pergunta["principais_numeros"]` e
    `pergunta["analises_complementares_numeros"]` — as mesmas tabelas já
    exibidas e com hash conferido, nunca um valor novo calculado aqui."""
    figuras = [_GRAFICOS_PRINCIPAIS[numero](pergunta)]
    segunda = _GRAFICOS_SECUNDARIOS.get(numero)
    if segunda is not None:
        figuras.append(segunda(pergunta))
    terceira = _GRAFICOS_TERCIARIOS.get(numero)
    if terceira is not None:
        figuras.append(terceira(pergunta))
    return figuras
