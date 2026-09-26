"""Aplicação Streamlit da Associação Passos Mágicos.

Ferramenta de apoio ao acompanhamento educacional para professores(as) e
profissionais da instituição, construída sobre o modelo oficialmente
avaliado do projeto. Usa exclusivamente `artifacts/modelo_avaliado.joblib`,
sem retreino, recalibração ou geração de novas métricas. A lógica de dados
fica em `src/inferencia.py` e o texto editorial em `src/textos_aplicacao.py`;
este arquivo cuida da interface e da navegação entre as quatro áreas da
aplicação (Início, Panorama e resultados, Avaliar um caso, Entenda os
indicadores).

Privacidade: nenhuma entrada do usuário é persistida, logada ou enviada a
serviços externos. A identificação da ficha existe somente durante a sessão,
não entra no modelo nem no nome do download. Nenhuma base de dados é
carregada ou aceita por upload.
"""
from __future__ import annotations

import html
import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

_ROOT = Path(__file__).resolve().parent
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import calculadoras_indicadores as calculadoras  # noqa: E402
import ficha_individual as ficha  # noqa: E402
import graficos_publicos as graficos  # noqa: E402
import inferencia  # noqa: E402
import narrativa_publica as narrativa  # noqa: E402
import rastreabilidade as rastro  # noqa: E402
import textos_aplicacao as textos  # noqa: E402

METRICAS_NEGOCIO_PATH = "reports/public/perguntas_oficiais_v1.json"
MANIFESTO_NEGOCIO_PATH = "reports/public/manifesto_integridade_v1.json"
CSS_PATH = _ROOT / "assets" / "styles" / "app.css"
LOGO_PATH = _ROOT / "assets" / "brand" / "passos-magicos-icon-cor.png"

st.set_page_config(
    page_title="Apoio ao acompanhamento educacional",
    page_icon="🎓",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Identidade visual — Claro/Escuro (revisão de identidade visual, 25/09/2026)
# ---------------------------------------------------------------------------

TEMA_CLARO = "Claro"
TEMA_ESCURO = "Escuro"
TEMA_KEY = "tema_aparencia"

# Ver docs/identidade_visual.md para a origem e a justificativa de cada cor
# (azul extraído do logo oficial; verde/amarelo/vermelho escolhidos para
# compor a paleta pedagógica pedida, com contraste WCAG verificado).
_VARIAVEIS_TEMA: dict[str, dict[str, str]] = {
    TEMA_CLARO: {
        "pm-bg": "#faf8f4", "pm-bg-elevado": "#ffffff", "pm-texto": "#22282c",
        "pm-texto-suave": "#5a6268", "pm-azul": "#145089", "pm-azul-claro": "#0367b0",
        "pm-verde": "#1e7a4f", "pm-amarelo": "#e8a400", "pm-vermelho": "#b23b3b",
        "pm-borda": "#e2ddd4", "pm-logo-fundo": "transparent",
    },
    TEMA_ESCURO: {
        "pm-bg": "#12211f", "pm-bg-elevado": "#16302c", "pm-texto": "#eef2f0",
        "pm-texto-suave": "#aab5b2", "pm-azul": "#5b9bd8", "pm-azul-claro": "#7fb8e8",
        "pm-verde": "#4caf7d", "pm-amarelo": "#f0c33c", "pm-vermelho": "#e07a7a",
        "pm-borda": "#2a423d", "pm-logo-fundo": "#f4f1ea",
    },
}


def _tema_atual() -> str:
    valor = st.session_state.get(TEMA_KEY, TEMA_CLARO)
    return valor if valor in _VARIAVEIS_TEMA else TEMA_CLARO


@st.cache_resource(show_spinner=False)
def _carregar_css() -> str:
    """Lê o CSS local e estático (assets/styles/app.css) uma única vez por
    processo — um recurso fixo do próprio código-fonte, não um dado de
    entrada do usuário (por isso o cache de RECURSO, não o de dados, a
    mesma convenção já usada para o modelo e os artefatos). Nenhum conteúdo
    de usuário, sessão ou formulário é interpolado; o texto injetado é
    exatamente o conteúdo do arquivo em disco. Puramente cosmético: se o
    arquivo não estiver presente numa cópia pública mínima, a aplicação
    continua funcionando normalmente, só sem o refinamento visual (nunca um
    erro fatal por causa de estilo)."""
    try:
        return CSS_PATH.read_text(encoding="utf-8")
    except OSError:
        return ""


def _aplicar_estilo_visual() -> None:
    """Injeta as variáveis do modo claro/escuro atual (`st.session_state`,
    nunca conteúdo de formulário) seguidas do CSS estático — a única
    chamada de todo o app que permite HTML bruto no markdown. O pequeno
    bloco de variáveis é gerado a cada execução (valores fixos de
    `_VARIAVEIS_TEMA`, escolhidos só pelo modo atual); o CSS em si continua
    vindo do arquivo estático em cache."""
    variaveis = "\n".join(f"  --{chave}: {valor};" for chave, valor in _VARIAVEIS_TEMA[_tema_atual()].items())
    st.markdown(f"<style>\n:root {{\n{variaveis}\n}}\n{_carregar_css()}</style>", unsafe_allow_html=True)

FASE_OPCOES = ("", *inferencia.PHASE_CATEGORIES)
FASE_IDEAL_OPCOES = ("", *calculadoras.FASES_FICHA)
PANORAMA_PERGUNTA_KEY = "panorama_pergunta"


def _rotulo_fase(valor: str) -> str:
    if valor == "":
        return "Selecione a fase"
    if valor == "0":
        return "0 — Alfa (alfabetização)"
    return f"{valor} — Fase {valor}"


@st.cache_resource(show_spinner="Carregando e validando os dados oficiais…")
def _carregar_aplicacao() -> inferencia.ApplicationContext:
    """Executado uma única vez por processo (cache de recurso, nunca de
    dados). Localiza a raiz, roda o validador público e carrega o modelo."""
    return inferencia.prepare_application()


class PainelIndisponivelError(RuntimeError):
    """Levantada quando o painel de perguntas de negócio não pode ser
    carregado com segurança (artefato ausente ou hash divergente). Nunca
    expõe caminho local completo nem hash completo na mensagem."""


@st.cache_resource(show_spinner="Carregando o panorama de dados…")
def _carregar_metricas_negocio(root: Path) -> dict:
    """Lê exclusivamente a camada pública sanitizada e valida seus hashes.

    O carregamento nunca acessa os artefatos históricos, `DATATHON/`,
    `local_data/` ou `local_recovery/`.
    """
    caminho_json = root / METRICAS_NEGOCIO_PATH
    caminho_manifesto = root / MANIFESTO_NEGOCIO_PATH
    if not caminho_json.is_file() or not caminho_manifesto.is_file():
        raise PainelIndisponivelError("Artefato de panorama ausente")
    try:
        metricas = json.loads(caminho_json.read_text(encoding="utf-8"))
        manifesto = json.loads(caminho_manifesto.read_text(encoding="utf-8"))
    except (OSError, ValueError) as erro:
        raise PainelIndisponivelError("Falha ao ler o artefato de panorama") from erro

    if metricas.get("camada") != "publica_sanitizada" or len(metricas.get("perguntas", [])) != 11:
        raise PainelIndisponivelError("Schema público do panorama inválido")
    hashes_registrados: dict = manifesto.get("output_hashes", {})
    caminhos_publicos = [METRICAS_NEGOCIO_PATH, *(p["grafico"] for p in metricas["perguntas"])]
    for caminho_relativo in caminhos_publicos:
        hash_esperado = hashes_registrados.get(caminho_relativo)
        arquivo = root / caminho_relativo
        if not hash_esperado or not arquivo.is_file():
            raise PainelIndisponivelError("Arquivo público ausente ou não registrado")
        if not rastro.file_matches_sha256(arquivo, hash_esperado):
            raise PainelIndisponivelError("Arquivo público com hash divergente do registro")
    return metricas


def _preencher_exemplo_sintetico() -> None:
    for campo in textos.CAMPOS_NUMERICOS:
        st.session_state[f"campo_{campo}"] = textos.INDICADORES[campo]["exemplo"]
    st.session_state[f"campo_{textos.CAMPO_FASE}"] = textos.INDICADORES[textos.CAMPO_FASE]["exemplo"]
    st.session_state["campo_identificacao_caso"] = "caso-sintetico"
    st.session_state["campo_idade_contexto"] = "10"
    st.session_state["campo_sexo_contexto"] = "Feminino"
    st.session_state["campo_fase_ideal_calculo"] = "2"
    st.session_state["campo_ipp_contexto"] = "7.0"
    st.session_state["modo_defasagem"] = textos.ROTULO_MODO_DEFASAGEM_CALCULADO
    st.session_state["modo_ida"] = textos.ROTULO_MODO_IDA_DIRETO
    st.session_state["modo_iaa"] = textos.ROTULO_MODO_IAA_DIRETO


# Rede de segurança: traduz qualquer termo técnico que ainda apareça em
# textos de `analises_publicas.py` antes de chegar à interface pública.
_TRADUCOES_JARGAO = {
    "caixa pequena": "grupo pequeno demais para publicar com segurança",
    "artefato interno": "registro interno da análise",
    "artefato congelado": "registro congelado do modelo",
    "células pequenas": "grupos pequenos",
    "células maiores": "grupos maiores",
    "partição de 2024": "recorte de 2024",
}


def _texto_publico(texto: str) -> str:
    for termo, traducao in _TRADUCOES_JARGAO.items():
        texto = texto.replace(termo, traducao)
    return texto


def _tabela_para_exibicao(linhas: list[dict]) -> pd.DataFrame:
    """Substitui `None` por um travessão antes de exibir a tabela na
    interface — a mesma convenção já usada por `render_report()` em
    `src/analises_publicas.py` para o relatório em markdown. Um `None` cru
    numa célula (ex.: a linha de supressão integral da pergunta 6) lia-se
    como um possível erro do sistema; a nota abaixo da tabela já explica o
    porquê, mas a própria célula precisa ser compreensível sozinha. Não
    altera `pergunta["principais_numeros"]` (a fonte, usada também pelos
    gráficos e por outras verificações) — só a cópia exibida.

    Colunas que passam a misturar números com o travessão são convertidas
    para texto explicitamente aqui: sem isso, a serialização Arrow do
    `st.dataframe` falha na primeira tentativa (tipo misto) e o Streamlit
    aplica um reparo automático internamente a cada render — funciona, mas
    dispara uma exceção capturada (e seu traceback no log do servidor) toda
    vez. Convertendo de antemão, a serialização funciona de primeira."""
    linhas_com_travessao = [
        {_RENOMEIA_COLUNA.get(chave, chave): ("—" if valor is None else valor) for chave, valor in linha.items()}
        for linha in linhas
    ]
    tabela = pd.DataFrame(linhas_com_travessao)
    # Uma coluna ausente em algumas linhas (ex.: uma tabela genérica que
    # mistura mais de um tipo de recorte) vira `NaN` do próprio pandas ao
    # montar o DataFrame — não passa pelo `None` tratado acima. Tratada aqui
    # antes de qualquer conversão de tipo, para nunca aparecer como "nan".
    tabela = tabela.where(tabela.notna(), "—")
    for coluna in tabela.columns:
        if tabela[coluna].map(type).nunique() > 1:
            tabela[coluna] = tabela[coluna].astype(str)
    return tabela


# Nomes de coluna compreensíveis, aplicados em toda tabela renderizada —
# tanto na tabela genérica de "Principais números" quanto na de recortes
# adicionais quando uma pergunta não tem tabela específica (revisão
# editorial, 24/09/2026, Parte 3, item 7).
_RENOMEIA_COLUNA = {
    "n": "Quantidade de estudantes",
    "Sexo": "Grupo",
}


def _capitulo_da_pergunta(numero: int) -> str:
    for capitulo, numeros in textos.CAPITULOS:
        if numero in numeros:
            return capitulo
    raise ValueError(f"Pergunta sem capítulo: {numero}")


def _mover_pergunta_panorama(deslocamento: int) -> None:
    atual = int(st.session_state.get(PANORAMA_PERGUNTA_KEY, 1))
    st.session_state[PANORAMA_PERGUNTA_KEY] = min(11, max(1, atual + deslocamento))


def _abrir_indice_panorama() -> None:
    st.session_state["panorama_indice_aberto"] = True


# --------------------------------------------------------------------------- #
# Início                                                                     #
# --------------------------------------------------------------------------- #

def _tab_inicio() -> None:
    """Abertura editorial (revisão de identidade visual, 25/09/2026, item
    12): título e texto de apoio, contexto institucional, questão central
    em destaque editorial (sem parecer cartão de alerta), três caminhos em
    linhas numeradas e a equipe — sem repetir logo/subtítulo/seletor de
    aparência, já no cabeçalho (`_cabecalho`), e sem começar por métricas do
    modelo."""
    with st.container(key="inicio_abertura_principal"):
        st.markdown(f"## {textos.TITULO_EDITORIAL_INICIO}")
        st.markdown(textos.TEXTO_APOIO_INICIO)

    st.divider()
    st.markdown(textos.CONTEXTO_DESAFIO)

    st.markdown(f"> **Questão central**\n>\n> {textos.QUESTAO_CENTRAL}")

    st.markdown("#### Três caminhos")
    for indice, (titulo, descricao) in enumerate(textos.CAMINHOS_APLICACAO, start=1):
        with st.container(key=f"inicio_caminho_{indice}"):
            st.markdown(f"**{indice}. {titulo}**")
            st.markdown(descricao)

    st.markdown("#### Equipe")
    with st.container(key="inicio_equipe_lista"):
        st.markdown(" · ".join(textos.EQUIPE))
    st.caption("Projeto desenvolvido em equipe para o Datathon — Fase 5.")


# --------------------------------------------------------------------------- #
# Panorama e resultados                                                     #
# --------------------------------------------------------------------------- #

def _tab_panorama_e_resultados(root: Path) -> None:
    st.subheader("Panorama e resultados")
    st.caption("O que os dados da Passos Mágicos mostram (2022–2024).")

    try:
        metricas = _carregar_metricas_negocio(root)
    except PainelIndisponivelError:
        st.error(
            "Não foi possível carregar o panorama de dados nesta instância. "
            "Tente novamente mais tarde ou contate a equipe responsável pelo projeto."
        )
        return

    perguntas = {int(item["numero"]): item for item in metricas["perguntas"]}

    st.markdown(
        f"Este painel responde às {len(perguntas)} perguntas de negócio do projeto, com "
        "evidências e explicações voltadas para o dia a dia da equipe pedagógica."
    )

    rotulos_perguntas = {
        numero: f"{numero}. {pergunta['pergunta']}"
        for numero, pergunta in perguntas.items()
    }
    if st.session_state.get(PANORAMA_PERGUNTA_KEY) not in perguntas:
        st.session_state[PANORAMA_PERGUNTA_KEY] = 1

    # Resumo, índice e capítulos ficam recolhidos e ANTES do navegador — só
    # o essencial (introdução + escolha da pergunta) aparece aberto por
    # padrão, para que o seletor fique imediatamente acima do conteúdo da
    # pergunta (revisão editorial, 24/09/2026, Parte 2).
    with st.expander("Resumo executivo"):
        for ponto in metricas["resumo_executivo"]:
            st.markdown(f"- {_texto_publico(ponto)}")

    with st.expander("Índice completo das 11 perguntas", expanded=st.session_state.get("panorama_indice_aberto", False)):
        for numero, pergunta_indice in perguntas.items():
            st.markdown(f"{numero}. {pergunta_indice['pergunta']}")

    with st.expander("Organização por capítulos"):
        for capitulo, numeros in textos.CAPITULOS:
            st.markdown(f"**{capitulo} — {len(numeros)} perguntas**")
            for numero in numeros:
                st.markdown(f"- {numero}. {perguntas[numero]['pergunta']}")

    with st.expander("Sobre estes dados"):
        for linha in textos.CONTEXTO_DADOS_PANORAMA:
            st.markdown(f"- {linha}")
        st.caption(textos.AVISO_TRES_PERIODOS)

    st.session_state["panorama_indice_aberto"] = False
    st.divider()

    with st.container(border=False, key="panorama_navegador_"):
        atual = int(st.session_state[PANORAMA_PERGUNTA_KEY])
        st.caption(f"Capítulo: {_capitulo_da_pergunta(atual)}")

        numero_selecionado = st.selectbox(
            "Escolha uma das 11 perguntas",
            options=list(perguntas),
            format_func=lambda numero: rotulos_perguntas[numero],
            key=PANORAMA_PERGUNTA_KEY,
        )

        anterior, contador, seguinte = st.columns([2, 1, 2], gap="medium")
        with anterior:
            st.button(
                "← Pergunta anterior",
                key="panorama_pergunta_anterior",
                disabled=numero_selecionado == 1,
                on_click=_mover_pergunta_panorama,
                args=(-1,),
                width="stretch",
            )
        with contador:
            st.markdown(f"**Pergunta {numero_selecionado} de {len(perguntas)}**")
        with seguinte:
            st.button(
                "Próxima pergunta →",
                key="panorama_proxima_pergunta",
                disabled=numero_selecionado == len(perguntas),
                on_click=_mover_pergunta_panorama,
                args=(1,),
                width="stretch",
            )

    pergunta = perguntas[numero_selecionado]
    numero = pergunta["numero"]
    with st.container(border=True):
        # A. Identificação
        st.markdown(f"### Pergunta {numero} de {len(perguntas)}")
        st.markdown(f"**{pergunta['pergunta']}**")
        st.caption(f"Por que isso importa: {_texto_publico(pergunta['por_que_importa'])}")

        # B. Resposta direta ("Em resumo")
        with st.container(border=False, key=f"panorama_resumo_{numero}"):
            st.markdown("##### Em resumo")
            st.markdown(_texto_publico(pergunta["resposta"]))

        # C. Números principais (2 a 4 cartões)
        st.markdown("##### Números principais")
        cartoes = narrativa.cartoes_numeros(pergunta)
        colunas_cartoes = st.columns(len(cartoes), gap="medium")
        for indice_cartao, (coluna, cartao) in enumerate(zip(colunas_cartoes, cartoes)):
            with coluna:
                # Markdown estilizado, não st.metric: o widget de métrica é
                # reservado à estimativa do modelo em "Avaliar um caso" (a
                # única leitura quantitativa acionável da aplicação); um
                # cartão informativo do panorama não deveria se confundir
                # visualmente com ela.
                with st.container(border=False, key=f"panorama_cartao_{numero}_{indice_cartao}"):
                    st.caption(cartao["rotulo"])
                    st.markdown(f"#### {cartao['valor']}")
                    st.caption(cartao["nota"])

        # D. Evidências visuais (gráfico + leitura do resultado, uma a uma)
        st.markdown("##### Evidências")
        figuras = graficos.graficos_interativos(numero, pergunta)
        blocos_evidencia = narrativa.evidencias(numero)
        for indice_figura, (figura, bloco) in enumerate(zip(figuras, blocos_evidencia)):
            with st.container(border=False, key=f"panorama_evidencia_{numero}_{indice_figura}"):
                st.markdown(f"**{bloco['titulo']}**")
                st.caption(bloco["frase"])
                st.plotly_chart(
                    figura,
                    width="stretch",
                    key=f"panorama_grafico_{numero}_{indice_figura}",
                    # Sem a barra de ferramentas técnica do Plotly (zoom, laço,
                    # download): em telas estreitas de celular seus botões
                    # ficam cortados, e o público desta aplicação não precisa
                    # de ferramentas de exploração técnica — só do tooltip ao
                    # passar o cursor, que continua ativo.
                    config={"displayModeBar": False, "responsive": True},
                )
                leitura = bloco["leitura"]
                with st.container(border=False, key=f"panorama_leitura_{numero}_{indice_figura}"):
                    st.markdown("Leitura do resultado")
                    st.markdown(f"- {leitura['padrao']}")
                    st.markdown(f"- {leitura['comparacao']}")
                    st.markdown(f"- {leitura['atencao']}")
                    st.markdown(f"- {leitura['cuidado']}")

        # E. Conclusão da análise — texto contínuo e pedagógico (revisão
        # editorial, 24/09/2026, Parte 4), não mais 5 linhas com rótulos.
        with st.container(border=False, key=f"panorama_conclusao_{numero}"):
            st.markdown("##### O que isso significa")
            for paragrafo in narrativa.conclusao_fluida(numero):
                st.markdown(_texto_publico(paragrafo))

        # F. Conteúdo secundário (recolhido por padrão)
        with st.expander("Ver dados da análise"):
            st.markdown("###### Principais números")
            st.dataframe(
                _tabela_para_exibicao(pergunta["principais_numeros"]),
                hide_index=True,
                width="stretch",
            )
            if pergunta.get("nota_numeros"):
                st.caption(_texto_publico(pergunta["nota_numeros"]))

            tabelas_recorte = narrativa.tabelas_complementares(pergunta)
            if tabelas_recorte:
                # Uma tabela pequena e específica por tipo de recorte (sexo,
                # faixa etária aproximada, fase...) em vez de uma única
                # tabela genérica com muitas colunas vazias (revisão
                # editorial, 24/09/2026, Parte 3).
                st.markdown("###### Outros recortes")
                for tabela in tabelas_recorte:
                    st.markdown(f"**{tabela['titulo']}**")
                    st.dataframe(_tabela_para_exibicao(tabela["linhas"]), hide_index=True, width="stretch")
                    if tabela.get("nota"):
                        st.caption(tabela["nota"])
            elif pergunta.get("analises_complementares_numeros"):
                st.markdown("###### Outros recortes")
                st.dataframe(
                    _tabela_para_exibicao(pergunta["analises_complementares_numeros"]),
                    hide_index=True,
                    width="stretch",
                )
                # A nota técnica completa (`analises_complementares_nota`)
                # não é mais exibida aqui: seu conteúdo, em linguagem
                # técnica de desenvolvimento, já está traduzido para o
                # público em "Leitura do resultado", nas evidências acima.

        with st.expander("Fonte e metodologia"):
            st.markdown(f"**População e período analisados:** {pergunta['populacao_periodo']}")
            st.markdown(f"**Origem dos dados:** {narrativa.fonte_publica(numero)}")
            st.markdown(f"**Limites da análise:** {_texto_publico(pergunta['limites'])}")

    # Navegação final: repete os mesmos controles do topo, para quem chega
    # ao fim do conteúdo sem rolar de volta (revisão editorial, Parte 2).
    with st.container(border=False, key=f"panorama_navegador_fim_{numero}"):
        st.divider()
        fim_anterior, fim_indice, fim_seguinte = st.columns([2, 2, 2], gap="medium")
        with fim_anterior:
            st.button(
                "← Pergunta anterior",
                key="panorama_pergunta_anterior_fim",
                disabled=numero == 1,
                on_click=_mover_pergunta_panorama,
                args=(-1,),
                width="stretch",
            )
        with fim_indice:
            st.button(
                "Voltar ao índice",
                key="panorama_voltar_indice_fim",
                on_click=_abrir_indice_panorama,
                width="stretch",
            )
        with fim_seguinte:
            st.button(
                "Próxima pergunta →",
                key="panorama_proxima_pergunta_fim",
                disabled=numero == len(perguntas),
                on_click=_mover_pergunta_panorama,
                args=(1,),
                width="stretch",
            )


# --------------------------------------------------------------------------- #
# Avaliar um caso (identificação, indicadores, resultado e relatório)       #
# --------------------------------------------------------------------------- #

def _campo_numerico(campo: str) -> str:
    info = textos.INDICADORES[campo]
    ajuda = f"{info['definicao']} {info['o_que_informar']} {info['ausencia']}"
    return st.text_input(
        f"{info['sigla']} — {info['nome_extenso']} *",
        key=f"campo_{campo}",
        help=ajuda,
        placeholder=f"ex.: {info['exemplo']}",
    )


def _campo_fase() -> str:
    info = textos.INDICADORES[textos.CAMPO_FASE]
    ajuda = f"{info['definicao']} {info['o_que_informar']} {info['ausencia']}"
    return st.selectbox(
        "Fase atual *",
        options=FASE_OPCOES,
        format_func=_rotulo_fase,
        key="campo_fase_origem",
        help=ajuda,
    )


def _campo_fase_ideal() -> str:
    return st.selectbox(
        "Fase ideal *",
        options=FASE_IDEAL_OPCOES,
        format_func=_rotulo_fase,
        key="campo_fase_ideal_calculo",
        help=textos.AJUDA_FASE_IDEAL,
    )


def _ian_a_partir_do_valor(defasagem_bruta: str | None) -> float | None:
    """IAN de contexto (nunca enviado à estimativa) a partir do valor de
    defasagem atualmente em uso, direto ou calculado."""
    texto = "" if defasagem_bruta is None else str(defasagem_bruta).strip()
    if texto == "":
        return None
    try:
        valor = float(texto.replace(",", "."))
    except ValueError:
        return None
    try:
        return calculadoras.ian_pela_defasagem(valor)
    except calculadoras.EntradaInvalidaError:
        return None


def _snapshot_formulario(valores: dict, contexto_caso: dict) -> dict:
    return {**{campo: valores.get(campo, "") for campo in inferencia.FEATURES}, **contexto_caso}


def _campo_idade_contexto() -> str:
    return st.text_input(
        textos.ROTULO_IDADE_CONTEXTO,
        key="campo_idade_contexto",
        help=textos.AJUDA_IDADE_CONTEXTO,
        placeholder="ex.: 12",
    )


def _secao_identificacao_e_contexto() -> dict:
    st.markdown("##### Identificação e contexto")
    with st.container(key="avaliar_contexto_campos"):
        c1, c2 = st.columns(2)
        with c1:
            identificacao = st.text_input(
                textos.ROTULO_IDENTIFICACAO_CASO,
                key="campo_identificacao_caso",
                help=textos.AVISO_IDENTIFICACAO_OPCIONAL,
                placeholder="ex.: J.S. ou caso-014",
            )
        with c2:
            sexo = st.selectbox(
                "Sexo informado no cadastro institucional *",
                options=textos.SEXO_OPCOES,
                key="campo_sexo_contexto",
            )
    st.caption(textos.AVISO_IDENTIFICACAO_OPCIONAL)
    st.caption(textos.AVISO_CONTEXTO_NAO_ALTERA_ESTIMATIVA)
    return {"identificacao": identificacao, "sexo": sexo}


def _situacao_e_ian(defasagem_bruta: str | None) -> tuple[str | None, float | None]:
    """Situação (Em fase/Moderada/Severa) e IAN a partir da defasagem já
    conhecida (direta ou calculada) — sempre informação educacional,
    nunca um oitavo preditor."""
    texto = "" if defasagem_bruta is None else str(defasagem_bruta).strip()
    if not texto:
        return None, None
    try:
        numero = float(texto.replace(",", "."))
        return calculadoras.categoria_defasagem(numero), calculadoras.ian_pela_defasagem(numero)
    except (ValueError, calculadoras.EntradaInvalidaError):
        return None, None


def _secao_trajetoria_escolar(valores: dict) -> dict:
    """Idade (sugestão de fase ideal, nunca automática) → fase atual → fase
    ideal confirmada → defasagem → situação → IAN. A fase efetiva enviada
    ao modelo é sempre a selecionada em "Fase atual", no domínio oficial
    0–7 — a sugestão por idade nunca substitui essa escolha nem é aplicada
    silenciosamente."""
    st.markdown("##### Trajetória escolar")
    c1, c2 = st.columns(2)
    with c1:
        idade_texto = _campo_idade_contexto()
    with c2:
        valores["fase_origem"] = _campo_fase()
    st.caption(textos.AJUDA_IDADE_CONTEXTO)
    st.caption(textos.AVISO_IDADE_NAO_AUTOMATIZA_CALCULO)

    idade_valida = None
    try:
        idade_valida = ficha.idade_em_anos(idade_texto)
    except ValueError:
        pass
    if idade_valida is not None:
        sugestao = calculadoras.sugerir_fase_ideal_por_idade(idade_valida)
        st.caption(textos.texto_sugestao_fase_ideal(sugestao["candidatas"], sugestao["ambigua"]))
        if not sugestao["candidatas"]:
            st.caption("Consulte o registro institucional e confirme manualmente a fase ideal.")
    st.caption(textos.AVISO_SUGESTAO_FASE_IDEAL)
    fase_ideal_selecionada = _campo_fase_ideal()

    modo = st.radio(
        "Como você quer informar a defasagem?",
        (textos.ROTULO_MODO_DEFASAGEM_CALCULADO, textos.ROTULO_MODO_DEFASAGEM_DIRETO),
        key="modo_defasagem", horizontal=True,
    )
    registrada = ""
    escolha_defasagem = None
    if modo == textos.ROTULO_MODO_DEFASAGEM_DIRETO:
        registrada = _campo_numerico("defasagem_origem")

    try:
        calculada = calculadoras.calcular_defasagem(
            int(valores["fase_origem"]), int(fase_ideal_selecionada))
    except (ValueError, calculadoras.EntradaInvalidaError):
        calculada = None
    st.markdown(
        "**Diferença entre a fase atual e a fase ideal:** "
        f"{'—' if calculada is None else calculada}")
    st.caption(textos.EXPLICACAO_CALCULO_DEFASAGEM)

    if registrada.strip() and calculada is not None:
        try:
            registrada_num = ficha.numero_decimal(registrada)
        except ValueError:
            registrada_num = None
        if registrada_num is not None and registrada_num != calculada:
            st.warning(
                f"A defasagem registrada ({registrada_num:g}) diverge da calculada pelas fases ({calculada:g})."
            )
            escolha_defasagem = st.radio(
                "Qual defasagem deve ser utilizada?",
                ("calculada", "registrada"), index=None,
                format_func=lambda valor: "Calculada pelas fases" if valor == "calculada" else "Registrada na instituição",
                key="escolha_defasagem_divergente",
            )
    try:
        defasagem_final, origem_defasagem = ficha.resolver_defasagem(
            valores.get("fase_origem", ""), fase_ideal_selecionada,
            registrada if modo == textos.ROTULO_MODO_DEFASAGEM_DIRETO else None,
            escolha_defasagem,
        )
        valores["defasagem_origem"] = f"{defasagem_final:g}"
    except ValueError:
        valores["defasagem_origem"] = ""
        origem_defasagem = "pendente"

    situacao, ian_valor = _situacao_e_ian(valores.get("defasagem_origem"))
    if situacao is not None:
        st.markdown(f"**Situação:** {situacao} · **IAN:** {ian_valor:g}")
        st.caption(textos.EXPLICACAO_CALCULO_IAN)

    return {
        "modo_defasagem": modo, "fase_ideal": fase_ideal_selecionada,
        "idade": idade_texto, "defasagem_registrada": registrada,
        "escolha_defasagem": escolha_defasagem, "origem_defasagem": origem_defasagem,
    }


def _secao_desempenho_academico(valores: dict) -> str:
    st.markdown("##### Desempenho acadêmico")
    modo = st.radio(
        "Como você quer informar o IDA?",
        (textos.ROTULO_MODO_IDA_DIRETO, textos.ROTULO_MODO_IDA_CALCULADO),
        key="modo_ida", horizontal=True,
    )
    if modo == textos.ROTULO_MODO_IDA_DIRETO:
        valores["ida"] = _campo_numerico("ida")
        return "direto"

    campos_notas = (
        ("campo_nota_matematica", textos.ROTULO_NOTA_MATEMATICA, "7.5"),
        ("campo_nota_portugues", textos.ROTULO_NOTA_PORTUGUES, "8.0"),
        ("campo_nota_ingles", textos.ROTULO_NOTA_INGLES, "6.5"),
    )
    notas_validas: list[float] = []
    colunas = st.columns(3)
    for coluna, (chave, rotulo, exemplo) in zip(colunas, campos_notas):
        with coluna:
            bruta = st.text_input(rotulo, key=chave, placeholder=f"ex.: {exemplo}")
            if bruta.strip():
                try:
                    notas_validas.append(ficha.numero_decimal(bruta, minimo=0, maximo=10))
                except ValueError as erro:
                    st.caption(f"⚠️ {rotulo}: {erro}.")
    st.caption(textos.AJUDA_NOTAS_IDA)
    st.caption(textos.AVISO_IDA_ESCOPO_FASES)
    ida_calculado = None
    if len(notas_validas) == 3:
        try:
            ida_calculado = calculadoras.calcular_ida(*notas_validas)
        except calculadoras.EntradaInvalidaError:
            ida_calculado = None
    st.markdown(f"**IDA calculado:** {'—' if ida_calculado is None else f'{ida_calculado:.2f}'}")
    valores["ida"] = "" if ida_calculado is None else f"{ida_calculado:.4f}"
    return "calculado"


def _secao_iaa(valores: dict) -> str:
    st.markdown("###### IAA — Indicador de Autoavaliação")
    modo = st.radio(
        "Como você quer informar o IAA?",
        (textos.ROTULO_MODO_IAA_DIRETO, textos.ROTULO_MODO_IAA_CALCULADO),
        key="modo_iaa", horizontal=True,
    )
    if modo == textos.ROTULO_MODO_IAA_DIRETO:
        valores["iaa"] = _campo_numerico("iaa")
        return "direto"

    st.caption(textos.AJUDA_IAA_CALCULO)
    try:
        grupo = calculadoras.grupo_fase_iaa(valores.get("fase_origem", ""))
    except calculadoras.EntradaInvalidaError:
        grupo = None
    if grupo is None:
        st.caption("Selecione a fase atual em \"Trajetória escolar\" para ver as perguntas do IAA.")
        valores["iaa"] = ""
        return "calculado"

    opcoes = ("", "A", "B", "C") if grupo == "0-2" else ("", "A", "B", "C", "D")
    respostas: dict[int, str] = {}
    for numero, pergunta in enumerate(calculadoras.PERGUNTAS_IAA, start=1):
        respostas[numero] = st.selectbox(
            f"{numero}. {pergunta}",
            options=opcoes,
            format_func=lambda opcao: textos.OPCOES_RESPOSTA_IAA_TEXTO[opcao],
            key=f"campo_iaa_pergunta_{numero}",
        )
    try:
        iaa_calculado = calculadoras.calcular_iaa(valores.get("fase_origem", ""), respostas)
    except calculadoras.EntradaInvalidaError:
        iaa_calculado = None
    st.markdown(f"**IAA calculado:** {'—' if iaa_calculado is None else f'{iaa_calculado:.2f}'}")
    valores["iaa"] = "" if iaa_calculado is None else f"{iaa_calculado:.4f}"
    return "calculado"


def _secao_ipp(fase_origem: str) -> str:
    """Campo do IPP — visível diretamente na ficha (não escondido em um
    expander), pois é obrigatório para concluir a ficha nas fases Alfa–7.
    Nunca é um dos sete preditores; usado só como contexto para o INDE."""
    if fase_origem not in calculadoras.FASES_VALIDAS:
        st.caption(textos.NOTA_IPP_NAO_SE_APLICA)
        return ""
    return st.text_input(
        textos.ROTULO_IPP_INSTITUCIONAL,
        key="campo_ipp_contexto",
        help=textos.AJUDA_IPP_INSTITUCIONAL,
        placeholder="ex.: 7.0",
    )


def _secao_engajamento_e_desenvolvimento(valores: dict) -> tuple[str, str]:
    st.markdown("##### Engajamento e desenvolvimento")
    c1, c2 = st.columns(2)
    with c1:
        valores["ieg"] = _campo_numerico("ieg")
    with c2:
        valores["ips"] = _campo_numerico("ips")
    st.caption(textos.NOTA_IEG_SEM_CALCULO)
    st.caption(textos.NOTA_IPS_SEM_CALCULO)

    valores["ipv"] = _campo_numerico("ipv")
    st.caption(textos.NOTA_IPV_SEM_CALCULO)

    ipp_texto = _secao_ipp(valores.get("fase_origem", ""))

    origem_iaa = _secao_iaa(valores)
    return origem_iaa, ipp_texto


def _linha_resumo(campo: str, valor_bruto: str, origem: str) -> dict:
    info = textos.INDICADORES[campo]
    texto = "" if valor_bruto is None else str(valor_bruto).strip()
    valor_exibicao = (_rotulo_fase(texto) if campo == textos.CAMPO_FASE else texto) if texto else "Pendente"
    return {
        "Indicador": f"{info['sigla']} — {info['nome_extenso']}",
        "Valor utilizado": valor_exibicao,
        "Origem": origem if texto else "Pendente",
    }


def _numero_ou_none(valor) -> float | None:
    texto = str(valor or "").strip()
    if not texto:
        return None
    try:
        return float(texto.replace(",", "."))
    except ValueError:
        return None


def _secao_inde_complementar(valores: dict, ipp_texto: str) -> dict:
    """INDE só como informação complementar — nunca enviado ao modelo, nunca
    confundido com a estimativa, nunca calculado com componente ausente. O
    campo do IPP é coletado antes, fora deste expander (`_secao_ipp`) — aqui
    ele só é reaproveitado para o cálculo."""
    with st.expander("INDE (informação complementar)"):
        st.caption(textos.EXPLICACAO_INDE)
        fase = valores.get("fase_origem") or ""
        if fase not in calculadoras.FASES_VALIDAS:
            st.caption("Selecione a fase atual em \"Trajetória escolar\" para calcular o INDE.")
            return {"ipp": "", "inde": None}
        st.caption(f"IPP informado: {ipp_texto or 'pendente'} (ver seção \"Engajamento e desenvolvimento\").")
        _situacao_ignorada, ian_valor = _situacao_e_ian(valores.get("defasagem_origem"))
        componentes = {
            "ian": ian_valor, "ida": _numero_ou_none(valores.get("ida")),
            "ieg": _numero_ou_none(valores.get("ieg")), "iaa": _numero_ou_none(valores.get("iaa")),
            "ips": _numero_ou_none(valores.get("ips")), "ipp": _numero_ou_none(ipp_texto),
            "ipv": _numero_ou_none(valores.get("ipv")),
        }
        try:
            valor_inde, faltantes = calculadoras.calcular_inde(fase, componentes)
        except calculadoras.EntradaInvalidaError:
            valor_inde, faltantes = None, []
        if valor_inde is not None:
            st.markdown(f"**INDE calculado:** {valor_inde:.2f}")
        elif faltantes:
            st.caption(textos.texto_inde_incompleto(faltantes))
        return {"ipp": ipp_texto, "inde": valor_inde}


def _resumo_indicadores(valores: dict, contexto: dict, trajetoria: dict,
                        origem_ida: str, origem_iaa: str, ipp_texto: str) -> dict:
    origem_defasagem = (
        "Calculado pelas fases"
        if trajetoria["modo_defasagem"] == textos.ROTULO_MODO_DEFASAGEM_CALCULADO
        else "Informado diretamente"
    )
    origem_ida_texto = "Calculado pelas três notas" if origem_ida == "calculado" else "Informado diretamente"
    origem_iaa_texto = "Calculado pelas seis perguntas" if origem_iaa == "calculado" else "Informado diretamente"
    situacao, ian_valor = _situacao_e_ian(valores.get("defasagem_origem"))

    # Resumo em um expander colapsado por padrão: útil para conferência antes
    # de gerar a estimativa, mas não precisa ficar em primeiro plano para
    # quem está avaliando a ficha (revisão de linguagem/ênfase visual).
    with st.expander("Resumo da ficha antes de gerar a estimativa"):
        st.markdown("##### Dados da ficha")
        ficha_linhas = [
            {"Dado": "Identificação", "Valor": contexto.get("identificacao") or "Pendente"},
            {"Dado": "Idade", "Valor": contexto.get("idade") or "Pendente"},
            {"Dado": "Sexo", "Valor": contexto.get("sexo") if contexto.get("sexo") != "Selecione" else "Pendente"},
            {"Dado": "Fase atual", "Valor": _rotulo_fase(valores.get("fase_origem", "")) if valores.get("fase_origem") else "Pendente"},
            {"Dado": "Fase ideal", "Valor": _rotulo_fase(trajetoria.get("fase_ideal", "")) if trajetoria.get("fase_ideal") else "Pendente"},
            {"Dado": "Defasagem", "Valor": valores.get("defasagem_origem") or "Pendente"},
            {"Dado": "Situação", "Valor": situacao or "Pendente"},
            {"Dado": "IAN", "Valor": f"{ian_valor:g}" if ian_valor is not None else "Pendente"},
            {"Dado": "IPP", "Valor": ipp_texto or "Pendente"},
        ]
        st.table(pd.DataFrame(ficha_linhas))

        st.markdown("##### Indicadores usados na estimativa")
        linhas = [
            _linha_resumo("ida", valores.get("ida", ""), origem_ida_texto),
            _linha_resumo("ieg", valores.get("ieg", ""), "Informado diretamente"),
            _linha_resumo("iaa", valores.get("iaa", ""), origem_iaa_texto),
            _linha_resumo("ips", valores.get("ips", ""), "Informado diretamente"),
            _linha_resumo("ipv", valores.get("ipv", ""), "Informado diretamente"),
            _linha_resumo("fase_origem", valores.get("fase_origem", ""), "Confirmado pelo usuário"),
            _linha_resumo("defasagem_origem", valores.get("defasagem_origem", ""), origem_defasagem),
        ]
        # `st.table` (não `st.dataframe`): estático, sem paginação/ordenação —
        # apropriado para um resumo curto de 7 linhas, e mantém esta tabela
        # fora da varredura de `at.dataframe` usada pelos testes específicos
        # das tabelas de recorte do Panorama (tipos de elemento diferentes).
        st.table(pd.DataFrame(linhas))
        st.caption("Os sete indicadores acima são exatamente os usados na estimativa. Se algo estiver errado, "
                   "volte às seções acima e corrija antes de gerar a estimativa.")

        if situacao is not None:
            st.caption(f"IAN (não enviado à estimativa): {ian_valor:g} — {situacao}.")

    return _secao_inde_complementar(valores, ipp_texto)


def _formulario() -> tuple[dict, dict, dict, bool]:
    st.caption(
        "Campos marcados com * são obrigatórios para concluir a ficha."
    )
    st.button(
        "Preencher exemplo sintético", on_click=_preencher_exemplo_sintetico,
        help="Preenche o formulário com valores ilustrativos inventados, "
             "que não correspondem a nenhum(a) estudante real.",
    )

    contexto_caso = _secao_identificacao_e_contexto()

    valores: dict[str, str] = {}
    trajetoria = _secao_trajetoria_escolar(valores)
    contexto_caso["idade"] = trajetoria.get("idade", "")
    origem_ida = _secao_desempenho_academico(valores)
    origem_iaa, ipp_texto = _secao_engajamento_e_desenvolvimento(valores)
    trajetoria["origem_ida"] = origem_ida
    trajetoria["origem_iaa"] = origem_iaa

    complemento = _resumo_indicadores(valores, contexto_caso, trajetoria, origem_ida, origem_iaa, ipp_texto)
    trajetoria.update(complemento)

    dados_validacao = {
        **valores, **contexto_caso,
        "fase_ideal": trajetoria.get("fase_ideal", ""),
        "defasagem_registrada": trajetoria.get("defasagem_registrada", ""),
        "escolha_defasagem": trajetoria.get("escolha_defasagem"),
        "ipp": trajetoria.get("ipp", ""),
    }
    validacao = ficha.validar_ficha(dados_validacao)
    if validacao.erros:
        st.caption("Pendências da ficha: " + " ".join(validacao.erros.values()))
    enviado = st.button(
        "Gerar estimativa e relatório", type="primary", key="botao_gerar_estimativa",
        disabled=not validacao.valida,
    )
    trajetoria["validacao"] = validacao
    return valores, contexto_caso, trajetoria, enviado


def _gerar_relatorio_html(estado: dict) -> str:
    resultado = estado["resultado"]
    entradas = estado["entradas"]
    contexto_caso = estado["contexto"]
    gerado_em = estado["gerado_em"]

    def esc(valor) -> str:
        return html.escape(str(valor)) if valor not in (None, "") else "—"

    identificacao = esc(contexto_caso.get("identificacao"))
    idade_exibicao = esc(contexto_caso.get("idade"))
    sexo = contexto_caso.get("sexo") or ""
    sexo_exibicao = esc(sexo) if sexo and sexo != "Selecione" else "—"
    fase_exibicao = esc(_rotulo_fase(entradas.get("fase_origem") or ""))

    origem_defasagem = (
        textos.RELATORIO_ROTULO_CALCULADO
        if estado.get("modo_defasagem") == textos.ROTULO_MODO_DEFASAGEM_CALCULADO
        else textos.RELATORIO_ROTULO_INDICADOR
    )
    origem_ida = (
        textos.RELATORIO_ROTULO_CALCULADO
        if estado.get("modo_ida") == textos.ROTULO_MODO_IDA_CALCULADO
        else textos.RELATORIO_ROTULO_INDICADOR
    )
    origem_iaa = (
        textos.RELATORIO_ROTULO_CALCULADO
        if estado.get("modo_iaa") == textos.ROTULO_MODO_IAA_CALCULADO
        else textos.RELATORIO_ROTULO_INDICADOR
    )

    linhas_indicadores = [
        f"<tr><td>{esc(textos.INDICADORES['ida']['sigla'])}</td><td>{esc(entradas.get('ida'))}</td>"
        f"<td>{esc(origem_ida)}</td></tr>",
    ]
    notas = estado.get("notas_ida") or {}
    if estado.get("modo_ida") == textos.ROTULO_MODO_IDA_CALCULADO:
        linhas_indicadores.append(
            f"<tr><td>Nota de Matemática</td><td>{esc(notas.get('matematica'))}</td>"
            f"<td>{esc(textos.RELATORIO_ROTULO_INDICADOR)}</td></tr>"
        )
        linhas_indicadores.append(
            f"<tr><td>Nota de Português</td><td>{esc(notas.get('portugues'))}</td>"
            f"<td>{esc(textos.RELATORIO_ROTULO_INDICADOR)}</td></tr>"
        )
        linhas_indicadores.append(
            f"<tr><td>Nota de Inglês</td><td>{esc(notas.get('ingles'))}</td>"
            f"<td>{esc(textos.RELATORIO_ROTULO_INDICADOR)}</td></tr>"
        )
    linhas_indicadores.append(
        f"<tr><td>{esc(textos.INDICADORES['ieg']['sigla'])}</td><td>{esc(entradas.get('ieg'))}</td>"
        f"<td>{esc(textos.RELATORIO_ROTULO_INDICADOR)}</td></tr>"
    )
    linhas_indicadores.append(
        f"<tr><td>{esc(textos.INDICADORES['iaa']['sigla'])}</td><td>{esc(entradas.get('iaa'))}</td>"
        f"<td>{esc(origem_iaa)}</td></tr>"
    )
    if estado.get("modo_iaa") == textos.ROTULO_MODO_IAA_CALCULADO:
        for numero, pergunta in enumerate(calculadoras.PERGUNTAS_IAA, start=1):
            resposta = (estado.get("respostas_iaa") or {}).get(numero)
            linhas_indicadores.append(
                f"<tr><td>{numero}. {esc(pergunta)}</td><td>{esc(resposta)}</td>"
                f"<td>Resposta do estudante</td></tr>"
            )
    linhas_indicadores.append(
        f"<tr><td>{esc(textos.INDICADORES['ips']['sigla'])}</td><td>{esc(entradas.get('ips'))}</td>"
        f"<td>{esc(textos.RELATORIO_ROTULO_INDICADOR)}</td></tr>"
    )
    linhas_indicadores.append(
        f"<tr><td>{esc(textos.INDICADORES['ipv']['sigla'])}</td><td>{esc(entradas.get('ipv'))}</td>"
        f"<td>{esc(textos.RELATORIO_ROTULO_INDICADOR)}</td></tr>"
    )
    linhas_indicadores.append(
        f"<tr><td>Fase atual</td><td>{fase_exibicao}</td>"
        f"<td>{esc(textos.RELATORIO_ROTULO_INDICADOR)}</td></tr>"
    )
    if estado.get("fase_ideal"):
        linhas_indicadores.append(
            f"<tr><td>Fase ideal confirmada</td><td>{esc(_rotulo_fase(estado['fase_ideal']))}</td>"
            f"<td>{esc(textos.RELATORIO_ROTULO_CONTEXTO)}</td></tr>"
        )
    linhas_indicadores.append(
        f"<tr><td>Defasagem</td><td>{esc(entradas.get('defasagem_origem'))}</td>"
        f"<td>{esc(origem_defasagem)}</td></tr>"
    )
    situacao, ian_valor = _situacao_e_ian(entradas.get("defasagem_origem"))
    if situacao is not None:
        linhas_indicadores.append(
            f"<tr><td>Situação da adequação</td><td>{esc(situacao)}</td>"
            f"<td>{esc(textos.RELATORIO_ROTULO_CONTEXTO)}</td></tr>"
        )
        linhas_indicadores.append(
            f"<tr><td>IAN</td><td>{ian_valor:g}</td>"
            f"<td>{esc(textos.RELATORIO_ROTULO_CALCULADO)}</td></tr>"
        )

    linha_inde = ""
    ipp_contexto = _numero_ou_none(estado.get("ipp_contexto"))
    fase_para_inde = entradas.get("fase_origem") or ""
    if fase_para_inde in calculadoras.FASES_VALIDAS and ian_valor is not None:
        componentes = {
            "ian": ian_valor, "ida": _numero_ou_none(entradas.get("ida")),
            "ieg": _numero_ou_none(entradas.get("ieg")), "iaa": _numero_ou_none(entradas.get("iaa")),
            "ips": _numero_ou_none(entradas.get("ips")), "ipp": ipp_contexto,
            "ipv": _numero_ou_none(entradas.get("ipv")),
        }
        try:
            valor_inde, faltantes_inde = calculadoras.calcular_inde(fase_para_inde, componentes)
        except calculadoras.EntradaInvalidaError:
            valor_inde, faltantes_inde = None, []
        if valor_inde is not None:
            linha_inde = (
                f"<h2>INDE (informação complementar)</h2>"
                f"<p><strong>IPP:</strong> {ipp_contexto:g}</p>"
                f"<p><strong>INDE calculado:</strong> {valor_inde:.2f}</p>"
                f"<p class=\"aviso\">{esc(textos.EXPLICACAO_INDE)}</p>"
            )

    posicao = textos.TITULO_ACIMA_DO_PONTO if resultado.is_risk else textos.TITULO_ABAIXO_DO_PONTO
    interpretacao = textos.TEXTO_ACIMA_DO_PONTO if resultado.is_risk else textos.TEXTO_ABAIXO_DO_PONTO
    proximos_passos = (
        "".join(f"<li>{esc(passo)}</li>" for passo in textos.PROTOCOLO_PROXIMOS_PASSOS)
        if resultado.is_risk else f"<li>{esc(textos.ORIENTACAO_PRIORIDADE_ABAIXO)}</li>"
    )

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>Relatório de acompanhamento</title>
<style>
body {{ font-family: Arial, Helvetica, sans-serif; margin: 2rem; color: #1a1a1a; }}
h1 {{ font-size: 1.4rem; }}
h2 {{ font-size: 1.1rem; margin-top: 1.5rem; border-bottom: 0.06rem solid #ccc; padding-bottom: .25rem; }}
table {{ border-collapse: collapse; width: 100%; margin-top: .5rem; }}
td, th {{ border: 0.06rem solid #ccc; padding: .4rem .6rem; text-align: left; font-size: .95rem; }}
.aviso {{ background: #f4f4f4; padding: .75rem 1rem; margin-top: .75rem; border-left: 0.25rem solid #888; }}
.rodape {{ margin-top: 2rem; font-size: .8rem; color: #555; }}
</style>
</head>
<body>
<h1>Relatório de acompanhamento educacional</h1>
<p>Gerado em {esc(gerado_em.strftime('%d/%m/%Y %H:%M:%S'))} — Datathon Fase 5, Associação Passos Mágicos.</p>

<h2>Identificação e contexto</h2>
<table>
<tr><th>Nome ou identificação interna</th><td>{identificacao}</td></tr>
<tr><th>Idade em anos completos</th><td>{idade_exibicao}</td></tr>
<tr><th>Sexo informado no cadastro institucional</th><td>{sexo_exibicao}</td></tr>
</table>
<p class="aviso">{esc(textos.AVISO_CONTEXTO_NAO_ALTERA_ESTIMATIVA)}</p>

<h2>Trajetória e indicadores</h2>
<table>
<tr><th>Indicador</th><th>Valor</th><th>Categoria</th></tr>
{''.join(linhas_indicadores)}
</table>
{linha_inde}

<h2>Resultado da ferramenta</h2>
<p><strong>Estimativa:</strong> {resultado.probability * 100:.1f}%</p>
<p><strong>Ponto de atenção operacional utilizado:</strong> aproximadamente {round(resultado.threshold * 100)}% (valor exato: {resultado.threshold:.17f})</p>
<p><strong>{esc(posicao)}</strong></p>
<p>{esc(interpretacao)}</p>

<h2>Próximos passos sugeridos</h2>
<ul>{proximos_passos}</ul>
<p class="aviso">{esc(textos.AVISO_DECISAO_PROFISSIONAIS)}</p>

<h2>Limitações e aviso</h2>
<p>{esc(textos.AVISO_NAO_CAUSAL)}</p>
<p>{esc(textos.AVISO_ABAIXO_NAO_ELIMINA_RISCO)}</p>
<p class="aviso">{esc(textos.RELATORIO_AVISO_DIAGNOSTICO)}</p>

<p class="rodape">{esc(textos.RELATORIO_AVISO_ARMAZENAMENTO)}</p>
<p class="rodape">{esc(textos.RELATORIO_AVISO_IMPRESSAO)}</p>
</body>
</html>"""


def _relatorio_do_caso(estado: dict) -> None:
    st.markdown("##### Relatório do caso")
    st.caption(
        "O relatório reúne as informações desta tela em um arquivo HTML "
        "autocontido, gerado apenas em memória — nada é salvo no servidor."
    )
    st.caption(textos.RELATORIO_AVISO_ARMAZENAMENTO)
    conteudo_html = _gerar_relatorio_html(estado)
    st.download_button(
        "Baixar relatório (.html)",
        data=conteudo_html.encode("utf-8"),
        file_name=textos.RELATORIO_ARQUIVO_NOME,
        mime="text/html",
        key="botao_baixar_relatorio",
    )
    st.caption(textos.RELATORIO_AVISO_IMPRESSAO)


def _apresentar_resultado(estado: dict, valores_atuais: dict, contexto_atual: dict) -> None:
    resultado = estado["resultado"]
    st.subheader("Resultado")

    resultado_desatualizado = _snapshot_formulario(valores_atuais, contexto_atual) != estado["snapshot"]
    if resultado_desatualizado:
        st.info(
            "Os campos foram alterados após a última estimativa gerada. Clique em "
            "\"Gerar estimativa\" novamente para atualizar o resultado e o relatório.",
            icon="ℹ️",
        )

    st.progress(resultado.probability, text=f"Estimativa: {resultado.probability * 100:.1f}%")
    st.metric("Estimativa", f"{resultado.probability * 100:.1f}%")

    if resultado.is_risk:
        st.warning(f"**{textos.TITULO_ACIMA_DO_PONTO}**\n\n{textos.TEXTO_ACIMA_DO_PONTO}", icon="⚠️")
    else:
        st.success(f"**{textos.TITULO_ABAIXO_DO_PONTO}**\n\n{textos.TEXTO_ABAIXO_DO_PONTO}", icon="✅")

    st.caption(
        f"Ponto de atenção operacional (arredondado): aproximadamente "
        f"{round(resultado.threshold * 100)}%.")
    st.caption(textos.EXPLICACAO_AJUSTE_PONTO_ATENCAO)
    st.caption(textos.EXPLICACAO_MAIS_ENCAMINHADOS_OBSERVACAO)

    situacao, ian_valor = _situacao_e_ian(estado["entradas"].get("defasagem_origem"))
    if situacao is not None:
        st.caption(f"Situação: {situacao} · IAN (contexto, não enviado à estimativa): {ian_valor:g}.")

    st.markdown(textos.AVISO_NAO_CAUSAL)
    st.markdown(textos.AVISO_SUPERVISAO_HUMANA)
    st.caption(textos.AVISO_ABAIXO_NAO_ELIMINA_RISCO)

    with st.expander("Detalhes técnicos deste resultado"):
        st.markdown(f"Estimativa exata (probabilidade predita): {resultado.probability:.6f}")
        st.markdown(f"Ponto de atenção operacional (threshold) exato: {resultado.threshold:.6f}")
        st.markdown(f"Caso sinalizado para acompanhamento (classe positiva): {'sim' if resultado.is_risk else 'não'}")
        st.caption(
            "Termos técnicos: probabilidade predita = estimativa; threshold = ponto "
            "de atenção operacional (o ponto metodológico original, preservado para "
            "rastreabilidade, está documentado à parte pela equipe responsável).")

    st.markdown("##### Próximos passos sugeridos")
    if resultado.is_risk:
        colunas = st.columns(2, gap="large")
        for indice, passo in enumerate(textos.PROTOCOLO_PROXIMOS_PASSOS, start=1):
            with colunas[(indice - 1) % 2]:
                with st.container(border=True):
                    st.markdown(f"**{indice}.** {passo}")
    else:
        st.markdown(textos.ORIENTACAO_PRIORIDADE_ABAIXO)
    st.caption(textos.AVISO_DECISAO_PROFISSIONAIS)

    if not resultado_desatualizado:
        _relatorio_do_caso(estado)
    else:
        st.caption("O relatório fica disponível novamente depois que a ficha atualizada for validada e processada.")


def _tab_avaliar(contexto_app: inferencia.ApplicationContext) -> None:
    st.subheader("Avaliar um caso")
    st.caption(textos.AVISO_PRIVACIDADE_AVALIAR)

    valores, contexto_caso, trajetoria, enviado = _formulario()

    if enviado:
        validacao = trajetoria["validacao"]
        entradas = dict(validacao.payload or {})
        try:
            resultado = inferencia.run_inference(contexto_app, entradas)
        except inferencia.InputValidationError as erro:
            st.error(f"Entrada inválida — corrija e envie novamente. {erro}")
        except inferencia.PublicValidationError:
            st.error(
                "Não foi possível concluir a estimativa com segurança nesta instância. "
                "Tente novamente mais tarde ou contate a equipe responsável pelo projeto."
            )
        else:
            st.session_state["caso_resultado"] = {
                "resultado": resultado,
                "entradas": dict(entradas),
                "contexto": dict(contexto_caso),
                "modo_defasagem": trajetoria.get("modo_defasagem"),
                "fase_ideal": trajetoria.get("fase_ideal"),
                "modo_ida": st.session_state.get("modo_ida"),
                "modo_iaa": st.session_state.get("modo_iaa"),
                "notas_ida": {
                    "matematica": st.session_state.get("campo_nota_matematica", ""),
                    "portugues": st.session_state.get("campo_nota_portugues", ""),
                    "ingles": st.session_state.get("campo_nota_ingles", ""),
                },
                "ipp_contexto": st.session_state.get("campo_ipp_contexto", ""),
                "inde": trajetoria.get("inde"),
                "respostas_iaa": {
                    numero: st.session_state.get(f"campo_iaa_pergunta_{numero}", "")
                    for numero in range(1, 7)
                },
                "snapshot": _snapshot_formulario(valores, contexto_caso),
                "gerado_em": datetime.now(),
            }

    estado = st.session_state.get("caso_resultado")
    if estado is not None:
        _apresentar_resultado(estado, valores, contexto_caso)


# --------------------------------------------------------------------------- #
# Entenda os indicadores                                                    #
# --------------------------------------------------------------------------- #

def _tab_indicadores() -> None:
    st.subheader("Entenda os indicadores")
    st.markdown(textos.EXPLICACAO_DEFASAGEM)
    st.divider()

    colunas_indicadores = st.columns(2, gap="large")
    for indice, campo in enumerate(inferencia.FEATURES):
        info = textos.INDICADORES[campo]
        with colunas_indicadores[indice % 2]:
            with st.expander(f"{info['sigla']} — {info['nome_extenso']}"):
                st.markdown(info["definicao"])
                st.markdown(f"**O que informar:** {info['o_que_informar']}")
                st.markdown(f"**Se não souber o valor:** {info['ausencia']}")
                st.caption(info["ressalva"])

    st.divider()
    st.markdown("##### Idade, notas e o que a ferramenta realmente recebe")
    st.markdown(textos.EXPLICACAO_IDADE_FASE_DEFASAGEM)
    st.markdown(textos.EXPLICACAO_NOTAS_IDA)
    st.markdown(textos.EXPLICACAO_AGREGADO_VS_DETALHE)

    st.markdown("##### Observação anual e par longitudinal")
    st.markdown(textos.EXPLICACAO_OBSERVACAO_ANUAL_PAR_LONGITUDINAL)

    st.markdown("##### Pedras e Ponto de Virada")
    st.markdown(textos.EXPLICACAO_PEDRAS)
    st.markdown(textos.EXPLICACAO_PONTO_DE_VIRADA)

    st.divider()
    st.caption("Fontes documentais: " + "; ".join(textos.FONTES_DOCUMENTAIS) + ".")


# --------------------------------------------------------------------------- #
# Orquestração                                                              #
# --------------------------------------------------------------------------- #
# "Modelo e limitações" (visão simples, comparação dos dois pontos de
# atenção, detalhes técnicos e tradução de termos) foi removida da
# navegação — ver `scripts/gerar_relatorio_modelo_e_limitacoes.py`, que gera
# o mesmo conteúdo (atualizado com o ponto operacional em destaque) como
# documento HTML/PDF autônomo em `reports/`.

def _cabecalho() -> None:
    """Logo oficial + subtítulo do projeto + seletor de aparência, seguidos
    das cinco abas (renderizadas logo depois, por `main()`). O logo é um
    arquivo local estático (`assets/brand/`, ver `assets/brand/ORIGEM.md`);
    sem hotlink em tempo de execução. No modo escuro, uma pequena superfície
    clara (`--pm-logo-fundo`) preserva a legibilidade das silhuetas escuras
    do logo — o arquivo em si nunca é alterado."""
    with st.container(key="cabecalho_principal"):
        col_logo, col_titulo, col_tema = st.columns([1, 5, 2], vertical_alignment="center")
        with col_logo:
            if LOGO_PATH.is_file():
                with st.container(key="logo_moldura_principal"):
                    st.image(str(LOGO_PATH), width=150)
        with col_titulo:
            st.title("Passos Mágicos")
            st.caption(textos.SUBTITULO_PROJETO)
        with col_tema:
            st.segmented_control(
                "Aparência", (TEMA_CLARO, TEMA_ESCURO), key=TEMA_KEY,
                default=TEMA_CLARO, label_visibility="collapsed",
            )


def main() -> None:
    _aplicar_estilo_visual()
    graficos.aplicar_tema(_tema_atual() == TEMA_ESCURO)
    try:
        contexto = _carregar_aplicacao()
    except Exception:  # noqa: BLE001 — falha de inicialização: mensagem genérica e segura, sem detalhes técnicos.
        st.error(
            "Não foi possível carregar os dados oficiais desta aplicação nesta instância. "
            "A aplicação não pode continuar. Tente novamente mais tarde ou contate a "
            "equipe responsável pelo projeto."
        )
        st.stop()
        return

    _cabecalho()

    # "Modelo e limitações" foi removida da navegação (decisão de produto,
    # 25/09/2026): conteúdo técnico demais para o dia a dia da ficha. Migrada
    # para um documento autônomo (HTML/PDF), gerado por
    # `scripts/gerar_relatorio_modelo_e_limitacoes.py` a partir dos mesmos
    # artefatos oficiais — útil para a equipe (ex.: material de apoio para
    # apresentação), sem precisar ficar em primeiro plano na aplicação.
    tab_inicio, tab_panorama, tab_avaliar, tab_indicadores = st.tabs(
        ["Início", "Panorama e resultados", "Avaliar um caso", "Entenda os indicadores"]
    )
    with tab_inicio:
        _tab_inicio()
    with tab_panorama:
        _tab_panorama_e_resultados(contexto.root)
    with tab_avaliar:
        _tab_avaliar(contexto)
    with tab_indicadores:
        _tab_indicadores()

    st.divider()
    st.caption(textos.RODAPE_APLICACAO)


if __name__ == "__main__":
    # Guarda padrão: evita que um `import streamlit_app` feito por fora
    # (ex.: testes que precisam inspecionar `_carregar_metricas_negocio`/
    # `PainelIndisponivelError` sem abrir uma sessão real) execute `main()`
    # "a seco", fora do ciclo de vida controlado do script runner do
    # Streamlit — algo que corrompe o rastreamento interno de formulários
    # do Streamlit para o resto do processo. Tanto `streamlit run
    # streamlit_app.py` quanto `AppTest` executam este arquivo sob um
    # módulo chamado exatamente "__main__" (documentado no próprio
    # `script_runner.py` do Streamlit), então esta guarda não muda nada do
    # comportamento real da aplicação nos dois casos.
    main()
