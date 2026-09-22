"""Aplicação Streamlit pública — TASK 009.

Demonstra, de forma educacional, o modelo oficialmente avaliado do Datathon
Fase 5 (Associação Passos Mágicos). Usa exclusivamente
`artifacts/modelo_avaliado.joblib`, sem retreino, recalibração ou geração de
novas métricas. Toda a lógica de dados fica em `src/inferencia.py`; este
arquivo cuida apenas da interface.

Privacidade: nenhuma entrada do usuário é persistida, logada ou enviada a
serviços externos. Nenhum RA, nome ou identificador é solicitado. Nenhuma
base de dados é carregada ou aceita por upload.
"""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

_ROOT = Path(__file__).resolve().parent
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import inferencia  # noqa: E402

st.set_page_config(
    page_title="Datathon Fase 5 — Risco de defasagem",
    page_icon="🎓",
    layout="centered",
)

FASE_OPCOES = ("", *inferencia.PHASE_CATEGORIES)
CAMPO_ROTULO = {
    "ida": "IDA — Indicador de Desempenho Acadêmico",
    "ieg": "IEG — Indicador de Engajamento",
    "iaa": "IAA — Indicador de Autoavaliação",
    "ips": "IPS — Indicador Psicossocial",
    "ipv": "IPV — Indicador do Ponto de Virada",
    "defasagem_origem": "Defasagem registrada no ano de origem",
}
CAMPO_AJUDA = {
    "ida": "Valor numérico do indicador, como registrado na base oficial. Deixe em branco se não souber.",
    "ieg": "Valor numérico do indicador, como registrado na base oficial. Deixe em branco se não souber.",
    "iaa": "Valor numérico do indicador, como registrado na base oficial. Deixe em branco se não souber.",
    "ips": "Valor numérico do indicador, como registrado na base oficial. Deixe em branco se não souber.",
    "ipv": "Valor numérico do indicador, como registrado na base oficial. Deixe em branco se não souber.",
    "defasagem_origem": "Diferença registrada entre a fase efetiva e a fase ideal no ano de origem "
                        "(pode ser negativa, zero ou positiva). Deixe em branco se não souber.",
}
EXEMPLO_SINTETICO = {
    "ida": "6.5", "ieg": "8.0", "iaa": "7.0", "ips": "5.0", "ipv": "7.5",
    "fase_origem": "2", "defasagem_origem": "0",
}


@st.cache_resource(show_spinner="Carregando e validando os artefatos oficiais…")
def _carregar_aplicacao() -> inferencia.ApplicationContext:
    """Executado uma única vez por processo (cache de recurso, nunca de
    dados). Localiza a raiz, roda o validador público e carrega o modelo."""
    return inferencia.prepare_application()


def _preencher_exemplo_sintetico() -> None:
    for campo, valor in EXEMPLO_SINTETICO.items():
        st.session_state[f"campo_{campo}"] = valor


def _cabecalho() -> None:
    st.title("🎓 Risco de entrada em defasagem escolar")
    st.caption("Datathon Fase 5 — Associação Passos Mágicos")
    st.info(
        "**Finalidade educacional e demonstrativa.** Esta aplicação mostra, de forma "
        "interativa, como o modelo já avaliado do projeto classifica uma transição "
        "aluno-ano hipotética. Ela não é um sistema de produção institucional, não "
        "treina nem reavalia nada: usa exclusivamente o modelo oficialmente avaliado "
        "e o limiar já congelado no projeto.",
        icon="🎓",
    )
    with st.expander("O que este número significa e o que ele não significa"):
        st.markdown(
            "- A saída é a **probabilidade estatística** de um aluno sem defasagem no "
            "ano de origem entrar em defasagem no ano seguinte, segundo o modelo "
            "avaliado.\n"
            "- **Não é uma relação de causa e efeito.** O modelo descreve associações "
            "observadas nos dados históricos, não mecanismos causais.\n"
            "- **Não é um diagnóstico individual definitivo** nem substitui avaliação "
            "pedagógica ou profissional.\n"
            "- O resultado é apoio à priorização e deve ser sempre revisado por uma "
            "equipe pedagógica ou profissional responsável."
        )


def _formulario() -> dict | None:
    st.subheader("Sete indicadores do aluno na origem")
    st.caption(
        "Preencha os indicadores conhecidos. Os campos numéricos podem ficar em "
        "branco quando o valor não for conhecido."
    )
    st.button("Preencher exemplo sintético", on_click=_preencher_exemplo_sintetico,
             help="Preenche o formulário com valores ilustrativos inventados, "
                  "que não correspondem a nenhum aluno real.")

    with st.form("formulario_preditores", clear_on_submit=False):
        valores: dict[str, str] = {}
        col_esquerda, col_direita = st.columns(2)
        campos_numericos_esquerda = ("ida", "ieg", "iaa")
        campos_numericos_direita = ("ips", "ipv", "defasagem_origem")
        for campo in campos_numericos_esquerda:
            with col_esquerda:
                valores[campo] = st.text_input(
                    CAMPO_ROTULO[campo], key=f"campo_{campo}", help=CAMPO_AJUDA[campo], placeholder="ex.: 7.2")
        for campo in campos_numericos_direita:
            with col_direita:
                valores[campo] = st.text_input(
                    CAMPO_ROTULO[campo], key=f"campo_{campo}", help=CAMPO_AJUDA[campo], placeholder="ex.: 7.2")

        valores["fase_origem"] = st.selectbox(
            "Fase educacional de origem",
            options=FASE_OPCOES,
            key="campo_fase_origem",
            help="Categoria oficial da fase de origem (domínio fechado: "
                f"{', '.join(inferencia.PHASE_CATEGORIES)}). Selecione uma opção.",
        )

        enviado = st.form_submit_button("Gerar estimativa", type="primary")

    return valores if enviado else None


def _apresentar_resultado(resultado: inferencia.InferenceResult) -> None:
    percentual = 100 * resultado.probability
    st.subheader("Resultado")
    st.metric("Probabilidade estimada de entrada em defasagem", f"{percentual:.1f}%")

    if resultado.is_risk:
        st.warning(
            "**Classificação: risco sinalizado** — a probabilidade estimada atingiu ou "
            "superou o limiar oficialmente congelado do modelo.",
            icon="⚠️",
        )
    else:
        st.success(
            "**Classificação: risco não sinalizado** — a probabilidade estimada ficou "
            "abaixo do limiar oficialmente congelado do modelo.",
            icon="✅",
        )
    st.caption(
        f"Limiar de decisão: **{resultado.threshold:.4f}** — o mesmo limiar congelado "
        "usado na avaliação temporal oficial do projeto, sem qualquer ajuste feito por "
        "esta aplicação."
    )

    st.markdown(
        "> Um resultado **abaixo do limiar não elimina o risco**: é apenas o ponto de "
        "corte usado pelo modelo para sinalizar prioridade, calibrado para um nível "
        "de sensibilidade que **não se manteve completo no teste temporal mais "
        "recente** (ver limitações abaixo). A leitura é sempre **associação "
        "estatística, não causalidade**, e não substitui a avaliação de uma equipe "
        "pedagógica ou profissional."
    )


def _limitacoes() -> None:
    with st.expander("Limitações importantes do modelo", expanded=True):
        st.markdown(
            "- **Queda de recall no teste temporal:** a sensibilidade do modelo caiu "
            "de cerca de 82% na validação interna do desenvolvimento para cerca de 40% "
            "no teste temporal mais recente — ou seja, no ano seguinte o modelo "
            "identificou uma fração bem menor dos casos reais de entrada em defasagem.\n"
            "- **Subestimação de risco observada:** no teste temporal, o modelo tendeu "
            "a prever probabilidades menores do que a proporção real de casos "
            "observados.\n"
            "- **Caráter observacional:** o modelo é preditivo, não causal, e não "
            "constitui diagnóstico individual.\n"
            "- **Amostra pequena e um único corte temporal:** os resultados têm "
            "incerteza relevante e podem não se repetir em anos futuros.\n"
            "- **Supervisão humana obrigatória:** toda saída exige revisão por equipe "
            "pedagógica ou profissional antes de qualquer decisão; o resultado nunca "
            "deve decidir, sozinho, inclusão, exclusão ou atendimento de um aluno."
        )


def _rodape() -> None:
    st.divider()
    st.caption(
        "Aplicação educacional e demonstrativa do Datathon Fase 5 (Associação Passos "
        "Mágicos). Usa exclusivamente o modelo oficialmente avaliado, com o limiar "
        "congelado na avaliação temporal do projeto. Nenhum dado individual é "
        "solicitado, armazenado ou enviado a terceiros nesta aplicação."
    )


def main() -> None:
    try:
        contexto = _carregar_aplicacao()
    except Exception:  # noqa: BLE001 — falha de inicialização: mensagem genérica e segura, sem detalhes técnicos.
        st.error(
            "Não foi possível validar os artefatos oficiais do modelo nesta instância. "
            "A aplicação não pode continuar. Tente novamente mais tarde ou contate a "
            "equipe responsável pelo projeto."
        )
        st.stop()
        return

    _cabecalho()
    entradas = _formulario()

    if entradas is not None:
        try:
            resultado = inferencia.run_inference(contexto, entradas)
        except inferencia.InputValidationError as erro:
            st.error(f"Entrada inválida — corrija e envie novamente. {erro}")
        except inferencia.PublicValidationError:
            st.error(
                "Não foi possível concluir a inferência com segurança nesta instância. "
                "Tente novamente mais tarde ou contate a equipe responsável pelo projeto."
            )
        else:
            _apresentar_resultado(resultado)

    _limitacoes()
    _rodape()


main()
